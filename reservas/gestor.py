from database.consultas import (
    registrar_reserva,
    buscar_reserva_por_telefono,
    buscar_por_folio,
    listar_reservas,
)


def crear_reserva(nombre, telefono, producto, cantidad=1):
    if not all([nombre, telefono, producto]):
        return {"exito": False, "error": "Faltan datos requeridos"}
    resultado = registrar_reserva(nombre, telefono, producto, cantidad)
    return {"exito": True, "datos": resultado}


def consultar_reserva_por_telefono(telefono):
    if not telefono:
        return {"exito": False, "error": "Teléfono requerido"}
    resultados = buscar_reserva_por_telefono(telefono)
    if not resultados:
        return {"exito": False, "error": "No se encontraron reservas"}
    return {"exito": True, "datos": resultados}


def consultar_reserva_por_folio(folio):
    if not folio:
        return {"exito": False, "error": "Folio requerido"}
    resultado = buscar_por_folio(folio)
    if not resultado:
        return {"exito": False, "error": "Reserva no encontrada"}
    return {"exito": True, "datos": resultado}


def obtener_reportes_reservas(estado=None):
    return listar_reservas(estado)
