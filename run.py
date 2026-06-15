import os
import sys

from gunicorn.app.wsgiapp import WSGIApplication

if __name__ == "__main__":
    port = os.environ.get("PORT", "5000")
    workers = os.environ.get("GUNICORN_WORKERS", "2")
    timeout = os.environ.get("GUNICORN_TIMEOUT", "120")
    sys.argv = [
        "gunicorn",
        "wsgi:app",
        "--bind", f"0.0.0.0:{port}",
        "--workers", workers,
        "--timeout", timeout,
        "--access-logfile", "-",
        "--error-logfile", "-",
    ]
    WSGIApplication().run()
