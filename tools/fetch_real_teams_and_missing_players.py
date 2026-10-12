#!/usr/bin/env python3
"""
Comprehensive script to:
1. Download official ESPN PNG logos for all 30 NBA teams and generate sleek 280x350 team cards.
2. For all players currently lacking photos (< 3.2KB fallback cards):
   - Fetch real headshots from Wikipedia search ("{name} basketball").
   - If no headshot exists, assign the official card of the team they played for as placeholder.
3. Update nba_draft_pick.json:
   - "prompt": "Who was drafted HIGHER (Better Draft Pick)?"
   - "lower_is_better": True
4. Update nba_wingspan.json:
   - "prompt": "Who has the LONGER Wingspan (Feet & Inches)?"
   - "unit": "ft/in"
   - "value_format": "{feet} ft {inches} in"
   - Reformat display_value for all items to "X ft Y in"
5. Ensure all corresponding .import files have compress/mode=1 and lossy_quality=0.75.
"""

import os
import re
import json
import glob
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
from PIL import Image, ImageDraw

ASSETS_DIR = "assets/images/nba"
CAT_DIR = "data/categories"
TARGET_SIZE = (280, 350)
WEBP_QUALITY = 80
LOSSY_QUALITY = 0.75

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
WIKI_HEADERS = {
    "User-Agent": "NBAOverUnderGame/1.0 (contact: admin@overundergame.org)"
}

TEAMS_MAP = {
    "1610612737": ("atl", "Atlanta Hawks", (224, 58, 62)),
    "1610612738": ("bos", "Boston Celtics", (0, 122, 51)),
    "1610612739": ("cle", "Cleveland Cavaliers", (134, 0, 56)),
    "1610612740": ("no",  "New Orleans Pelicans", (0, 43, 92)),
    "1610612741": ("chi", "Chicago Bulls", (206, 17, 65)),
    "1610612742": ("dal", "Dallas Mavericks", (0, 83, 188)),
    "1610612743": ("den", "Denver Nuggets", (13, 34, 64)),
    "1610612744": ("gs",  "Golden State Warriors", (29, 66, 138)),
    "1610612745": ("hou", "Houston Rockets", (206, 17, 65)),
    "1610612746": ("lac", "LA Clippers", (200, 16, 46)),
    "1610612747": ("lal", "Los Angeles Lakers", (85, 37, 130)),
    "1610612748": ("mia", "Miami Heat", (152, 0, 46)),
    "1610612749": ("mil", "Milwaukee Bucks", (0, 71, 27)),
    "1610612750": ("min", "Minnesota Timberwolves", (12, 35, 64)),
    "1610612751": ("bkn", "Brooklyn Nets", (119, 125, 132)),
    "1610612752": ("ny",  "New York Knicks", (0, 107, 182)),
    "1610612753": ("orl", "Orlando Magic", (0, 119, 192)),
    "1610612754": ("ind", "Indiana Pacers", (0, 45, 98)),
    "1610612755": ("phi", "Philadelphia 76ers", (0, 107, 182)),
    "1610612756": ("phx", "Phoenix Suns", (29, 17, 96)),
    "1610612757": ("por", "Portland Trail Blazers", (224, 58, 62)),
    "1610612758": ("sac", "Sacramento Kings", (91, 43, 130)),
    "1610612759": ("sa",  "San Antonio Spurs", (196, 206, 211)),
    "1610612760": ("okc", "Oklahoma City Thunder", (0, 122, 193)),
    "1610612761": ("tor", "Toronto Raptors", (206, 17, 65)),
    "1610612762": ("utah", "Utah Jazz", (0, 43, 92)),
    "1610612763": ("mem", "Memphis Grizzlies", (93, 118, 169)),
    "1610612764": ("was", "Washington Wizards", (0, 43, 92)),
    "1610612765": ("det", "Detroit Pistons", (29, 66, 138)),
    "1610612766": ("cha", "Charlotte Hornets", (29, 17, 96)),
}

TEAM_NAME_TO_ID = {
    "hawks": "1610612737", "celtics": "1610612738", "cavaliers": "1610612739", "cavs": "1610612739",
    "pelicans": "1610612740", "bulls": "1610612741", "mavericks": "1610612742", "mavs": "1610612742",
    "nuggets": "1610612743", "warriors": "1610612744", "rockets": "1610612745", "clippers": "1610612746",
    "lakers": "1610612747", "heat": "1610612748", "bucks": "1610612749", "timberwolves": "1610612750",
    "wolves": "1610612750", "nets": "1610612751", "knicks": "1610612752", "magic": "1610612753",
    "pacers": "1610612754", "76ers": "1610612755", "sixers": "1610612755", "suns": "1610612756",
    "trail blazers": "1610612757", "blazers": "1610612757", "kings": "1610612758", "spurs": "1610612759",
    "thunder": "1610612760", "supersonics": "1610612760", "sonics": "1610612760",
    "raptors": "1610612761", "jazz": "1610612762", "grizzlies": "1610612763", "wizards": "1610612764",
    "bullets": "1610612764", "pistons": "1610612765", "hornets": "1610612766", "bobcats": "1610612766"
}

def create_import_file_if_needed(image_path):
    imp_path = image_path + ".import"
    if not os.path.exists(imp_path):
        import hashlib
        h = hashlib.md5(image_path.encode()).hexdigest()
        bname = os.path.basename(image_path)
        content = f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://{h[:12]}"
path="res://.godot/imported/{bname}-{h}.ctex"
metadata={{
"vram_texture": false
}}

[deps]

source_file="res://{image_path}"
dest_files=["res://.godot/imported/{bname}-{h}.ctex"]

[params]

