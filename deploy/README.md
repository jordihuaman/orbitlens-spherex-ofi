# Despliegue público de referencia

Estos archivos son plantillas. **No se han construido ni desplegado desde esta
máquina** (Docker no está instalado aquí). Verificar en el host antes de anunciar
una URL.

## Opción recomendada: Compose + Caddy (TLS automático)

1. Tener un dominio con DNS tipo A/AAAA al host y puertos 80/443 abiertos.
2. Copiar `.env.production.example` a `.env.production` y completar dominio,
   origen, hosts, red del proxy y contacto. No versionar ese archivo.
3. Revisar `compose.yaml` y `compose.production.yaml`. El backend no se publica
   fuera de `127.0.0.1`; Caddy es el único servicio con 80/443.
4. Construir y arrancar:

   ```bash
   docker compose -f compose.yaml -f compose.production.yaml \
     --env-file .env.production up -d --build
   ```

5. Comprobar:

   ```bash
   curl -fsS https://TU_DOMINIO/api/health
   curl -fsSI https://TU_DOMINIO/ | sed -n '1,30p'
   curl -fsS https://TU_DOMINIO/.well-known/security.txt
   ```

6. Ejecutar una búsqueda real, reiniciar el contenedor y reabrir el resultado.
7. Probar desde un teléfono físico y una red externa.

Caddy obtiene y renueva el certificado. El volumen `caddy-data` debe conservarse.
El volumen `orbitlens-data` contiene resultados, trabajos y caché: respaldarlo y
probar la restauración. No ejecutar `docker compose down -v` salvo decisión
explícita de borrar datos.

## Opción Nginx

Usar `deploy/nginx.conf` como base dentro del contexto `http {}`. Sustituir
dominio, rutas de certificados y `proxy_pass` si el backend no está en
`127.0.0.1:8000`. El backend debe escuchar solo en loopback o en una red interna.
Configurar `ORBITLENS_TRUSTED_PROXIES` con la IP/CIDR exacta de Nginx.

## Variables imprescindibles

| Variable | Valor |
| --- | --- |
| `ORBITLENS_PRODUCTION` | `true` |
| `ORBITLENS_PUBLIC_ORIGIN` | `https://dominio` (sin ruta) |
| `ORBITLENS_ALLOWED_WEB_HOSTS` | dominio y, si aplica, `localhost` |
| `ORBITLENS_TRUSTED_PROXIES` | red/IP del proxy, nunca `*` |
| `ORBITLENS_SECURITY_CONTACT` | `mailto:` o `https://` real |
| `ORBITLENS_ENABLE_DOCS` | `false` |
| `ORBITLENS_DATA_DIR` | volumen persistente (`/app/data`) |

Si `ORBITLENS_PRODUCTION=true` y falta el origen HTTPS, la allowlist o el contacto
válido, la aplicación **falla al arrancar** en lugar de quedar abierta.

## Endurecimiento del contenedor

`compose.yaml` ya aplica: usuario no root, root filesystem de solo lectura,
`/tmp` en `tmpfs`, `cap_drop: ALL`, `no-new-privileges`, límites de PID/memoria/
CPU, healthcheck y rotación de logs. No añadir `privileged`, `network_mode: host`
ni montar el socket de Docker.

## Límites que siguen siendo del operador

- Firewall: solo 80/443; SSH restringido; sin base de datos ni backend expuestos.
- WAF/CDN/anti-DDoS si la exposición es internacional.
- Monitorización, alertas, retención de logs y respuesta a incidentes.
- Respaldos cifrados y restauración probada.
- Escaneo externo (ZAP baseline, SSL Labs, Mozilla Observatory) y revisión manual
  de accesibilidad; ver `SEGURIDAD.md`.
- Un solo proceso propietario del directorio de datos. No autoscaling ni varios
  workers: cola, cuotas y locks no se comparten.
