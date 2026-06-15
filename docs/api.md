# Referencia de API

## Endpoints públicos

### `GET /`

Info del chatbot.

**Respuesta:**
```json
{
  "nombre": "Mi Negocio",
  "version": "1.0.0",
  "tipo": "Consultorio Médico",
  "eslogan": "Tu salud es nuestra prioridad",
  "estado": "activo",
  "modo": "simulación"
}
```

---

### `GET /salud`

Health check.

**Respuesta:**
```json
{
  "status": "ok",
  "timestamp": "2026-06-14T12:00:00"
}
```

---

### `POST /chat`

Procesar un mensaje en el chatbot. Rate limit: 30/min.

**Body:**
```json
{
  "mensaje": "Hola, quiero agendar una cita",
  "numero": "521234567890",
  "contexto": {}
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `mensaje` | string | Sí | Texto del mensaje |
| `numero` | string | No | Número de teléfono (default: "0000000000") |
| `contexto` | object | No | Contexto adicional para entidades |

**Respuesta (modo simulación):**
```json
{
  "respuesta": "¡Hola! ¿En qué puedo ayudarte?",
  "respuestas": ["¡Hola! ¿En qué puedo ayudarte?"],
  "intencion": "saludo",
  "transferir": false,
  "modo": "simulacion"
}
```

**Respuesta (modo producción):**
```json
{
  "respuesta": "Mensaje de respuesta",
  "respuestas": ["Mensaje 1", "Mensaje 2"],
  "intencion": "horarios",
  "transferir": false,
  "enviado": true
}
```

---

### `GET /webhook`

Verificación del webhook de WhatsApp.

**Query params:** `hub.mode`, `hub.verify_token`, `hub.challenge`

**Respuesta:** El challenge si `verify_token` coincide, 403 si no.

---

### `POST /webhook`

Webhook entrante de WhatsApp Cloud API. Procesa mensajes y envía respuestas automáticamente.

---

## Endpoints protegidos (Bearer token)

Requieren header `Authorization: Bearer <REPORTES_API_KEY>`.

### `GET /reportes/citas`

Listar citas. Rate limit: 10/min.

**Query params:**
- `estado` (opcional) — filtrar por estado: `pendiente_confirmacion`, `pendiente`, `rechazada`, `cancelada`

**Respuesta:**
```json
{
  "total": 2,
  "citas": [
    {
      "nombre": "Juan Pérez",
      "telefono": "521234567890",
      "fecha": "15/06/2026",
      "hora": "10:00 AM",
      "servicio": "Medicina General",
      "folio": "F-240614-ABC123",
      "estado": "pendiente_confirmacion"
    }
  ]
}
```

---

### `GET /reportes/reservas`

Listar reservas. Rate limit: 10/min.

**Query params:**
- `estado` (opcional) — filtrar por estado

**Respuesta:**
```json
{
  "total": 1,
  "reservas": [
    {
      "nombre": "María García",
      "telefono": "521234567891",
      "producto": "Consulta Especializada",
      "cantidad": 1,
      "folio": "F-240614-DEF456",
      "estado": "pendiente"
    }
  ]
}
```

---

## Rate limiting

| Ámbito | Límite |
|--------|--------|
| Global | 200/día, 50/hora |
| `POST /chat` | 30/minuto |
| `GET /reportes/*` | 10/minuto |
