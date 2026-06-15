from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _key_func_usuario():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        numero = data.get("numero") or data.get("from") or ""
        if numero:
            return f"user:{numero}"
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    if msg.get("from"):
                        return f"user:{msg['from']}"
    return get_remote_address()


limiter = Limiter(
    key_func=_key_func_usuario,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
