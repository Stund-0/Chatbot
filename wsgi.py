import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database"))

from config.logging_config import setup_logging
logger = setup_logging()

from database.agenda_db import inicializar
inicializar()

from api import app

logger.info("WSGI iniciado correctamente")
