# Chatbot WhatsApp — Bitácora

**Última actualización:** Junio 2026  
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

## Pendientes

- [ ] **Personalizar datos del negocio** — `datos/*.txt`, `mensajes/*.txt`, `config/empresa.txt` (tuyo)
- [ ] **Configurar Railway:**
  - Agregar `DATABASE_URL` (PostgreSQL plugin)
  - Configurar `ADMIN_TELEFONO` para notificaciones
  - Configurar `REPORTES_API_KEY`
- [ ] **Probar en Railway** — verificar webhook, flujo completo agendar→confirmar→usuario
