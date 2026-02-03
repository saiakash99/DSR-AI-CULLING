import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")

# ==========================================
# 1. CORE/DATABASE.PY
# ==========================================
CODE_DATABASE = """import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="database/dsr_pro.db"):
        # Ensure database folder exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        query = \"\"\"
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            path TEXT UNIQUE,
            status TEXT DEFAULT 'PENDING',  -- PENDING, KEEP, REJECT
            ai_tags TEXT,                   -- 'Blurry, Eyes Closed'
            score INTEGER DEFAULT 0
        )
        \"\"\"
        self.conn.execute(query)
        self.conn.commit()

    def add_image(self, filename, path):
        try:
            self.conn.execute(
                "INSERT INTO images (filename, path) VALUES (?, ?)", 
                (filename, path)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass # Skip duplicates

    def get_all_images(self):
        cursor = self.conn.execute("SELECT * FROM images")
        return cursor.fetchall()

    def update_status(self, path, status):
        self.conn.execute(
            "UPDATE images SET status = ? WHERE path = ?", 
            (status, path)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
"""

# ==========================================
# 2. CORE/AI.PY (MediaPipe Logic)
# ==========================================
CODE_AI = """import cv2
import mediapipe as mp

class AIProcessor:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def analyze_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            return {"valid": False, "error": "Could not read image"}

        results = self.face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        tags = []
        score = 100
        
        # Mock Logic: Check if faces exist
        if not results.detections:
            tags.append("No Face")
            score -= 50
        else:
            tags.append("Sharp Face") # Placeholder for blur detection logic

        return {
            "valid": True,
            "tags": ", ".join(tags),
            "score": score
        }
"""

# ==========================================
# 3. CORE/FILES.PY (File Manager)
# ==========================================
CODE_FILES = """import os
import shutil

class FileManager:
    @staticmethod
    def scan_folder(folder_path):
        supported_exts = ('.jpg', '.jpeg', '.png', '.webp')
        images = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(supported_exts):
                    full_path = os.path.join(root, file)
                    images.append((file, full_path))
        return images

    @staticmethod
    def move_file(src, dest_folder):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        try:
            shutil.move(src, os.path.join(dest_folder, os.path.basename(src)))
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False
"""

# --- EXECUTION ---
def restore_files():
    files = {
        "database.py": CODE_DATABASE,
        "ai.py": CODE_AI,
        "files.py": CODE_FILES
    }

    print(f"--- RESTORING CORE FILES TO: {CORE_DIR} ---")
    if not os.path.exists(CORE_DIR):
        os.makedirs(CORE_DIR)

    for filename, code in files.items():
        path = os.path.join(CORE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✅ Created: {filename}")

if __name__ == "__main__":
    restore_files()