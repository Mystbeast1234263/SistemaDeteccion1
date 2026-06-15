# Sprint 5 — Reporte de Testing SIDACS

Generado: 2026-06-15 05:06:46

## Casos de prueba

### Video normal sin actividad sospechosa
- **ID:** `normal_video`
- **Tipo:** session
- **Descripcion:** Escena estable o movimiento leve sin patron sospechoso.
- **Resultado esperado:** Intensidad baja, pocas alertas, sin detecciones sospechosas ML.
- **Resultado obtenido:** APROBADO — Alertas: 3, sospechosos: 2, max int: 31%
- **Fecha:** 2026-06-15 05:03:09

### Movimiento excesivo
- **ID:** `excessive_motion`
- **Tipo:** session
- **Descripcion:** Movimiento brusco o intenso en el encuadre.
- **Resultado esperado:** Intensidad alta, alertas de actividad elevada o riesgo alto.
- **Resultado obtenido:** REVISAR — Intensidad max 31%, eventos riesgo alto: 0
- **Fecha:** 2026-06-15 05:03:11

### Simulacion de comportamiento sospechoso
- **ID:** `suspicious_simulation`
- **Tipo:** session
- **Descripcion:** Patron de movimiento intenso sostenido con modelo activo.
- **Resultado esperado:** Prediccion sospechosa o riesgo ALTO con confianza relevante.
- **Resultado obtenido:** APROBADO — Sospechosos: 2, conf max: 78.0%
- **Fecha:** 2026-06-15 05:03:11

### Video vacio / estatico
- **ID:** `empty_video`
- **Tipo:** automated
- **Descripcion:** Frame sin cambios entre capturas consecutivas.
- **Resultado esperado:** Intensidad 0 o muy baja, sin alertas de movimiento.
- **Resultado obtenido:** APROBADO — Video estatico: sin falsos positivos de movimiento.
- **Fecha:** 2026-06-15 05:03:12
- **Observaciones:** Prueba automatica

### Webcam en tiempo real
- **ID:** `webcam_realtime`
- **Tipo:** session
- **Descripcion:** Monitoreo en vivo con camara web.
- **Resultado esperado:** Analisis fluido, FPS estable, sin cuelgues de interfaz.
- **Resultado obtenido:** APROBADO — Frames: 380, FPS prom: 24.0
- **Fecha:** 2026-06-15 05:03:14

## Resumen

- Total registros: 6
- Aprobados: 5
- A revisar: 1

## Como repetir las pruebas

1. Abra la pestana **Pruebas** en SIDACS.
2. Para *Video vacio*, use **Ejecutar automatico**.
3. Para los demas casos, cargue video o webcam, inicie monitoreo y pulse **Registrar resultado**.
4. Pulse **Generar reporte** para actualizar este archivo.
