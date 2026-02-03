import os
import copy
import subprocess
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.ai_engine import AIEngine
from ui.export_dialog import ExportDialog

# --- TITANIUM BRAIN STACK IMPORTS ---
try:
    from core.ai_worker import TitaniumWorker
    from core.db_sync import DatabaseSync
    from core.project_manager import AlbumTracker
    from core.safety_net import SafetyNet
    from core.cache_manager import EmbeddingCache
    from core.intelligent_search import IntelligentSearch
    TITANIUM_AVAILABLE = True
except ImportError:
    TITANIUM_AVAILABLE = False
    print("Titanium Stack not found. Running in Engine-Only Mode.")

# ==================================================================================
#   SECTION 1: THE ENGINE (Performance & Caching)
# ==================================================================================

class ImageCache(QObject):
    def __init__(self):
        super().__init__()
        self.cache = {} 
        self.max_items = 1500 

    def get(self, key):
        return self.cache.get(key)

    def insert(self, key, pixmap):
        if len(self.cache) >= self.max_items:
            try:
                first = next(iter(self.cache))
                self.cache.pop(first)
            except (StopIteration, KeyError): pass
        self.cache[key] = pixmap

global_cache = ImageCache()

class LoaderSignals(QObject):
    loaded = Signal(str, QPixmap)

class ThumbnailRunnable(QRunnable):
    def __init__(self, path, size, signals):
        super().__init__()
        self.path = path
        self.size = size
        self.signals = signals

    def run(self):
        if not os.path.exists(self.path): return
        reader = QImageReader(self.path)
        # FIX: AutoTransform handles EXIF rotation (sideways images)
        reader.setAutoTransform(True)
        if reader.canRead():
            reader.setScaledSize(self.size)
            img = reader.read()
            if not img.isNull():
                pix = QPixmap.fromImage(img)
                self.signals.loaded.emit(self.path, pix)

