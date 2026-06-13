import os
import logging
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "")
_pg_pool = None

logger = logging.getLogger(__name__)


def conectar():
    if DATABASE_URL:
        return _conectar_pg()
    return _conectar_sqlite()


def _conectar_sqlite():
    import sqlite3
    _DB_DIR = os.getenv("DB_PATH") or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(os.path.join(_DB_DIR, "agenda.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _conectar_pg():
    global _pg_pool
    if _pg_pool is None:
        import psycopg2
        from psycopg2 import pool
        try:
            _pg_pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=DATABASE_URL,
                sslmode="require",
            )
            logger.info("PostgreSQL connection pool created (min=2, max=10)")
        except Exception:
            logger.warning("Falling back to single connection for PostgreSQL")
            import psycopg2.extras
            conn = psycopg2.connect(
                DATABASE_URL,
                sslmode="require",
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            conn.autocommit = False
            return conn

    conn = _pg_pool.getconn()
    conn.autocommit = False
    return conn


def liberar_conexion(conn):
    global _pg_pool
    if DATABASE_URL and _pg_pool:
        _pg_pool.putconn(conn)
    else:
        conn.close()


def _fetchall(conn, cursor):
    if DATABASE_URL:
        return [dict(row) for row in cursor]
    return [dict(row) for row in cursor.fetchall()]


def _last_id(conn, cursor):
    if DATABASE_URL:
        return cursor.fetchone()["id"]
    return cursor.lastrowid


def es_postgresql():
    return bool(DATABASE_URL)


def inicializar():
    conn = conectar()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id SERIAL PRIMARY KEY,
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
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_telefono ON agenda(telefono)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_folio ON agenda(folio)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_estado ON agenda(estado)
        """)
    else:
        cursor.execute("""
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
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_telefono ON agenda(telefono)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_folio ON agenda(folio)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agenda_estado ON agenda(estado)
        """)

    conn.commit()
    liberar_conexion(conn)


def generar_folio():
    import random
    import string
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"F-{timestamp}-{random_part}"
