# Chatbot WhatsApp — Bitácora

**Última actualización:** 14 Junio 2026  
**URL:** https://web-production-96a9a.up.railway.app  
**Repo:** https://github.com/Stund-0/Chatbot

## Estado actual

- [x] API Flask + gunicorn funcionando en Railway (producción)
- [x] WhatsApp Cloud API conectada — webhook verificando y procesando mensajes
- [x] Token permanente generado desde System Users
- [x] Flujo de agendamiento: captura → pendiente_confirmacion → admin confirma/rechaza
- [x] Notificaciones al admin por nueva cita y transferencia
- [x] Log de mensajes no entendidos (`datos/no_entendidos.jsonl`)
- [x] Rate limiting (50/hora global, 30/min /chat, 10/min /reportes)
- [x] Autenticación Bearer token en `/reportes/*`
- [x] Conexión PostgreSQL con pool (min=2, max=10) + SQLite como fallback
- [x] Captura multi-turno con contexto por número
- [x] Fechas relativas (mañana, pasado mañana, días de la semana)
- [x] Filtrado de horarios disponibles contra BD
- [x] Comandos admin vía WhatsApp (CONFIRMAR/RECHAZAR + folio)
- [x] Modo simulación para desarrollo sin WhatsApp real
- [x] 22 tests pytest (API + intérprete) — todos pasan
- [x] 184 tests exhaustivos de intenciones — todas pasan
- [x] Logging estructurado JSON (configurable)
- [x] docker-compose.yml (PostgreSQL + app)
- [x] CI/CD (GitHub Actions: lint → test → docker build)
- [x] Dockerfile con usuario no-root + healthcheck
- [x] Fix fuera_horario: agenda 24/7, transfer notifica admin fuera de horario
- [x] README con documentación completa
- [x] Reconocimiento de texto libre con formato "nombre X, telefono Y, especialidad Z, fecha W, horario V"
- [x] Validación de formato en datos de cita (teléfono, fecha no pasada, hora)
- [x] Pregunta "¿Te gustaría agendar?" después de dar info (precios, horarios, servicios)
- [x] Lista de especialidades disponibles cuando se pregunta "especialidad"
- [x] Cancelación redirige a contacto directo con admin
- [x] Recordatorio automático de citas (endpoint POST /recordatorios)
- [x] Transferencia notifica al admin, quien contacta al cliente directamente
- [x] Limpieza de archivos muertos (interprete_avanzado, prompts, wrappers no usados)
- [x] **Detección multi-intent** — cuando el usuario pide 2+ datos (precios+horarios, especialidades+horarios, etc.), el bot responde con mensajes separados para cada uno
- [x] **Cita_agendar + info combinado** — si el usuario pide info y agendar en el mismo mensaje, recibe respuestas de info + prompt de agendamiento
- [x] **Fix: NameError en webhook.py** — variable `texto_respuesta` no definida causaba HTTP 500 y WhatsApp retry generaba 9 mensajes duplicados
- [x] **Fix: puntuación rompía keywords** — comas impedían detectar "especialidades," como "especialidades"; se limpia puntuación antes de matchear
- [x] **Fix: "lugar/lugares" no detectaban ubicación** — faltaban keywords en `INTENCIONES` de `interprete.py`
- [x] **Fix: contexto secuestraba preguntas info** — si había `esperando_datos=True` y el usuario preguntaba "que precios y horarios tiene", el bot lo trataba como datos de agendamiento; ahora las intenciones informativas resetean el contexto

## Commits recientes

| Fecha | Hash | Descripción |
|-------|------|-------------|
| 14 Jun | `6ed9a19` | docs: actualizar bitacora con multi-intent, fix contexto, y commits recientes |
| 14 Jun | `4ac4304` | fix: contexto de agendamiento se resetea al preguntar info |
| 14 Jun | `f80c0aa` | fix: puntuación, lugar/lugares, cita_agendar junto a info |
| 14 Jun | `73fdf32` | fix: NameError en webhook.py — duplicación de mensajes |
| 14 Jun | `0983e06` | feat: detección multi-intent + respuestas múltiples |

## Pendientes

### Prioridad alta
- [ ] **Probar flujo completo en Railway** — webhook, agendar→confirmar→usuario, handoff con admin
- [ ] **Configurar Railway para producción:**
  - Agregar `DATABASE_URL` (PostgreSQL plugin)
  - Configurar `ADMIN_TELEFONO` para notificaciones al admin
  - Configurar `REPORTES_API_KEY`
  - Verificar que `MODO_SIMULACION=false` funcione correctamente

### Prioridad media
- [ ] **Personalizar datos del negocio** — revisar y completar `datos/*.txt`, `mensajes/*.txt`, `config/empresa.txt`
- [ ] **Pruebas automatizadas del flujo de agendamiento** — no hay tests que cubran multi-turno, `registrar_cita`, confirmación admin
- [ ] **Manejo de errores en multi-intent** — qué pasa si una de las intenciones múltiples falla (ej: servicio_especifico no encuentra datos)
- [ ] **Logging de multi-intent** — registrar en `no_entendidos.jsonl` cuando el usuario hace multi-intent pero ninguna intención es reconocida

### Prioridad baja
- [ ] **Rate limiting más granular** — diferenciar límites por número de usuario
- [ ] **Métricas monitoreables** — endpoint `/health` con estado de BD, WhatsApp API, cola de mensajes
