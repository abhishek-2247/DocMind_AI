# Procfile — used by Heroku, Railway, and Render
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --preload
