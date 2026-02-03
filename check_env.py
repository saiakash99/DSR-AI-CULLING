import sys
import importlib

def check_setup():
    libraries = ['PySide6', 'numpy', 'sqlite3', 'cv2']
    print("🛡️ DSR PRO V2 - PRE-FLIGHT CHECK\n" + "-"*30)
    
    missing = []
    for lib in libraries:
        try:
            importlib.import_module(lib)
            print(f"✅ {lib:10} : INSTALLED")
        except ImportError:
            print(f"❌ {lib:10} : MISSING")
            missing.append(lib)

    if missing:
        print("\n🔧 ACTION REQUIRED: Run the following command:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\n🚀 ALL SYSTEMS GO: Your environment is ready for DSR PRO V2.")

if __name__ == "__main__":
    check_setup()