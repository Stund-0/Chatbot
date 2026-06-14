import json
import os
import re

INTENCIONES = {
    "saludo": ["hola", "buenos días", "buenas tardes", "buenas noches", "qué tal", "hey", "saludos", "buen día", "buenas", "qué hay", "cómo estás", "como estas", "que tal", "que hay", "como estas", "buen dia", "buenos dias"],
    "informacion": ["qué hacen", "qué ofrecen", "información", "informacion", "servicios", "productos", "conocen", "a qué se dedican", "a que se dedican", "qué ofrecen", "que ofrecen", "me pueden decir", "que hacen"],
    "horarios": ["horario", "horarios", "atienden", "abren", "cierran", "cuándo atienden", "días de atención", "días de atención", "dias de atencion", "qué días trabajan", "que dias trabajan", "están abiertos", "estan abiertos"],
    "precios": ["precio", "precios", "cuánto cuesta", "costo", "costos", "tarifa", "valor", "cuesta", "cuanto cuesta", "cuánto vale", "cuanto vale", "cuánto cobran", "cuanto cobran", "cuánto sale", "cuanto sale", "qué precio tiene", "que precio tiene", "precio de", "de precio"],
    "ubicacion": ["dirección", "ubicación", "ubicacion", "dónde están", "dónde queda", "donde estan", "donde queda", "ubicados", "direccion", "cómo llegar", "como llegar", "mapa", "dónde se ubican", "donde se ubican"],
    "cita_agendar": ["agendar", "cita", "consulta", "agenda", "reservar cita", "quiero una cita", "necesito una cita", "programar cita", "sacar cita", "pedir cita"],
    "cita_consultar": ["mi cita", "consultar cita", "ver cita", "estado de mi cita", "tengo una cita", "consulta mi cita", "revisar mi cita", "cómo va mi cita", "como va mi cita", "quiero ver mi cita", "quiero consultar mi cita", "ver mi cita"],
    "cita_cancelar": ["cancelar", "cancelación", "cancelacion", "cancelar cita", "anular cita", "anular"],
    "reserva_crear": ["reservar", "apartar", "quiero comprar", "ordenar", "pedido", "comprar", "producto", "hacer una reserva"],
    "reserva_consultar": ["mi reserva", "mi pedido", "consultar reserva", "estado de mi pedido", "ver reserva", "consultar mi pedido", "ver mi reserva"],
    "contacto": ["teléfono", "telefono", "correo", "contacto", "comunicarme", "llamar", "email", "whatsapp", "cuál es su número", "cual es su numero", "dónde llamo", "donde llamo"],
    "servicio_especifico": ["medicina general", "pediatría", "pediatria", "ginecología", "ginecologia", "cardiología", "cardiologia", "dermatología", "dermatologia", "psicología", "psicologia", "especialidad"],
    "pago": ["pagar", "pago", "métodos de pago", "formas de pago", "transferencia", "tarjeta", "métodos de pago", "formas de pago"],
    "emergencia": ["emergencia", "urgencia", "grave", "accidente", "duele", "ayuda urgente", "necesito ayuda"],
    "transferir": ["persona", "humano", "asesor", "operador", "hablar con alguien", "transferir", "agente", "atención personal", "atencion personal"],
    "gracias": ["gracias", "muchas gracias", "agradezco", "thanks", "muy amable", "te agradezco"],
    "despedida": ["adiós", "adios", "nos vemos", "hasta luego", "bye", "chao", "hasta pronto"],
    "faq": ["preguntas frecuentes", "faq", "dudas frecuentes", "preguntas comunes"],
    "fechas_disponibles": ["fechas disponibles", "fechas libres", "días disponibles", "días libres", "dias disponibles", "dias libres", "esta semana", "este mes", "fechas ocupadas", "días ocupados", "dias ocupados", "qué fecha", "que fecha", "cuándo hay", "cuando hay", "tiene libre", "tienes libre", "están reservados", "estan reservados"],
    "reportes": ["reporte", "reportes", "lista citas", "citas agendadas", "reservas activas", "ver citas", "lista de citas", "ver reservas", "lista de reservas", "citas pendientes", "reservas pendientes", "mostrar citas", "mostrar reservas"],
}


def _normalizar(texto):
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
    }
    for acento, sin_acento in reemplazos.items():
        texto = texto.replace(acento, sin_acento)
    return texto


