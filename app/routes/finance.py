"""记账与账单提醒"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Transaction, BillReminder
from app.pagination import get_pagination_params, paginate_query
from app.compat import parse_iso_date
from app.utils import current_user, family_id
from app.validators import validate_required, validate_amount, validate_choice
from datetime import date, timedelta

finance_bp = Blueprint("finance", __name__)


# ─── 账单提醒 ───────────────────────────────────────────

@finance_bp.route("/bills", methods=["GET"])
@jwt_required()
def list_bills():
    bills = BillReminder.query.filter_by(family_id=family_id()).order_by(BillReminder.due_day.asc()).all()
    today = date.today()
    result = []
    for b in bills:
        d = b.to_dict()
        d["days_until_due"] = _days_until_due(today, b.due_day)
        result.append(d)
    return jsonify({"bills": result}), 200


def _days_until_due(today, due_day):
    """计算距离下一次账单截止还剩几天"""
    import calendar
    try:
        due_this_month = today.replace(day=min(due_day, calendar.monthrange(today.year, today.month)[1]))
    except Exception:
        return 999
    if due_this_month < today:
        # 下个月
        next_month = today.month + 1
        next_year = today.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        due_this_month = due_this_month.replace(year=next_year, month=next_month,
                                                 day=min(due_day, calendar.monthrange(next_year, next_month)[1]))
    return (due_this_month - today).days


@finance_bp.route("/bills", methods=["POST"])
@jwt_required()
def create_bill():
    data = request.get_json() or {}
    try:
        validate_required(data, ["title"])
        title = (data.get("title") or "").strip()
        amount = validate_amount(data.get("amount", 0))
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    due_day = data.get("due_day", 1)
    if not 1 <= due_day <= 31:
        return jsonify({"msg": "日期必须在 1-31 之间"}), 400
    bill = BillReminder(
        family_id=family_id(),
        creator_id=current_user().id,
        title=title,
        amount=amount,
        due_day=due_day,
    )
    db.session.add(bill)
    db.session.commit()
    return jsonify({"bill": bill.to_dict()}), 201


@finance_bp.route("/bills/<int:bill_id>", methods=["PUT"])
@jwt_required()
def update_bill(bill_id):
    bill = BillReminder.query.filter_by(id=bill_id, family_id=family_id()).first()
    if not bill:
        return jsonify({"msg": "账单不存在"}), 404
    data = request.get_json() or {}
    for field in ("title", "amount", "due_day"):
        if field in data:
            setattr(bill, field, data[field])
    db.session.commit()
    return jsonify({"bill": bill.to_dict()}), 200


@finance_bp.route("/bills/<int:bill_id>", methods=["DELETE"])
@jwt_required()
def delete_bill(bill_id):
    bill = BillReminder.query.filter_by(id=bill_id, family_id=family_id()).first()
    if not bill:
        return jsonify({"msg": "账单不存在"}), 404
    db.session.delete(bill)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 收支记录 ───────────────────────────────────────────

@finance_bp.route("/transactions", methods=["GET"])
@jwt_required()
def list_transactions():
    fid = family_id()
    month = request.args.get("month", "", type=str)  # YYYY-MM
    ttype = request.args.get("type", "", type=str)   # income / expense
    cat = request.args.get("category", "", type=str)
    page, per_page = get_pagination_params()

    query = Transaction.query.filter_by(family_id=fid)
    if month:
        parts = month.split("-")
        if len(parts) == 2:
            query = query.filter(
                db.extract("year", Transaction.date) == int(parts[0]),
                db.extract("month", Transaction.date) == int(parts[1]),
            )
    if ttype:
        query = query.filter_by(type=ttype)
    if cat:
        query = query.filter_by(category=cat)

    query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
    result = paginate_query(query, page, per_page)

    # 摘要
    income_total = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.family_id == fid, Transaction.type == "income"
    )
    expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.family_id == fid, Transaction.type == "expense"
    )
    if month:
        parts = month.split("-")
        if len(parts) == 2:
            income_total = income_total.filter(
                db.extract("year", Transaction.date) == int(parts[0]),
                db.extract("month", Transaction.date) == int(parts[1]),
            )
            expense_total = expense_total.filter(
                db.extract("year", Transaction.date) == int(parts[0]),
                db.extract("month", Transaction.date) == int(parts[1]),
            )

    inc = income_total.scalar() or 0
    exp = expense_total.scalar() or 0

    # 按类别统计
    from sqlalchemy import func
    cat_stats = db.session.query(
        Transaction.category, func.sum(Transaction.amount)
    ).filter(Transaction.family_id == fid)
    if month:
        parts = month.split("-")
        if len(parts) == 2:
            cat_stats = cat_stats.filter(
                db.extract("year", Transaction.date) == int(parts[0]),
                db.extract("month", Transaction.date) == int(parts[1]),
            )
    cat_stats = cat_stats.group_by(Transaction.category).all()

    return jsonify({
        "transactions": [t.to_dict() for t in result["items"]],
        "summary": {
            "income": inc,
            "expense": exp,
            "balance": inc - exp,
        },
        "by_category": [{"category": c, "amount": a} for c, a in cat_stats],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@finance_bp.route("/transactions", methods=["POST"])
@jwt_required()
def create_transaction():
    data = request.get_json() or {}
    try:
        ttype = validate_choice(data.get("type", "expense"), ("income", "expense"))
        amount = validate_amount(data.get("amount", 0))
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    tx_date = data.get("date", date.today().isoformat())
    try:
        tx_date = parse_iso_date(tx_date)
    except Exception:
        tx_date = date.today()

    tx = Transaction(
        family_id=family_id(),
        user_id=current_user().id,
        type=ttype,
        category=data.get("category", "其他"),
        amount=amount,
        note=data.get("note", ""),
        date=tx_date,
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify({"transaction": tx.to_dict()}), 201


@finance_bp.route("/transactions/<int:tx_id>", methods=["PUT"])
@jwt_required()
def update_transaction(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, family_id=family_id()).first()
    if not tx:
        return jsonify({"msg": "记录不存在"}), 404
    data = request.get_json() or {}
    for field in ("type", "category", "amount", "note", "date"):
        if field in data:
            val = data[field]
            if field == "date":
                try:
                    val = parse_iso_date(val)
                except Exception:
                    continue
            setattr(tx, field, val)
    db.session.commit()
    return jsonify({"transaction": tx.to_dict()}), 200


@finance_bp.route("/transactions/<int:tx_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, family_id=family_id()).first()
    if not tx:
        return jsonify({"msg": "记录不存在"}), 404
    db.session.delete(tx)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
