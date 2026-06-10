import json
import os

import requests


class WhatsAppSender:
    def __init__(self, token=None, phone_id=None, api_version="v22.0"):
        self.token = token or os.getenv("WHATSAPP_TOKEN", "")
        self.phone_id = phone_id or os.getenv("WHATSAPP_PHONE_ID", "")
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_id}/messages"

    def enviar_texto(self, numero_destino, texto):
        if not self.token or not self.phone_id:
            return self._simular_envio(numero_destino, texto)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_destino,
            "type": "text",
            "text": {"preview_url": False, "body": texto},
        }

        try:
            response = requests.post(
                self.base_url, headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()
            return {"exito": True, "data": response.json()}
        except requests.RequestException as e:
            return {"exito": False, "error": str(e)}

    def _simular_envio(self, numero_destino, texto):
        print(f"\n[WHATSAPP SIMULADO] Para: {numero_destino}")
        print(f"[MENSAJE]: {texto[:200]}..." if len(texto) > 200 else f"[MENSAJE]: {texto}")
        print("=" * 50)
        return {"exito": True, "simulado": True}
