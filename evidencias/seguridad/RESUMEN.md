# Evidencia de seguridad — 2026-11-14

Base: commit `aa594` + árbol de trabajo de este bloque (pipeline 0.1.6). No se ha
publicado un commit con estos cambios al generar esta evidencia.

## Comandos y resultados

| Comando | Resultado |
| --- | --- |
| `pytest` | 215 pruebas pasan |
| `ruff check .` | Sin hallazgos |
| `npm run build --prefix frontend` | Correcto |
| `npm run test:e2e --prefix frontend` | 34/34 pasan (Edge, escritorio y viewport móvil) |
| `pip_audit -r requirements.txt -r requirements-dev.txt --strict` | Sin vulnerabilidades conocidas |
| `bandit -q -r api.py orbitlens scripts -ll` | Sin hallazgos; B104 de `serve.py` documentado con `# nosec` |
| `npm audit --audit-level=high --prefix frontend` | Sin vulnerabilidades |

## Archivos

- `pip-audit-before.json`: informe inicial; 88 avisos duplicados en Pillow,
  Starlette y pytest. Se conserva para no ocultar el estado previo.
- `pip-audit-after.json`: informe tras actualizar FastAPI 0.163.0, Starlette
  1.10.0, Pillow 13.0.0 y pytest 9.2.0.
- `bandit-after.json`: análisis estático final.
- `npm-audit.json`: auditoría de dependencias del frontend.

## Límites

Estos resultados son locales. No sustituyen el CI remoto, una auditoría externa,
un pentest, SSL Labs, ZAP, Mozilla Observatory ni una prueba en el host público.
El Dockerfile/Compose no se construyó aquí porque Docker no está instalado.
Ver `../../SEGURIDAD.md` para riesgos residuales y checklist.
