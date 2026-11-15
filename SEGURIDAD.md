# Seguridad y exposición pública — OrbitLens SPHEREx

Revisión: **2026-11-14**, pipeline **0.1.6**. Este documento describe controles
verificables en el código y en la configuración de despliegue. **No es una
certificación**: no sustituye una auditoría externa, un pentest, un SOC, un WAF
gestionado ni el cumplimiento legal de una jurisdicción concreta. Tampoco se ha
desplegado una URL pública desde esta máquina.

## 1. Alcance y activos

| Activo | Riesgo principal |
| --- | --- |
| Disponibilidad del servicio | Agotamiento de CPU/disco/cola, descargas amplificadas, DDoS |
| Reputación y cuota de IRSA | Consultas abusivas o reintentos descontrolados |
| Integridad de resultados | FITS/manifiestos manipulados, rutas fuera del directorio, caché corrupta |
| Host y red interna | SSRF, redirecciones a metadata/red privada, fuga de rutas |
| Navegador del visitante | XSS, clickjacking, inyección de HTML, mixed content |
| Cadena de suministro | Dependencias vulnerables o imágenes sin actualizar |
| Privacidad | IPs, logs, retención; no hay cuentas ni datos personales declarados |

No hay autenticación, cookies, pagos ni formularios con datos personales. Los
resultados publicados son públicos por ID; no se deben subir datos privados.

## 2. Modelo de amenazas resumido

- **Escáner/bot oportunista:** busca paneles, `.env`, `.git`, Swagger, errores
  verbosos, cabeceras débiles y endpoints sin límites.
- **Usuario malicioso:** intenta SSRF hacia la red interna, inyección de HTML,
  CSRF, cuerpos gigantes, consultas costosas o muchas cuentas/IPs.
- **FITS hostil:** dimensiones/heap excesivos, gzip bomb, HDU inesperadas,
  cabeceras WCS falsas o rutas manipuladas en manifiestos.
- **Fallo de dependencia:** vulnerabilidad conocida en FastAPI/Starlette/Pillow,
  npm o imagen base.
- **Abuso de recursos:** trabajos simultáneos, descargas grandes, polling,
  almacenamiento lleno.
- **Error operativo:** proxy mal configurado que confía en `X-Forwarded-For`,
  TLS ausente, volumen sin respaldo, logs con IPs o secretos.

## 3. Controles implementados

| Área | Control | Dónde |
| --- | --- | --- |
| Transporte | HTTPS obligatorio en perfil de producción; HTTP→HTTPS en el proxy; HSTS de 1 año | `orbitlens/security.py`, `deploy/` |
| Cabeceras | CSP estricta sin `unsafe-inline`, `nosniff`, `DENY`, `no-referrer`, Permissions-Policy, COOP/CORP, `X-Permitted-Cross-Domain-Policies` | `security_headers()` |
| Host | Allowlist exacta de `Host`, rechazo de duplicados, credenciales, rutas y puertos inválidos | `SecurityMiddleware` |
| Entrada | Pydantic estricto, campos extra prohibidos, límites de longitud/rango, rechazo de booleanos donde se espera número | `orbitlens/api_models.py` |
| Cuerpo HTTP | `application/json` obligatorio, sin `Content-Encoding`, máximo 16 KiB, timeout de recepción, rechazo de `Content-Length`+`Transfer-Encoding` | `SecurityMiddleware` |
| CSRF | Sin cookies; POST con `Origin`/`Sec-Fetch-Site` validados contra el origen público | `SecurityMiddleware` |
| Cuotas | Token bucket por IP (600/min, ráfaga 120), cupo de trabajos por IP y global, `Retry-After` | `RequestLimiter`, `jobs.py` |
| SSRF | Solo HTTPS, host exacto, puerto 443, sin credenciales/fragmentos; sin redirects automáticos | `orbitlens/network_policy.py` |
| FITS | Límite de HDU, ejes, píxeles, bytes y heap **antes** de materializar; rechazo de `.gz` completo; validación MEF/WCS/detector/tiempo | `orbitlens/pipeline.py` |
| Archivos | IDs hexadecimales, contención de rutas, rechazo de symlinks, SHA-256 y tamaño antes de servir | `api.py`, `manifest.py` |
| Errores | Mensajes públicos genéricos, `request_id`, sin traceback/rutas/URLs internas al cliente | `orbitlens/public_errors.py`, `api.py` |
| Logs | JSON con método/ruta/estado/duración/`request_id`; **sin IP, query ni cabeceras**; acceso Uvicorn desactivado | `security.py`, `scripts/serve.py` |
| Dependencias | Versiones fijadas, `pip-audit`, Bandit, `npm audit`, Dependabot | `requirements*.txt`, CI |
| Contenedor | Usuario no root, root filesystem de solo lectura, `tmpfs`, `cap_drop: ALL`, `no-new-privileges`, límites de PID/memoria/CPU, volumen persistente | `Dockerfile`, `compose*.yaml` |
| Proxy | TLS, límite de cuerpo, timeouts, ocultación de `Server`, reescritura de `X-Forwarded-For` | `deploy/Caddyfile`, `deploy/nginx.conf` |
| Divulgación | `/.well-known/security.txt` solo si hay contacto configurado; sin inventar buzón | `api.py` |
| Accesibilidad | Enlace de salto, foco visible, `prefers-reduced-motion`, auditoría axe WCAG 2.x A/AA en E2E | `frontend/` |
| Privacidad | Sin cookies/analytics/cuentas; IP solo en memoria y hasheada para cuotas | `RequestLimiter` |

