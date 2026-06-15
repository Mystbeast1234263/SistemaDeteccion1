# Sprint 5 — Optimizaciones SIDACS

Documento para estudiar y presentar las mejoras del Sprint 5.

---

## 1. Problema que reportaron los usuarios

- El video y la webcam se veían **lentos** o con tirones.
- En monitoreo, la app procesaba demasiado en cada frame antes de mostrarlo.
- Videos 1080p/2K saturaban la CPU al copiar, analizar y dibujar overlays en resolución completa.

---

## 2. Objetivo de fluidez

Que el usuario vea video y cámara **fluidos**, mientras el análisis (flujo óptico + ML) sigue funcionando en segundo plano sin bloquear la pantalla.

---

## 3. Herramientas y tecnologías usadas

| Herramienta | Para qué se usó |
|-------------|-----------------|
| **OpenCV (cv2)** | Captura webcam, reproducción de video, escalado con `INTER_AREA`, flujo óptico Farneback en resolución reducida |
| **PyQt5 (QTimer, QPixmap)** | Timer de reproducción, conversión frame→pantalla, throttling de refresco visual |
| **NumPy** | Conversión BGR→RGB rápida con slicing `[:, :, ::-1]` |
| **psutil** | Medir CPU, RAM y tiempo por frame en el panel Métricas |
| **scikit-learn** | Métricas del modelo (Accuracy, Precision, Recall, F1) |

---

## 4. Optimizaciones de fluidez (video y webcam)

### 4.1 Separar lo que se VE de lo que se ANALIZA

**Antes:** cada frame pasaba por flujo óptico con overlay (copia del frame + vectores + HUD) y eso se mostraba en pantalla.

**Ahora:**
- En pantalla siempre se muestra el **frame original** (sin copiar ni dibujar vectores).
- El análisis corre con `draw_overlay=False` (sin copia del frame completo).
- Las métricas van al panel lateral; la imagen queda limpia y rápida.

**Archivos:** `ui/main_window.py`, `video/optical_flow.py`

---

### 4.2 Límite de resolución en pantalla

Los videos 4K/2K ya no se escalan a pantalla completa en memoria completa.

- Máximo de visualización: **1280×720** (`DISPLAY_MAX_WIDTH`, `DISPLAY_MAX_HEIGHT`).
- OpenCV escala con `INTER_AREA` (mejor para reducir tamaño).
- Qt usa `FastTransformation` para el ajuste final.

**Archivo:** `video/frame_utils.py`

---

### 4.3 Análisis menos frecuente (sin perder detección)

| Resolución | Cada cuántos frames se analiza |
|------------|-------------------------------|
| Normal     | 1 de cada 4                   |
| 1080p+     | 1 de cada 6                   |
| 2K/4K+     | 1 de cada 8                   |

Entre análisis se **reutiliza el último resultado** de movimiento/ML.

**Constantes:** `ANALYSIS_FRAME_INTERVAL`, `ANALYSIS_FRAME_INTERVAL_HD`, `ANALYSIS_FRAME_INTERVAL_2K`

---

### 4.4 Webcam con baja latencia

- Resolución de captura limitada a **1280×720**.
- Buffer de cámara = **1 frame** (menos retraso acumulado).
- Se descartan frames viejos del buffer (`grab()` × 2 + `retrieve()`) antes de mostrar.
- DirectShow (`CAP_DSHOW`) en Windows para arranque más rápido.

**Archivo:** `video/webcam.py`

---

### 4.5 Reproductor de video más ligero

- `QTimer` con **CoarseTimer** (menos overhead en Windows).
- Actualización de timeline cada **3 frames** (menos señales Qt).
- Salto automático de frames si el PC no alcanza el FPS del video.

**Archivo:** `video/player.py`

---

### 4.6 Throttling de refresco visual

Durante monitoreo, la pantalla se actualiza como máximo a **30 FPS** (`DISPLAY_TARGET_FPS`), aunque lleguen más frames. Evita saturar la UI.

**Archivo:** `ui/video_panel.py`

---

### 4.7 Menos trabajo en UI y evidencias

- Actualización del sidebar cada **8 frames** (`UI_UPDATE_INTERVAL`).
- Buffer de evidencias cada **8 frames** (`EVIDENCE_FRAME_INTERVAL`).
- Monitor de rendimiento (CPU/RAM) solo cada 10 frames o en pestaña Métricas.

### 4.8 Overlay de analisis opcional

- Checkbox **Overlay analisis** en la barra de controles (solo durante monitoreo).
- **Desactivado (predeterminado):** video limpio, maxima fluidez.
- **Activado:** vectores de flujo optico + HUD (intensidad, riesgo) como en Sprint 2–4.
- El analisis ML y las alertas funcionan igual con overlay on u off.

**Archivos:** `ui/control_bar.py`, `ui/main_window.py`

---

## 5. Reduccion de falsos positivos (Sprint 5)

| Técnica | Descripción |
|---------|-------------|
| **BehaviorFilter** | Exige movimiento sostenido antes de alertar |
| Umbrales ajustados | 18 / 28 / 58 en lugar de 15 / 26 / 56 |
| Confirmación ML | Varios ciclos con confianza ≥ 45% antes de marcar sospechoso |

**Archivo:** `ml/behavior_filter.py`

---

## 6. Estadísticas en porcentajes (presentación profesional)

El panel **Métricas** y el sidebar muestran valores en **%** donde aplica:

| Métrica | Formato |
|---------|---------|
| Eficiencia FPS | % respecto a 30 FPS objetivo |
| Riesgo bajo/medio/alto | % del total de eventos |
| Sospechosos | % de frames analizados |
| Confianza ML | % |
| Capturas | % sobre detecciones sospechosas |
| Modelo | Accuracy, Precision, Recall, F1 en % |
| Rendimiento | CPU %, carga por frame % |

**Archivos:** `ml/statistics.py`, `ui/metrics_panel.py`, `ui/sidebar_panel.py`

---

## 7. Módulo de testing

- Pestaña **Pruebas** con 5 casos documentados.
- Resultados en `testing/test_results.json`.
- Reporte en `docs/sprint5_testing.md`.

**Archivo:** `ml/test_runner.py`, `ui/test_panel.py`

---

## 8. Resultados esperados

- Video y webcam **más fluidos** para el usuario.
- Menos CPU en videos pesados.
- Menos falsos positivos por movimientos normales.
- Métricas visibles en porcentajes para la exposición.
- **Compatibilidad total** con Sprint 1, 2, 3 y 4.

---

## 9. Cómo explicarlo en la presentación (frase corta)

> "Separamos la visualización del análisis: el usuario ve el video original a 30 FPS, mientras OpenCV analiza una versión reducida cada pocos frames. Usamos PyQt5, escalado inteligente y buffer mínimo en webcam para que la app se sienta fluida sin perder detección."

---

## 10. Archivos modificados en esta optimización de fluidez

- `utils/constants.py` — intervalos y límites de display
- `video/frame_utils.py` — cap 1280×720, conversión rápida
- `video/webcam.py` — captura ligera, drop de buffers
- `video/player.py` — timer optimizado
- `video/optical_flow.py` — análisis sin overlay en pantalla
- `ui/main_window.py` — pipeline desacoplado
- `ui/video_panel.py` — throttling 30 FPS
- `ml/statistics.py` — porcentajes
- `ui/metrics_panel.py` — dashboard en %
- `ui/sidebar_panel.py` — estadísticas en %

---

*SIDACS v5.0.0-sprint5*
