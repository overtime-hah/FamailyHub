"""共享日历"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, CalendarEvent, Feed
from app.compat import parse_iso_datetime
from app.utils import current_user, family_id
from app.validators import validate_required, sanitize_string
from datetime import datetime

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/events", methods=["GET"])
@jwt_required()
def list_events():
    """获取指定月份及前后的事件"""
    fid = family_id()
    year = request.args.get("year", type=int, default=datetime.utcnow().year)
    month = request.args.get("month", type=int, default=datetime.utcnow().month)

    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_dt = datetime(year, month, 1)
    end_dt = datetime(year, month, last_day, 23, 59, 59)

    events = CalendarEvent.query.filter(
        CalendarEvent.family_id == fid,
        CalendarEvent.start <= end_dt,
        CalendarEvent.end >= start_dt,
    ).order_by(CalendarEvent.start.asc()).all()

    return jsonify({"events": [e.to_dict() for e in events]}), 200


@calendar_bp.route("/events", methods=["POST"])
@jwt_required()
def create_event():
    """创建日历事件"""
    data = request.get_json() or {}
    try:
        validate_required(data, ["title"])
        title = sanitize_string(data["title"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400

    try:
        start = parse_iso_datetime(data.get("start", ""))
        end = parse_iso_datetime(data.get("end", ""))
    except Exception:
        return jsonify({"msg": "时间格式无效"}), 400

    user = current_user()
    event = CalendarEvent(
        family_id=family_id(),
        creator_id=user.id,
        title=title,
        start=start,
        end=end,
        all_day=data.get("all_day", False),
        location=sanitize_string(data.get("location") or "", max_length=200),
        description=sanitize_string(data.get("description") or "", max_length=2000),
        repeat_rule=data.get("repeat_rule", "none"),
        color=data.get("color", "#007aff"),
    )
    db.session.add(event)
    db.session.flush()
    feed = Feed(family_id=family_id(), user_id=user.id,
                content=f"创建了日历事件「{title}」", type="event")
    db.session.add(feed)
    db.session.commit()
    return jsonify({"event": event.to_dict()}), 201


@calendar_bp.route("/events/<int:event_id>", methods=["PUT"])
@jwt_required()
def update_event(event_id):
    """更新日历事件"""
    event = CalendarEvent.query.filter_by(id=event_id, family_id=family_id()).first()
    if not event:
        return jsonify({"msg": "事件不存在"}), 404

    data = request.get_json() or {}
    if "title" in data:
        event.title = data["title"].strip()
    try:
        if "start" in data:
            event.start = parse_iso_datetime(data["start"])
        if "end" in data:
            event.end = parse_iso_datetime(data["end"])
    except Exception:
        return jsonify({"msg": "时间格式无效"}), 400
    for field in ("all_day", "location", "description", "repeat_rule", "color"):
        if field in data:
            setattr(event, field, data[field])
    db.session.commit()
    return jsonify({"event": event.to_dict()}), 200


@calendar_bp.route("/events/<int:event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    """删除日历事件"""
    event = CalendarEvent.query.filter_by(id=event_id, family_id=family_id()).first()
    if not event:
        return jsonify({"msg": "事件不存在"}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
