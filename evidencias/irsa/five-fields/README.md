# Cinco campos reales — adquisición y verificación técnica

> **Histórico, centrado corregido después:** la auditoría de catálogo mostró
> que las posiciones predichas de Barnard y WISE 0855 quedaban fuera de estas
> salidas de 4′. Los archivos son reales, pero no acreditan cobertura del objeto
> en su época. No utilizar estos IDs como presets vigentes. Ver
> [ASTROMETRIA.md](../../../ASTROMETRIA.md) para los nuevos centros y paquetes.

Pipeline 0.1.4; ejecución registrada en `acquisition-report.json`. Código base
`19fd5+working-tree`: cambios del bloque de integridad/parser, no una ejecución
del commit 19fd5 limpio. No se atribuye esta revisión técnica a Jordi/Dany.

Comando ejecutado desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -u scripts\verify_real_sequences.py --target all --fov 4 --frames 3 --maxrec 20 --max-candidates 6
```

Colecciones: DR1, QR3 y ambas deep. Un intento por petición, conexión 5 s,
lectura 12 s. Los cinco paquetes tienen tres frames reales, FOV 4 arcmin,
misma rejilla por resultado, escala común y VERSION FITS 7.0.5.

| Campo de referencia | result_id local | Detector | MJD mínimo–máximo | λ mínimo–máximo (µm) | Fracción válida salida | Centros válidos | Tiempo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Barnard | `3b1352edd877bddd` | D3 | 60902.864715–61272.906175 | 2.204–2.341 | 93.36–96.25% | 3/3 | 25.953 s |
| Epsilon Indi B | `40457e8dccea6c10` | D6 | 60794.064813–61306.724295 | 4.427–4.867 | 74.29–94.08% | 1/3 | 26.063 s |
| WISE 0855 | `1966b97f9c87160f` | D2 | 60801.108089–60801.448624 | 1.342–1.591 | 86.79–91.26% | 3/3 | 25.079 s |
| RW Aurigae | `69b4af920d55eff0` | D1 | 60919.419647–61291.276650 | 0.771–1.068 | 85.54–88.63% | 2/3 | 17.890 s |
| R Draconis | `7266e9f837994b6f` | D6 | 60794.093521–61183.493490 | 4.456–4.726 | 83.43–88.56% | 0/3 | 14.687 s |

## Estado y límites

**Todos son `partial`, no `ready`.** Todas las búsquedas presentaron overflow:
la muestra MAXREC=20 por colección no es exhaustiva ni necesariamente cubre
todo el intervalo disponible. Fallaron 1/1/2/0/2 candidatos respectivamente;
se usaron sustitutos sin cambiar de detector. Ninguna colección falló por
completo en esta ejecución. El proceso devuelve 1 porque no todos son ready,
no porque no haya paquetes útiles.

- Coordenadas aproximadas `verified=False`: no se han propagado movimientos
  propios ni confirmado identidad de las fuentes.
- λ cambia entre los frames de cada campo. Las diferencias visuales no prueban
  variabilidad ni movimiento. No se han habilitado restas/apilados.
- «Centro válido» es el píxel del centro solicitado según nuestra máscara,
  no una detección. R Draconis tiene los tres centros enmascarados; no se oculta.
- WISE 0855 solo abarca ~8.17 horas en esta muestra, no una línea base anual.

## Verificaciones efectivas

`fits-verification.json`: 15 FITS originales abiertos; OBSID y detector de IMAGE,
VERSION de PRIMARY y MJD-OBS coinciden con el manifiesto/SIA (tolerancia MJD
1e-6 día por redondeo). Los 45 archivos indexados pasan tamaño y SHA-256.
λ/ancho se obtienen del WCS espectral en la coordenada solicitada; no se ha hecho
todavía contraste independiente con Firefly/calibraciones científicas.

`browser-verification.json` y cinco capturas: Edge 157.0.4341.46, escritorio
1366×900, America/Lima. Se abrieron los cinco resultados persistidos, se
recorrieron sus tres frames, se verificó reproducción/pausa y se descargaron
los 45 artefactos con HTTP 200, además de los cinco manifiestos 200.
No es prueba de adquisición desde formulario ni de teléfono físico.

## Abrir y reproducir

Con el servidor local y los paquetes de esta máquina:
`http://127.0.0.1:8000/?result=RESULT_ID`.

Esta carpeta contiene informes, manifiestos y capturas, **no los FITS/PNG
del paquete**. Los datos están en `data/results/`, ignorado por Git. En otra
máquina, repetir el script con red; la selección y el result_id pueden variar.
Los manifiestos conservan URLs y hashes de los originales seleccionados para
auditar la adquisición. La disponibilidad futura de IRSA no está garantizada.
