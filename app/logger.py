"""调试日志管理器 — 按日切片，保留7天

日志文件命名: logs/debug-YYYY-MM-DD.log
内容示例:
  [2026-06-03 14:22:31] INFO  POST /api/auth/login -> 200 | 0.035s | IP=127.0.0.1 | User=None | Body={"username":"admin"}
  [2026-06-03 14:22:32] INFO  GET /api/family/info -> 200 | 0.012s | IP=127.0.0.1 | User=1
  [2026-06-03 14:22:33] ERROR GET /api/tasks/999 -> 404 | 0.008s | IP=127.0.0.1 | User=1
"""
import os
import re
import logging
import glob
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
DEBUG_LOG_PREFIX = "debug"
MAX_LOG_DAYS = 7


def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _cleanup_old_logs():
    """删除超过 MAX_LOG_DAYS 天的调试日志文件"""
    _ensure_dir()
    cutoff = datetime.now() - timedelta(days=MAX_LOG_DAYS)
    pattern = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}-*.log")
    for filepath in glob.glob(pattern):
        basename = os.path.basename(filepath)
        try:
            # 文件名格式: debug-YYYY-MM-DD.log 或 debug-YYYY-MM-DD.log.1
            date_part = basename.split("-", 1)[1].split(".")[0]  # "YYYY-MM-DD"
            file_date = datetime.strptime(date_part, "%Y-%m-%d")
            if file_date < cutoff:
                os.remove(filepath)
                print(f"[Logger] Cleaned up old debug log: {basename}")
        except (ValueError, IndexError):
            pass


def setup_logging(app):
    """为 Flask 应用配置调试日志

    - 控制台输出: INFO 级别（带颜色）
    - 文件输出: DEBUG 级别，按日切片，保留 7 天
    """
    _ensure_dir()
    _cleanup_old_logs()

    # ── 日志格式 ─────────────────────────────────────
    # 文件格式: 完整信息
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # 控制台格式: 简洁
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S"
    )

    # ── 文件处理器: 按日切片 ─────────────────────────
    # 文件名: logs/debug.log（当天）
    # 切片后: logs/debug-2026-06-03.log
    log_file = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}.log")
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=MAX_LOG_DAYS,
        encoding="utf-8"
    )
    # 切片后的文件名格式: debug-2026-06-03.log
    file_handler.suffix = "%Y-%m-%d"
    file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # ── 控制台处理器 ────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # ── 配置 Flask logger ───────────────────────────
    # 清除 Flask 默认的 handler，避免重复输出
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    # 设置日志级别: DEBUG 以捕获所有信息
    app.logger.setLevel(logging.DEBUG)

    # 同时配置 werkzeug 的日志（Flask 内部 HTTP 日志）
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)

    app.logger.debug("=" * 60)
    app.logger.debug("FamilyHub 调试日志系统已启动")
    app.logger.debug(f"日志目录: {LOG_DIR}")
    app.logger.debug(f"日志保留: {MAX_LOG_DAYS} 天")
    app.logger.debug("=" * 60)


def get_debug_logs(date_str=None):
    """读取指定日期的调试日志（默认今天）

    Args:
        date_str: 日期字符串 "YYYY-MM-DD"，默认今天

    Returns:
        日志内容字符串列表
    """
    _ensure_dir()
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 今天的日志在 debug.log，历史日志在 debug-YYYY-MM-DD.log
    today = datetime.now().strftime("%Y-%m-%d")
    if date_str == today:
        log_file = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}.log")
    else:
        log_file = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}-{date_str}.log")

    if not os.path.exists(log_file):
        return []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return f.readlines()
    except IOError:
        return []


def list_debug_log_dates():
    """列出所有可用的调试日志日期

    Returns:
        日期字符串列表 ["2026-06-03", "2026-06-02", ...]
    """
    _ensure_dir()
    dates = []

    # 当天日志
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}.log")
    if os.path.exists(today_file) and os.path.getsize(today_file) > 0:
        dates.append(today)

    # 历史日志
    pattern = os.path.join(LOG_DIR, f"{DEBUG_LOG_PREFIX}-*.log")
    for filepath in sorted(glob.glob(pattern), reverse=True):
        basename = os.path.basename(filepath)
        try:
            date_part = basename.split("-", 1)[1].split(".")[0]
            datetime.strptime(date_part, "%Y-%m-%d")  # 验证格式
            if date_part not in dates:
                dates.append(date_part)
        except (ValueError, IndexError):
            pass

    return sorted(dates, reverse=True)
