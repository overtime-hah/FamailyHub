"""共享工具函数 — 消除路由文件中的重复代码"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models import User, FamilyMember


def current_user():
    """获取当前登录用户对象"""
    return User.query.get(int(get_jwt_identity()))


def family_id():
    """从 JWT claims 中获取当前家庭 ID"""
    return get_jwt()["family_id"]


def require_admin(fn):
    """装饰器：限制仅管理员可访问的接口"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"msg": "用户不存在"}), 401
        fm = FamilyMember.query.filter_by(
            user_id=user.id, family_id=family_id()
        ).first()
        if not fm or fm.role != "admin":
            return jsonify({"msg": "仅管理员可操作"}), 403
        return fn(*args, **kwargs)
    return wrapper
