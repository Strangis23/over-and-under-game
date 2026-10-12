#!/usr/bin/env python3
import os
import glob
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image

ASSETS_DIR = "/run/media/system/Games/Workbench/Over and Under Game/assets/images/nba"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

def convert_one(png_path, quality=82):
    png_size = os.path.getsize(png_path)
    webp_path = os.path.splitext(png_path)[0] + ".webp"
    
    with Image.open(png_path) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.save(webp_path, format="WEBP", quality=quality, method=4)
        
    webp_size = os.path.getsize(webp_path)
    
    # Remove original PNG and its .import file
    try:
        os.remove(png_path)
    except OSError:
        pass
    import_path = png_path + ".import"
    if os.path.exists(import_path):
        try:
            os.remove(import_path)
        except OSError:
            pass
            
    return (png_size, webp_size)

def convert_pngs_to_webp(quality=82):
    png_files = sorted(glob.glob(os.path.join(ASSETS_DIR, "*.png")))
    total_files = len(png_files)
    print(f"Found {total_files} PNG files to convert to WebP...", flush=True)
    if total_files == 0:
        return
        
    total_png_bytes = 0
    total_webp_bytes = 0
    t0 = time.time()
    
    cpu_count = min(os.cpu_count() or 4, 16)
    print(f"Running conversion with {cpu_count} worker processes...", flush=True)
    
    completed = 0
    with ProcessPoolExecutor(max_workers=cpu_count) as executor:
        futures = {executor.submit(convert_one, p, quality): p for p in png_files}
        for fut in as_completed(futures):
            p_bytes, w_bytes = fut.result()
            total_png_bytes += p_bytes
            total_webp_bytes += w_bytes
            completed += 1
            if completed % 100 == 0 or completed == total_files:
                print(f"  [{completed}/{total_files}] converted ({(completed/total_files)*100:.1f}%) in {time.time()-t0:.1f}s", flush=True)
                
    elapsed = time.time() - t0
    saved_bytes = total_png_bytes - total_webp_bytes
    print(f"\nConversion finished in {elapsed:.2f}s!", flush=True)
    print(f"Original PNG size: {total_png_bytes / (1024*1024):.2f} MB", flush=True)
    print(f"New WebP size:      {total_webp_bytes / (1024*1024):.2f} MB", flush=True)
    if total_png_bytes > 0:
        print(f"Space saved:        {saved_bytes / (1024*1024):.2f} MB ({(saved_bytes/total_png_bytes)*100:.1f}% reduction)", flush=True)

def update_category_jsons():
    cat_files = sorted(glob.glob(os.path.join(CAT_DIR, "*.json")))
    print(f"\nUpdating {len(cat_files)} category JSON files...", flush=True)
    total_replacements = 0
    
    for cat_path in cat_files:
        with open(cat_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content.replace(".png\"", ".webp\"")
        
        if content != new_content:
            repl_count = content.count(".png\"") - new_content.count(".png\"")
            total_replacements += repl_count
            with open(cat_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  {os.path.basename(cat_path)}: updated {repl_count} image references", flush=True)
            
    print(f"Total JSON image paths updated to .webp: {total_replacements}", flush=True)

if __name__ == "__main__":
    convert_pngs_to_webp()
    update_category_jsons()
