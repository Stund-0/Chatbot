import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Directorio raiz del proyecto para resolver rutas relativas
RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _obtener_admin_telefono():
    """Obtiene el telefono del admin desde variable de entorno o archivo settings.json."""
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
    """Carga el template de notificacion admin desde archivo o usa uno por defecto."""
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
    """Rellena el template de notificacion con los datos del cliente y la fecha/hora actual."""
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
    """Notifica al administrador sobre una nueva cita agendada o pendiente de confirmacion."""
    admin_telefono = _obtener_admin_telefono()
    if not admin_telefono:
        logger.warning("ADMIN_TELEFONO no configurado. Notificacion de cita no enviada.")
        return {"exito": False, "error": "Admin phone not configured"}

    # Construye mensaje distinto segun si la cita requiere confirmacion o no
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

    # Envia el mensaje via sender de WhatsApp si esta disponible
    if sender:
        resultado = sender.enviar_texto(admin_telefono, mensaje)
        if resultado.get("exito"):
            logger.info("Notificacion de nueva cita enviada al admin (folio %s)", datos.get("folio"))
        else:
            logger.error("Error al notificar nueva cita: %s", resultado.get("error"))
        return resultado

    # Modo simulacion: imprime la notificacion en consola
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
    """Notifica al administrador cuando el chatbot solicita transferencia al humano."""
    admin_telefono = _obtener_admin_telefono()
    if not admin_telefono:
        logger.warning(
            "ADMIN_TELEFONO no configurado. "
            "Notificacion no enviada."
        )
        return {"exito": False, "error": "Admin phone not configured"}

    # Formatea el mensaje con los datos del cliente
    mensaje = _formatear_mensaje_admin(
        numero_cliente, mensaje_cliente, nombre_cliente
    )

    # Envia la notificacion via sender de WhatsApp
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

    # Modo simulacion: imprime la notificacion en consola
    if os.getenv("MODO_SIMULACION", "true").lower() == "true":
        import sys
        _stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
        _stdout.write(f"\n[NOTIFICACION ADMIN] Para: {admin_telefono}\n".encode("utf-8", errors="replace"))
        _stdout.write(f"[CONTENIDO]: {mensaje}\n".encode("utf-8", errors="replace"))
        _stdout.write(("=" * 50 + "\n").encode("utf-8", errors="replace"))
        return {"exito": True, "simulado": True}

    return {"exito": False, "error": "No sender available"}
