"""购物清单、家务待办、心愿单"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, ShoppingItem, Task, Wish, Feed, FamilyMember
from app.pagination import get_pagination_params, paginate_query
from app.compat import parse_iso_date
from app.utils import current_user, family_id
from app.validators import validate_required, sanitize_string

tasks_bp = Blueprint("tasks", __name__)


# ─── 购物清单 ───────────────────────────────────────────

@tasks_bp.route("/shopping", methods=["GET"])
@jwt_required()
def list_shopping():
    page, per_page = get_pagination_params()
    query = ShoppingItem.query.filter_by(family_id=family_id()).order_by(ShoppingItem.bought.asc(), ShoppingItem.created_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        "items": [i.to_dict() for i in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@tasks_bp.route("/shopping", methods=["POST"])
@jwt_required()
def create_shopping():
    data = request.get_json() or {}
    try:
        validate_required(data, ["name"])
        name = sanitize_string(data["name"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    item = ShoppingItem(
        family_id=family_id(),
        added_by=current_user().id,
        name=name,
        quantity=data.get("quantity", "1"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@tasks_bp.route("/shopping/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_shopping(item_id):
    item = ShoppingItem.query.filter_by(id=item_id, family_id=family_id()).first()
    if not item:
        return jsonify({"msg": "物品不存在"}), 404
    data = request.get_json() or {}
    if "bought" in data:
        item.bought = data["bought"]
    if "name" in data:
        item.name = data["name"].strip()
    if "quantity" in data:
        item.quantity = data["quantity"]
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 200


@tasks_bp.route("/shopping/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_shopping(item_id):
    item = ShoppingItem.query.filter_by(id=item_id, family_id=family_id()).first()
    if not item:
        return jsonify({"msg": "物品不存在"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 家务待办 ───────────────────────────────────────────

@tasks_bp.route("/chores", methods=["GET"])
@jwt_required()
def list_chores():
    page, per_page = get_pagination_params()
    query = Task.query.filter_by(family_id=family_id()).order_by(Task.completed.asc(), Task.due_date.asc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        "tasks": [t.to_dict() for t in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@tasks_bp.route("/chores", methods=["POST"])
@jwt_required()
def create_chore():
    data = request.get_json() or {}
    try:
        validate_required(data, ["title"])
        title = sanitize_string(data["title"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    from datetime import date
    due = None
    if data.get("due_date"):
        try:
            due = parse_iso_date(data["due_date"])
        except Exception:
            return jsonify({"msg": "日期格式无效 (YYYY-MM-DD)"}), 400
    task = Task(
        family_id=family_id(),
        creator_id=current_user().id,
        assignee_id=data.get("assignee_id", current_user().id),
        title=title,
        due_date=due,
    )
    db.session.add(task)
    db.session.flush()
    feed = Feed(family_id=family_id(), user_id=current_user().id,
                content=f"创建了待办「{title}」", type="task")
    db.session.add(feed)
    db.session.commit()
    return jsonify({"task": task.to_dict()}), 201


@tasks_bp.route("/chores/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_chore(task_id):
    task = Task.query.filter_by(id=task_id, family_id=family_id()).first()
    if not task:
        return jsonify({"msg": "任务不存在"}), 404
    data = request.get_json() or {}
    if "completed" in data:
        task.completed = data["completed"]
        if data["completed"]:
            feed = Feed(family_id=family_id(), user_id=current_user().id,
                        content=f"完成了待办「{task.title}」", type="task")
            db.session.add(feed)
    if "title" in data:
        task.title = data["title"].strip()
    if "assignee_id" in data:
        task.assignee_id = data["assignee_id"]
    if "due_date" in data:
        from datetime import date
        try:
            task.due_date = parse_iso_date(data["due_date"]) if data["due_date"] else None
        except Exception:
            pass
    db.session.commit()
    return jsonify({"task": task.to_dict()}), 200


@tasks_bp.route("/chores/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_chore(task_id):
    task = Task.query.filter_by(id=task_id, family_id=family_id()).first()
    if not task:
        return jsonify({"msg": "任务不存在"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 心愿单 ─────────────────────────────────────────────

@tasks_bp.route("/wishes", methods=["GET"])
@jwt_required()
def list_wishes():
    wishes = Wish.query.filter_by(family_id=family_id()).order_by(Wish.created_at.desc()).all()
    return jsonify({"wishes": [w.to_dict() for w in wishes]}), 200


@tasks_bp.route("/wishes", methods=["POST"])
@jwt_required()
def create_wish():
    data = request.get_json() or {}
    try:
        validate_required(data, ["name"])
        name = sanitize_string(data["name"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    wish = Wish(
        user_id=current_user().id,
        family_id=family_id(),
        name=name,
        link=data.get("link", ""),
        note=data.get("note", ""),
    )
    db.session.add(wish)
    db.session.commit()
    return jsonify({"wish": wish.to_dict()}), 201


@tasks_bp.route("/wishes/<int:wish_id>", methods=["PUT"])
@jwt_required()
def update_wish(wish_id):
    wish = Wish.query.filter_by(id=wish_id, family_id=family_id(), user_id=current_user().id).first()
    if not wish:
        return jsonify({"msg": "只能修改自己的心愿"}), 403
    data = request.get_json() or {}
    for field in ("name", "link", "note"):
        if field in data:
            setattr(wish, field, data[field])
    db.session.commit()
    return jsonify({"wish": wish.to_dict()}), 200


@tasks_bp.route("/wishes/<int:wish_id>", methods=["DELETE"])
@jwt_required()
def delete_wish(wish_id):
    wish = Wish.query.filter_by(id=wish_id, family_id=family_id()).first()
    if not wish:
        return jsonify({"msg": "心愿不存在"}), 404
    fm = FamilyMember.query.filter_by(user_id=current_user().id, family_id=family_id()).first()
    if wish.user_id != current_user().id and (not fm or fm.role != "admin"):
        return jsonify({"msg": "只能删除自己的心愿"}), 403
    db.session.delete(wish)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
