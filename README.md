# OrbitLens — SPHEREx

Proyecto de exploración de imágenes infrarrojas de SPHEREx para el reto
Planet X and SPHEREx descrito en el plan del equipo.

## Organización

El reparto completo, las tareas y los criterios de aceptación están en
[TRABAJO_EQUIPO.md](TRABAJO_EQUIPO.md).

| Integrante | Responsabilidad |
| --- | --- |
| Jesús | Ingeniería, correcciones e integración |
| Jordi | Datos y revisión científica |
| Dany | Experiencia de usuario y QA funcional |
| Terán | Demo y video |
| Regalado | Documentación, pitch y submission |

## Estado del repositorio

Al inspeccionar `origin/master` el 14 de noviembre de 2026, solo contenía
`PLAN.md`. La aplicación y las pruebas descritas allí aún deben incorporarse;
por eso no hay instrucciones de ejecución verificadas en esta copia.

- [Plan funcional e historial](PLAN.md)
- [Protocolo de construcción](PROTOCOLO_CONSTRUCCION.md)
- [Recursos oficiales revisados y decisiones técnicas](RECURSOS_RETO.md)
- [Reparto y secuencia de trabajo](TRABAJO_EQUIPO.md)
- Demo citada en el plan: https://orbitlens-spherex.onrender.com
  (disponibilidad no comprobada en esta revisión).

Los resultados exploratorios no constituyen detecciones ni movimientos
confirmados científicamente.

## Base técnica vigente

La revisión del 14 de noviembre de 2026 adopta imágenes individuales **DR1 + QR3**
(wide y deep). QR2 ya no aparece en búsquedas IRSA/VO. Los cubos espectrales de
102 canales son productos diferentes de una secuencia temporal.

El protocolo define cómo recuperar o construir la aplicación y verificarla.
Sus comandos de arranque son objetivos pendientes de comprobar cuando se
incorpore el código; las pruebas históricas no acreditan esta copia.
