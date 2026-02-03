import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import TitaniumMainWindow
from core.app_controller import TitaniumController

def main():
    print("🚀 STARTING TITANIUM DIAGNOSTIC MODE...")
    app = QApplication(sys.argv)
    
    # 1. Launch App Hidden (or Visible)
    window = TitaniumMainWindow()
    controller = TitaniumController(window)
    window.controller = controller
    
    window.show() # Show it so you can see the bot working
    
    # 2. Start the Bot immediately
    print("🤖 Bot is taking over...")
    controller.run_diagnostics()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()