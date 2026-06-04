"""健康档案与宠物"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, HealthRecord, Pet
from app.pagination import get_pagination_params, paginate_query
from app.compat import parse_iso_date
from app.utils import current_user, family_id
from app.validators import validate_required, sanitize_string
from datetime import date

health_bp = Blueprint("health", __name__)


# ─── 健康档案 ───────────────────────────────────────────

@health_bp.route("/records", methods=["GET"])
@jwt_required()
def list_records():
    uid = request.args.get("user_id", type=int)
    rec_type = request.args.get("record_type", "", type=str)
    page, per_page = get_pagination_params()
    query = HealthRecord.query.filter_by(family_id=family_id())
    if uid:
        query = query.filter_by(user_id=uid)
    if rec_type:
        query = query.filter_by(record_type=rec_type)
    query = query.order_by(HealthRecord.record_date.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        "records": [r.to_dict() for r in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@health_bp.route("/records", methods=["POST"])
@jwt_required()
def create_record():
    data = request.get_json() or {}
    try:
        validate_required(data, ["record_type", "value"])
        record_type = sanitize_string(data["record_type"], max_length=100)
        value = sanitize_string(data["value"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    try:
        rec_date = parse_iso_date(data.get("record_date", date.today().isoformat()))
    except Exception:
        rec_date = date.today()
    hr = HealthRecord(
        user_id=data.get("user_id", current_user().id),
        family_id=family_id(),
        record_type=record_type,
        value=value,
        unit=data.get("unit", ""),
        record_date=rec_date,
        note=data.get("note", ""),
    )
    db.session.add(hr)
    db.session.commit()
    return jsonify({"record": hr.to_dict()}), 201


@health_bp.route("/records/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_record(record_id):
    hr = HealthRecord.query.filter_by(id=record_id, family_id=family_id()).first()
    if not hr:
        return jsonify({"msg": "记录不存在"}), 404
    data = request.get_json() or {}
    for field in ("record_type", "value", "unit", "note"):
        if field in data:
            setattr(hr, field, data[field])
    if "record_date" in data:
        try:
            hr.record_date = parse_iso_date(data["record_date"])
        except Exception:
            pass
    db.session.commit()
    return jsonify({"record": hr.to_dict()}), 200


@health_bp.route("/records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    hr = HealthRecord.query.filter_by(id=record_id, family_id=family_id()).first()
    if not hr:
        return jsonify({"msg": "记录不存在"}), 404
    db.session.delete(hr)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 宠物 ───────────────────────────────────────────────

@health_bp.route("/pets", methods=["GET"])
@jwt_required()
def list_pets():
    pets = Pet.query.filter_by(family_id=family_id()).order_by(Pet.created_at.desc()).all()
    today = date.today()
    result = []
    for p in pets:
        d = p.to_dict()
        # 计算到期提醒
        from datetime import timedelta
        d["deworming_soon"] = p.deworming_date and (p.deworming_date - today).days <= 7
        d["vaccine_soon"] = p.vaccine_date and (p.vaccine_date - today).days <= 7
        result.append(d)
    return jsonify({"pets": result}), 200


@health_bp.route("/pets", methods=["POST"])
@jwt_required()
def create_pet():
    data = request.get_json() or {}
    try:
        validate_required(data, ["name"])
        name = sanitize_string(data["name"], max_length=100)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    dew = data.get("deworming_date")
    vac = data.get("vaccine_date")
    try:
        dew = parse_iso_date(dew) if dew else None
        vac = parse_iso_date(vac) if vac else None
    except Exception:
        return jsonify({"msg": "日期格式无效 (YYYY-MM-DD)"}), 400
    pet = Pet(
        family_id=family_id(),
        name=name,
        species=data.get("species", ""),
        deworming_date=dew,
        vaccine_date=vac,
        note=data.get("note", ""),
    )
    db.session.add(pet)
    db.session.commit()
    return jsonify({"pet": pet.to_dict()}), 201


@health_bp.route("/pets/<int:pet_id>", methods=["PUT"])
@jwt_required()
def update_pet(pet_id):
    pet = Pet.query.filter_by(id=pet_id, family_id=family_id()).first()
    if not pet:
        return jsonify({"msg": "宠物不存在"}), 404
    data = request.get_json() or {}
    for field in ("name", "species", "note"):
        if field in data:
            setattr(pet, field, data[field])
    for date_field in ("deworming_date", "vaccine_date"):
        if date_field in data:
            try:
                setattr(pet, date_field, parse_iso_date(data[date_field]) if data[date_field] else None)
            except Exception:
                pass
    db.session.commit()
    return jsonify({"pet": pet.to_dict()}), 200


@health_bp.route("/pets/<int:pet_id>", methods=["DELETE"])
@jwt_required()
def delete_pet(pet_id):
    pet = Pet.query.filter_by(id=pet_id, family_id=family_id()).first()
    if not pet:
        return jsonify({"msg": "宠物不存在"}), 404
    db.session.delete(pet)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
