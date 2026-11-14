# Decisiones científicas y límites — OrbitLens SPHEREx

Actualización pipeline 0.1.3: un recorte DR1 real del campo de referencia del
tutorial IRSA fue descargado e inspeccionado. Evidencia y limitaciones en
`DATOS_REALES.md`; las referencias anteriores a «ningún FITS real» describen el
estado inicial, no el actual. No hay validación de los cinco objetivos.
Con coordenada solicitada, λ/ancho se evalúan en su posición WCS dentro del
recorte, no simplemente en el píxel central entero. Ambos ejes WAVE-TAB se
interpretan cuando el WCS identifica el segundo como ancho de banda.

Documento vivo. Registra **qué hace el pipeline**, **qué no puede afirmarse** y
las decisiones que Jordi debe revisar. No es una validación científica: en esta
copia no se ha inspeccionado ningún FITS real de SPHEREx (ver
[ENTREGA_TECNICA.md](ENTREGA_TECNICA.md)).

## 1. Qué construye OrbitLens

Dada una coordenada (RA/Dec) y un campo de visión, OrbitLens:

1. consulta las cuatro colecciones vigentes de IRSA —`spherex_dr1`,
   `spherex_qr3`, `spherex_dr1_deep`, `spherex_qr3_deep`— mediante SIA2;
2. conserva únicamente productos de tipo imagen y descarta registros sin `t_min`;
3. reparte la selección a lo largo del intervalo temporal disponible;
4. descarga **recortes** FITS, nunca el archivo completo;
5. lee la extensión `IMAGE` (2D), aplica máscaras y reproyecta a una rejilla
   común;
6. genera un PNG por época y un FITS derivado alineado;
7. escribe un manifiesto con procedencia, tiempos, metadatos, avisos y SHA-256.

El resultado es una **secuencia temporal de imágenes**. No es un cubo espectral:
el cubo All-Sky de DR1 (102 planos) es otro producto y queda fuera del
reproductor temporal.

## 2. Máscaras de calidad

`FLAGS` se lee de la extensión `FLAGS` del MEF. Las definiciones de bits se
interpretan desde las claves `MSKN#`/`MSKD#` de la cabecera:

- el **número de bit es el sufijo** de la clave (`MSKN3` → bit 3);
- `MSKN#` aporta el nombre corto y `MSKD#` la descripción de respaldo;
- solo se enmascaran los nombres de rechazo que la cabecera defina realmente;
- si no hay definiciones, **no se inventan bits**: solo se descartan valores no
  finitos o negativos, y el manifiesto registra el aviso.

Nombres de rechazo previstos: `TRANSIENT`, `OVERFLOW`, `SUR_ERROR`, `NONFUNC`,
`DICHROIC`, `MISSING_DATA`, `HOT`, `COLD`, `PHANMISS`, `NONLINEAR`, `PERSIST`,
`OUTLIER`, `CROSSTALK`, `GHOST`, `GHOST_FPA`, `GHOST_EXT`, `STREAK`, `BLOOM`,
`SNOWBALL`, `HALO`, `SATELLITE_HALO`.

`SOURCE` y `FULLSAMPLE` no se rechazan por sí solos. La política exacta debe
revisarse contra las cabeceras reales cuando IRSA esté disponible; por eso el
manifiesto incluye `mask_policy_version` y los avisos por frame.

## 3. Longitud de onda

La longitud de onda central se intenta obtener del WCS espectral (`WCS-WAVE`,
clave `W`). Si no está disponible, se aceptan `CWAVE`, `WAVELEN` o `WAVE` como
respaldo, **registrando que no proviene de `WCS-WAVE`**. El ancho de banda se lee
de `CBAND`, `BANDWID` o `BWIDTH`.

Las unidades se normalizan a micrómetros solo cuando el valor es plausible para
SPHEREx (≈0.75–5 µm). Si no se puede interpretar, se devuelve `null` y se emite
un aviso; **no se adivina**.

Consecuencia importante: dos frames del mismo detector pueden no corresponder a
la misma longitud de onda en el píxel objetivo. Mostrar λ y ancho de banda es
obligatorio para no comparar épocas espectralmente incompatibles. En esta copia
no se ha comprobado la calibración real.

## 4. Alineación y render

- Rejilla de salida: proyección `RA---TAN`/`DEC--TAN`, norte arriba y este a la
  izquierda, centrada en la coordenada solicitada.
- Escala de píxel por defecto: 6.15″; el tamaño depende del FOV (1–30′).
- Reproyección bilineal con `reproject`; los píxeles sin cobertura quedan
  inválidos y se hacen transparentes.
- Estiramiento **global** para todos los frames de un resultado (`asinh`), con
  límites calculados sobre los píxeles válidos de toda la secuencia. No se
  estira cada frame por separado.
- El centro del campo no se recentra sobre el objeto: una diferencia visual no
  implica movimiento propio.

## 5. Tiempo

Desde pipeline 0.1.1, se reconoce la etiqueta IRSA `SPHEREx-Dn`. Una selección
explícita sin datos no cambia de detector: devuelve `empty`. Automático elige
un único detector por número de exposiciones fechadas (empate D1–D6), sin
interpretar esa elección como sensibilidad científica ni compatibilidad de λ.

`t_min`/`t_max` se toman del registro SIA (MJD) y se convierten a ISO UTC. Los
registros sin `t_min` se excluyen de la secuencia y se avisa de cuántos se
descartaron. La selección se reparte uniformemente por el intervalo disponible
para no concentrar todas las épocas en una sola noche.

## 6. Estados y significado

| Estado | Significado |
| --- | --- |
| `ready` | Secuencia completa con los frames solicitados |
| `partial` | Menos frames de los pedidos, fallos parciales u overflow de SIA |
| `empty` | La consulta no devolvió imágenes utilizables |
| `error` | Fallo de consulta/descarga o ningún frame procesable |

`empty` **no significa que el objeto no exista**. Puede reflejar falta de
cobertura, una selección espectral restrictiva, máscaras o un fallo de datos.

## 7. Afirmaciones prohibidas sin evidencia

Mientras H1 no se cierre con FITS reales inspeccionados, no debe afirmarse:

- que un objeto fue detectado;
- que existe movimiento propio medido;
- que hay variabilidad;
- que la cobertura o la calidad de máscaras de los cinco presets es la esperada;
- que las longitudes de onda están calibradas científicamente.

Las coordenadas de los presets son referencias J2000 aproximadas y están
marcadas `verified=False`. Jordi debe revisarlas contra SIMBAD/IRSA y registrar
época, movimiento propio y limitaciones antes de cualquier uso público.

## 8. Qué falta para cerrar la parte científica

1. Conseguir un FITS real de DR1/QR3 y registrar HDU, unidades, `VERSION`,
   `FLAGS`, `WCS-WAVE`, tiempos y cobertura.
2. Comparar las definiciones `MSKN*`/`MSKD*` reales con la lista de rechazo.
3. Medir residuales de alineación con fuentes de referencia.
4. Revisar los cinco presets y documentar cobertura y limitaciones por campo.
5. Separar explícitamente «secuencia visual» de «detección» en demo y pitch.
