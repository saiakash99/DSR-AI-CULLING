import os

SIGNAL_FIX = {
    "ui/zen_view.py": """
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

class ZenView(QWidget):
    # This is the missing 'socket' the Controller is looking for
    request_next_pair = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel("ZEN MODE: AI COMPARISON ACTIVE")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #d4af37; font-size: 20px; font-weight: bold;")
        layout.addWidget(self.label)

    def load_images(self, path_a, path_b):
        print(f"⏭️ ZenView loading: {path_a} vs {path_b}")
""",
    "ui/side_navigation.py": """
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Signal

class SideNavigation(QWidget):
    # This socket is required for the filtering logic
    filter_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search #tags or filenames...")
        layout.addWidget(self.search_bar)

        # Simple Tree for Filters
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        smart_filters = QTreeWidgetItem(self.tree, ["Smart Filters"])
        QTreeWidgetItem(smart_filters, ["👑 VVIP Present"])
        QTreeWidgetItem(smart_filters, ["⭐ Best of Burst"])
        
        layout.addWidget(self.tree)
        self.tree.itemClicked.connect(self.emit_filter)

    def emit_filter(self, item, column):
        self.filter_changed.emit({"filter": item.text(0)})
"""
}

def fix_signals():
    print("🔌 Re-wiring UI Signals...")
    for path, code in SIGNAL_FIX.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code.strip())
        print(f"✅ Fixed: {path}")
    print("-" * 30)
    print("🚀 ALIGNMENT COMPLETE. Run 'python connect_gallery.py' now.")

if __name__ == "__main__":
    fix_signals()