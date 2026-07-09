from app.routes.auth      import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.documents import documents_bp
from app.routes.ai        import ai_bp
from app.routes.profile   import profile_bp
from app.routes.misc      import misc_bp

__all__ = ["auth_bp", "dashboard_bp", "documents_bp", "ai_bp", "profile_bp", "misc_bp"]
