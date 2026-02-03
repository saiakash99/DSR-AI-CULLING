import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import TitaniumMainWindow
from core.app_controller import TitaniumController
from ui.styles import GLOBAL_STYLE
# Add this small function to your UI class to see results immediately
def show_me_the_magic(self):
    # This pulls whatever the IntelligentSearch has indexed so far
    results = self.search_engine.get_all_scanned_images() 
    if results:
        self.gallery_grid.update_images(results)
        print(f"🚀 Success! Displaying {len(results)} images.")
    else:
        print("Still scanning... give it 10 more seconds!")
def launch_test_session():
    # 1. Initialize the Application
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)

    # 2. Initialize the Controller
    controller = TitaniumController()
    
    # 3. Correct Path (Ensuring no extra spaces at the start of the line)
    test_path = r"C:\Users\Bhanu\OneDrive\Desktop\WeddingCuller\test_photos"
    
    if not os.path.exists(test_path):
        print(f"❌ Error: Path not found at {test_path}")
        print("💡 Hint: Please manually create the folder 'WeddingCuller/test_photos' on your Desktop.")
        return

    print(f"📂 Connecting to: {test_path}")
    
    # 4. Trigger the AI Scan logic
    controller.start_ai_scan([test_path])
    
    # 5. Display the UI
    controller.window.show()
    print("🚀 SUCCESS: Gallery Loaded. UI is now active!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_test_session()