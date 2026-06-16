# Módulo de consultas de alto nivel para la agenda del chatbot
import logging

from .agenda_db import conectar, liberar_conexion, generar_folio, es_postgresql, _fetchall, _last_id

logger = logging.getLogger(__name__)


# Adapta placeholders de PostgreSQL (%s) a SQLite (?)
def _adaptar_query(query):
    if not es_postgresql():
        return query.replace("%s", "?")
    return query


# Ejecuta un INSERT y retorna el ID generado; maneja rollback en caso de error
def _registrar(conn, query, params):
    try:
        cursor = conn.cursor()
        query = _adaptar_query(query)
        if es_postgresql():
            cursor.execute(query + " RETURNING id", params)
            row_id = _last_id(conn, cursor)
        else:
            cursor.execute(query, params)
            row_id = _last_id(conn, cursor)
        conn.commit()
        return row_id
    except Exception:
        logger.exception("Error en _registrar")
        conn.rollback()
        raise
    finally:
        liberar_conexion(conn)


# Ejecuta una consulta SELECT y retorna los resultados como lista de diccionarios
def _consultar(query, params=None):
    conn = conectar()
    try:
        cursor = conn.cursor()
        query = _adaptar_query(query)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return _fetchall(conn, cursor)
    except Exception:
        logger.exception("Error en _consultar")
        conn.rollback()
        raise
    finally:
        liberar_conexion(conn)


# Registra una nueva cita en la agenda y devuelve su ID, folio y tipo
def registrar_cita(nombre, telefono, fecha, hora, especialidad, servicio=None, estado="pendiente"):
    conn = conectar()
    folio = generar_folio()
    row_id = _registrar(
        conn,
        """INSERT INTO agenda
           (nombre, telefono, fecha, hora, especialidad, servicio, tipo, estado, folio)
           VALUES (%s, %s, %s, %s, %s, %s, 'cita', %s, %s)""",
        (nombre, telefono, fecha, hora, especialidad, servicio or especialidad, estado, folio),
    )
    return {"id": row_id, "folio": folio, "tipo": "cita"}


# Registra una reserva de producto y devuelve su ID, folio y tipo
def registrar_reserva(nombre, telefono, producto, cantidad):
    conn = conectar()
    folio = generar_folio()
    row_id = _registrar(
        conn,
        """INSERT INTO agenda
           (nombre, telefono, producto_reservado, cantidad, tipo, estado, folio)
           VALUES (%s, %s, %s, %s, 'reserva', 'pendiente', %s)""",
        (nombre, telefono, producto, cantidad, folio),
    )
    return {"id": row_id, "folio": folio, "tipo": "reserva"}


# Busca las últimas 5 citas de un cliente por su teléfono
def buscar_cita_por_telefono(telefono):
    return _consultar(
        """SELECT id, nombre, telefono, fecha, hora, especialidad, servicio, folio, estado
           FROM agenda
           WHERE telefono = %s AND tipo = 'cita'
           ORDER BY fecha_creacion DESC LIMIT 5""",
        (telefono,),
    )


# Busca las últimas 5 reservas de un cliente por su teléfono
def buscar_reserva_por_telefono(telefono):
    return _consultar(
        """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
           FROM agenda
           WHERE telefono = %s AND tipo = 'reserva'
           ORDER BY fecha_creacion DESC LIMIT 5""",
        (telefono,),
    )


# Confirma una cita: cambia de pendiente_confirmacion a pendiente
def confirmar_cita(folio):
    conn = conectar()
    try:
        cursor = conn.cursor()
        query = _adaptar_query(
            "UPDATE agenda SET estado = 'pendiente' WHERE folio = %s AND tipo = 'cita' AND estado = 'pendiente_confirmacion'"
        )
        cursor.execute(query, (folio,))
        conn.commit()
        cambios = cursor.rowcount
        return cambios > 0
    except Exception:
        logger.exception("Error en confirmar_cita")
        conn.rollback()
        return False
    finally:
        liberar_conexion(conn)


# Rechaza una cita: cambia de pendiente_confirmacion a rechazada
def rechazar_cita(folio):
    conn = conectar()
    try:
        cursor = conn.cursor()
        query = _adaptar_query(
            "UPDATE agenda SET estado = 'rechazada' WHERE folio = %s AND tipo = 'cita' AND estado = 'pendiente_confirmacion'"
        )
        cursor.execute(query, (folio,))
        conn.commit()
        cambios = cursor.rowcount
        return cambios > 0
    except Exception:
        logger.exception("Error en rechazar_cita")
        conn.rollback()
        return False
    finally:
        liberar_conexion(conn)


# Busca una cita por su folio único; retorna None si no existe
def buscar_cita_por_folio(folio):
    conn = conectar()
    try:
        cursor = conn.cursor()
        query = _adaptar_query(
            "SELECT * FROM agenda WHERE folio = %s AND tipo = 'cita'"
        )
        cursor.execute(query, (folio,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception:
        logger.exception("Error en buscar_cita_por_folio")
        conn.rollback()
        raise
    finally:
        liberar_conexion(conn)


# Retorna las horas ocupadas de una fecha específica (citas activas)
def buscar_citas_por_fecha(fecha):
    return _consultar(
        """SELECT hora FROM agenda
           WHERE fecha = %s AND tipo = 'cita' AND estado IN ('pendiente', 'pendiente_confirmacion')
           ORDER BY hora""",
        (fecha,),
    )


# Retorna citas ocupadas en un rango de fechas (para vista de calendario)
def buscar_ocupadas_por_rango(fecha_inicio, fecha_fin):
    return _consultar(
        """SELECT fecha, hora FROM agenda
           WHERE fecha >= %s AND fecha <= %s AND tipo = 'cita' AND estado IN ('pendiente', 'pendiente_confirmacion')
           ORDER BY fecha, hora""",
        (fecha_inicio, fecha_fin),
    )


# Lista todas las citas, opcionalmente filtradas por estado
def listar_citas(estado=None):
    if estado:
        return _consultar(
            """SELECT id, nombre, telefono, fecha, hora, especialidad, folio, estado
               FROM agenda WHERE tipo = 'cita' AND estado = %s
               ORDER BY fecha DESC""",
            (estado,),
        )
    return _consultar(
        """SELECT id, nombre, telefono, fecha, hora, especialidad, folio, estado
           FROM agenda WHERE tipo = 'cita'
           ORDER BY fecha DESC""",
    )


# Lista todas las reservas, opcionalmente filtradas por estado
def listar_reservas(estado=None):
    if estado:
        return _consultar(
            """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
               FROM agenda WHERE tipo = 'reserva' AND estado = %s
               ORDER BY fecha_creacion DESC""",
            (estado,),
        )
    return _consultar(
        """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
           FROM agenda WHERE tipo = 'reserva'
           ORDER BY fecha_creacion DESC""",
    )
