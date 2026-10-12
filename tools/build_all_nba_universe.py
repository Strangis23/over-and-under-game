#!/usr/bin/env python3
"""
Build the full NBA universe:
- Extracts all 3,632 players from common_player_info + draft_history + draft_combine_stats.
- Downloads headshots from NBA CDN for any players without a photo.
- Assigns official team cards to older/historical players without headshots.
- Generates comprehensive category JSON files:
    - nba_height.json (all players)
    - nba_weight.json (all players)
    - nba_draft_pick.json (all drafted players)
    - nba_seasons_played.json (all players)
    - nba_wingspan.json (all combine participants)
    - nba_vertical_leap.json (all combine participants)
    - nba_bench_press.json (all combine participants)
- Optimizes images (280x350, Lossy WebP quality 0.75 in .import).
"""

import os
import re
import io
import json
import glob
import time
import sqlite3
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

DB_PATH = "data/categories/nba data/nba.sqlite"
CAT_DIR = "data/categories"
ASSETS_DIR = "assets/images/nba"
TARGET_SIZE = (280, 350)
WEBP_QUALITY = 80
LOSSY_QUALITY = 0.75

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
WIKI_HEADERS = {
    "User-Agent": "NBAOverUnderGame/2.0 (contact: admin@overundergame.org)"
}

TEAMS_CONFERENCE = {
    'Atlanta Hawks': ('Eastern', 'Southeast', 'Hawks', '1610612737'),
    'Boston Celtics': ('Eastern', 'Atlantic', 'Celtics', '1610612738'),
    'Brooklyn Nets': ('Eastern', 'Atlantic', 'Nets', '1610612751'),
    'Charlotte Hornets': ('Eastern', 'Southeast', 'Hornets', '1610612766'),
    'Chicago Bulls': ('Eastern', 'Central', 'Bulls', '1610612741'),
    'Cleveland Cavaliers': ('Eastern', 'Central', 'Cavaliers', '1610612739'),
    'Dallas Mavericks': ('Western', 'Southwest', 'Mavericks', '1610612742'),
    'Denver Nuggets': ('Western', 'Northwest', 'Nuggets', '1610612743'),
    'Detroit Pistons': ('Eastern', 'Central', 'Pistons', '1610612765'),
    'Golden State Warriors': ('Western', 'Pacific', 'Warriors', '1610612744'),
    'Houston Rockets': ('Western', 'Southwest', 'Rockets', '1610612745'),
    'Indiana Pacers': ('Eastern', 'Central', 'Pacers', '1610612754'),
    'LA Clippers': ('Western', 'Pacific', 'Clippers', '1610612746'),
    'Los Angeles Clippers': ('Western', 'Pacific', 'Clippers', '1610612746'),
    'Los Angeles Lakers': ('Western', 'Pacific', 'Lakers', '1610612747'),
    'Memphis Grizzlies': ('Western', 'Southwest', 'Grizzlies', '1610612763'),
    'Miami Heat': ('Eastern', 'Southeast', 'Heat', '1610612748'),
    'Milwaukee Bucks': ('Eastern', 'Central', 'Bucks', '1610612749'),
    'Minnesota Timberwolves': ('Western', 'Northwest', 'Timberwolves', '1610612750'),
    'New Orleans Pelicans': ('Western', 'Southwest', 'Pelicans', '1610612740'),
    'New York Knicks': ('Eastern', 'Atlantic', 'Knicks', '1610612752'),
    'Oklahoma City Thunder': ('Western', 'Northwest', 'Thunder', '1610612760'),
    'Orlando Magic': ('Eastern', 'Southeast', 'Magic', '1610612753'),
    'Philadelphia 76ers': ('Eastern', 'Atlantic', '76ers', '1610612755'),
    'Phoenix Suns': ('Western', 'Pacific', 'Suns', '1610612756'),
    'Portland Trail Blazers': ('Western', 'Northwest', 'Trail Blazers', '1610612757'),
    'Sacramento Kings': ('Western', 'Pacific', 'Kings', '1610612758'),
    'San Antonio Spurs': ('Western', 'Southwest', 'Spurs', '1610612759'),
    'Toronto Raptors': ('Eastern', 'Atlantic', 'Raptors', '1610612761'),
    'Utah Jazz': ('Western', 'Northwest', 'Jazz', '1610612762'),
    'Washington Wizards': ('Eastern', 'Southeast', 'Wizards', '1610612764'),
}

