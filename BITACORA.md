=== CHATBOT WHATSAPP - BITÁCORA DE CONFIGURACIÓN ===
Última actualización: Junio 2026

========================================
ESTADO ACTUAL
========================================

✔ Proyecto creado localmente en C:\Users\Victor\Documents\Programming\chatbot
✔ Código verificado - 32/32 pruebas pasadas
✔ Desplegado en Railway: https://web-production-96a9a.up.railway.app
✔ API funcionando (chat, reportes, webhook)
✔ MODO_SIMULACION = false (producción)
✔ WHATSAPP_VERIFY_TOKEN = chatbot123
✔ Webhook verificando correctamente (GET /webhook)
✔ Webhook procesando mensajes (POST /webhook)
✔ Chatbot responde por API y WhatsApp real
✔ Token permanente generado desde System Users (Business Settings)

========================================
HISTORIAL DE CAMBIOS
========================================

[2026-06-11] Conexión WhatsApp real:
  - Se generó token permanente desde System Users en
    https://business.facebook.com/settings/system-users
  - Se asignaron permisos: whatsapp_business_management,
    whatsapp_business_messaging
  - Se actualizó WHATSAPP_TOKEN en Railway con token permanente
  - Se cambió MODO_SIMULACION = false
  - Prueba exitosa: bot responde mensajes en WhatsApp real

========================================
PRÓXIMOS PASOS (pendientes)
========================================

[ ] 1. Personalizar datos del negocio (datos/*.txt, mensajes/*.txt):
      - config/empresa.txt (nombre, tipo, eslogan)
      - datos/informacion.txt (descripción del negocio)
      - datos/servicios.txt (servicios reales)
      - datos/precios.txt (precios reales)
      - datos/horarios.txt (horarios reales)
      - datos/horarios_disponibles.txt (slots para citas)
      - datos/direccion.txt (dirección real)
      - datos/telefonos.txt (teléfonos reales)
      - datos/correo.txt (correos reales)
      - datos/productos.txt (productos reales)
      - datos/preguntas_frecuentes.txt (FAQ real)
      - mensajes/*.txt (personalizar respuestas del bot)

========================================
DATOS DE CONTACTO RAILWAY
========================================

URL: https://web-production-96a9a.up.railway.app
API Chat: POST /chat
Webhook: POST /webhook
Reportes: GET /reportes/citas, GET /reportes/reservas
GitHub: https://github.com/Stund-0/Chatbot

========================================
NOTAS DE COSTOS
========================================

WhatsApp Cloud API:
  - Conversaciones de servicio: GRATIS (cliente inicia)
  - 1,000 conversaciones de servicio gratis/mes
  - Sin costo para respuestas automáticas del bot

Railway:
  - $5 USD crédito único de prueba
  - Plan Hobby: $5/mes después del crédito
  - Estimado total: ~$5-10/mes

========================================