class FolderScanner(QThread):
    batch_found = Signal(list) 
    finished = Signal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.raw', '.arw')
        batch = []
        # Batch size 20 is smoother than 500
        BATCH_SIZE = 20
        
        try:
            with os.scandir(self.folder_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        if entry.name.lower().endswith(valid_exts):
                            batch.append(entry.path)
                            if len(batch) >= BATCH_SIZE:
                                self.batch_found.emit(batch)
                                batch = []
                                self.msleep(15) 
            if batch: self.batch_found.emit(batch)
        except: pass
        self.finished.emit()

# --- LEGACY WORKER (Fallback Safety) ---
class AIWorker(QThread):
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
                analysis = self.ai.analyze_technical_quality(path)
            except AttributeError:
                analysis = {'score': 0, 'focus': 'PENDING', 'eyes': 'N/A'}
            self.result_ready.emit(i, analysis)
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = int((total - i) * avg)
                msg = f"{rem//60}m {rem%60}s Left"
                self.progress_update.emit(i + 1, total, msg)
                self.msleep(1)
        self.finished_scan.emit()

    def stop(self):
        self.is_running = False

# ==================================================================================
#   SECTION 2: LUXURY UI COMPONENTS
# ==================================================================================

class VIPBadge(QLabel):
    def __init__(self, level="VVIP", parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        color = "#D4B37D" if level == "VVIP" else "#C0C0C0"
        text = "👑👑" if level == "VVIP" else "👑"
        self.setText(text)
        self.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.5); border-radius: 4px;")
        self.setAlignment(Qt.AlignCenter)

class ManualMarker(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setText("👤")
        self.setStyleSheet("color: #D4B37D; font-size: 11px; background: rgba(0,0,0,0.6); border-radius: 9px;")
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip("Hand-picked by User")

class ConfidenceDot(QFrame):
    def __init__(self, level="high", parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 8)
        color = {"high": "#98C379", "medium": "#E5C07B", "low": "#E06C75"}.get(level, "#555")
        self.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

class QueueChip(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)
        # FIX: Prevent button from stealing keyboard focus
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
        # FIX: Prevent button from stealing keyboard focus
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

    def update_progress(self, current, total):
        self.setText(f"🧠 {current}/{total}")

# ==================================================================================
#   SECTION 3: GRID CARD (Updated with Metadata Bar & Dynamic Width)
# ==================================================================================

class GridCard(QFrame):
    clicked = Signal(int, object)
    double_clicked = Signal(int)
    image_loaded = Signal()

    def __init__(self, index, data, is_selected, is_multi, width=240):
        super().__init__()
        self.index = index; self.data = data; self.loaded = False
        self.setCursor(Qt.PointingHandCursor)
        
        # FIX: Dynamic width passed from Controller (3x3 alignment)
        if width < 100: width = 240
        self.setFixedSize(width, width)
        
        self.setStyleSheet("background: #111; border: 2px solid #222; border-radius: 10px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        self.lbl_thumb = QLabel("..."); self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.lbl_thumb.setStyleSheet("color:#444; border:none; background:transparent;")
        layout.addWidget(self.lbl_thumb, 1) # Image takes upper space
        
        # FIX: Metadata Description Bar
        self.desc_bar = QFrame()
        self.desc_bar.setFixedHeight(28)
        self.desc_bar.setStyleSheet("background: rgba(0,0,0,0.85); border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        d_lay = QHBoxLayout(self.desc_bar); d_lay.setContentsMargins(8,0,8,0)
        
        fname = os.path.basename(data['path'])
        short_name = fname[:15] + ".." if len(fname) > 15 else fname
        lbl_name = QLabel(short_name)
        lbl_name.setStyleSheet("color: #CCC; font-size: 10px; font-weight: bold; border:none; background:transparent;")
        d_lay.addWidget(lbl_name)
        d_lay.addStretch()
        
        # Status Text in Bar
        status_text = data.get('status', 'pending').upper() if data.get('status') != 'pending' else ""
        status_col = "#98C379" if data.get('status') == 'keep' else "#E06C75" if data.get('status') == 'reject' else "#AAA"
        self.lbl_status = QLabel(status_text)
        self.lbl_status.setStyleSheet(f"color: {status_col}; font-weight:900; font-size:9px; border:none; background:transparent;")
        d_lay.addWidget(self.lbl_status)
        
        layout.addWidget(self.desc_bar)
        
        self.setup_overlays()
        self.update_style(is_selected, is_multi)
        self.trigger_load()

    def setup_overlays(self):
        # Keeps your Luxury Badges
        if self.data.get('vip_level') in ["VIP", "VVIP"]:
            self.vip_badge = VIPBadge(self.data['vip_level'], self)
            self.vip_badge.move(self.width() - 40, 10) 
        
        self.conf_dot = ConfidenceDot(self.data.get('confidence', 'low'), self)
        self.conf_dot.move(12, 12)
        
        if self.data.get('is_manual'):
            self.m_marker = ManualMarker(self)
            self.m_marker.move(10, self.height() - 45) # Above desc bar
        
        if self.data.get('is_burst'):
            burst_lbl = QLabel("🔗", self)
            burst_lbl.setStyleSheet("color:#AAA; font-size:12px; background:rgba(0,0,0,0.5); border-radius:4px;")
            burst_lbl.move(12, 30)
            if self.data.get('is_best_of_burst'):
                best_lbl = QLabel("⭐", self)
                best_lbl.setStyleSheet("color:#D4B37D; font-size:12px;")
                best_lbl.move(30, 30)

        if self.data.get('ai_tags'):
            tag_lbl = QLabel(self.data['ai_tags'][:20], self)
            tag_lbl.setStyleSheet("color:#888; font-size:9px; background:rgba(0,0,0,0.7); padding:2px;")
            tag_lbl.move(10, self.height() - 65)

        self.badge = QLabel("✨ AI", self)
        self.badge.setStyleSheet("background:#D4B37D; color:#000; font-weight:bold; font-size:10px; padding:2px 6px; border-radius:3px;")
        self.badge.move(30, 10)
        self.badge.setVisible(self.data.get('ai_pick', False))
        
        if self.data.get('rating', 0) > 0:
            stars = QLabel("★" * self.data['rating'], self)
            stars.setStyleSheet("color:#FFD700; background:rgba(0,0,0,0.6); font-size:14px; padding:2px 6px; border-radius:4px;")
            stars.setParent(self) # Re-parent to ensure visibility
            stars.move(self.width() - 80, self.height() - 50)

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
        
        c = self.data.get('color')
        colors = {'red': "#2D1414", 'yellow': "#2D2A14", 'green': "#142D19", 'blue': "#141A2D"}
        if c in colors: bg = colors[c]
        
        self.setStyleSheet(f"GridCard {{ background:{bg}; border:2px solid {border}; border-radius:10px; }}")
        if hasattr(self, 'badge'): self.badge.setVisible(self.data.get('ai_pick', False))
        
        # Update text
        if hasattr(self, 'lbl_status'):
            self.lbl_status.setText(status.upper() if status != 'pending' else "")
            col = "#98C379" if status == 'keep' else "#E06C75" if status == 'reject' else "#AAA"
            self.lbl_status.setStyleSheet(f"color: {col}; font-weight:900; font-size:9px; border:none; background:transparent;")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit(self.index, e.modifiers())
        super().mousePressEvent(e)
    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton: self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #111; border: 1px solid #D4B37D; color: #FFF; padding: 5px; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background-color: #D4B37D; color: #000; }")
        act_reveal = menu.addAction("📂  Reveal")
        act_copy = menu.addAction("📋  Copy Path")
        action = menu.exec(e.globalPos())
        path = os.path.normpath(self.data['path'])
        if action == act_reveal: subprocess.Popen(f'explorer /select,"{path}"')
        elif action == act_copy: QApplication.clipboard().setText(path)

# ==================================================================================
#   SECTION 4: ZEN VIEWER (Improved Flow & Direct Load)
# ==================================================================================

class ZenViewer(QGraphicsView):
    double_clicked = Signal()
    def __init__(self):
        super().__init__()
        self.current_path = None 
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setStyleSheet("background:#000; border:none;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pix_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pix_item)

    def set_image(self, path):
        self.current_path = path
        self.resetTransform()
        
        # FIX: Direct Load for Instant Flow
        if os.path.exists(path):
            reader = QImageReader(path)
            reader.setAutoTransform(True)
            if reader.canRead():
                # Cap max size for performance
                reader.setScaledSize(QSize(3840, 2160)) 
                img = reader.read()
                if not img.isNull():
                    self._on_loaded(path, QPixmap.fromImage(img))
                    return

        # Fallback
        sig = LoaderSignals(); sig.loaded.connect(self._on_loaded)
        QThreadPool.globalInstance().start(ThumbnailRunnable(path, QSize(4000, 4000), sig))

    def _on_loaded(self, path, pix):
        if path == self.current_path or self.current_path is None: 
            self.pix_item.setPixmap(pix)
            self.scene.setSceneRect(self.pix_item.boundingRect())
            self.fitInView(self.pix_item, Qt.KeepAspectRatio)

    def wheelEvent(self, e): 
        factor = 1.15 if e.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, e):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e):
        if not self.current_path: return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #111; border: 1px solid #D4B37D; color: #FFF; padding: 5px; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background-color: #D4B37D; color: #000; }")
        act_reveal = menu.addAction("📂  Reveal"); act_copy = menu.addAction("📋  Copy Path")
        menu.addSeparator(); act_search = menu.addAction("🔍  Find Similar Faces")
        action = menu.exec(e.globalPos())
        path = os.path.normpath(self.current_path)
        if action == act_reveal: subprocess.Popen(f'explorer /select,"{path}"')
        elif action == act_copy: QApplication.clipboard().setText(path)
        elif action == act_search: print(f"Triggering Intelligent Search for {path}")

# ==================================================================================
#   SECTION 5: MAIN GALLERY CONTROLLER
# ==================================================================================

class GalleryView(QWidget):
    image_selected = Signal(str) # For Zen Mode sync

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.ai = AIEngine()
        
        self.current_folder = None
        self.image_data = []
        self.current_index = 0
        self.multi_selection = set()
        self.filter_state = "all"
        self.visible_indices = []
        self.rendered_count = 0
        self.BATCH_SIZE = 50 
        self.GRID_COLS = 3 # FIX: Default set to 3 as requested
        self.auto_advance = True
        self.loaded_thumbnails_count = 0
        self.undo_stack = []
        self.redo_stack = []
        self.lights_out = False
        self.ai_worker = None
        self.scanner_worker = None
        self.album_target = 100
        self.is_rendering_batch = False
        
        # Initialize Titanium Modules
        if TITANIUM_AVAILABLE:
            self.album_tracker = AlbumTracker()
            self.safety_net = SafetyNet() # Blueprint #3

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setup_guidance_banner()
        self.setup_top_bar()
        self.setup_queue_bar()
        self.setup_filter_bar() 
        
        self.content_layout = QHBoxLayout()
        self.layout.addLayout(self.content_layout)
        
        self.sidebar_panel = QFrame()
        self.sidebar_panel.setFixedWidth(200)
        self.sidebar_panel.setStyleSheet("background: #050505; border-right: 1px solid #222;")
        self.sidebar_layout = QVBoxLayout(self.sidebar_panel)
        self.setup_sidebar_filters() 
        self.content_layout.addWidget(self.sidebar_panel)

        self.view_stack = QStackedWidget()
        self.content_layout.addWidget(self.view_stack)
        
        self.setup_grid_ui()
        self.setup_insight_panel()
        
        # FIX: Enable keyboard focus immediately for shortcuts
        self.setFocusPolicy(Qt.StrongFocus)

    # --- UI INIT METHODS ---

    def setup_guidance_banner(self):
        self.guidance_banner = QFrame()
        self.guidance_banner.setFixedHeight(40)
        self.guidance_banner.setStyleSheet("background: #111; border-bottom: 1px solid #D4B37D;")
        g_lay = QHBoxLayout(self.guidance_banner)
        msg = QLabel("✨ You can start selecting now. AI insights will be available when analysis is ready.")
        msg.setStyleSheet("color: #D4B37D; font-size: 11px; font-weight: bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20,20)
        # FIX: Prevent buttons from stealing shortcut focus
        close_btn.setFocusPolicy(Qt.NoFocus)
        close_btn.setStyleSheet("border:none; color:#666;")
        close_btn.clicked.connect(self.guidance_banner.hide)
        g_lay.addWidget(msg); g_lay.addStretch(); g_lay.addWidget(close_btn)
        self.layout.addWidget(self.guidance_banner)
        self.guidance_banner.hide()

    def setup_top_bar(self):
        self.top_bar = QFrame(); self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background:#000; border-bottom:1px solid #222;")
        t_lay = QHBoxLayout(self.top_bar); t_lay.setContentsMargins(20,0,20,0)
        title = QLabel("TITANIUM WORKFLOW")
        title.setStyleSheet("color:#D4B37D; font-weight:bold; font-size:14px; letter-spacing:2px;")
        t_lay.addWidget(title); t_lay.addStretch()
        
        self.btn_analyze = MagicAnalyzeButton()
        self.btn_analyze.setFocusPolicy(Qt.NoFocus)
        self.btn_analyze.clicked.connect(self.trigger_ai_analysis)
        t_lay.addWidget(self.btn_analyze); t_lay.addSpacing(20)
        
        # FIX: SETTINGS BUTTON FOR GRID SIZE
        self.btn_settings = QPushButton("⚙️ Grid")
        self.btn_settings.setFocusPolicy(Qt.NoFocus)
        self.btn_settings.setStyleSheet("color:#AAA; border:1px solid #333; padding:5px;")
        self.btn_settings.clicked.connect(self.cycle_grid_size)
        t_lay.addWidget(self.btn_settings); t_lay.addSpacing(10)

        self.btn_export = QPushButton("EXPORT")
        self.btn_export.setCursor(Qt.PointingHandCursor); self.btn_export.setFixedHeight(36)
        self.btn_export.setFocusPolicy(Qt.NoFocus)
        self.btn_export.setStyleSheet("background: #222; color: #FFF; border: 1px solid #444; border-radius: 6px; font-weight: bold; padding: 0 15px;")
        self.btn_export.clicked.connect(self.launch_export)
        t_lay.addWidget(self.btn_export); t_lay.addSpacing(20)
        
        btn_grid = QPushButton("GRID (G)"); btn_grid.clicked.connect(lambda: self.set_mode(0))
        btn_zen = QPushButton("ZEN (E)"); btn_zen.clicked.connect(lambda: self.set_mode(1))
        
        btn_focus = QPushButton("👁"); btn_focus.setFixedSize(36, 36)
        btn_focus.setToolTip("Toggle Focus Mode (L)")
        btn_focus.clicked.connect(self.toggle_lights_out)

        for b in [btn_grid, btn_zen, btn_focus]:
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet("background:#111; color:#D4B37D; border:1px solid #333; padding:8px 10px; border-radius:6px; font-weight:bold;")
            b.setCursor(Qt.PointingHandCursor); t_lay.addWidget(b)
        self.layout.addWidget(self.top_bar)

    def setup_queue_bar(self):
        self.queue_bar = QFrame(); self.queue_bar.setFixedHeight(50)
        self.queue_bar.setStyleSheet("background: #050505; border-bottom: 1px solid #111;")
        q_lay = QHBoxLayout(self.queue_bar); q_lay.setContentsMargins(20, 0, 20, 0)
        q_lay.addWidget(QLabel("PRIORITY QUEUES:"))
        self.chip_vvip = QueueChip("VVIP PENDING"); q_lay.addWidget(self.chip_vvip)
        self.chip_risk = QueueChip("VVIP AT RISK"); q_lay.addWidget(self.chip_risk)
        self.chip_emo = QueueChip("EMOTIONAL"); q_lay.addWidget(self.chip_emo)
        q_lay.addStretch()
        self.layout.addWidget(self.queue_bar)

    def setup_filter_bar(self):
        self.filter_bar = QFrame(); self.filter_bar.setFixedHeight(45)
        self.filter_bar.setStyleSheet("background:#050505; border-bottom:1px solid #222;")
        f_lay = QHBoxLayout(self.filter_bar); f_lay.setContentsMargins(20, 5, 20, 5); f_lay.setSpacing(10)
        self.btn_all = QPushButton("ALL (0)"); self.btn_keep = QPushButton("KEEP (0)")
        self.btn_reject = QPushButton("REJECT (0)"); self.btn_ai_best = QPushButton("✨ AI BEST (0)")
        self.btn_all.clicked.connect(lambda: self.set_filter("all"))
        self.btn_keep.clicked.connect(lambda: self.set_filter("keep"))
        self.btn_reject.clicked.connect(lambda: self.set_filter("reject"))
        self.btn_ai_best.clicked.connect(lambda: self.set_filter("ai_best"))
        for b in [self.btn_all, self.btn_keep, self.btn_reject, self.btn_ai_best]:
            b.setCursor(Qt.PointingHandCursor); b.setFixedWidth(120); f_lay.addWidget(b)
            b.setFocusPolicy(Qt.NoFocus)
        f_lay.addStretch()
        self.layout.addWidget(self.filter_bar)
        self.update_filter_styles()

    def setup_sidebar_filters(self):
        label = QLabel("SUBJECT FILTERS")
        label.setStyleSheet("color: #666; font-size: 9px; font-weight: bold; margin-top: 10px;")
        self.sidebar_layout.addWidget(label)
        self.btn_no_face = QPushButton("NO FACES")
        self.btn_single_face = QPushButton("SINGLE SUBJECT")
        self.btn_group_face = QPushButton("GROUP SHOTS (5+)")
        for b in [self.btn_no_face, self.btn_single_face, self.btn_group_face]:
            b.setCheckable(True)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet("QPushButton { text-align: left; padding: 8px; color: #AAA; border: none; } QPushButton:checked { color: #D4B37D; font-weight: bold; }")
            self.sidebar_layout.addWidget(b)
        self.sidebar_layout.addStretch()

    def setup_grid_ui(self):
        self.page_grid = QWidget(); self.g_lay = QVBoxLayout(self.page_grid)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:#000; border:none;")
        self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(15,15,15,15)
        self.scroll.setWidget(self.grid_container)
        self.g_lay.addWidget(self.scroll)
        
        # --- ZEN MODE ---
        self.page_zen = QWidget(); self.z_lay = QVBoxLayout(self.page_zen)
        
        # FIX: Zen Header Metadata
        self.lbl_zen_header = QLabel("FILENAME.JPG")
        self.lbl_zen_header.setStyleSheet("color: #AAA; font-size: 14px; padding: 10px; font-weight:bold;")
        self.lbl_zen_header.setAlignment(Qt.AlignCenter)
        self.z_lay.addWidget(self.lbl_zen_header)

        self.zen_viewer = ZenViewer()
        self.zen_viewer.double_clicked.connect(lambda: self.set_mode(0))
        self.z_lay.addWidget(self.zen_viewer, 8)
        
        self.filmstrip_area = QScrollArea()
        self.filmstrip_area.setFixedHeight(120)
        self.filmstrip_area.setWidgetResizable(True)
        self.filmstrip_area.setStyleSheet("background:#050505; border-top:1px solid #D4B37D;")
        self.strip_container = QWidget()
        self.strip_layout = QHBoxLayout(self.strip_container)
        self.strip_layout.setAlignment(Qt.AlignLeft)
        self.filmstrip_area.setWidget(self.strip_container)
        self.z_lay.addWidget(self.filmstrip_area, 2)
        
        self.view_stack.addWidget(self.page_grid)
        self.view_stack.addWidget(self.page_zen)

    def setup_insight_panel(self):
        self.insight_panel = QFrame(); self.insight_panel.setFixedHeight(30)
        self.insight_panel.setStyleSheet("background:#050505; border-top:1px solid #222;")
        self.i_lay = QHBoxLayout(self.insight_panel); self.i_lay.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_insight = QLabel("SYSTEM READY")
        self.lbl_insight.setStyleSheet("color:#AAA; font-size:11px; font-family:Consolas; letter-spacing:1px;")
        
        self.lbl_album = QLabel("ALBUM: 0/100")
        self.lbl_album.setStyleSheet("color:#D4B37D; font-size:10px; font-weight:bold; padding-right:20px;")
        
        self.progress_bar = QProgressBar(); self.progress_bar.setFixedWidth(300); self.progress_bar.setFixedHeight(4); self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #111; border-radius: 2px; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C5A96F, stop:1 #D4B37D); border-radius: 2px; }")
        self.progress_bar.hide()
        
        self.i_lay.addWidget(self.lbl_insight); self.i_lay.addStretch()
        self.i_lay.addWidget(self.lbl_album); self.i_lay.addWidget(self.progress_bar)
        self.layout.addWidget(self.insight_panel)

    # --- BRAIN INTEGRATION ---

    def trigger_ai_analysis(self):
        """Creates the link between the Gallery UI and the Titanium Brain."""
        paths = [d['path'] for d in self.image_data]
        if not paths: return
        
        self.btn_analyze.set_loading(True)
        self.progress_bar.show()
        self.progress_bar.setRange(0, len(paths))

        # Start the TitaniumWorker thread
        if TITANIUM_AVAILABLE:
            self.ai_worker = TitaniumWorker(paths)
            self.ai_worker.signals.result.connect(self.handle_ai_result)
            self.ai_worker.signals.progress.connect(self.update_ai_progress)
            self.ai_worker.signals.finished.connect(self.on_ai_finished)
            QThreadPool.globalInstance().start(self.ai_worker)

    def handle_ai_result(self, result):
        """Updates the visual cards (Green/Red) as soon as a score arrives."""
        for i, img in enumerate(self.image_data):
            if img['path'] == result['path']:
                # Update the data dictionary
                img.update(result)
                # Auto-filter logic: Score > 80 is 'keep', else 'reject'
                img['status'] = 'keep' if result.get('score', 0) >= 80 else 'reject'
                
                # Update the card color on the screen
                self.update_card_style(i)
                break

    def update_ai_progress(self, current, total, msg=""):
        self.progress_bar.setValue(current)
        self.lbl_insight.setText(f"🧠 ANALYZING: {current}/{total} | {msg}")

    def on_ai_finished(self):
        self.btn_analyze.set_loading(False)
        self.progress_bar.hide()
        self.lbl_insight.setText(f"✅ ANALYSIS COMPLETE: {len(self.image_data)} IMAGES")
        self.update_filter_styles()

    def handle_ai_result(self, result):
        for img in self.image_data:
            if img['path'] == result['path']:
                img.update(result)
                break
        
        if TITANIUM_AVAILABLE:
            try:
                db_sync = DatabaseSync()
                db_sync.save_ai_verdict(result)
            except: pass

        self.rebuild_grid()

    def update_ai_progress(self, current, total, msg="Processing..."):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.btn_analyze.update_progress(current, total)
        self.lbl_insight.setText(f"AI: {msg}")

    def on_ai_finished(self):
        self.btn_analyze.set_loading(False)
        self.progress_bar.hide()
        self.lbl_insight.setText("TITANIUM ANALYSIS COMPLETE")
        self.rebuild_grid()
        self.update_filter_styles()

    # --- CORE LOGIC ---

    def cycle_grid_size(self):
        self.GRID_COLS += 1
        if self.GRID_COLS > 6: self.GRID_COLS = 3
        self.btn_settings.setText(f"⚙️ {self.GRID_COLS}x{self.GRID_COLS}")
        self.rebuild_grid()

    def set_filter(self, mode):
        self.filter_state = mode
        self.update_filter_styles()
        self.rebuild_grid()
        if self.current_index not in self.visible_indices and self.visible_indices:
            self.current_index = self.visible_indices[0]
            self.multi_selection = {self.current_index}
        if self.view_stack.currentIndex() == 1: self.refresh_zen()
        self.setFocus()

    def update_filter_styles(self):
        def get_style(active, color="#D4B37D"):
            return f"QPushButton {{ color: {'#666' if not active else color}; background-color: {'#1A1A1A' if active else 'transparent'}; border: 1px solid {color if active else '#333'}; border-radius: 4px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background-color: #111; color: {color}; }}"
        self.btn_all.setStyleSheet(get_style(self.filter_state == "all", "#D4B37D"))
        self.btn_keep.setStyleSheet(get_style(self.filter_state == "keep", "#98C379"))
        self.btn_reject.setStyleSheet(get_style(self.filter_state == "reject", "#E06C75"))
        self.btn_ai_best.setStyleSheet(get_style(self.filter_state == "ai_best", "#88E0EF"))
        total = len(self.image_data)
        keep = sum(1 for d in self.image_data if d['status'] == 'keep')
        reject = sum(1 for d in self.image_data if d['status'] == 'reject')
        ai = sum(1 for d in self.image_data if d.get('ai_pick'))
        self.btn_all.setText(f"ALL ({total})"); self.btn_keep.setText(f"KEEP ({keep})")
        self.btn_reject.setText(f"REJECT ({reject})"); self.btn_ai_best.setText(f"✨ AI BEST ({ai})")
        self.update_album_stats(keep)

    def update_album_stats(self, keep_count=None):
        if not hasattr(self, 'lbl_album'): return
        if TITANIUM_AVAILABLE and hasattr(self, 'album_tracker'):
            stats = self.album_tracker.calculate_progress(self.image_data)
            current = stats['current']; target = stats['target']; is_over = stats['is_over']
        else:
            if keep_count is None: keep_count = sum(1 for d in self.image_data if d['status'] == 'keep')
            current = keep_count; target = self.album_target; is_over = current > target

        self.lbl_album.setText(f"ALBUM: {current}/{target}")
        if is_over: self.lbl_album.setStyleSheet("color:#E06C75; font-size:10px; font-weight:bold; padding-right:20px;")
        else: self.lbl_album.setStyleSheet("color:#D4B37D; font-size:10px; font-weight:bold; padding-right:20px;")

    def apply_settings(self, settings):
        self.GRID_COLS = settings.get('grid_cols', 4)
        self.auto_advance = settings.get('auto_advance', True)
        self.album_target = settings.get('album_target', 100)
        if self.image_data: self.rebuild_grid()

    def clear_all(self):
        self.image_data = []
        self.visible_indices = []
        self.rendered_count = 0
        self.current_index = 0
        self.loaded_thumbnails_count = 0
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self.strip_layout.count():
            item = self.strip_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def load_images(self, folder_path):
        if not folder_path or not os.path.isdir(folder_path): return
        
        if hasattr(self, 'ai_worker') and self.ai_worker:
             try:
                 self.ai_worker.signals.result.disconnect()
                 self.ai_worker.signals.progress.disconnect()
                 self.ai_worker.signals.finished.disconnect()
             except: pass
             self.ai_worker.stop()
             self.ai_worker = None
        
        # Hard Reset to fix switching
        self.clear_all()
        
        self.btn_analyze.set_loading(False)
        self.progress_bar.hide()
        self.lbl_insight.setText("SYSTEM READY")
        self.guidance_banner.show()
        self.set_filter("all")
        
        self.current_folder = folder_path
        self.lbl_insight.setText(f"Scanning: {folder_path}")
        self.progress_bar.setRange(0, 0); self.progress_bar.show()
        
        QApplication.processEvents()
        
        self.scanner_worker = FolderScanner(folder_path)
        self.scanner_worker.batch_found.connect(self.on_batch_found)
        self.scanner_worker.finished.connect(self.on_scan_finished)
        self.scanner_worker.start()

    def on_batch_found(self, batch_paths):
        start_idx = len(self.image_data)
        # CRITICAL FIX: Add 'color' key to prevent KeyError crash
        new_items = [{
            'path': p, 
            'status': 'pending', 
            'rating': 0, 
            'color': None, 
            'vip_level': 'None', 
            'confidence': 'high', 
            'is_manual': False, 
            'is_burst': False, 
            'is_best_of_burst': False, 
            'ai_tags': [],
            'ai_pick': False
        } for p in batch_paths]
        
        if self.db:
            saved = self.db.fetch_folder_data(self.current_folder)
            for img in new_items:
                if img['path'] in saved: img.update(saved[img['path']])
        
        self.image_data.extend(new_items)
        
        for i, d in enumerate(new_items):
            if self.filter_state == "all": self.visible_indices.append(start_idx + i)
        
        if self.rendered_count < len(self.visible_indices):
            self.render_next_batch()
            
        # FIX: Populate Filmstrip safely
        if self.strip_layout.count() < 50:
            for item in new_items:
                if self.strip_layout.count() >= 50: break
                thumb = QLabel()
                thumb.setFixedSize(80, 60)
                thumb.setStyleSheet("background:#222; border:1px solid #444;")
                thumb.setScaledContents(True)
                self.strip_layout.addWidget(thumb)
                
                # FIX: Lambda to drop extra args, stopping TypeError crash
                sig = LoaderSignals()
                sig.loaded.connect(lambda p, pix: thumb.setPixmap(pix))
                QThreadPool.globalInstance().start(ThumbnailRunnable(item['path'], QSize(80, 60), sig))
        
        self.lbl_insight.setText(f"Found {len(self.image_data)} files...")
        QApplication.processEvents()
        self.setFocus()

    def on_scan_finished(self):
        self.lbl_insight.setText(f"LOAD COMPLETE. {len(self.image_data)} IMAGES.")
        self.progress_bar.hide()
        self.update_filter_styles()
        self.setFocus()

    def rebuild_grid(self):
        self.page_grid.setUpdatesEnabled(False)
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for c in range(self.GRID_COLS): self.grid_layout.setColumnStretch(c, 1)
        self.visible_indices = []
        for i, d in enumerate(self.image_data):
            if self.filter_state == "all": self.visible_indices.append(i)
            elif self.filter_state == "keep" and d['status'] == "keep": self.visible_indices.append(i)
            elif self.filter_state == "reject" and d['status'] == "reject": self.visible_indices.append(i)
            elif self.filter_state == "ai_best" and d.get('ai_pick'): self.visible_indices.append(i)
        self.rendered_count = 0; self.render_next_batch()
        self.page_grid.setUpdatesEnabled(True)
        self.setFocus()

    def render_next_batch(self):
        if self.is_rendering_batch: return
        self.is_rendering_batch = True
        
        # FIX: Dynamic Grid Size Calculation
        available_w = self.scroll.width() - 40
        if available_w < 100: available_w = 800
        card_size = int(available_w / self.GRID_COLS) - 15
        if card_size < 100: card_size = 100
        
        limit = min(self.rendered_count + self.BATCH_SIZE, len(self.visible_indices))
        for i in range(self.rendered_count, limit):
            idx = self.visible_indices[i]
            d = self.image_data[idx]
            # Pass calculated width
            card = GridCard(idx, d, (idx == self.current_index), (idx in self.multi_selection), width=card_size)
            card.clicked.connect(self.on_card_click)
            card.double_clicked.connect(lambda: self.set_mode(1)) 
            card.image_loaded.connect(self.update_load_status)
            self.grid_layout.addWidget(card, i // self.GRID_COLS, i % self.GRID_COLS)
        self.rendered_count = limit
        
        self.is_rendering_batch = False

    def update_load_status(self):
        self.loaded_thumbnails_count += 1
        if self.loaded_thumbnails_count % 10 == 0:
            total = len(self.image_data)
            self.lbl_insight.setText(f"GENERATING PREVIEWS: {self.loaded_thumbnails_count} / {total}")

    def check_scroll_position(self, value):
        if value > (self.scroll.verticalScrollBar().maximum() * 0.9):
            if self.rendered_count < len(self.visible_indices): self.render_next_batch()

    def scroll_to_current(self):
        if self.current_index >= self.rendered_count:
            self.rendered_count = self.current_index + 20; self.render_next_batch()
        if self.current_index in self.visible_indices:
            idx = self.visible_indices.index(self.current_index)
            if idx < self.grid_layout.count():
                w = self.grid_layout.itemAt(idx).widget()
                if w: self.scroll.ensureWidgetVisible(w)

    def on_card_click(self, idx, mods=Qt.NoModifier):
        prev_idx = self.current_index; self.current_index = idx
        if mods & Qt.ShiftModifier: pass 
        elif not (mods & Qt.ControlModifier): self.multi_selection = {idx}
        
        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if w and w.index == idx: w.update_style(True, False)
            elif w and w.index == prev_idx: w.update_style(False, False)
            
        if self.current_folder and self.db: self.db.save_session_state(self.current_folder, self.current_index)
        QTimer.singleShot(10, self.update_insights)
        if self.view_stack.currentIndex() == 1: self.refresh_zen()
        self.setFocus()

    def update_card_style(self, idx_global):
        if idx_global in self.visible_indices:
            layout_idx = self.visible_indices.index(idx_global)
            item = self.grid_layout.itemAt(layout_idx)
            if item and item.widget():
                item.widget().update_style((idx_global == self.current_index), (idx_global in self.multi_selection))

    def apply_decision(self, status=None, rating=None, color=None):
        targets = self.multi_selection if self.multi_selection else {self.current_index}
        
        if TITANIUM_AVAILABLE and hasattr(self, 'safety_net'):
             self.safety_net.push_undo([copy.deepcopy(self.image_data[i]) for i in targets])
        else:
             prev_states = [copy.deepcopy(self.image_data[idx]) for idx in targets]
             self.undo_stack.append((list(targets), prev_states)); self.redo_stack.clear()

        for idx in targets:
            if status: self.image_data[idx]['status'] = status
            if rating is not None: self.image_data[idx]['rating'] = rating
            if color: self.image_data[idx]['color'] = color
            self.image_data[idx]['is_manual'] = True 
            if self.db: self.db.save_decision(self.image_data[idx]['path'], self.image_data[idx]['status'], self.image_data[idx]['rating'], self.image_data[idx]['color'])
            self.update_card_style(idx)
        
        self.update_filter_styles()
        if self.view_stack.currentIndex() == 1: self.refresh_zen()
        if self.auto_advance and len(targets) == 1: self.move_index(1)
        self.update_album_stats()

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

    def launch_export(self):
        dlg = ExportDialog(self.image_data, self)
        dlg.exec_()

    def set_mode(self, index):
        # FIX: Prevent crash if Zen mode clicked with no images
        if index == 1 and not self.image_data:
            self.lbl_insight.setText("⚠️ Load Images First!")
            return
            
        self.view_stack.setCurrentIndex(index)
        if index == 1: self.refresh_zen()
        self.setFocus()
    
    def refresh_zen(self):
        if not self.image_data: return
        if 0 <= self.current_index < len(self.image_data):
            data = self.image_data[self.current_index]
            self.zen_viewer.set_image(data['path'])
            self.lbl_zen_header.setText(f"{os.path.basename(data['path'])}  |  ({self.current_index + 1} / {len(self.image_data)})")

    def update_insights(self):
        pass
        
    def toggle_lights_out(self):
        self.lights_out = not self.lights_out
        if self.lights_out:
            self.sidebar_panel.hide()
            self.queue_bar.hide()
            self.filter_bar.hide()
        else:
            self.sidebar_panel.show()
            self.top_bar.show()
            self.queue_bar.show()
            self.filter_bar.show()
        self.setFocus()

    def apply_decision(self, status=None, rating=None, color=None):
        """Manually overrides AI results for the currently selected image."""
        if not self.image_data or self.current_index >= len(self.image_data):
            return

        idx = self.current_index
        target = self.image_data[idx]

        # Update the local data Pack
        if status: target['status'] = status
        if rating is not None: target['rating'] = rating
        if color: target['color'] = color
        
        # Mark as manual so AI doesn't overwrite it later
        target['is_manual'] = True 

        # Save to Database immediately
        if self.db:
            self.db.save_decision(target['path'], target['status'], 
                                 target.get('rating', 0), target.get('color'))

        # Update visuals (Green/Red border)
        self.update_card_style(idx)
        self.update_filter_styles()

        # Pre-load the next image for Zen Mode speed
        if self.auto_advance:
            self.move_index(1)
        
        self.setFocus() # Keep keyboard focus active

    def keyPressEvent(self, e):
        """The Master Shortcut List."""
        k = e.key()
        
        # NAVIGATION
        if k == Qt.Key_Right: self.move_index(1)
        elif k == Qt.Key_Left: self.move_index(-1)
        elif k == Qt.Key_G: self.set_mode(0) # Grid
        elif k == Qt.Key_E: self.set_mode(1) # Zen (Enter)
        elif k == Qt.Key_Escape: self.set_mode(0)

        # DECISIONS (The overrides)
        elif k == Qt.Key_C or k == Qt.Key_Space: 
            self.apply_decision(status='keep') # GREEN
        elif k == Qt.Key_X or k == Qt.Key_Backspace: 
            self.apply_decision(status='reject') # RED
        
        # RATINGS & COLORS
        elif Qt.Key_1 <= k <= Qt.Key_5:
            self.apply_decision(rating=int(e.text()))
        elif Qt.Key_6 <= k <= Qt.Key_9:
            colors = {Qt.Key_6: 'red', Qt.Key_7: 'yellow', Qt.Key_8: 'green', Qt.Key_9: 'blue'}
            self.apply_decision(color=colors.get(k))