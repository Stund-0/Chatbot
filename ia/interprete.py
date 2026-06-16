import os
import re

# Lista de especialidades médicas que ofrece el servicio
ESPECIALIDADES = [
    "medicina general", "pediatría", "pediatria", "ginecología", "ginecologia",
    "cardiología", "cardiologia", "dermatología", "dermatologia", "psicología", "psicologia",
    "medicina interna", "medicina familiar",
]

# Palabras clave para identificar menciones a especialidades en el mensaje
PALABRAS_ESPECIALIDAD = [
    "medicina", "pediatria", "pediatría", "ginecologia", "ginecología",
    "cardiologia", "cardiología", "dermatologia", "dermatología",
    "psicologia", "psicología", "especialidad", "especialidades",
]

# Diccionario principal de intenciones: cada clave es una intención y su valor es una lista de patrones
INTENCIONES = {
    # Saludos y apertura de conversación
    "saludo": ["hola", "buenos días", "buenas tardes", "buenas noches", "qué tal", "hey", "saludos", "buen día", "buenas", "qué hay", "cómo estás", "como estas", "que tal", "que hay", "como estas", "buen dia", "buenos dias"],
    # Solicitudes de información general sobre la empresa
    "informacion": ["qué hacen", "qué ofrecen", "información", "informacion", "servicios", "productos", "conocen", "a qué se dedican", "a que se dedican", "qué ofrecen", "que ofrecen", "me pueden decir", "que hacen"],
    # Consultas sobre horarios de atención
    "horarios": ["horario", "horarios", "atienden", "abren", "cierran", "cuándo atienden", "días de atención", "días de atención", "dias de atencion", "qué días trabajan", "que dias trabajan", "están abiertos", "estan abiertos"],
    # Preguntas sobre precios y costos
    "precios": ["precio", "precios", "cuánto cuesta", "costo", "costos", "tarifa", "valor", "cuesta", "cuanto cuesta", "cuánto vale", "cuanto vale", "cuánto cobran", "cuanto cobran", "cuánto sale", "cuanto sale", "qué precio tiene", "que precio tiene", "precio de", "de precio"],
    # Consultas sobre ubicación y direcciones
    "ubicacion": ["dirección", "ubicación", "ubicacion", "dónde están", "dónde queda", "donde estan", "donde queda", "ubicados", "direccion", "cómo llegar", "como llegar", "mapa", "dónde se ubican", "donde se ubican", "lugar", "lugares", "en qué lugar", "en que lugar", "qué lugar", "que lugar"],
    # Agendar una nueva cita médica
    "cita_agendar": ["agendar", "cita", "consulta", "agenda", "reservar cita", "quiero una cita", "necesito una cita", "programar cita", "sacar cita", "pedir cita"],
    # Consultar el estado de una cita existente
    "cita_consultar": ["mi cita", "consultar cita", "ver cita", "estado de mi cita", "tengo una cita", "consulta mi cita", "revisar mi cita", "cómo va mi cita", "como va mi cita", "quiero ver mi cita", "quiero consultar mi cita", "ver mi cita"],
    # Cancelar una cita agendada
    "cita_cancelar": ["cancelar", "cancelación", "cancelacion", "cancelar cita", "anular cita", "anular"],
    # Crear una reserva de producto
    "reserva_crear": ["reservar", "apartar", "quiero comprar", "ordenar", "pedido", "comprar", "producto", "hacer una reserva"],
    # Consultar el estado de una reserva
    "reserva_consultar": ["mi reserva", "mi pedido", "consultar reserva", "estado de mi pedido", "ver reserva", "consultar mi pedido", "ver mi reserva"],
    # Información de contacto (teléfono, correo, WhatsApp)
    "contacto": ["teléfono", "telefono", "correo", "contacto", "comunicarme", "llamar", "email", "whatsapp", "cuál es su número", "cual es su numero", "dónde llamo", "donde llamo"],
    # Consulta sobre un servicio o especialidad específica
    "servicio_especifico": ESPECIALIDADES + ["especialidad", "especialidades"],
    # Métodos y formas de pago
    "pago": ["pagar", "pago", "métodos de pago", "formas de pago", "transferencia", "tarjeta", "métodos de pago", "formas de pago"],
    # Situaciones de emergencia o urgencia
    "emergencia": ["emergencia", "urgencia", "grave", "accidente", "duele", "ayuda urgente", "necesito ayuda"],
    # Solicitud de transferencia a un operador humano
    "transferir": ["persona", "humano", "asesor", "operador", "hablar con alguien", "transferir", "agente", "atención personal", "atencion personal"],
    # Expresiones de agradecimiento
    "gracias": ["gracias", "muchas gracias", "agradezco", "thanks", "muy amable", "te agradezco"],
    # Despedidas y cierre de conversación
    "despedida": ["adiós", "adios", "nos vemos", "hasta luego", "bye", "chao", "hasta pronto"],
    # Preguntas frecuentes
    "faq": ["preguntas frecuentes", "faq", "dudas frecuentes", "preguntas comunes"],
    # Consulta de fechas y disponibilidad
    "fechas_disponibles": ["fechas disponibles", "fechas libres", "días disponibles", "días libres", "dias disponibles", "dias libres", "esta semana", "este mes", "fechas ocupadas", "días ocupados", "dias ocupados", "qué fecha", "que fecha", "cuándo hay", "cuando hay", "tiene libre", "tienes libre", "están reservados", "estan reservados"],
    # Reportes y listados de citas o reservas
    "reportes": ["reporte", "reportes", "lista citas", "citas agendadas", "reservas activas", "ver citas", "lista de citas", "ver reservas", "lista de reservas", "citas pendientes", "reservas pendientes", "mostrar citas", "mostrar reservas"],
}


