import os

PROJECT_FILES = {
    "ui/styles.py": """
GLOBAL_STYLE = \"\"\"
QMainWindow, QWidget, QDialog {
    background-color: #0d0d0d;
    color: #eee;
}
QLineEdit {
    background-color: #1a1a1a;
    border: 1px solid #333;
    color: #eee;
    padding: 8px;
    border-radius: 4px;
}
QPushButton {
    background-color: #d4af37;
    border-radius: 5px;
    padding: 8px;
    color: #000;
    font-weight: bold;
}
\"\"\"
""",
    "core/app_controller.py": """
from ui.main_window import TitaniumMainWindow
from core.db_sync import DatabaseSync

class TitaniumController:
    def __init__(self):
        self.db = DatabaseSync()
        self.window = TitaniumMainWindow()
        self.connect_signals()

    def connect_signals(self):
        # Connecting the wires (Signals to Functions)
        self.window.sidebar.search_bar.textChanged.connect(self.handle_search)
        self.window.sidebar.filter_changed.connect(self.apply_smart_filter)

    def handle_search(self, text):
        print(f"Searching for: {text}")

    def apply_smart_filter(self, filter_dict):
        print(f"Applying filter: {filter_dict}")

    def start_ai_scan(self, paths):
        print(f"🚀 AI Scanning paths: {paths}")
""",
    "ui/batch_bar.py": """
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
class BatchActionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.btn = QPushButton("BATCH ACTIONS")
        layout.addWidget(self.btn)
"""
}

def synchronize():
    print("🔄 MASTER SYNC: Fixing Controller and BatchBar...")
    for path, code in PROJECT_FILES.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code.strip())
        print(f"✅ Synchronized: {path}")
    print("-" * 30)
    print("🚀 SYSTEM ALIGNED. Run 'python connect_gallery.py' now.")

if __name__ == "__main__":
    synchronize()