"""家庭管理：成员、邀请码、个人信息"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
from app.models import db, User, Family, FamilyMember, Feed
from app.compat import parse_iso_date
from app.utils import current_user, family_id
from app.validators import sanitize_string, validate_date, validate_choice

family_bp = Blueprint("family", __name__)


def _check_admin():
    """检查当前用户是否为管理员，返回 role 字符串或 None"""
    user = current_user()
    if not user:
        return None
    fm = FamilyMember.query.filter_by(user_id=user.id, family_id=family_id()).first()
    return fm.role if fm else None


@family_bp.route("/info", methods=["GET"])
@jwt_required()
def family_info():
    """获取家庭信息"""
    fid = family_id()
    family = Family.query.get(fid)
    if not family:
        return jsonify({"msg": "家庭不存在"}), 404
    members = [m.to_dict() for m in family.members]
    return jsonify({
        "family": family.to_dict(),
        "members": members,
    }), 200


@family_bp.route("/invite-code", methods=["GET"])
@jwt_required()
def get_invite_code():
    """获取邀请码（仅管理员）"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可查看邀请码"}), 403
    family = Family.query.get(family_id())
    return jsonify({"invite_code": family.invite_code}), 200


@family_bp.route("/invite-code", methods=["POST"])
@jwt_required()
def regenerate_invite_code():
    """重新生成邀请码（仅管理员）"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可操作"}), 403
    import random, string
    family = Family.query.get(family_id())
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    while Family.query.filter_by(invite_code=code).first():
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    family.invite_code = code
    db.session.commit()
    return jsonify({"invite_code": code}), 200


@family_bp.route("/members/<int:member_id>/role", methods=["PUT"])
@jwt_required()
def update_member_role(member_id):
    """修改成员角色（仅管理员）"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可操作"}), 403
    fm = FamilyMember.query.filter_by(id=member_id, family_id=family_id()).first()
    if not fm:
        return jsonify({"msg": "成员不存在"}), 404
    try:
        role = validate_choice(
            ((request.get_json() or {}).get("role") or "").strip(),
            ("admin", "adult", "child"),
        )
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    fm.role = role
    db.session.commit()
    return jsonify({"msg": "角色已更新"}), 200


@family_bp.route("/members/<int:member_id>", methods=["DELETE"])
@jwt_required()
def remove_member(member_id):
    """移出成员（仅管理员，不可移出自己）"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可操作"}), 403
    fm = FamilyMember.query.filter_by(id=member_id, family_id=family_id()).first()
    if not fm:
        return jsonify({"msg": "成员不存在"}), 404
    if fm.user_id == current_user().id:
        return jsonify({"msg": "不能移出自己"}), 400
    member_name = fm.user.nickname or fm.user.username
    db.session.delete(fm)
    db.session.flush()
    feed = Feed(family_id=family_id(), user_id=current_user().id,
                content=f"{member_name} 已被移出家庭", type="member")
    db.session.add(feed)
    db.session.commit()
    return jsonify({"msg": "成员已移出"}), 200


@family_bp.route("/members/<int:member_id>/profile", methods=["PUT"])
@jwt_required()
def admin_update_member(member_id):
    """管理员修改任何成员的信息"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可操作"}), 403
    fm = FamilyMember.query.filter_by(id=member_id, family_id=family_id()).first()
    if not fm:
        return jsonify({"msg": "成员不存在"}), 404
    user = fm.user
    data = request.get_json() or {}
    try:
        if "nickname" in data:
            user.nickname = sanitize_string(data["nickname"], max_length=100)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    if "email" in data:
        email = data["email"].strip()
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return jsonify({"msg": "邮箱已被使用"}), 409
        user.email = email
    try:
        if "birthday" in data:
            if data["birthday"]:
                user.birthday = validate_date(data["birthday"])
            else:
                user.birthday = None
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"].strip()
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200


@family_bp.route("/members/<int:member_id>/password", methods=["PUT"])
@jwt_required()
def admin_reset_password(member_id):
    """管理员重置成员密码（无需旧密码）"""
    if _check_admin() != "admin":
        return jsonify({"msg": "仅管理员可操作"}), 403
    fm = FamilyMember.query.filter_by(id=member_id, family_id=family_id()).first()
    if not fm:
        return jsonify({"msg": "成员不存在"}), 404
    data = request.get_json() or {}
    new_password = data.get("new_password") or ""
    if len(new_password) < 6:
        return jsonify({"msg": "新密码至少6位"}), 400
    fm.user.password_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
    db.session.commit()
    return jsonify({"msg": "密码已重置"}), 200


@family_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """更新个人信息（昵称、生日、头像）"""
    user = current_user()
    data = request.get_json() or {}
    try:
        if "nickname" in data:
            user.nickname = sanitize_string(data["nickname"], max_length=100)
        if "birthday" in data:
            if data["birthday"]:
                user.birthday = validate_date(data["birthday"])
            else:
                user.birthday = None
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"].strip()
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200


@family_bp.route("/leave", methods=["POST"])
@jwt_required()
def leave_family():
    """退出家庭"""
    user = current_user()
    fid = family_id()
    fm = FamilyMember.query.filter_by(user_id=user.id, family_id=fid).first()
    if not fm:
        return jsonify({"msg": "不在任何家庭中"}), 400
    if fm.role == "admin":
        # 检查是否还有其他管理员
        other_admins = FamilyMember.query.filter(
            FamilyMember.family_id == fid,
            FamilyMember.role == "admin",
            FamilyMember.id != fm.id
        ).count()
        if other_admins == 0:
            return jsonify({"msg": "你是唯一的管理员，请先将管理员权限转移给其他成员"}), 400
    nickname = user.nickname or user.username
    db.session.delete(fm)
    db.session.flush()
    feed = Feed(family_id=fid, user_id=user.id, content=f"{nickname} 退出了家庭", type="member")
    db.session.add(feed)
    db.session.commit()
    return jsonify({"msg": "已退出家庭"}), 200
