# Catálogo, época y límites de los cinco campos — pipeline 0.1.5

## Corrección que invalida una interpretación anterior

Los 15 frames iniciales (`evidencias/irsa/five-fields/`) sí son datos reales,
pero **no acreditan que Barnard ni WISE 0855 estén dentro del recorte de salida**.
Con el catálogo y movimiento propio consultados, sus posiciones predichas
quedaban fuera de los recortes de 4′ en las tres fechas de cada campo.

Esto era un problema de centrado/época, no ausencia de datos SPHEREx ni una
no-detección. No se borran aquellos paquetes ni se alteran sus manifiestos:
se conservan como evidencia histórica con advertencia. La reimportación local
de Barnard `c7733d27c7bfbc6a` demuestra funcionamiento del importador, **no**
resuelve su centrado anterior.

## Fuente y modelo

Se consultó SIMBAD TAP. El endpoint CDS devolvió 404 en estas peticiones; el
espejo oficial Harvard respondió 200 con cinco identificaciones, coordenadas,
movimientos propios y referencias bibliográficas. Respuesta y consulta exactas:
`evidencias/astrometria/simbad-probes.json`. Snapshot operativo:
`orbitlens/catalog_snapshot.json` (recuperado 2026-11-14).

La metadata TAP declara posiciones ICRS con epoch=J2000; `pmra` se interpreta
como μ_α cos δ y `pmdec` como μ_δ, en mas/año. Los centros se propagan a J2026
con un modelo tangencial 3D normalizado. Se omiten paralaje anual, velocidad
radial/perspectiva, aceleración y órbitas de binarias. **Sirve para centrar el
campo, no para medir astrometría ni identificar fuentes en los píxeles.**

| Campo | RA centro J2026 (°) | Dec centro J2026 (°) | Referencia de coordenadas/PM en SIMBAD |
| --- | --- | --- | --- |
| Barnard | 269.446267879734 | +4.768204411842 | 2020yCat.1350....0G |
| Epsilon Indi B | 331.096668778670 | −56.800649173668 | 2020yCat.1350....0G |
| WISE 0855 | 133.759765270652 | −7.242182182634 | 2021ApJS..253....7K |
| RW Aurigae | 76.956586575487 | +30.401291346097 | 2007A&A...474..653V |
| R Draconis | 248.167233072120 | +66.755023826213 | 2020yCat.1350....0G |

Todos los presets mantienen `verified=False`: no existe ajuste astrométrico
a SPHEREx ni detección confirmada. La API conserva época, referencia y modelo
en solicitudes por nombre. El centro permanece fijo durante la reproducción;
no se desplaza/recentra cada frame para simular movimiento.

## Paquetes seleccionados con el centrado corregido

| Campo | result_id local | Frames | Método / estado |
| --- | --- | --- | --- |
| Barnard | `59e0515d0d3a48a8` | 3, D1 | SIA/IBE, partial |
| Epsilon Indi B | `9867e7a480d0fcce` | 3, D3 | SIA/IBE, partial |
| WISE 0855 | `799cfc2d9920b4bf` | 3, D3 | SIA/IBE, partial |
| RW Aurigae | `f3f8e67c01bbaf99` | 3, D6 | SIA/IBE, partial |
| R Draconis | `27ade5bccee5d737` | 3, D6 | Importación local explícita, ready de construcción |

La búsqueda en línea de R Draconis solo produjo un frame D2 válido dentro de
ocho candidatos (`10a5e91142c39ebd`, partial); otros fallaron por 503/calidad.
No se cambió de detector silenciosamente: se importaron **por separado** tres
originales D6 ya descargados, conservando sus URLs/hashes y reproyectándolos al
centro nuevo. `ready` ahí significa que terminó la importación, no consulta
exhaustiva de IRSA ni validez científica. El visor identifica la importación.

Con los nuevos centros, las posiciones predichas están dentro de la rejilla
en los 15 frames seleccionados. Muchos píxeles próximos a la posición predicha
siguen enmascarados; se registran como tales, no como fuentes ausentes.
Ni siquiera un píxel válido implica detección. λ cambia entre frames y no se
han validado restas ni fotometría. La comprobación es geométrica de catálogo.

## Reproducir la auditoría

```powershell
.\.venv\Scripts\python.exe scripts\audit_astrometry.py --acquisition-report evidencias\astrometria\corrected-fields\selected-results.json
```

Requiere los paquetes locales correspondientes. La auditoría evalúa la posición
de catálogo a la fecha MJD de cada frame, la proyecta al WCS derivado y registra
si está dentro y si su píxel más próximo es finito. No busca máximos ni ajusta
centroides; no proporciona error astrométrico ni validación independiente de λ.
Evidencia: `previous-fields-audit.json`, `corrected-fields/selected-astrometry-audit.json`.
