import json
import os
import logging

from flask import Blueprint, request, jsonify, current_app

from .notificaciones import notificar_nueva_cita, notificar_admin

webhook_bp = Blueprint("webhook", __name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "chatbot123")
logger = logging.getLogger(__name__)


@webhook_bp.route("/webhook", methods=["GET"])
def verificar_webhook():
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    desafio = request.args.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN:
        return desafio, 200
    return "Verification failed", 403


@webhook_bp.route("/webhook", methods=["POST"])
def recibir_mensaje():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    try:
        chatbot = current_app.config.get("chatbot")
        sender = current_app.config.get("sender")
        modo_simulacion = os.getenv("MODO_SIMULACION", "true").lower() == "true"

        entries = data.get("entry", [])
        mensajes_procesados = []

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})

                for msg in messages:
                    if msg.get("type") == "text":
                        from_number = msg.get("from", "")
                        text_body = msg.get("text", {}).get("body", "")

                        if chatbot:
                            respuesta = chatbot.procesar_mensaje(text_body, from_number)

                            if not isinstance(respuesta, dict) or "respuesta" not in respuesta:
                                logger.warning(f"Respuesta invalida del chatbot: {respuesta}")
                                continue

                            texto_respuesta = respuesta["respuesta"]
                            if not isinstance(texto_respuesta, str):
                                texto_respuesta = str(texto_respuesta)

                            if not modo_simulacion and sender:
                                sender.enviar_texto(from_number, texto_respuesta)

                            if respuesta.get("intencion") == "cita_agendar" and respuesta.get("datos"):
                                notificar_nueva_cita(
                                    respuesta["datos"],
                                    sender,
                                    pendiente_confirmacion=respuesta.get("pendiente_confirmacion", False),
                                )

                            if respuesta.get("transferir"):
                                notificar_admin(
                                    numero_cliente=from_number,
                                    mensaje_cliente=text_body,
                                    sender=sender,
                                )

                            mensajes_procesados.append({
                                "numero": from_number,
                                "mensaje": text_body,
                                "respuesta": texto_respuesta[:100],
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
