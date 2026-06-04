"""相册与照片"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.models import db, Album, Photo, PhotoComment, Feed
from app.compat import parse_iso_datetime
from app.utils import current_user, family_id

album_bp = Blueprint("album", __name__)


# ─── 相册 ───────────────────────────────────────────────

@album_bp.route("/albums", methods=["GET"])
@jwt_required()
def list_albums():
    albums = Album.query.filter_by(family_id=family_id()).order_by(Album.created_at.desc()).all()
    return jsonify({"albums": [a.to_dict() for a in albums]}), 200


@album_bp.route("/albums", methods=["POST"])
@jwt_required()
def create_album():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"msg": "名称不能为空"}), 400
    album = Album(family_id=family_id(), creator_id=current_user().id, name=name)
    db.session.add(album)
    db.session.commit()
    return jsonify({"album": album.to_dict()}), 201


@album_bp.route("/albums/<int:album_id>", methods=["DELETE"])
@jwt_required()
def delete_album(album_id):
    album = Album.query.filter_by(id=album_id, family_id=family_id()).first()
    if not album:
        return jsonify({"msg": "相册不存在"}), 404
    # 删除关联照片文件
    for photo in album.photos:
        _remove_photo_file(photo.filename)
    db.session.delete(album)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 照片 ───────────────────────────────────────────────

def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


def _remove_photo_file(filename):
    try:
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        current_app.logger.warning(f"Failed to remove photo file {filename}: {e}")


@album_bp.route("/albums/<int:album_id>/photos", methods=["GET"])
@jwt_required()
def list_photos(album_id):
    photos = Photo.query.filter_by(album_id=album_id).order_by(Photo.upload_time.desc()).all()
    result = []
    for p in photos:
        d = p.to_dict()
        d["comments"] = [c.to_dict() for c in sorted(p.comments, key=lambda c: c.created_at)]
        result.append(d)
    return jsonify({"photos": result}), 200


@album_bp.route("/albums/<int:album_id>/photos", methods=["POST"])
@jwt_required()
def upload_photo(album_id):
    album = Album.query.filter_by(id=album_id, family_id=family_id()).first()
    if not album:
        return jsonify({"msg": "相册不存在"}), 404

    files = request.files.getlist("photos")
    if not files or not any(f.filename for f in files):
        return jsonify({"msg": "请选择文件"}), 400

    photos = []
    for f in files:
        if not f.filename or not _allowed_file(f.filename):
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower()
        unique_name = f"{uuid.uuid4().hex}_{int(uuid.uuid1().time)}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
        f.save(filepath)

        from datetime import datetime
        taken_at = request.form.get("taken_at", None)
        if taken_at:
            try:
                taken_at = parse_iso_datetime(taken_at)
            except Exception:
                taken_at = None

        photo = Photo(
            album_id=album_id,
            uploader_id=current_user().id,
            filename=unique_name,
            description=request.form.get("description", ""),
            taken_at=taken_at,
        )
        db.session.add(photo)
        photos.append(photo)
    if photos:
        db.session.flush()
        feed = Feed(family_id=family_id(), user_id=current_user().id,
                    content=f"向「{album.name}」上传了 {len(photos)} 张照片", type="photo")
        db.session.add(feed)
        db.session.commit()
    return jsonify({"photos": [p.to_dict() for p in photos], "msg": f"上传了 {len(photos)} 张照片"}), 201


@album_bp.route("/photos/<int:photo_id>", methods=["PUT"])
@jwt_required()
def update_photo(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        return jsonify({"msg": "照片不存在"}), 404
    data = request.get_json() or {}
    if "description" in data:
        photo.description = data["description"]
    db.session.commit()
    return jsonify({"photo": photo.to_dict()}), 200


@album_bp.route("/photos/<int:photo_id>", methods=["DELETE"])
@jwt_required()
def delete_photo(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        return jsonify({"msg": "照片不存在"}), 404
    _remove_photo_file(photo.filename)
    db.session.delete(photo)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 照片评论 ───────────────────────────────────────────

@album_bp.route("/photos/<int:photo_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        return jsonify({"msg": "照片不存在"}), 404
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"msg": "评论内容不能为空"}), 400
    c = PhotoComment(photo_id=photo_id, user_id=current_user().id, content=content)
    db.session.add(c)
    db.session.commit()
    return jsonify({"comment": c.to_dict()}), 201
