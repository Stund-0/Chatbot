from whatsapp.sender import WhatsAppSender


class MessageHandler:
    def __init__(self, sender: WhatsAppSender):
        self.sender = sender

    def manejar_mensaje_entrante(self, numero, mensaje, respuesta_chatbot):
        textos = respuesta_chatbot.get("respuestas", [respuesta_chatbot.get("respuesta", "")])
        textos = [str(t) for t in textos if isinstance(t, str) or str(t)]
        transferir = respuesta_chatbot.get("transferir", False)

        for texto in textos:
            self.sender.enviar_texto(numero, texto)

        return {"numero": numero, "respuestas_enviadas": len(textos), "transferir": transferir}
