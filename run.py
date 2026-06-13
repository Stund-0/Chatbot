import os
import sys

from gunicorn.app.wsgiapp import WSGIApplication

if __name__ == "__main__":
    port = os.environ.get("PORT", "5000")
    sys.argv = [
        "gunicorn",
        "wsgi:app",
        "--bind", f"0.0.0.0:{port}",
        "--workers", "2",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
    ]
    WSGIApplication().run()
