import json
import os
import re
from datetime import datetime, timedelta

import pytz

ZONA_HORARIA = pytz.timezone("America/Mexico_City")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Chatbot:
    def __init__(self, modo_simulacion=True):
        self.modo_simulacion = modo_simulacion
        self.config = self._cargar_config()
        self.datos = {}
        self.mensajes = {}
        self._cargar_archivos()

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
        consulta_lower = consulta.lower()
        palabras_clave = consulta_lower.split()

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
                seccion_lower = seccion.lower()
                coincidencias = sum(
                    1 for palabra in palabras_clave if len(palabra) > 3 and palabra in seccion_lower
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
                    linea_lower = linea.lower()
                    for palabra in palabras_clave:
                        if len(palabra) > 3 and palabra in linea_lower:
                            return linea

        return None

    def _obtener_info_servicio(self, servicio_buscado):
        servicios = self.datos.get("servicios", "")
        if not servicios:
            return None

        servicio_lower = servicio_buscado.lower().strip()
        secciones = servicios.split("\n\n")

        for seccion in secciones:
            if servicio_lower in seccion.lower():
                return seccion.strip()

        return None

    def _obtener_precio(self, item):
        precios = self.datos.get("precios", "")
        if not precios:
            return None

        item_lower = item.lower().strip()
        lineas = precios.split("\n")
        for linea in lineas:
            if ":" in linea and item_lower in linea.lower():
                return linea.strip()

        for linea in lineas:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                palabras_clave = item_lower.split()
                if any(p in clave.lower() for p in palabras_clave if len(p) > 3):
                    return linea.strip()

        return None

    def _obtener_producto(self, producto_buscado):
        productos = self.datos.get("productos", "")
        if not productos:
            return None

        producto_lower = producto_buscado.lower().strip()
        secciones = productos.split("\n\n")

        for seccion in secciones:
            if producto_lower in seccion.lower():
                return seccion.strip()

        for seccion in secciones:
            palabras = producto_lower.split()
            if any(p in seccion.lower() for p in palabras if len(p) > 3):
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

    def _formatear_horarios_disponibles(self):
        horarios = self.datos.get("horarios_disponibles", "")
        if not horarios:
            return self.datos.get("horarios", "No disponible")
        lineas = [l.strip() for l in horarios.split("\n") if l.strip() and not l.startswith("===")]
        return "\n".join(lineas) if lineas else "No disponible"

    def procesar_mensaje(self, mensaje_usuario, numero_usuario=None, contexto=None):
        from ia.interprete import detectar_intencion, extraer_entidades

        intencion = detectar_intencion(mensaje_usuario)
        entidades = extraer_entidades(mensaje_usuario)

        if contexto:
            entidades.update(contexto)

        if not self._esta_en_horario_laboral():
            return self._respuesta_fuera_horario()

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
            "reportes": self._manejar_reportes,
            "consulta_general": self._manejar_consulta_general,
        }

        manejador = gestor_respuesta.get(intencion, self._manejar_consulta_general)
        return manejador(mensaje_usuario, entidades, numero_usuario)

    def _respuesta_fuera_horario(self):
        template = self.mensajes.get("fuera_horario", "Estamos fuera de horario.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "fuera_horario", "transferir": False}

    def _manejar_saludo(self, mensaje, entidades, numero):
        template = self.mensajes.get("bienvenida", "¡Hola! ¿En qué puedo ayudarte?")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "saludo", "transferir": False}

    def _manejar_informacion_general(self, mensaje, entidades, numero):
        info = self.datos.get("informacion", "")
        if info:
            lineas = [l for l in info.split("\n") if not l.startswith("===") and l.strip()]
            respuesta = "\n".join(lineas[:6])
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
        return {"respuesta": respuesta, "intencion": "informacion", "transferir": False}

    def _manejar_horarios(self, mensaje, entidades, numero):
        horarios = self.datos.get("horarios", "")
        disponibles = self._formatear_horarios_disponibles()
        if horarios:
            respuesta = f"📅 *Horarios de Atención:*\n\n{horarios}\n\n🕒 *Horarios Disponibles para Citas:*\n\n{disponibles}"
        else:
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo esa información.")
            )
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
            respuesta = (
                "Claro, con gusto te ayudo a agendar una cita. Por favor, proporciona los siguientes datos:\n\n"
                "1. 📝 *Nombre completo*\n"
                "2. 📱 *Teléfono de contacto*\n"
                "3. 🏥 *Especialidad deseada*\n"
                "4. 📅 *Fecha preferida (dd/mm/aaaa)*\n"
                "5. 🕐 *Horario preferido*\n\n"
                f"*Horarios disponibles:*\n{self._formatear_horarios_disponibles()}"
            )
            return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False, "esperando_datos": True}

        from database.consultas import registrar_cita
        resultado = registrar_cita(
            nombre=entidades["nombre"],
            telefono=entidades.get("telefono", numero or ""),
            fecha=entidades.get("fecha", ""),
            hora=entidades.get("hora", ""),
            especialidad=entidades["especialidad"],
        )

        variables = {
            "nombre": entidades["nombre"],
            "telefono": entidades.get("telefono", numero or ""),
            "especialidad": entidades["especialidad"],
            "fecha": entidades.get("fecha", "Pendiente"),
            "hora": entidades.get("hora", "Pendiente"),
            "folio": resultado["folio"],
        }
        template = self.mensajes.get("cita_exitosa", "Cita agendada.")
        respuesta = self._reemplazar_variables(template, variables)
        return {"respuesta": respuesta, "intencion": "cita_agendar", "transferir": False, "datos": resultado}

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
        from database.consultas import cancelar_cita, buscar_cita_por_telefono

        if entidades.get("folio"):
            exito = cancelar_cita(entidades["folio"])
            if exito:
                variables = {"folio_cancelacion": entidades["folio"]}
                template = self.mensajes.get("cancelacion", "Cita cancelada.")
                respuesta = self._reemplazar_variables(template, variables)
                return {"respuesta": respuesta, "intencion": "cita_cancelar", "transferir": False}
            else:
                respuesta = "No se pudo cancelar la cita. Verifica el folio e intenta de nuevo."
                return {"respuesta": respuesta, "intencion": "cita_cancelar", "transferir": False}

        telefono_buscar = entidades.get("telefono") or numero
        if telefono_buscar:
            citas = buscar_cita_por_telefono(telefono_buscar)
            if citas:
                respuesta = "Tienes las siguientes citas. Indica el *folio* de la que deseas cancelar:\n\n"
                for c in citas:
                    if c["estado"] == "pendiente":
                        respuesta += f"▪️ *Folio:* {c['folio']} - {c['especialidad']} ({c['fecha']} {c['hora']})\n"
                if not citas:
                    respuesta = "No tienes citas pendientes para cancelar."
            else:
                respuesta = "No encontré citas registradas. Proporciona tu folio de cita para cancelarla."
        else:
            respuesta = "Para cancelar tu cita, proporciona el *folio* que te fue asignado."

        return {"respuesta": respuesta, "intencion": "cita_cancelar", "transferir": False}

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
            respuesta = self._reemplazar_variables(
                self.mensajes.get("sin_respuesta", "No tengo información específica.")
            )
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

    def _manejar_reportes(self, mensaje, entidades, numero):
        respuesta = (
            "Los reportes están disponibles para el administrador. "
            "Si eres administrador, consulta la documentación del sistema."
        )
        return {"respuesta": respuesta, "intencion": "reportes", "transferir": True}

    def _manejar_consulta_general(self, mensaje, entidades, numero):
        resultado = self._buscar_en_archivos(mensaje)

        if resultado:
            respuesta = resultado
            return {"respuesta": respuesta, "intencion": "consulta_general", "transferir": False}

        template = self.mensajes.get("sin_respuesta", "No encontré información.")
        respuesta = self._reemplazar_variables(template)
        return {"respuesta": respuesta, "intencion": "sin_respuesta", "transferir": True}
