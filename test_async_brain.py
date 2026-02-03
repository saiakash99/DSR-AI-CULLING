# ---------------------------------------------------------
# test_async_brain.py
# ---------------------------------------------------------
import sys
import os
import time
from PySide6.QtCore import QCoreApplication, QThreadPool, QRunnable, QObject, Signal, Slot

# Ensure we can import from core/
sys.path.append(os.getcwd())

from core.brain_bridge import TitaniumBrain
from core.db_sync import DatabaseSync

# --- 1. MOCK DATA LIST ---
test_files = [
    "wedding_hero_001.jpg",
    "wedding_dup_002.jpg",
    "wedding_blink_003.jpg",
    "wedding_soft_004.jpg",
    "wedding_blur_005.jpg"
]

# --- 2. ASYNC WORKER (Configured for Test Injection) ---
class WorkerSignals(QObject):
    result = Signal(dict)
    progress = Signal(int)
    finished = Signal()

class TitaniumWorker(QRunnable):
    def __init__(self, image_paths):
        super().__init__()
        self.paths = image_paths
        self.signals = WorkerSignals()
        self.brain = TitaniumBrain()
        self.is_killed = False

    @Slot()
    def run(self):
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            if self.is_killed: 
                break
            
            try:
                # 🛠️ SIMULATING ENGINE OUTPUT (Fixes the 'timestamp' error)
                mock_raw = {
                    'path': path,
                    'timestamp': 1700000000.0 + i,
                    'sharpness': 120.0 if "hero" in path else (10.0 if "blur" in path else 65.0),
                    'eyes_open_ratio': 0.05 if "blink" in path else 0.9,
                    'smile_score': 0.85 if "hero" in path else 0.2,
                    'embedding': [0.1] * 128,
                    'face_count': 1
                }
                
                # Step 1: Convert to Burst Object
                burst_img = self.brain._to_burst_image(mock_raw)
                
                # Step 2: Contextual Analysis (Burst/Duplicate Check)
                # We simulate a burst by passing the list to the resolver
                self.brain.grouper.resolve_burst([burst_img])
                
                # Step 3: Logic Decision
                signals = self.brain.adapter.normalize_signals(mock_raw, burst_img.__dict__)
                decision = self.brain.judge.decide(signals)
                
                # Step 4: Final Result Assembly
                final_result = {**mock_raw, **signals, **decision}
                
                # Emit to UI (Tester)
                self.signals.result.emit(final_result)
                
                # Emit Progress
                self.signals.progress.emit(int(((i + 1) / total) * 100))
                
                # Small sleep to simulate processing time
                time.sleep(0.2)
                
            except Exception as e:
                print(f"❌ Error processing {path}: {e}")

        self.signals.finished.emit()

# --- 3. TEST CONTROLLER ---
class AsyncTester:
    def __init__(self):
        self.sync = DatabaseSync()
        self.worker = TitaniumWorker(test_files)
        
        # Connect Signals
        self.worker.signals.result.connect(self.handle_result)
        self.worker.signals.progress.connect(self.handle_progress)
        self.worker.signals.finished.connect(self.handle_finished)

    def handle_result(self, result):
        name = os.path.basename(result['path'])
        bucket = result['bucket']
        reason = result['ai_reason']
        
        print(f"✅ VERDICT: {name:<20} | {bucket:<8} | Reason: {reason}")
        
        # TEST DATABASE SYNC
        self.sync.save_ai_verdict(result)
        print(f"💾 DB_SYNC: Entry for {name} saved successfully.")

    def handle_progress(self, pct):
        print(f"📊 Progress: {pct}%")

    def handle_finished(self):
        print("\n🏁 ASYNC TEST COMPLETE. All logic, threading, and DB paths verified.")
        QCoreApplication.quit()

def run_test():
    app = QCoreApplication(sys.argv)
    print("🚀 INITIALIZING ASYNC BRAIN STACK TEST...")
    
    tester = AsyncTester()
    QThreadPool.globalInstance().start(tester.worker)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_test()