# Personalización del Negocio

## Archivos de datos (`datos/`)

| Archivo | Contenido | Formato |
|---------|-----------|---------|
| `empresa.txt` | Nombre, tipo, eslogan | `CLAVE: valor` |
| `servicios.txt` | Lista de servicios con descripciones | Secciones separadas por `\n\n` |
| `precios.txt` | Lista de precios | `Servicio: $Precio MXN` |
| `horarios.txt` | Horarios de atención | Texto libre |
| `horarios_disponibles.txt` | Slots disponibles para citas | Secciones por día |
| `direccion.txt` | Dirección del local | Texto libre |
| `telefonos.txt` | Teléfonos de contacto | `Etiqueta: número` |
| `correo.txt` | Correos electrónicos | Texto libre |
| `productos.txt` | Productos para reserva | Secciones separadas por `\n\n` |
| `preguntas_frecuentes.txt` | FAQ | Secciones con `=== Pregunta ===` |
| `informacion.txt` | Misión, visión, valores | Texto libre |

### Ejemplo de `servicios.txt`

```
Servicio: Medicina General
Descripción: Consulta general de medicina interna.
Duración: 30 minutos
Precio: $500 MXN

Servicio: Pediatría
Descripción: Atención pediátrica para niños de 0 a 12 años.
Duración: 40 minutos
Precio: $600 MXN
```

### Ejemplo de `horarios_disponibles.txt`

```
=== Lunes a Viernes ===
9:00 AM
10:00 AM
11:00 AM
12:00 PM
2:00 PM
3:00 PM
4:00 PM
5:00 PM

=== Sábados ===
9:00 AM
10:00 AM
11:00 AM
12:00 PM
1:00 PM
```

## Archivos de mensajes (`mensajes/`)

| Archivo | Uso | Variables disponibles |
|---------|-----|----------------------|
| `bienvenida.txt` | Saludo inicial | `{{NOMBRE_EMPRESA}}`, `{{ESLOGAN}}` |
| `transferencia.txt` | Transferir a admin | `{{TELEFONO}}`, `{{TELEFONO_PRINCIPAL}}` |
| `sin_respuesta.txt` | No entendido | — |
| `reserva_exitosa.txt` | Confirmación reserva | `{{PRODUCTO}}`, `{{CANTIDAD}}`, `{{NOMBRE}}`, `{{TELEFONO}}`, `{{FOLIO}}` |
| `pago.txt` | Info de pago | — |
| `fuera_horario.txt` | Fuera de horario laboral | `{{HORARIOS}}` |
| `espera_confirmacion.txt` | Cita pendiente de confirmación | `{{ESPECIALIDAD}}`, `{{FECHA}}`, `{{HORA}}`, `{{NOMBRE}}`, `{{FOLIO}}` |
| `error_formato.txt` | Error en datos de cita | — |
| `cancelacion.txt` | Confirmación cancelación | `{{FOLIO_CANCELACION}}` |
| `mensaje_admin.txt` | Plantilla para notificar al admin | `{{NOMBRE_CLIENTE}}`, `{{TELEFONO_CLIENTE}}`, `{{MENSAJE_CLIENTE}}`, `{{FECHA}}`, `{{HORA}}` |

## Variables disponibles en templates

| Variable | Fuente |
|----------|--------|
| `{{NOMBRE_EMPRESA}}` | `config/empresa.txt` → `NOMBRE` |
| `{{ESLOGAN}}` | `config/empresa.txt` → `ESLOGAN` |
| `{{HORARIOS}}` | `datos/horarios.txt` |
| `{{TELEFONO}}` | Variable del contexto |
| `{{TELEFONO_PRINCIPAL}}` | `datos/telefonos.txt` → línea con "Principal" o "WhatsApp" |
| `{{NOMBRE}}` | Entidad extraída del mensaje |
| `{{ESPECIALIDAD}}` | Entidad extraída del mensaje |
| `{{FECHA}}` | Entidad extraída del mensaje |
| `{{HORA}}` | Entidad extraída del mensaje |
| `{{PRODUCTO}}` | Entidad extraída del mensaje |
| `{{CANTIDAD}}` | Entidad extraída (default: 1) |
| `{{FOLIO}}` | Generado por BD |
| `{{FOLIO_CANCELACION}}` | Folio de la cita a cancelar |
| `{{NOMBRE_CLIENTE}}` | Cliente que solicita transferencia |
| `{{TELEFONO_CLIENTE}}` | Teléfono del cliente |
| `{{MENSAJE_CLIENTE}}` | Mensaje original del cliente |

## Configuración general (`config/settings.json`)

```json
{
  "zona_horaria": "America/Mexico_City",
  "formato_fecha": "dd/mm/yyyy",
  "formato_hora": "HH:MM",
  "moneda": "MXN",
  "idioma": "es",
  "max_intentos_ia": 3,
  "tiempo_espera_minutos": 30,
  "dias_anticipacion_max": 30,
  "permitir_cancelar": true
}
```

## WhatsApp Cloud API

### Obtener token permanente

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Crea/abre tu app de Facebook
3. Agrega producto **WhatsApp** → **Business Platform**
4. Ve a **System Users** → **Add System User**
5. Asigna permiso `whatsapp_business_messaging` y `whatsapp_business_management`
6. Genera token permanente
7. Copia el token a `WHATSAPP_TOKEN`

### Configurar webhook

- **Callback URL:** `https://tu-dominio.railway.app/webhook`
- **Verify token:** El mismo que `WHATSAPP_VERIFY_TOKEN`
- **Suscripciones:** `messages`, `message_deliveries`