def _normalizar(texto):
    """Normaliza el texto eliminando tildes y caracteres especiales."""
    # Mapa de reemplazo: caracteres acentuados -> su versión sin acento
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
    }
    # Aplica cada reemplazo al texto
    for acento, sin_acento in reemplazos.items():
        texto = texto.replace(acento, sin_acento)
    return texto


def _coincide_patron(patron, mensaje):
    """Verifica si un patrón aparece en el mensaje, normalizando ambos."""
    mensaje_norm = _normalizar(mensaje)
    patron_norm = _normalizar(patron)
    palabras = patron.split()
    # Si el patrón es una sola palabra, usa búsqueda por palabra completa
    if len(palabras) == 1:
        return (
            re.search(r'\b' + re.escape(patron) + r'\b', mensaje) is not None
            or re.search(r'\b' + re.escape(patron_norm) + r'\b', mensaje_norm) is not None
        )
    # Para patrones de varias palabras, busca coincidencia exacta
    return patron in mensaje or patron_norm in mensaje_norm


# Palabras clave de desempate: refuerzan una intención específica cuando aparecen en el mensaje
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
    """Detecta la intención principal de un mensaje del usuario."""
    mensaje = mensaje.lower().strip()                   # Normaliza el mensaje a minúsculas
    puntajes = {}                                       # Diccionario intención -> puntaje acumulado

    # Recorre todas las intenciones y sus patrones para calcular puntajes
    for intencion, patrones in INTENCIONES.items():
        puntaje = 0
        for patron in patrones:
            # Suma puntos según la longitud del patrón si coincide
            if _coincide_patron(patron, mensaje):
                puntaje += len(patron.split())
            palabras_patron = patron.split()
            # Bonus si el mensaje comienza exactamente con el patrón
            if mensaje.startswith(patron) and (len(palabras_patron) > 1 or len(mensaje) < len(patron) + 10):
                puntaje += len(palabras_patron) * 2
        if puntaje > 0:
            puntajes[intencion] = puntaje

    # Si no hay ninguna coincidencia, devuelve intención genérica
    if not puntajes:
        return "consulta_general"

    # Aplica palabras clave de desempate para reforzar ciertas intenciones
    palabras_limpias = re.sub(r'[^\w\s]', '', mensaje)
    palabras_msg = set(palabras_limpias.split())
    for palabra_clave, intencion_asignada in PALABRAS_CLAVE_DESEMPATE.items():
        if palabra_clave in palabras_msg and intencion_asignada in puntajes:
            puntajes[intencion_asignada] += 5

    # Refuerza la intención de servicio_especifico si hay palabras de especialidad
    if "servicio_especifico" in puntajes:
        for esp in PALABRAS_ESPECIALIDAD:
            if esp in palabras_msg:
                puntajes["servicio_especifico"] += 3
                break

    # Encuentra la(s) intención(es) con mayor puntaje
    max_puntaje = max(puntajes.values())
    candidatos = [k for k, v in puntajes.items() if v == max_puntaje]

    # Si hay empate, usa un orden de prioridad predefinido para desempatar
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


# Conjunto de intenciones consideradas informativas (no requieren acción inmediata)
INTENCIONES_INFORMATIVAS = {"horarios", "precios", "ubicacion", "contacto", "informacion", "servicio_especifico", "faq", "fechas_disponibles", "pago"}


