# Problemas de Railway y Soluciones

## 1. `$PORT` no se expande en el startCommand

### Problema
Railway ejecuta el `startCommand` del servicio en **exec form** (sin shell), por lo que `$PORT` se pasa literal como string. Gunicorn falla con:
```
Error: '$PORT' is not a valid port number.
```

El `startCommand` estaba configurado a nivel de servicio (`gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -`) e ignoraba el `CMD` del Dockerfile y el `Procfile`.

### Solución
1. Cambiar el `startCommand` del servicio a `python run.py` usando la GraphQL API de Railway.
2. `run.py` lee `PORT` como variable de entorno con fallback a `5000` y ejecuta gunicorn correctamente.

### Código relevante
- `run.py`: entrypoint Python que maneja `PORT`
- `.railway/update.mjs`: script que usa `IacClient` para actualizar el startCommand vía API

---

## 2. `DATABASE_URL` contiene solo host:port (TCP Proxy)

### Problema
Railway conectó el servicio PostgreSQL del proyecto `truthful-youth` al proyecto `charming-growth` mediante un **TCP Proxy**. La variable `DATABASE_URL` que Railway inyecta automáticamente es solo `acela.proxy.rlwy.net:31193` (host:port), no una URL de conexión completa.

psycopg2 falla con:
```
invalid dsn: missing "=" after "acela.proxy.rlwy.net:31193" in connection info string
```

Railway bloquea modificar variables con nombres reservados (`DATABASE_URL`, `PGPASSWORD`, etc.).

### Solución
1. Agregar `_build_pg_dsn()` en `database/agenda_db.py` que construye la URL completa desde `host:port` si el formato no tiene `://`.
2. Crear variable `CUSTOM_DB_URL` en Railway con la conexión PostgreSQL completa (`postgresql://postgres:password@acela.proxy.rlwy.net:31193/railway`).
3. El código prioriza `CUSTOM_DB_URL` sobre `DATABASE_URL`.

### Código relevante
- `database/agenda_db.py`: función `_build_pg_dsn()` y cambio de `DATABASE_URL` a `os.getenv("CUSTOM_DB_URL") or os.getenv("DATABASE_URL", "")`
