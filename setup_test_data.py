import os
import requests

# 1. Define the path exactly where the app is looking
desktop = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')
target_folder = os.path.join(desktop, 'WeddingCuller', 'test_photos')

# 2. Create the folders if they don't exist
if not os.path.exists(target_folder):
    os.makedirs(target_folder)
    print(f"✅ Created folder: {target_folder}")
else:
    print(f"✅ Folder already exists: {target_folder}")

# 3. Download a sample "Wedding" image so the AI has something to read
image_url = "https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
image_path = os.path.join(target_folder, "sample_wedding.jpg")

if not os.path.exists(image_path):
    print("⬇️ Downloading sample image for AI analysis...")
    img_data = requests.get(image_url).content
    with open(image_path, 'wb') as handler:
        handler.write(img_data)
    print(f"📸 Created sample image: {image_path}")
else:
    print("📸 Sample image already ready.")

print("-" * 30)
print("🚀 SETUP COMPLETE. Run 'python connect_gallery.py' now.")