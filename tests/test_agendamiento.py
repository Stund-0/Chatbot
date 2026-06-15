import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["MODO_SIMULACION"] = "true"
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"
os.environ["ADMIN_TELEFONO"] = "521234567890"

from database.agenda_db import inicializar as inicializar_db, conectar, liberar_conexion
inicializar_db()

from database.consultas import (
    registrar_cita,
    buscar_cita_por_folio,
    buscar_cita_por_telefono,
    confirmar_cita,
    rechazar_cita,
    buscar_citas_por_fecha,
    listar_citas,
)

ESTADO_PENDIENTE_CONF = "pendiente_confirmacion"

MAÑANA = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
PASADO = (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y")


def _limpiar_agenda():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agenda")
    conn.commit()
    liberar_conexion(conn)


class TestDBRegistrarCita:
    def setup_method(self):
        _limpiar_agenda()

    def test_registrar_cita_retorna_folio(self):
        resultado = registrar_cita("Juan Perez", "52123456789", MAÑANA, "10:00 AM", "Medicina General")
        assert "folio" in resultado
        assert resultado["folio"].startswith("F-")

    def test_registrar_cita_crea_registro(self):
        resultado = registrar_cita("Maria Lopez", "52119876543", PASADO, "3:00 PM", "Pediatria")
        cita = buscar_cita_por_folio(resultado["folio"])
        assert cita is not None
        assert cita["nombre"] == "Maria Lopez"
        assert cita["telefono"] == "52119876543"
        assert cita["fecha"] == PASADO
        assert cita["hora"] == "3:00 PM"
        assert cita["especialidad"] == "Pediatria"
        assert cita["estado"] == "pendiente"

    def test_registrar_cita_pendiente_confirmacion(self):
        resultado = registrar_cita("Paciente", "52123456789", MAÑANA, "10:00 AM", "General", estado=ESTADO_PENDIENTE_CONF)
        cita = buscar_cita_por_folio(resultado["folio"])
        assert cita["estado"] == ESTADO_PENDIENTE_CONF

    def test_registrar_cita_con_estado_personalizado(self):
        resultado = registrar_cita("Admin", "52100000000", MAÑANA, "9:00 AM", "General", estado="pendiente")
        cita = buscar_cita_por_folio(resultado["folio"])
        assert cita["estado"] == "pendiente"


class TestDBConfirmarRechazar:
    def setup_method(self):
        _limpiar_agenda()
        self.resultado = registrar_cita("Test User", "52123456789", MAÑANA, "11:00 AM", "Dermatologia", estado=ESTADO_PENDIENTE_CONF)
        self.folio = self.resultado["folio"]

    def test_confirmar_cita_cambia_estado(self):
        assert confirmar_cita(self.folio) is True
        cita = buscar_cita_por_folio(self.folio)
        assert cita["estado"] == "pendiente"

    def test_confirmar_cita_ya_confirmada_retorna_false(self):
        confirmar_cita(self.folio)
        assert confirmar_cita(self.folio) is False

    def test_rechazar_cita_cambia_estado(self):
        assert rechazar_cita(self.folio) is True
        cita = buscar_cita_por_folio(self.folio)
        assert cita["estado"] == "rechazada"

    def test_rechazar_cita_ya_rechazada_retorna_false(self):
        rechazar_cita(self.folio)
        assert rechazar_cita(self.folio) is False

    def test_confirmar_folio_inexistente_retorna_false(self):
        assert confirmar_cita("F-000000-XXXXXX") is False

    def test_rechazar_folio_inexistente_retorna_false(self):
        assert rechazar_cita("F-000000-XXXXXX") is False


class TestDBBuscar:
    def setup_method(self):
        _limpiar_agenda()
        self.r1 = registrar_cita("Ana", "52111111111", MAÑANA, "9:00 AM", "Cardiologia")
        self.r2 = registrar_cita("Bob", "52222222222", PASADO, "2:00 PM", "Pediatria")
        self.r3 = registrar_cita("Ana", "52111111111", PASADO, "10:00 AM", "General")

    def test_buscar_por_telefono(self):
        citas = buscar_cita_por_telefono("52111111111")
        assert len(citas) == 2

    def test_buscar_por_telefono_sin_resultados(self):
        citas = buscar_cita_por_telefono("52999999999")
        assert citas == []

    def test_buscar_por_fecha(self):
        horas = buscar_citas_por_fecha(MAÑANA)
        assert len(horas) == 1
        assert horas[0]["hora"] == "9:00 AM"

    def test_listar_todas(self):
        citas = listar_citas()
        assert len(citas) == 3

    def test_listar_por_estado(self):
        r_conf = registrar_cita("Conf", "52111111111", MAÑANA, "9:00 AM", "General", estado=ESTADO_PENDIENTE_CONF)
        pendientes_conf_antes = listar_citas(estado=ESTADO_PENDIENTE_CONF)
        assert len(pendientes_conf_antes) == 1
        confirmar_cita(r_conf["folio"])
        pendientes_conf_despues = listar_citas(estado=ESTADO_PENDIENTE_CONF)
        assert len(pendientes_conf_despues) == 0


class TestChatbotValidacion:
    def setup_method(self):
        _limpiar_agenda()
        from chatbot import Chatbot
        self.bot = Chatbot(modo_simulacion=True)

    def test_datos_completos(self):
        entidades = {
            "nombre": "Juan",
            "especialidad": "Pediatria",
            "fecha": MAÑANA,
            "hora": "10:00 AM",
        }
        assert self.bot._datos_completos_para_cita(entidades) is True

    def test_datos_incompletos(self):
        entidades = {"nombre": "Juan", "especialidad": "Pediatria"}
        assert self.bot._datos_completos_para_cita(entidades) is False

    def test_validar_datos_correctos(self):
        entidades = {"telefono": "52123456789", "fecha": MAÑANA, "hora": "10:00 AM"}
        errores = self.bot._validar_datos_cita(entidades)
        assert errores == []

    def test_validar_telefono_invalido(self):
        entidades = {"telefono": "123", "fecha": MAÑANA, "hora": "10:00 AM"}
        errores = self.bot._validar_datos_cita(entidades)
        assert any("teléfono" in e for e in errores)

    def test_validar_fecha_pasada(self):
        ayer = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        entidades = {"telefono": "52123456789", "fecha": ayer, "hora": "10:00 AM"}
        errores = self.bot._validar_datos_cita(entidades)
        assert any("fecha" in e for e in errores)

    def test_validar_hora_invalida(self):
        entidades = {"telefono": "52123456789", "fecha": MAÑANA, "hora": "abc"}
        errores = self.bot._validar_datos_cita(entidades)
        assert any("hora" in e for e in errores)

    def test_detectar_datos_incompletos_con_2_indicios(self):
        entidades = {"telefono": "52123456789", "fecha": MAÑANA}
        assert self.bot._detectar_datos_incompletos_cita(
            "mi nombre es Juan", entidades, "consulta_general"
        ) is True

    def test_detectar_datos_incompletos_con_1_indicio(self):
        entidades = {"telefono": "52123456789"}
        assert self.bot._detectar_datos_incompletos_cita(
            "hola", entidades, "consulta_general"
        ) is False


class TestChatbotManejarCita:
    def setup_method(self):
        _limpiar_agenda()
        from chatbot import Chatbot
        self.bot = Chatbot(modo_simulacion=True)

    def test_agendar_cita_completa_crea_registro(self):
        entidades = {
            "nombre": "Carlos Ruiz",
            "telefono": "52123456789",
            "especialidad": "Cardiologia",
            "fecha": MAÑANA,
            "hora": "10:00 AM",
        }
        respuesta = self.bot._manejar_agendar_cita("quiero una cita", entidades, "52123456789")
        assert respuesta["intencion"] == "cita_agendar"
        assert respuesta["pendiente_confirmacion"] is True
        assert "datos" in respuesta
        assert respuesta["datos"]["folio"].startswith("F-")

    def test_agendar_cita_incompleta_pide_datos(self):
        entidades = {"especialidad": "Pediatria"}
        respuesta = self.bot._manejar_agendar_cita("quisiera una cita", entidades, "52123456789")
        assert respuesta["intencion"] == "cita_agendar"
        assert respuesta.get("esperando_datos") is True
        assert "nombre" in respuesta["respuesta"].lower() or "Nombre" in respuesta["respuesta"]

    def test_agendar_cita_con_errores_validacion(self):
        entidades = {
            "nombre": "Test",
            "especialidad": "General",
            "fecha": MAÑANA,
            "hora": "99:99 AM",
            "telefono": "12",
        }
        respuesta = self.bot._manejar_agendar_cita("agendar", entidades, "52123456789")
        assert respuesta["intencion"] == "cita_agendar"
        assert "error" in respuesta["respuesta"].lower() or "errores" in respuesta["respuesta"]


class TestChatbotAdminComandos:
    def setup_method(self):
        _limpiar_agenda()
        from chatbot import Chatbot
        self.bot = Chatbot(modo_simulacion=True)
        self.resultado = registrar_cita("Admin Test", "52123456789", MAÑANA, "2:00 PM", "General", estado=ESTADO_PENDIENTE_CONF)
        self.folio = self.resultado["folio"]

    def test_confirmar_desde_admin(self):
        respuesta = self.bot._manejar_comando_admin(
            f"CONFIRMAR {self.folio}", "521234567890"
        )
        assert respuesta is not None
        assert "confirmada" in respuesta["respuesta"].lower()
        cita = buscar_cita_por_folio(self.folio)
        assert cita["estado"] == "pendiente"

    def test_rechazar_desde_admin(self):
        respuesta = self.bot._manejar_comando_admin(
            f"RECHAZAR {self.folio}", "521234567890"
        )
        assert respuesta is not None
        assert "rechazada" in respuesta["respuesta"].lower()
        cita = buscar_cita_por_folio(self.folio)
        assert cita["estado"] == "rechazada"

    def test_comando_admin_desde_no_admin_retorna_none(self):
        respuesta = self.bot._manejar_comando_admin(
            f"CONFIRMAR {self.folio}", "52999999999"
        )
        assert respuesta is None

    def test_comando_admin_sin_argumentos_retorna_none(self):
        respuesta = self.bot._manejar_comando_admin("CONFIRMAR", "521234567890")
        assert respuesta is None

    def test_comando_admin_folio_inexistente(self):
        respuesta = self.bot._manejar_comando_admin(
            "CONFIRMAR F-000000-XXXXXX", "521234567890"
        )
        assert respuesta is not None
        assert "no encontré" in respuesta["respuesta"].lower()


class TestFlujoMultiturno:
    def setup_method(self):
        _limpiar_agenda()
        from chatbot import Chatbot
        self.bot = Chatbot(modo_simulacion=True)
        self.numero = "52111111111"

    def test_mensaje_completo_crea_cita(self):
        mensaje = (
            f"nombre Carlos Ruiz, telefono {self.numero}, "
            f"especialidad Medicina General, fecha {MAÑANA}, hora 10:00 AM"
        )
        respuesta = self.bot.procesar_mensaje(mensaje, self.numero)
        assert respuesta["intencion"] == "cita_agendar", f"Esperaba cita_agendar, obtuve {respuesta['intencion']}"
        assert respuesta.get("pendiente_confirmacion") is True
        assert respuesta["datos"]["folio"].startswith("F-")

    def test_mensaje_completo_guarda_en_bd(self):
        mensaje = (
            f"nombre Ana Garcia, telefono {self.numero}, "
            f"especialidad Medicina General, fecha {MAÑANA}, hora 11:00 AM"
        )
        respuesta = self.bot.procesar_mensaje(mensaje, self.numero)
        folio = respuesta["datos"]["folio"]
        cita = buscar_cita_por_folio(folio)
        assert cita is not None
        assert cita["nombre"] == "Ana Garcia"
        assert cita["estado"] == ESTADO_PENDIENTE_CONF

    def test_flujo_incompleto_luego_completo(self):
        paso1 = self.bot.procesar_mensaje(
            "nombre Carlos Ruiz, especialidad Medicina General", self.numero
        )
        assert paso1["intencion"] in ("cita_agendar", "error_formato")

        paso2 = self.bot.procesar_mensaje(
            f"telefono {self.numero}, fecha {MAÑANA}, hora 3:00 PM", self.numero
        )
        if paso2["intencion"] == "cita_agendar" and paso2.get("pendiente_confirmacion"):
            assert paso2["datos"]["folio"].startswith("F-")
        else:
            assert paso2["intencion"] in ("cita_agendar", "error_formato")

    def test_pregunta_info_resetea_contexto(self):
        self.bot.procesar_mensaje("nombre Ana, especialidad General", self.numero)
        paso2 = self.bot.procesar_mensaje("que horarios tienen", self.numero)
        assert paso2["intencion"] == "horarios"
        ctx = self.bot._obtener_contexto(self.numero)
        assert ctx is None

    def test_deteccion_multi_intent_con_agendar(self):
        mensaje = "que precios y horarios tienen, tambien quiero agendar una cita"
        respuesta = self.bot.procesar_mensaje(mensaje, self.numero)
        assert respuesta["intencion"] == "cita_agendar"
        assert len(respuesta.get("respuestas", [])) >= 2
