import os
import sys

from gunicorn.app.wsgiapp import WSGIApplication

if __name__ == "__main__":
    # Leer configuración desde variables de entorno con valores por defecto
    port = os.environ.get("PORT", "5000")
    workers = os.environ.get("GUNICORN_WORKERS", "2")
    timeout = os.environ.get("GUNICORN_TIMEOUT", "120")
    # Construir argumentos para Gunicorn con los parámetros configurados
    sys.argv = [
        "gunicorn",
        "wsgi:app",
        "--bind", f"0.0.0.0:{port}",
        "--workers", workers,
        "--timeout", timeout,
        "--access-logfile", "-",
        "--error-logfile", "-",
    ]
    # Iniciar el servidor WSGI Gunicorn
    WSGIApplication().run()
