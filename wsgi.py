import os
import sys

# Agregar el directorio raíz al path para permitir importaciones absolutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Establecer ruta por defecto de la base de datos
os.environ.setdefault("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database"))

from config.logging_config import setup_logging
# Configurar logging para el proceso WSGI
logger = setup_logging()

from database.agenda_db import inicializar
# Inicializar la base de datos al arrancar el servidor
inicializar()

# Importar la aplicación Flask (esto ejecuta el módulo api.py)
from api import app

logger.info("WSGI iniciado correctamente")
