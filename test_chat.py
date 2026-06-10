#!/usr/bin/env python3
"""
Consola interactiva de prueba para el chatbot.
Simula una conversación con el asistente.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.agenda_db import inicializar as inicializar_db
from chatbot import Chatbot


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_banner():
    print("=" * 60)
    print("  🤖 CHATBOT WHATSAPP - MODO DE PRUEBA")
    print("  Sistema Universal de Atención al Cliente")
    print("=" * 60)
    print("  Comandos:")
    print("    /salir   - Terminar la conversación")
    print("    /ayuda   - Mostrar comandos disponibles")
    print("    /reportes - Ver reportes de citas y reservas")
    print("=" * 60)
    print()


def mostrar_reportes():
    from database.consultas import listar_citas, listar_reservas
    citas = listar_citas()
    reservas = listar_reservas()

    print("\n" + "=" * 50)
    print("📋 REPORTES DEL SISTEMA")
    print("=" * 50)

    print(f"\n📅 CITAS ({len(citas)}):")
    if citas:
        for c in citas:
            print(f"  {c['folio']} | {c['nombre']} | {c['fecha']} {c['hora']} | {c['especialidad']} | {c['estado']}")
    else:
        print("  No hay citas registradas.")

    print(f"\n📦 RESERVAS ({len(reservas)}):")
    if reservas:
        for r in reservas:
            print(f"  {r['folio']} | {r['nombre']} | {r['producto_reservado']} x{r['cantidad']} | {r['estado']}")
    else:
        print("  No hay reservas registradas.")

    print("=" * 50 + "\n")


def main():
    inicializar_db()
    bot = Chatbot(modo_simulacion=True)

    limpiar_pantalla()
    mostrar_banner()

    bienvenida = bot.procesar_mensaje("hola")
    print(f"🤖: {bienvenida['respuesta']}\n")

    while True:
        try:
            entrada = input("👤: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n¡Hasta luego!")
            break

        if not entrada:
            continue

        if entrada.lower() == "/salir":
            print("\n🤖: ¡Hasta luego! Gracias por usar el chatbot.")
            break

        if entrada.lower() == "/ayuda":
            mostrar_banner()
            continue

        if entrada.lower() == "/reportes":
            mostrar_reportes()
            continue

        respuesta = bot.procesar_mensaje(entrada)

        print(f"\n🤖: {respuesta['respuesta']}")

        if respuesta.get("transferir"):
            print("\n⚠️  [Esta consulta será transferida al administrador]")

        print()


if __name__ == "__main__":
    main()
