"""Python 3.6 兼容：fromisoformat 在 3.7 才引入"""
from datetime import datetime, date


def parse_iso_datetime(s):
    """解析 ISO datetime 字符串（兼容 <input type="datetime-local">）"""
    s = s.strip() if hasattr(s, 'strip') else s
    if not s:
        raise ValueError("empty datetime string")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {s}")


def parse_iso_date(s):
    """解析 ISO date 字符串 YYYY-MM-DD"""
    s = s.strip() if hasattr(s, 'strip') else s
    if not s:
        raise ValueError("empty date string")
    return datetime.strptime(s, "%Y-%m-%d").date()
