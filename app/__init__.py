"""
DocMind AI — Flask application factory + extensions
"""

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db           = SQLAlchemy()
login_manager = LoginManager()
limiter       = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

login_manager.login_view         = "auth.login"
login_manager.login_message_duration = 5
login_manager.login_message      = "Please log in to access DocMind AI."
login_manager.login_message_category = "warning"


def create_app(config_object=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Configuration ────────────────────────────────────────────────────────
    if config_object is None:
        import sys
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from config import get_config
        config_object = get_config()
    app.config.from_object(config_object)

    # ── Trust proxy (needed for HTTPS redirect on hosting platforms) ─────────
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Extensions ───────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # ── Upload folder ────────────────────────────────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    # ── Blueprints ───────────────────────────────────────────────────────────
    from app.routes.auth      import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.documents import documents_bp
    from app.routes.ai        import ai_bp
    from app.routes.profile   import profile_bp
    from app.routes.misc      import misc_bp

    app.register_blueprint(misc_bp)                              # landing, health, errors
    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(documents_bp, url_prefix="/documents")
    app.register_blueprint(ai_bp,        url_prefix="/ai")
    app.register_blueprint(profile_bp,   url_prefix="/profile")

    # ── Error handlers ───────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("errors/429.html"), 429

    # ── Database tables ──────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app
