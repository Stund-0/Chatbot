#!/usr/bin/env python3
"""
Prueba exhaustiva de todas las intenciones del chatbot.
Detecta palabras clave faltantes y respuestas incorrectas.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.agenda_db import inicializar as inicializar_db
from ia.interprete import detectar_intencion, INTENCIONES
from chatbot import Chatbot

inicializar_db()
bot = Chatbot(modo_simulacion=True)

PRUEBAS = {
    "saludo": [
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "que tal",
        "hey",
        "saludos",
        "buen dia",
        "hola buenos dias",
        "hola que tal",
        "que hay",
        "como estas",
        "buenas",
    ],
    "informacion": [
        "que hacen",
        "que ofrecen",
        "informacion",
        "servicios",
        "productos",
        "que servicios tienen",
        "a que se dedican",
        "que ofrecen",
        "cuales son sus servicios",
        "me pueden decir que hacen",
    ],
    "horarios": [
        "horario",
        "horarios",
        "atienden",
        "a que hora abren",
        "a que hora cierran",
        "cuando atienden",
        "dias de atencion",
        "que dias trabajan",
        "horario de atencion",
        "en que horario atienden",
        "estan abiertos",
        "cual es el horario",
    ],
    "precios": [
        "precio",
        "precios",
        "cuanto cuesta",
        "costo",
        "costos",
        "tarifa",
        "cuesta",
        "cuanto vale",
        "que precio tiene",
        "cuanto cobran",
        "mejores precios",
        "cual es el costo",
        "precio de consulta",
        "cuanto sale",
    ],
    "ubicacion": [
        "direccion",
        "ubicacion",
        "donde estan",
        "donde queda",
        "ubicados",
        "como llegar",
        "en donde estan",
        "mapa",
        "cual es su direccion",
        "donde se ubican",
    ],
    "cita_agendar": [
        "agendar",
        "cita",
        "consulta",
        "agenda",
        "reservar cita",
        "quiero una cita",
        "necesito una cita",
        "programar cita",
        "quiero agendar",
        "puedo agendar una cita",
        "me gustaria una cita",
        "agendar consulta",
        "quiero apartar cita",
        "sacar cita",
        "pedir cita",
        "agendar una consulta",
    ],
    "cita_consultar": [
        "mi cita",
        "consultar cita",
        "ver cita",
        "estado de mi cita",
        "tengo una cita",
        "quiero ver mi cita",
        "consulta mi cita",
        "como va mi cita",
        "revisar mi cita",
    ],
    "cita_cancelar": [
        "cancelar",
        "cancelacion",
        "cancelar cita",
        "quiero cancelar",
        "cancelar mi cita",
        "necesito cancelar",
        "quiero cancelar mi cita",
        "cancelar consulta",
        "anular cita",
    ],
    "reserva_crear": [
        "reservar",
        "apartar",
        "quiero comprar",
        "ordenar",
        "pedido",
        "comprar",
        "producto",
        "quiero hacer un pedido",
        "quiero un producto",
        "hacer una reserva",
        "apartar un producto",
        "comprar algo",
    ],
    "reserva_consultar": [
        "mi reserva",
        "mi pedido",
        "consultar reserva",
        "estado de mi pedido",
        "ver reserva",
        "consultar mi pedido",
        "revisar mi reserva",
        "como va mi pedido",
    ],
    "contacto": [
        "telefono",
        "correo",
        "contacto",
        "comunicarme",
        "llamar",
        "numero de telefono",
        "como contacto",
        "cual es su numero",
        "donde llamo",
        "cual es el telefono",
        "email",
        "whatsapp",
    ],
    "servicio_especifico": [
        "medicina general",
        "pediatria",
        "ginecologia",
        "cardiologia",
        "dermatologia",
        "psicologia",
        "especialidad",
        "quiero saber de pediatria",
        "informacion sobre cardiologia",
        "me interesa ginecologia",
    ],
    "pago": [
        "pagar",
        "pago",
        "metodos de pago",
        "formas de pago",
        "transferencia",
        "tarjeta",
        "como puedo pagar",
        "formas de pago aceptadas",
        "pago con tarjeta",
        "pago en efectivo",
        "aceptan tarjeta",
        "donde pago",
    ],
    "emergencia": [
        "emergencia",
        "urgencia",
        "grave",
        "accidente",
        "duele",
        "tengo una emergencia",
        "es una urgencia",
        "me duele mucho",
        "necesito ayuda urgente",
    ],
    "transferir": [
        "persona",
        "humano",
        "asesor",
        "operador",
        "hablar con alguien",
        "transferir",
        "agente",
        "quiero hablar con un humano",
        "hablar con un asesor",
        "pasa a un operador",
        "quiero una persona",
        "atencion personal",
    ],
    "gracias": [
        "gracias",
        "muchas gracias",
        "agradezco",
        "te agradezco",
        "muy amable",
    ],
    "despedida": [
        "adios",
        "nos vemos",
        "hasta luego",
        "bye",
        "chao",
        "hasta pronto",
        "nos vemos luego",
    ],
    "faq": [
        "preguntas frecuentes",
        "faq",
        "dudas frecuentes",
        "preguntas comunes",
    ],
}

errores = []
aciertos = []

print("=" * 70)
print("PRUEBA EXHAUSTIVA DE INTENCIONES")
print("=" * 70)

for intencion, frases in PRUEBAS.items():
    print(f"\n--- [{intencion.upper()}] ---")
    for frase in frases:
        resultado = detectar_intencion(frase)
        estado = "[OK]" if resultado == intencion else "[ERR]"
        if resultado == intencion:
            aciertos.append((intencion, frase))
        else:
            errores.append((intencion, frase, resultado))
        print(f"  {estado} '{frase}' -> {resultado}")

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)
print(f"ACIERTOS: {len(aciertos)}")
print(f"ERRORES: {len(errores)}")

if errores:
    print("\n--- FRASES NO DETECTADAS CORRECTAMENTE ---")
    for intencion, frase, resultado in errores:
        print(f"  [ERR] [{intencion}] '{frase}' -> detecto '{resultado}'")

print("\n--- PALABRAS FALTANTES POR INTENCION ---")
palabras_faltantes = {}
for intencion, frase, resultado in errores:
    palabras = frase.lower().split()
    for p in palabras:
        todas_palabras = [y for x in INTENCIONES.values() for y in x]
        todas_planas = []
        for item in todas_palabras:
            todas_planas.extend(item.split())
        if p not in todas_planas and len(p) > 2:
            if intencion not in palabras_faltantes:
                palabras_faltantes[intencion] = set()
            palabras_faltantes[intencion].add(p)

for intencion, palabras in palabras_faltantes.items():
    print(f"  [{intencion}] faltan: {', '.join(sorted(palabras))}")
