"""DocMind AI — Dashboard routes"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Document, Conversation, Message

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    docs = (
        Document.query
        .filter_by(user_id=current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    recent_docs = docs[:5]
    total_docs = len(docs)

    recent_convs = (
        Conversation.query
        .filter_by(user_id=current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(5)
        .all()
    )

    # Aggregate stats
    total_words = sum(d.word_count for d in docs)
    total_pages = sum(d.page_count for d in docs)

    return render_template(
        "dashboard/index.html",
        recent_docs=recent_docs,
        total_docs=total_docs,
        recent_convs=recent_convs,
        total_words=total_words,
        total_pages=total_pages,
    )
