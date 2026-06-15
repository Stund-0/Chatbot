# Flujo de Mensajes e Intenciones

## Ciclo de vida de un mensaje

```
  Mensaje entrante
       │
       ▼
┌──────────────────────────────┐
│ ¿Es comando admin?           │
│ CONFIRMAR / RECHAZAR + folio │
└──────┬───────────┬───────────┘
       │ No        │ Sí
       ▼           ▼
  Detectar       Ejecutar comando
  intención      → notificar usuario
       │
       ▼
  Extraer entidades
  (nombre, fecha, hora,
   teléfono, especialidad)
       │
       ▼
  ¿Datos completos para cita?
  (nombre + especialidad + fecha + hora)
       │
       ├── Sí → forzar intención = cita_agendar
       │
       ▼ No
  ¿Contexto previo con esperando_datos?
       │
       ├── Sí → restaurar contexto, fusionar entidades
       │         ¿Intención es informativa?
       │           ├── Sí → resetear contexto (el usuario preguntó info)
       │           └── No → continuar con flujo normal
       │
       ▼ No
  ¿Datos incompletos con indicios de cita?
  (teléfono + fecha o especialidad + hora, etc.)
       │
       ├── Sí → responder error_formato
       │
       ▼ No
  ¿Múltiples intenciones detectadas?
  (2+ intenciones informativas)
       │
       ├── Sí → _procesar_intenciones_multiples()
       │         → responder cada intención por separado
       │         → si incluye cita, agregar prompt de agendamiento
       │
       ▼ No
  Enrutar a handler según intención
       │
       ▼
  ¿Respuesta tiene esperando_datos?
       │
       ├── Sí → guardar contexto para el próximo mensaje
       └── No → limpiar contexto
       │
       ▼
  ¿Requiere notificar al admin?
  (cita_agendar con datos, transferir)
       │
       ├── Sí → notificar_nueva_cita() / notificar_admin()
       │
       ▼
  Responder al usuario
```

## Intenciones detectadas

| Intención | Disparadores | Handler | Respuesta |
|-----------|-------------|---------|-----------|
| `saludo` | hola, buenos días, qué tal | `_manejar_saludo` | Template bienvenida |
| `informacion` | info, información, qué hacen | `_manejar_informacion_general` | Info general + oferta agendar |
| `horarios` | horario, horarios, atienden | `_manejar_horarios` | Horarios + disponibles + oferta |
| `precios` | precio, precios, cuánto cuesta | `_manejar_precios` | Lista de precios + oferta |
| `ubicacion` | ubicación, dirección, dónde están, lugar | `_manejar_ubicacion` | Dirección del consultorio |
| `cita_agendar` | agendar, cita, reservar cita, + nombre+esp+fecha+hora | `_manejar_agendar_cita` | Prompt de datos o confirmación |
| `cita_consultar` | consultar cita, ver cita, mis citas | `_manejar_consultar_cita` | Listado de citas del teléfono |
| `cita_cancelar` | cancelar, cancelación, cancelar cita | `_manejar_cancelar_cita` | Redirige a admin |
| `reserva_crear` | reservar, apartar, producto | `_manejar_crear_reserva` | Prompt de datos o confirmación |
| `reserva_consultar` | ver reserva, mis reservas | `_manejar_consultar_reserva` | Listado de reservas |
| `contacto` | contacto, teléfono, correo, whatsapp | `_manejar_contacto` | Teléfonos + correo |
| `servicio_especifico` | servicio, especialidad, [nombre servicio] | `_manejar_servicio_especifico` | Info del servicio + oferta |
| `pago` | pago, pagar, formas de pago | `_manejar_pago` | Template pago + transferir |
| `emergencia` | emergencia, urgencia, grave | `_manejar_emergencia` | Mensaje de emergencia |
| `transferir` | hablar con, agente, humano, persona, asesor | `_manejar_transferencia` | Notificar admin + fuera horario |
| `gracias` | gracias, gracias, muchas gracias | `_manejar_gracias` | Agradecimiento |
| `despedida` | adiós, bye, hasta luego, buen día | `_manejar_despedida` | Despedida |
| `faq` | preguntas frecuentes, FAQ, dudas | `_manejar_faq` | Lista de FAQs |
| `fechas_disponibles` | fechas disponibles, días disponibles, qué días | `_manejar_fechas_disponibles` | Días y horarios libres |
| `reportes` | reportes, reporte, estadísticas | `_manejar_reportes` | Reportes (solo admin) |
| `consulta_general` | (fallback) | `_manejar_consulta_general` | Búsqueda en archivos + oferta |

## Multi-intent

Cuando un mensaje contiene 2+ intenciones informativas (ej: "precios y horarios"), el sistema:

1. Detecta todas las intenciones con `detectar_intenciones_multiples()`
2. Ejecuta cada handler por separado, omitiendo la oferta de agendar en cada una
3. Combina las respuestas separadas por `\n\n`
4. Agrega una sola oferta de agendar al final
5. Si el mensaje también implica agendar (ej: "info y agendar cita"), incluye el prompt de agendamiento completo

## Contexto multi-turno

El chatbot mantiene un diccionario `contextos` indexado por número de teléfono:

```python
contextos[numero] = {
    "intencion": "cita_agendar",
    "entidades": {"nombre": "Juan", "especialidad": "Cardiología"},
    "esperando_datos": True,
}
```

- Se guarda cuando el handler responde con `esperando_datos=True`
- Se restaura al inicio del procesamiento del siguiente mensaje
- Las entidades del contexto se fusionan con las nuevas (las nuevas ganan)
- Las intenciones informativas (`INTENCIONES_INFORMATIVAS`) resetean el contexto
- Las intenciones de reseteo (`INTENCIONES_RESET`) también lo limpian

## Comandos admin

El admin puede responder a las notificaciones con:

- `CONFIRMAR F-240614-ABC123` — Confirma la cita, notifica al usuario
- `RECHAZAR F-240614-ABC123` — Rechaza la cita, notifica al usuario con horarios disponibles

Solo el número configurado como `ADMIN_TELEFONO` puede ejecutar estos comandos.
