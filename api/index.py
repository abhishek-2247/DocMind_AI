"""
Vercel serverless adapter for DocMind AI.

IMPORTANT LIMITATIONS ON VERCEL FREE TIER:
  - File uploads will fail (read-only filesystem — /tmp only, wiped between requests)
  - SQLite database resets on every cold start (use PostgreSQL via DATABASE_URL instead)
  - IBM watsonx.ai calls may timeout (Vercel free tier: 10s limit, Pro: 60s)
  - Uploaded files are lost after each function invocation

For a fully functional deployment use Railway or Render instead.
See README.md for instructions.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Override upload folder to /tmp (only writable dir on Vercel)
os.environ.setdefault("UPLOAD_FOLDER", "/tmp/docmind_uploads")
os.environ.setdefault("FLASK_ENV", "production")

from app import create_app

# Vercel looks for a variable named 'app'
app = create_app()
