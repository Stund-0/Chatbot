import json
import os
import re
from datetime import datetime, timedelta

import pytz

ZONA_HORARIA = pytz.timezone("America/Mexico_City")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _normalizar(texto):
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
    }
    for acento, sin_acento in reemplazos.items():
        texto = texto.replace(acento, sin_acento)
    return texto


class Chatbot:
    def __init__(self, modo_simulacion=True):
        self.modo_simulacion = modo_simulacion
        self.config = self._cargar_config()
        self.datos = {}
        self.mensajes = {}
        self.contextos = {}
        self._cargar_archivos()

    INTENCIONES_RESET = {"saludo", "emergencia", "transferir", "despedida", "cita_cancelar", "faq", "reportes", "gracias"}

    def _obtener_contexto(self, numero):
        if not numero:
            return None
        return self.contextos.get(numero)

    def _guardar_contexto(self, numero, contexto):
        if not numero:
            return
        if contexto:
            self.contextos[numero] = contexto
        else:
            self.contextos.pop(numero, None)

    def _ruta(self, *parts):
        return os.path.join(BASE_DIR, *parts)

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

    def _cargar_archivos(self):
        data_dir = self._ruta("datos")
        mensajes_dir = self._ruta("mensajes")

        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.isdir(mensajes_dir):
            os.makedirs(mensajes_dir, exist_ok=True)

        for archivo in os.listdir(data_dir):
            ruta = os.path.join(data_dir, archivo)
            if os.path.isfile(ruta) and archivo.endswith(".txt"):
                clave = archivo.replace(".txt", "")
                with open(ruta, "r", encoding="utf-8") as f:
                    self.datos[clave] = f.read()

        for archivo in os.listdir(mensajes_dir):
            ruta = os.path.join(mensajes_dir, archivo)
            if os.path.isfile(ruta) and archivo.endswith(".txt"):
                clave = archivo.replace(".txt", "")
                with open(ruta, "r", encoding="utf-8") as f:
                    self.mensajes[clave] = f.read()

    def _reemplazar_variables(self, texto, variables=None):
        if variables is None:
            variables = {}

        nombre_empresa = self.config.get("nombre", "Mi Negocio")
        eslogan = self.config.get("eslogan", "")
        horarios = self.datos.get("horarios", "")
        telefonos = self.datos.get("telefonos", "")
        telefono_principal = ""

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

    def _buscar_en_archivos(self, consulta):
        consulta_norm = _normalizar(consulta.lower())
        palabras_clave = consulta_norm.split()

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

        for archivo in orden_busqueda:
            contenido = self.datos.get(archivo, "")
            if not contenido:
                continue

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

        resultados.sort(key=lambda x: x["relevancia"], reverse=True)

        if resultados:
            return resultados[0]["contenido"]

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

    def _obtener_precio(self, item):
        precios = self.datos.get("precios", "")
        if not precios:
            return None

        item_norm = _normalizar(item.lower().strip())
        lineas = precios.split("\n")
        for linea in lineas:
            if ":" in linea and item_norm in _normalizar(linea.lower()):
                return linea.strip()

        for linea in lineas:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                palabras_clave = item_norm.split()
                if any(p in _normalizar(clave.lower()) for p in palabras_clave if len(p) > 3):
                    return linea.strip()

        return None

    def _obtener_producto(self, producto_buscado):
        productos = self.datos.get("productos", "")
        if not productos:
            return None

        producto_norm = _normalizar(producto_buscado.lower().strip())
        secciones = productos.split("\n\n")

        for seccion in secciones:
            if producto_norm in _normalizar(seccion.lower()):
                return seccion.strip()

        for seccion in secciones:
            palabras = producto_norm.split()
            if any(p in _normalizar(seccion.lower()) for p in palabras if len(p) > 3):
                return seccion.strip()

        return None

    def _esta_en_horario_laboral(self):
        if self.modo_simulacion:
            return True
        ahora = datetime.now(ZONA_HORARIA)
        dia_semana = ahora.weekday()
        hora_actual = ahora.hour + ahora.minute / 60

        if dia_semana < 5:
            return 8 <= hora_actual < 18
        elif dia_semana == 5:
            return 9 <= hora_actual < 14
        else:
            return False

    def _formatear_horarios_disponibles(self, fecha=None):
        horarios_raw = self.datos.get("horarios_disponibles", "")
        if not horarios_raw:
            return self.datos.get("horarios", "No disponible")

        secciones = horarios_raw.split("\n\n")
        etiqueta_dia = None
        if fecha:
            dia_semana = datetime.strptime(fecha, "%d/%m/%Y").weekday()
            if dia_semana < 5:
                etiqueta_dia = "Lunes a Viernes"
            elif dia_semana == 5:
                etiqueta_dia = "Sábados"
            else:
                return "No hay atención los domingos."

        if etiqueta_dia:
            for seccion in secciones:
                if etiqueta_dia in seccion:
                    lineas = [l.strip() for l in seccion.split("\n") if l.strip() and not l.startswith("===") and not l.startswith("Lunes") and not l.startswith("Sáb")]
                    break
            else:
                return "No disponible"
        else:
            vistas = set()
            lineas = []
            for seccion in secciones:
                for l in seccion.split("\n"):
                    l = l.strip()
                    if l and not l.startswith("===") and not l.startswith("Lunes") and not l.startswith("Sáb"):
                        if l not in vistas:
                            lineas.append(l)
                            vistas.add(l)

        if fecha:
            from database.consultas import buscar_citas_por_fecha
            ocupadas = {c["hora"].strip() for c in buscar_citas_por_fecha(fecha)}
            if ocupadas:
                lineas = [l for l in lineas if l not in ocupadas]

        if not lineas:
            return "No hay horarios disponibles para esta fecha."

        return "\n".join(lineas)

    def _obtener_numero_admin(self):
        admin_tel = self.config.get("admin_telefono", "")
        if not admin_tel:
            admin_tel = os.getenv("ADMIN_TELEFONO", "")
        return admin_tel.replace("+", "").replace(" ", "").replace("-", "")

    def _manejar_comando_admin(self, mensaje_usuario, numero_usuario):
        from database.consultas import confirmar_cita, rechazar_cita, buscar_cita_por_folio
        from whatsapp.notificaciones import notificar_admin

        if not numero_usuario:
            return None
        numero_limpio = numero_usuario.replace("+", "").replace(" ", "").replace("-", "")
        admin_limpio = self._obtener_numero_admin()
        if numero_limpio != admin_limpio:
            return None

        msg = mensaje_usuario.strip()
        cmd_parts = msg.split(None, 1)
        if len(cmd_parts) != 2:
            return None

        comando, argumento = cmd_parts
        comando = comando.upper()
        argumento = argumento.strip()

        if comando in ("CONFIRMAR", "RECHAZAR"):
            cita = buscar_cita_por_folio(argumento)
            if not cita:
                return {
                    "respuesta": f"No encontré ninguna cita con folio {argumento}.",
                    "intencion": "admin_comando",
                    "transferir": False,
                }
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
                    from whatsapp.sender import WhatsAppSender
                    sender = WhatsAppSender(
                        token=self.config.get("whatsapp_token", os.getenv("WHATSAPP_TOKEN", "")),
                        phone_id=self.config.get("whatsapp_phone_id", os.getenv("WHATSAPP_PHONE_ID", "")),
                    )
                    if self.modo_simulacion:
                        print(f"\n[ENVIANDO CONFIRMACION A USUARIO {cita['telefono']}]: {msg_usuario}\n")
                    else:
                        sender.enviar_texto(cita["telefono"], msg_usuario)
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
                    from whatsapp.sender import WhatsAppSender
                    sender = WhatsAppSender(
                        token=self.config.get("whatsapp_token", os.getenv("WHATSAPP_TOKEN", "")),
                        phone_id=self.config.get("whatsapp_phone_id", os.getenv("WHATSAPP_PHONE_ID", "")),
                    )
                    if self.modo_simulacion:
                        print(f"\n[ENVIANDO RECHAZO A USUARIO {cita['telefono']}]: {msg_usuario}\n")
                    else:
                        sender.enviar_texto(cita["telefono"], msg_usuario)
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

    OFERTA_AGENDAR = "\n\n¿Te gustaría agendar una cita? Solo envíame tus datos: nombre, teléfono, especialidad, fecha y horario."

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

    def _datos_completos_para_cita(self, entidades):
        return all(entidades.get(k) for k in ("nombre", "especialidad", "fecha", "hora"))

    def _datos_completos_para_reserva(self, entidades):
        return all(entidades.get(k) for k in ("nombre", "producto"))

    def _detectar_datos_incompletos_cita(self, mensaje, entidades, intencion):
        if intencion in self.INTENCIONES_RESET:
            return False
        if self._datos_completos_para_cita(entidades):
            return False
        mensaje_lower = mensaje.lower()
        indicios = 0
        if entidades.get("telefono"):
            indicios += 1
        if entidades.get("fecha"):
            indicios += 1
        if entidades.get("hora"):
            indicios += 1
        if entidades.get("especialidad"):
            indicios += 1
        if re.search(r'\bnombre\s+', mensaje_lower):
            indicios += 1
        return indicios >= 2

    def procesar_mensaje(self, mensaje_usuario, numero_usuario=None, contexto=None):
        resultado_admin = self._manejar_comando_admin(mensaje_usuario, numero_usuario)
        if resultado_admin:
            return resultado_admin

        from ia.interprete import detectar_intencion, extraer_entidades

        intencion = detectar_intencion(mensaje_usuario)
        entidades = extraer_entidades(mensaje_usuario)

        if self._datos_completos_para_cita(entidades) and intencion not in self.INTENCIONES_RESET:
            intencion = "cita_agendar"
        elif self._datos_completos_para_reserva(entidades) and intencion not in self.INTENCIONES_RESET:
            intencion = "reserva_crear"

        if contexto:
            entidades.update(contexto)

        ctx_previo = self._obtener_contexto(numero_usuario)
        if ctx_previo and ctx_previo.get("esperando_datos") and intencion not in self.INTENCIONES_RESET:
            intencion = ctx_previo["intencion"]
            entidades_previas = ctx_previo.get("entidades", {})
            for k, v in entidades_previas.items():
                if k not in entidades:
                    entidades[k] = v

        self._es_fuera_horario = not self._esta_en_horario_laboral()

        if not ctx_previo and self._detectar_datos_incompletos_cita(mensaje_usuario, entidades, intencion):
            template = self.mensajes.get("error_formato", "No entendí los datos.")
            respuesta = self._reemplazar_variables(template)
            return {"respuesta": respuesta, "intencion": "error_formato", "transferir": False}

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

        manejador = gestor_respuesta.get(intencion, self._manejar_consulta_general)
        respuesta = manejador(mensaje_usuario, entidades, numero_usuario)

        if respuesta.get("esperando_datos"):
            self._guardar_contexto(numero_usuario, {
                "intencion": intencion,
                "entidades": entidades,
                "esperando_datos": True,
            })
        else:
            self._guardar_contexto(numero_usuario, None)

        return respuesta

    def _respuesta_fuera_horario(self):
        template = self.mensajes.get("fuera_horario", "Estamos fuera de horario.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "fuera_horario", "transferir": False}

    def _manejar_saludo(self, mensaje, entidades, numero):
        template = self.mensajes.get("bienvenida", "¡Hola! ¿En qué puedo ayudarte?")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "saludo", "transferir": False}

    def _manejar_informacion_general(self, mensaje, entidades, numero):
        esp = entidades.get("especialidad", "")
        if esp:
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

    def _manejar_fechas_disponibles(self, mensaje, entidades, numero):
        from database.consultas import buscar_ocupadas_por_rango
        from datetime import datetime, timedelta

        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        slots_semana = {"0": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"],
                        "1": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"],
                        "2": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"],
                        "3": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"],
                        "4": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"],
                        "5": ["9:00 AM","10:00 AM","11:00 AM","12:00 PM","1:00 PM"],
                        "6": []}

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

    def _manejar_agendar_cita(self, mensaje, entidades, numero):
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

        errores = self._validar_datos_cita(entidades)
        if errores:
            respuesta = (
                "Los datos tienen los siguientes errores:\n\n"
                + "\n".join(f"❌ {e}" for e in errores)
                + "\n\nPor favor, corrije los datos e intenta de nuevo."
            )
            return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False}

        from database.consultas import registrar_cita
        resultado = registrar_cita(
            nombre=entidades["nombre"],
            telefono=entidades.get("telefono", numero or ""),
            fecha=entidades.get("fecha", ""),
            hora=entidades.get("hora", ""),
            especialidad=entidades["especialidad"],
            estado="pendiente_confirmacion",
        )

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

    def _manejar_cancelar_cita(self, mensaje, entidades, numero):
        respuesta = (
            "Para cancelar una cita, por favor contacta directamente con nuestro equipo "
            "para que podamos atenderte personalmente.\n\n"
            "Te transferiré con un administrador para gestionar la cancelación."
        )
        return {"respuesta": respuesta, "intencion": "cita_cancelar", "transferir": True}

    def _manejar_crear_reserva(self, mensaje, entidades, numero):
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

        from database.consultas import registrar_reserva
        resultado = registrar_reserva(
            nombre=entidades["nombre"],
            telefono=entidades.get("telefono", numero or ""),
            producto=entidades.get("producto", mensaje),
            cantidad=entidades.get("cantidad", 1),
        )

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

        respuesta = "📦 *Tus reservas:*\n\n"
        for r in resultados:
            respuesta += (
                f"▪️ *Folio:* {r['folio']}\n"
                f"▪️ *Producto:* {r['producto_reservado']}\n"
                f"▪️ *Cantidad:* {r['cantidad']}\n"
                f"▪️ *Estado:* {r['estado']}\n───\n"
            )
        return {"respuesta": respuesta, "intencion": "reserva_consultar", "transferir": False}

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

    def _manejar_pago(self, mensaje, entidades, numero):
        template = self.mensajes.get("pago", "El pago es presencial.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "pago", "transferir": True}

    def _manejar_emergencia(self, mensaje, entidades, numero):
        respuesta = (
            "🚨 *Si se trata de una emergencia, por favor llama al 911 o acude a la unidad de emergencias más cercana.*\n\n"
            "Este chat no puede proporcionar atención médica de emergencia. "
            "Si requieres información general, puedo ayudarte a agendar una cita para una consulta presencial."
        )
        return {"respuesta": respuesta, "intencion": "emergencia", "transferir": False}

    def _manejar_transferencia(self, mensaje, entidades, numero):
        if getattr(self, "_es_fuera_horario", False):
            fuera_template = self.mensajes.get("fuera_horario", "Estamos fuera de horario.")
            respuesta = self._reemplazar_variables(fuera_template) + "\n\nHemos enviado un aviso a nuestro equipo. Te contactaremos en nuestro próximo horario de atención."
            return {"respuesta": respuesta, "intencion": "transferir", "transferir": True}
        template = self.mensajes.get("transferencia", "Transfiriendo al administrador.")
        respuesta = self._reemplazar_variables(template, {"telefono": numero or ""})
        return {"respuesta": respuesta, "intencion": "transferir", "transferir": True}

    def _manejar_gracias(self, mensaje, entidades, numero):
        respuesta = "¡De nada! Estoy aquí para ayudarte. Si tienes alguna otra pregunta, no dudes en consultarme. 😊"
        return {"respuesta": respuesta, "intencion": "gracias", "transferir": False}

    def _manejar_despedida(self, mensaje, entidades, numero):
        respuesta = "¡Ha sido un placer atenderte! Que tengas un excelente día. 😊\n\nSi necesitas algo más, aquí estaremos."
        return {"respuesta": respuesta, "intencion": "despedida", "transferir": False}

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

    def _es_admin(self, numero):
        if not numero:
            return False
        admin_tel = self.config.get("admin_telefono", "")
        if not admin_tel:
            admin_tel = os.getenv("ADMIN_TELEFONO", "")
        numero_limpio = numero.replace("+", "").replace(" ", "").replace("-", "")
        admin_limpio = admin_tel.replace("+", "").replace(" ", "").replace("-", "")
        return numero_limpio == admin_limpio

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

    def obtener_citas_confirmadas_manana(self):
        from database.consultas import listar_citas
        manana = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        citas = listar_citas(estado="pendiente")
        return [c for c in citas if c.get("fecha") == manana]

    def _enviar_recordatorios(self):
        from whatsapp.sender import WhatsAppSender
        citas_manana = self.obtener_citas_confirmadas_manana()
        if not citas_manana:
            return {"enviados": 0, "mensaje": "No hay citas para mañana"}
        sender = WhatsAppSender(
            token=self.config.get("whatsapp_token", os.getenv("WHATSAPP_TOKEN", "")),
            phone_id=self.config.get("whatsapp_phone_id", os.getenv("WHATSAPP_PHONE_ID", "")),
        )
        enviados = 0
        for cita in citas_manana:
            msg = (
                f"🔔 *Recordatorio de cita médica*\n\n"
                f"Estimado/a {cita['nombre']}, te recordamos que tienes una cita mañana:\n\n"
                f"▪️ *Especialidad:* {cita.get('especialidad', 'N/A')}\n"
                f"▪️ *Fecha:* {cita['fecha']}\n"
                f"▪️ *Hora:* {cita['hora']}\n"
                f"▪️ *Folio:* {cita['folio']}\n\n"
                "Te esperamos. Si no puedes asistir, contacta a nuestro equipo para reagendar."
            )
            if self.modo_simulacion:
                print(f"\n[RECORDATORIO] Para: {cita['telefono']}")
                print(f"[MENSAJE]: {msg}\n")
                enviados += 1
            else:
                resultado = sender.enviar_texto(cita["telefono"], msg)
                if resultado.get("exito"):
                    enviados += 1
        return {"enviados": enviados, "total": len(citas_manana)}

    def _registrar_no_entendido(self, mensaje, numero=None, intencion=None):
        import json
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

    def _manejar_consulta_general(self, mensaje, entidades, numero):
        resultado = self._buscar_en_archivos(mensaje)

        if resultado:
            respuesta = resultado
            return {"respuesta": respuesta, "intencion": "consulta_general", "transferir": False}

        self._registrar_no_entendido(mensaje, numero, "consulta_general")
        template = self.mensajes.get("sin_respuesta", "No encontré información.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "sin_respuesta", "transferir": True}
