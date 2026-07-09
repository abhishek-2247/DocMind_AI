"""DocMind AI — Authentication routes"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([username, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("auth/register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Welcome to DocMind AI, {username}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/toggle-theme", methods=["POST"])
@login_required
def toggle_theme():
    current_user.theme = "dark" if current_user.theme == "light" else "light"
    db.session.commit()
    return {"theme": current_user.theme}
