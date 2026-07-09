"""DocMind AI — AI feature routes (chat, summary, comparison, insights)"""

from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, jsonify,
    redirect, url_for, flash, abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import Document, Conversation, Message
from app.services.watsonx_service import (
    answer_question,
    summarise_document,
    compare_documents,
    extract_insights,
)

ai_bp = Blueprint("ai", __name__)


# ── Chat ──────────────────────────────────────────────────────────────────────

@ai_bp.route("/chat")
@login_required
def chat():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    convs = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).limit(10).all()
    doc_id = request.args.get("doc_id", type=int)
    conv_id = request.args.get("conv_id", type=int)

    selected_doc = None
    if doc_id:
        selected_doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    selected_conv = None
    conv_messages = []
    if conv_id:
        selected_conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if selected_conv:
            conv_messages = selected_conv.messages.all()

    return render_template(
        "ai/chat.html",
        documents=docs,
        conversations=convs,
        selected_doc=selected_doc,
        selected_conv=selected_conv,
        conv_messages=conv_messages,
    )


@ai_bp.route("/chat/send", methods=["POST"])
@login_required
def chat_send():
    data = request.get_json(force=True)
    doc_id = data.get("doc_id")
    question = data.get("message", "").strip()
    conv_id = data.get("conv_id")

    if not question:
        return jsonify({"error": "Empty message"}), 400

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Get or create conversation
    if conv_id:
        conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
    else:
        conv = Conversation(user_id=current_user.id, title=question[:80])
        db.session.add(conv)
        db.session.flush()

    # Build history
    history = [
        {"role": m.role, "content": m.content}
        for m in conv.messages.order_by(Message.created_at).all()
    ]

    # Call AI
    answer = answer_question(doc.content_text, question, history)

    # Persist messages
    user_msg = Message(conversation_id=conv.id, document_id=doc.id, role="user", content=question)
    ai_msg = Message(conversation_id=conv.id, document_id=doc.id, role="assistant", content=answer)
    db.session.add_all([user_msg, ai_msg])
    conv.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "answer": answer,
        "conv_id": conv.id,
        "conv_title": conv.title,
    })


@ai_bp.route("/chat/new-conversation", methods=["POST"])
@login_required
def new_conversation():
    conv = Conversation(user_id=current_user.id, title="New Conversation")
    db.session.add(conv)
    db.session.commit()
    return jsonify({"conv_id": conv.id})


@ai_bp.route("/chat/delete-conversation/<int:conv_id>", methods=["POST"])
@login_required
def delete_conversation(conv_id: int):
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"success": True})


# ── Summary ───────────────────────────────────────────────────────────────────

@ai_bp.route("/summary")
@login_required
def summary():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    doc_id = request.args.get("doc_id", type=int)
    selected_doc = None
    if doc_id:
        selected_doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    return render_template("ai/summary.html", documents=docs, selected_doc=selected_doc)


@ai_bp.route("/summary/generate", methods=["POST"])
@login_required
def generate_summary():
    data = request.get_json(force=True)
    doc_id = data.get("doc_id")
    style = data.get("style", "bullets")

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    result = summarise_document(doc.content_text, style)
    if not result.startswith("[AI Error]"):
        doc.ai_summary = result
        db.session.commit()

    return jsonify({"summary": result, "doc_name": doc.original_name, "style": style})


# ── Comparison ────────────────────────────────────────────────────────────────

@ai_bp.route("/compare")
@login_required
def compare():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template("ai/compare.html", documents=docs)


@ai_bp.route("/compare/run", methods=["POST"])
@login_required
def run_compare():
    data = request.get_json(force=True)
    doc_id_a = data.get("doc_id_a")
    doc_id_b = data.get("doc_id_b")

    if doc_id_a == doc_id_b:
        return jsonify({"error": "Please select two different documents."}), 400

    doc_a = Document.query.filter_by(id=doc_id_a, user_id=current_user.id).first()
    doc_b = Document.query.filter_by(id=doc_id_b, user_id=current_user.id).first()

    if not doc_a or not doc_b:
        return jsonify({"error": "One or both documents not found."}), 404

    result = compare_documents(doc_a.content_text, doc_b.content_text,
                                doc_a.original_name, doc_b.original_name)
    return jsonify(result)


# ── Insights ──────────────────────────────────────────────────────────────────

@ai_bp.route("/insights")
@login_required
def insights():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    doc_id = request.args.get("doc_id", type=int)
    selected_doc = None
    doc_insights = None

    if doc_id:
        selected_doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
        if selected_doc:
            doc_insights = extract_insights(selected_doc.content_text)
            # Persist tags
            if doc_insights.get("tags"):
                selected_doc.ai_tags = ", ".join(doc_insights["tags"])
                db.session.commit()

    return render_template(
        "ai/insights.html",
        documents=docs,
        selected_doc=selected_doc,
        doc_insights=doc_insights,
    )


@ai_bp.route("/insights/generate", methods=["POST"])
@login_required
def generate_insights():
    data = request.get_json(force=True)
    doc_id = data.get("doc_id")

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    result = extract_insights(doc.content_text)
    if result.get("tags"):
        doc.ai_tags = ", ".join(result["tags"])
        db.session.commit()

    result["reading_time"] = doc.reading_time
    result["word_count"] = doc.word_count
    result["page_count"] = doc.page_count
    result["doc_name"] = doc.original_name
    return jsonify(result)
