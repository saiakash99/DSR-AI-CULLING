import sys
import os
import platform
import psutil # You may need to: pip install psutil
import sqlite3

def industrial_verify():
    print(f"🛠️  DSR PRO V2 - SYSTEM READINESS SCAN")
    print("-" * 40)

    # 1. OS & Python Check
    print(f"🖥️  OS: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")

    # 2. Memory Check (Crucial for 30k images)
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024**3)
    status = "✅ PASS" if total_gb >= 8 else "⚠️ WARNING (8GB+ Recommended)"
    print(f"🧠 RAM: {total_gb:.2f} GB - {status}")

    # 3. Database Write Test (Update 2 Logic)
    try:
        conn = sqlite3.connect('test_verify.db')
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.close()
        os.remove('test_verify.db')
        print(f"🗄️  DB Write Access: ✅ PASS")
    except Exception as e:
        print(f"🗄️  DB Write Access: ❌ FAIL ({e})")

    # 4. Critical UI Engine Check
    try:
        from PySide6 import QtCore
        print(f"🎨 UI Engine (PySide6): ✅ INSTALLED")
    except ImportError:
        print(f"🎨 UI Engine (PySide6): ❌ MISSING (Required for Obsidian UI)")

    print("-" * 40)
    print("🚀 READINESS COMPLETE. You are cleared for takeoff.")

if __name__ == "__main__":
    industrial_verify()