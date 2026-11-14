# Guion de demo — borrador grabable (90 segundos)

Preparado por el agente para Jesús; sustituye el bloqueo de redacción de la
parte de Terán, **no una grabación realizada ni una revisión firmada por Jordi**.
Revisar reglas del evento antes de elegir duración/formato final.

## Versión A: honesta con el estado actual (datos sintéticos)

| Tiempo | Pantalla / acción | Narración |
| --- | --- | --- |
| 00–12 | Título OrbitLens; abrir recursos oficiales | «Los archivos de NASA contienen muchas observaciones del cielo. Compararlas puede ser difícil: cambian la orientación, la longitud de onda y la calidad de los píxeles.» |
| 12–25 | Formulario; seleccionar Epsilon Indi B, mostrar RA/Dec y referencia | «OrbitLens permite elegir un campo por coordenadas y preparar una secuencia temporal de imágenes SPHEREx. La referencia del objeto y sus límites están visibles: elegir un nombre no confirma su detección.» |
| 25–38 | Abrir resultado sintético preparado; mantener su etiqueta en pantalla | «Esta demostración de la interfaz utiliza imágenes sintéticas, no observaciones de NASA. El acceso a IRSA está fallando en nuestro entorno; no presentamos estos píxeles como datos reales.» |
| 38–52 | Play, pausa, fecha, avanzar y slider | «El reproductor mantiene el campo fijo y permite recorrer las fechas. El pipeline está diseñado para reproyectar los recortes a una rejilla común y usar una escala visual compartida.» |
| 52–65 | Detector, λ, cobertura y avisos; descargar manifiesto | «Cada frame muestra su detector y calidad. En los datos reales registramos procedencia y hashes. Una diferencia visual puede ser banda, fondo o máscara: no demuestra movimiento ni un nuevo objeto.» |
| 65–78 | Panel de recursos; abrir WiseView en pestaña separada | «También enlazamos el campo con WiseView, operado por AMNH para imágenes WISE, otra misión NASA. Las misiones y los datos se mantienen separados. Los tutoriales oficiales de IRSA guían la lectura FITS y WCS.» |
| 78–90 | Compartir enlace; cierre con código y pendientes | «La interfaz y sus archivos son reproducibles y tienen pruebas automatizadas. El siguiente paso es validar recortes DR1 y QR3 de los cinco campos. OrbitLens ayuda a explorar evidencia; no anuncia un descubrimiento de Planet X.» |

No pulsar «Buscar» en una grabación para fingir una respuesta real. Precargar el
resultado sintético y narrar su naturaleza. No tapar su etiqueta en el montaje.

## Preparación técnica

```powershell
npm --prefix frontend run build
.\.venv\Scripts\python.exe scripts\make_demo_result.py
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Abrir `http://127.0.0.1:8000/?result=5e1c78336933afa7`. Grabar a 1080p con texto
legible, sin terminales con credenciales. Añadir subtítulos; música solo propia
o con licencia compatible. Atribuir fuentes según `CREDITOS.md`.

## Versión B: solo después de validar datos reales

Sustituir la escena 25–38 por «Este recorte procede de [colección], observación
[obs_id], [fecha], procesado con [pipeline/commit]». Adjuntar el manifiesto y
los FITS inspeccionados. Para narrar una **secuencia temporal real**, exigir
varias épocas reales: un recorte aislado no basta. Conservar avisos de máscaras,
λ y coordenadas. No reciclar manifiestos QR2 como si fueran DR1.

El ejemplo WISE del usuario usa RA 133.786245°, Dec −7.244372°, FOV 176″.
No convertir esas coordenadas, de época no establecida aquí, en una nueva
identificación astrométrica de WISE 0855 ni confundir sus imágenes con SPHEREx.

## Revisión de narrativa (autocontrol, sin firma externa)

- [x] Distingue datos sintéticos, datos previstos y evidencia verificada.
- [x] Epsilon Indi B/Ba-Bb no se confunde con A o el planeta Ab.
- [x] Las fechas no se confunden con los 102 planos de un cubo espectral.
- [x] No atribuye detección, movimiento propio ni fotometría calibrada al visor.
- [x] WiseView/AMNH, Gaia/ESA y NEOSSat/CSA se atribuyen correctamente.
- [ ] Revisión humana de Jordi o Jesús sobre la grabación final.

## Registro de ensayos

| Ensayo | Fecha | Duración medida | Fallos / cambios | Estado |
| --- | --- | --- | --- | --- |
| 1 | — | — | — | Pendiente |
| 2 | — | — | — | Pendiente |
| 3 | — | — | — | Pendiente |

Los timecodes son objetivos, no duraciones medidas. Video final, subtítulos
exportados, URL pública y permisos de reproducción siguen pendientes.
