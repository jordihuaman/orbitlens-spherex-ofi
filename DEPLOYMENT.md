# Despliegue reproducible — no es una URL pública ya desplegada

## Requisitos y estado

- Un único proceso/instancia por directorio de datos. Cola, locks y cuotas se
  comparten entre hilos, no entre máquinas. No habilitar autoscaling ni varios workers.
- Python 3.12, Node 22 para construir, disco persistente >=3 GiB; se necesita salida
  HTTPS a IRSA. `data/` contiene resultados y snapshots de trabajos.
- Esta máquina no tiene Docker ni CLI de hosting instalados. El Dockerfile/Compose
  están preparados, **no construidos ni desplegados aquí**. No hay credenciales de
  hosting confirmadas ni URL pública de este commit. No se contratan servicios.
- Controles y riesgos residuales: [SEGURIDAD.md](SEGURIDAD.md). Plantillas de
  proxy/contenedor: [deploy/README.md](deploy/README.md).

## Opción A: Python, sin Docker

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
$env:ORBITLENS_CODE_COMMIT = git rev-parse HEAD
$env:ORBITLENS_DATA_DIR = 'D:\orbitlens-data'
$env:PORT = '8000'
.\.venv\Scripts\python.exe scripts\serve.py
```

En un host Linux usar su venv equivalente y un gestor de servicios. `serve.py`
desactiva la interpretación automática de cabeceras proxy de Uvicorn: la
aplicación valida por sí misma la cadena X-Forwarded-For. Sin proxy confiable,
la cabecera enviada por un visitante no altera su cuota.

## Opción B: contenedor no privilegiado

```powershell
$env:ORBITLENS_CODE_COMMIT = git rev-parse HEAD
docker compose build
docker compose up -d
```

Solo expone `127.0.0.1:8000`; poner un reverse proxy TLS delante. El volumen
con nombre conserva resultados/trabajos tras recrear el contenedor.
No ejecutar `docker compose down -v` salvo decisión explícita de borrar datos.

## Opción C: perfil público con Caddy

Copiar `.env.production.example` a `.env.production`, completar los valores y
arrancar el perfil que termina TLS:

```bash
docker compose -f compose.yaml -f compose.production.yaml \
  --env-file .env.production up -d --build
```

Caddy obtiene el certificado, redirige HTTP a HTTPS y reescribe
`X-Forwarded-For` con la IP directa. El backend sigue sin publicarse fuera de la
red interna. Guardar los volúmenes `orbitlens-data`, `caddy-data` y
`caddy-config`. Alternativa Nginx en `deploy/nginx.conf`.

### Variables que fallan cerrado

Con `ORBITLENS_PRODUCTION=true` la aplicación exige:

- `ORBITLENS_PUBLIC_ORIGIN` HTTPS, sin ruta ni credenciales.
- El host de ese origen dentro de `ORBITLENS_ALLOWED_WEB_HOSTS`.
- `ORBITLENS_ENABLE_DOCS=false`.
- `ORBITLENS_TRUSTED_PROXIES` con IP/CIDR concretos si hay proxy.
- `ORBITLENS_SECURITY_CONTACT` con `mailto:` o `https:` si se publica
  `/.well-known/security.txt`.

Si falta algo, el arranque falla en vez de quedar expuesto. `ORBITLENS_CORS_ORIGINS`
vacío en producción: el frontend se sirve desde el mismo origen.

## Proxy y seguridad

Configurar `ORBITLENS_TRUSTED_PROXIES` con IP/CIDR **del proxy real**, nunca `*`
ni redes amplias accesibles por visitantes. Por defecto está vacío. Ejemplo
Nginx en la misma máquina, con backend no accesible desde Internet:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_read_timeout 650s;
    client_max_body_size 16k;
}
```

