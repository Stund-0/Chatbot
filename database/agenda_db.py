import sqlite3
import os
from datetime import datetime

_DB_DIR = os.getenv("DB_PATH") or os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DB_DIR, "agenda.db")


def conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def inicializar():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            fecha TEXT,
            hora TEXT,
            servicio TEXT,
            especialidad TEXT,
            producto_reservado TEXT,
            cantidad INTEGER DEFAULT 1,
            tipo TEXT NOT NULL DEFAULT 'cita',
            estado TEXT NOT NULL DEFAULT 'pendiente',
            folio TEXT UNIQUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notas TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agenda_telefono ON agenda(telefono)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agenda_folio ON agenda(folio)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agenda_estado ON agenda(estado)
    """)
    conn.commit()
    conn.close()


def generar_folio():
    import random
    import string
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"F-{timestamp}-{random_part}"