def detectar_intenciones_multiples(mensaje):
    """Detecta múltiples intenciones informativas en un mismo mensaje."""
    mensaje = mensaje.lower().strip()                   # Normaliza el mensaje
    puntajes = {}                                       # Diccionario intención -> puntaje acumulado

    # Recorre todas las intenciones y sus patrones (misma lógica que detectar_intencion)
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
        return [("consulta_general", 0)]

    # Aplica palabras clave de desempate
    palabras_limpias = re.sub(r'[^\w\s]', '', mensaje)
    palabras_msg = set(palabras_limpias.split())
    for palabra_clave, intencion_asignada in PALABRAS_CLAVE_DESEMPATE.items():
        if palabra_clave in palabras_msg and intencion_asignada in puntajes:
            puntajes[intencion_asignada] += 5

    # Refuerza servicio_especifico si hay palabras de especialidad
    if "servicio_especifico" in puntajes:
        for esp in PALABRAS_ESPECIALIDAD:
            if esp in palabras_msg:
                puntajes["servicio_especifico"] += 3
                break

    # Filtra solo las intenciones informativas
    informativas = [(k, v) for k, v in puntajes.items() if k in INTENCIONES_INFORMATIVAS]

    # Si hay dos o más intenciones informativas, las devuelve ordenadas por puntaje y prioridad
    if len(informativas) >= 2:
        result = [(k, v) for k, v in informativas if v >= 1]
        if len(result) >= 2:
            orden = ["servicio_especifico", "pago", "horarios", "precios", "ubicacion", "contacto", "informacion", "faq", "fechas_disponibles"]
            result.sort(key=lambda x: (-x[1], orden.index(x[0]) if x[0] in orden else 999))
            return result

    # Si no hay múltiples informativas, aplica desempate por prioridad
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
                return [(ref, max_puntaje)]
    return [(candidatos[0], max_puntaje)]


def extraer_entidades(mensaje):
    """Extrae entidades estructuradas (fecha, hora, teléfono, nombre, etc.) del mensaje."""
    mensaje_lower = mensaje.lower()
    entidades = {}

    # Extrae fechas en formato dd/mm/aaaa o dd-mm-aaaa
    fecha_pattern = r"\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b"
    fecha_match = re.search(fecha_pattern, mensaje)
    if fecha_match:
        dia, mes, anio = fecha_match.groups()
        if len(anio) == 2:
            anio = "20" + anio
        entidades["fecha"] = f"{dia:0>2}/{mes:0>2}/{anio}"

    # Detecta días de la semana y calcula la fecha correspondiente
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
    # Detecta referencias relativas: pasado mañana, mañana, hoy
    if "fecha" not in entidades:
        if "pasado manana" in mensaje_lower or "pasado mañana" in mensaje_lower or "pasadomanana" in mensaje_lower:
            pasado = hoy + timedelta(days=2)
            entidades["fecha"] = pasado.strftime("%d/%m/%Y")
        elif "manana" in mensaje_lower or "mañana" in mensaje_lower:
            manana = hoy + timedelta(days=1)
            entidades["fecha"] = manana.strftime("%d/%m/%Y")
        elif "hoy" in mensaje_lower:
            entidades["fecha"] = hoy.strftime("%d/%m/%Y")

    # Extrae hora en formato HH:MM AM/PM
    hora_pattern = r"\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b"
    hora_match = re.search(hora_pattern, mensaje)
    if hora_match:
        entidades["hora"] = hora_match.group(0)

    # Extrae número de teléfono (con o sin código de país)
    telefono_pattern = r"\b(\+?\d{1,3}\s?\d{7,10})\b"
    telefono_match = re.search(telefono_pattern, mensaje)
    if telefono_match:
        entidades["telefono"] = telefono_match.group(1).strip()

    # Extrae nombre del usuario a partir de frases como "me llamo", "soy", etc.
    nombre_patterns = [
        r"(?:llamo|soy|nombre es|me llamo|mi nombre es|nombre)\s*:?\s*([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+?)(?:\.|,|telefono|teléfono|especialidad|fecha|horario|$)",
        r"(?:soy)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+?)$",
    ]
    for pattern in nombre_patterns:
        nombre_match = re.search(pattern, mensaje_lower, re.IGNORECASE)
        if nombre_match:
            nombre = nombre_match.group(1).strip().title()
            if len(nombre) > 2:
                entidades["nombre"] = nombre
                break

    # Extrae especialidad médica mencionada
    for esp in ESPECIALIDADES:
        if esp in mensaje_lower:
            entidades["especialidad"] = esp.title()
            break

    # Extrae cantidad de productos (unidades, piezas, kg, litros)
    cantidad_pattern = r"(\d+)\s*(?:unidad|unidades|pieza|piezas|kg|litro|litros)"
    cantidad_match = re.search(cantidad_pattern, mensaje_lower)
    if cantidad_match:
        entidades["cantidad"] = int(cantidad_match.group(1))

    return entidades


