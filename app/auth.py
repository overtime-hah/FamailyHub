"""认证蓝图：注册、登录、token刷新"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, Family, FamilyMember, Feed
from app.validators import validate_required, validate_email, sanitize_string
from app.security import rate_limiter, get_client_ip, log_security_event

auth_bp = Blueprint("auth", __name__)


def _create_feed(family_id, user_id, content, feed_type="info"):
    """在家庭动态流中添加一条记录"""
    feed = Feed(family_id=family_id, user_id=user_id, content=content, type=feed_type)
    db.session.add(feed)


@auth_bp.route("/register", methods=["POST"])
def register():
    """注册新用户，可同时创建家庭或加入现有家庭"""
    ip = get_client_ip()

    # 速率限制：1小时内最多3次注册尝试
    if rate_limiter.is_rate_limited(f"register:{ip}", max_attempts=3, window_seconds=3600):
        log_security_event("REGISTER_RATE_LIMITED", f"IP {ip} exceeded register rate limit")
        return jsonify({"msg": "注册尝试过于频繁，请1小时后重试"}), 429

    data = request.get_json() or {}
    try:
        validate_required(data, ["username", "email", "password"])
        username = sanitize_string(data["username"], max_length=100)
        email = validate_email(data["email"])
        password = sanitize_string(data["password"], max_length=200)
        nickname = sanitize_string(data.get("nickname") or username, max_length=100)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    invite_code = (data.get("invite_code") or "").strip()

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "用户名已存在"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "邮箱已被注册"}), 409
    if len(password) < 6:
        return jsonify({"msg": "密码至少6位"}), 400

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        nickname=nickname,
    )
    db.session.add(user)
    db.session.flush()

    if invite_code:
        # 加入现有家庭
        family = Family.query.filter_by(invite_code=invite_code.upper()).first()
        if not family:
            db.session.rollback()
            return jsonify({"msg": "邀请码无效"}), 404
        fm = FamilyMember(user_id=user.id, family_id=family.id, role="adult")
        db.session.add(fm)
        db.session.flush()
        _create_feed(family.id, user.id, f"{nickname} 通过邀请码加入了家庭", "member")
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"family_id": family.id})
        return jsonify({"msg": "加入家庭成功", "access_token": token, "user": user.to_dict()}), 201
    else:
        # 创建新家庭
        import random, string
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # 确保邀请码唯一
        while Family.query.filter_by(invite_code=code).first():
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        family_name = (data.get("family_name") or "").strip() or f"{nickname}的家"
        family = Family(name=family_name, invite_code=code)
        db.session.add(family)
        db.session.flush()
        fm = FamilyMember(user_id=user.id, family_id=family.id, role="admin")
        db.session.add(fm)
        db.session.flush()
        _create_feed(family.id, user.id, f"欢迎 {nickname} 创建了「{family_name}」！", "announcement")
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"family_id": family.id})
        return jsonify({"msg": "创建家庭成功", "access_token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    ip = get_client_ip()

    # 速率限制：5分钟内最多5次登录尝试
    if rate_limiter.is_rate_limited(f"login:{ip}", max_attempts=5, window_seconds=300):
        log_security_event("LOGIN_RATE_LIMITED", f"IP {ip} exceeded login rate limit")
        return jsonify({"msg": "登录尝试过于频繁，请5分钟后重试"}), 429

    data = request.get_json() or {}
    try:
        validate_required(data, ["username", "password"])
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    # 限制输入长度
    if len(username) > 80 or len(password) > 128:
        return jsonify({"msg": "输入内容过长"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        log_security_event("LOGIN_FAILED", f"username={username}")
        return jsonify({"msg": "用户名或密码错误"}), 401

    family_id = user.family_id
    if not family_id:
        return jsonify({"msg": "你尚未加入任何家庭"}), 403

    # 登录成功，清除该 IP 的登录速率限制记录
    rate_limiter.clear(f"login:{ip}")

    token = create_access_token(identity=str(user.id), additional_claims={"family_id": family_id})
    log_security_event("LOGIN_SUCCESS", f"username={username}", user_id=user.id)
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required()
def refresh():
    """刷新 token"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.family_id:
        return jsonify({"msg": "用户无效"}), 401
    token = create_access_token(identity=str(user.id), additional_claims={"family_id": user.family_id})
    return jsonify({"access_token": token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/password", methods=["PUT"])
@jwt_required()
def change_password():
    """修改自己的密码"""
    user_id = int(get_jwt_identity())
    ip = get_client_ip()

    # 速率限制：1小时内最多5次密码修改尝试
    if rate_limiter.is_rate_limited(f"pwd_change:{ip}", max_attempts=5, window_seconds=3600):
        log_security_event("PWD_CHANGE_RATE_LIMITED", f"IP {ip} exceeded password change rate limit", user_id=user_id)
        return jsonify({"msg": "密码修改尝试过于频繁，请1小时后重试"}), 429

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    data = request.get_json() or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    if not old_password or not new_password:
        return jsonify({"msg": "旧密码和新密码不能为空"}), 400

    # 限制输入长度
    if len(old_password) > 128 or len(new_password) > 128:
        return jsonify({"msg": "输入内容过长"}), 400

    if not check_password_hash(user.password_hash, old_password):
        log_security_event("PWD_CHANGE_FAILED", "wrong old password", user_id=user_id)
        return jsonify({"msg": "旧密码错误"}), 401
    if len(new_password) < 6:
        return jsonify({"msg": "新密码至少6位"}), 400
    user.password_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
    db.session.commit()
    log_security_event("PWD_CHANGE_SUCCESS", "password changed", user_id=user_id)
    return jsonify({"msg": "密码已修改"}), 200
