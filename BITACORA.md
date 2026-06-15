# Chatbot WhatsApp — Bitácora

**Última actualización:** 15 Junio 2026  
**URL:** https://web-production-96a9a.up.railway.app  
**Repo:** https://github.com/Stund-0/Chatbot

## Estado actual

- [x] API Flask + gunicorn funcionando en Railway (producción)
- [x] WhatsApp Cloud API conectada — webhook verificando y procesando mensajes
- [x] Token permanente generado desde System Users
- [x] Flujo de agendamiento: captura → pendiente_confirmacion → admin confirma/rechaza
- [x] Notificaciones al admin por nueva cita y transferencia
- [x] Log de mensajes no entendidos (`datos/no_entendidos.jsonl`)
- [x] Rate limiting por número de usuario (200/día, 50/hora global; 30/min /chat, 30/min webhook, 10/min /reportes)
- [x] Autenticación Bearer token en `/reportes/*`
- [x] Conexión PostgreSQL con pool thread-safe (min=2, max=10) + SQLite como fallback
- [x] Captura multi-turno con contexto por número
- [x] Fechas relativas (mañana, pasado mañana, días de la semana)
- [x] Filtrado de horarios disponibles contra BD + lectura de `horarios_disponibles.txt`
- [x] Comandos admin vía WhatsApp (CONFIRMAR/RECHAZAR + folio) con sender inyectado
- [x] Modo simulación para desarrollo (default `false` en producción)
- [x] 58 tests pytest (API + intérprete + agendamiento) — todos pasan
- [x] Logging estructurado JSON (configurable) con logging en operaciones DB
- [x] docker-compose.yml (PostgreSQL + app)
- [x] CI/CD (GitHub Actions: lint → test → docker build)
- [x] Dockerfile con usuario no-root + healthcheck
- [x] Fix fuera_horario: agenda 24/7, transfer notifica admin fuera de horario
- [x] README con documentación completa
- [x] Reconocimiento de texto libre con formato "nombre X, telefono Y, especialidad Z, fecha W, horario V"
- [x] Validación de formato en datos de cita (teléfono, fecha no pasada, hora)
- [x] Pregunta "¿Te gustaría agendar?" después de dar info (precios, horarios, servicios)
- [x] Lista de especialidades disponibles cuando se pregunta "especialidad"
- [x] Transferencia notifica al admin, quien contacta al cliente directamente
- [x] Detección multi-intent — cuando el usuario pide 2+ datos, el bot responde con mensajes separados
- [x] Endpoint `/health` con estado de DB + WhatsApp config
- [x] Config compartida `config/limiter.py` con key function por usuario
- [x] Error handling + logging en multi-intent
- [x] Thread-safe pool init con `threading.Lock` (double-checked locking)
- [x] Endpoint `/health` con estado de DB + WhatsApp config
- [x] Config compartida `config/limiter.py` con key function por usuario
- [x] 36 tests de agendamiento (DB, validación, handlers, multi-turno, admin) + 22 previos = 58
- [x] Documentación técnica actualizada (`docs/api.md`, `docs/arquitectura.md`, etc.)
- [x] ~~Recordatorio automático de citas~~ eliminado
- [x] ~~Limpieza archivos muertos~~ (interprete_avanzado, prompts, wrappers no usados)
- [x] ~~Código muerto~~ imports/funciones eliminados (consultas.py, interprete.py, api.py)
- [x] ~~`__import__("datetime")~~ corregido a import directo
- [x] ~~Connection leaks~~ corregidos: `confirmar_cita`, `rechazar_cita`, `buscar_cita_por_folio`
- [x] ~~Especialidades triplicadas~~ consolidado en constantes modulares `ESPECIALIDADES`/`PALABRAS_ESPECIALIDAD`
- [x] ~~Config muerta en settings.json~~ limpiado (11 keys eliminadas)
- [x] ~~Broad except sin logging~~ corregido con `logger.exception` en consultas.py
- [x] ~~MODO_SIMULACION default "true"~~ cambiado a "false"
- [x] ~~WhatsAppSender creado por comando admin~~ corregido con inyección via `Chatbot.__init__(sender=...)`
- [x] ~~Multi-intent interceptaba cita_agendar con datos completos~~ corregido
- [x] Rate limiter migrado a Redis (`REDIS_URL`) — fallback a `memory://` si no está configurado
- [x] Fix horarios duplicados en multi-intent — si ya se mostraron, no se repiten en prompt de agendar
- [x] `inicializar_db()` movido fuera de `if __name__` — la tabla se crea al importar con gunicorn
- [x] `cursor_factory=RealDictCursor` en pool PostgreSQL — corrige 500 al agendar citas en Railway
- [x] try/except en `/chat` — errores se loggean sin devolver 500 al cliente
- [x] Redis instalado y probado localmente (58 tests + rate limiting funcional)
- [x] Pool size configurable via `PG_POOL_MIN`/`PG_POOL_MAX` (antes hardcodeado 2/10)
- [x] Zona horaria configurable via `TZ` (antes hardcodeada Mexico_City)
- [x] Horario laboral configurable via `HORARIO_WEEKDAY`/`HORARIO_SATURDAY` (antes hardcodeado 8-18/9-14)
- [x] Gunicorn workers/timeout configurables via `GUNICORN_WORKERS`/`GUNICORN_TIMEOUT`
- [x] `node_modules/` eliminado del repo (493 archivos, ~93k líneas) + `.gitignore` actualizado

