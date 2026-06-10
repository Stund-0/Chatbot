import json
import os
import re

import openai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class InterpreteAvanzado:
    def __init__(self, api_key=None, modelo="gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.modelo = modelo
        self.cliente = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        self.prompt_maestro = self._cargar_prompt("prompts/prompt_maestro.txt")
        self.prompt_negocio = self._cargar_prompt("prompts/prompt_negocio.txt")

    def _cargar_prompt(self, ruta):
        ruta_completa = os.path.join(BASE_DIR, ruta)
        if os.path.exists(ruta_completa):
            with open(ruta_completa, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def interpretar(self, mensaje_usuario, contexto=None):
        if not self.cliente:
            return self._fallback(mensaje_usuario)

        system_prompt = f"{self.prompt_maestro}\n\n{self.prompt_negocio}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": (
                    "Debes clasificar la intención del usuario y extraer entidades. "
                    "Responde ÚNICAMENTE en este formato JSON, sin texto adicional:\n"
                    '{\n'
                    '  "intencion": "<intencion>",\n'
                    '  "entidades": {},\n'
                    '  "consulta_especifica": "<texto>"\n'
                    "}\n\n"
                    "Intenciones posibles: "
                    "saludo, horarios, precios, servicios, ubicacion, "
                    "cita_agendar, cita_consultar, cita_cancelar, "
                    "reserva_crear, reserva_consultar, "
                    "contacto, pago, emergencia, transferir, gracias, despedida, "
                    "faq, informacion, reportes, consulta_general, sin_respuesta"
                ),
            },
        ]

        if contexto:
            messages.append({"role": "user", "content": f"Contexto: {json.dumps(contexto)}"})

        messages.append({"role": "user", "content": mensaje_usuario})

        try:
            response = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=messages,
                temperature=0.1,
                max_tokens=300,
            )
            contenido = response.choices[0].message.content.strip()
            if contenido.startswith("```"):
                contenido = contenido.strip("`").strip()
                if contenido.startswith("json"):
                    contenido = contenido[4:].strip()
            resultado = json.loads(contenido)
            return resultado
        except Exception:
            return self._fallback(mensaje_usuario)

    def _fallback(self, mensaje_usuario):
        from ia.interprete import interpretar_mensaje
        return interpretar_mensaje(mensaje_usuario, modo_simulacion=True)
