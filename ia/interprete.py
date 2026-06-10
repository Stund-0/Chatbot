import json
import os
import re

INTENCIONES = {
    "saludo": ["hola", "buenos días", "buenas tardes", "buenas noches", "qué tal", "hey", "saludos", "buen día"],
    "informacion": ["qué hacen", "qué ofrecen", "información", "informacion", "servicios", "productos", "conocen"],
    "horarios": ["horario", "horarios", "atienden", "abren", "cierran", "cuándo atienden", "días de atención"],
    "precios": ["precio", "precios", "cuánto cuesta", "costo", "costos", "tarifa", "valor", "cuesta"],
    "ubicacion": ["dirección", "ubicación", "ubicacion", "dónde están", "dónde queda", "donde estan", "donde queda", "ubicados", "direccion"],
    "cita_agendar": ["agendar", "cita", "consulta", "agenda", "reservar cita", "quiero una cita", "necesito una cita", "programar cita"],
    "cita_consultar": ["mi cita", "consultar cita", "ver cita", "estado de mi cita", "tengo una cita"],
    "cita_cancelar": ["cancelar", "cancelación", "cancelacion", "cancelar cita"],
    "reserva_crear": ["reservar", "apartar", "quiero comprar", "ordenar", "pedido", "comprar", "producto"],
    "reserva_consultar": ["mi reserva", "mi pedido", "consultar reserva", "estado de mi pedido", "ver reserva"],
    "contacto": ["teléfono", "telefono", "correo", "contacto", "comunicarme", "llamar"],
    "servicio_especifico": ["medicina general", "pediatría", "ginecología", "cardiología", "dermatología", "psicología", "especialidad"],
    "pago": ["pagar", "pago", "métodos de pago", "formas de pago", "transferencia", "tarjeta"],
    "emergencia": ["emergencia", "urgencia", "emergencia", "grave", "accidente", "duele"],
    "transferir": ["persona", "humano", "asesor", "operador", "hablar con alguien", "transferir", "agente"],
    "gracias": ["gracias", "muchas gracias", "agradezco", "thanks"],
    "despedida": ["adiós", "adios", "nos vemos", "hasta luego", "bye", "chao"],
    "faq": ["preguntas frecuentes", "faq", "dudas frecuentes"],
    "reportes": ["reporte", "reportes", "lista citas", "citas agendadas", "reservas activas"],
}


def _coincide_patron(patron, mensaje):
    palabras = patron.split()
    if len(palabras) == 1:
        return re.search(r'\b' + re.escape(patron) + r'\b', mensaje) is not None
    return patron in mensaje


PALABRAS_CLAVE_DESEMPATE = {
    "cancelar": "cita_cancelar",
    "cancelacion": "cita_cancelar",
    "cancelación": "cita_cancelar",
    "comprar": "reserva_crear",
    "pagar": "pago",
    "pago": "pago",
}


def detectar_intencion(mensaje):
    mensaje = mensaje.lower().strip()
    puntajes = {}

    for intencion, patrones in INTENCIONES.items():
        puntaje = 0
        for patron in patrones:
            if _coincide_patron(patron, mensaje):
                puntaje += len(patron.split())
            if mensaje.startswith(patron):
                puntaje += len(patron.split()) * 2
        if puntaje > 0:
            puntajes[intencion] = puntaje

    if not puntajes:
        return "consulta_general"

    palabras_msg = set(mensaje.split())
    for palabra_clave, intencion_asignada in PALABRAS_CLAVE_DESEMPATE.items():
        if palabra_clave in palabras_msg and intencion_asignada in puntajes:
            puntajes[intencion_asignada] += 5

    max_puntaje = max(puntajes.values())
    candidatos = [k for k, v in puntajes.items() if v == max_puntaje]

    if len(candidatos) > 1:
        orden = [
            "cita_cancelar", "cita_consultar", "cita_agendar",
            "reserva_crear", "reserva_consultar",
            "servicio_especifico",
            "emergencia", "transferir",
            "pago", "horarios", "precios", "ubicacion", "contacto",
            "informacion", "faq",
            "saludo", "gracias", "despedida",
            "reportes", "consulta_general",
        ]
        for ref in orden:
            if ref in candidatos:
                return ref

    return candidatos[0]


def extraer_entidades(mensaje):
    mensaje_lower = mensaje.lower()
    entidades = {}

    fecha_pattern = r"\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b"
    fecha_match = re.search(fecha_pattern, mensaje)
    if fecha_match:
        dia, mes, anio = fecha_match.groups()
        if len(anio) == 2:
            anio = "20" + anio
        entidades["fecha"] = f"{dia:0>2}/{mes:0>2}/{anio}"

    hora_pattern = r"\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b"
    hora_match = re.search(hora_pattern, mensaje)
    if hora_match:
        entidades["hora"] = hora_match.group(0)

    telefono_pattern = r"\b(\+?\d{1,3}\s?\d{7,10})\b"
    telefono_match = re.search(telefono_pattern, mensaje)
    if telefono_match:
        entidades["telefono"] = telefono_match.group(1).strip()

    nombre_patterns = [
        r"(?:llamo|soy|nombre es|me llamo|mi nombre es)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+?)(?:\.|,|$|y\s+mi\s+teléfono)",
        r"(?:soy)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+?)$",
    ]
    for pattern in nombre_patterns:
        nombre_match = re.search(pattern, mensaje_lower, re.IGNORECASE)
        if nombre_match:
            nombre = nombre_match.group(1).strip().title()
            if len(nombre) > 2:
                entidades["nombre"] = nombre
                break

    especialidades = [
        "medicina general", "pediatría", "pediatria", "ginecología", "ginecologia",
        "cardiología", "cardiologia", "dermatología", "dermatologia", "psicología", "psicologia",
        "medicina interna", "medicina familiar",
    ]
    for esp in especialidades:
        if esp in mensaje_lower:
            entidades["especialidad"] = esp.title()
            break

    cantidad_pattern = r"(\d+)\s*(?:unidad|unidades|pieza|piezas|kg|litro|litros)"
    cantidad_match = re.search(cantidad_pattern, mensaje_lower)
    if cantidad_match:
        entidades["cantidad"] = int(cantidad_match.group(1))

    return entidades


def interpretar_mensaje(mensaje, modo_simulacion=True):
    intencion = detectar_intencion(mensaje)
    entidades = extraer_entidades(mensaje)

    return {
        "intencion": intencion,
        "entidades": entidades,
        "mensaje_original": mensaje,
        "modo_simulacion": modo_simulacion,
    }
