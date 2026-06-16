import os
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from config.logging_config import setup_logging
# Configurar el sistema de logging
logger = setup_logging()

from config.limiter import limiter
from database.agenda_db import inicializar as inicializar_db
from chatbot import Chatbot
from whatsapp.webhook import webhook_bp
from whatsapp.sender import WhatsAppSender
from whatsapp.handlers import MessageHandler

# Crear la aplicación Flask principal
app = Flask(__name__)

# Determinar si se ejecuta en modo simulación (sin WhatsApp real)
MODO_SIMULACION = os.getenv("MODO_SIMULACION", "false").lower() == "true"
# Habilitar/deshabilitar modo debug
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
# Puerto del servidor
PUERTO = int(os.getenv("PUERTO", "5000"))
# Clave API para proteger endpoints de reportes
REPORTES_API_KEY = os.getenv("REPORTES_API_KEY", "")

# Vincular el limitador de tasa a la app
limiter.init_app(app)

# Inicializar el sender de WhatsApp con token y phone ID
sender = WhatsAppSender(
    token=os.getenv("WHATSAPP_TOKEN"),
    phone_id=os.getenv("WHATSAPP_PHONE_ID"),
)
# Instanciar el chatbot principal
chatbot = Chatbot(modo_simulacion=MODO_SIMULACION, sender=sender)
# Manejador de mensajes entrantes de WhatsApp
msg_handler = MessageHandler(sender)

# Almacenar componentes en la configuración de Flask para acceso global
app.config["chatbot"] = chatbot
app.config["sender"] = sender
app.config["msg_handler"] = msg_handler


@app.route("/")
def index():
    # Endpoint raíz: muestra información básica del chatbot
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
    # Endpoint de salud simple para verificar que el servicio responde
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/health", methods=["GET"])
def health():
    # Endpoint de health check: verifica BD y configuración de WhatsApp
    db_ok = False
    db_error = ""
    try:
        # Probar conectividad con la base de datos
        from database.agenda_db import conectar, liberar_conexion
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        liberar_conexion(conn)
        db_ok = True
    except Exception as e:
        db_error = str(e)

    sender = app.config.get("sender")
    whatsapp_ok = bool(sender and sender.token and sender.phone_id)

    return jsonify({
        "status": "ok" if db_ok else "degradado",
        "base_datos": "conectada" if db_ok else f"error: {db_error}",
        "whatsapp_api": "configurado" if whatsapp_ok else "no configurado",
        "modo": "simulación" if MODO_SIMULACION else "producción",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    # Endpoint principal de chat: procesa un mensaje y devuelve la respuesta
    data = request.get_json()
    if not data or "mensaje" not in data:
        return jsonify({"error": "Mensaje requerido"}), 400

    mensaje = data["mensaje"]
    numero = data.get("numero", "0000000000")
    contexto = data.get("contexto")

    logger.info("Chat request", extra={"numero": numero, "intencion": ""})
    try:
        # Procesar el mensaje a través del chatbot (NLP + lógica de negocio)
        respuesta = chatbot.procesar_mensaje(mensaje, numero, contexto)
    except Exception as e:
        logger.exception("Error en procesar_mensaje: %s", e)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    logger.info("Chat response", extra={
        "numero": numero,
        "intencion": respuesta.get("intencion"),
        "transferir": respuesta.get("transferir", False),
    })

    from whatsapp.notificaciones import notificar_nueva_cita, notificar_admin

    # Si se agendó una cita, enviar notificación
    if respuesta.get("intencion") == "cita_agendar" and respuesta.get("datos"):
        try:
            notificar_nueva_cita(
                respuesta["datos"],
                sender if not MODO_SIMULACION else None,
                pendiente_confirmacion=respuesta.get("pendiente_confirmacion", False),
            )
        except Exception as e:
            logger.exception("Error al notificar nueva cita: %s", e)

    # Si el chatbot determinó que debe transferir a un humano, notificar al admin
    if respuesta.get("transferir"):
        try:
            notificar_admin(
                numero_cliente=numero,
                mensaje_cliente=mensaje,
                sender=sender if not MODO_SIMULACION else None,
            )
        except Exception as e:
            logger.exception("Error al notificar admin: %s", e)

    respuestas = respuesta.get("respuestas", [respuesta["respuesta"]])
    if MODO_SIMULACION:
        # En modo simulación solo devolver JSON sin enviar a WhatsApp
        return jsonify({
            "respuesta": respuesta["respuesta"],
            "respuestas": respuestas,
            "intencion": respuesta.get("intencion"),
            "transferir": respuesta.get("transferir", False),
            "modo": "simulacion",
        })

    try:
        # Enviar la respuesta al usuario vía WhatsApp
        msg_handler.manejar_mensaje_entrante(numero, mensaje, respuesta)
    except Exception as e:
        logger.exception("Error al enviar mensaje WhatsApp: %s", e)

    return jsonify({
        "respuesta": respuesta["respuesta"],
        "respuestas": respuestas,
        "intencion": respuesta.get("intencion"),
        "transferir": respuesta.get("transferir", False),
        "enviado": True,
    })


def requerir_api_key(f):
    # Decorador que protege endpoints requiriendo una API key vía header Authorization
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
    # Endpoint de reportes: lista citas filtradas por estado
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
    # Endpoint de reportes: lista reservas de productos filtradas por estado
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


# Registrar blueprint con las rutas del webhook de WhatsApp
app.register_blueprint(webhook_bp)

# Inicializar la base de datos (crear tablas si no existen)
inicializar_db()
logger.info(f"Chatbot iniciado en modo {'SIMULACION' if MODO_SIMULACION else 'PRODUCCION'}")

if __name__ == "__main__":
    logger.info(f"Servidor en http://0.0.0.0:{PUERTO}")
    # Iniciar servidor Flask en desarrollo
    app.run(host="0.0.0.0", port=PUERTO, debug=DEBUG)
