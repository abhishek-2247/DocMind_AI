"""DocMind AI — Profile / account settings routes"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/")
@login_required
def index():
    from app.models import Document, Conversation
    total_docs  = Document.query.filter_by(user_id=current_user.id).count()
    total_convs = Conversation.query.filter_by(user_id=current_user.id).count()
    return render_template("profile/index.html",
                           total_docs=total_docs, total_convs=total_convs)


@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_pw  = request.form.get("current_password", "")
    new_pw      = request.form.get("new_password", "")
    confirm_pw  = request.form.get("confirm_password", "")

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile.index"))
    if len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for("profile.index"))
    if new_pw != confirm_pw:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile.index"))

    current_user.set_password(new_pw)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("profile.index"))


@profile_bp.route("/update", methods=["POST"])
@login_required
def update():
    username = request.form.get("username", "").strip()
    if not username or len(username) < 3:
        flash("Username must be at least 3 characters.", "danger")
        return redirect(url_for("profile.index"))
    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != current_user.id:
        flash("That username is already taken.", "danger")
        return redirect(url_for("profile.index"))
    current_user.username = username
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile.index"))


@profile_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    """Permanently delete the account and all its data."""
    import os
    from flask import current_app
    from app.models import Document
    from flask_login import logout_user

    # Remove uploaded files
    docs = Document.query.filter_by(user_id=current_user.id).all()
    for doc in docs:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_name)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash("Your account has been permanently deleted.", "info")
    return redirect(url_for("misc.landing"))
