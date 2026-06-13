import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.agenda_db import inicializar as inicializar_db
inicializar_db()

from ia.interprete import detectar_intencion


class TestInterprete:
    def test_saludo(self):
        assert detectar_intencion("hola") == "saludo"
        assert detectar_intencion("buenos dias") == "saludo"
        assert detectar_intencion("buenas tardes") == "saludo"

    def test_horarios(self):
        assert detectar_intencion("horario") == "horarios"
        assert detectar_intencion("a que hora abren") == "horarios"

    def test_ubicacion(self):
        assert detectar_intencion("direccion") == "ubicacion"
        assert detectar_intencion("donde estan") == "ubicacion"

    def test_cita_agendar(self):
        assert detectar_intencion("quiero una cita") == "cita_agendar"
        assert detectar_intencion("agendar consulta") == "cita_agendar"

    def test_cita_cancelar(self):
        assert detectar_intencion("cancelar cita") == "cita_cancelar"

    def test_precios(self):
        assert detectar_intencion("cuanto cuesta") == "precios"

    def test_contacto(self):
        assert detectar_intencion("telefono") == "contacto"
        assert detectar_intencion("correo") == "contacto"

    def test_emergencia(self):
        assert detectar_intencion("emergencia") == "emergencia"

    def test_transferir(self):
        assert detectar_intencion("hablar con un humano") == "transferir"

    def test_gracias(self):
        assert detectar_intencion("gracias") == "gracias"

    def test_despedida(self):
        assert detectar_intencion("adios") == "despedida"

    def test_faq(self):
        assert detectar_intencion("preguntas frecuentes") == "faq"
