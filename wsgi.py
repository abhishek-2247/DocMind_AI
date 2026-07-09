"""
DocMind AI — Production WSGI entry point
Used by gunicorn: gunicorn wsgi:application
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

application = create_app()

# Also expose as 'app' for compatibility with some platforms
app = application