## 4. Correspondencia con estándares (parcial, no certificada)

| Referencia | Cobertura en este repositorio | Límite |
| --- | --- | --- |
| OWASP Top 10 2021 | A01 control de acceso por IDs y rutas; A03 inyección/validación; A04 diseño seguro y cuotas; A05 configuración; A06 dependencias; A08 integridad; A09 logging; A10 SSRF | No cubre A02 criptografía de datos en reposo (no hay datos personales) ni A07 autenticación (no existe login) |
| OWASP ASVS 5.0, nivel 2 (subconjunto) | V1 codificación, V2 validación, V4 control de acceso a archivos, V5 archivos, V6 HTTP, V7 errores/logs, V8 protección de datos, V9 comunicaciones, V12 recursos, V13 API, V14 configuración | Faltan verificación externa, pruebas de penetración y varios controles organizativos |
| RFC 9116 `security.txt` | Ruta y formato, `Expires`, `Canonical`, contacto configurable | Falta publicar un buzón real y revisar caducidad |
| RFC 6797 HSTS | `max-age=31536000` en producción | No se ha enviado a la lista de precarga; no se usa `includeSubDomains` |
| WCAG 2.2 AA | axe automatizado en escritorio y viewport móvil; teclado y foco | axe cubre un subconjunto; falta auditoría manual con lectores de pantalla |
| CIS Docker Benchmark (esencial) | No root, solo lectura, capabilities mínimas, límites, healthcheck | No se ha ejecutado `docker-bench-security` porque Docker no está instalado aquí |

## 5. Evidencia ejecutada en esta copia

| Comprobación | Resultado |
| --- | --- |
| `pytest` | **215 pruebas pasan** |
| Playwright/Edge (escritorio y viewport móvil) | **34 casos pasan**, incluidos axe y CSP |
| `ruff check .` | Sin hallazgos |
| `npm run build` | Correcto (`tsc --noEmit && vite build`) |
| `pip-audit -r requirements.txt -r requirements-dev.txt --strict` | **0 vulnerabilidades conocidas** |
| `bandit -q -r api.py orbitlens scripts -ll` | **0 hallazgos** (B104 de escucha en contenedor documentado con `# nosec`) |
| `npm audit --audit-level=high` | **0 vulnerabilidades** |
| Revisión inicial de dependencias | **88 avisos** en Pillow/Starlette/pytest; corregidos actualizando versiones |

Los informes están en `evidencias/seguridad/`. Antes de la actualización se
detectaron 88 avisos duplicados en 3 paquetes; no se ocultaron. Las versiones
actuales son FastAPI 0.163.0, Starlette 1.10.0, Pillow 13.0.0 y pytest 9.2.0.

## 6. Riesgos residuales y controles que faltan

1. **Sin auditoría externa ni pentest.** Este documento no acredita seguridad
   ante terceros. Antes de anunciar la web, ejecutar al menos OWASP ZAP baseline,
   SSL Labs y Mozilla Observatory, y guardar los informes.
2. **Sin WAF/CDN/anti-DDoS.** El límite por IP es de aplicación, en memoria y por
   proceso; se reinicia con el servicio. Un ataque distribuido puede agotar CPU,
   disco o la cuota de IRSA. Para exposición internacional se recomienda un proxy
   gestionado con rate limiting y scrubbing.
3. **Un solo proceso.** La cola, cuotas y locks no se comparten entre réplicas.
   No habilitar autoscaling ni varios workers sin rediseñar el estado.
4. **Sin monitorización/SIEM/on-call.** Hay logs estructurados y `/api/health`,
   pero no alertas, trazas, retención legal ni respuesta 24/7.
5. **Sin gestor de secretos.** No hay secretos en el repositorio; el contacto y
   el dominio van por entorno. Si se añaden credenciales, usar un gestor.
6. **Sin firma de imágenes ni SBOM publicado.** Dependabot y auditorías cubren
   detección; falta firmar (cosign), generar SBOM y aplicar política de admisión.
