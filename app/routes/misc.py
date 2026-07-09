"""DocMind AI — Miscellaneous routes: landing page, health check"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/")
def landing():
    """Public landing page. Authenticated users go straight to dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")


@misc_bp.route("/health")
def health():
    """Health check endpoint used by Railway / Render / load balancers."""
    from app import db
    try:
        db.session.execute(db.text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}, status