TEAM_NAME_TO_FULL = {v[2]: k for k, v in TEAMS_CONFERENCE.items()}
TEAM_ID_TO_TID = {
    1610612737: "1610612737", 1610612738: "1610612738", 1610612739: "1610612739", 1610612740: "1610612740",
    1610612741: "1610612741", 1610612742: "1610612742", 1610612743: "1610612743", 1610612744: "1610612744",
    1610612745: "1610612745", 1610612746: "1610612746", 1610612747: "1610612747", 1610612748: "1610612748",
    1610612749: "1610612749", 1610612750: "1610612750", 1610612751: "1610612751", 1610612752: "1610612752",
    1610612753: "1610612753", 1610612754: "1610612754", 1610612755: "1610612755", 1610612756: "1610612756",
    1610612757: "1610612757", 1610612758: "1610612758", 1610612759: "1610612759", 1610612760: "1610612760",
    1610612761: "1610612761", 1610612762: "1610612762", 1610612763: "1610612763", 1610612764: "1610612764",
    1610612765: "1610612765", 1610612766: "1610612766"
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

def get_decades(from_y, to_y):
    if not from_y:
        return ['2020s']
    decs = set()
    fy = int(from_y)
    ty = int(to_y) if to_y else fy
    for y in range(fy, ty + 1):
        if y <= 1989:
            decs.add('1980s & Prior')
        elif y <= 1999:
            decs.add('1990s')
        elif y <= 2009:
            decs.add('2000s')
        elif y <= 2019:
            decs.add('2010s')
        else:
            decs.add('2020s')
    order = ['1980s & Prior', '1990s', '2000s', '2010s', '2020s']
    return [d for d in order if d in decs]

def get_positions(pos_str):
    if not pos_str:
        return ['Forward']
    p = pos_str.lower()
    res = []
    if 'guard' in p or 'g' in p:
        res.append('Guard')
    if 'forward' in p or 'f' in p:
        res.append('Forward')
    if 'center' in p or 'c' in p:
        res.append('Center')
    return res if res else ['Forward']

def parse_height_to_inches(ht_str):
    if not ht_str:
        return None
    try:
        if '-' in ht_str:
            parts = ht_str.split('-')
            return int(parts[0]) * 12 + int(parts[1])
        elif "'" in ht_str:
            parts = ht_str.replace('"', '').split("'")
            return int(parts[0]) * 12 + int(parts[1])
    except Exception:
        pass
    return None

def process_and_save_headshot(img_bytes, dest_path):
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
            y_offset = max(0, min(int((new_h - target_h) * 0.15), new_h - target_h))
            im_cropped = im_resized.crop((0, y_offset, target_w, y_offset + target_h))

        im_cropped.convert("RGB").save(dest_path, "WEBP", quality=WEBP_QUALITY, method=6)
        create_import_file_if_needed(dest_path)
        return True
    except Exception:
        return False

def resolve_player_assets(all_players):
    print(f"\n=== Resolving Asset Images for {len(all_players)} players ===")
    
    # 1. Existing local images
    to_fetch = []
    for pid, pdata in all_players.items():
        name = pdata["name"]
        clean_name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("'", "")
        
        cand_p = os.path.join(ASSETS_DIR, f"p_{pid}.webp")
        cand_name = os.path.join(ASSETS_DIR, f"{clean_name}.webp")
        
        if os.path.exists(cand_p):
            pdata["image"] = f"res://assets/images/nba/p_{pid}.webp"
        elif os.path.exists(cand_name):
            pdata["image"] = f"res://assets/images/nba/{clean_name}.webp"
        else:
            to_fetch.append((pid, name, pdata))

    print(f"Players requiring headshot check/download: {len(to_fetch)}")

    def fetch_player_headshot(pid, name, pdata):
        dest_p = os.path.join(ASSETS_DIR, f"p_{pid}.webp")
        
        # Try NBA CDN
        nba_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
        try:
            req = urllib.request.Request(nba_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    data = r.read()
                    if len(data) > 3000 and process_and_save_headshot(data, dest_p):
                        pdata["image"] = f"res://assets/images/nba/p_{pid}.webp"
                        return (pid, True, "NBA CDN")
        except Exception:
            pass

        # Try Wikipedia if modern/active player
        if pdata.get("to_year", 0) >= 2010 or pdata.get("status") == "Active":
            try:
                query = f"{name} basketball"
                wurl = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=1&prop=pageimages&format=json&pithumbsize=600"
                req = urllib.request.Request(wurl, headers=WIKI_HEADERS)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    pages = data.get("query", {}).get("pages", {})
                    for p in pages.values():
                        if "thumbnail" in p and "source" in p["thumbnail"]:
                            ir = urllib.request.Request(p["thumbnail"]["source"], headers=WIKI_HEADERS)
                            with urllib.request.urlopen(ir, timeout=6) as ir_resp:
                                b = ir_resp.read()
                                if len(b) > 2000 and process_and_save_headshot(b, dest_p):
                                    pdata["image"] = f"res://assets/images/nba/p_{pid}.webp"
                                    return (pid, True, "Wiki Headshot")
            except Exception:
                pass

        # Fallback to team card placeholder
        tid = pdata.get("team_id")
        team_str_id = TEAM_ID_TO_TID.get(tid, "1610612738")
        team_path = f"res://assets/images/nba/team_{team_str_id}.webp"
        pdata["image"] = team_path
        return (pid, False, f"Team Card ({team_str_id})")

    t0 = time.time()
    fetched_success = 0
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(fetch_player_headshot, pid, name, pdata): pid for pid, name, pdata in to_fetch}
        for future in as_completed(futures):
            pid, ok, source = future.result()
            if ok:
                fetched_success += 1
            if fetched_success % 50 == 0 and fetched_success > 0:
                print(f"  [Progress] Downloaded {fetched_success} new player headshots...")

    print(f"Asset resolution completed in {time.time() - t0:.1f}s. New headshots downloaded: {fetched_success}")

def run():
    print("=== Step 1: Loading all players from nba.sqlite ===")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
    SELECT person_id, display_first_last, position, height, weight, draft_number, draft_year, season_exp,
           team_id, team_name, team_abbreviation, from_year, to_year, rosterstatus
    FROM common_player_info
    WHERE display_first_last IS NOT NULL AND display_first_last != '';
    ''')
    rows = cur.fetchall()
    print(f"Loaded {len(rows)} players from common_player_info")

    all_players = {}
    for r in rows:
        pid = str(r[0])
        name = r[1]
        pos = r[2] or "Forward"
        ht = r[3]
        wt = r[4]
        draft_num = r[5]
        draft_yr = r[6]
        season_exp = r[7]
        team_id = r[8]
        team_name = r[9] or "NBA"
        team_abbr = r[10] or "NBA"
        from_y = r[11]
        to_y = r[12]
        status = "Active" if r[13] == "Active" else "Retired"

        positions = get_positions(pos)
        full_team = TEAM_NAME_TO_FULL.get(team_name, team_name if team_name != "NBA" else "NBA League")
        decades = get_decades(from_y, to_y)

        all_players[pid] = {
            "pid": pid,
            "name": name,
            "position": positions[0],
            "positions": positions,
            "height_str": ht,
            "weight_str": wt,
            "draft_num": draft_num,
            "draft_yr": draft_yr,
            "season_exp": season_exp,
            "team_id": team_id,
            "team": team_name,
            "team_full": full_team,
            "from_year": int(from_y) if from_y else 2000,
            "to_year": int(to_y) if to_y else 2024,
            "status": status,
            "decades": decades,
            "subtext": f"{positions[0]} • {team_name}"
        }

    # Resolve all image assets
    resolve_player_assets(all_players)

    print("\n=== Step 2: Generating Height Category ===")
    height_items = []
    for pid, p in all_players.items():
        inches = parse_height_to_inches(p["height_str"])
        if inches and 60 <= inches <= 96:
            feet = inches // 12
            rem_in = inches % 12
            height_items.append({
                "name": p["name"],
                "subtext": p["subtext"],
                "value": inches,
                "display_value": f"{feet} ft {rem_in} in",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": p["position"],
                "positions": p["positions"],
                "team": p["team"],
                "team_full": p["team_full"],
                "decades": p["decades"],
                "status": p["status"],
                "from_year": p["from_year"],
                "to_year": p["to_year"],
                "image": p["image"]
            })
    height_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_height.json"), "w") as f:
        json.dump({
            "id": "nba_height",
            "title": "Player Height",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who is TALLER (Feet & Inches)?",
            "unit": "ft/in",
            "value_format": "{feet} ft {inches} in",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#00BFFF",
            "items": height_items
        }, f, indent=2)
    print(f"Generated nba_height.json: {len(height_items)} players")

    print("\n=== Step 3: Generating Weight Category ===")
    weight_items = []
    for pid, p in all_players.items():
        if p["weight_str"] and p["weight_str"].isdigit():
            lbs = int(p["weight_str"])
            if 130 <= lbs <= 400:
                weight_items.append({
                    "name": p["name"],
                    "subtext": p["subtext"],
                    "value": lbs,
                    "display_value": f"{lbs} lbs",
                    "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                    "position": p["position"],
                    "positions": p["positions"],
                    "team": p["team"],
                    "team_full": p["team_full"],
                    "decades": p["decades"],
                    "status": p["status"],
                    "from_year": p["from_year"],
                    "to_year": p["to_year"],
                    "image": p["image"]
                })
    weight_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_weight.json"), "w") as f:
        json.dump({
            "id": "nba_weight",
            "title": "Player Weight",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who is HEAVIER (Weight in LBS)?",
            "unit": "lbs",
            "value_format": "{value} lbs",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#FF7F50",
            "items": weight_items
        }, f, indent=2)
    print(f"Generated nba_weight.json: {len(weight_items)} players")

    print("\n=== Step 4: Generating Draft Pick Category ===")
    draft_items = []
    for pid, p in all_players.items():
        dn = p["draft_num"]
        if dn and dn.isdigit():
            pick_num = int(dn)
            if 1 <= pick_num <= 60:
                draft_yr = p["draft_yr"] or p["from_year"]
                draft_items.append({
                    "name": p["name"],
                    "subtext": f"{p['position']} • Draft Class {draft_yr}",
                    "value": pick_num,
                    "display_value": f"Pick #{pick_num}",
                    "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                    "position": p["position"],
                    "positions": p["positions"],
                    "team": p["team"],
                    "team_full": p["team_full"],
                    "decades": p["decades"],
                    "status": p["status"],
                    "from_year": p["from_year"],
                    "to_year": p["to_year"],
                    "image": p["image"]
                })
    draft_items.sort(key=lambda x: x["value"])
    with open(os.path.join(CAT_DIR, "nba_draft_pick.json"), "w") as f:
        json.dump({
            "id": "nba_draft_pick",
            "title": "Overall Draft Pick Number",
            "group": "career",
            "group_label": "Career & Draft",
            "filter_type": "player",
            "prompt": "Who was drafted HIGHER (Better Draft Pick)?",
            "unit": "pick",
            "value_format": "Pick #{value}",
            "lower_is_better": True,
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#DA70D6",
            "items": draft_items
        }, f, indent=2)
    print(f"Generated nba_draft_pick.json: {len(draft_items)} players")

    print("\n=== Step 5: Generating Seasons Played Category ===")
    seasons_items = []
    for pid, p in all_players.items():
        if p["season_exp"] is not None:
            exp = int(p["season_exp"])
            if exp >= 1:
                seasons_items.append({
                    "name": p["name"],
                    "subtext": f"{p['position']} • {p['from_year']}–{p['to_year']}",
                    "value": exp,
                    "display_value": f"{exp} Seasons" if exp > 1 else "1 Season",
                    "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                    "position": p["position"],
                    "positions": p["positions"],
                    "team": p["team"],
                    "team_full": p["team_full"],
                    "decades": p["decades"],
                    "status": p["status"],
                    "from_year": p["from_year"],
                    "to_year": p["to_year"],
                    "image": p["image"]
                })
    seasons_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_seasons_played.json"), "w") as f:
        json.dump({
            "id": "nba_seasons_played",
            "title": "NBA Seasons Played",
            "group": "career",
            "group_label": "Career & Draft",
            "filter_type": "player",
            "prompt": "Who played MORE Seasons in the NBA?",
            "unit": "seasons",
            "value_format": "{value} Seasons",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#32CD32",
            "items": seasons_items
        }, f, indent=2)
    print(f"Generated nba_seasons_played.json: {len(seasons_items)} players")

    print("\n=== Step 6: Generating Combine Categories (Wingspan, Vertical, Bench Press) ===")
    cur.execute('''
    SELECT player_id, player_name, wingspan, max_vertical_leap, bench_press, position, season
    FROM draft_combine_stats;
    ''')
    combine_rows = cur.fetchall()

    ws_items, vert_items, bench_items = [], [], []
    for pid, name, ws, vert, bp, pos, season in combine_rows:
        pid_str = str(pid)
        p_info = all_players.get(pid_str, {
            "name": name,
            "position": get_positions(pos)[0],
            "positions": get_positions(pos),
            "team": "NBA",
            "team_full": "NBA League",
            "decades": get_decades(season, season),
            "status": "Retired",
            "from_year": int(season) if season else 2010,
            "to_year": int(season) if season else 2024,
            "image": f"res://assets/images/nba/team_1610612738.webp"
        })
        img_res = all_players.get(pid_str, {}).get("image", "res://assets/images/nba/team_1610612738.webp")

        if ws and ws > 70:
            feet = int(ws // 12)
            rem_in = ws - (feet * 12)
            rem_str = str(int(round(rem_in))) if rem_in == int(rem_in) or abs(rem_in - round(rem_in)) < 0.05 else f"{rem_in:.1f}"
            ws_items.append({
                "name": name,
                "subtext": f"{p_info['position']} • Combine {season}",
                "value": round(float(ws), 2),
                "display_value": f"{feet} ft {rem_str} in",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": p_info["position"],
                "positions": p_info["positions"],
                "team": p_info["team"],
                "team_full": p_info["team_full"],
                "decades": p_info["decades"],
                "status": p_info["status"],
                "from_year": p_info["from_year"],
                "to_year": p_info["to_year"],
                "image": img_res
            })

        if vert and vert > 25:
            vert_items.append({
                "name": name,
                "subtext": f"{p_info['position']} • Combine {season}",
                "value": round(float(vert), 1),
                "display_value": f"{round(float(vert), 1)}\" Vertical",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": p_info["position"],
                "positions": p_info["positions"],
                "team": p_info["team"],
                "team_full": p_info["team_full"],
                "decades": p_info["decades"],
                "status": p_info["status"],
                "from_year": p_info["from_year"],
                "to_year": p_info["to_year"],
                "image": img_res
            })

        if bp and bp > 0:
            bench_items.append({
                "name": name,
                "subtext": f"{p_info['position']} • Combine {season}",
                "value": int(bp),
                "display_value": f"{int(bp)} Reps",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": p_info["position"],
                "positions": p_info["positions"],
                "team": p_info["team"],
                "team_full": p_info["team_full"],
                "decades": p_info["decades"],
                "status": p_info["status"],
                "from_year": p_info["from_year"],
                "to_year": p_info["to_year"],
                "image": img_res
            })

    ws_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_wingspan.json"), "w") as f:
        json.dump({
            "id": "nba_wingspan",
            "title": "Combine Wingspan",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who has the LONGER Wingspan (Feet & Inches)?",
            "unit": "ft/in",
            "value_format": "{feet} ft {inches} in",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#9370DB",
            "items": ws_items
        }, f, indent=2)
    print(f"Generated nba_wingspan.json: {len(ws_items)} combine participants")

    vert_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_vertical_leap.json"), "w") as f:
        json.dump({
            "id": "nba_vertical_leap",
            "title": "Combine Max Vertical Leap",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who recorded the HIGHER Max Vertical Leap?",
            "unit": "in",
            "value_format": "{value}\" Vertical",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#FFD700",
            "items": vert_items
        }, f, indent=2)
    print(f"Generated nba_vertical_leap.json: {len(vert_items)} combine participants")

    bench_items.sort(key=lambda x: x["value"], reverse=True)
    with open(os.path.join(CAT_DIR, "nba_bench_press.json"), "w") as f:
        json.dump({
            "id": "nba_bench_press",
            "title": "Combine Bench Press (185 lbs)",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who benched MORE Reps (185 lbs) at the Combine?",
            "unit": "reps",
            "value_format": "{value} Reps",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#FF4500",
            "items": bench_items
        }, f, indent=2)
    print(f"Generated nba_bench_press.json: {len(bench_items)} combine participants")

    conn.close()
    print("\nAll categories updated successfully with all players from database!")

if __name__ == "__main__":
    run()
