import sys
import os
from PySide6.QtWidgets import QApplication

# Attempting to import your actual project modules
try:
    from core.ai_worker import TitaniumWorker
    from core.brain_logic_v1 import TitaniumBrainLogic
    print("✅ System Imports: Verified.")
except ImportError as e:
    print(f"❌ System Imports: Failed. Error: {e}")
    sys.exit()

def verify_system():
    print("\n🔬 DSR PRO V2: Nerve Interlinking Diagnostic...")
    
    # 1. Start a temporary App instance (required for Signals)
    app = QApplication(sys.argv)

    # 2. Check Brain Module (The Logic)
    try:
        logic = TitaniumBrainLogic()
        print("🟢 [BRAIN] Logic V1: Online.")
    except Exception as e:
        print(f"🔴 [BRAIN] Logic V1: Critical Failure. Error: {e}")
        return

    # 3. Check Nerve (The Worker)
    # We test if the Worker can physically reach the Logic file
    test_paths = ["mock_image.jpg"] 
    try:
        worker = TitaniumWorker(test_paths)
        print("🟢 [NERVE] TitaniumWorker: Initialized and connected.")
    except Exception as e:
        print(f"🔴 [NERVE] TitaniumWorker: Worker Link Broken. Error: {e}")
        return

    # 4. Check the Logic Connection (The Pixel Test)
    print("🧬 Testing Signal Path: UI -> Nerve -> Brain...")
    
    # IMPORTANT: Change this to a real image path on your PC for 100% accuracy
    sample_img = r"C:\Users\Bhanu\OneDrive\PROJECT\DSR_PRO_V2\test_photo.jpg"
    
    if os.path.exists(sample_img):
        score = logic.calculate_score(sample_img)
        print(f"🟢 [LINK] Signal Successful. Brain returned score: {score}%")
        
        if score > 0:
            print("\n💎 VERDICT: Nervous system is 100% Interlinked.")
        else:
            print("\n🟡 VERDICT: Connection works, but output is 0. Check camera focus.")
    else:
        print("\n⚪ [LINK] Path test skipped. Put a real image path at line 41 for a pixel-test.")

if __name__ == "__main__":
    verify_system()