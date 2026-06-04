"""变更日志管理器 - 自动记录变更并清理超过30天的旧日志"""
import os
import json
import glob
from datetime import datetime, timedelta

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
CHANGELOG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CHANGELOG.md")
MAX_AGE_DAYS = 30


def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_change(action, detail="", author="system"):
    """记录一次变更到当天的日志文件和 CHANGELOG.md

    Args:
        action: 变更类型 (created, modified, deleted, fixed, added)
        detail: 变更描述
        author: 操作者
    """
    _ensure_dir()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    timestamp = now.isoformat()

    # 写入当天的 JSON 日志
    log_file = os.path.join(LOG_DIR, f"{date_str}.json")
    entries = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            entries = []

    entry = {
        "timestamp": timestamp,
        "action": action,
        "detail": detail,
        "author": author,
    }
    entries.append(entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # 追加到 CHANGELOG.md（仅记录概要，当天的不重复添加日期标题）
    _append_changelog(date_str, action, detail)

    # 自动清理超过 30 天的旧日志
    _cleanup_old_logs()


def _append_changelog(date_str, action, detail):
    """向 CHANGELOG.md 追加一条记录，同一天内的记录不重复写日期标题"""
    today_header = f"## [{date_str}]"
    emoji_map = {
        "created": "➕", "added": "✨", "modified": "🔧",
        "fixed": "🐛", "deleted": "🗑️", "updated": "📦",
    }
    emoji = emoji_map.get(action, "📝")

    # 检查 CHANGELOG 是否已有今天的标题
    try:
        with open(CHANGELOG, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, IOError):
        content = ""

    line = f"- {emoji} **{action}**: {detail}  \n"

    if today_header in content:
        # 在今天的标题段落末尾追加
        # 找到今天标题的位置，在下一个标题之前插入
        lines = content.split("\n")
        insert_idx = None
        in_today = False
        for i, ln in enumerate(lines):
            if ln.strip() == today_header:
                in_today = True
                continue
            if in_today and ln.startswith("## [") and today_header not in ln:
                insert_idx = i
                break
        if insert_idx is None:
            insert_idx = len(lines)
        lines.insert(insert_idx, line.rstrip("\n"))
        with open(CHANGELOG, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    else:
        # 新增今天的标题段落
        if "---" in content:
            # 在最后的分隔线之前插入
            parts = content.rsplit("---", 1)
            new_section = f"\n{today_header}\n\n{line}\n"
            content = parts[0].rstrip() + new_section + "---" + parts[1] if len(parts) > 1 else parts[0] + new_section + "---"
        else:
            content = content.rstrip() + f"\n\n{today_header}\n\n{line}\n"
        with open(CHANGELOG, "w", encoding="utf-8") as f:
            f.write(content)


def _cleanup_old_logs():
    """删除超过 MAX_AGE_DAYS 天的日志文件"""
    _ensure_dir()
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    pattern = os.path.join(LOG_DIR, "*.json")
    for filepath in glob.glob(pattern):
        basename = os.path.basename(filepath)
        try:
            file_date = datetime.strptime(basename.replace(".json", ""), "%Y-%m-%d")
            if file_date < cutoff:
                os.remove(filepath)
                print(f"[LogManager] Cleaned up old log: {basename}")
        except ValueError:
            pass  # 文件名不是日期格式，跳过


def get_recent_logs(days=7):
    """获取最近 N 天的变更日志列表"""
    _ensure_dir()
    cutoff = datetime.now() - timedelta(days=days)
    logs = {}
    pattern = os.path.join(LOG_DIR, "*.json")
    for filepath in sorted(glob.glob(pattern), reverse=True):
        basename = os.path.basename(filepath)
        try:
            file_date = datetime.strptime(basename.replace(".json", ""), "%Y-%m-%d")
            if file_date >= cutoff:
                with open(filepath, "r", encoding="utf-8") as f:
                    logs[basename] = json.load(f)
        except (ValueError, json.JSONDecodeError, IOError):
            pass
    return logs


def init_log():
    """项目启动时运行：清理旧日志，记录启动事件"""
    _ensure_dir()
    _cleanup_old_logs()
    # 记录启动事件（仅在当天首次启动时）
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{today}.json")
    if not os.path.exists(log_file):
        log_change("added", "FamilyHub 服务启动", "system")
    print(f"[LogManager] Log system initialized. Log directory: {LOG_DIR}")
