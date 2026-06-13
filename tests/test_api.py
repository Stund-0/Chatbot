import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["MODO_SIMULACION"] = "true"
os.environ["DEBUG"] = "false"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test123"
os.environ["REPORTES_API_KEY"] = "test-api-key"
os.environ["LOG_LEVEL"] = "CRITICAL"

from database.agenda_db import inicializar as inicializar_db
inicializar_db()


class TestAPI:
    def setup_method(self):
        from api import app
        self.app = app
        self.client = app.test_client()
        self.app.config["TESTING"] = True

    def test_health_endpoint(self):
        resp = self.client.get("/salud")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_index(self):
        resp = self.client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "nombre" in data
        assert data["estado"] == "activo"

    def test_chat_no_message(self):
        resp = self.client.post("/chat", json={})
        assert resp.status_code == 400

    def test_chat_simulacion(self):
        resp = self.client.post("/chat", json={"mensaje": "hola"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "respuesta" in data
        assert data["modo"] == "simulacion"

    def test_chat_with_context(self):
        resp = self.client.post("/chat", json={
            "mensaje": "hola",
            "numero": "521234567890",
            "contexto": {"nombre": "Victor"},
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "respuesta" in data

    def test_reportes_citas_requires_auth(self):
        resp = self.client.get("/reportes/citas")
        assert resp.status_code == 401

    def test_reportes_citas_with_auth(self):
        resp = self.client.get(
            "/reportes/citas",
            headers={"Authorization": "Bearer test-api-key"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "citas" in data
        assert "total" in data

    def test_reportes_reservas_with_auth(self):
        resp = self.client.get(
            "/reportes/reservas",
            headers={"Authorization": "Bearer test-api-key"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reservas" in data

    def test_webhook_verification(self):
        resp = self.client.get(
            "/webhook?hub.mode=subscribe&hub.verify_token=test123&hub.challenge=12345"
        )
        assert resp.status_code == 200
        assert resp.data.decode() == "12345"

    def test_webhook_verification_fails(self):
        resp = self.client.get(
            "/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=12345"
        )
        assert resp.status_code == 403
