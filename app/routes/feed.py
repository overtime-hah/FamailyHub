"""动态流与公告"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Feed, User, FamilyMember
from app.utils import current_user, family_id

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/list", methods=["GET"])
@jwt_required()
def feed_list():
    """获取动态流（公告置顶，按时间倒序）"""
    fid = family_id()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)

    query = Feed.query.filter_by(family_id=fid).order_by(Feed.is_pinned.desc(), Feed.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    feeds = [f.to_dict() for f in pagination.items]

    # 即将到来的生日（7天内）
    from datetime import date, timedelta
    today = date.today()
    week_later = today + timedelta(days=7)
    upcoming_birthdays = []
    for fm in FamilyMember.query.filter_by(family_id=fid).all():
        u = fm.user
        if u and u.birthday:
            # 检查今年生日是否在7天内
            try:
                bday_this_year = u.birthday.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = u.birthday.replace(year=today.year + 1)
            except ValueError:
                continue  # 2月29日
            if today <= bday_this_year <= week_later:
                upcoming_birthdays.append({
                    "user_id": u.id,
                    "username": u.nickname or u.username,
                    "birthday": u.birthday.isoformat(),
                    "days_left": (bday_this_year - today).days,
                })

    return jsonify({
        "feeds": feeds,
        "upcoming_birthdays": upcoming_birthdays,
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@feed_bp.route("/announcement", methods=["POST"])
@jwt_required()
def create_announcement():
    """管理员发布置顶公告"""
    user = current_user()
    fm = FamilyMember.query.filter_by(user_id=user.id, family_id=family_id()).first()
    if not fm or fm.role != "admin":
        return jsonify({"msg": "仅管理员可发布公告"}), 403

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"msg": "公告内容不能为空"}), 400

    feed = Feed(family_id=family_id(), user_id=user.id, content=content, type="announcement", is_pinned=True)
    db.session.add(feed)
    db.session.commit()
    return jsonify({"feed": feed.to_dict()}), 201


@feed_bp.route("/<int:feed_id>", methods=["DELETE"])
@jwt_required()
def delete_feed(feed_id):
    """删除动态"""
    feed = Feed.query.filter_by(id=feed_id, family_id=family_id()).first()
    if not feed:
        return jsonify({"msg": "动态不存在"}), 404
    user = current_user()
    fm = FamilyMember.query.filter_by(user_id=user.id, family_id=family_id()).first()
    if not fm:
        return jsonify({"msg": "无权操作"}), 403
    if fm.role != "admin" and feed.user_id != user.id:
        return jsonify({"msg": "无权删除"}), 403
    db.session.delete(feed)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
