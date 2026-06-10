from database.consultas import (
    registrar_cita,
    buscar_cita_por_telefono,
    buscar_por_folio,
    cancelar_cita,
    listar_citas,
)


def crear_cita(nombre, telefono, fecha, hora, especialidad, servicio=None):
    if not all([nombre, telefono, fecha, hora, especialidad]):
        return {"exito": False, "error": "Faltan datos requeridos"}
    resultado = registrar_cita(nombre, telefono, fecha, hora, especialidad, servicio)
    return {"exito": True, "datos": resultado}


def consultar_cita_por_telefono(telefono):
    if not telefono:
        return {"exito": False, "error": "Teléfono requerido"}
    resultados = buscar_cita_por_telefono(telefono)
    if not resultados:
        return {"exito": False, "error": "No se encontraron citas"}
    return {"exito": True, "datos": resultados}


def consultar_cita_por_folio(folio):
    if not folio:
        return {"exito": False, "error": "Folio requerido"}
    resultado = buscar_por_folio(folio)
    if not resultado:
        return {"exito": False, "error": "Cita no encontrada"}
    return {"exito": True, "datos": resultado}


def cancelar_cita_por_folio(folio):
    if not folio:
        return {"exito": False, "error": "Folio requerido"}
    exito = cancelar_cita(folio)
    if not exito:
        return {"exito": False, "error": "No se pudo cancelar la cita"}
    return {"exito": True, "mensaje": "Cita cancelada exitosamente"}


def obtener_reportes_citas(estado=None):
    return listar_citas(estado)
