import sys
import os
import shutil
import time
import random
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSize, Qt
from PIL import Image, ImageDraw # Requires pip install pillow

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.main_window import TitaniumMainWindow
from core.app_controller import TitaniumController

TEST_FOLDER = "C:/Temp/DSR_Stress_Test"

def generate_dummy_data(count):
    """Generates 'count' dummy images to simulate heavy load."""
    if not os.path.exists(TEST_FOLDER):
        os.makedirs(TEST_FOLDER)
    
    print(f"🔥 STRESS TEST: Generating {count} dummy images...")
    for i in range(count):
        img = Image.new('RGB', (800, 600), color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        d = ImageDraw.Draw(img)
        d.text((10,10), f"IMG_{i}", fill=(255,255,255))
        img.save(os.path.join(TEST_FOLDER, f"img_{i}.jpg"), "JPEG")
    print("🔥 Generation Complete.")

def run_stress_test():
    print("🚀 LAUNCHING HEAVY LOAD TEST...")
    app = QApplication(sys.argv)
    
    # 1. Setup Data
    generate_dummy_data(500) # Start with 500 images
    
    # 2. Launch App
    window = TitaniumMainWindow()
    controller = TitaniumController(window)
    window.controller = controller
    window.showMaximized()
    
    # 3. Define the Attack Sequence
    def step_1_load():
        print("🔨 STEP 1: Heavy Import...")
        controller.handle_import(TEST_FOLDER)
        QTimer.singleShot(5000, step_2_scroll) # Wait 5s for load

    def step_2_scroll():
        print("🔨 STEP 2: Rapid Scrolling...")
        # Simulate scrolling down
        scroll_bar = window.gallery.scroll.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        QTimer.singleShot(2000, step_3_zen_spam)

    def step_3_zen_spam():
        print("🔨 STEP 3: Mode Switching Spam...")
        window.gallery.set_mode(1) # Zen
        QTimer.singleShot(500, lambda: window.gallery.set_mode(0)) # Grid
        QTimer.singleShot(1000, lambda: window.gallery.set_mode(1)) # Zen
        QTimer.singleShot(1500, lambda: window.gallery.set_mode(0)) # Grid
        QTimer.singleShot(3000, finish)

    def finish():
        print("✅ STRESS TEST PASSED: App did not crash.")
        # Cleanup
        # shutil.rmtree(TEST_FOLDER) 
        sys.exit()

    # Start the chain
    QTimer.singleShot(1000, step_1_load)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_stress_test()