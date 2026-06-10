from .agenda_db import conectar, generar_folio


def registrar_cita(nombre, telefono, fecha, hora, especialidad, servicio=None):
    conn = conectar()
    folio = generar_folio()
    conn.execute(
        """INSERT INTO agenda
           (nombre, telefono, fecha, hora, especialidad, servicio, tipo, estado, folio)
           VALUES (?, ?, ?, ?, ?, ?, 'cita', 'pendiente', ?)""",
        (nombre, telefono, fecha, hora, especialidad, servicio or especialidad, folio),
    )
    conn.commit()
    cita_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": cita_id, "folio": folio, "tipo": "cita"}


def registrar_reserva(nombre, telefono, producto, cantidad):
    conn = conectar()
    folio = generar_folio()
    conn.execute(
        """INSERT INTO agenda
           (nombre, telefono, producto_reservado, cantidad, tipo, estado, folio)
           VALUES (?, ?, ?, ?, 'reserva', 'pendiente', ?)""",
        (nombre, telefono, producto, cantidad, folio),
    )
    conn.commit()
    reserva_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": reserva_id, "folio": folio, "tipo": "reserva"}


def buscar_cita_por_telefono(telefono):
    conn = conectar()
    cursor = conn.execute(
        """SELECT id, nombre, telefono, fecha, hora, especialidad, servicio, folio, estado
           FROM agenda
           WHERE telefono = ? AND tipo = 'cita'
           ORDER BY fecha_creacion DESC LIMIT 5""",
        (telefono,),
    )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def buscar_reserva_por_telefono(telefono):
    conn = conectar()
    cursor = conn.execute(
        """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
           FROM agenda
           WHERE telefono = ? AND tipo = 'reserva'
           ORDER BY fecha_creacion DESC LIMIT 5""",
        (telefono,),
    )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def buscar_por_folio(folio):
    conn = conectar()
    cursor = conn.execute(
        "SELECT * FROM agenda WHERE folio = ?", (folio,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def cancelar_cita(folio):
    conn = conectar()
    conn.execute(
        "UPDATE agenda SET estado = 'cancelada' WHERE folio = ? AND tipo = 'cita'",
        (folio,),
    )
    conn.commit()
    cambios = conn.total_changes
    conn.close()
    return cambios > 0


def listar_citas(estado=None):
    conn = conectar()
    if estado:
        cursor = conn.execute(
            """SELECT id, nombre, telefono, fecha, hora, especialidad, folio, estado
               FROM agenda WHERE tipo = 'cita' AND estado = ?
               ORDER BY fecha DESC""",
            (estado,),
        )
    else:
        cursor = conn.execute(
            """SELECT id, nombre, telefono, fecha, hora, especialidad, folio, estado
               FROM agenda WHERE tipo = 'cita'
               ORDER BY fecha DESC""",
        )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def listar_reservas(estado=None):
    conn = conectar()
    if estado:
        cursor = conn.execute(
            """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
               FROM agenda WHERE tipo = 'reserva' AND estado = ?
               ORDER BY fecha_creacion DESC""",
            (estado,),
        )
    else:
        cursor = conn.execute(
            """SELECT id, nombre, telefono, producto_reservado, cantidad, folio, estado
               FROM agenda WHERE tipo = 'reserva'
               ORDER BY fecha_creacion DESC""",
        )
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados
