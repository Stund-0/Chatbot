from whatsapp.sender import WhatsAppSender


class MessageHandler:
    def __init__(self, sender: WhatsAppSender):
        self.sender = sender

    def manejar_mensaje_entrante(self, numero, mensaje, respuesta_chatbot):
        texto_respuesta = respuesta_chatbot.get("respuesta", "")
        transferir = respuesta_chatbot.get("transferir", False)

        self.sender.enviar_texto(numero, texto_respuesta)

        return {"numero": numero, "respuesta_enviada": True, "transferir": transferir}
