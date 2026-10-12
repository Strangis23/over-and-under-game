#!/usr/bin/env python3
"""
Optimize all NBA images in the project:
1. Downscale high-resolution images to max width 280 (preserving aspect ratio) using Lanczos.
2. Re-encode with WebP quality=80.
3. Update corresponding .import files to use Godot Lossy WebP texture compression (compress/mode=1, lossy_quality=0.75).
"""

import os
import glob
from PIL import Image

ASSETS_DIR = "assets/images/nba"
TARGET_WIDTH = 280
WEBP_QUALITY = 80
LOSSY_QUALITY = 0.75

def optimize_images():
    webp_files = sorted(glob.glob(os.path.join(ASSETS_DIR, "*.webp")))
    print(f"Found {len(webp_files)} webp files in {ASSETS_DIR}")
    
    total_before = 0
    total_after = 0
    resized_count = 0

    for file_path in webp_files:
        before_size = os.path.getsize(file_path)
        total_before += before_size
        
        try:
            with Image.open(file_path) as im:
                w, h = im.size
                if w > TARGET_WIDTH:
                    new_w = TARGET_WIDTH
                    new_h = max(1, int(h * (TARGET_WIDTH / w)))
                    im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    # Convert to RGBA or RGB if necessary
                    im_resized.save(file_path, "WEBP", quality=WEBP_QUALITY, method=6)
                    resized_count += 1
                else:
                    # Even if not resizing, make sure it's optimized
                    pass
        except Exception as e:
            print(f"Error optimizing {file_path}: {e}")

        after_size = os.path.getsize(file_path)
        total_after += after_size

    print(f"Resized {resized_count} images.")
    print(f"Source WebP total: {total_before / (1024*1024):.2f} MB -> {total_after / (1024*1024):.2f} MB "
          f"({(1 - total_after / total_before) * 100:.1f}% reduction)")

def update_import_files():
    import_files = sorted(glob.glob(os.path.join(ASSETS_DIR, "*.webp.import")))
    print(f"Updating {len(import_files)} .import files to Lossy WebP...")
    
    updated_count = 0
    for imp_path in import_files:
        with open(imp_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        # Ensure compress/mode=1
        if "compress/mode=0" in new_content:
            new_content = new_content.replace("compress/mode=0", "compress/mode=1")
        elif "compress/mode=" not in new_content:
            new_content = new_content.replace("[params]\n", "[params]\ncompress/mode=1\n")

        # Ensure compress/lossy_quality
        if "compress/lossy_quality=" in new_content:
            import re
            new_content = re.sub(r"compress/lossy_quality=[0-9.]+", f"compress/lossy_quality={LOSSY_QUALITY}", new_content)
        else:
            new_content = new_content.replace("[params]\n", f"[params]\ncompress/lossy_quality={LOSSY_QUALITY}\n")

        # Set high_quality=false
        if "compress/high_quality=true" in new_content:
            new_content = new_content.replace("compress/high_quality=true", "compress/high_quality=false")

        if new_content != content:
            with open(imp_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            updated_count += 1

    print(f"Updated {updated_count} .import files.")

if __name__ == "__main__":
    optimize_images()
    update_import_files()