7. **HSTS no precargado y sin `includeSubDomains`.** Activarlo solo cuando todos
   los subdominios sean HTTPS; enviar a `hstspreload.org` es una decisión aparte.
8. **Logs del proxy.** Caddy/Nginx pueden registrar IPs. Configurar retención,
   acceso restringido y base legal; la aplicación no las guarda.
9. **Sin CSP de reporte.** La CSP bloquea, pero no recibe informes. Añadir
   `report-to` requiere un endpoint y privacidad adicional.
10. **Sin prueba en teléfono físico ni red externa.** El viewport móvil de
    Playwright no sustituye un dispositivo real.
11. **Docker no construido en esta máquina.** El Dockerfile y Compose están
    preparados y revisados, pero la construcción/ejecución debe verificarse en el
    host. No se declara que funcionen hasta hacerlo.
12. **Disponibilidad de IRSA.** Un fallo de IRSA no prueba ausencia de cobertura;
    los estados `partial`/`error` deben mostrarse sin convertirlos en `empty`.

## 7. Respuesta a incidentes

1. **Contener:** retirar el servicio del proxy o bloquear la IP/ruta afectada;
   conservar logs y el volumen de datos; no borrar evidencia.
2. **Evaluar:** identificar versión/commit (`/api/health`), `request_id`, rutas,
   hora y alcance; comprobar integridad de resultados y dependencias.
3. **Erradicar:** actualizar la dependencia/imagen, rotar credenciales del host
   (no hay credenciales de aplicación), reconstruir desde un commit limpio.
4. **Recuperar:** restaurar el volumen desde respaldo verificado; validar
   `/api/health`, búsqueda, reinicio y artefactos antes de reabrir.
5. **Notificar:** usar el contacto de `security.txt`; informar a usuarios y a
   IRSA si se afectó su servicio; publicar un aviso con hechos confirmados.
6. **Aprender:** añadir una prueba de regresión y actualizar este documento.

No se ofrece bug bounty ni recompensa económica. Se pide divulgación coordinada,
sin acceso destructivo, sin datos de terceros y con un plazo razonable antes de
publicar.

## 8. Privacidad y retención

- No hay cuentas, cookies, analítica ni píxeles de seguimiento.
- La IP se usa solo para cuotas, en memoria, hasheada con SHA-256; no se escribe
  en disco ni se devuelve en la API.
- Los logs de la aplicación no incluyen IP, query ni cabeceras. El proxy puede
  registrarlas; configurar rotación y acceso restringido.
- Los FITS y metadatos provienen de IRSA y son públicos. No subir datos privados.
- Los resultados no expiran automáticamente. Un ID ausente responde 404; no hay
  tombstones/410. El operador debe definir retención y respaldo antes de borrar.

## 9. Lista de verificación antes de publicar

- [ ] Dominio y DNS apuntando al host; certificado TLS válido y renovación automática.
- [ ] Solo 80/443 expuestos; backend en `127.0.0.1` o red interna sin acceso público.
- [ ] `ORBITLENS_PRODUCTION=true`, `ORBITLENS_PUBLIC_ORIGIN` HTTPS y host en `ORBITLENS_ALLOWED_WEB_HOSTS`.
- [ ] `ORBITLENS_TRUSTED_PROXIES` con la red/IP exacta del proxy; nunca `*` ni `0.0.0.0/0`.
- [ ] `ORBITLENS_SECURITY_CONTACT` real y `/.well-known/security.txt` responde 200.
- [ ] Documentación interactiva desactivada (`ORBITLENS_ENABLE_DOCS=false`).
- [ ] Volumen persistente con permisos mínimos, respaldo y restauración probada.
- [ ] Contenedor no root, solo lectura, capabilities mínimas y límites de recursos.
- [ ] Logs sin secretos, con rotación y retención definida.
- [ ] `pytest`, E2E, Ruff, build, `pip-audit`, Bandit y `npm audit` en verde.
- [ ] Escaneo externo (ZAP/SSL Labs/Observatory) y revisión manual de accesibilidad.
- [ ] Búsqueda real, reinicio, cuotas/proxy y teléfono físico verificados.
- [ ] Plan de rollback y contacto de incidentes disponibles.

## 10. Reproducir las comprobaciones

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt -r requirements-dev.txt --strict
.\.venv\Scripts\python.exe -m bandit -q -r api.py orbitlens scripts -ll
npm --prefix frontend run build
npm --prefix frontend run test:e2e
npm audit --audit-level=high --prefix frontend
```

Los resultados locales no acreditan el CI remoto ni el host. El CI incluye un
trabajo `security` separado; su ejecución debe comprobarse tras publicar el commit.
