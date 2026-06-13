# Chatbot WhatsApp

Chatbot inteligente para WhatsApp Business API con agendamiento de citas, reservas de productos y respuestas automáticas. Construido con Flask y desplegable en Railway.

## Caracteristicas

- Recepción y envío de mensajes vía WhatsApp Cloud API
- Detección de intenciones por reglas + OpenAI (opcional)
- Agendamiento de citas con confirmación administrativa
- Reserva de productos/servicios
- Consulta de horarios, precios, ubicación y contacto
- Panel de reportes protegido por API key
- Soporte PostgreSQL (producción) y SQLite (desarrollo)
- Rate limiting en endpoints públicos
- Logging estructurado en formato JSON
- Modo simulación para pruebas sin WhatsApp real

## Requisitos

- Python 3.12+
- (Opcional) Cuenta de WhatsApp Business API
- (Opcional) OpenAI API key para intérprete avanzado

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
| `WHATSAPP_PHONE_ID` | Producción | ID de número de teléfono de WhatsApp Business |
| `WHATSAPP_VERIFY_TOKEN` | Sí | Token de verificación del webhook |
| `WHATSAPP_API_VERSION` | No | Versión de la API (default: v22.0) |
| `OPENAI_API_KEY` | No | Para intérprete NLP avanzado |
| `ADMIN_TELEFONO` | Sí | Número del administrador (notificaciones) |
| `ADMIN_CORREO` | No | Correo del administrador |
| `DATABASE_URL` | No | URL de PostgreSQL (vacío = SQLite) |
| `REPORTES_API_KEY` | Recomendado | API key para endpoints /reportes/ |
| `MODO_SIMULACION` | Sí | `true` para pruebas, `false` para producción |
| `DEBUG` | No | Modo debug de Flask |

## Desarrollo local

```bash
# Modo simulación (no requiere WhatsApp real)
python api.py

# Probar el chatbot en consola interactiva
python test_chat.py

# Ejecutar pruebas de intenciones
python test_exhaustivo.py

# Ejecutar tests automatizados
pytest tests/ -v
```

### Con Docker Compose (PostgreSQL)

```bash
docker compose up --build
```

## API endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | No | Info del chatbot |
| GET | `/salud` | No | Health check |
| POST | `/chat` | No | Enviar mensaje al chatbot |
| POST | `/webhook` | Meta | Webhook de WhatsApp |
| GET | `/webhook` | Meta | Verificación de webhook |
| GET | `/reportes/citas` | Bearer | Listar citas |
| GET | `/reportes/reservas` | Bearer | Listar reservas |

## Despliegue en Railway

```bash
# Asegúrate de tener las variables de entorno configuradas en Railway:
# WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, ADMIN_TELEFONO,
# DATABASE_URL (PostgreSQL), REPORTES_API_KEY, MODO_SIMULACION=false

# El proyecto incluye:
# - Dockerfile
# - railway.json
# - Procfile (fallback para deploys sin Docker)
```

## Estructura del proyecto

```
├── api.py                     # Aplicación Flask
├── wsgi.py                    # Entry point WSGI
├── chatbot.py                 # Lógica principal del chatbot
├── config/
│   ├── empresa.txt            # Datos de la empresa
│   ├── settings.json          # Configuración general
│   └── logging_config.py      # Configuración de logging
├── database/
│   ├── agenda_db.py           # Conexión y esquema de BD
│   └── consultas.py           # CRUD de citas y reservas
├── datos/                     # Base de conocimiento del negocio
├── ia/
│   ├── interprete.py          # Detección de intenciones por reglas
│   └── interprete_avanzado.py # Intérprete con OpenAI
├── mensajes/                  # Plantillas de respuestas
├── prompts/                   # Prompts del sistema
├── whatsapp/
│   ├── webhook.py             # Webhook de WhatsApp
│   ├── handlers.py            # Manejador de mensajes
│   ├── sender.py              # Envío de mensajes
│   └── notificaciones.py      # Notificaciones al admin
├── tests/                     # Tests automatizados
├── docker-compose.yml         # PostgreSQL + App
├── Dockerfile                 # Imagen Docker
├── railway.json               # Config Railway
└── Procfile                   # Proceso web para gunicorn
```
