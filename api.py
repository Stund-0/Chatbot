import json
import os
import logging

from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from config.logging_config import setup_logging
logger = setup_logging()

from database.agenda_db import inicializar as inicializar_db
from chatbot import Chatbot
from whatsapp.webhook import webhook_bp
from whatsapp.sender import WhatsAppSender
from whatsapp.handlers import MessageHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

MODO_SIMULACION = os.getenv("MODO_SIMULACION", "true").lower() == "true"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
PUERTO = int(os.getenv("PUERTO", "5000"))
REPORTES_API_KEY = os.getenv("REPORTES_API_KEY", "")

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

chatbot = Chatbot(modo_simulacion=MODO_SIMULACION)
sender = WhatsAppSender(
    token=os.getenv("WHATSAPP_TOKEN"),
    phone_id=os.getenv("WHATSAPP_PHONE_ID"),
)
msg_handler = MessageHandler(sender)

app.config["chatbot"] = chatbot
app.config["sender"] = sender
app.config["msg_handler"] = msg_handler


@app.route("/")
def index():
    return jsonify({
        "nombre": chatbot.config.get("nombre", "Chatbot WhatsApp"),
        "version": chatbot.config.get("version", "1.0.0"),
        "tipo": chatbot.config.get("tipo", ""),
        "eslogan": chatbot.config.get("eslogan", ""),
        "estado": "activo",
        "modo": "simulación" if MODO_SIMULACION else "producción",
    })


@app.route("/salud", methods=["GET"])
def salud():
    return jsonify({"status": "ok", "timestamp": __import__("datetime").datetime.now().isoformat()})


@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    data = request.get_json()
    if not data or "mensaje" not in data:
        return jsonify({"error": "Mensaje requerido"}), 400

    mensaje = data["mensaje"]
    numero = data.get("numero", "0000000000")
    contexto = data.get("contexto")

    logger.info("Chat request", extra={"numero": numero, "intencion": ""})
    respuesta = chatbot.procesar_mensaje(mensaje, numero, contexto)
    logger.info("Chat response", extra={
        "numero": numero,
        "intencion": respuesta.get("intencion"),
        "transferir": respuesta.get("transferir", False),
    })

    if MODO_SIMULACION:
        return jsonify({
            "respuesta": respuesta["respuesta"],
            "intencion": respuesta.get("intencion"),
            "transferir": respuesta.get("transferir", False),
            "modo": "simulacion",
        })

    msg_handler.manejar_mensaje_entrante(numero, mensaje, respuesta)

    return jsonify({
        "respuesta": respuesta["respuesta"],
        "intencion": respuesta.get("intencion"),
        "transferir": respuesta.get("transferir", False),
        "enviado": True,
    })


def requerir_api_key(f):
    from functools import wraps
    @wraps(f)
    def decorada(*args, **kwargs):
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not REPORTES_API_KEY:
            return jsonify({"error": "Reportes no configurados (falta REPORTES_API_KEY)"}), 503
        if api_key != REPORTES_API_KEY:
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorada


@app.route("/reportes/citas", methods=["GET"])
@limiter.limit("10 per minute")
@requerir_api_key
def reportes_citas():
    estado = request.args.get("estado")
    from database.consultas import listar_citas
    citas = listar_citas(estado)
    return jsonify({
        "total": len(citas),
        "citas": [
            {
                "nombre": c["nombre"],
                "telefono": c["telefono"],
                "fecha": c["fecha"],
                "hora": c["hora"],
                "servicio": c.get("servicio", c.get("especialidad")),
                "folio": c["folio"],
                "estado": c["estado"],
            }
            for c in citas
        ],
    })


@app.route("/reportes/reservas", methods=["GET"])
@limiter.limit("10 per minute")
@requerir_api_key
def reportes_reservas():
    estado = request.args.get("estado")
    from database.consultas import listar_reservas
    reservas = listar_reservas(estado)
    return jsonify({
        "total": len(reservas),
        "reservas": [
            {
                "nombre": r["nombre"],
                "telefono": r["telefono"],
                "producto": r["producto_reservado"],
                "cantidad": r["cantidad"],
                "folio": r["folio"],
                "estado": r["estado"],
            }
            for r in reservas
        ],
    })


app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    inicializar_db()
    logger.info(f"Chatbot iniciado en modo {'SIMULACION' if MODO_SIMULACION else 'PRODUCCION'}")
    logger.info(f"Servidor en http://0.0.0.0:{PUERTO}")
    app.run(host="0.0.0.0", port=PUERTO, debug=DEBUG)
