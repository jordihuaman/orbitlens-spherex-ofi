# Correcciones y revisión cruzada — 2026-11-14

## Jesús: corrección técnica (pipeline 0.1.1)

- Epsilon Indi B: corregido el error de un grado en RA: **330.04375 →
  331.04375 grados** (22h04m10.5s). Dec −56.78264 grados. Es una referencia
  aproximada J2000 para el campo Ba/Bb, no Epsilon Indi A ni el planeta Ab.
  `verified=False` se conserva: falta resolver/propagar astrometría actual con
  Jordi. No se presenta la coordenada histórica propagada 2026.5 de PLAN como
  una nueva medición. El formulario muestra ahora referencia y advertencia.
- Detector: reconoce `D2` y `SPHEREx-D2` (también minúsculas). Una petición
  explícita sin coincidencias termina `empty`, sin sustituirla por otras bandas.
- `auto`: elige un solo detector con más exposiciones fechadas; empate por
  D1–D6. Excluye metadatos desconocidos/contradictorios antes de seleccionar
  épocas. No es una elección de sensibilidad ni de detectabilidad científica.
- La elección queda registrada en `search.detector_requested` y
  `search.detector_selected`. Un FITS con detector reconocible diferente se
  descarta. Un detector común **no garantiza λ compatible**.
- Pipeline incrementado para no reutilizar resultados previos a esta corrección.

## Entrega del recorte real

```powershell
$env:ORBITLENS_CODE_COMMIT = git rev-parse HEAD
.\.venv\Scripts\python.exe scripts\verify_real_data.py --target epsindi_b --maxrec 5 --download --detector D2
```

Con acceso, el script genera `data/results/<id>/` con el **recorte original**,
FITS alineado, PNG y manifiesto con colección, obs_id, URLs, coordenadas,
referencia, detector, tiempos, metadatos de calidad, tamaños y SHA-256.
Los tres archivos se indexan en la API. Un solo recorte no cierra H2.

Reintento ejecutado tras corregir las coordenadas: cero registros recuperados;
DR1 y DR1 deep agotaron el timeout de lectura (15 s); QR3 y QR3 deep
devolvieron HTTP 502. Intentos limitados a uno por colección en esta sonda.
**No hay entrega real todavía ni se cierra H1.** Las pruebas del contrato usan
FITS sintéticos; no sustituyen esta evidencia. No se suben descargas a Git.

## Dany: QA real del navegador (pendiente)

Probar el commit publicado, registrar navegador/versión, fecha, escritorio/móvil,
pasos, resultado esperado/observado, consola/red y captura cuando corresponda:

1. Epsilon Indi B carga RA 331.04375 y muestra referencia no verificada.
2. D2 solo reproduce D2; si no tiene cobertura muestra vacío, nunca otra banda.
3. Automático informa un único detector; revisar fecha, λ y avisos por frame.
4. Play/pausa, anterior/siguiente, slider, velocidad y enlace compartido.
5. Recargar el enlace exacto, descargar PNG/FITS y abrir manifiesto.
6. Entradas inválidas, errores IRSA y presentación móvil.

Puede usarse la demo **sintética** para los controles, etiquetándolo en el
informe; no acredita consultas reales ni O3. No se ejecutó QA visual real como
parte de estas pruebas automatizadas de backend/build.

## Terán: guion para revisión científica (pendiente)

Entregar el texto del guion (y, si existe, storyboard/timecodes) para revisión
de Jordi antes de grabar. Debe distinguir:

- datos reales de demostración sintética, indicando cuál aparece en cada escena;
- campo de Epsilon Indi B/Ba-Bb frente a la primaria A y el planeta Ab;
- secuencia visual frente a detección o movimiento confirmado;
- cambios de fecha frente a cambios de λ, máscaras o cobertura;
- resultados comprobados frente al bloqueo actual de IRSA.

No hay guion nuevo en esta copia para revisar. No se atribuyen a Dany/Terán
pruebas, entregas ni aceptación que todavía no hayan comunicado.
