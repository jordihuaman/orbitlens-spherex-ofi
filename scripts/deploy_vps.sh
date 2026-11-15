#!/usr/bin/env bash
# Despliegue del perfil público en un VPS con Docker + Caddy.
# Uso:
#   ./scripts/deploy_vps.sh --check   # solo valida variables y requisitos
#   ./scripts/deploy_vps.sh           # construye y arranca
#
# No lee ni imprime secretos. El archivo .env.production no se versiona.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ORBITLENS_ENV_FILE:-.env.production}"
CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=1
fi

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

note() {
  printf 'OK: %s\n' "$*"
}

command -v docker >/dev/null 2>&1 || fail "Docker no está instalado"
docker compose version >/dev/null 2>&1 || fail "Falta el plugin 'docker compose'"
command -v curl >/dev/null 2>&1 || fail "Falta curl"

[[ -f "$ENV_FILE" ]] || fail "Falta $ENV_FILE; copia .env.production.example y complétalo"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

for var in \
  ORBITLENS_DOMAIN \
  ORBITLENS_PUBLIC_ORIGIN \
  ORBITLENS_ALLOWED_WEB_HOSTS \
  ORBITLENS_SECURITY_CONTACT \
  ORBITLENS_TRUSTED_PROXIES; do
  [[ -n "${!var:-}" ]] || fail "Falta $var en $ENV_FILE"
done

[[ "$ORBITLENS_DOMAIN" != *example.org* ]] || fail "Sustituye el dominio de ejemplo en $ENV_FILE"
[[ "$ORBITLENS_PUBLIC_ORIGIN" == https://* ]] || fail "ORBITLENS_PUBLIC_ORIGIN debe empezar por https://"
[[ "$ORBITLENS_PUBLIC_ORIGIN" != *"@"* ]] || fail "ORBITLENS_PUBLIC_ORIGIN no debe contener credenciales"
[[ "$ORBITLENS_PUBLIC_ORIGIN" == "https://$ORBITLENS_DOMAIN" ]] || \
  fail "ORBITLENS_PUBLIC_ORIGIN debe ser exactamente https://$ORBITLENS_DOMAIN"
[[ "$ORBITLENS_ALLOWED_WEB_HOSTS" == *"$ORBITLENS_DOMAIN"* ]] || \
  fail "ORBITLENS_ALLOWED_WEB_HOSTS debe incluir $ORBITLENS_DOMAIN"
[[ "$ORBITLENS_SECURITY_CONTACT" == mailto:* || "$ORBITLENS_SECURITY_CONTACT" == https://* ]] || \
  fail "ORBITLENS_SECURITY_CONTACT debe usar mailto: o https:"
[[ "$ORBITLENS_TRUSTED_PROXIES" != *"0.0.0.0/0"* && "$ORBITLENS_TRUSTED_PROXIES" != "*" ]] || \
  fail "ORBITLENS_TRUSTED_PROXIES no puede ser 0.0.0.0/0 ni *"

note "variables de producción válidas para $ORBITLENS_DOMAIN"

if [[ "$CHECK_ONLY" == "1" ]]; then
  exit 0
fi

COMPOSE=(docker compose -f compose.yaml -f compose.production.yaml --env-file "$ENV_FILE")

"${COMPOSE[@]}" config >/dev/null
note "configuración de Compose válida"

"${COMPOSE[@]}" build --pull
"${COMPOSE[@]}" up -d --remove-orphans

printf 'Esperando a que Caddy obtenga el certificado y /api/health responda...\n'
healthy=0
for _ in $(seq 1 60); do
  if curl -fsS --max-time 5 "https://$ORBITLENS_DOMAIN/api/health" >/dev/null 2>&1; then
    healthy=1
    break
  fi
  sleep 5
done

if [[ "$healthy" != "1" ]]; then
  printf '\nNo respondió /api/health. Últimos registros:\n' >&2
  "${COMPOSE[@]}" logs --tail=80 caddy orbitlens >&2 || true
  fail "el despliegue no alcanzó un estado saludable"
fi

note "https://$ORBITLENS_DOMAIN/api/health responde"
"${COMPOSE[@]}" ps
printf '\nSiguiente: ejecutar la lista de aceptación de DEPLOYMENT.md.\n'
