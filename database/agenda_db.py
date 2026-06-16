# Módulo de base de datos para la agenda del chatbot
# Maneja conexiones a PostgreSQL (producción) y SQLite (desarrollo/fallback)
import os
import logging
import threading
from datetime import datetime

# Variable de entorno para elegir entre PostgreSQL o SQLite
DATABASE_URL = os.getenv("CUSTOM_DB_URL") or os.getenv("DATABASE_URL", "")
# Pool de conexiones a PostgreSQL (inicializado bajo demanda)
_pg_pool = None
# Candado para evitar condiciones de carrera al crear el pool
_pg_pool_lock = threading.Lock()

logger = logging.getLogger(__name__)


# Construye un DSN completo de PostgreSQL a partir de una URL parcial
def _build_pg_dsn(raw_url: str) -> str:
    if "://" in raw_url:
        return raw_url
    host, port = raw_url.rsplit(":", 1)
    user = os.getenv("PGUSER", "postgres")
    pw = os.getenv("PGPASSWORD", "")
    db = os.getenv("PGDATABASE", "railway")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"


# Punto de entrada: elige PostgreSQL o SQLite según la configuración
def conectar():
    if DATABASE_URL:
        return _conectar_pg()
    return _conectar_sqlite()


# Conexión a SQLite local con WAL y timeout para concurrencia
def _conectar_sqlite():
    import sqlite3
    _DB_DIR = os.getenv("DB_PATH") or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(os.path.join(_DB_DIR, "agenda.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# Conexión a PostgreSQL con pool de hilos y fallback a conexión simple
def _conectar_pg():
    global _pg_pool
    pg_dsn = _build_pg_dsn(DATABASE_URL) if DATABASE_URL else DATABASE_URL
    # Doble verificación con candado para crear el pool una sola vez
    if _pg_pool is None:
        with _pg_pool_lock:
            if _pg_pool is None:
                try:
                    import psycopg2
                    import psycopg2.extras
                    from psycopg2 import pool
                    # Pool de conexiones reutilizables entre hilos
                    _pg_pool = pool.ThreadedConnectionPool(
                        minconn=int(os.getenv("PG_POOL_MIN", "2")),
                        maxconn=int(os.getenv("PG_POOL_MAX", "10")),
                        dsn=pg_dsn,
                        sslmode="require",
                        cursor_factory=psycopg2.extras.RealDictCursor,
                    )
                    logger.info("PostgreSQL connection pool created (min=%s, max=%s)",
                                os.getenv("PG_POOL_MIN", "2"),
                                os.getenv("PG_POOL_MAX", "10"))
                except Exception:
                    # Fallback: conexión única si falla el pool
                    logger.warning("Falling back to single connection for PostgreSQL")
                    import psycopg2.extras
                    conn = psycopg2.connect(
                        pg_dsn,
                        sslmode="require",
                        cursor_factory=psycopg2.extras.RealDictCursor,
                    )
                    conn.autocommit = False
                    return conn
    # Obtiene una conexión del pool (o crea una si hay capacidad)
    conn = _pg_pool.getconn()
    conn.autocommit = False
    return conn


# Devuelve la conexión al pool o la cierra según el motor
def liberar_conexion(conn):
    global _pg_pool
    if DATABASE_URL and _pg_pool:
        _pg_pool.putconn(conn)
    else:
        conn.close()


# Convierte resultados de cursor a lista de diccionarios
def _fetchall(conn, cursor):
    if DATABASE_URL:
        return [dict(row) for row in cursor]
    return [dict(row) for row in cursor.fetchall()]


# Obtiene el ID de la última fila insertada (varía según el motor)
def _last_id(conn, cursor):
    if DATABASE_URL:
        return cursor.fetchone()["id"]
    return cursor.lastrowid


# Indica si se está usando PostgreSQL
def es_postgresql():
    return bool(DATABASE_URL)


# Crea la tabla agenda y sus índices si no existen
def inicializar():
    conn = conectar()
    cursor = conn.cursor()
    # Esquema para PostgreSQL (con SERIAL)
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
    # Esquema para SQLite (con AUTOINCREMENT)
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
    # Confirma los cambios y libera la conexión
    conn.commit()
    liberar_conexion(conn)


# Genera un folio único con formato F-AAMMDD-XXXXXX
def generar_folio():
    import random
    import string
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"F-{timestamp}-{random_part}"
