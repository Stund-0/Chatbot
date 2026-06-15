# Guía de Despliegue

## Despliegue local

### Requisitos

- Python 3.12+
- (Opcional) PostgreSQL 16 para pruebas con BD real

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Stund-0/Chatbot.git
cd Chatbot

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env según sea necesario
```

### Ejecución

```bash
# Modo simulación (no requiere WhatsApp)
python api.py

# Con Gunicorn (local)
python run.py

# Con Docker Compose (incluye PostgreSQL)
docker compose up --build
```

### Variables de entorno

| Variable | Requerido | Default | Descripción |
|----------|-----------|---------|-------------|
| `WHATSAPP_TOKEN` | Producción | — | Token permanente de WhatsApp Cloud API |
| `WHATSAPP_PHONE_ID` | Producción | — | ID del número de teléfono en WhatsApp Business |
| `WHATSAPP_VERIFY_TOKEN` | Sí | `chatbot123` | Token de verificación del webhook |
| `WHATSAPP_API_VERSION` | No | `v22.0` | Versión de la API de WhatsApp |
| `DATABASE_URL` | No | — | URL de PostgreSQL (vacío = SQLite) |
| `CUSTOM_DB_URL` | No | — | Fallback para Railway (host:port) |
| `ADMIN_TELEFONO` | Sí | — | Número del admin (notificaciones WhatsApp) |
| `REPORTES_API_KEY` | Recomendado | — | API key para endpoints de reportes |
| `MODO_SIMULACION` | Sí | `true` | `true` = simulación, `false` = producción |
| `DEBUG` | No | `true` | Modo debug de Flask |
| `LOG_LEVEL` | No | `INFO` | Nivel de logging |
| `LOG_FORMAT` | No | `text` | `json` o `text` |

---

## Despliegue en Railway

### Opción 1: Deploy automático desde GitHub

1. Conecta el repo `Stund-0/Chatbot` a Railway
2. Railway detecta `railway.json` y usa Dockerfile automáticamente
3. Agrega las variables de entorno en el dashboard de Railway
4. El servicio se despliega con `python run.py` (puerto 5000)

### Opción 2: Deploy con Railway CLI

```bash
npm i -g @railway/cli
railway login
railway link
railway up
railway variables set WHATSAPP_TOKEN=...
railway variables set MODO_SIMULACION=false
```

### Configuración de Railway

Variables requeridas en producción:

| Variable | Valor |
|----------|-------|
| `WHATSAPP_TOKEN` | Token permanente de System Users |
| `WHATSAPP_PHONE_ID` | ID del número telefónico |
| `ADMIN_TELEFONO` | Número del admin (ej: 521234567890) |
| `REPORTES_API_KEY` | Clave para acceder a reportes |
| `MODO_SIMULACION` | `false` |
| `DATABASE_URL` | Generada por Railway PostgreSQL plugin |

### Problemas conocidos

**1. `$PORT` no se expande en startCommand**

Railway usa exec form (sin shell). Solución: el entrypoint es `python run.py` que lee `PORT` desde `os.environ`.

**2. `DATABASE_URL` contiene solo host:port**

Railway inyecta `host:port` en lugar de URL completa. Solución: `_build_pg_dsn()` en `database/agenda_db.py` construye la URL automáticamente. Usar `CUSTOM_DB_URL` como fallback.

---

## Docker

### Construir imagen

```bash
docker build -t chatbot-whatsapp .
```

### Ejecutar contenedor

```bash
docker run -p 5000:5000 \
  -e WHATSAPP_TOKEN=... \
  -e WHATSAPP_PHONE_ID=... \
  -e MODO_SIMULACION=true \
  chatbot-whatsapp
```

### Docker Compose (desarrollo)

```bash
docker compose up --build
```

Inicia PostgreSQL 16 + la app, con la app conectándose automáticamente a PostgreSQL.

---

## CI/CD

El pipeline en `.github/workflows/ci.yml` ejecuta:

| Job | Trigger | Descripción |
|-----|---------|-------------|
| `lint` | push + PR | Flake8 (errores + warnings) |
| `test` | push + PR | 184 tests exhaustivos + pytest |
| `docker` | main branch | Build de imagen Docker |
| `deploy` | (deshabilitado) | Placeholder para deploy automático |
