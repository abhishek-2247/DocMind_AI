"""DocMind AI — Document management routes"""

import os
import uuid
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, send_from_directory, jsonify, abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import Document
from app.services.document_service import extract_text, count_words, estimate_reading_time

documents_bp = Blueprint("documents", __name__)


def _allowed(filename: str) -> bool:
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@documents_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Document.query.filter_by(user_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Document.original_name.ilike(like)) | (Document.content_text.ilike(like))
        )
    docs = query.order_by(Document.uploaded_at.desc()).all()
    return render_template("documents/index.html", documents=docs, search_query=q)


@documents_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("documents.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("documents.index"))

    if not _allowed(file.filename):
        flash("File type not allowed. Supported: PDF, DOCX, PPTX, TXT", "danger")
        return redirect(url_for("documents.index"))

    original_name = file.filename
    ext = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)

    file.save(save_path)
    size = os.path.getsize(save_path)

    # Extract content
    text, pages = extract_text(save_path)
    words = count_words(text)
    reading = estimate_reading_time(words)

    doc = Document(
        user_id=current_user.id,
        original_name=original_name,
        stored_name=stored_name,
        file_type=ext,
        file_size=size,
        page_count=pages,
        word_count=words,
        reading_time=reading,
        content_text=text,
    )
    db.session.add(doc)
    db.session.commit()
    flash(f'"{original_name}" uploaded successfully!', "success")
    return redirect(url_for("documents.index"))


@documents_bp.route("/<int:doc_id>")
@login_required
def view(doc_id: int):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    return render_template("documents/view.html", document=doc)


@documents_bp.route("/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete(doc_id: int):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(doc)
    db.session.commit()
    flash(f'"{doc.original_name}" deleted.', "success")
    return redirect(url_for("documents.index"))


@documents_bp.route("/download/<int:doc_id>")
@login_required
def download(doc_id: int):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        doc.stored_name,
        as_attachment=True,
        download_name=doc.original_name,
    )


@documents_bp.route("/api/list")
@login_required
def api_list():
    """JSON endpoint for document picker in AI pages."""
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return jsonify([
        {"id": d.id, "name": d.original_name, "type": d.file_type, "size": d.size_human}
        for d in docs
    ])
