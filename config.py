"""
DocMind AI — Application Configuration
=======================================
All runtime settings are loaded from environment variables (via .env).
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _db_url() -> str:
    """
    Railway and Heroku inject DATABASE_URL as 'postgres://...' (legacy scheme).
    SQLAlchemy 1.4+ requires 'postgresql://...'.  Fix it transparently.
    """
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'docmind.db')}"


class Config:
    """Base configuration shared across all environments."""

    # ── Flask core ──────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    FLASK_ENV: str  = os.getenv("FLASK_ENV", "development")

    # ── Database ─────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str    = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True}

    # ── File uploads ─────────────────────────────────────────────────────────
    UPLOAD_FOLDER: str    = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS: set = set(
        os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,pptx,txt").split(",")
    )

    # ── IBM watsonx.ai ───────────────────────────────────────────────────────
    IBM_API_KEY:     str = os.getenv("IBM_API_KEY", "")
    IBM_PROJECT_ID:  str = os.getenv("IBM_PROJECT_ID", "")
    IBM_WATSONX_URL: str = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    # ── Session ──────────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str  = "Lax"
    PERMANENT_SESSION_LIFETIME: int = 60 * 60 * 24 * 30  # 30 days

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT         = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL     = os.getenv("REDIS_URL", "memory://")
    RATELIMIT_STRATEGY        = "fixed-window"
    RATELIMIT_HEADERS_ENABLED = True

    # ──────────────────────────────────────────────────────────────────────────
    # AGENT CONFIGURATION
    # Edit these values to customise the AI assistant behaviour without
    # touching any other code.
    # ──────────────────────────────────────────────────────────────────────────
    AGENT_CONFIGURATION = {
        # Model ID served by watsonx.ai — must match your project's allowed list.
        # US-South default. Change to a Granite model when available in your project.
        "model_id": "meta-llama/llama-3-3-70b-instruct",
        # Personality / role description injected into every prompt
        "personality": (
            "You are DocMind AI, an expert enterprise document analyst. "
            "You are helpful, precise, and professional. "
            "You cite specific sections of documents when answering questions."
        ),
        # Response tone: formal | friendly | concise
        "tone": "professional",
        # Hard cap on generated tokens
        "max_new_tokens": 1024,
        # Decoding temperature  (0 = deterministic, 1 = creative)
        "temperature": 0.7,
        # Top-P nucleus sampling
        "top_p": 0.9,
        # Repetition penalty — values > 1 discourage repeating phrases
        "repetition_penalty": 1.1,
        # Default summary style: bullets | short | detailed
        "summary_style": "bullets",
        # Languages the assistant will respond in (informational)
        "supported_languages": ["English", "Spanish", "French", "German", "Hindi"],
        # Safety preamble prepended to every AI request
        "safety_instructions": (
            "Do not generate harmful, offensive, or misleading content. "
            "If a question is outside the scope of the uploaded documents, "
            "say so clearly rather than guessing."
        ),
    }


class DevelopmentConfig(Config):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False


class ProductionConfig(Config):
    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool  = True
    SESSION_COOKIE_HTTPONLY: bool = True
    # Trust the proxy headers set by Railway / Render / Heroku
    PREFERRED_URL_SCHEME: str = "https"


class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False
    RATELIMIT_ENABLED: bool = False


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config() -> Config:
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
