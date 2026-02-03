import sys
import io
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QGuiApplication
from PySide6.QtCore import Qt, QTimer
from ui.main_window import TitaniumMainWindow
from core.app_controller import TitaniumController

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("🚀 DSR PRO V2: Initiating Stable Multi-Stage Launch...")
    
    # 1. PRE-RENDER PAINT
    # We apply the Dark Palette at the Application level before the window exists.
    # This is the ONLY way to truly stop the white flash.
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(5, 5, 5))
    dark_palette.setColor(QPalette.WindowText, QColor(204, 204, 204))
    dark_palette.setColor(QPalette.Base, QColor(10, 10, 10))
    dark_palette.setColor(QPalette.Text, QColor(204, 204, 204))
    dark_palette.setColor(QPalette.Button, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.ButtonText, QColor(204, 204, 204))
    app.setPalette(dark_palette)
    
    # 2. INITIALIZE BODY
    window = TitaniumMainWindow(controller=None)
    
    # 3. CONNECT NERVOUS SYSTEM
    try:
        controller = TitaniumController(window)
        window.controller = controller
    except Exception as e:
        print(f"⚠️ Warning: Brain not linked yet: {e}")

    # 4. Show window and clamp to available screen geometry
    window.show()
    screen = QGuiApplication.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        window.setGeometry(geo)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