En ese ejemplo, permitir solo `127.0.0.1/32,::1/128`. La búsqueda devuelve 202
rápidamente; el polling no necesita un timeout HTTP de diez minutos. Las cuotas
son 2 trabajos nuevos activos por IP y 10/minuto; deduplicación y lectura de
resultados no consumen búsqueda pesada. El historial de cuotas es de proceso y
se reinicia al reiniciar el servicio; no se persisten IPs.

La aplicación ya añade CSP, `nosniff`, `DENY`, `no-referrer`, Permissions-Policy,
COOP/CORP y HSTS en producción. El proxy de referencia limita el cuerpo a 16 KiB,
oculta `Server` y aplica timeouts. No confiar en cabeceras del visitante para TLS
ni para la IP: solo el proxy autorizado puede afirmarlas.

## Tiempo, disco y reinicios

- Presupuesto temporal cooperativo de 600 s desde ejecución (no desde cola).
  Cada operación HTTP y espera se limita al restante; streams comprueban entre
  chunks y etapas de procesamiento comprueban antes/después. No hay cancelación
  forzada dentro de un cálculo Astropy/reproject en curso. El apagado espera a
  trabajos en ejecución y cancela los que aún están en cola.
- LRU conservador de entradas `data/cache/sia` y `data/cache/cutout`, solo sin
  constructores activos. Presupuesto blando de 2 GiB y reserva libre de 64 MiB.
  Resultados publicados y archivos manuales **no se expulsan**; si ocupan el
  presupuesto, se bloquea trabajo nuevo y se requiere mantenimiento/ampliación.
  La suma se verifica entre chunks, no es una reserva transaccional de filesystem.
- `data/jobs/*.json` persiste cada cambio. Al arrancar, trabajos incompletos
  pasan a error recuperable; resultados existentes siguen por su ID tras
  validación de integridad. Respaldar resultados, jobs e índices del operador.
- No hay expiración automática de resultados; por eso IDs ausentes responden
  404, no 410. Implementar tombstones antes de habilitar una política de borrado.

## Operación y mantenimiento

- `/api/health` informa versión, commit, colecciones y trabajos activos. No
  sustituye monitorización: añadir alertas de disponibilidad, errores 5xx, disco,
  latencia y saturación de cola.
- Logs JSON de la aplicación sin IP/query/cabeceras. El proxy puede registrar IPs:
  definir retención, acceso y base legal. Rotar logs y no incluir secretos.
- Respaldos cifrados del volumen de datos y prueba de restauración. Sin respaldo
  verificado no se puede prometer recuperación.
- Actualizar dependencias con Dependabot y ejecutar `pip-audit`, Bandit y
  `npm audit` antes de cada despliegue. Reconstruir la imagen; no parchear dentro
  del contenedor.
- Un solo propietario del directorio de datos. Reiniciar es seguro para trabajos
  ya publicados, pero no para cálculos en curso: se recuperan como error.

## Aceptación antes de anunciar una URL

1. Registrar commit y comprobar `/api/health` y activos estáticos.
2. Ejecutar una búsqueda real desde formulario; verificar estado y metadatos.
3. Reiniciar y volver a abrir su resultado; comprobar estado del trabajo.
4. Probar cuotas con IP real y cabeceras falsificadas desde fuera del proxy.
5. Abrir desde teléfono físico y red externa; anotar dispositivo/fecha/URL.
6. Verificar HTTPS, HSTS, CSP, `/.well-known/security.txt` y ausencia de `/docs`,
   `/openapi.json`, `.env` y `.git`.
7. Ejecutar ZAP baseline, SSL Labs y Mozilla Observatory; guardar informes y
   corregir hallazgos. Revisar accesibilidad manualmente además de axe.
8. Confirmar respaldo/restauración y plan de rollback.

El CI añadido prueba fixtures sin IRSA y un trabajo de seguridad separado. No
acredita disponibilidad pública, datos científicos, el resultado de la
construcción Docker en esta máquina ni una auditoría externa.
