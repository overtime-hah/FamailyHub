"""位置上报与查看"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Location, FamilyMember
from app.utils import current_user, family_id

location_bp = Blueprint("location", __name__)


@location_bp.route("/report", methods=["POST"])
@jwt_required()
def report_location():
    """上报当前位置"""
    data = request.get_json() or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is None or lng is None:
        return jsonify({"msg": "缺少经纬度"}), 400

    loc = Location.query.filter_by(user_id=current_user().id, family_id=family_id()).first()
    if loc:
        loc.latitude = lat
        loc.longitude = lng
        loc.timestamp = db.func.now()
    else:
        loc = Location(user_id=current_user().id, family_id=family_id(), latitude=lat, longitude=lng)
        db.session.add(loc)
    db.session.commit()
    return jsonify({"location": loc.to_dict()}), 200


@location_bp.route("/members", methods=["GET"])
@jwt_required()
def get_member_locations():
    """获取所有家庭成员的最新位置"""
    members = FamilyMember.query.filter_by(family_id=family_id()).all()
    result = []
    for fm in members:
        u = fm.user
        loc = Location.query.filter_by(user_id=u.id, family_id=family_id()).first()
        result.append({
            "user_id": u.id,
            "username": u.nickname or u.username,
            "role": fm.role,
            "avatar_url": u.avatar_url or "",
            "location": loc.to_dict() if loc else None,
        })
    return jsonify({"members": result}), 200


@location_bp.route("/my-history", methods=["GET"])
@jwt_required()
def my_history():
    """获取自己的位置历史（需要另外存储轨迹，此处简化：只返回最新一条）"""
    loc = Location.query.filter_by(user_id=current_user().id, family_id=family_id()).first()
    return jsonify({"location": loc.to_dict() if loc else None}), 200
