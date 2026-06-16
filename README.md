# Chatbot WhatsApp — Agendamiento Inteligente

Chatbot inteligente para WhatsApp Business API con detección de intenciones, agendamiento de citas con confirmación administrativa, reserva de productos y respuestas automáticas. Construido con Flask y desplegado en Railway.

## Funcionalidades

- **WhatsApp Cloud API**: Recepción y envío de mensajes en tiempo real vía webhook
- **20 intenciones detectadas**: saludo, horarios, precios, ubicación, contacto, servicios, agendar/consultar/cancelar citas, crear/consultar reservas, emergencia, FAQ, fechas disponibles, reportes admin, y más
- **Multi-intent**: Detecta y responde múltiples preguntas en un solo mensaje
- **Contexto multi-turno**: Recuerda el estado de la conversación por número de teléfono
- **Agendamiento con confirmación**: El admin confirma o rechaza citas vía WhatsApp (CONFIRMAR/RECHAZAR + folio)
- **Notificaciones al admin**: Nueva cita, transferencia a humano, fuera de horario
- **Fechas relativas**: "mañana", "pasado mañana", "lunes", etc.
- **Filtrado de disponibilidad**: Horarios libres vs ocupados desde la BD
- **Rate limiting**: 200 msgs/día por usuario, 50/hora global, con Redis o memoria
- **Reportes protegidos**: Endpoints `/reportes/*` con API key
- **Dual DB**: PostgreSQL (producción) con pool thread-safe, SQLite (desarrollo)
- **58 tests automatizados** (API + intérprete + agendamiento)
- **Logging estructurado JSON** configurable
- **Modo simulación**: Pruebas sin WhatsApp real

## Stack técnico

| Componente | Tecnología |
|------------|-----------|
| Framework | Flask 3.1 |
| WSGI | Gunicorn 23 |
| Base de datos | PostgreSQL / SQLite |
| Cache/Rate limiter | Redis (o memoria) |
| Contenedor | Docker + Python 3.12-slim |
| Cloud | Railway |
| CI/CD | GitHub Actions (lint → test → docker build) |

## Requisitos

- Python 3.12+
- Cuenta de WhatsApp Business API (para producción)
- (Opcional) OpenAI API key

## Configuración rápida

```bash
cp .env.example .env
# Editar .env con tus credenciales
pip install -r requirements.txt
python wsgi.py
```

## Variables de entorno

| Variable | Requerido | Descripción |
|----------|-----------|-------------|
| `WHATSAPP_TOKEN` | Producción | Token permanente de WhatsApp Cloud API |
| `WHATSAPP_PHONE_ID` | Producción | ID de teléfono de WhatsApp Business |
| `WHATSAPP_VERIFY_TOKEN` | Sí | Token de verificación del webhook |
| `ADMIN_TELEFONO` | Sí | Número del administrador (notificaciones) |
| `DATABASE_URL` | No | URL de PostgreSQL (vacío = SQLite) |
| `REPORTES_API_KEY` | Recomendado | API key para endpoints `/reportes/` |
| `MODO_SIMULACION` | Sí | `true` para pruebas, `false` para producción |
| `REDIS_URL` | No | Redis para rate limiter compartido |

## Desarrollo local

```bash
# Modo simulación (no requiere WhatsApp real)
python api.py

# Probar el chatbot en consola interactiva
python test_exhaustivo.py

# Ejecutar tests automatizados
pytest tests/ -v
```

### Con Docker Compose

```bash
docker compose up --build
```

## API endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | No | Info del chatbot |
| GET | `/salud` | No | Health check simple |
| GET | `/health` | No | Health check con DB + WhatsApp |
| POST | `/chat` | No | Enviar mensaje al chatbot (pruebas) |
| POST | `/webhook` | Meta | Webhook de WhatsApp |
| GET | `/webhook` | Meta | Verificación de webhook |
| GET | `/reportes/citas` | Bearer | Listar citas |
| GET | `/reportes/reservas` | Bearer | Listar reservas |

## Despliegue

### Railway (producción)

```bash
# Configurar variables en Railway:
# WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, ADMIN_TELEFONO,
# DATABASE_URL (PostgreSQL), REPORTES_API_KEY, MODO_SIMULACION=false
```

Incluye: `Dockerfile`, `railway.json`, `Procfile`

## Personalización

Editar los archivos en:

- `datos/*.txt` — Base de conocimiento del negocio (servicios, precios, horarios, etc.)
- `mensajes/*.txt` — Plantillas de respuestas del chatbot
- `config/empresa.txt` — Nombre, tipo y eslogan del negocio

## Estructura del proyecto

```
├── api.py                     # Aplicación Flask (endpoints, notificaciones)
├── wsgi.py                    # Entry point WSGI
├── run.py                     # Arranque con Gunicorn
├── chatbot.py                 # Lógica principal del chatbot (~1100 líneas)
│
├── ia/
│   └── interprete.py          # Detección de intenciones por reglas (20 intenciones)
│
├── whatsapp/
│   ├── webhook.py             # Webhook de WhatsApp (recibe mensajes)
│   ├── sender.py              # Envío de mensajes a WhatsApp API
│   ├── handlers.py            # Orquestación de respuestas
│   └── notificaciones.py      # Notificaciones al admin
│
├── database/
│   ├── agenda_db.py           # Conexión PostgreSQL/SQLite con pool
│   └── consultas.py           # CRUD de citas y reservas
│
├── config/                    # Configuración (logging, rate limiting, empresa)
├── datos/                     # Base de conocimiento del negocio
├── mensajes/                  # Plantillas de respuestas
├── tests/                     # 58 tests automatizados
├── docs/                      # Documentación técnica
├── Dockerfile                 # Imagen Docker
└── docker-compose.yml         # PostgreSQL + App local
```
