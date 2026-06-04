"""FamilyHub 数据模型"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


def _utcnow():
    """返回当前 UTC 时间"""
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(50), default="")
    birthday = db.Column(db.Date, nullable=True)
    avatar_url = db.Column(db.String(512), default="")

    memberships = db.relationship("FamilyMember", back_populates="user", lazy="select")
    feed_items = db.relationship("Feed", back_populates="user", lazy="select")
    tasks_assigned = db.relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee", lazy="select")
    wishes = db.relationship("Wish", back_populates="user", lazy="select")
    locations = db.relationship("Location", back_populates="user", lazy="select")
    health_records = db.relationship("HealthRecord", back_populates="user", lazy="select")

    @property
    def family_id(self):
        m = self.memberships[0] if self.memberships else None
        return m.family_id if m else None

    @property
    def role(self):
        m = self.memberships[0] if self.memberships else None
        return m.role if m else None

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nickname": self.nickname or self.username,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "avatar_url": self.avatar_url or "",
            "family_id": self.family_id,
            "role": self.role,
        }


class Family(db.Model):
    __tablename__ = "families"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    members = db.relationship("FamilyMember", back_populates="family", lazy="select")
    feed_items = db.relationship("Feed", back_populates="family", lazy="select")
    events = db.relationship("CalendarEvent", back_populates="family", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "invite_code": self.invite_code,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members),
        }


class FamilyMember(db.Model):
    __tablename__ = "family_members"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    role = db.Column(db.String(20), default="adult")  # admin, adult, child
    joined_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="memberships")
    family = db.relationship("Family", back_populates="members")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "family_id": self.family_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
            "user": self.user.to_dict() if self.user else None,
        }


class Feed(db.Model):
    __tablename__ = "feeds"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default="info")  # announcement, member, event, task, photo, info
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="feed_items")
    family = db.relationship("Family", back_populates="feed_items")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "content": self.content,
            "type": self.type,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat(),
        }


class CalendarEvent(db.Model):
    __tablename__ = "calendar_events"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    all_day = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(200), default="")
    description = db.Column(db.Text, default="")
    repeat_rule = db.Column(db.String(20), default="none")  # none, daily, weekly, monthly, yearly
    color = db.Column(db.String(20), default="#007aff")
    created_at = db.Column(db.DateTime, default=_utcnow)

    creator = db.relationship("User")
    family = db.relationship("Family", back_populates="events")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "creator_id": self.creator_id,
            "creator_name": self.creator.nickname or self.creator.username if self.creator else "",
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "all_day": self.all_day,
            "location": self.location or "",
            "description": self.description or "",
            "repeat_rule": self.repeat_rule,
            "color": self.color,
            "created_at": self.created_at.isoformat(),
        }


class ShoppingItem(db.Model):
    __tablename__ = "shopping_items"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(100), default="1")
    bought = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    adder = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "added_by": self.added_by,
            "adder_name": self.adder.nickname or self.adder.username if self.adder else "",
            "name": self.name,
            "quantity": self.quantity,
            "bought": self.bought,
            "created_at": self.created_at.isoformat(),
        }


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    creator = db.relationship("User", foreign_keys=[creator_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id], back_populates="tasks_assigned")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "creator_id": self.creator_id,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee.nickname or self.assignee.username if self.assignee else "",
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }


class Wish(db.Model):
    __tablename__ = "wishes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(512), default="")
    note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="wishes")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "family_id": self.family_id,
            "name": self.name,
            "link": self.link or "",
            "note": self.note or "",
            "created_at": self.created_at.isoformat(),
        }


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_md = db.Column(db.Text, default="")
    category = db.Column(db.String(50), default="")  # 家电, 急救, WiFi, 其他
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    author = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "author_id": self.author_id,
            "author_name": self.author.nickname or self.author.username if self.author else "",
            "title": self.title,
            "content_md": self.content_md,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, default="")
    steps = db.Column(db.Text, default="")
    image_url = db.Column(db.String(512), default="")
    created_at = db.Column(db.DateTime, default=_utcnow)

    author = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "author_id": self.author_id,
            "author_name": self.author.nickname or self.author.username if self.author else "",
            "name": self.name,
            "ingredients": self.ingredients,
            "steps": self.steps,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
        }


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    author = db.relationship("User")
    replies = db.relationship("Message", backref=db.backref("parent", remote_side=[id]), lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "author_id": self.author_id,
            "author_name": self.author.nickname or self.author.username if self.author else "",
            "content": self.content,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "reply_count": len(self.replies),
        }


class Album(db.Model):
    __tablename__ = "albums"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    creator = db.relationship("User")
    photos = db.relationship("Photo", back_populates="album", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "creator_id": self.creator_id,
            "creator_name": self.creator.nickname or self.creator.username if self.creator else "",
            "name": self.name,
            "photo_count": len(self.photos),
            "created_at": self.created_at.isoformat(),
        }


class Photo(db.Model):
    __tablename__ = "photos"
    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default="")
    taken_at = db.Column(db.DateTime, nullable=True)
    upload_time = db.Column(db.DateTime, default=_utcnow)

    album = db.relationship("Album", back_populates="photos")
    uploader = db.relationship("User")
    comments = db.relationship("PhotoComment", back_populates="photo", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "album_id": self.album_id,
            "album_name": self.album.name if self.album else "",
            "uploader_id": self.uploader_id,
            "uploader_name": self.uploader.nickname or self.uploader.username if self.uploader else "",
            "filename": self.filename,
            "url": f"/uploads/{self.filename}",
            "description": self.description or "",
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "upload_time": self.upload_time.isoformat(),
            "comment_count": len(self.comments),
        }


class PhotoComment(db.Model):
    __tablename__ = "photo_comments"
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User")
    photo = db.relationship("Photo", back_populates="comments")

    def to_dict(self):
        return {
            "id": self.id,
            "photo_id": self.photo_id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }


class Folder(db.Model):
    __tablename__ = "folders"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    files = db.relationship("UserFile", back_populates="folder", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "name": self.name,
            "file_count": len(self.files),
            "created_at": self.created_at.isoformat(),
        }


class UserFile(db.Model):
    __tablename__ = "user_files"
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    size = db.Column(db.Integer, default=0)  # bytes
    upload_time = db.Column(db.DateTime, default=_utcnow)

    folder = db.relationship("Folder", back_populates="files")
    uploader = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "folder_id": self.folder_id,
            "folder_name": self.folder.name if self.folder else "",
            "uploader_id": self.uploader_id,
            "uploader_name": self.uploader.nickname or self.uploader.username if self.uploader else "",
            "filename": self.filename,
            "original_name": self.original_name,
            "size": self.size,
            "url": f"/uploads/{self.filename}",
            "upload_time": self.upload_time.isoformat(),
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # income, expense
    category = db.Column(db.String(50), nullable=False)  # 餐饮, 交通, 购物, 医疗, 工资, 其他
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200), default="")
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "note": self.note,
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class BillReminder(db.Model):
    __tablename__ = "bill_reminders"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, default=0)
    due_day = db.Column(db.Integer, nullable=False)  # day of month
    last_reminded = db.Column(db.Date, nullable=True)

    creator = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "amount": self.amount,
            "due_day": self.due_day,
            "last_reminded": self.last_reminded.isoformat() if self.last_reminded else None,
        }


class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="locations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "family_id": self.family_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthRecord(db.Model):
    __tablename__ = "health_records"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # height, weight, blood_pressure, vaccine
    value = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), default="")
    record_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="health_records")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.nickname or self.user.username if self.user else "",
            "family_id": self.family_id,
            "record_type": self.record_type,
            "value": self.value,
            "unit": self.unit,
            "record_date": self.record_date.isoformat(),
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class Pet(db.Model):
    __tablename__ = "pets"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(100), default="")
    deworming_date = db.Column(db.Date, nullable=True)
    vaccine_date = db.Column(db.Date, nullable=True)
    note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "family_id": self.family_id,
            "name": self.name,
            "species": self.species,
            "deworming_date": self.deworming_date.isoformat() if self.deworming_date else None,
            "vaccine_date": self.vaccine_date.isoformat() if self.vaccine_date else None,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }
