import os
import datetime

# --- CONFIGURATION ---
PROJECT_NAME = "DSR_PRO_V2"

# ==========================================
# 1. FILE CONTENTS (UI & CORE)
# ==========================================

# 1.1 requirements.txt
CODE_REQUIREMENTS = """
PySide6
opencv-python
mediapipe
"""

# 1.2 main.py (The Entry Point)
CODE_MAIN = """import sys
import os
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow
from ui.styles import apply_theme

def main():
    # 1. Setup Application
    app = QApplication(sys.argv)
    app.setApplicationName("DSR PRO AI")
    app.setOrganizationName("DSR Executive")

    # 2. Apply "Billionaire" Dark Theme
    apply_theme(app)

    # 3. Launch Main Window
    window = MainWindow()
    window.show()

    # 4. Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
"""

# 1.3 ui/styles.py (The Look & Feel - FULL VERSION)
CODE_STYLES = """from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

# -- COLORS --
COLOR_BG_MAIN = "#050505"      # Deepest Black
COLOR_BG_PANEL = "#101010"     # Sidebar/Header
COLOR_ACCENT = "#D4AF37"       # Gold
COLOR_TEXT = "#E0E0E0"
COLOR_TEXT_DIM = "#666666"

def apply_theme(app):
    app.setStyle("Fusion")
    
    # Define Dark Palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLOR_BG_MAIN))
    palette.setColor(QPalette.WindowText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Base, QColor(COLOR_BG_PANEL))
    palette.setColor(QPalette.AlternateBase, QColor(COLOR_BG_MAIN))
    palette.setColor(QPalette.ToolTipBase, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ToolTipText, QColor(COLOR_BG_MAIN))
    palette.setColor(QPalette.Text, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Button, QColor(COLOR_BG_PANEL))
    palette.setColor(QPalette.ButtonText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.BrightText, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.Link, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.Highlight, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("black"))
    
    app.setPalette(palette)

    # Global Stylesheet (CSS for Desktop)
    app.setStyleSheet(f\"""
        QMainWindow {{
            background-color: {COLOR_BG_MAIN};
        }}
        QLabel {{
            color: {COLOR_TEXT};
            font-family: 'Segoe UI', sans-serif;
        }}
        /* Sidebar Styling */
        QWidget#Sidebar {{
            background-color: {COLOR_BG_PANEL};
            border-right: 1px solid #222;
        }}
        /* Gold Accent Button */
        QPushButton.accent {{
            background-color: {COLOR_ACCENT};
            color: black;
            font-weight: bold;
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton.accent:hover {{
            background-color: #E5C560;
        }}
    \""")
"""

# 1.4 ui/mainwindow.py (The Layout Shell - FULL VERSION)
CODE_MAINWINDOW = """from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.setWindowTitle("DSR PRO AI | Executive Edition")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 800)

        # Central Widget (The Container)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout (Horizontal: Sidebar | Content)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # -- BUILD UI --
        self.setup_sidebar()
        self.setup_content_area()

    def setup_sidebar(self):
        # Sidebar Container
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar") # For CSS
        self.sidebar.setFixedWidth(280)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("DSR PRO AI")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #D4AF37;")
        layout.addWidget(title)

        # Menu Items (Mock)
        btn_import = QPushButton("Import Folder")
        btn_import.setProperty("class", "accent") # Uses the Gold CSS
        layout.addWidget(btn_import)
        
        layout.addStretch() # Pushes everything up
        self.main_layout.addWidget(self.sidebar)

    def setup_content_area(self):
        # Right Side Content
        self.content = QWidget()
        layout = QVBoxLayout(self.content)
        
        # Header
        header = QLabel("DASHBOARD")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(header)
        
        layout.addStretch()
        self.main_layout.addWidget(self.content)
"""

# ==========================================
# 2. SNAPSHOT & BACKUP SYSTEM
# ==========================================

