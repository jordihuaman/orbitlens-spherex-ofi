#!/usr/bin/env bash
# Respaldo comprimido del volumen de datos de OrbitLens.
# Uso: ./scripts/backup_volume.sh [directorio-destino]
# No detiene el servicio; el tar se hace en modo lectura.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

command -v docker >/dev/null 2>&1 || {
  printf 'ERROR: Docker no está instalado\n' >&2
  exit 1
}

VOLUME="$(docker volume ls \
  --filter label=com.docker.compose.volume=orbitlens-data \
  --format '{{.Name}}' | head -n 1)"

if [[ -z "$VOLUME" ]]; then
  printf 'ERROR: no se encontró el volumen orbitlens-data\n' >&2
  exit 1
fi

mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
ARCHIVE="$DEST/orbitlens-data-$STAMP.tar.gz"

docker run --rm \
  -v "$VOLUME":/data:ro \
  -v "$DEST":/backup \
  alpine:3.21 \
  sh -c "tar czf /backup/$(basename "$ARCHIVE") -C /data ."

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$ARCHIVE" | tee "$ARCHIVE.sha256"
else
  shasum -a 256 "$ARCHIVE" | tee "$ARCHIVE.sha256"
fi

printf 'Respaldo creado: %s\n' "$ARCHIVE"
printf 'Copia el archivo fuera del VPS y prueba una restauración antes de confiar en él.\n'
