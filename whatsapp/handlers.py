from whatsapp.sender import WhatsAppSender


class MessageHandler:
    """Manejador que orquesta el envio de respuestas del chatbot a traves del sender."""

    def __init__(self, sender: WhatsAppSender):
        """Guarda la referencia al sender de WhatsApp."""
        self.sender = sender

    def manejar_mensaje_entrante(self, numero, mensaje, respuesta_chatbot):
        """Procesa la respuesta del chatbot y envia los textos al numero del usuario."""
        # Extrae lista de textos soportando formato antiguo (respuesta) y nuevo (respuestas)
        textos = respuesta_chatbot.get("respuestas", [respuesta_chatbot.get("respuesta", "")])
        textos = [str(t) for t in textos if isinstance(t, str) or str(t)]
        transferir = respuesta_chatbot.get("transferir", False)

        # Envia cada texto individualmente al numero destino
        for texto in textos:
            self.sender.enviar_texto(numero, texto)

        return {"numero": numero, "respuestas_enviadas": len(textos), "transferir": transferir}
