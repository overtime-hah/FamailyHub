"""文件柜"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.models import db, Folder, UserFile
from app.utils import current_user, family_id

files_bp = Blueprint("files", __name__)

# 额外允许的文件扩展名（与 config.py 中的 ALLOWED_EXTENSIONS 合并使用）
_EXTRA_ALLOWED = {"doc", "docx", "xls", "xlsx", "pdf", "png", "jpg", "jpeg", "gif", "zip", "txt"}


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", set())
    return ext in allowed or ext in _EXTRA_ALLOWED


# ─── 文件夹 ─────────────────────────────────────────────

@files_bp.route("/folders", methods=["GET"])
@jwt_required()
def list_folders():
    folders = Folder.query.filter_by(family_id=family_id()).order_by(Folder.created_at.asc()).all()
    return jsonify({"folders": [f.to_dict() for f in folders]}), 200


@files_bp.route("/folders", methods=["POST"])
@jwt_required()
def create_folder():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"msg": "名称不能为空"}), 400
    folder = Folder(family_id=family_id(), name=name)
    db.session.add(folder)
    db.session.commit()
    return jsonify({"folder": folder.to_dict()}), 201


@files_bp.route("/folders/<int:folder_id>", methods=["DELETE"])
@jwt_required()
def delete_folder(folder_id):
    folder = Folder.query.filter_by(id=folder_id, family_id=family_id()).first()
    if not folder:
        return jsonify({"msg": "文件夹不存在"}), 404
    # 删除关联文件
    for f in folder.files:
        _remove_file(f.filename)
        db.session.delete(f)
    db.session.delete(folder)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


def _remove_file(filename):
    try:
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        current_app.logger.warning(f"Failed to remove file {filename}: {e}")


# ─── 文件 ───────────────────────────────────────────────

@files_bp.route("/folders/<int:folder_id>/files", methods=["GET"])
@jwt_required()
def list_files(folder_id):
    files = UserFile.query.filter_by(folder_id=folder_id).order_by(UserFile.upload_time.desc()).all()
    return jsonify({"files": [f.to_dict() for f in files]}), 200


@files_bp.route("/folders/<int:folder_id>/files", methods=["POST"])
@jwt_required()
def upload_file(folder_id):
    folder = Folder.query.filter_by(id=folder_id, family_id=family_id()).first()
    if not folder:
        return jsonify({"msg": "文件夹不存在"}), 404

    uploaded = request.files.getlist("files")
    if not uploaded or not any(f.filename for f in uploaded):
        return jsonify({"msg": "请选择文件"}), 400

    results = []
    for f in uploaded:
        if not f.filename or not _allowed_file(f.filename):
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower()
        unique_name = f"{uuid.uuid4().hex}_{int(uuid.uuid1().time)}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
        f.save(filepath)
        uf = UserFile(
            folder_id=folder_id,
            uploader_id=current_user().id,
            filename=unique_name,
            original_name=f.filename,
            size=os.path.getsize(filepath),
        )
        db.session.add(uf)
        results.append(uf)
    db.session.commit()
    return jsonify({"files": [r.to_dict() for r in results], "msg": f"上传了 {len(results)} 个文件"}), 201


@files_bp.route("/files/<int:file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    uf = UserFile.query.get(file_id)
    if not uf:
        return jsonify({"msg": "文件不存在"}), 404
    _remove_file(uf.filename)
    db.session.delete(uf)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
