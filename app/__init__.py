"""FamilyHub 应用工厂"""
import os
import time
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from app.models import db
from app.log_manager import init_log
from app.logger import setup_logging
from app.response import not_found as resp_not_found, server_error as resp_server_error, error as resp_error


def _mask_sensitive(data):
    """对敏感字段（密码、token 等）进行脱敏处理"""
    sensitive_keys = {"password", "old_password", "new_password", "token", "secret", "authorization"}
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if k.lower() in sensitive_keys:
                masked[k] = "***"
            elif isinstance(v, (dict, list)):
                masked[k] = _mask_sensitive(v)
            else:
                masked[k] = v
        return masked
    elif isinstance(data, list):
        return [_mask_sensitive(item) for item in data]
    return data


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化调试日志系统（按日切片，保留7天）
    setup_logging(app)

    # 初始化变更日志系统（自动清理30天前的旧日志）
    init_log()

    # 初始化扩展 — CORS 限制允许的来源
    allowed_origins = os.environ.get("CORS_ORIGINS", "http://127.0.0.1:417,http://localhost:417").split(",")
    CORS(app, supports_credentials=True, origins=allowed_origins)
    db.init_app(app)
    JWTManager(app)

    # ── 全局请求大小限制 ──────────────────────────
    @app.before_request
    def limit_request_size():
        """限制请求体大小为 16 MB"""
        if request.content_length and request.content_length > 16 * 1024 * 1024:
            return jsonify({"msg": "请求体过大"}), 413

    # ── 请求计时 ──────────────────────────────────────
    @app.before_request
    def _start_timer():
        """记录请求开始时间，用于计算耗时"""
        request._start_time = time.time()

    # ── 全局错误处理器（使用统一响应格式）──────────
    @app.errorhandler(404)
    def not_found(e):
        return resp_not_found()

    @app.errorhandler(500)
    def server_error(e):
        return resp_server_error()

    @app.errorhandler(422)
    def unprocessable(e):
        return resp_error(msg="请求参数无效", code=422)

    # 注册蓝图
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.family import family_bp
    app.register_blueprint(family_bp, url_prefix="/api/family")

    from app.routes.feed import feed_bp
    app.register_blueprint(feed_bp, url_prefix="/api/feed")

    from app.routes.calendar import calendar_bp
    app.register_blueprint(calendar_bp, url_prefix="/api/calendar")

    from app.routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")

    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix="/api/notes")

    from app.routes.album import album_bp
    app.register_blueprint(album_bp, url_prefix="/api/album")

    from app.routes.files import files_bp
    app.register_blueprint(files_bp, url_prefix="/api/files")

    from app.routes.finance import finance_bp
    app.register_blueprint(finance_bp, url_prefix="/api/finance")

    from app.routes.location import location_bp
    app.register_blueprint(location_bp, url_prefix="/api/location")

    from app.routes.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api/health")

    # ── 请求日志（详细版）──────────────────────────────
    @app.after_request
    def log_request(response):
        """记录 API 请求的详细调试日志"""
        if not request.path.startswith("/api/"):
            return response

        # 计算请求耗时
        duration = 0
        if hasattr(request, "_start_time"):
            duration = time.time() - request._start_time

        # 获取客户端 IP
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if "," in ip:
            ip = ip.split(",")[0].strip()

        # 获取用户信息（如果已登录）
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
        except Exception:
            pass

        # 构建日志消息
        status = response.status_code
        method = request.method
        path = request.path
        query = f"?{request.query_string.decode()}" if request.query_string else ""

        # 根据状态码选择日志级别
        level = "INFO"
        if status >= 500:
            level = "ERROR"
        elif status >= 400:
            level = "WARNING"

        log_msg = (
            f"{method} {path}{query} -> {status} | "
            f"{duration:.3f}s | IP={ip} | User={user_id}"
        )

        # 记录请求体（仅 POST/PUT/PATCH，且排除文件上传和登录密码）
        if method in ("POST", "PUT", "PATCH"):
            content_type = request.content_type or ""
            if "application/json" in content_type:
                try:
                    body = request.get_json(silent=True)
                    if body:
                        # 脱敏处理：隐藏密码字段
                        safe_body = _mask_sensitive(body)
                        log_msg += f" | Body={safe_body}"
                except Exception:
                    pass

        # 根据级别记录
        if level == "ERROR":
            app.logger.error(log_msg)
        elif level == "WARNING":
            app.logger.warning(log_msg)
        else:
            app.logger.info(log_msg)

        return response

    # ── 健康检查端点 ──────────────────────────────────
    @app.route("/api/ping")
    def health_check():
        return jsonify({"status": "ok", "service": "FamilyHub"})

    # 前端页面路由
    @app.route("/")
    def serve_login():
        from flask import render_template
        return render_template("login.html")

    @app.route("/app")
    def serve_index():
        from flask import render_template
        return render_template("index.html")

    # 上传文件访问
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # 创建表并初始化示例数据
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """插入示例数据（幂等——仅当无数据时才插入）"""
    from app.models import User, Family, FamilyMember, Feed
    from app.models import CalendarEvent, ShoppingItem, Task, Wish, Note
    from app.models import Recipe, Message, Album, Photo, UserFile, Folder
    from app.models import Transaction, BillReminder, Location, HealthRecord, Pet
    from werkzeug.security import generate_password_hash
    from datetime import datetime, timedelta

    if User.query.first():
        return  # 已有数据则跳过

    # ---- 家庭 ----
    family = Family(name="温暖小窝", invite_code="ABC123")
    db.session.add(family)
    db.session.flush()

    # ---- 用户 ----
    admin = User(
        username="admin",
        email="admin@familyhub.local",
        password_hash=generate_password_hash("admin123", method="pbkdf2:sha256"),
        nickname="爸爸",
        avatar_url=""
    )
    user1 = User(
        username="user1",
        email="user1@familyhub.local",
        password_hash=generate_password_hash("user123", method="pbkdf2:sha256"),
        nickname="妈妈",
        avatar_url=""
    )
    child = User(
        username="child1",
        email="child1@familyhub.local",
        password_hash=generate_password_hash("child123", method="pbkdf2:sha256"),
        nickname="小明",
        birthday=datetime(2018, 5, 15).date(),
        avatar_url=""
    )
    db.session.add_all([admin, user1, child])
    db.session.flush()

    # ---- 家庭成员 ----
    db.session.add_all([
        FamilyMember(user_id=admin.id, family_id=family.id, role="admin"),
        FamilyMember(user_id=user1.id, family_id=family.id, role="adult"),
        FamilyMember(user_id=child.id, family_id=family.id, role="child"),
    ])
    db.session.flush()

    # ---- 动态 ----
    now = datetime.utcnow()
    db.session.add_all([
        Feed(family_id=family.id, user_id=admin.id, content="欢迎加入温暖小窝！这是我们的家庭共享空间 🏠", type="announcement", is_pinned=True, created_at=now),
        Feed(family_id=family.id, user_id=user1.id, content="妈妈加入了家庭", type="member", created_at=now - timedelta(minutes=10)),
        Feed(family_id=family.id, user_id=child.id, content="小明加入了家庭", type="member", created_at=now - timedelta(minutes=5)),
    ])

    # ---- 日历事件 ----
    db.session.add_all([
        CalendarEvent(
            family_id=family.id, creator_id=admin.id,
            title="家庭聚餐", start=now + timedelta(days=2), end=now + timedelta(days=2, hours=2),
            all_day=False, location="家里", description="周末家庭聚餐", repeat_rule="none", color="#ff9500"
        ),
        CalendarEvent(
            family_id=family.id, creator_id=user1.id,
            title="小明家长会", start=now + timedelta(days=5, hours=9), end=now + timedelta(days=5, hours=11),
            all_day=False, location="学校", description="期中家长会", repeat_rule="none", color="#007aff"
        ),
    ])

    # ---- 购物清单 ----
    db.session.add_all([
        ShoppingItem(family_id=family.id, added_by=admin.id, name="牛奶", quantity="2瓶", bought=False),
        ShoppingItem(family_id=family.id, added_by=user1.id, name="面包", quantity="1袋", bought=True),
        ShoppingItem(family_id=family.id, added_by=admin.id, name="水果", quantity="若干", bought=False),
    ])

    # ---- 家务待办 ----
    db.session.add_all([
        Task(family_id=family.id, creator_id=admin.id, assignee_id=admin.id, title="倒垃圾", due_date=now.date(), completed=False),
        Task(family_id=family.id, creator_id=user1.id, assignee_id=admin.id, title="修理水龙头", due_date=(now + timedelta(days=3)).date(), completed=False),
        Task(family_id=family.id, creator_id=admin.id, assignee_id=user1.id, title="整理衣柜", due_date=(now + timedelta(days=1)).date(), completed=True),
    ])

    # ---- 心愿单 ----
    db.session.add_all([
        Wish(user_id=admin.id, family_id=family.id, name="机械键盘", link="https://example.com/keyboard", note="Cherry MX 茶轴"),
        Wish(user_id=user1.id, family_id=family.id, name="瑜伽垫", link="https://example.com/mat", note="加厚防滑款"),
    ])

    # ---- 笔记 ----
    db.session.add_all([
        Note(family_id=family.id, author_id=admin.id, title="WiFi 信息", content_md="**WiFi名称**: WarmHome\n**密码**: 12345678\n\n管理地址: http://192.168.1.1", category="家电"),
        Note(family_id=family.id, author_id=user1.id, title="急救电话", content_md="火警: 119\n急救: 120\n报警: 110\n\n小区物业: 8888-1234", category="急救"),
    ])

    # ---- 食谱 ----
    db.session.add_all([
        Recipe(family_id=family.id, author_id=user1.id, name="番茄炒蛋", ingredients="番茄2个, 鸡蛋3个, 盐适量, 糖少许", steps="1. 鸡蛋打散加盐\n2. 番茄切块\n3. 先炒蛋出锅\n4. 炒番茄出汁后加入蛋翻炒", image_url=""),
    ])

    # ---- 留言 ----
    msg1 = Message(family_id=family.id, author_id=admin.id, content="晚上想吃什么？", created_at=now - timedelta(hours=3))
    db.session.add(msg1)
    db.session.flush()  # 获取 msg1.id
    db.session.add_all([
        Message(family_id=family.id, author_id=user1.id, content="火锅怎么样？", parent_id=msg1.id, created_at=now - timedelta(hours=2)),
        Message(family_id=family.id, author_id=child.id, content="好耶！吃火锅！", parent_id=msg1.id, created_at=now - timedelta(hours=1)),
    ])

    # ---- 相册 ----
    album = Album(family_id=family.id, creator_id=admin.id, name="家庭相册")
    db.session.add(album)

    # ---- 文件夹 ----
    db.session.add_all([
        Folder(family_id=family.id, name="医疗"),
        Folder(family_id=family.id, name="教育"),
        Folder(family_id=family.id, name="合同"),
    ])

    # ---- 记账 ----
    db.session.add_all([
        Transaction(family_id=family.id, user_id=admin.id, type="expense", category="餐饮", amount=128.5, note="周末外出吃饭", date=(now - timedelta(days=2)).date()),
        Transaction(family_id=family.id, user_id=user1.id, type="expense", category="购物", amount=350.0, note="超市采购", date=(now - timedelta(days=1)).date()),
        Transaction(family_id=family.id, user_id=admin.id, type="income", category="工资", amount=15000.0, note="月薪", date=now.date()),
    ])

    # ---- 账单提醒 ----
    db.session.add_all([
        BillReminder(family_id=family.id, creator_id=admin.id, title="房租", amount=3500.0, due_day=1),
        BillReminder(family_id=family.id, creator_id=admin.id, title="网费", amount=99.0, due_day=15),
    ])

    # ---- 宠物 ----
    db.session.add(Pet(family_id=family.id, name="毛球", species="英短蓝猫", deworming_date=(now + timedelta(days=30)).date(), vaccine_date=(now + timedelta(days=60)).date(), note="活泼好动"))

    db.session.commit()
    print("[OK] Seed data initialized.")
