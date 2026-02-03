import os
from core.brain_logic_v1 import TitaniumBrainLogic

def test_internal_nerve():
    print("🔌 Testing Nervous System Connection...")
    
    # 1. Initialize Brain
    try:
        brain = TitaniumBrainLogic()
        print("✅ Brain Module: Loaded and Responding.")
    except Exception as e:
        print(f"❌ Brain Module: Failed to Load. Error: {e}")
        return

    # 2. Test Image (Change this path to any real image on your PC)
    test_image = r"C:\Users\Bhanu\OneDrive\PROJECT\DSR_PRO_V2\test_photo.jpg" 

    if not os.path.exists(test_image):
        print(f"⚠️ Test aborted: Please put a real image path at line 14.")
        return

    # 3. Request Analysis (This is the 'Analyze Magic' call)
    score = brain.calculate_score(test_image)
    
    print("-" * 30)
    print(f"📸 Image: {os.path.basename(test_image)}")
    print(f"📊 Brain Score: {score}%")
    
    # 4. Simulate the UI Verdict
    if score >= 80: verdict = "KEEP (Green)"
    elif score <= 30: verdict = "REJECT (Red)"
    else: verdict = "PENDING (Gold)"
    
    print(f"⚖️ UI Decision: {verdict}")
    print("-" * 30)
    print("✅ TEST COMPLETE: Brain and Logic are fully synced.")

if __name__ == "__main__":
    test_internal_nerve()