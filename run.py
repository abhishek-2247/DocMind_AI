"""
DocMind AI — Application entry point
Run:  python run.py
      flask run  (set FLASK_APP=run.py first)
"""

import sys
import os

# Always resolve to the venv's site-packages so Flask's reloader
# does not lose the virtualenv when it restarts the process.
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# Point the reloader at the active venv so it inherits site-packages.
_venv = os.path.join(_here, "venv")
if os.path.isdir(_venv):
    import glob
    for _sp in glob.glob(os.path.join(_venv, "Lib", "site-packages")):   # Windows
        if _sp not in sys.path:
            sys.path.insert(1, _sp)
    for _sp in glob.glob(os.path.join(_venv, "lib", "python*", "site-packages")):  # Unix
        if _sp not in sys.path:
            sys.path.insert(1, _sp)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
        use_reloader=True,
    )
