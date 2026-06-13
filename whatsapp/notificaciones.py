import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _obtener_admin_telefono():
    telefono = os.getenv("ADMIN_TELEFONO", "")
    if not telefono:
        settings_path = os.path.join(RUTA_BASE, "config", "settings.json")
        try:
            import json
            with open(settings_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            telefono = config.get("admin_telefono", "")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return telefono


def _cargar_template_admin():
    ruta = os.path.join(RUTA_BASE, "mensajes", "mensaje_admin.txt")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "NOTIFICACION DE CONSULTA PENDIENTE\n\n"
            "Cliente: {{NOMBRE_CLIENTE}}\n"
            "Telefono: {{TELEFONO_CLIENTE}}\n"
            "Mensaje: {{MENSAJE_CLIENTE}}\n"
            "Fecha: {{FECHA}}\n"
            "Hora: {{HORA}}"
        )


def _formatear_mensaje_admin(numero_cliente, mensaje_cliente, nombre_cliente=""):
    template = _cargar_template_admin()
    ahora = datetime.now()
    reemplazos = {
        "{{NOMBRE_CLIENTE}}": nombre_cliente or numero_cliente,
        "{{TELEFONO_CLIENTE}}": numero_cliente,
        "{{MENSAJE_CLIENTE}}": mensaje_cliente,
        "{{FECHA}}": ahora.strftime("%d/%m/%Y"),
        "{{HORA}}": ahora.strftime("%H:%M"),
    }
    for placeholder, valor in reemplazos.items():
        template = template.replace(placeholder, valor)
    return template


def notificar_nueva_cita(datos, sender, pendiente_confirmacion=False):
    admin_telefono = _obtener_admin_telefono()
    if not admin_telefono:
        logger.warning("ADMIN_TELEFONO no configurado. Notificacion de cita no enviada.")
        return {"exito": False, "error": "Admin phone not configured"}

    if pendiente_confirmacion:
        folio = datos.get("folio", "N/A")
        mensaje = (
            "🆕 *NUEVA CITA - PENDIENTE DE CONFIRMACIÓN*\n\n"
            f"▪️ *Folio:* {folio}\n"
            f"▪️ *Cliente:* {datos.get('nombre', 'N/A')}\n"
            f"▪️ *Teléfono:* {datos.get('telefono', 'N/A')}\n"
            f"▪️ *Especialidad:* {datos.get('especialidad', 'N/A')}\n"
            f"▪️ *Fecha:* {datos.get('fecha', 'N/A')}\n"
            f"▪️ *Hora:* {datos.get('hora', 'N/A')}\n\n"
            "─" * 30 + "\n"
            f"Para *CONFIRMAR* responde:\n"
            f"CONFIRMAR {folio}\n\n"
            f"Para *RECHAZAR* responde:\n"
            f"RECHAZAR {folio}"
        )
    else:
        mensaje = (
            "🆕 *NUEVA CITA AGENDADA*\n\n"
            f"▪️ *Folio:* {datos.get('folio', 'N/A')}\n"
            f"▪️ *Cliente:* {datos.get('nombre', 'N/A')}\n"
            f"▪️ *Teléfono:* {datos.get('telefono', 'N/A')}\n"
            f"▪️ *Especialidad:* {datos.get('especialidad', 'N/A')}\n"
            f"▪️ *Fecha:* {datos.get('fecha', 'N/A')}\n"
            f"▪️ *Hora:* {datos.get('hora', 'N/A')}"
        )

    if sender:
        resultado = sender.enviar_texto(admin_telefono, mensaje)
        if resultado.get("exito"):
            logger.info("Notificacion de nueva cita enviada al admin (folio %s)", datos.get("folio"))
        else:
            logger.error("Error al notificar nueva cita: %s", resultado.get("error"))
        return resultado

    if os.getenv("MODO_SIMULACION", "true").lower() == "true":
        import sys
        mensaje_plano = mensaje.replace("*", "").replace("─", "-")
        _stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
        _stdout.write(f"\n[NUEVA CITA - NOTIFICACION ADMIN] Para: {admin_telefono}\n".encode("utf-8", errors="replace"))
        _stdout.write(f"[CONTENIDO]: {mensaje_plano}\n".encode("utf-8", errors="replace"))
        _stdout.write(("=" * 50 + "\n").encode("utf-8", errors="replace"))
        return {"exito": True, "simulado": True}

    return {"exito": False, "error": "No sender available"}


def notificar_admin(numero_cliente, mensaje_cliente, sender, nombre_cliente=""):
    admin_telefono = _obtener_admin_telefono()
    if not admin_telefono:
        logger.warning(
            "ADMIN_TELEFONO no configurado. "
            "Notificacion no enviada."
        )
        return {"exito": False, "error": "Admin phone not configured"}

    mensaje = _formatear_mensaje_admin(
        numero_cliente, mensaje_cliente, nombre_cliente
    )

    if sender:
        resultado = sender.enviar_texto(admin_telefono, mensaje)
        if resultado.get("exito"):
            logger.info(
                "Notificacion enviada al admin %s sobre cliente %s",
                admin_telefono, numero_cliente,
            )
        else:
            logger.error(
                "Error al notificar al admin: %s", resultado.get("error")
            )
        return resultado

    if os.getenv("MODO_SIMULACION", "true").lower() == "true":
        print(f"\n[NOTIFICACION ADMIN] Para: {admin_telefono}")
        print(f"[CONTENIDO]: {mensaje}")
        print("=" * 50)
        return {"exito": True, "simulado": True}

    return {"exito": False, "error": "No sender available"}
