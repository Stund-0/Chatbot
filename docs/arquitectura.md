# Arquitectura del Sistema

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     WhatsApp Cloud API                       │
│                  (Facebook Graph API v22.0)                  │
└──────────────┬────────────────────────────────┬──────────────┘
               │ Webhook (POST/GET)             │ Envío (POST)
               ▼                                ▼
┌──────────────────────────────┐  ┌──────────────────────────┐
│  whatsapp/webhook.py         │  │  whatsapp/sender.py      │
│  • Verifica webhook          │  │  • enviar_texto()        │
│  • Recibe mensajes entrantes │  │  • POST /v22.0/.../messages │
│  • Delega en chatbot         │  │  • Simulación en consola │
└──────────────┬───────────────┘  └──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                     api.py (Flask)                           │
│  • GET / → info del chatbot                                  │
│  • GET /salud → health check                                 │
│  • POST /chat → endpoint público para pruebas                │
│  • GET/POST /webhook → blueprint registrado                  │
│  • GET /reportes/* → endpoints protegidos con API key        │
│  • GET /health → health check con DB + WhatsApp              │
│  • Rate limiting: 50/hora global, 30/min /chat, 10/min /reportes│
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    chatbot.py (Chatbot)                      │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Config      │  │ Contextos    │  │ Base conocimiento │    │
│  │ empresa.txt │  │ por número   │  │ datos/*.txt      │    │
│  │ settings.js.│  │ multi-turno  │  │ mensajes/*.txt   │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │            Motor de procesamiento                    │    │
│  │  1. Admin command? → CONFIRMAR/RECHAZAR              │    │
│  │  2. Detectar intención (ia/interprete.py)            │    │
│  │  3. Extraer entidades (fecha, hora, nombre, etc.)    │    │
│  │  4. Validar contexto previo                          │    │
│  │  5. Detectar multi-intent                            │    │
│  │  6. Enrutar a handler específico (20 handlers)       │    │
│  │  7. Guardar/limpiar contexto                         │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                  database/ (Capa de datos)                   │
│                                                              │
│  agenda_db.py                consultas.py                    │
│  • Conexión PostgreSQL/SQLite • CRUD citas y reservas        │
│  • Pool de conexiones (PG)    • Búsquedas por folio/tel/fecha│
│  • Esquema de tablas          • Confirmar/rechazar citas     │
│  • Generación de folios       • Listados con filtro estado   │
└──────────────────────────────────────────────────────────────┘
```

##Flujo de datos

```
Usuario WhatsApp → Webhook → chatbot.procesar_mensaje()
  → detectar_intencion()
  → extraer_entidades()
  → (contexto previo?)
  → (multi-intent?)
  → handler específico
  → (registrar en BD?)
  → (notificar admin?)
  → respuesta al usuario
```

## Base de datos

### Esquema de tabla `agenda`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER/PK | ID autoincremental |
| `nombre` | TEXT | Nombre del cliente |
| `telefono` | TEXT | Teléfono de contacto |
| `fecha` | TEXT | Fecha de cita (dd/mm/aaaa) |
| `hora` | TEXT | Hora de cita |
| `servicio` | TEXT | Servicio solicitado |
| `especialidad` | TEXT | Especialidad médica |
| `producto_reservado` | TEXT | Producto (para reservas) |
| `cantidad` | INTEGER | Cantidad (para reservas) |
| `tipo` | TEXT | `cita` o `reserva` |
| `estado` | TEXT | `pendiente_confirmacion`, `pendiente`, `confirmada`, `rechazada`, `cancelada` |
| `folio` | TEXT | Formato: `F-YYMMDD-RRRRRR` |
| `fecha_creacion` | TIMESTAMP | Fecha de registro |
| `notas` | TEXT | Notas adicionales |

### Soporte dual PostgreSQL / SQLite

- **PostgreSQL** (producción): Pool de conexiones (min=2, max=10) con SSL.
- **SQLite** (desarrollo/local): WAL mode, busy timeout 5s.
- La detección es automática via `DATABASE_URL` o `CUSTOM_DB_URL`.
