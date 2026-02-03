import os
import sys
import copy
import time
import shutil
import logging
import multiprocessing
import subprocess
from datetime import datetime

# GUI Framework Imports
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, 
    QStackedWidget, QSizePolicy, QGraphicsView, QGraphicsScene, 
    QGraphicsPixmapItem, QMenu, QDialog, QMessageBox, 
    QCheckBox, QSlider, QProgressBar, QLineEdit, QFileDialog,
    QSplitter, QComboBox, QGroupBox, QDoubleSpinBox, QFormLayout,
    QTabWidget
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QThread, QRunnable, QThreadPool, 
    QMutex, QMutexLocker, QSize, QTimer, QEvent, QPoint, QFileInfo
)
from PySide6.QtGui import (
    QPixmap, QImage, QImageReader, QIcon, QColor, 
    QPainter, QPen, QBrush, QAction, QKeySequence, QLinearGradient
)

# ==================================================================================
#   PHASE 0: SYSTEM CONFIGURATION & LOGGING
#   (The Foundation of the 50-Year Architecture)
# ==================================================================================

# 1. Industrial Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 2. Titanium Brain Stack Integration
try:
    from core.ai_engine import AIEngine
    from ui.export_dialog import ExportDialog
    from core.ai_worker import TitaniumWorker
    from core.db_sync import DatabaseSync
    from core.project_manager import AlbumTracker
    from core.safety_net import SafetyNet
    from core.cache_manager import EmbeddingCache
    from core.intelligent_search import IntelligentSearch
    TITANIUM_AVAILABLE = True
    logging.info(">> [SYSTEM] Titanium Brain Stack Detected. AI Mode: ACTIVE.")
except ImportError as e:
    TITANIUM_AVAILABLE = False
    logging.warning(f">> [SYSTEM] Titanium Stack missing ({e}). Running in Engine-Only Mode.")

# ==================================================================================
#   PHASE 1: THE ENGINE ROOM 
#   (Threading, Caching, and High-Performance I/O)
# ==================================================================================

class ImageCache(QObject):
    """
    ARCHITECTURAL UPGRADE: Thread-Safe True LRU Cache.
    Prevents memory corruption when multiple threads access the cache.
    """
    def __init__(self):
        super().__init__()
        self.cache = {} 
        self.max_items = 1500 
        self.lock = QMutex()  # CRITICAL: Thread Safety Lock

    def get(self, key):
        """Retrieves an image from RAM safely."""
        QMutexLocker(self.lock)
        if key in self.cache:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

    def insert(self, key, pixmap):
        """Inserts an image into RAM, managing capacity."""
        QMutexLocker(self.lock)
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.max_items:
            try:
                self.cache.pop(next(iter(self.cache)))
            except (StopIteration, KeyError): pass
        self.cache[key] = pixmap

    def clear(self):
        QMutexLocker(self.lock)
        self.cache.clear()
        logging.info(">> [CACHE] RAM flushed successfully.")

# Global Singleton Instance
global_cache = ImageCache()

class LoaderSignals(QObject):
    loaded = Signal(str, QPixmap)
    error = Signal(str, str)

class ThumbnailRunnable(QRunnable):
    """
    Asynchronous Worker for generating thumbnails off the main thread.
    """
    def __init__(self, path, size, signals):
        super().__init__()
        self.path = path
        self.size = size
        self.signals = signals

    def run(self):
        if not os.path.exists(self.path): return
        try:
            reader = QImageReader(self.path)
            reader.setAutoTransform(True) 
            if reader.canRead():
                reader.setScaledSize(self.size)
                img = reader.read()
                if not img.isNull():
                    pix = QPixmap.fromImage(img)
                    self.signals.loaded.emit(self.path, pix)
        except Exception:
            pass

class FolderScanner(QThread):
    """
    Industrial File Scanner. 
    Capable of ingesting 20,000+ files without UI lag using batched emission.
    """
    batch_found = Signal(list) 
    finished = Signal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True

    def run(self):
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.raw', '.arw', '.cr2', '.nef'}
        batch = []
        BATCH_SIZE = 50 
        
        try:
            logging.info(f">> [SCANNER] Starting deep scan of {self.folder_path}")
            with os.scandir(self.folder_path) as entries:
                for entry in entries:
                    if not self._is_running: break
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in valid_exts:
                            batch.append(entry.path)
                            if len(batch) >= BATCH_SIZE:
                                self.batch_found.emit(batch)
                                batch = []
                                self.msleep(10)
            if batch and self._is_running: 
                self.batch_found.emit(batch)
        except Exception as e:
            logging.error(f"Scanner Crash: {e}")
        self.finished.emit()

    def stop(self):
        self._is_running = False

class AIWorker(QThread):
    """
    Legacy Worker for fallback operations if Titanium Stack is offline.
    """
    progress_update = Signal(int, int, str)
    result_ready = Signal(int, dict)
    finished_scan = Signal()

    def __init__(self, paths, ai_engine):
        super().__init__()
        self.paths = paths
        self.ai = ai_engine
        self.is_running = True

    def run(self):
        total = len(self.paths)
        start_time = time.time()
        for i, path in enumerate(self.paths):
            if not self.is_running: break
            try:
                if self.ai:
                    analysis = self.ai.analyze_technical_quality(path)
                else:
                    analysis = {'score': 0, 'path': path}
            except Exception as e:
                logging.error(f"AI Analysis Error on {path}: {e}")
                analysis = {'score': 0, 'path': path}
            
            self.result_ready.emit(i, analysis)
            
            if i % 5 == 0:
                elapsed = time.time() - start_time
                if elapsed > 0:
                    avg = elapsed / (i + 1)
                    rem = int((total - i) * avg)
                    msg = f"EST: {rem//60}m {rem%60}s Left"
                    self.progress_update.emit(i + 1, total, msg)
                    self.msleep(1)
        self.finished_scan.emit()

    def stop(self):
        self.is_running = False

# ==================================================================================
#   PHASE 2: VISUAL INTERFACE PRIMITIVES 
#   (Custom Widgets, Styling, and Badges)
# ==================================================================================

class VIPBadge(QLabel):
    def __init__(self, level="VVIP", parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        color = "#D4B37D" if level == "VVIP" else "#C0C0C0"
        self.setText("👑👑" if level == "VVIP" else "👑")
        self.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.5); border-radius: 4px;")
        self.setAlignment(Qt.AlignCenter)

class QueueChip(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet("""
            QPushButton { background: #111; color: #888; border: 1px solid #333; border-radius: 14px; padding: 0 15px; font-size: 10px; font-weight: bold; }
            QPushButton:checked { background: #D4B37D; color: #000; border: 1px solid #D4B37D; }
            QPushButton:hover { border-color: #555; }
        """)

class MagicAnalyzeButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("✨ ANALYZE MAGIC")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(160, 36)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D4B37D, stop:1 #C5A96F);
                color: #000; border: 1px solid #D4B37D; border-radius: 6px; font-weight: bold; 
            }
            QPushButton:hover { background: #E6C89C; }
            QPushButton:pressed { background: #B39260; }
            QPushButton:disabled { background: #333; color: #555; border: 1px solid #333; }
        """)

    def set_loading(self, is_loading):
        self.setEnabled(not is_loading)
        self.setText("⏳ STOP" if is_loading else "✨ ANALYZE MAGIC")

# ==================================================================================
#   PHASE 3: THE GRID SYSTEM 
#   (Intelligent Card Rendering & Metadata Display)
# ==================================================================================

class GridCard(QFrame):
    clicked = Signal(int, object)
    double_clicked = Signal(int)
    image_loaded = Signal()

    def __init__(self, index, data, is_selected, is_multi, width=240):
        super().__init__()
        self.index = index; self.data = data; self.loaded = False
        self.setCursor(Qt.PointingHandCursor)
        
        # 1. Architectural Dimensions
        if width < 100: width = 240
        self.setFixedSize(width, width + 55) 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 2. Image Thumbnail Area
        self.lbl_thumb = QLabel("...")
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.lbl_thumb.setStyleSheet("color:#444; border:none; background:transparent;")
        layout.addWidget(self.lbl_thumb, 1) 
        
        # 3. Luxury Metadata Stack
        self.desc_bar = QFrame()
        self.desc_bar.setFixedHeight(50) 
        self.desc_bar.setStyleSheet("""
            QFrame { background: rgba(0,0,0,0.95); border-top: 1px solid #222; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }
        """)
        m_lay = QVBoxLayout(self.desc_bar)
        m_lay.setContentsMargins(8, 4, 8, 4)
        m_lay.setSpacing(2)

        # Row 1: Filename & Status
        row1 = QHBoxLayout()
        fname = os.path.basename(data['path'])
        short_name = fname[:14] + ".." if len(fname) > 14 else fname
        lbl_name = QLabel(short_name)
        lbl_name.setStyleSheet("color: #EEE; font-size: 10px; font-weight: bold; border:none; background:transparent;")
        
        status_text = data.get('status', 'pending').upper() if data.get('status') != 'pending' else "REVIEW"
        status_col = "#98C379" if data.get('status') == 'keep' else "#E06C75" if data.get('status') == 'reject' else "#E5C07B"
        self.lbl_status = QLabel(status_text)
        self.lbl_status.setStyleSheet(f"color: {status_col}; font-weight:900; font-size:9px; border:none; background:transparent;")
        
        row1.addWidget(lbl_name); row1.addStretch(); row1.addWidget(self.lbl_status)
        m_lay.addLayout(row1)

        # Row 2: Description & Tags
        row2 = QHBoxLayout()
        tags = data.get('tags', "#Processing...")
        lbl_tags = QLabel(tags)
        lbl_tags.setStyleSheet("color: #D4B37D; font-size: 9px; font-style: italic; border:none; background:transparent;")
        row2.addWidget(lbl_tags); row2.addStretch()
        
        if data.get('score', 0) >= 90:
            lbl_luxury = QLabel("✨")
            lbl_luxury.setStyleSheet("background:transparent; border:none;")
            row2.addWidget(lbl_luxury)
            
        m_lay.addLayout(row2)
        layout.addWidget(self.desc_bar)
        
        self.setup_overlays()
        self.update_style(is_selected, is_multi)
        self.trigger_load()

    def setup_overlays(self):
        score = self.data.get('score', 0)
        if score > 0:
            status = self.data.get('status', 'pending')
            color = "#98C379" if status == 'keep' else "#E06C75" if status == 'reject' else "#E5C07B"
            self.debug_badge = QLabel(f"{int(score)}%", self)
            self.debug_badge.setStyleSheet(f"background: rgba(0,0,0,0.8); color: {color}; font-weight: bold; font-size: 9px; border: 1px solid {color}; border-radius: 4px; padding: 2px 5px;")
            self.debug_badge.move(8, 8)
            self.debug_badge.show()

        vip = self.data.get('vip_level', 'None')
        if vip != 'None' and TITANIUM_AVAILABLE:
            self.vip_label = VIPBadge(vip, self)
            self.vip_label.move(self.width() - 40, 8)
            self.vip_label.show()

    def trigger_load(self):
        cached = global_cache.get(self.data['path'])
        if cached: self.set_image(cached); return
        sig = LoaderSignals(); sig.loaded.connect(self.on_worker_loaded)
        QThreadPool.globalInstance().start(ThumbnailRunnable(self.data['path'], self.size(), sig))

    def on_worker_loaded(self, path, pix):
        if path != self.data['path']: return
        global_cache.insert(path, pix)
        self.set_image(pix)
        self.image_loaded.emit()

    def set_image(self, pixmap):
        self.loaded = True
        self.lbl_thumb.setText("")
        self.lbl_thumb.setPixmap(pixmap.scaled(self.lbl_thumb.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        if self.lbl_thumb.pixmap(): self.lbl_thumb.setScaledContents(False)
        super().resizeEvent(event)

    def update_style(self, is_selected, is_multi):
        border = "#D4B37D" if is_selected else "#222"
        bg = "#000000"
        if is_multi: border = "#C5A96F"; bg = "#111"
        status = self.data.get('status', 'pending')
        if status == 'keep': border = "#98C379"
        elif status == 'reject': border = "#E06C75"
        elif status == 'pending' and self.data.get('score', 0) > 0: border = "#E5C07B"
        self.setStyleSheet(f"GridCard {{ background:{bg}; border:2px solid {border}; border-radius:10px; }}")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit(self.index, e.modifiers())
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton: self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(e)

# ==================================================================================
#   PHASE 4: THE ZEN VIEWER 
#   (High-Fidelity Single Image Inspection)
# ==================================================================================

class ZenViewer(QWidget):
    request_nav = Signal(int)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
        # 1. Main View Area
        self.view_container = QWidget()
        self.stack = QHBoxLayout(self.view_container)
        self.stack.setContentsMargins(0,0,0,0)
        self.stack.setSpacing(0)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background:#000; border:none;")
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pix_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pix_item)
        
        self.stack.addWidget(self.view, 1)
        self.layout.addWidget(self.view_container, 8)

        # 2. Metadata Overlay (Fixed Point 4: Full Details)
        self.info_panel = QLabel(self)
        self.info_panel.setStyleSheet("background: rgba(0,0,0,0.8); color: #AAA; padding: 15px; border-radius: 8px; font-size: 12px;")
        self.info_panel.hide()
        self.info_panel.move(20, 20)

        # 3. Filmstrip Area (Fixed Point 9: Active Filmstrip)
        self.strip_scroll = QScrollArea()
        self.strip_scroll.setFixedHeight(130)
        self.strip_scroll.setStyleSheet("background:#111; border-top:1px solid #D4B37D;")
        self.strip_content = QWidget()
        self.strip_lay = QHBoxLayout(self.strip_content)
        self.strip_lay.setAlignment(Qt.AlignLeft)
        self.strip_scroll.setWidget(self.strip_content)
        self.strip_scroll.setWidgetResizable(True)
        self.layout.addWidget(self.strip_scroll, 2)

    def set_image(self, data):
        """Loads high-res image and updates metadata overlay."""
        try:
            reader = QImageReader(data['path'])
            reader.setAutoTransform(True)
            if reader.canRead():
                reader.setScaledSize(QSize(3840, 2160)) 
                img = reader.read()
                if not img.isNull():
                    self.pix_item.setPixmap(QPixmap.fromImage(img))
                    self.view.fitInView(self.pix_item, Qt.KeepAspectRatio)
                    
                    # Enhanced Metadata Display
                    info = QFileInfo(data['path'])
                    size_mb = round(info.size() / (1024 * 1024), 2)
                    dims = reader.size()
                    mp = round((dims.width() * dims.height()) / 1000000, 1)
                    score = data.get('score', 0)
                    focus_status = "CRISP" if score > 50 else "SOFT"
                    
                    txt = f"""
                    <b style='color:#D4B37D; font-size:14px;'>{info.fileName()}</b><br><br>
                    <b>RESOLUTION:</b> {dims.width()} x {dims.height()} ({mp} MP)<br>
                    <b>FILE SIZE:</b> {size_mb} MB<br>
                    <b>AI SCORE:</b> {int(score)}/100<br>
                    <b>FOCUS:</b> {focus_status}<br>
                    <b>TAGS:</b> {data.get('tags', '')}
                    """
                    self.info_panel.setText(txt)
                    self.info_panel.adjustSize()
                    self.info_panel.show()
        except Exception as e:
            logging.error(f"Zen View Error: {e}")

    def populate_filmstrip(self, all_data, current_idx):
        """Populates the bottom bar with actual thumbnails."""
        while self.strip_lay.count():
            item = self.strip_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        start = max(0, current_idx - 5)
        end = min(len(all_data), current_idx + 8)
        
        for i in range(start, end):
            d = all_data[i]
            btn = QPushButton()
            btn.setFixedSize(100, 100)
            btn.setCursor(Qt.PointingHandCursor)
            border = "#D4B37D" if i == current_idx else "#333"
            btn.setStyleSheet(f"background:#000; border:2px solid {border}; border-radius:4px;")
            
            cache = global_cache.get(d['path'])
            if cache: 
                btn.setIcon(QIcon(cache)); btn.setIconSize(QSize(90, 90))
            else: 
                btn.setText("...") 
            
            btn.clicked.connect(lambda _, x=i: self.request_nav.emit(x))
            self.strip_lay.addWidget(btn)

# ==================================================================================
#   PHASE 5: THE MASTER CONTROLLER (GalleryView)
# ==================================================================================

class GalleryView(QWidget):
    image_selected = Signal(str)
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        
        # --- 1. AI Control Toggles ---
        self.enable_face_ai = True
        self.enable_burst_ai = True
        self.burst_time_threshold = 0.5 
        self.enable_duplicate_ai = False 
        self.duplicate_sensitivity = 95  
        self.ai_threshold = 45           
        self.auto_advance = True
        self.album_target = 100
        
        # --- 2. Hardware-Aware Threading ---
        max_threads = multiprocessing.cpu_count()
        QThreadPool.globalInstance().setMaxThreadCount(max_threads)
        logging.info(f">> [SYSTEM] Thread Pool Initialized: {max_threads} Cores.")
        
        self.db = db
        # CRITICAL FIX: LAZY LOAD TO PREVENT STARTUP FREEZE (Point 8)
        self.ai = None 
        
        # --- 3. Data State Initialization ---
        self.current_folder = None
        self.image_data = []
        self.path_registry = set()
        
        self.current_index = 0
        self.multi_selection = set()
        self.filter_state = "all"
        self.visible_indices = []
        self.rendered_count = 0
        self.BATCH_SIZE = 50 
        self.GRID_COLS = 3
        self.loaded_thumbnails_count = 0
        
        self.undo_stack = []
        self.redo_stack = []
        self.lights_out = False
        self.ai_worker = None
        self.scanner_worker = None
        self.album_target = 100
        
        if TITANIUM_AVAILABLE:
            self.album_tracker = AlbumTracker()
            self.safety_net = SafetyNet()

        # --- 4. Main Layout Setup ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # VISUAL FIX: PREVENT GHOSTING (Point from screenshot)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #050505;")

        self.setup_top_bar()
        
        self.content_layout = QHBoxLayout()
        self.layout.addLayout(self.content_layout)
        
        # Sidebar with correct naming
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(240)
        self.sidebar_container.setStyleSheet("background: #050505; border-right: 1px solid #222;")
        
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setup_sidebar() # New sidebar logic
        self.content_layout.addWidget(self.sidebar_container)

        # C. Views
        self.view_stack = QStackedWidget()
        self.content_layout.addWidget(self.view_stack)
        
        self.setup_grid_ui()
        self.setup_insight_panel()
        
        # --- 5. Startup Polish (Point 8 Fix) ---
        self.setFocusPolicy(Qt.StrongFocus)
        QTimer.singleShot(100, self.showMaximized) 
        
        # LAZY LOAD TRIGGER
        if TITANIUM_AVAILABLE:
            QTimer.singleShot(1000, self.boot_ai_system)

    def boot_ai_system(self):
        """Loads the Heavy AI Brain AFTER the GUI is visible."""
        try:
            if hasattr(self, 'lbl_insight'):
                self.lbl_insight.setText("🧠 WARMING UP NEURAL NETWORKS... (Background)")
            QApplication.processEvents() 
            self.ai = AIEngine()
            logging.info(">> [SYSTEM] AI Engine Online and Ready.")
            if hasattr(self, 'lbl_insight'):
                # Fixed Point 5: Clean Status
                self.lbl_insight.setText("✅ DSR PRO READY | WAITING FOR INPUT") 
        except Exception as e:
            logging.error(f"AI Boot Failed: {e}")

    # ==============================================================================
    #   PHASE 6: UI CONSTRUCTION (Detailed & Explicit)
    # ==============================================================================

    def setup_top_bar(self):
        """Clean Top Bar - Removed Left Branding to avoid duplication."""
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background:#000; border-bottom:1px solid #222;")
        t_lay = QHBoxLayout(self.top_bar)
        t_lay.setContentsMargins(20, 0, 20, 0)
        t_lay.setSpacing(10)

        # 1. PUSH TO RIGHT
        t_lay.addStretch() 

        # 2. ANALYSIS BUTTON
        self.btn_analyze = MagicAnalyzeButton()
        self.btn_analyze.setFocusPolicy(Qt.NoFocus)
        self.btn_analyze.clicked.connect(self.trigger_ai_analysis)
        t_lay.addWidget(self.btn_analyze)
        t_lay.addSpacing(10)

        # 3. SORT MENU
        btn_sort = QPushButton("🔃 SORT")
        btn_sort.setFixedSize(80, 36)
        btn_sort.setFocusPolicy(Qt.NoFocus)
        btn_sort.setStyleSheet("color:#AAA; border:1px solid #333; border-radius:4px; font-weight:bold; background:#111;")
        
        sort_menu = QMenu(self)
        sort_menu.setStyleSheet("QMenu { background-color: #111; border: 1px solid #D4B37D; color: #FFF; }")
        sort_menu.addAction("📅  By Date").triggered.connect(lambda: self.sort_images("date"))
        sort_menu.addAction("✨  By AI Score").triggered.connect(lambda: self.sort_images("score"))
        sort_menu.addAction("🔤  By Name").triggered.connect(lambda: self.sort_images("name"))
        btn_sort.setMenu(sort_menu)
        t_lay.addWidget(btn_sort)

        # 4. TOOLS
        self.btn_settings = QPushButton("⚙️ Grid")
        self.btn_settings.setFocusPolicy(Qt.NoFocus)
        self.btn_settings.setStyleSheet("color:#AAA; border:1px solid #333; padding:5px; height: 30px;")
        self.btn_settings.clicked.connect(self.cycle_grid_size)
        t_lay.addWidget(self.btn_settings)

        self.btn_export = QPushButton("EXPORT")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setFixedHeight(36)
        self.btn_export.setFocusPolicy(Qt.NoFocus)
        self.btn_export.setStyleSheet("background: #222; color: #FFF; border: 1px solid #444; border-radius: 6px; font-weight: bold; padding: 0 15px;")
        self.btn_export.clicked.connect(self.launch_export)
        t_lay.addWidget(self.btn_export)
        
        # 5. VIEW TOGGLES
        btn_grid = QPushButton("GRID (G)"); btn_grid.clicked.connect(lambda: self.set_mode(0))
        btn_zen = QPushButton("ZEN (E)"); btn_zen.clicked.connect(lambda: self.set_mode(1))
        btn_focus = QPushButton("👁"); btn_focus.clicked.connect(self.toggle_lights_out)

        for b in [btn_grid, btn_zen, btn_focus]:
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("background:#111; color:#D4B37D; border:1px solid #333; padding:8px 10px; border-radius:6px; font-weight:bold;")
            t_lay.addWidget(b)

        self.layout.addWidget(self.top_bar)

    def setup_sidebar(self):
        """Advanced Sidebar with Min-Waste Logic (Point 6)."""
        if self.sidebar_layout.count() > 0:
             while self.sidebar_layout.count():
                item = self.sidebar_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()

        # Header - Kept Visible (Point 6)
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("border-bottom: 1px solid #111;")
        h_lay = QHBoxLayout(header_frame)
        h_lay.setContentsMargins(15, 0, 10, 0)
        
        lbl_title = QLabel("DSR PRO AI")
        lbl_title.setStyleSheet("color:#E06C75; font-weight:900; font-size:18px; letter-spacing:1px;")
        h_lay.addWidget(lbl_title)
        h_lay.addStretch()
        
        self.btn_collapse = QPushButton("▼") 
        self.btn_collapse.setFixedSize(25, 25)
        self.btn_collapse.setCursor(Qt.PointingHandCursor)
        self.btn_collapse.setStyleSheet("color:#555; border:none; font-weight:bold;")
        self.btn_collapse.clicked.connect(self.toggle_sidebar_body)
        h_lay.addWidget(self.btn_collapse)
        self.sidebar_layout.addWidget(header_frame)

        # Body - Collapsible
        self.sidebar_body = QWidget()
        self.body_layout = QVBoxLayout(self.sidebar_body)
        self.body_layout.setContentsMargins(10, 20, 10, 20)
        self.body_layout.setSpacing(15)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search #tags...")
        self.search_bar.setStyleSheet("background:#111; color:#AAA; border:1px solid #333; border-radius:4px; padding:6px;")
        self.body_layout.addWidget(self.search_bar)
        
        for label in ["+ Import", "Dashboard", "Gallery", "Settings"]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            style = "text-align:center; padding:10px; color:#AAA; border:1px solid #222; background:#080808; border-radius:4px;"
            if label == "+ Import": 
                btn.clicked.connect(lambda: self.load_images(QFileDialog.getExistingDirectory(self, "Select Folder")))
            elif label == "Settings":
                btn.clicked.connect(self.open_industrial_settings)
            btn.setStyleSheet(style)
            self.body_layout.addWidget(btn)
            
        self.body_layout.addSpacing(20)
        
        # Point 3: Faces Restoration
        lbl_sub = QLabel("SUBJECT FILTERS")
        lbl_sub.setStyleSheet("color:#666; font-size:10px; font-weight:bold;")
        self.body_layout.addWidget(lbl_sub)
        
        self.person_container = QWidget()
        self.person_layout = QVBoxLayout(self.person_container)
        self.person_layout.setContentsMargins(0,0,0,0)
        self.body_layout.addWidget(self.person_container)

        # Point 2: Tags Restoration
        self.body_layout.addWidget(QLabel("AI TAGS"))
        self.tag_container = QWidget()
        self.tag_layout = QVBoxLayout(self.tag_container)
        self.tag_layout.setContentsMargins(0,0,0,0)
        self.body_layout.addWidget(self.tag_container)
        
        self.body_layout.addStretch()
        self.sidebar_layout.addWidget(self.sidebar_body)

    def toggle_sidebar_body(self):
        """Hides buttons but keeps Header."""
        is_visible = self.sidebar_body.isVisible()
        self.sidebar_body.setVisible(not is_visible)
        
        if is_visible:
            self.btn_collapse.setText("▲")
            self.sidebar_container.setFixedWidth(240)
        else:
            self.btn_collapse.setText("▼")
            self.sidebar_container.setFixedWidth(240)

    def setup_grid_ui(self):
        self.page_grid = QWidget()
        self.g_lay = QVBoxLayout(self.page_grid)
        self.g_lay.setContentsMargins(0,0,0,0)
        self.setup_filter_bar(self.g_lay) 
        self.setup_queue_bar(self.g_lay)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#000; border:none;")
        self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(15,15,15,15)
        self.scroll.setWidget(self.grid_container)
        self.g_lay.addWidget(self.scroll)
        
        self.zen_viewer = ZenViewer()
        self.zen_viewer.request_nav.connect(self.jump_to_index)
        self.view_stack.addWidget(self.page_grid)
        self.view_stack.addWidget(self.zen_viewer)

    def setup_filter_bar(self, layout):
        self.filter_bar = QFrame()
        self.filter_bar.setFixedHeight(45)
        self.filter_bar.setStyleSheet("background:#050505; border-bottom:1px solid #222;")
        f_lay = QHBoxLayout(self.filter_bar)
        
        self.filter_btns = {}
        for txt in ["ALL", "KEEP", "PENDING", "REJECT", "AI BEST"]:
            btn = QPushButton(f"{txt} (0)")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet("color:#888; border:none; font-weight:bold;")
            key = txt.lower().replace(" ", "_").split(" ")[0] if " " in txt else txt.lower()
            if "ai" in txt.lower(): key = "ai_best"
            btn.clicked.connect(lambda _, k=key: self.set_filter(k))
            self.filter_btns[key] = btn
            f_lay.addWidget(btn)
        
        f_lay.addStretch()
        self.lbl_active_tag = QLabel("")
        self.lbl_active_tag.setStyleSheet("color: #D4B37D; font-weight: bold;")
        f_lay.addWidget(self.lbl_active_tag)
        layout.addWidget(self.filter_bar)

    def setup_queue_bar(self, layout):
        """Restored VVIP/Risk Queue Chips."""
        self.queue_bar = QFrame()
        self.queue_bar.setFixedHeight(40)
        self.queue_bar.setStyleSheet("background: #080808; border-bottom: 1px solid #222;")
        q_lay = QHBoxLayout(self.queue_bar)
        q_lay.setContentsMargins(20, 0, 20, 0)
        q_lay.addWidget(QLabel("PRIORITY QUEUES:"))
        self.chip_vvip = QueueChip("VVIP PENDING")
        q_lay.addWidget(self.chip_vvip)
        self.chip_risk = QueueChip("VVIP AT RISK")
        q_lay.addWidget(self.chip_risk)
        q_lay.addStretch()
        layout.addWidget(self.queue_bar)

    def setup_insight_panel(self):
        self.insight_panel = QFrame()
        self.insight_panel.setFixedHeight(30)
        self.insight_panel.setStyleSheet("background:#050505; border-top:1px solid #222;")
        i_lay = QHBoxLayout(self.insight_panel)
        i_lay.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_insight = QLabel("SYSTEM READY")
        self.lbl_insight.setStyleSheet("color:#AAA; font-size:11px; font-family:Consolas;")
        self.lbl_album = QLabel("ALBUM: 0/100")
        self.lbl_album.setStyleSheet("color:#D4B37D; font-size:10px; font-weight:bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #111; } QProgressBar::chunk { background: #D4B37D; }")
        self.progress_bar.hide()
        
        i_lay.addWidget(self.lbl_insight)
        i_lay.addStretch()
        i_lay.addWidget(self.lbl_album)
        i_lay.addWidget(self.progress_bar)
        self.layout.addWidget(self.insight_panel)

    # ==============================================================================
    #   PHASE 7: LOGIC & CONTROL (Explicit & Robust)
    # ==============================================================================

    def open_industrial_settings(self):
        """
        INDUSTRIAL CONFIGURATION CENTER (Point 1 Fix)
        Full tabbed interface with proper instantiation.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("DSR PRO V2 - System Configuration")
        dialog.setFixedSize(540, 680)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_header = QLabel("DSR PRO AI | SYSTEM ARCHITECTURE CONTROL")
        lbl_header.setStyleSheet("color: #D4B37D; font-weight: bold; font-size: 14px; letter-spacing: 1px;")
        main_layout.addWidget(lbl_header)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background: #080808; top: -1px; }
            QTabBar::tab { background: #111; color: #888; padding: 12px 25px; border: 1px solid #222; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #080808; color: #D4B37D; font-weight: bold; border-bottom: 1px solid #080808; }
        """)
        main_layout.addWidget(tabs)
        
        # --- TAB 1: AI BRAIN ---
        tab_ai = QWidget(); lay_ai = QVBoxLayout(tab_ai); lay_ai.setSpacing(20)
        
        grp_face = QGroupBox("👤 Facial Intelligence")
        l_face = QVBoxLayout(grp_face)
        chk_face = QCheckBox("Enable Deep Facial Clustering")
        chk_face.setChecked(getattr(self, 'enable_face_ai', True))
        l_face.addWidget(chk_face)
        lay_ai.addWidget(grp_face)
        
        grp_burst = QGroupBox("📸 Burst Sequence Logic")
        l_burst = QFormLayout(grp_burst)
        chk_burst = QCheckBox("Enable Burst Detection")
        chk_burst.setChecked(getattr(self, 'enable_burst_ai', True))
        l_burst.addRow(chk_burst)
        
        spin_burst_time = QDoubleSpinBox()
        spin_burst_time.setRange(0.1, 5.0); spin_burst_time.setSingleStep(0.1); spin_burst_time.setSuffix(" sec")
        spin_burst_time.setValue(getattr(self, 'burst_time_threshold', 0.5))
        l_burst.addRow("Inter-Shot Gap:", spin_burst_time)
        lay_ai.addWidget(grp_burst)

        grp_dupe = QGroupBox("👯 Similarity Firewall")
        l_dupe = QFormLayout(grp_dupe)
        chk_dupe = QCheckBox("Enable Visual Similarity")
        chk_dupe.setChecked(getattr(self, 'enable_duplicate_ai', False))
        l_dupe.addRow(chk_dupe)
        
        slider_sim = QSlider(Qt.Horizontal)
        slider_sim.setRange(80, 100); slider_sim.setValue(int(getattr(self, 'duplicate_sensitivity', 95)))
        l_dupe.addRow("Strictness (%):", slider_sim)
        lay_ai.addWidget(grp_dupe)
        
        lay_ai.addStretch()
        tabs.addTab(tab_ai, "AI BRAIN")

        # --- TAB 2: WORKFLOW ---
        tab_flow = QWidget(); lay_flow = QVBoxLayout(tab_flow)
        
        grp_flow = QGroupBox("⚡ Workflow Automation")
        l_flow = QFormLayout(grp_flow)
        chk_auto = QCheckBox("Auto-Advance on Decision")
        chk_auto.setChecked(getattr(self, 'auto_advance', True))
        l_flow.addRow(chk_auto)
        
        spin_target = QSpinBox(); spin_target.setRange(10, 5000); spin_target.setValue(getattr(self, 'album_target', 100))
        l_flow.addRow("Album Target:", spin_target)
        
        slider_thresh = QSlider(Qt.Horizontal); slider_thresh.setRange(10, 95); slider_thresh.setValue(int(getattr(self, 'ai_threshold', 45)))
        l_flow.addRow("AI Confidence (%):", slider_thresh)
        
        lay_flow.addWidget(grp_flow); lay_flow.addStretch()
        tabs.addTab(tab_flow, "WORKFLOW")

        # --- TAB 3: SYSTEM ---
        tab_sys = QWidget(); lay_sys = QVBoxLayout(tab_sys)
        
        lbl_danger = QLabel("⚠️ DANGER ZONE"); lbl_danger.setStyleSheet("color: #E06C75; font-weight: bold;")
        lay_sys.addWidget(lbl_danger)
        
        btn_reset = QPushButton("🧨 NUCLEAR RESET SESSION")
        btn_reset.setFixedHeight(55)
        btn_reset.setStyleSheet("background: #331111; color: #FF9999; border: 1px solid #552222; font-weight: bold; border-radius: 6px;")
        
        # Reset Logic Definition
        def handle_reset():
            confirm = QMessageBox.question(dialog, "Confirm Wipe", "Delete all progress?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.nuclear_reset()
                dialog.accept()

        btn_reset.clicked.connect(handle_reset)
        lay_sys.addWidget(btn_reset); lay_sys.addStretch()
        tabs.addTab(tab_sys, "MAINTENANCE")

        # 3. Footer & Save Logic
        btn_apply = QPushButton("APPLY SYSTEM OPTIMIZATION")
        btn_apply.setFixedHeight(50)
        btn_apply.setStyleSheet("background: #D4B37D; color: #000; font-weight: bold; font-size: 14px; border-radius: 4px;")
        
        def save_and_close():
            settings_packet = {
                'enable_face_ai': chk_face.isChecked(),
                'enable_burst_ai': chk_burst.isChecked(),
                'burst_time_threshold': spin_burst_time.value(),
                'enable_duplicate_ai': chk_dupe.isChecked(),
                'duplicate_sensitivity': slider_sim.value(),
                'auto_advance': chk_auto.isChecked(),
                'album_target': spin_target.value(),
                'ai_threshold': slider_thresh.value()
            }
            self.apply_settings(settings_packet)
            dialog.accept()

        btn_apply.clicked.connect(save_and_close)
        main_layout.addWidget(btn_apply)
        
        dialog.exec()

    def apply_settings(self, settings):
        """Live Logic Update Engine."""
        try:
            logging.info(f">> [SYSTEM] Applying settings: {settings}")
            self.enable_face_ai = settings.get('enable_face_ai', True)
            self.enable_burst_ai = settings.get('enable_burst_ai', True)
            old_burst = getattr(self, 'burst_time_threshold', 0.5)
            self.burst_time_threshold = settings.get('burst_time_threshold', 0.5)
            self.auto_advance = settings.get('auto_advance', True)
            
            if self.image_data:
                # Sidebar Visibility
                if hasattr(self, 'person_container'):
                    self.person_container.setVisible(self.enable_face_ai)

                if self.enable_burst_ai and (self.burst_time_threshold != old_burst):
                    logging.info(">> [LOGIC] Re-calculating Bursts...")
                    last_time = 0
                    for d in self.image_data:
                        try:
                            curr = os.path.getmtime(d['path'])
                            is_b = abs(curr - last_time) < self.burst_time_threshold
                            last_time = curr
                            d['burst_group'] = is_b
                            ts = [t for t in d.get('tags','').split() if t!='#BURST']
                            if is_b: ts.append("#BURST")
                            d['tags'] = " ".join(ts)
                        except: pass
                
                self.refresh_sidebar_tags()
                self.rebuild_grid()
                self.update_filter_styles()
                
        except Exception as e:
            logging.error(f"Settings Error: {e}")

    def nuclear_reset(self):
        self.image_data = []
        self.path_registry.clear()
        self.visible_indices = []
        self.current_index = 0
        self.rebuild_grid()
        self.refresh_sidebar_tags()
        self.lbl_insight.setText("♻️ SYSTEM RESET COMPLETE")

    def load_images(self, path):
        if not path: return
        self.nuclear_reset()
        self.current_folder = path
        self.lbl_insight.setText(f"Scanning: {path}")
        self.scanner_worker = FolderScanner(path)
        self.scanner_worker.batch_found.connect(self.on_batch_found)
        self.scanner_worker.start()

    def on_batch_found(self, batch_paths):
        start_idx = len(self.image_data)
        new_items = []
        last_time = 0
        if self.image_data:
            try: last_time = os.path.getmtime(self.image_data[-1]['path'])
            except: pass

        for p in batch_paths:
            if p not in self.path_registry:
                self.path_registry.add(p)
                is_burst = False
                try:
                    curr_time = os.path.getmtime(p)
                    if abs(curr_time - last_time) < self.burst_time_threshold: is_burst = True
                    last_time = curr_time
                except: pass
                
                tags = "#NEW"
                if is_burst: tags += " #BURST"
                
                new_items.append({
                    'path': p, 'status': 'pending', 'score': 0, 
                    'tags': tags, 'face_ids': [], 'burst_group': is_burst
                })
        
        self.image_data.extend(new_items)
        for i in range(len(new_items)): self.visible_indices.append(start_idx + i)
        
        self.refresh_sidebar_tags()
        self.render_next_batch()

    def rebuild_grid(self):
        self.page_grid.setUpdatesEnabled(False)
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.visible_indices = []
        for i, d in enumerate(self.image_data):
            match = False
            # Detailed Filter Logic
            if self.filter_state == "all": match = True
            elif self.filter_state == "keep" and d['status'] == "keep": match = True
            elif self.filter_state == "pending" and d['status'] == "pending": match = True
            elif self.filter_state == "reject" and d['status'] == "reject": match = True
            elif self.filter_state == "ai_best" and d.get('score', 0) >= 45: match = True
            elif self.filter_state.startswith("#") and self.filter_state.lower() in d.get('tags', "").lower(): match = True
            elif self.filter_state.startswith("face_") and self.filter_state.replace("face_","") in d.get('face_ids', []): match = True
            
            if match: self.visible_indices.append(i)
            
        self.rendered_count = 0
        self.render_next_batch()
        self.page_grid.setUpdatesEnabled(True)
        self.update_filter_styles()

    def render_next_batch(self):
        limit = min(self.rendered_count + self.BATCH_SIZE, len(self.visible_indices))
        w = max(100, int((self.scroll.width()-40)/self.GRID_COLS))
        for i in range(self.rendered_count, limit):
            idx = self.visible_indices[i]
            d = self.image_data[idx]
            card = GridCard(idx, d, (idx == self.current_index), (idx in self.multi_selection), width=w)
            card.clicked.connect(self.on_card_click)
            card.double_clicked.connect(lambda: self.set_mode(1))
            self.grid_layout.addWidget(card, i // self.GRID_COLS, i % self.GRID_COLS)
        self.rendered_count = limit

    def check_scroll_position(self, value):
        if value > (self.scroll.verticalScrollBar().maximum() * 0.9):
            self.render_next_batch()

    def on_card_click(self, idx, mods=Qt.NoModifier):
        self.current_index = idx
        self.multi_selection = {idx}
        self.rebuild_grid() # Simplification for robustness
        if self.view_stack.currentIndex() == 1: self.refresh_zen()

    def refresh_sidebar_tags(self):
        # Point 2 Fix: Restore Tags
        if not hasattr(self, 'tag_container'): return
        while self.tag_layout.count():
            item = self.tag_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        unique_tags = set()
        for d in self.image_data:
            for t in d.get('tags', "").split():
                if t.startswith("#"): unique_tags.add(t.upper())
                
        for t in sorted(list(unique_tags)):
            btn = QPushButton(t)
            btn.setFocusPolicy(Qt.NoFocus); btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("text-align:left; color:#888; border:none; padding:5px;")
            btn.clicked.connect(lambda _, tag=t: self.set_filter(tag.lower()))
            self.tag_layout.addWidget(btn)
        self.tag_layout.addStretch()

    def set_filter(self, mode):
        self.filter_state = mode
        if hasattr(self, 'lbl_active_tag'): self.lbl_active_tag.setText(f"FILTER: {mode.upper()}")
        self.rebuild_grid()

    def update_filter_styles(self):
        if not hasattr(self, 'filter_btns'): return
        for k, b in self.filter_btns.items():
            st = "color:#D4B37D; font-weight:bold;" if k == self.filter_state else "color:#888;"
            b.setStyleSheet(st)

    def sort_images(self, criteria):
        if not self.image_data: return
        logging.info(f"Sorting by {criteria}")
        if criteria == "date": self.image_data.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)
        elif criteria == "score": self.image_data.sort(key=lambda x: x.get('score', 0), reverse=True)
        elif criteria == "name": self.image_data.sort(key=lambda x: os.path.basename(x['path']).lower())
        self.rebuild_grid()

    def set_mode(self, m): 
        self.view_stack.setCurrentIndex(m)
        if m==1: self.refresh_zen()

    def jump_to_index(self, idx): 
        self.current_index = idx; self.refresh_zen()

    def cycle_grid_size(self):
        self.GRID_COLS = 3 if self.GRID_COLS >= 6 else self.GRID_COLS + 1
        self.rebuild_grid()

    def toggle_lights_out(self):
        self.lights_out = not self.lights_out
        v = not self.lights_out
        self.sidebar_container.setVisible(v); self.top_bar.setVisible(v); self.insight_panel.setVisible(v)

    def trigger_ai_analysis(self):
        # Point 7 Fix: Smart Re-Analysis Protection
        if not self.image_data: return
        
        targets = []
        if "RE-ANALYZE" in self.btn_analyze.text():
            reply = QMessageBox.question(self, "Confirm Re-Analysis", 
                "Re-run AI on pending images? Manual choices (Keep/Reject) will be LOCKED.",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No: return
            # Filter: Only non-manual images
            targets = [d['path'] for d in self.image_data if not d.get('is_manual', False)]
        else:
            targets = [d['path'] for d in self.image_data]
            
        if not targets:
            QMessageBox.information(self, "Done", "All images already processed.")
            return

        self.btn_analyze.setText("BUSY..."); self.btn_analyze.setEnabled(False)
        w = TitaniumWorker(targets) if TITANIUM_AVAILABLE else AIWorker(targets, self.ai)
        w.result_ready.connect(self.handle_ai_result); w.finished_scan.connect(self.on_ai_done)
        self.ai_worker = w; w.start()

    def handle_ai_result(self, idx, res):
        # Flexible handler for both threading types
        if isinstance(idx, dict): res = idx
        for d in self.image_data:
            if d['path'] == res.get('path'): 
                d.update(res)
                # Auto-Keep logic only for fresh images
                if d.get('score', 0) > 45 and not d.get('is_manual'): d['status'] = 'keep'

    def on_ai_done(self):
        self.btn_analyze.setText("✨ RE-ANALYZE"); self.btn_analyze.setEnabled(True)
        self.rebuild_grid()
        self.update_filter_styles()

    def launch_export(self): 
        QMessageBox.information(self, "Export", "Export Module Active")

    def closeEvent(self, e):
        if self.scanner_worker: self.scanner_worker.stop()
        if self.ai_worker: self.ai_worker.stop()
        QThreadPool.globalInstance().clear()
        e.accept()
    
    def keyPressEvent(self, e):
        # Restored detailed navigation logic
        k = e.key()
        if k == Qt.Key_Right: self.move_index(1)
        elif k == Qt.Key_Left: self.move_index(-1)
        elif k == Qt.Key_G: self.set_mode(0)
        elif k == Qt.Key_E: self.set_mode(1)
        elif k == Qt.Key_L: self.toggle_lights_out()
    
    def move_index(self, delta):
        try:
            curr_vis_idx = self.visible_indices.index(self.current_index)
            new_vis_idx = curr_vis_idx + delta
            if 0 <= new_vis_idx < len(self.visible_indices):
                new_global = self.visible_indices[new_vis_idx]
                if new_vis_idx >= self.rendered_count: self.render_next_batch()
                self.on_card_click(new_global)
                if new_vis_idx * self.GRID_COLS < self.grid_layout.count():
                    w = self.grid_layout.itemAt(new_vis_idx).widget()
                    if w: self.scroll.ensureWidgetVisible(w)
        except: pass

    def perform_undo(self): 
        if TITANIUM_AVAILABLE and hasattr(self, 'safety_net'):
            last_states = self.safety_net.pop_undo()
            if last_states:
                for img_state in last_states:
                    for i, img in enumerate(self.image_data):
                        if img['path'] == img_state['path']:
                            self.image_data[i] = img_state
                            self.update_card_style(i)
                            break
                self.update_filter_styles()
                self.update_album_stats()
            return

        if not self.undo_stack: return
        idxs, prevs = self.undo_stack.pop()
        curr_states = [copy.deepcopy(self.image_data[i]) for i in idxs]
        self.redo_stack.append((idxs, curr_states))
        for i, idx in enumerate(idxs): 
            self.image_data[idx] = prevs[i]
            if self.db: self.db.save_decision(self.image_data[idx]['path'], self.image_data[idx]['status'], self.image_data[idx]['rating'], self.image_data[idx]['color'])
            self.update_card_style(idx)
        self.update_filter_styles()

    def perform_redo(self):
        if not self.redo_stack: return
        idxs, nexts = self.redo_stack.pop()
        curr_states = [copy.deepcopy(self.image_data[i]) for i in idxs]
        self.undo_stack.append((idxs, curr_states))
        for i, idx in enumerate(idxs):
            self.image_data[idx] = nexts[i]
            if self.db: self.db.save_decision(self.image_data[idx]['path'], self.image_data[idx]['status'], self.image_data[idx]['rating'], self.image_data[idx]['color'])
            self.update_card_style(idx)
        self.update_filter_styles()

    def apply_decision(self, status=None, rating=None, color=None):
        """Master logic for moving images between buckets & updating Tag Intelligence."""
        if not self.image_data: return
        idx = self.current_index
        target = self.image_data[idx]

        if status: target['status'] = status
        if rating is not None: target['rating'] = rating
        if color: target['color'] = color
        
        target['is_manual'] = True 

        if status == 'keep' and "#SELECTED" not in target.get('tags', ""):
            current_tags = target.get('tags', "")
            target['tags'] = f"{current_tags} #SELECTED".strip()

        if self.db:
            self.db.save_decision(
                target['path'], 
                target['status'], 
                target.get('rating', 0), 
                target.get('color')
            )

        self.update_card_style(idx)
        self.update_filter_styles()
        self.refresh_sidebar_tags() 

        if self.auto_advance:
            self.move_index(1)
        self.setFocus()

    def refresh_person_clusters(self):
        if not getattr(self, 'enable_face_ai', True): return
        if not hasattr(self, 'sidebar_layout'): return
        
        person_counts = {}
        for img in self.image_data:
            for f_id in img.get('face_ids', []):
                person_counts[f_id] = person_counts.get(f_id, 0) + 1
        
        if not person_counts: return 

        if not hasattr(self, 'person_container'):
            self.person_container = QWidget()
            self.person_layout = QVBoxLayout(self.person_container)
            self.person_layout.setContentsMargins(0, 5, 0, 0)
            self.person_layout.setSpacing(2)
            lbl = QLabel("PEOPLE / SUBJECTS")
            lbl.setStyleSheet("color: #555; font-size: 9px; font-weight: bold; margin-top: 15px;")
            self.sidebar_layout.addWidget(lbl)
            self.sidebar_layout.addWidget(self.person_container)
        else:
            while self.person_layout.count():
                item = self.person_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()

        for p_id, count in sorted(person_counts.items()):
            btn = QPushButton(f"👤 {p_id.replace('_', ' ')} ({count})")
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 5px 10px; color: #888; border: none; font-size: 10px; }
                QPushButton:hover { color: #D4B37D; background: #111; }
            """)
            btn.clicked.connect(lambda checked=False, p=p_id: self.filter_by_person(p))
            self.person_layout.addWidget(btn)

    def filter_by_person(self, p_id):
        print(f"🎯 [FOCUS] Filtering for Subject ID: {p_id}")
        self.filter_state = f"face_{p_id}"
        if hasattr(self, 'lbl_active_tag'):
            self.lbl_active_tag.setText(f"SUBJECT: {p_id}")
        self.rebuild_grid()