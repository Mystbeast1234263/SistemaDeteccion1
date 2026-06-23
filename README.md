# SIDACS — Sistema Inteligente de Detección y Análisis de Comportamientos Sospechosos

Aplicación de escritorio (Python + PyQt5 + OpenCV) para analizar video en tiempo real con flujo óptico Farneback y Machine Learning.

**Integrantes:** Joshua Jair Chavez Abirari · Marcelo Mena Molina  
**Versión:** 6.0.0-sprint6

## Requisitos

- Python 3.8+
- Dependencias: `pip install -r requirements.txt`

## Ejecución

```bash
python main.py
```

## Documentación

| Archivo | Contenido |
|---------|-----------|
| `documentacion.html` | Manual del proyecto (Sprints 0–6) |
| `manual_tecnico.html` | Arquitectura técnica |
| `docs/acta_reclamacion_40_puntos_ENTREGA.docx` | Acta de entrega y evidencias (versión actualizada) |

## Estructura

```
SistemaDeteccion/
├── main.py              # Entrada
├── ui/                  # Interfaz gráfica
├── video/               # Reproductor, webcam, flujo óptico
├── ml/                  # Dataset, modelo, evidencias, pruebas
├── models/              # Modelos .pkl
├── dataset/             # dataset.csv
├── evidence/            # Capturas y clips en runtime
├── testing/             # Resultados de pruebas
├── videoPrueba/         # Videos de demostración
└── docs/evidencias/     # Capturas para acta de entrega
```

## Repositorio

https://github.com/Mystbeast1234263/SistemaDeteccion1
