"""
Sistema Inteligente de Detección y Análisis de Comportamientos Sospechosos
Punto de entrada de la aplicación — Sprint 1: Interfaz, reproducción de video y webcam.
"""

import os
import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.chdir(ROOT_DIR)


def check_dependencies() -> None:
    missing = []
    try:
        import PyQt5  # noqa: F401
    except ImportError:
        missing.append("PyQt5")
    try:
        import cv2  # noqa: F401
    except ImportError:
        missing.append("opencv-python")
    try:
        import numpy  # noqa: F401
    except ImportError:
        missing.append("numpy")

    if missing:
        print("Faltan dependencias:", ", ".join(missing))
        print(f'Instale con:  cd "{ROOT_DIR}"  y luego  pip install -r requirements.txt')
        sys.exit(1)


def load_stylesheet(app) -> None:
    qss_path = ROOT_DIR / "styles" / "dark_theme.qss"
    if qss_path.exists():
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> int:
    check_dependencies()

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from ui.main_window import MainWindow
    from utils.constants import APP_SHORT_NAME

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_SHORT_NAME)
    if hasattr(app, "setApplicationDisplayName"):
        app.setApplicationDisplayName(APP_SHORT_NAME)

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec_()


def _show_fatal_error(message: str) -> None:
    print(message, file=sys.stderr)
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error al iniciar SIDACS", message)
    except Exception:
        input("\nPresione Enter para salir...")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        _show_fatal_error(traceback.format_exc())
        sys.exit(1)

