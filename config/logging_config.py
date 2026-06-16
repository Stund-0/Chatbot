import json
import logging
import os
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formateador que convierte cada registro de log a una linea JSON estructurada."""

    def format(self, record):
        """Convierte un LogRecord en un string JSON con timestamp, nivel, modulo y mensaje."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Configura el logging global: nivel, formato (JSON o texto) y handlers."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json")

    # Configura el logger raiz con el nivel solicitado
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpia handlers previos para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Agrega un handler que escribe a stdout
    stream_handler = logging.StreamHandler(sys.stdout)

    # Elige el formateador segun la configuracion: JSON o texto plano
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Silencia librerias externas ruidosas a nivel WARNING
    for lib_logger in ("urllib3", "openai", "werkzeug"):
        l = logging.getLogger(lib_logger)
        l.setLevel(logging.WARNING)

    logging.getLogger("flask-limiter").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
