# Despliegue reproducible — no es una URL pública ya desplegada

## Requisitos y estado

- Un único proceso/instancia por directorio de datos. Cola, locks y cuotas se
  comparten entre hilos, no entre máquinas. No habilitar autoscaling/múltiples workers.
- Python 3.12, Node 22 para construir, disco persistente >=3 GiB; se necesita salida
  HTTPS a IRSA. `data/` contiene resultados y snapshots de trabajos.
- Esta máquina no tiene Docker ni CLI de hosting instalados. El Dockerfile/Compose
  están preparados, **no construidos ni desplegados aquí**. No hay credenciales de
  hosting confirmadas ni URL pública de este commit. No se contratan servicios.

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

## Proxy y seguridad

Configurar `ORBITLENS_TRUSTED_PROXIES` con IP/CIDR **del proxy real**, nunca `*`
ni redes amplias accesibles por visitantes. Por defecto está vacío. Ejemplo
Nginx en la misma máquina, con backend no accesible desde Internet:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_read_timeout 30s;
    client_max_body_size 16k;
}
```

En ese ejemplo, permitir solo `127.0.0.1/32,::1/128`. La búsqueda devuelve 202
rápidamente; el polling no necesita un timeout HTTP de diez minutos. Las cuotas
son 2 trabajos nuevos activos por IP y 10/minuto; deduplicación y lectura de
resultados no consumen búsqueda pesada. El historial de cuotas es de proceso y
se reinicia al reiniciar el servicio; no se persisten IPs.

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

## Aceptación antes de anunciar una URL

1. Registrar commit y comprobar `/api/health` y activos estáticos.
2. Ejecutar una búsqueda real desde formulario; verificar estado y metadatos.
3. Reiniciar y volver a abrir su resultado; comprobar estado del trabajo.
4. Probar cuotas con IP real y cabeceras falsificadas desde fuera del proxy.
5. Abrir desde teléfono físico y red externa; anotar dispositivo/fecha/URL.

El CI añadido prueba fixtures sin IRSA. No acredita disponibilidad pública,
datos científicos ni el resultado de la construcción Docker en esta máquina.
