import json
import logging
import os
import re
from datetime import datetime, timedelta

import pytz

logger = logging.getLogger(__name__)

# Zona horaria configurable (default: CDMX)
ZONA_HORARIA = pytz.timezone(os.getenv("TZ", "America/Mexico_City"))
# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Función auxiliar: elimina acentos y diéresis para comparaciones
def _normalizar(texto):
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
    }
    for acento, sin_acento in reemplazos.items():
        texto = texto.replace(acento, sin_acento)
    return texto


class Chatbot:
    # Inicializa el chatbot: configuración, datos, mensajes y contexto por usuario
    def __init__(self, modo_simulacion=True, sender=None):
        self.modo_simulacion = modo_simulacion  # Modo simulación (sin enviar WhatsApp real)
        self.sender = sender                    # Objeto sender para enviar mensajes reales
        self.config = self._cargar_config()     # Carga config desde archivos
        self.datos = {}                         # Diccionario con contenido de archivos .txt (información)
        self.mensajes = {}                      # Diccionario con templates de mensajes de respuesta
        self.contextos = {}                     # Contexto de conversación por número de teléfono
        self._cargar_archivos()                 # Lee directorios datos/ y mensajes/

    # Intenciones que reinician el flujo de captura de datos
    INTENCIONES_RESET = {"saludo", "emergencia", "transferir", "despedida", "cita_cancelar", "faq", "reportes", "gracias"}
    # Intenciones que solo consultan información (no requieren captura de datos)
    INTENCIONES_INFORMATIVAS = {"horarios", "precios", "ubicacion", "contacto", "informacion", "servicio_especifico", "faq", "fechas_disponibles", "pago"}

    # Recupera el contexto guardado para un número de teléfono
    def _obtener_contexto(self, numero):
        if not numero:
            return None
        return self.contextos.get(numero)

    # Guarda o elimina el contexto de conversación para un número
    def _guardar_contexto(self, numero, contexto):
        if not numero:
            return
        if contexto:
            self.contextos[numero] = contexto
        else:
            self.contextos.pop(numero, None)

    # Construye una ruta absoluta dentro del directorio base del proyecto
    def _ruta(self, *parts):
        return os.path.join(BASE_DIR, *parts)

    # Carga configuración desde empresa.txt y settings.json
    def _cargar_config(self):
        config = {}
        config_path = self._ruta("config", "empresa.txt")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        config[key.strip().lower()] = value.strip()

        settings_path = self._ruta("config", "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                config.update(json.load(f))

        return config

    # Lee todos los archivos .txt de datos/ y mensajes/ en diccionarios
    def _cargar_archivos(self):
        data_dir = self._ruta("datos")
        mensajes_dir = self._ruta("mensajes")

        # Crea los directorios si no existen
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.isdir(mensajes_dir):
            os.makedirs(mensajes_dir, exist_ok=True)

        # Carga archivos de datos (información del negocio)
        for archivo in os.listdir(data_dir):
            ruta = os.path.join(data_dir, archivo)
            if os.path.isfile(ruta) and archivo.endswith(".txt"):
                clave = archivo.replace(".txt", "")
                with open(ruta, "r", encoding="utf-8") as f:
                    self.datos[clave] = f.read()

        # Carga archivos de mensajes (templates de respuesta)
        for archivo in os.listdir(mensajes_dir):
            ruta = os.path.join(mensajes_dir, archivo)
            if os.path.isfile(ruta) and archivo.endswith(".txt"):
                clave = archivo.replace(".txt", "")
                with open(ruta, "r", encoding="utf-8") as f:
                    self.mensajes[clave] = f.read()

    # Reemplaza placeholders {{VARIABLE}} en un texto con valores reales
    def _reemplazar_variables(self, texto, variables=None):
        if variables is None:
            variables = {}

        nombre_empresa = self.config.get("nombre", "Mi Negocio")
        eslogan = self.config.get("eslogan", "")
        horarios = self.datos.get("horarios", "")
        telefonos = self.datos.get("telefonos", "")
        telefono_principal = ""

        # Extrae el teléfono principal/WhatsApp de la lista de teléfonos
        for line in telefonos.split("\n"):
            if "Principal" in line or "WhatsApp" in line:
                partes = line.split(":")
                if len(partes) > 1:
                    telefono_principal = partes[1].strip()

        reemplazos = {
            "{{NOMBRE_EMPRESA}}": nombre_empresa,
            "{{ESLOGAN}}": eslogan,
            "{{HORARIOS}}": horarios,
            "{{TELEFONO}}": variables.get("telefono", telefono_principal),
            "{{TELEFONO_PRINCIPAL}}": telefono_principal,
            "{{NOMBRE}}": variables.get("nombre", ""),
            "{{ESPECIALIDAD}}": variables.get("especialidad", ""),
            "{{FECHA}}": variables.get("fecha", ""),
            "{{HORA}}": variables.get("hora", ""),
            "{{PRODUCTO}}": variables.get("producto", ""),
            "{{CANTIDAD}}": str(variables.get("cantidad", "1")),
            "{{FOLIO}}": variables.get("folio", ""),
            "{{FOLIO_CANCELACION}}": variables.get("folio_cancelacion", ""),
            "{{NOMBRE_CLIENTE}}": variables.get("nombre_cliente", ""),
            "{{TELEFONO_CLIENTE}}": variables.get("telefono_cliente", ""),
            "{{MENSAJE_CLIENTE}}": variables.get("mensaje_cliente", ""),
        }

        for placeholder, valor in reemplazos.items():
            texto = texto.replace(placeholder, valor)

        return texto

    # Busca coincidencias de palabras clave en los archivos de datos
    def _buscar_en_archivos(self, consulta):
        consulta_norm = _normalizar(consulta.lower())
        palabras_clave = consulta_norm.split()

        # Orden de prioridad de archivos para la búsqueda
        orden_busqueda = [
            "preguntas_frecuentes",
            "productos",
            "servicios",
            "precios",
            "informacion",
            "horarios",
            "direccion",
            "telefonos",
            "correo",
        ]

        resultados = []

        # Busca por secciones dentro de cada archivo y calcula relevancia
        for archivo in orden_busqueda:
            contenido = self.datos.get(archivo, "")
            if not contenido:
                continue

            # Divide el contenido en secciones separadas por marcadores === ... ===
            lineas = contenido.split("\n")
            secciones = []
            seccion_actual = []
            for linea in lineas:
                if linea.startswith("=== ") and linea.endswith(" ==="):
                    if seccion_actual:
                        secciones.append("\n".join(seccion_actual))
                    seccion_actual = [linea]
                else:
                    seccion_actual.append(linea)
            if seccion_actual:
                secciones.append("\n".join(seccion_actual))

            # Cuenta cuántas palabras clave coinciden en cada sección
            for seccion in secciones:
                seccion_norm = _normalizar(seccion.lower())
                coincidencias = sum(
                    1 for palabra in palabras_clave if len(palabra) > 3 and palabra in seccion_norm
                )
                if coincidencias > 0:
                    resultados.append({
                        "archivo": archivo,
                        "contenido": seccion,
                        "relevancia": coincidencias,
                    })

        # Ordena por relevancia descendente y devuelve el mejor resultado
        resultados.sort(key=lambda x: x["relevancia"], reverse=True)

        if resultados:
            return resultados[0]["contenido"]

        # Fallback: si no hay sección completa, busca línea por línea
        for archivo in orden_busqueda:
            contenido = self.datos.get(archivo, "")
            if contenido:
                lineas = contenido.strip().split("\n")
                lineas_utiles = [l for l in lineas if not l.startswith("===") and l.strip()]
                for linea in lineas_utiles:
                    linea_norm = _normalizar(linea.lower())
                    for palabra in palabras_clave:
                        if len(palabra) > 3 and palabra in linea_norm:
                            return linea

        return None

    # Busca información de un servicio por nombre en datos/servicios.txt
    def _obtener_info_servicio(self, servicio_buscado):
        servicios = self.datos.get("servicios", "")
        if not servicios:
            return None

        servicio_norm = _normalizar(servicio_buscado.lower().strip())
        secciones = servicios.split("\n\n")

        for seccion in secciones:
            if servicio_norm in _normalizar(seccion.lower()):
                return seccion.strip()

        return None

    # Busca el precio de un ítem en datos/precios.txt
    def _obtener_precio(self, item):
        precios = self.datos.get("precios", "")
        if not precios:
            return None

        item_norm = _normalizar(item.lower().strip())
        lineas = precios.split("\n")
        # Coincidencia exacta del nombre en la línea
        for linea in lineas:
            if ":" in linea and item_norm in _normalizar(linea.lower()):
                return linea.strip()

        # Coincidencia parcial con palabras clave
        for linea in lineas:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                palabras_clave = item_norm.split()
                if any(p in _normalizar(clave.lower()) for p in palabras_clave if len(p) > 3):
                    return linea.strip()

        return None

    # Busca información de un producto por nombre en datos/productos.txt
    def _obtener_producto(self, producto_buscado):
        productos = self.datos.get("productos", "")
        if not productos:
            return None

        producto_norm = _normalizar(producto_buscado.lower().strip())
        secciones = productos.split("\n\n")

        # Coincidencia exacta del nombre en la sección
        for seccion in secciones:
            if producto_norm in _normalizar(seccion.lower()):
                return seccion.strip()

        # Coincidencia parcial con palabras clave
        for seccion in secciones:
            palabras = producto_norm.split()
            if any(p in _normalizar(seccion.lower()) for p in palabras if len(p) > 3):
                return seccion.strip()

        return None

    # Parsea un rango horario "8-18" a tupla de floats (inicio, fin)
    @staticmethod
    def _parse_hour_range(val):
        parts = val.split("-", 1)
        return float(parts[0]), float(parts[1])

    # Verifica si la hora actual está dentro del horario laboral
    def _esta_en_horario_laboral(self):
        if self.modo_simulacion:
            return True  # En simulación siempre está "dentro de horario"
        ahora = datetime.now(ZONA_HORARIA)
        dia_semana = ahora.weekday()
        hora_actual = ahora.hour + ahora.minute / 60

        # Rangos configurables vía variables de entorno
        weekday_range = os.getenv("HORARIO_WEEKDAY", "8-18")
        saturday_range = os.getenv("HORARIO_SATURDAY", "9-14")
        weekday_start, weekday_end = self._parse_hour_range(weekday_range)
        saturday_start, saturday_end = self._parse_hour_range(saturday_range)

        if dia_semana < 5:
            return weekday_start <= hora_actual < weekday_end
        elif dia_semana == 5:
            return saturday_start <= hora_actual < saturday_end
        else:
            return False  # Domingos: sin atención

    # Carga los slots disponibles por día desde datos/horarios_disponibles.txt
    def _cargar_slots_horarios(self):
        slots_semana = {"0": [], "1": [], "2": [], "3": [], "4": [], "5": [], "6": []}
        horarios_raw = self.datos.get("horarios_disponibles", "")
        if not horarios_raw:
            return slots_semana

        secciones = horarios_raw.split("\n\n")
        for seccion in secciones:
            # Extrae slots de lunes a viernes
            if "Lunes a Viernes" in seccion or "lunes a viernes" in seccion.lower():
                slots = []
                for linea in seccion.split("\n"):
                    l = linea.strip()
                    if l and not l.startswith("Lunes") and not l.startswith("lunes") and not l.startswith("Sáb") and not l.startswith("sáb") and not l.startswith("==="):
                        slots.append(l)
                for k in ["0", "1", "2", "3", "4"]:
                    slots_semana[k] = list(slots)
            # Extrae slots de sábados
            elif "Sáb" in seccion or "sáb" in seccion.lower():
                slots = []
                for linea in seccion.split("\n"):
                    l = linea.strip()
                    if l and not l.startswith("Sáb") and not l.startswith("sáb") and not l.startswith("==="):
                        slots.append(l)
                slots_semana["5"] = slots

        return slots_semana

    # Formatea los horarios disponibles legibles, opcionalmente filtrados por fecha
    def _formatear_horarios_disponibles(self, fecha=None):
        horarios_raw = self.datos.get("horarios_disponibles", "")
        if not horarios_raw:
            return self.datos.get("horarios", "No disponible")

        secciones = horarios_raw.split("\n\n")
        etiqueta_dia = None
        if fecha:
            # Determina qué día de la semana es la fecha solicitada
            dia_semana = datetime.strptime(fecha, "%d/%m/%Y").weekday()
            if dia_semana < 5:
                etiqueta_dia = "Lunes a Viernes"
            elif dia_semana == 5:
                etiqueta_dia = "Sábados"
            else:
                return "No hay atención los domingos."

        # Filtra por etiqueta si se especificó fecha
        if etiqueta_dia:
            for seccion in secciones:
                if etiqueta_dia in seccion:
                    lineas = [l.strip() for l in seccion.split("\n") if l.strip() and not l.startswith("===") and not l.startswith("Lunes") and not l.startswith("Sáb")]
                    break
            else:
                return "No disponible"
        else:
            # Sin fecha: une todos los slots sin duplicados
            vistas = set()
            lineas = []
            for seccion in secciones:
                for l in seccion.split("\n"):
                    l = l.strip()
                    if l and not l.startswith("===") and not l.startswith("Lunes") and not l.startswith("Sáb"):
                        if l not in vistas:
                            lineas.append(l)
                            vistas.add(l)

        # Excluye horarios ya ocupados en la BD para esa fecha
        if fecha:
            from database.consultas import buscar_citas_por_fecha
            ocupadas = {c["hora"].strip() for c in buscar_citas_por_fecha(fecha)}
            if ocupadas:
                lineas = [l for l in lineas if l not in ocupadas]

        if not lineas:
            return "No hay horarios disponibles para esta fecha."

        return "\n".join(lineas)

    # Obtiene el número del administrador desde config o variable de entorno
    def _obtener_numero_admin(self):
        admin_tel = self.config.get("admin_telefono", "")
        if not admin_tel:
            admin_tel = os.getenv("ADMIN_TELEFONO", "")
        return admin_tel.replace("+", "").replace(" ", "").replace("-", "")

    # Procesa comandos especiales del administrador (CONFIRMAR / RECHAZAR citas)
    def _manejar_comando_admin(self, mensaje_usuario, numero_usuario):
        from database.consultas import confirmar_cita, rechazar_cita, buscar_cita_por_folio
        from whatsapp.notificaciones import notificar_admin

        # Solo el número de admin puede ejecutar comandos
        if not numero_usuario:
            return None
        numero_limpio = numero_usuario.replace("+", "").replace(" ", "").replace("-", "")
        admin_limpio = self._obtener_numero_admin()
        if numero_limpio != admin_limpio:
            return None

        # Parsea el comando: CONFIRMAR <folio> o RECHAZAR <folio>
        msg = mensaje_usuario.strip()
        cmd_parts = msg.split(None, 1)
        if len(cmd_parts) != 2:
            return None

        comando, argumento = cmd_parts
        comando = comando.upper()
        argumento = argumento.strip()

        if comando in ("CONFIRMAR", "RECHAZAR"):
            # Busca la cita por folio en la base de datos
            try:
                cita = buscar_cita_por_folio(argumento)
            except Exception:
                logger.exception("Error buscando cita %s", argumento)
                return {
                    "respuesta": f"Error al buscar la cita {argumento}. Intenta de nuevo.",
                    "intencion": "admin_comando",
                    "transferir": False,
                }
            if not cita:
                return {
                    "respuesta": f"No encontré ninguna cita con folio {argumento}.",
                    "intencion": "admin_comando",
                    "transferir": False,
                }
            # CONFIRMAR: aprueba la cita y notifica al usuario
            if comando == "CONFIRMAR":
                exito = confirmar_cita(argumento)
                if exito:
                    msg_usuario = (
                        f"✅ *Tu cita ha sido confirmada!*\n\n"
                        f"▪️ *Folio:* {cita['folio']}\n"
                        f"▪️ *Especialidad:* {cita['especialidad']}\n"
                        f"▪️ *Fecha:* {cita['fecha']}\n"
                        f"▪️ *Hora:* {cita['hora']}\n\n"
                        f"Te esperamos! 🏥"
                    )
                    # Envía notificación al usuario (simulado o real)
                    if self.modo_simulacion:
                        print(f"\n[ENVIANDO CONFIRMACION A USUARIO {cita['telefono']}]: {msg_usuario}\n")
                    elif self.sender:
                        try:
                            self.sender.enviar_texto(cita["telefono"], msg_usuario)
                        except Exception:
                            logger.exception("Error enviando confirmacion al cliente %s", cita["telefono"])
                    return {
                        "respuesta": f"✅ Cita {argumento} confirmada. El usuario ha sido notificado.",
                        "intencion": "admin_comando",
                        "transferir": False,
                    }
                else:
                    return {
                        "respuesta": f"No se pudo confirmar la cita {argumento}. Verifica que esté en estado 'pendiente_confirmacion'.",
                        "intencion": "admin_comando",
                        "transferir": False,
                    }
            # RECHAZAR: rechaza la cita y ofrece horarios alternativos al usuario
            if comando == "RECHAZAR":
                exito = rechazar_cita(argumento)
                if exito:
                    horarios = self._formatear_horarios_disponibles(cita["fecha"])
                    msg_usuario = (
                        f"⚠️ *Cita no disponible*\n\n"
                        f"Lo sentimos, la hora solicitada para el {cita['fecha']} a las {cita['hora']} "
                        f"ya no está disponible.\n\n"
                        f"*Horarios disponibles para esa fecha:*\n{horarios}\n\n"
                        f"Por favor, elige un nuevo horario y vuelve a solicitarlo. 🙏"
                    )
                    if self.modo_simulacion:
                        print(f"\n[ENVIANDO RECHAZO A USUARIO {cita['telefono']}]: {msg_usuario}\n")
                    elif self.sender:
                        try:
                            self.sender.enviar_texto(cita["telefono"], msg_usuario)
                        except Exception:
                            logger.exception("Error enviando rechazo al cliente %s", cita["telefono"])
                    return {
                        "respuesta": f"❌ Cita {argumento} rechazada. El usuario ha sido notificado con horarios disponibles.",
                        "intencion": "admin_comando",
                        "transferir": False,
                    }
                else:
                    return {
                        "respuesta": f"No se pudo rechazar la cita {argumento}. Verifica que esté en estado 'pendiente_confirmacion'.",
                        "intencion": "admin_comando",
                        "transferir": False,
                    }

        return None

    # Texto promocional que se agrega al final de respuestas informativas
    OFERTA_AGENDAR = "\n\n¿Te gustaría agendar una cita? Solo envíame tus datos: nombre, teléfono, especialidad, fecha y horario."

    # Valida formato de teléfono, fecha y hora para una cita
    def _validar_datos_cita(self, entidades):
        errores = []
        telefono = entidades.get("telefono", "")
        if telefono and not re.match(r'^\+?\d{8,15}$', telefono.replace(" ", "")):
            errores.append("teléfono (debe tener entre 8 y 15 dígitos)")
        fecha = entidades.get("fecha", "")
        if fecha:
            try:
                fecha_dt = datetime.strptime(fecha, "%d/%m/%Y")
                if fecha_dt.date() < datetime.now().date():
                    errores.append("fecha (no puede ser una fecha pasada)")
            except ValueError:
                errores.append("fecha (formato inválido, usa dd/mm/aaaa)")
        hora = entidades.get("hora", "")
        if hora and not re.match(r'^\d{1,2}:\d{2}\s*(AM|PM|am|pm)?$', hora.strip()):
            errores.append("hora (formato inválido, usa HH:MM AM/PM)")
        return errores

    # Verifica si están presentes todos los campos obligatorios para agendar
    def _datos_completos_para_cita(self, entidades):
        return all(entidades.get(k) for k in ("nombre", "especialidad", "fecha", "hora"))

    # Verifica si están presentes los campos mínimos para una reserva de producto
    def _datos_completos_para_reserva(self, entidades):
        return all(entidades.get(k) for k in ("nombre", "producto"))

    # Detecta si el mensaje contiene datos sueltos de cita (sin estar completo)
    def _detectar_datos_incompletos_cita(self, mensaje, entidades, intencion):
        if intencion in self.INTENCIONES_RESET:
            return False  # Intenciones de reset no activan esta detección
        if self._datos_completos_para_cita(entidades):
            return False  # Ya está completo, no hay datos incompletos
        mensaje_lower = mensaje.lower()
        # Cuenta cuántos campos de cita aparecen (2+ indica intención de agendar)
        indicios = 0
        if entidades.get("telefono"):
            indicios += 1
        if entidades.get("fecha"):
            indicios += 1
        if entidades.get("hora"):
            indicios += 1
        if entidades.get("especialidad"):
            indicios += 1
        if re.search(r'\bnombre\b', mensaje_lower):
            indicios += 1
        return indicios >= 2

    # Procesa mensajes con múltiples intenciones combinadas (ej. "horario y precio")
    def _procesar_intenciones_multiples(self, intenciones, mensaje, entidades, numero, intencion_original=None):
        # Mapa de manejadores para intenciones informativas
        gestor_respuesta = {
            "horarios": self._manejar_horarios,
            "precios": self._manejar_precios,
            "ubicacion": self._manejar_ubicacion,
            "contacto": self._manejar_contacto,
            "informacion": self._manejar_informacion_general,
            "servicio_especifico": self._manejar_servicio_especifico,
            "faq": self._manejar_faq,
            "fechas_disponibles": self._manejar_fechas_disponibles,
            "pago": self._manejar_pago,
        }

        respuestas = []
        intenciones_procesadas = set()
        esperando_datos = False
        # Ejecuta cada manejador por separado y acumula respuestas
        for intencion, _ in intenciones:
            manejador = gestor_respuesta.get(intencion)
            if manejador:
                try:
                    resultado = manejador(mensaje, entidades, numero)
                    texto = resultado["respuesta"]
                    # Remueve la oferta de agendar para evitar duplicados
                    oferta = self.OFERTA_AGENDAR
                    if texto.endswith(oferta):
                        texto = texto[:-len(oferta)]
                    respuestas.append(texto)
                    intenciones_procesadas.add(intencion)
                except Exception as e:
                    logger.exception("Error en multi-intent '%s': %s", intencion, e)
                    respuestas.append(f"Lo siento, tuve un problema al procesar la información sobre {intencion}.")

        # Si todas las intenciones fallaron, cae a consulta general
        if not respuestas:
            self._registrar_no_entendido(mensaje, numero, "multi_intent_fallido")
            return self._manejar_consulta_general(mensaje, entidades, numero)

        # Si la intención original incluía agendar cita, combina info + formulario
        if intencion_original == "cita_agendar":
            fecha_detectada = entidades.get("fecha", "")
            msg_agendar = (
                "Claro, con gusto te ayudo a agendar una cita. Por favor, proporciona los siguientes datos:\n\n"
                "1. 📝 *Nombre completo*\n"
                "2. 📱 *Teléfono de contacto*\n"
                "3. 🏥 *Especialidad deseada*\n"
            )
            if fecha_detectada:
                msg_agendar += f"4. 📅 *Fecha preferida:* {fecha_detectada}\n"
            else:
                msg_agendar += "4. 📅 *Fecha preferida (dd/mm/aaaa)*\n"
            msg_agendar += "5. 🕐 *Horario preferido*"
            # Solo muestra horarios si no se pidieron explícitamente
            if "horarios" not in intenciones_procesadas:
                horarios = self._formatear_horarios_disponibles(fecha_detectada or None)
                if fecha_detectada:
                    msg_agendar += f"\n\n*Horarios disponibles para el {fecha_detectada}:*\n{horarios}"
                else:
                    msg_agendar += f"\n\n*Horarios disponibles:*\n{horarios}"
            respuestas.append(msg_agendar)
            esperando_datos = True
            combined = "\n\n".join(respuestas)
            respuestas_enviar = list(respuestas)
        else:
            # Sin cita: combina respuestas y agrega oferta de agendar al final
            combined = "\n\n".join(respuestas)
            combined += self.OFERTA_AGENDAR
            respuestas_enviar = list(respuestas)
            respuestas_enviar.append(self.OFERTA_AGENDAR.strip())

        resultado = {
            "respuesta": combined,
            "respuestas": respuestas_enviar,
            "intencion": intenciones[0][0],
            "intenciones": [i for i, _ in intenciones],
            "transferir": False,
            "esperando_datos": esperando_datos,
        }

        # Guarda contexto si se esperan más datos del formulario de cita
        if esperando_datos:
            resultado["intencion"] = "cita_agendar"
            self._guardar_contexto(numero, {
                "intencion": "cita_agendar",
                "entidades": entidades,
                "esperando_datos": True,
            })
        else:
            self._guardar_contexto(numero, None)

        return resultado

    # Punto de entrada principal: procesa un mensaje y devuelve respuesta estructurada
    def procesar_mensaje(self, mensaje_usuario, numero_usuario=None, contexto=None):
        # 1. Verifica si es un comando de administrador (CONFIRMAR/RECHAZAR)
        resultado_admin = self._manejar_comando_admin(mensaje_usuario, numero_usuario)
        if resultado_admin:
            return resultado_admin

        # 2. Detecta intención y entidades mediante el módulo de IA
        from ia.interprete import detectar_intencion, extraer_entidades, detectar_intenciones_multiples

        intencion = detectar_intencion(mensaje_usuario)
        entidades = extraer_entidades(mensaje_usuario)

        # 3. Si los datos de cita/reserva están completos, fuerza la intención
        datos_cita_completos = self._datos_completos_para_cita(entidades)
        if datos_cita_completos and intencion not in self.INTENCIONES_RESET:
            intencion = "cita_agendar"
        elif self._datos_completos_para_reserva(entidades) and intencion not in self.INTENCIONES_RESET:
            intencion = "reserva_crear"

        # 4. Fusiona entidades del contexto externo (si se proporciona)
        if contexto:
            entidades.update(contexto)

        # 5. Recupera contexto previo de la conversación
        ctx_previo = self._obtener_contexto(numero_usuario)
        if ctx_previo and ctx_previo.get("esperando_datos"):
            # Si el usuario preguntó algo informativo, no interrumpe el flujo
            if intencion in self.INTENCIONES_INFORMATIVAS:
                self._guardar_contexto(numero_usuario, None)
                ctx_previo = None
            # Si no es intención de reset, continúa con la intención previa
            elif intencion not in self.INTENCIONES_RESET:
                intencion = ctx_previo["intencion"]
                entidades_previas = ctx_previo.get("entidades", {})
                for k, v in entidades_previas.items():
                    if k not in entidades:
                        entidades[k] = v

        # 6. Determina si está fuera de horario laboral
        self._es_fuera_horario = not self._esta_en_horario_laboral()

        # 7. Detecta datos incompletos de cita (ej. solo "fecha" y "hora") y pide completarlos
        if not ctx_previo and self._detectar_datos_incompletos_cita(mensaje_usuario, entidades, intencion):
            template = self.mensajes.get("error_formato", "No entendí los datos.")
            respuesta = self._reemplazar_variables(template)
            return {"respuesta": respuesta, "intencion": "error_formato", "transferir": False}

        # 8. Detecta múltiples intenciones en un solo mensaje (multi-intent)
        if not ctx_previo and not datos_cita_completos:
            intenciones_multi = detectar_intenciones_multiples(mensaje_usuario)
            if len(intenciones_multi) >= 2:
                msg_lower = mensaje_usuario.lower()
                tiene_cita = ("cita" in msg_lower and "agendar" in msg_lower) or "reservar cita" in msg_lower or "sacar cita" in msg_lower or "pedir cita" in msg_lower or "programar cita" in msg_lower or "necesito una cita" in msg_lower or "quiero una cita" in msg_lower
                return self._procesar_intenciones_multiples(intenciones_multi, mensaje_usuario, entidades, numero_usuario, intencion_original="cita_agendar" if tiene_cita else None)

        # 9. Mapa de todas las intenciones a sus manejadores respectivos
        gestor_respuesta = {
            "saludo": self._manejar_saludo,
            "informacion": self._manejar_informacion_general,
            "horarios": self._manejar_horarios,
            "precios": self._manejar_precios,
            "ubicacion": self._manejar_ubicacion,
            "cita_agendar": self._manejar_agendar_cita,
            "cita_consultar": self._manejar_consultar_cita,
            "cita_cancelar": self._manejar_cancelar_cita,
            "reserva_crear": self._manejar_crear_reserva,
            "reserva_consultar": self._manejar_consultar_reserva,
            "contacto": self._manejar_contacto,
            "servicio_especifico": self._manejar_servicio_especifico,
            "pago": self._manejar_pago,
            "emergencia": self._manejar_emergencia,
            "transferir": self._manejar_transferencia,
            "gracias": self._manejar_gracias,
            "despedida": self._manejar_despedida,
            "faq": self._manejar_faq,
            "fechas_disponibles": self._manejar_fechas_disponibles,
            "reportes": self._manejar_reportes,
            "consulta_general": self._manejar_consulta_general,
        }

        # 10. Ejecuta el manejador correspondiente a la intención detectada
        manejador = gestor_respuesta.get(intencion, self._manejar_consulta_general)
        respuesta = manejador(mensaje_usuario, entidades, numero_usuario)

        # 11. Guarda o limpia el contexto según si espera más datos
        if respuesta.get("esperando_datos"):
            self._guardar_contexto(numero_usuario, {
                "intencion": intencion,
                "entidades": entidades,
                "esperando_datos": True,
            })
        else:
            self._guardar_contexto(numero_usuario, None)

        return respuesta

    # Respuesta genérica para cuando se está fuera del horario laboral
    def _respuesta_fuera_horario(self):
        template = self.mensajes.get("fuera_horario", "Estamos fuera de horario.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "fuera_horario", "transferir": False}

    # Responde al saludo inicial del usuario
    def _manejar_saludo(self, mensaje, entidades, numero):
        template = self.mensajes.get("bienvenida", "¡Hola! ¿En qué puedo ayudarte?")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "saludo", "transferir": False}

    # Responde con información general del negocio o de una especialidad específica
    def _manejar_informacion_general(self, mensaje, entidades, numero):
        esp = entidades.get("especialidad", "")
        if esp:
            # Busca info + precio de la especialidad mencionada
            servicio_info = self._obtener_info_servicio(esp)
            precio = self._obtener_precio(esp)
            respuesta = ""
            if servicio_info:
                respuesta += f"📋 *{esp}*\n\n{servicio_info}\n"
            if precio:
                respuesta += f"\n💰 *Precio:* {precio.split(':', 1)[1].strip() if ':' in precio else precio}"
            if respuesta:
                respuesta += self.OFERTA_AGENDAR
                return {"respuesta": respuesta, "intencion": "informacion", "transferir": False}

        # Información general del negocio (primeras 6 líneas)
        info = self.datos.get("informacion", "")
        if info:
            lineas = [l for l in info.split("\n") if not l.startswith("===") and l.strip()]
            respuesta = "\n".join(lineas[:6])
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
        respuesta += self.OFERTA_AGENDAR
        return {"respuesta": respuesta, "intencion": "informacion", "transferir": False}

    # Muestra fechas con horarios disponibles, filtrando ocupadas de la BD
    def _manejar_fechas_disponibles(self, mensaje, entidades, numero):
        from database.consultas import buscar_ocupadas_por_rango
        from datetime import datetime, timedelta

        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        slots_semana = self._cargar_slots_horarios()

        # Determina el rango de fechas según la consulta (mes, semana o próximos 7 días)
        if "mes" in mensaje.lower():
            fecha_inicio = max(hoy.replace(day=1), hoy)
            if hoy.month == 12:
                fecha_fin = hoy.replace(year=hoy.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fecha_fin = hoy.replace(month=hoy.month+1, day=1) - timedelta(days=1)
            encabezado = f"📅 *Fechas disponibles de {meses_es[hoy.month]}:*"
        elif "semana" in mensaje.lower():
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_inicio = max(inicio_semana, hoy)
            fecha_fin = inicio_semana + timedelta(days=6)
            encabezado = f"📅 *Días disponibles de esta semana:*"
        else:
            fecha_inicio = hoy
            fecha_fin = hoy + timedelta(days=7)
            encabezado = f"📅 *Próximos días disponibles:*"

        # Consulta ocupadas en la BD y las agrupa por fecha
        ocupadas = buscar_ocupadas_por_rango(
            fecha_inicio.strftime("%d/%m/%Y"),
            fecha_fin.strftime("%d/%m/%Y"),
        )

        ocupadas_por_fecha = {}
        for o in ocupadas:
            f = o["fecha"]
            if f not in ocupadas_por_fecha:
                ocupadas_por_fecha[f] = set()
            ocupadas_por_fecha[f].add(o["hora"].strip())

        # Itera día por día mostrando los slots libres
        respuesta = encabezado + "\n\n"
        dia_actual = fecha_inicio
        while dia_actual <= fecha_fin:
            fecha_str = dia_actual.strftime("%d/%m/%Y")
            dia_idx = str(dia_actual.weekday())
            slots_dia = slots_semana.get(dia_idx, [])
            if not slots_dia:
                dia_actual += timedelta(days=1)
                continue
            ocupadas_hoy = ocupadas_por_fecha.get(fecha_str, set())
            libres = [s for s in slots_dia if s not in ocupadas_hoy]
            if libres:
                respuesta += f"▪️ *{nombres_dias[dia_actual.weekday()]} {dia_actual.strftime('%d/%m')}:* {', '.join(libres)}\n"
            else:
                respuesta += f"▪️ {nombres_dias[dia_actual.weekday()]} {dia_actual.strftime('%d/%m')}: Completamente ocupado ❌\n"
            dia_actual += timedelta(days=1)

        return {"respuesta": respuesta, "intencion": "fechas_disponibles", "transferir": False}

    # Muestra los horarios de atención general y disponibles para citas
    def _manejar_horarios(self, mensaje, entidades, numero):
        horarios = self.datos.get("horarios", "")
        disponibles = self._formatear_horarios_disponibles()
        if horarios:
            respuesta = f"📅 *Horarios de Atención:*\n\n{horarios}\n\n🕒 *Horarios Disponibles para Citas:*\n\n{disponibles}"
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
        respuesta += self.OFERTA_AGENDAR
        return {"respuesta": respuesta, "intencion": "horarios", "transferir": False}

    # Muestra precios generales o de una especialidad específica
    def _manejar_precios(self, mensaje, entidades, numero):
        servicios = self.datos.get("servicios", "")
        precios = self.datos.get("precios", "")

        if entidades.get("especialidad"):
            servicio_info = self._obtener_info_servicio(entidades["especialidad"])
            precio = self._obtener_precio(entidades["especialidad"])
            respuesta = ""
            if servicio_info:
                respuesta += f"📋 *{entidades['especialidad']}*\n\n{servicio_info}\n"
            if precio:
                respuesta += f"\n💰 *Precio:* {precio.split(':', 1)[1].strip() if ':' in precio else precio}"
            if not respuesta:
                respuesta = "No encontré información específica para esa consulta."
        else:
            if precios:
                response_lines = [l for l in precios.split("\n") if l.strip() and not l.startswith("===")]
                respuesta = "💰 *Lista de Precios:*\n\n" + "\n".join(response_lines)
            else:
                respuesta = "No tengo información de precios disponible."

        respuesta += self.OFERTA_AGENDAR
        return {"respuesta": respuesta, "intencion": "precios", "transferir": False}

    # Muestra la dirección/ubicación del negocio
    def _manejar_ubicacion(self, mensaje, entidades, numero):
        direccion = self.datos.get("direccion", "")
        if direccion:
            response_lines = [l for l in direccion.split("\n") if l.strip() and not l.startswith("===")]
            respuesta = "📍 *Ubicación:*\n\n" + "\n".join(response_lines)
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
        return {"respuesta": respuesta, "intencion": "ubicacion", "transferir": False}

    # Gestiona el flujo de agendar una cita: pide datos faltantes o registra
    def _manejar_agendar_cita(self, mensaje, entidades, numero):
        # Si faltan nombre o especialidad, pide completar el formulario
        if not entidades.get("nombre") or not entidades.get("especialidad"):
            fecha_detectada = entidades.get("fecha", "")
            if fecha_detectada:
                horarios = self._formatear_horarios_disponibles(fecha_detectada)
                respuesta = (
                    "Claro, con gusto te ayudo a agendar una cita. Por favor, proporciona los siguientes datos:\n\n"
                    "1. 📝 *Nombre completo*\n"
                    "2. 📱 *Teléfono de contacto*\n"
                    "3. 🏥 *Especialidad deseada*\n"
                    f"4. 📅 *Fecha preferida:* {fecha_detectada}\n"
                    "5. 🕐 *Horario preferido*\n\n"
                    f"*Horarios disponibles para el {fecha_detectada}:*\n{horarios}"
                )
            else:
                horarios = self._formatear_horarios_disponibles()
                respuesta = (
                    "Claro, con gusto te ayudo a agendar una cita. Por favor, proporciona los siguientes datos:\n\n"
                    "1. 📝 *Nombre completo*\n"
                    "2. 📱 *Teléfono de contacto*\n"
                    "3. 🏥 *Especialidad deseada*\n"
                    "4. 📅 *Fecha preferida (dd/mm/aaaa)*\n"
                    "5. 🕐 *Horario preferido*\n\n"
                    f"*Horarios disponibles:*\n{horarios}"
                )
            return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False, "esperando_datos": True}

        # Valida formato de los datos proporcionados
        errores = self._validar_datos_cita(entidades)
        if errores:
            respuesta = (
                "Los datos tienen los siguientes errores:\n\n"
                + "\n".join(f"❌ {e}" for e in errores)
                + "\n\nPor favor, corrije los datos e intenta de nuevo."
            )
            return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False}

        # Registra la cita en BD con estado pendiente de confirmación
        from database.consultas import registrar_cita
        resultado = registrar_cita(
            nombre=entidades["nombre"],
            telefono=entidades.get("telefono", numero or ""),
            fecha=entidades.get("fecha", ""),
            hora=entidades.get("hora", ""),
            especialidad=entidades["especialidad"],
            estado="pendiente_confirmacion",
        )

        # Arma respuesta con folio y datos para notificar al usuario
        datos_cita = {
            "folio": resultado["folio"],
            "nombre": entidades["nombre"],
            "telefono": entidades.get("telefono", numero or ""),
            "especialidad": entidades["especialidad"],
            "fecha": entidades.get("fecha", "Pendiente"),
            "hora": entidades.get("hora", "Pendiente"),
        }
        template = self.mensajes.get("espera_confirmacion", "Cita pendiente de confirmación.")
        respuesta = self._reemplazar_variables(template, datos_cita)
        return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False, "datos": datos_cita, "pendiente_confirmacion": True}

    # Consulta citas registradas por número de teléfono
    def _manejar_consultar_cita(self, mensaje, entidades, numero):
        from database.consultas import buscar_cita_por_telefono

        telefono_buscar = entidades.get("telefono") or numero
        if not telefono_buscar:
            respuesta = "Para consultar tu cita, por favor proporciona tu número de teléfono."
            return {"respuesta": respuesta, "intencion": "cita_consultar", "transferir": False}

        resultados = buscar_cita_por_telefono(telefono_buscar)
        if not resultados:
            respuesta = "No encontré citas registradas con ese número de teléfono."
            return {"respuesta": respuesta, "intencion": "cita_consultar", "transferir": False}

        # Lista todas las citas del usuario
        respuesta = "📋 *Tus citas registradas:*\n\n"
        for cita in resultados:
            respuesta += (
                f"▪️ *Folio:* {cita['folio']}\n"
                f"▪️ *Especialidad:* {cita['especialidad']}\n"
                f"▪️ *Fecha:* {cita['fecha']}\n"
                f"▪️ *Hora:* {cita['hora']}\n"
                f"▪️ *Estado:* {cita['estado']}\n"
                f"───\n"

            )
        return {"respuesta": respuesta, "intencion": "cita_consultar", "transferir": False}

    # Solicita cancelación de cita (transfiere al administrador)
    def _manejar_cancelar_cita(self, mensaje, entidades, numero):
        respuesta = (
            "Para cancelar una cita, por favor contacta directamente con nuestro equipo "
            "para que podamos atenderte personalmente.\n\n"
            "Te transferiré con un administrador para gestionar la cancelación."
        )
        return {"respuesta": respuesta, "intencion": "cita_cancelar", "transferir": True}

    # Gestiona el flujo de crear una reserva de producto
    def _manejar_crear_reserva(self, mensaje, entidades, numero):
        # Si falta el nombre, pide los datos del formulario
        if not entidades.get("nombre"):
            respuesta = (
                "Claro, te ayudo a realizar una reserva. Por favor proporciona:\n\n"
                "1. 📝 *Nombre completo*\n"
                "2. 📱 *Teléfono de contacto*\n"
                "3. 🛍️ *Producto que deseas*\n"
                "4. 🔢 *Cantidad*\n\n"
                f"*Productos disponibles:*\n{self.datos.get('productos', 'Consultar productos disponibles.')}"
            )
            return {"respuesta": respuesta, "intencion": "reserva_crear", "transferir": False, "esperando_datos": True}

        # Registra la reserva en la base de datos
        from database.consultas import registrar_reserva
        resultado = registrar_reserva(
            nombre=entidades["nombre"],
            telefono=entidades.get("telefono", numero or ""),
            producto=entidades.get("producto", mensaje),
            cantidad=entidades.get("cantidad", 1),
        )

        # Responde con los datos de la reserva creada
        variables = {
            "nombre": entidades["nombre"],
            "telefono": entidades.get("telefono", numero or ""),
            "producto": entidades.get("producto", "Producto solicitado"),
            "cantidad": str(entidades.get("cantidad", 1)),
            "folio": resultado["folio"],
        }
        template = self.mensajes.get("reserva_exitosa", "Reserva creada.")
        respuesta = self._reemplazar_variables(template, variables)
        return {"respuesta": respuesta, "intencion": "reserva_crear", "transferir": False, "datos": resultado}

    # Consulta reservas registradas por número de teléfono
    def _manejar_consultar_reserva(self, mensaje, entidades, numero):
        from database.consultas import buscar_reserva_por_telefono

        telefono_buscar = entidades.get("telefono") or numero
        if not telefono_buscar:
            respuesta = "Para consultar tu reserva, proporciona tu número de teléfono."
            return {"respuesta": respuesta, "intencion": "reserva_consultar", "transferir": False}

        resultados = buscar_reserva_por_telefono(telefono_buscar)
        if not resultados:
            respuesta = "No encontré reservas registradas con ese número."
            return {"respuesta": respuesta, "intencion": "reserva_consultar", "transferir": False}

        # Lista todas las reservas del usuario
        respuesta = "📦 *Tus reservas:*\n\n"
        for r in resultados:
            respuesta += (
                f"▪️ *Folio:* {r['folio']}\n"
                f"▪️ *Producto:* {r['producto_reservado']}\n"
                f"▪️ *Cantidad:* {r['cantidad']}\n"
                f"▪️ *Estado:* {r['estado']}\n───\n"
            )
        return {"respuesta": respuesta, "intencion": "reserva_consultar", "transferir": False}

    # Muestra los datos de contacto: teléfonos y correo electrónico
    def _manejar_contacto(self, mensaje, entidades, numero):
        telefonos = self.datos.get("telefonos", "")
        correo = self.datos.get("correo", "")
        respuesta = "📞 *Contacto:*\n\n"
        if telefonos:
            response_lines = [l for l in telefonos.split("\n") if l.strip() and not l.startswith("===")]
            respuesta += "📱 *Teléfonos:*\n" + "\n".join(response_lines) + "\n\n"
        if correo:
            response_lines = [l for l in correo.split("\n") if l.strip() and not l.startswith("===")]
            respuesta += "📧 *Correo:*\n" + "\n".join(response_lines)
        return {"respuesta": respuesta, "intencion": "contacto", "transferir": False}

    # Muestra información detallada de un servicio/especialidad específico
    def _manejar_servicio_especifico(self, mensaje, entidades, numero):
        esp = entidades.get("especialidad", "")
        servicio_info = self._obtener_info_servicio(esp) if esp else None
        precio = self._obtener_precio(esp) if esp else None

        respuesta = ""
        if servicio_info:
            respuesta += f"📋 *{esp}*\n\n{servicio_info}\n"
        if precio:
            respuesta += f"\n💰 *Precio:* {precio.split(':', 1)[1].strip() if ':' in precio else precio}"
        if not respuesta:
            # Si no hay coincidencia, lista todas las especialidades disponibles
            servicios_raw = self.datos.get("servicios", "")
            especialidades = []
            for linea in servicios_raw.split("\n"):
                if linea.startswith("Servicio:"):
                    especialidades.append(linea.replace("Servicio:", "").strip())
            if especialidades:
                respuesta = (
                    "🏥 *Especialidades disponibles:*\n\n"
                    + "\n".join(f"▪️ {e}" for e in especialidades)
                    + "\n\n¿Sobre cuál te gustaría más información?"
                )
            else:
                respuesta = self._reemplazar_variables(
                    self.mensajes.get("sin_respuesta", "No tengo información específica.")
                )
        else:
            respuesta += self.OFERTA_AGENDAR
        return {"respuesta": respuesta, "intencion": "servicio_especifico", "transferir": False}

    # Información sobre métodos de pago (transfiere al admin)
    def _manejar_pago(self, mensaje, entidades, numero):
        template = self.mensajes.get("pago", "El pago es presencial.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "pago", "transferir": True}

    # Maneja mensajes de emergencia: redirige al 911
    def _manejar_emergencia(self, mensaje, entidades, numero):
        respuesta = (
            "🚨 *Si se trata de una emergencia, por favor llama al 911 o acude a la unidad de emergencias más cercana.*\n\n"
            "Este chat no puede proporcionar atención médica de emergencia. "
            "Si requieres información general, puedo ayudarte a agendar una cita para una consulta presencial."
        )
        return {"respuesta": respuesta, "intencion": "emergencia", "transferir": False}

    # Transfiere la conversación a un administrador humano
    def _manejar_transferencia(self, mensaje, entidades, numero):
        # Si está fuera de horario, informa y deja aviso
        if getattr(self, "_es_fuera_horario", False):
            fuera_template = self.mensajes.get("fuera_horario", "Estamos fuera de horario.")
            respuesta = self._reemplazar_variables(fuera_template) + "\n\nHemos enviado un aviso a nuestro equipo. Te contactaremos en nuestro próximo horario de atención."
            return {"respuesta": respuesta, "intencion": "transferir", "transferir": True}
        template = self.mensajes.get("transferencia", "Transfiriendo al administrador.")
        respuesta = self._reemplazar_variables(template, {"telefono": numero or ""})
        return {"respuesta": respuesta, "intencion": "transferir", "transferir": True}

    # Responde a un agradecimiento del usuario
    def _manejar_gracias(self, mensaje, entidades, numero):
        respuesta = "¡De nada! Estoy aquí para ayudarte. Si tienes alguna otra pregunta, no dudes en consultarme. 😊"
        return {"respuesta": respuesta, "intencion": "gracias", "transferir": False}

    # Responde a una despedida del usuario
    def _manejar_despedida(self, mensaje, entidades, numero):
        respuesta = "¡Ha sido un placer atenderte! Que tengas un excelente día. 😊\n\nSi necesitas algo más, aquí estaremos."
        return {"respuesta": respuesta, "intencion": "despedida", "transferir": False}

    # Muestra las preguntas frecuentes (FAQ) del negocio
    def _manejar_faq(self, mensaje, entidades, numero):
        faq = self.datos.get("preguntas_frecuentes", "")
        if faq:
            response_lines = [l for l in faq.split("\n") if l.strip() and not l.startswith("===")]
            respuesta = "❓ *Preguntas Frecuentes:*\n\n" + "\n".join(response_lines[:20])
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
        return {"respuesta": respuesta, "intencion": "faq", "transferir": False}

    # Verifica si un número de teléfono pertenece al administrador
    def _es_admin(self, numero):
        if not numero:
            return False
        admin_tel = self.config.get("admin_telefono", "")
        if not admin_tel:
            admin_tel = os.getenv("ADMIN_TELEFONO", "")
        numero_limpio = numero.replace("+", "").replace(" ", "").replace("-", "")
        admin_limpio = admin_tel.replace("+", "").replace(" ", "").replace("-", "")
        return numero_limpio == admin_limpio

    # Genera reportes de citas y reservas (solo para administrador)
    def _manejar_reportes(self, mensaje, entidades, numero):
        if not self._es_admin(numero):
            respuesta = (
                "Los reportes solo están disponibles para el administrador. "
                "Si necesitas ayuda, puedo transferirte con él."
            )
            return {"respuesta": respuesta, "intencion": "reportes", "transferir": True}

        from database.consultas import listar_citas, listar_reservas

        citas = listar_citas()
        reservas = listar_reservas()

        respuesta = "📋 *REPORTES DEL SISTEMA*\n\n"

        # Lista las últimas 10 citas registradas
        respuesta += f"📅 *CITAS ({len(citas)}):*\n"
        if citas:
            for c in citas[:10]:
                respuesta += (
                    f"  {c['folio']} | {c['nombre']} | "
                    f"{c.get('fecha','?')} {c.get('hora','?')} | "
                    f"{c.get('especialidad','?')} | {c['estado']}\n"
                )
        else:
            respuesta += "  No hay citas registradas.\n"

        # Lista las últimas 10 reservas registradas
        respuesta += f"\n📦 *RESERVAS ({len(reservas)}):*\n"
        if reservas:
            for r in reservas[:10]:
                respuesta += (
                    f"  {r['folio']} | {r['nombre']} | "
                    f"{r.get('producto_reservado','?')} x{r.get('cantidad',1)} | "
                    f"{r['estado']}\n"
                )
        else:
            respuesta += "  No hay reservas registradas.\n"

        return {"respuesta": respuesta, "intencion": "reportes", "transferir": False}

    # Registra en un archivo JSONL los mensajes que el chatbot no entendió
    def _registrar_no_entendido(self, mensaje, numero=None, intencion=None):
        from datetime import datetime

        ruta = self._ruta("datos", "no_entendidos.jsonl")
        entrada = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": mensaje,
            "numero": numero or "",
            "intencion": intencion or "",
        }
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    # Manejador de último recurso: busca en archivos o marca como no entendido
    def _manejar_consulta_general(self, mensaje, entidades, numero):
        resultado = self._buscar_en_archivos(mensaje)

        # Si encuentra algo relevante en los archivos, lo devuelve
        if resultado:
            respuesta = resultado
            return {"respuesta": respuesta, "intencion": "consulta_general", "transferir": False}

        # Si no encuentra nada, registra y pide transferencia a humano
        self._registrar_no_entendido(mensaje, numero, "consulta_general")
        template = self.mensajes.get("sin_respuesta", "No encontré información.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "sin_respuesta", "transferir": True}
