import os

# Define the missing component and the updated window
FIX_UI_FILES = {
    "ui/status_bar.py": """
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

class TitaniumStatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 1. Project Label
        self.lbl_project = QLabel("PROJECT: WEDDING_JAN_2026")
        self.lbl_project.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 14px; letter-spacing: 1px;")
        
        # 2. AI Status Label (The one causing the crash)
        self.lbl_ai_status = QLabel("● AI Engine: Ready")
        self.lbl_ai_status.setStyleSheet("color: #00ff00; font-size: 12px;")
        
        # 3. Progress Stats
        self.lbl_progress = QLabel("Selections: 0 / 800")
        self.lbl_progress.setStyleSheet("color: #fff; font-weight: bold;")

        # Add to layout
        layout.addWidget(self.lbl_project)
        layout.addStretch()
        layout.addWidget(self.lbl_ai_status)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_progress)

    def update_progress(self, current, target):
        self.lbl_progress.setText(f"Selections: {current} / {target}")
""",
    "ui/main_window.py": """
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from ui.side_navigation import SideNavigation
from ui.virtual_grid import VirtualGrid
from ui.zen_view import ZenView
from ui.status_bar import TitaniumStatusBar  # Import the new component

class TitaniumMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSR PRO V2 | Industrial AI Culler")
        self.resize(1400, 900)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = SideNavigation()
        self.sidebar.setFixedWidth(260)

        # 2. Right Side Container
        right_container = QVBoxLayout()
        right_container.setContentsMargins(0, 0, 0, 0)
        right_container.setSpacing(0)

        # 3. Status Bar (The Fix)
        self.status_bar = TitaniumStatusBar()
        
        # 4. View Stack
        self.view_stack = QStackedWidget()
        self.grid_view = VirtualGrid()
        self.zen_view = ZenView()
        self.view_stack.addWidget(self.grid_view)
        self.view_stack.addWidget(self.zen_view)

        # Assemble Right Side
        right_container.addWidget(self.status_bar)
        right_container.addWidget(self.view_stack)

        # Assemble Main Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addLayout(right_container)
"""
}

def apply_statusbar_fix():
    print("🔧 Installing Status Bar...")
    for path, code in FIX_UI_FILES.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(code.strip())
        print(f"✅ Created/Updated: {path}")
    print("-" * 30)
    print("🚀 REPAIR COMPLETE. Run 'python connect_gallery.py' now.")

if __name__ == "__main__":
    apply_statusbar_fix()