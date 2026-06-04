"""笔记/Wiki、食谱、留言板"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Note, Recipe, Message, FamilyMember
from app.pagination import get_pagination_params, paginate_query
from app.utils import current_user, family_id
from app.validators import validate_required, sanitize_string

notes_bp = Blueprint("notes", __name__)


# ─── 笔记/Wiki ──────────────────────────────────────────

@notes_bp.route("/wiki", methods=["GET"])
@jwt_required()
def list_wiki():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    page, per_page = get_pagination_params()
    query = Note.query.filter_by(family_id=family_id())
    if q:
        query = query.filter(Note.title.contains(q) | Note.content_md.contains(q))
    if cat:
        query = query.filter_by(category=cat)
    query = query.order_by(Note.updated_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        "notes": [n.to_dict() for n in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@notes_bp.route("/wiki", methods=["POST"])
@jwt_required()
def create_wiki():
    data = request.get_json() or {}
    try:
        validate_required(data, ["title"])
        title = sanitize_string(data["title"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    note = Note(
        family_id=family_id(),
        author_id=current_user().id,
        title=title,
        content_md=data.get("content_md", ""),
        category=data.get("category", ""),
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({"note": note.to_dict()}), 201


@notes_bp.route("/wiki/<int:note_id>", methods=["PUT"])
@jwt_required()
def update_wiki(note_id):
    note = Note.query.filter_by(id=note_id, family_id=family_id()).first()
    if not note:
        return jsonify({"msg": "笔记不存在"}), 404
    data = request.get_json() or {}
    for field in ("title", "content_md", "category"):
        if field in data:
            setattr(note, field, data[field])
    db.session.commit()
    return jsonify({"note": note.to_dict()}), 200


@notes_bp.route("/wiki/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_wiki(note_id):
    note = Note.query.filter_by(id=note_id, family_id=family_id()).first()
    if not note:
        return jsonify({"msg": "笔记不存在"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 食谱 ───────────────────────────────────────────────

@notes_bp.route("/recipes", methods=["GET"])
@jwt_required()
def list_recipes():
    q = request.args.get("q", "").strip()
    page, per_page = get_pagination_params()
    query = Recipe.query.filter_by(family_id=family_id())
    if q:
        query = query.filter(Recipe.name.contains(q))
    query = query.order_by(Recipe.created_at.desc())
    result = paginate_query(query, page, per_page)
    return jsonify({
        "recipes": [r.to_dict() for r in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@notes_bp.route("/recipes", methods=["POST"])
@jwt_required()
def create_recipe():
    data = request.get_json() or {}
    try:
        validate_required(data, ["name"])
        name = sanitize_string(data["name"], max_length=200)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    recipe = Recipe(
        family_id=family_id(),
        author_id=current_user().id,
        name=name,
        ingredients=data.get("ingredients", ""),
        steps=data.get("steps", ""),
        image_url=data.get("image_url", ""),
    )
    db.session.add(recipe)
    db.session.commit()
    return jsonify({"recipe": recipe.to_dict()}), 201


@notes_bp.route("/recipes/<int:recipe_id>", methods=["PUT"])
@jwt_required()
def update_recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id, family_id=family_id()).first()
    if not recipe:
        return jsonify({"msg": "食谱不存在"}), 404
    data = request.get_json() or {}
    for field in ("name", "ingredients", "steps", "image_url"):
        if field in data:
            setattr(recipe, field, data[field])
    db.session.commit()
    return jsonify({"recipe": recipe.to_dict()}), 200


@notes_bp.route("/recipes/<int:recipe_id>", methods=["DELETE"])
@jwt_required()
def delete_recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id, family_id=family_id()).first()
    if not recipe:
        return jsonify({"msg": "食谱不存在"}), 404
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200


# ─── 留言板 ─────────────────────────────────────────────

@notes_bp.route("/messages", methods=["GET"])
@jwt_required()
def list_messages():
    # 顶层留言（没有 parent_id），按最新回复排序
    msgs = Message.query.filter_by(family_id=family_id(), parent_id=None).order_by(Message.created_at.desc()).all()
    result = []
    for m in msgs:
        d = m.to_dict()
        d["replies"] = [r.to_dict() for r in sorted(m.replies, key=lambda r: r.created_at)]
        result.append(d)
    return jsonify({"messages": result}), 200


@notes_bp.route("/messages", methods=["POST"])
@jwt_required()
def create_message():
    data = request.get_json() or {}
    try:
        validate_required(data, ["content"])
        content = sanitize_string(data["content"], max_length=5000)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    msg = Message(
        family_id=family_id(),
        author_id=current_user().id,
        content=content,
        parent_id=data.get("parent_id"),
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": msg.to_dict()}), 201


@notes_bp.route("/messages/<int:msg_id>", methods=["DELETE"])
@jwt_required()
def delete_message(msg_id):
    msg = Message.query.filter_by(id=msg_id, family_id=family_id()).first()
    if not msg:
        return jsonify({"msg": "留言不存在"}), 404
    if msg.author_id != current_user().id:
        fm = FamilyMember.query.filter_by(user_id=current_user().id, family_id=family_id()).first()
        if not fm or fm.role != "admin":
            return jsonify({"msg": "无权删除"}), 403
    db.session.delete(msg)
    db.session.commit()
    return jsonify({"msg": "已删除"}), 200
