# Guía para Desarrolladores

## Estructura del proyecto

```
chatbot.py          → Lógica principal del chatbot (1100 líneas)
api.py              → Aplicación Flask y endpoints
wsgi.py             → Entry point WSGI
run.py              → Entry point con Gunicorn
ia/interprete.py    → Detección de intenciones por reglas
database/
  agenda_db.py      → Conexión y esquema de BD
  consultas.py      → CRUD de citas y reservas
whatsapp/
  webhook.py        → Webhook de WhatsApp Cloud API
  sender.py         → Envío de mensajes vía API
  handlers.py       → Manejador de respuestas
  notificaciones.py → Notificaciones al admin
config/
  empresa.txt       → Datos del negocio
  settings.json     → Configuración general
  logging_config.py → Logging estructurado JSON
datos/              → Base de conocimiento (11 archivos)
mensajes/           → Plantillas de respuesta (10 archivos)
tests/
  test_interprete.py → Tests de detección de intenciones
  test_api.py        → Tests de API Flask
test_exhaustivo.py   → 184 tests de cobertura de intenciones
```

## Añadir una nueva intención

### 1. Registrar keywords en `ia/interprete.py`

```python
INTENCIONES = {
    # ... existentes ...
    "mi_nueva_intencion": [
        "palabra clave 1",
        "palabra clave 2",
        "frase detonante",
    ],
}
```

Si es una intención informativa, agrégala también a:

```python
INTENCIONES_INFORMATIVAS = {"horarios", "precios", ..., "mi_nueva_intencion"}
```

### 2. Crear handler en `chatbot.py`

```python
def _manejar_mi_nueva_intencion(self, mensaje, entidades, numero):
    respuesta = "Respuesta personalizada"
    return {"respuesta": respuesta, "intencion": "mi_nueva_intencion", "transferir": False}
```

### 3. Registrar en el dispatch `procesar_mensaje()`

```python
gestor_respuesta = {
    # ... existentes ...
    "mi_nueva_intencion": self._manejar_mi_nueva_intencion,
}
```

### 4. Agregar a multi-intent si aplica

En `_procesar_intenciones_multiples()`, agrega el manejador:

```python
gestor_respuesta = {
    # ... existentes ...
    "mi_nueva_intencion": self._manejar_mi_nueva_intencion,
}
```

### 5. Añadir tests en `tests/test_interprete.py`

```python
def test_mi_intencion(self):
    resultado = detectar_intencion("frase detonante")
    assert resultado == "mi_nueva_intencion"
```

### 6. Añadir casos al `test_exhaustivo.py`

```python
PRUEBAS = {
    # ... existentes ...
    "mi_nueva_intencion": [
        "frase detonante",
        "palabra clave 1",
        "otra variante",
    ],
}
```

## Añadir un nuevo tipo de respuesta

Si necesitas que el chatbot responda en un formato diferente (ej: botones, listas, imágenes):

### 1. Extender `WhatsAppSender` en `whatsapp/sender.py`

```python
def enviar_botones(self, numero_destino, texto, botones):
    # Construir payload con buttons
    # POST a WhatsApp Cloud API
    pass
```

### 2. Usar desde el handler

```python
def _manejar_algo(self, mensaje, entidades, numero):
    if not self.modo_simulacion:
        from flask import current_app
        sender = current_app.config["sender"]
        sender.enviar_botones(numero, "Texto", [{"id": "opt1", "title": "Opción 1"}])
    return {"respuesta": "Respuesta", "intencion": "algo", "transferir": False}
```

## Pruebas

### Tests unitarios

```bash
# Tests de intérprete + API
pytest tests/ -v

# Tests exhaustivos de intenciones
python test_exhaustivo.py
```

### Agregar tests de base de datos

Los tests actuales no cubren operaciones de BD. Para agregarlos:

```python
def test_registrar_cita(self):
    from database.consultas import registrar_cita, buscar_cita_por_folio
    resultado = registrar_cita("Test", "521234567890", "15/06/2026", "10:00 AM", "Medicina General")
    assert "folio" in resultado
    cita = buscar_cita_por_folio(resultado["folio"])
    assert cita["nombre"] == "Test"
```

## Logging

El sistema usa logging estructurado con formato JSON.

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Mensaje", extra={"key": "value"})
```

Salida JSON:
```json
{"timestamp": "...", "level": "INFO", "logger": "chatbot", "module": "chatbot", "function": "procesar_mensaje", "line": 535, "message": "Mensaje", "extra": {"key": "value"}}
```

Los mensajes no entendidos se registran automáticamente en `datos/no_entendidos.jsonl`.

## Depuración

### Simulación vs producción

- `MODO_SIMULACION=true`: las respuestas se devuelven en JSON, no se envían por WhatsApp
- `MODO_SIMULACION=false`: las respuestas se envían realmente por WhatsApp Cloud API

### Ver estado del chatbot

```bash
curl http://localhost:5000/
# → {"nombre": "Mi Negocio", "modo": "simulación", "estado": "activo"}
```

### Probar desde consola

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "Hola, quiero agendar una cita", "numero": "521234567890"}'
```

## Consideraciones de seguridad

- **Rate limiting**: 50/hora global, 30/min en `/chat`, 10/min en `/reportes`
- **Autenticación**: Endpoints `/reportes/*` requieren `Authorization: Bearer <REPORTES_API_KEY>`
- **Tokens**: No committear `WHATSAPP_TOKEN` ni `REPORTES_API_KEY` en el código
- **Validación**: Los datos de cita se validan (teléfono 8-15 dígitos, fecha no pasada, hora formato válido)
- **No-root**: Dockerfile ejecuta como usuario no-root