def _coincide_patron(patron, mensaje):
    mensaje_norm = _normalizar(mensaje)
    patron_norm = _normalizar(patron)
    palabras = patron.split()
    if len(palabras) == 1:
        return (
            re.search(r'\b' + re.escape(patron) + r'\b', mensaje) is not None
            or re.search(r'\b' + re.escape(patron_norm) + r'\b', mensaje_norm) is not None
        )
    return patron in mensaje or patron_norm in mensaje_norm


PALABRAS_CLAVE_DESEMPATE = {
    "cancelar": "cita_cancelar",
    "cancelacion": "cita_cancelar",
    "cancelación": "cita_cancelar",
    "anular": "cita_cancelar",
    "comprar": "reserva_crear",
    "vender": "reserva_crear",
    "agendar": "cita_agendar",
    "reservar": "cita_agendar",
    "pagar": "pago",
    "pago": "pago",
    "emergencia": "emergencia",
    "urgencia": "urgencia",
}


def detectar_intencion(mensaje):
    mensaje = mensaje.lower().strip()
    puntajes = {}

    for intencion, patrones in INTENCIONES.items():
        puntaje = 0
        for patron in patrones:
            if _coincide_patron(patron, mensaje):
                puntaje += len(patron.split())
            palabras_patron = patron.split()
            if mensaje.startswith(patron) and (len(palabras_patron) > 1 or len(mensaje) < len(patron) + 10):
                puntaje += len(palabras_patron) * 2
        if puntaje > 0:
            puntajes[intencion] = puntaje

    if not puntajes:
        return "consulta_general"

    palabras_msg = set(mensaje.split())
    for palabra_clave, intencion_asignada in PALABRAS_CLAVE_DESEMPATE.items():
        if palabra_clave in palabras_msg and intencion_asignada in puntajes:
            puntajes[intencion_asignada] += 5

    ESPECIALIDADES = [
        "medicina", "pediatria", "pediatría", "ginecologia", "ginecología",
        "cardiologia", "cardiología", "dermatologia", "dermatología",
        "psicologia", "psicología", "especialidad",
    ]
    if "servicio_especifico" in puntajes:
        for esp in ESPECIALIDADES:
            if esp in palabras_msg:
                puntajes["servicio_especifico"] += 3
                break

    max_puntaje = max(puntajes.values())
    candidatos = [k for k, v in puntajes.items() if v == max_puntaje]

    if len(candidatos) > 1:
        orden = [
            "cita_cancelar", "cita_agendar",
            "reserva_crear",
            "servicio_especifico",
            "emergencia", "transferir",
            "reportes",
            "pago", "horarios", "precios", "ubicacion", "contacto",
            "informacion", "faq",
            "fechas_disponibles",
            "cita_consultar", "reserva_consultar",
            "saludo", "gracias", "despedida",
            "consulta_general",
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

    from datetime import datetime, timedelta
    hoy = datetime.now()
    dias_semana = {"lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6}
    for nombre, idx in dias_semana.items():
        if f" {nombre}" in mensaje_lower or mensaje_lower.startswith(nombre):
            diff = (idx - hoy.weekday()) % 7
            if diff == 0:
                diff = 7
            dia = hoy + timedelta(days=diff)
            entidades["fecha"] = dia.strftime("%d/%m/%Y")
            break
    if "fecha" not in entidades:
        if "pasado manana" in mensaje_lower or "pasado mañana" in mensaje_lower or "pasadomanana" in mensaje_lower:
            pasado = hoy + timedelta(days=2)
            entidades["fecha"] = pasado.strftime("%d/%m/%Y")
        elif "manana" in mensaje_lower or "mañana" in mensaje_lower:
            manana = hoy + timedelta(days=1)
            entidades["fecha"] = manana.strftime("%d/%m/%Y")
        elif "hoy" in mensaje_lower:
            entidades["fecha"] = hoy.strftime("%d/%m/%Y")

    hora_pattern = r"\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b"
    hora_match = re.search(hora_pattern, mensaje)
    if hora_match:
        entidades["hora"] = hora_match.group(0)

    telefono_pattern = r"\b(\+?\d{1,3}\s?\d{7,10})\b"
    telefono_match = re.search(telefono_pattern, mensaje)
    if telefono_match:
        entidades["telefono"] = telefono_match.group(1).strip()

    nombre_patterns = [
        r"(?:llamo|soy|nombre es|me llamo|mi nombre es|nombre)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+?)(?:\.|,|$|y\s+mi\s+teléfono)",
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
