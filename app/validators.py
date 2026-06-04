"""Reusable input validation and sanitization helpers."""
import re
from datetime import date


def sanitize_string(value, max_length=200):
    """Strip whitespace and limit length of a string.

    Returns the cleaned string or raises ValueError.
    """
    if not isinstance(value, str):
        raise ValueError("值必须是字符串")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ValueError(f"长度不能超过 {max_length} 个字符")
    return cleaned


def validate_required(data, fields):
    """Check that all required fields exist and are non-empty in a dict.

    Raises ValueError with a descriptive message listing missing fields.
    """
    if not isinstance(data, dict):
        raise ValueError("请求数据格式无效")
    missing = [f for f in fields if not data.get(f) or not str(data[f]).strip()]
    if missing:
        raise ValueError(f"以下字段不能为空: {', '.join(missing)}")


def validate_email(email):
    """Basic email format validation.

    Returns the cleaned (lowered, stripped) email or raises ValueError.
    """
    if not isinstance(email, str):
        raise ValueError("邮箱必须是字符串")
    cleaned = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, cleaned):
        raise ValueError("邮箱格式无效")
    return cleaned


def validate_amount(value):
    """Validate a positive numeric amount.

    Returns a float or raises ValueError.
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError("金额必须是数字")
    if amount <= 0:
        raise ValueError("金额必须大于零")
    return amount


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string.

    Returns a datetime.date object or raises ValueError.
    Compatible with Python 3.6+ (date.fromisoformat requires 3.7+).
    """
    if not isinstance(date_str, str) or not date_str.strip():
        raise ValueError("日期不能为空")
    cleaned = date_str.strip()
    try:
        from datetime import datetime
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")


def validate_choice(value, choices):
    """Validate that value is in the allowed choices.

    Returns the value or raises ValueError.
    """
    if value not in choices:
        allowed = ", ".join(str(c) for c in choices)
        raise ValueError(f"无效的选项，允许的值: {allowed}")
    return value
