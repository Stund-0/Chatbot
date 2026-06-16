import os
import logging
from collections import OrderedDict

from flask import Blueprint, request, jsonify, current_app

from config.limiter import limiter
from .notificaciones import notificar_nueva_cita, notificar_admin

# Blueprint de Flask para agrupar rutas del webhook de WhatsApp
webhook_bp = Blueprint("webhook", __name__)

# Token de verificacion para el handshake con Meta
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "chatbot123")
logger = logging.getLogger(__name__)

# Cache LRU para deduplicacion de IDs de mensajes webhook (WhatsApp puede reenviar el mismo evento)
_processed_ids = OrderedDict()
_MAX_PROCESSED_IDS = 500


@webhook_bp.route("/webhook", methods=["GET"])
def verificar_webhook():
    """Maneja la verificacion del webhook (handshake GET) que exige Meta al configurarlo."""
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    desafio = request.args.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN:
        return desafio, 200
    return "Verification failed", 403


@webhook_bp.route("/webhook", methods=["POST"])
@limiter.limit("30 per minute")
def recibir_mensaje():
    """Procesa los mensajes entrantes de WhatsApp enviados por Meta via POST."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    try:
        chatbot = current_app.config.get("chatbot")
        sender = current_app.config.get("sender")
        modo_simulacion = chatbot.modo_simulacion if chatbot else False

        entries = data.get("entry", [])
        mensajes_procesados = []

        # Itera sobre cada entrada y cambio notificado por Meta
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})

                # Procesa cada mensaje individual dentro del payload
                for msg in messages:
                    msg_id = msg.get("id", "")
                    # Deduplicacion: salta si el ID ya fue procesado
                    if msg_id:
                        if msg_id in _processed_ids:
                            logger.debug("Mensaje %s ya procesado, saltando", msg_id)
                            continue
                        _processed_ids[msg_id] = True
                        # Mantiene el tamano del cache eliminando el mas antiguo
                        while len(_processed_ids) > _MAX_PROCESSED_IDS:
                            _processed_ids.popitem(last=False)

                    # Solo procesa mensajes de tipo texto
                    if msg.get("type") == "text":
                        from_number = msg.get("from", "")
                        text_body = msg.get("text", {}).get("body", "")

                        if chatbot:
                            # Envia el mensaje al chatbot para obtener una respuesta
                            try:
                                respuesta = chatbot.procesar_mensaje(text_body, from_number)
                            except Exception:
                                logger.exception("Error en chatbot.procesar_mensaje para %s: %s", from_number, text_body[:100])
                                continue

                            # Valida que la respuesta tenga el formato esperado
                            if not isinstance(respuesta, dict) or "respuesta" not in respuesta:
                                logger.warning(f"Respuesta invalida del chatbot: {respuesta}")
                                continue

                            # Extrae los textos de respuesta (soporta multiples respuestas)
                            textos = respuesta.get("respuestas", [respuesta.get("respuesta", "")])
                            textos = [str(t) for t in textos if isinstance(t, str) or str(t)]

                            # Envia cada texto al numero de WhatsApp del usuario
                            if not modo_simulacion and sender:
                                for t in textos:
                                    try:
                                        sender.enviar_texto(from_number, t)
                                    except Exception:
                                        logger.exception("Error enviando mensaje a %s", from_number)

                            # Si la intencion es agendar cita, notifica al administrador
                            if respuesta.get("intencion") == "cita_agendar" and respuesta.get("datos"):
                                notificar_nueva_cita(
                                    respuesta["datos"],
                                    sender,
                                    pendiente_confirmacion=respuesta.get("pendiente_confirmacion", False),
                                )

                            # Si el chatbot solicita transferencia, notifica al admin
                            if respuesta.get("transferir"):
                                notificar_admin(
                                    numero_cliente=from_number,
                                    mensaje_cliente=text_body,
                                    sender=sender,
                                )

                            # Acumula el resultado para el response
                            mensajes_procesados.append({
                                "numero": from_number,
                                "mensaje": text_body,
                                "respuesta": respuesta.get("respuesta", "")[:100],
                                "intencion": respuesta.get("intencion"),
                                "transferir": respuesta.get("transferir", False),
                            })

        return jsonify({
            "status": "ok",
            "processed": len(mensajes_procesados),
        }), 200

    except Exception as e:
        logger.exception("Error procesando webhook")
        return jsonify({"status": "error", "message": str(e)}), 500
