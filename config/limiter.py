import os

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _key_func_usuario():
    """Extrae el numero de telefono del payload del webhook para rate limiting por usuario."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        numero = data.get("numero") or data.get("from") or ""
        if numero:
            return f"user:{numero}"
        # Si no viene directo, busca dentro de la estructura anidada del webhook de Meta
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    if msg.get("from"):
                        return f"user:{msg['from']}"
    return get_remote_address()


# URI de almacenamiento: Redis si hay REDIS_URL, sino memoria local
_storage_uri = os.getenv("REDIS_URL") or "memory://"

# Instancia global del limitador con limites por defecto y key personalizada
limiter = Limiter(
    key_func=_key_func_usuario,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_storage_uri,
)
