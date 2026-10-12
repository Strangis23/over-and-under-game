#!/usr/bin/env python3
import os
import json
import glob
import re
import io
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = "/run/media/system/Games/Workbench/Over and Under Game/assets/images/nba"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

WIKI_HEADERS = {
    "User-Agent": "OverAndUnderTriviaGame/2.0 (contact: dev@overundergame.org)"
}

os.makedirs(ASSETS_DIR, exist_ok=True)

def process_image(img_bytes, dest_path, target_size=(360, 450)):
    try:
        im = Image.open(io.BytesIO(img_bytes))
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        
        # Center crop / resize to target_size maintaining aspect ratio
        im_ratio = im.width / im.height
        target_ratio = target_size[0] / target_size[1]
        
        if im_ratio > target_ratio:
            # Image is wider: fit height, crop width
            new_h = target_size[1]
            new_w = int(new_h * im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            x_offset = (new_w - target_size[0]) // 2
            im_cropped = im_resized.crop((x_offset, 0, x_offset + target_size[0], target_size[1]))
        else:
            # Image is taller: fit width, crop height
            new_w = target_size[0]
            new_h = int(new_w / im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            y_offset = (new_h - target_size[1]) // 2
            im_cropped = im_resized.crop((0, y_offset, target_size[0], y_offset + target_size[1]))

        # Optimize WebP output
        im_cropped.save(dest_path, "WEBP", quality=82, method=6)
        return True
    except Exception as e:
        print(f"Error processing image for {dest_path}: {e}")
        return False

def generate_fallback_avatar(name, team, dest_path, target_size=(360, 450)):
    try:
        # Create a handsome dark basketball-styled card
        im = Image.new("RGBA", target_size, (18, 22, 32, 255))
        draw = ImageDraw.Draw(im)
        
        # Subtle court line arch
        draw.arc([30, 40, target_size[0] - 30, target_size[1] - 40], 0, 360, fill=(40, 55, 80, 255), width=3)
        draw.line([target_size[0] // 2, 40, target_size[0] // 2, target_size[1] - 40], fill=(40, 55, 80, 255), width=2)
        
        # Center basketball silhouette
        cx = target_size[0] // 2
        cy = target_size[1] // 2 - 20
        r = 75
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(210, 105, 30, 255), outline=(245, 160, 60, 255), width=4)
        draw.arc([cx - r, cy - r, cx + r, cy + r], 45, 225, fill=(40, 20, 10, 200), width=3)
        draw.line([cx - r, cy, cx + r, cy], fill=(40, 20, 10, 200), width=3)
        draw.line([cx, cy - r, cx, cy + r], fill=(40, 20, 10, 200), width=3)
        
        # Initials in center
        parts = [p for p in name.split() if p]
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")) if parts else "NBA"
        
        # Draw initials
        draw.text((cx, cy), initials, fill=(255, 255, 255, 255), anchor="mm")
        
        im.save(dest_path, "WEBP", quality=82, method=6)
        return True
    except Exception as e:
        print(f"Fallback generation error for {name}: {e}")
        return False

def fetch_wiki_headshot(name):
    try:
        encoded = urllib.parse.quote(name)
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={encoded}&prop=pageimages&format=json&pithumbsize=600"
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                if "thumbnail" in p and "source" in p["thumbnail"]:
                    img_url = p["thumbnail"]["source"]
                    img_req = urllib.request.Request(img_url, headers=HEADERS)
                    with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                        return img_resp.read()
    except Exception:
        pass
    return None

def fetch_single_item(item):
    name = item.get("name", "")
    url = item.get("image_url", "")
    team = item.get("team", "")
    
    clean_name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("'", "")
    
    # 1. Determine target filename
    m_player = re.search(r"/(\d+)\.(png|webp)", url)
    m_team = re.search(r"/nba/(\d+)/", url)
    
    if m_player:
        filename = f"p_{m_player.group(1)}.webp"
    elif m_team:
        filename = f"team_{m_team.group(1)}.webp"
    else:
        filename = f"{clean_name}.webp"
        
    dest_path = os.path.join(ASSETS_DIR, filename)
    
    # Check if named version already exists
    if os.path.exists(os.path.join(ASSETS_DIR, f"{clean_name}.webp")):
        return (name, f"res://assets/images/nba/{clean_name}.webp", True)
        
    if os.path.exists(dest_path):
        return (name, f"res://assets/images/nba/{filename}", True)
        
    # Attempt 1: NBA CDN direct fetch
    if url and url.startswith("http"):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 1000 and process_image(data, dest_path):
                        return (name, f"res://assets/images/nba/{filename}", True)
        except Exception:
            pass
            
    # Attempt 2: Wikipedia headshot
    wiki_bytes = fetch_wiki_headshot(name)
    if wiki_bytes and len(wiki_bytes) > 1000 and process_image(wiki_bytes, dest_path):
        return (name, f"res://assets/images/nba/{filename}", True)
        
    # Attempt 3: High quality procedural card
    generate_fallback_avatar(name, team, dest_path)
    return (name, f"res://assets/images/nba/{filename}", True)

def run():
    print("=== Scanning all category files ===")
    cat_files = sorted(glob.glob(os.path.join(CAT_DIR, "*.json")))
    
    unique_items = {}
    for path in cat_files:
        with open(path) as f:
            d = json.load(f)
        for it in d.get("items", []):
            name = it.get("name", "")
            if name and name not in unique_items:
                unique_items[name] = it

    items_list = list(unique_items.values())
    print(f"Total unique contenders to ensure: {len(items_list)}")
    
    # Run concurrent downloads
    print("Fetching and processing all contender images concurrently (24 workers)...")
    name_to_res_path = {}
    completed_count = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(fetch_single_item, it): it for it in items_list}
        for future in as_completed(futures):
            name, res_path, ok = future.result()
            name_to_res_path[name] = res_path
            completed_count += 1
            if completed_count % 100 == 0 or completed_count == len(items_list):
                print(f"  [{completed_count}/{len(items_list)}] processed ({time.time() - t0:.1f}s)")
                
    print(f"\nAll images processed in {time.time() - t0:.1f}s!")
    
    # Update category JSONs with explicit local res:// path
    print("\nUpdating category JSONs with instant local paths...")
    for path in cat_files:
        with open(path) as f:
            data = json.load(f)
        updated = 0
        for it in data.get("items", []):
            name = it.get("name", "")
            if name in name_to_res_path:
                it["image"] = name_to_res_path[name]
                updated += 1
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  {os.path.basename(path)}: updated {updated}/{len(data.get('items', []))} items with local images")

    print("\n=== Done! All contender images are locally bundled! ===")

if __name__ == "__main__":
    run()
