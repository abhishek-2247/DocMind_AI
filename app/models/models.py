"""
DocMind AI — SQLAlchemy database models
"""

import os
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


# ── User ──────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    theme = db.Column(db.String(10), default="light")

    documents = db.relationship("Document", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    conversations = db.relationship("Conversation", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: int):
    return db.session.get(User, int(user_id))


# ── Document ──────────────────────────────────────────────────────────────────

class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(10), nullable=False)   # pdf | docx | pptx | txt
    file_size = db.Column(db.Integer, default=0)           # bytes
    page_count = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    reading_time = db.Column(db.Integer, default=0)        # minutes
    content_text = db.Column(db.Text, default="")          # extracted plain text
    ai_tags = db.Column(db.Text, default="")               # comma-separated AI tags
    ai_summary = db.Column(db.Text, default="")
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    messages = db.relationship("Message", backref="document", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def size_human(self) -> str:
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __repr__(self) -> str:
        return f"<Document {self.original_name}>"


# ── Conversation / Message ────────────────────────────────────────────────────

class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), default="New Conversation")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    messages = db.relationship("Message", backref="conversation", lazy="dynamic",
                                cascade="all, delete-orphan", order_by="Message.created_at")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    role = db.Column(db.String(10), nullable=False)    # user | assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