compress/mode=1
compress/high_quality=false
compress/lossy_quality={LOSSY_QUALITY}
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
"""
        with open(imp_path, "w", encoding="utf-8") as f:
            f.write(content)

def build_team_cards():
    print("=== Step 1: Generating Official Team Logo Cards for all 30 NBA Teams ===")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    for tid, (abbr, team_name, color) in TEAMS_MAP.items():
        url = f"https://a.espncdn.com/i/teamlogos/nba/500/{abbr}.png"
        dest_path = os.path.join(ASSETS_DIR, f"team_{tid}.webp")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            
            logo = Image.open(io.BytesIO(data)).convert("RGBA")
            
            # Create a card with a sleek dark stadium background + subtle team glow
            card = Image.new("RGBA", TARGET_SIZE, (14, 18, 28, 255))
            draw = ImageDraw.Draw(card)
            
            # Subtle vertical accent bar or glow with team primary color
            cx = TARGET_SIZE[0] // 2
            cy = TARGET_SIZE[1] // 2
            
            glow_r = 110
            # Draw subtle colored background circle
            draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r], 
                         fill=(color[0]//5, color[1]//5, color[2]//5, 255))
            
            # Scale logo to fit nicely (215x215)
            logo.thumbnail((215, 215), Image.Resampling.LANCZOS)
            lx = (TARGET_SIZE[0] - logo.width) // 2
            ly = (TARGET_SIZE[1] - logo.height) // 2
            
            card.paste(logo, (lx, ly), logo)
            card.convert("RGB").save(dest_path, "WEBP", quality=WEBP_QUALITY, method=6)
            create_import_file_if_needed(dest_path)
            print(f"  [Team {abbr.upper()}] Saved {dest_path}")
        except Exception as e:
            print(f"  Error building team {abbr}: {e}")

def process_headshot_bytes(img_bytes, dest_path):
    try:
        im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        w, h = im.size
        target_w, target_h = TARGET_SIZE
        target_ratio = target_w / target_h
        im_ratio = w / h

        if im_ratio > target_ratio:
            new_h = target_h
            new_w = int(new_h * im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            x_offset = (new_w - target_w) // 2
            im_cropped = im_resized.crop((x_offset, 0, x_offset + target_w, target_h))
        else:
            new_w = target_w
            new_h = int(new_w / im_ratio)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Favor top of image for faces/headshots (y_offset at 15% instead of 50%)
            y_offset = max(0, min(int((new_h - target_h) * 0.15), new_h - target_h))
            im_cropped = im_resized.crop((0, y_offset, target_w, y_offset + target_h))

        im_cropped.convert("RGB").save(dest_path, "WEBP", quality=WEBP_QUALITY, method=6)
        create_import_file_if_needed(dest_path)
        return True
    except Exception as e:
        print(f"  Error processing image {dest_path}: {e}")
        return False

def fetch_wiki_headshot(player_name):
    query = f"{player_name} basketball"
    url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=1&prop=pageimages&format=json&pithumbsize=600"
    try:
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                if "thumbnail" in p and "source" in p["thumbnail"]:
                    img_url = p["thumbnail"]["source"]
                    img_req = urllib.request.Request(img_url, headers=WIKI_HEADERS)
                    with urllib.request.urlopen(img_req, timeout=8) as ir:
                        return ir.read()
    except Exception:
        pass
    return None

def resolve_player_team_id(item):
    for key in ["team", "team_full", "subtext"]:
        val = item.get(key, "").lower()
        for nick, tid in TEAM_NAME_TO_ID.items():
            if nick in val:
                return tid
    return "1610612738" # default Celtics if unknown

def fix_missing_players():
    print("\n=== Step 2: Fetching Real Headshots for Missing Players ===")
    cat_files = sorted(glob.glob(os.path.join(CAT_DIR, "*.json")))
    
    unique_items = {}
    for cf in cat_files:
        with open(cf) as f:
            d = json.load(f)
        for it in d.get("items", []):
            name = it.get("name", "")
            img = it.get("image", "").replace("res://", "")
            if os.path.exists(img) and os.path.getsize(img) < 3200 and "team_" not in img:
                if name not in unique_items:
                    unique_items[name] = (it, img)

    print(f"Found {len(unique_items)} players with placeholder fallback cards.")
    
    def process_player(name, item, img_path):
        b = fetch_wiki_headshot(name)
        if b and len(b) > 2000 and process_headshot_bytes(b, img_path):
            return (name, True, "Wiki Headshot")
        
        # Fallback to team card placeholder
        tid = resolve_player_team_id(item)
        team_card = os.path.join(ASSETS_DIR, f"team_{tid}.webp")
        if os.path.exists(team_card):
            import shutil
            shutil.copyfile(team_card, img_path)
            create_import_file_if_needed(img_path)
            return (name, True, f"Team Card (team_{tid})")
            
        return (name, False, "Failed")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(process_player, name, item, img_path): name for name, (item, img_path) in unique_items.items()}
        for future in as_completed(futures):
            name, ok, reason = future.result()
            print(f"  {name}: {reason}")
            
    print(f"Finished player headshot processing in {time.time() - t0:.1f}s.")

def update_draft_pick_category():
    print("\n=== Step 3: Updating Draft Pick Category (Lower Pick # = Better) ===")
    path = os.path.join(CAT_DIR, "nba_draft_pick.json")
    with open(path) as f:
        data = json.load(f)
        
    data["prompt"] = "Who was drafted HIGHER (Better Draft Pick)?"
    data["lower_is_better"] = True
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("  Updated nba_draft_pick.json: lower_is_better = True, prompt updated.")

def update_wingspan_category():
    print("\n=== Step 4: Updating Wingspan Category to Feet & Inches ===")
    path = os.path.join(CAT_DIR, "nba_wingspan.json")
    with open(path) as f:
        data = json.load(f)
        
    data["prompt"] = "Who has the LONGER Wingspan (Feet & Inches)?"
    data["unit"] = "ft/in"
    data["value_format"] = "{feet} ft {inches} in"
    
    for it in data.get("items", []):
        val = float(it.get("value", 0))
        feet = int(val // 12)
        inches = val - (feet * 12)
        if inches == int(inches) or abs(inches - round(inches)) < 0.05:
            it["display_value"] = f"{feet} ft {int(round(inches))} in"
        else:
            it["display_value"] = f"{feet} ft {inches:.1f} in"
            
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Updated nba_wingspan.json: {len(data['items'])} items reformatted to feet and inches.")

def update_height_category():
    print("\n=== Step 5: Verifying Height Category Formats ===")
    path = os.path.join(CAT_DIR, "nba_height.json")
    with open(path) as f:
        data = json.load(f)
        
    for it in data.get("items", []):
        val = float(it.get("value", 0))
        feet = int(val // 12)
        inches = int(round(val - (feet * 12)))
        it["display_value"] = f"{feet} ft {inches} in"
        
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Updated nba_height.json: {len(data['items'])} items checked.")

if __name__ == "__main__":
    build_team_cards()
    fix_missing_players()
    update_draft_pick_category()
    update_wingspan_category()
    update_height_category()
