"""
WSGI entry point for Patchly web app.
Suitable for Gunicorn, Waitress, uWSGI, or cloud hosting (Render, Railway, Heroku).
"""

from app import app

if __name__ == "__main__":
    app.run()