# 2.1 snapshot/scripts/backup_manager.py
CODE_BACKUP_SCRIPT = """import shutil
import os
import datetime
import zipfile

def create_backup():
    # Config
    # Assuming this script is in project/snapshot/scripts/
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    BACKUP_DIR = os.path.join(PROJECT_ROOT, 'snapshot', 'backups')
    
    TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ZIP_NAME = f"DSR_PRO_Backup_{TIMESTAMP}.zip"
    ZIP_PATH = os.path.join(BACKUP_DIR, ZIP_NAME)

    # Ignore these folders to keep backup small
    IGNORE_FOLDERS = {'.git', '__pycache__', 'venv', 'env', 'backups', 'dist', 'build', '.idea', '.vscode'}
    IGNORE_EXTENSIONS = {'.pyc', '.tmp', '.log'}

    print(f"--- STARTING BACKUP ---")
    print(f"Target: {ZIP_PATH}")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # modify dirs in-place to skip ignored folders
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            
            # Don't backup the backups folder itself (recursive loop prevention)
            if 'snapshot\\\\backups' in root or 'snapshot/backups' in root:
                continue
            
            for file in files:
                if any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                    continue
                
                file_path = os.path.join(root, file)
                # Archive name should be relative to project root
                arcname = os.path.relpath(file_path, PROJECT_ROOT)
                zipf.write(file_path, arcname)
                
    print(f"✅ Backup Successful! Size: {os.path.getsize(ZIP_PATH) / 1024 / 1024:.2f} MB")
    print(f"Location: {ZIP_PATH}")

if __name__ == "__main__":
    create_backup()
"""

# 2.2 snapshot/reports/EXECUTIVE_STATUS.md
CODE_STATUS_REPORT = """# 📊 DSR PRO AI - Executive Project Status

**Date:** {DATE}
**Version:** 0.1.0 (Migration Phase)
**Project Lead:** [Your Name]

---

## 🚀 1. Executive Summary
**Current State:** Migration from Flet to PySide6 (Qt).
**Health:** 🟢 On Track
**Key Achievement:** Core architecture re-designed for 30,000+ image capacity using Virtualization.

## 🎯 2. Roadmap & Milestones

| Phase | Module | Status | Completion % |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Core Setup (PySide6)** | 🟡 In Progress | 40% |
| **Phase 2** | **UI Shell (Dark Mode)** | 🔴 Pending | 0% |
| **Phase 3** | **Grid Engine (Virtual)**| 🔴 Pending | 0% |
| **Phase 4** | **AI Integration** | 🟢 Ready (Old) | 100% |

## ⚠️ 3. Risks & Blockers
* **Previous:** Flet framework limitation (Arrow Keys/Performance).
* **Resolution:** Migrated to PySide6. Arrow key support is now native.
* **Current Risk:** Learning curve for Qt Model/View programming (High Complexity).

## 📝 4. Pending Tasks (To-Do)
- [ ] Verify `setup_project.py` execution.
- [ ] Copy `database_manager.py` from Old Project.
- [ ] Implement `QListView` for 30k image handling.
- [ ] Design "Gold/Black" CSS Theme.
"""

# ==========================================
# 3. SCRIPT EXECUTION LOGIC
# ==========================================

def create_structure():
    print(f"--- INITIALIZING PROJECT: {PROJECT_NAME} ---")
    
    # 1. Folder Hierarchy
    folders = [
        PROJECT_NAME,
        f"{PROJECT_NAME}/ui",
        f"{PROJECT_NAME}/core",
        f"{PROJECT_NAME}/assets",
        f"{PROJECT_NAME}/database",
        f"{PROJECT_NAME}/snapshot",          
        f"{PROJECT_NAME}/snapshot/backups",  
        f"{PROJECT_NAME}/snapshot/reports",  
        f"{PROJECT_NAME}/snapshot/scripts"   
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Created dir:  {folder}")
        else:
            print(f"⚠️  Dir exists:  {folder}")

    # 2. File Generation
    files = {
        f"{PROJECT_NAME}/requirements.txt": CODE_REQUIREMENTS,
        f"{PROJECT_NAME}/main.py": CODE_MAIN,
        f"{PROJECT_NAME}/ui/styles.py": CODE_STYLES,
        f"{PROJECT_NAME}/ui/mainwindow.py": CODE_MAINWINDOW,
        f"{PROJECT_NAME}/ui/__init__.py": "",
        f"{PROJECT_NAME}/core/__init__.py": "",
        # New Snapshot Files
        f"{PROJECT_NAME}/snapshot/scripts/backup_manager.py": CODE_BACKUP_SCRIPT,
        f"{PROJECT_NAME}/snapshot/reports/EXECUTIVE_STATUS.md": CODE_STATUS_REPORT.format(DATE=datetime.date.today())
    }

    for filepath, content in files.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Created file: {filepath}")

    print("\n--- SETUP COMPLETE ---")
    print(f"📂 New Folder: {PROJECT_NAME}")
    print(f"▶️  Run App:    python {PROJECT_NAME}/main.py")
    print(f"💾 Backup:     python {PROJECT_NAME}/snapshot/scripts/backup_manager.py")
    print(f"📊 Status:     Open {PROJECT_NAME}/snapshot/reports/EXECUTIVE_STATUS.md")

if __name__ == "__main__":
    create_structure()