# Política de seguridad / Security policy

## Reportar una vulnerabilidad

No publiques detalles explotables en un issue público. Usa, en este orden:

1. **GitHub Security Advisories** del repositorio, si el mantenedor ha habilitado
   la divulgación privada.
2. El contacto configurado por el operador en `ORBITLENS_SECURITY_CONTACT` y
   publicado en `/.well-known/security.txt` de la instancia desplegada.

Este repositorio **no incluye un buzón de seguridad activo** ni promete un SLA.
No se debe inventar ni usar una dirección de ejemplo para reportar incidentes
reales.

Incluye: versión/commit (`/api/health`), `X-Request-ID` si existe, URL afectada,
pasos mínimos, impacto y si hay datos de terceros. No accedas a datos ajenos, no
hagas pruebas destructivas y no interrumpas el servicio.

## Alcance

- Backend FastAPI, pipeline FITS/WCS, cola, caché y API.
- Frontend React/Vite y cabeceras HTTP.
- Contenedor, Compose, proxy de referencia y configuración de despliegue.
- Dependencias y cadena de suministro.

Quedan fuera: IRSA/NASA, SIMBAD, WiseView, Gaia y cualquier servicio externo. Los
fallos de disponibilidad de IRSA no son vulnerabilidades de OrbitLens; un fallo
de descarga tampoco prueba ausencia de cobertura.

## Divulgación coordinada

Se pide un plazo razonable antes de publicar. No hay bug bounty ni compensación
económica. Se acreditará la divulgación si la persona lo solicita y acepta.

## Documentación ampliada

Controles, modelo de amenazas, límites, riesgos residuales y lista de verificación
antes de publicar: [SEGURIDAD.md](SEGURIDAD.md). Despliegue: [DEPLOYMENT.md](DEPLOYMENT.md).