## Commits recientes

| Fecha | Hash | Descripción |
|-------|------|-------------|
| 14 Jun | `da1d8c6` | fix: pool thread-safe, sender inyectado, especialidades consolidadas, modo_simulacion default false, logging DB, config limpiado, docs actualizados |
| 14 Jun | `6ed9a19` | docs: actualizar bitacora con multi-intent, fix contexto, y commits recientes |
| 14 Jun | `4ac4304` | fix: contexto de agendamiento se resetea al preguntar info |
| 14 Jun | `f80c0aa` | fix: puntuación, lugar/lugares, cita_agendar junto a info |
| 14 Jun | `73fdf32` | fix: NameError en webhook.py — duplicación de mensajes |
| 14 Jun | `0983e06` | feat: detección multi-intent + respuestas múltiples |
| 14 Jun | `3920a62` | docs: actualizar bitacora con resumen de sesión, fixes y pendientes |
| 15 Jun | `edb6471` | fix: evitar duplicar horarios en multi-intent + rate limiter con Redis |
| 15 Jun | `f73e972` | fix: inicializar DB al importar módulo, no solo en `__main__` |
| 15 Jun | `af3f1e0` | fix: try/except en chat endpoint para capturar error exacto |
| 15 Jun | `9cd9340` | fix: `cursor_factory=RealDictCursor` en pool PostgreSQL |

## Pendientes

### Prioridad alta
- [x] **Probar flujo completo en Railway** — webhook, agendar→confirmar→usuario, handoff con admin ✅
- [ ] **Configurar Railway para producción:**
  - Configurar `ADMIN_TELEFONO` para notificaciones al admin
  - Configurar `REPORTES_API_KEY`
  - Personalizar datos del negocio (`datos/*.txt`, `mensajes/*.txt`, `config/empresa.txt`)
  - Agregar Redis (Upstash gratis) y configurar `REDIS_URL` para rate limiter compartido entre workers

### Prioridad media
- [x] **`storage_uri="memory://"` en rate limiter** — migrado a Redis vía `REDIS_URL`; si no está configurada, fallback a `memory://`
- [ ] **Agregar Redis a Railway (Upstash)** — para rate limiter compartido entre workers de gunicorn

### Prioridad baja
- [ ] **Pool size hardcodeado** (`minconn=2, maxconn=10`) — podría ser configurable via env vars
- [ ] **Zona horaria hardcodeada** `America/Mexico_City` en `chatbot.py:11`
- [ ] **Horario laboral hardcodeado** 8-18 weekdays, 9-14 Sat en `chatbot.py:260-264`
- [ ] **Gunicorn workers/timeout hardcodeados** en `run.py:12-13`
- [x] **`node_modules/` y `venv/` commiteados** — limpiado (`node_modules/` eliminado, 93k líneas menos en repo)
- [ ] **Notificaciones por email** — no existe sistema de reporte por email
