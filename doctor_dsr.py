import os
import sys
import sqlite3
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REQUIRED_DIRS = ['core', 'ui', 'assets', 'assets/icons']
REQUIRED_FILES = [
    'main.py', 
    'core/brain_logic_v1.py', 
    'core/ai_worker.py', 
    'ui/main_window.py', 
    'ui/gallery.py'
]

def print_status(component, status, message):
    icon = "✅" if status == "OK" else "❌"
    print(f"{icon} [{component:<15}] : {message}")

def check_structure():
    print("\n--- 1. FILE SYSTEM CHECK ---")
    all_good = True
    for folder in REQUIRED_DIRS:
        path = os.path.join(PROJECT_ROOT, folder)
        if os.path.exists(path):
            print_status("FOLDER", "OK", folder)
        else:
            print_status("FOLDER", "FAIL", f"Missing: {folder}")
            all_good = False
            
    for file in REQUIRED_FILES:
        path = os.path.join(PROJECT_ROOT, file)
        if os.path.exists(path):
            print_status("FILE", "OK", file)
        else:
            print_status("FILE", "FAIL", f"Missing: {file}")
            all_good = False
    return all_good

def check_brain():
    print("\n--- 2. BRAIN & LOGIC CHECK ---")
    try:
        from core.brain_logic_v1 import TitaniumBrainLogic
        brain = TitaniumBrainLogic()
        
        # Create a dummy image to test math
        dummy = np.zeros((500, 500, 3), dtype=np.uint8)
        # Draw a shape so it has 'sharpness'
        cv2.rectangle(dummy, (10, 10), (200, 200), (255, 255, 255), -1) 
        cv2.imwrite("temp_brain_test.jpg", dummy)
        
        score = brain.calculate_score("temp_brain_test.jpg")
        
        # Cleanup
        if os.path.exists("temp_brain_test.jpg"):
            os.remove("temp_brain_test.jpg")
        
        if score > 0:
            print_status("AI ENGINE", "OK", f"Logic is functioning. Test Score: {score}%")
        else:
            print_status("AI ENGINE", "FAIL", "Brain returned 0.0 on test pattern.")
            
    except ImportError as e:
        print_status("AI ENGINE", "FAIL", f"Import Error: {e}")
    except Exception as e:
        print_status("AI ENGINE", "FAIL", f"Crash: {e}")

def check_memory():
    print("\n--- 3. DATABASE MEMORY CHECK ---")
    db_path = os.path.join(PROJECT_ROOT, "dsr_pro_memory.db")
    if not os.path.exists(db_path):
        print_status("DATABASE", "WARN", "No database found (Will be created on launch).")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        if 'decisions' in tables:
            print_status("TABLES", "OK", f"Found tables: {tables}")
            cursor.execute("SELECT count(*) FROM decisions")
            count = cursor.fetchone()[0]
            print_status("DATA", "OK", f"Memory contains {count} saved decisions.")
        else:
            print_status("TABLES", "FAIL", "Database exists but tables are missing.")
        conn.close()
    except Exception as e:
        print_status("DATABASE", "FAIL", f"Corrupt DB: {e}")

def check_ui_components():
    print("\n--- 4. UI COMPONENT CHECK ---")
    try:
        # We need a headless app to inspect widgets
        app = QApplication(sys.argv)
        # Import main window logic
        sys.path.append(PROJECT_ROOT) # Ensure root is in path
        from ui.main_window import DSRMainWindow
        
        # Try to initialize the window
        window = DSRMainWindow()
        
        # Check vital organs
        if hasattr(window, 'gallery'):
            print_status("GALLERY", "OK", "Gallery Widget loaded.")
            
            # Check buttons inside gallery
            if hasattr(window.gallery, 'btn_export'):
                print_status("EXPORT BTN", "OK", "Export Button found.")
            else:
                print_status("EXPORT BTN", "FAIL", "Export Button missing.")
                
            if hasattr(window.gallery, 'btn_pending'):
                print_status("PENDING BTN", "OK", "Pending Filter Button found.")
            else:
                print_status("PENDING BTN", "FAIL", "Pending Filter Button missing.")
                
            if hasattr(window.gallery, 'btn_ai_best'):
                print_status("AI BEST BTN", "OK", "AI Best Button found.")
            else:
                print_status("AI BEST BTN", "FAIL", "AI Best Button missing.")

        else:
            print_status("GALLERY", "FAIL", "Gallery Widget missing from Main Window.")

    except Exception as e:
        print_status("UI BUILD", "FAIL", f"Interface crashed during init: {e}")

if __name__ == "__main__":
    print("🏥 STARTING DSR PRO SYSTEM DIAGNOSIS...")
    check_structure()
    check_brain()
    check_memory()
    check_ui_components()
    print("\n--- DIAGNOSIS COMPLETE ---")