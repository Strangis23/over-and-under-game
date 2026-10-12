#!/usr/bin/env python3
import os
import io
import re
import glob
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

ASSETS_DIR = "/run/media/system/Games/Workbench/Over and Under Game/assets/images/nba"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/jpeg,image/png,*/*;q=0.8"
}

WIKI_HEADERS = {
    "User-Agent": "OverAndUnderTriviaGame/2.0 (contact: dev@overundergame.org)",
    "Accept": "application/json"
}

# Team mapping
TEAM_MAP = {
    "76ers": "team_1610612755.webp",
    "sixers": "team_1610612755.webp",
    "philadelphia 76ers": "team_1610612755.webp",
    "bucks": "team_1610612749.webp",
    "milwaukee bucks": "team_1610612749.webp",
    "bulls": "team_1610612741.webp",
    "chicago bulls": "team_1610612741.webp",
    "cavaliers": "team_1610612739.webp",
    "cavs": "team_1610612739.webp",
    "cleveland cavaliers": "team_1610612739.webp",
    "celtics": "team_1610612738.webp",
    "boston celtics": "team_1610612738.webp",
    "clippers": "team_1610612746.webp",
    "los angeles clippers": "team_1610612746.webp",
    "braves": "team_1610612746.webp",
    "grizzlies": "team_1610612763.webp",
    "memphis grizzlies": "team_1610612763.webp",
    "hawks": "team_1610612737.webp",
    "atlanta hawks": "team_1610612737.webp",
    "heat": "team_1610612748.webp",
    "miami heat": "team_1610612748.webp",
    "hornets": "team_1610612766.webp",
    "charlotte hornets": "team_1610612766.webp",
    "bobcats": "team_1610612766.webp",
    "jazz": "team_1610612762.webp",
    "utah jazz": "team_1610612762.webp",
    "kings": "team_1610612758.webp",
    "sacramento kings": "team_1610612758.webp",
    "royals": "team_1610612758.webp",
    "knicks": "team_1610612752.webp",
    "new york knicks": "team_1610612752.webp",
    "lakers": "team_1610612747.webp",
    "los angeles lakers": "team_1610612747.webp",
    "magic": "team_1610612753.webp",
    "orlando magic": "team_1610612753.webp",
    "mavericks": "team_1610612742.webp",
    "mavs": "team_1610612742.webp",
    "dallas mavericks": "team_1610612742.webp",
    "nets": "team_1610612751.webp",
    "brooklyn nets": "team_1610612751.webp",
    "nuggets": "team_1610612743.webp",
    "denver nuggets": "team_1610612743.webp",
    "pacers": "team_1610612754.webp",
    "indiana pacers": "team_1610612754.webp",
    "pelicans": "team_1610612740.webp",
    "new orleans pelicans": "team_1610612740.webp",
    "pistons": "team_1610612765.webp",
    "detroit pistons": "team_1610612765.webp",
    "raptors": "team_1610612761.webp",
    "toronto raptors": "team_1610612761.webp",
    "rockets": "team_1610612745.webp",
    "houston rockets": "team_1610612745.webp",
    "spurs": "team_1610612759.webp",
    "san antonio spurs": "team_1610612759.webp",
    "suns": "team_1610612756.webp",
    "phoenix suns": "team_1610612756.webp",
    "thunder": "team_1610612760.webp",
    "oklahoma city thunder": "team_1610612760.webp",
    "supersonics": "team_1610612760.webp",
    "sonics": "team_1610612760.webp",
    "timberwolves": "team_1610612750.webp",
    "minnesota timberwolves": "team_1610612750.webp",
    "wolves": "team_1610612750.webp",
    "trail blazers": "team_1610612757.webp",
    "portland trail blazers": "team_1610612757.webp",
    "blazers": "team_1610612757.webp",
    "warriors": "team_1610612744.webp",
    "golden state warriors": "team_1610612744.webp",
    "wizards": "team_1610612764.webp",
    "washington wizards": "team_1610612764.webp",
    "bullets": "team_1610612764.webp"
}

def is_fallback_avatar(file_path):
    if not os.path.exists(file_path):
        return True
    try:
        size = os.path.getsize(file_path)
        if size < 6000:
            with Image.open(file_path) as im:
                tl = im.getpixel((5, 5))
                if tl[0] in range(15, 23) and tl[1] in range(19, 27) and tl[2] in range(29, 37):
                    return True
    except Exception:
        pass
    return False

def process_and_save_webp(img_bytes, dest_path, target_size=(360, 450)):
    try:
        im = Image.open(io.BytesIO(img_bytes))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        
        im_ratio = im.width / im.height
        target_ratio = target_size[0] / target_size[1]
        
        if im_ratio > target_ratio:
            new_h = target_size[1]
            new_w = int(new_h * im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            x_offset = (new_w - target_size[0]) // 2
            im_cropped = im_resized.crop((x_offset, 0, x_offset + target_size[0], target_size[1]))
        else:
            new_w = target_size[0]
            new_h = int(new_w / im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            y_offset = (new_h - target_size[1]) // 2
            im_cropped = im_resized.crop((0, y_offset, target_size[0], y_offset + target_size[1]))

        im_cropped.save(dest_path, "WEBP", quality=82, method=4)
        return True
    except Exception:
        return False

def fetch_wiki_search_image(name):
    for q_suffix in ["basketball", "NBA", ""]:
        try:
            query = f"{name} {q_suffix}".strip()
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
            req = urllib.request.Request(url, headers=WIKI_HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("query", {}).get("search", [])
                if not results:
                    continue
                # Check top 2 results
                for r in results[:2]:
                    title = r["title"]
                    url2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=600"
                    req2 = urllib.request.Request(url2, headers=WIKI_HEADERS)
                    with urllib.request.urlopen(req2, timeout=5) as resp2:
                        data2 = json.loads(resp2.read().decode())
                        pages = data2.get("query", {}).get("pages", {})
                        for p in pages.values():
                            if "thumbnail" in p and "source" in p["thumbnail"]:
                                img_url = p["thumbnail"]["source"]
                                img_req = urllib.request.Request(img_url, headers=HEADERS)
                                with urllib.request.urlopen(img_req, timeout=6) as img_resp:
                                    return img_resp.read()
        except Exception:
            pass
    return None

def resolve_and_apply(item):
    name = item.get("name", "")
    url = item.get("image_url", "")
    team = (item.get("team") or item.get("team_full") or "").lower().strip()
    subtext = item.get("subtext", "").lower()
    clean_name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("'", "")
    
    m_player = re.search(r"/(\d+)\.", url)
    if m_player:
        dest_filename = f"p_{m_player.group(1)}.webp"
        pid = m_player.group(1)
    else:
        dest_filename = f"{clean_name}.webp"
        pid = None
        
    dest_path = os.path.join(ASSETS_DIR, dest_filename)
    
    # 1. Try NBA CDN
    if pid:
        for cdn_url in [
            f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
            f"https://cdn.nba.com/headshots/nba/latest/260x190/{pid}.png"
        ]:
            try:
                req = urllib.request.Request(cdn_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if len(data) > 1000 and process_and_save_webp(data, dest_path):
                            return (name, "NBA_CDN")
            except Exception:
                pass
                
    # 2. Try Wikipedia
    wiki_data = fetch_wiki_search_image(name)
    if wiki_data and len(wiki_data) > 1000 and process_and_save_webp(wiki_data, dest_path):
        return (name, "WIKIPEDIA")
        
    # 3. Use Team card placeholder
    team_file = TEAM_MAP.get(team)
    if not team_file:
        for k, v in TEAM_MAP.items():
            if k in subtext or k in team:
                team_file = v
                break
    if not team_file:
        team_file = "nba_league.webp"
        
    src_path = os.path.join(ASSETS_DIR, team_file)
    if os.path.exists(src_path):
        try:
            with Image.open(src_path) as team_im:
                team_im = team_im.resize((360, 450), Image.Resampling.LANCZOS)
                team_im.save(dest_path, "WEBP", quality=82)
            return (name, f"TEAM_CARD ({team_file})")
        except Exception:
            pass
            
    return (name, "FAILED")

def run():
    print("=== Scanning remaining fallback players ===", flush=True)
    cat_files = sorted(glob.glob(os.path.join(CAT_DIR, "*.json")))
    
    unique_items = {}
    for cf in cat_files:
        if "franchise" in cf or "arena" in cf: continue
        with open(cf) as f: d = json.load(f)
        for it in d.get("items", []):
            name = it.get("name", "")
            img_rel = it.get("image", "").replace("res://", "")
            if name and is_fallback_avatar(img_rel):
                unique_items[name] = it

    items_to_fetch = list(unique_items.values())
    print(f"Total players to update: {len(items_to_fetch)}", flush=True)
    
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(resolve_and_apply, it): it for it in items_to_fetch}
        for fut in as_completed(futures):
            name, src = fut.result()
            results[src] = results.get(src, 0) + 1
            
    print(f"\nDone in {time.time()-t0:.1f}s!")
    for k, v in sorted(results.items()):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    run()
