#!/usr/bin/env python3
"""
Build all 18 NBA stats categories with hundreds of all-time players:
- Scrapes Basketball-Reference comprehensive all-time leaderboards (250 - 550+ players per stat).
- Expands PPG, All-Time Points, 3PM, 3PM/G, Assists, APG, Rebounds, RPG, Blocks, BPG,
  Steals, SPG, Turnovers, TOPG, FTM, FTM/G, 2PM, 2PM/G.
- Maps player metadata from existing catalog, SQLite player/common_player_info/draft_history.
- Downloads any missing player headshots (NBA CDN or Wikipedia) at 280x350 WebP.
- Writes full category JSON files.
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
from bs4 import BeautifulSoup
from PIL import Image

ASSETS_DIR = "/run/media/system/Games/Workbench/Over and Under Game/assets/images/nba"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"
DB_PATH = "/run/media/system/Games/Workbench/Over and Under Game/data/categories/nba data/nba.sqlite"
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
TEAM_MAP_FILES = {
    "76ers": "team_1610612755.webp",
    "sixers": "team_1610612755.webp",
    "bucks": "team_1610612749.webp",
    "bulls": "team_1610612741.webp",
    "cavaliers": "team_1610612739.webp",
    "cavs": "team_1610612739.webp",
    "celtics": "team_1610612738.webp",
    "clippers": "team_1610612746.webp",
    "braves": "team_1610612746.webp",
    "grizzlies": "team_1610612763.webp",
    "hawks": "team_1610612737.webp",
    "heat": "team_1610612748.webp",
    "hornets": "team_1610612766.webp",
    "bobcats": "team_1610612766.webp",
    "jazz": "team_1610612762.webp",
    "kings": "team_1610612758.webp",
    "royals": "team_1610612758.webp",
    "knicks": "team_1610612752.webp",
    "lakers": "team_1610612747.webp",
    "magic": "team_1610612753.webp",
    "mavericks": "team_1610612742.webp",
    "mavs": "team_1610612742.webp",
    "nets": "team_1610612751.webp",
    "nuggets": "team_1610612743.webp",
    "pacers": "team_1610612754.webp",
    "pelicans": "team_1610612740.webp",
    "pistons": "team_1610612765.webp",
    "raptors": "team_1610612761.webp",
    "rockets": "team_1610612745.webp",
    "spurs": "team_1610612759.webp",
    "suns": "team_1610612756.webp",
    "thunder": "team_1610612760.webp",
    "supersonics": "team_1610612760.webp",
    "sonics": "team_1610612760.webp",
    "timberwolves": "team_1610612750.webp",
    "wolves": "team_1610612750.webp",
    "trail blazers": "team_1610612757.webp",
    "blazers": "team_1610612757.webp",
    "warriors": "team_1610612744.webp",
    "wizards": "team_1610612764.webp",
    "bullets": "team_1610612764.webp"
}

def create_import_file_if_needed(webp_path):
    imp_path = f"{webp_path}.import"
    if not os.path.exists(imp_path):
        content = f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://{abs(hash(webp_path)):x}"
path="res://.godot/imported/{os.path.basename(webp_path)}-{abs(hash(webp_path)):x}.ctex"
metadata={{
"vram_texture": false
}}

[deps]

source_file="res://assets/images/nba/{os.path.basename(webp_path)}"
dest_files=["res://.godot/imported/{os.path.basename(webp_path)}-{abs(hash(webp_path)):x}.ctex"]

[params]

compress/mode=1
compress/high_quality=false
compress/lossy_quality={LOSSY_QUALITY}
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

def clean_player_name(raw_name):
    name = re.sub(r"[\*\^\†\§\[\d\]#]", "", raw_name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def parse_decades(from_y, to_y):
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

def save_image_bytes(img_bytes, dest_path):
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

# 1. Load Existing Catalog
print("Loading existing player catalog...")
existing_catalog = {}
for p in glob.glob(os.path.join(CAT_DIR, "*.json")):
    with open(p) as fp:
        d = json.load(fp)
    for it in d.get("items", []):
        name = it.get("name")
        if name and name.lower().strip() not in existing_catalog:
            existing_catalog[name.lower().strip()] = it

# 2. Load SQLite player & common_player_info & draft_history databases
print("Loading SQLite player databases...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT person_id, display_first_last, team_name, position, rosterstatus, from_year, to_year, team_id
    FROM common_player_info
""")
cpi_players = {}
for pid, dfl, tm_name, pos, status, fy, ty, tid in cursor.fetchall():
    if dfl:
        cpi_players[dfl.lower().strip()] = {
            "pid": pid,
            "name": dfl,
            "team_name": tm_name or "NBA",
            "position": pos or "Forward",
            "status": "Active" if status == "Active" else "Retired",
            "from_year": fy or 2000,
            "to_year": ty or 2024,
            "team_id": tid or ""
        }

cursor.execute("SELECT id, full_name, is_active FROM player")
all_players_table = {}
for pid, fname, is_act in cursor.fetchall():
    if fname:
        all_players_table[fname.lower().strip()] = (pid, fname, is_act)

cursor.execute("SELECT person_id, player_name, season, team_name FROM draft_history")
draft_history_table = {}
for pid, pname, ssn, tname in cursor.fetchall():
    if pname and pname.lower().strip() not in draft_history_table:
        draft_history_table[pname.lower().strip()] = (pid, ssn, tname)

conn.close()

def ensure_player_image(name, pid=None, team_name="NBA"):
    clean_name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("'", "")
    
    # 1. Existing local files
    cand1 = os.path.join(ASSETS_DIR, f"{clean_name}.webp")
    if os.path.exists(cand1):
        return f"res://assets/images/nba/{clean_name}.webp"
    if pid:
        cand2 = os.path.join(ASSETS_DIR, f"player_{pid}.webp")
        if os.path.exists(cand2):
            return f"res://assets/images/nba/player_{pid}.webp"

    # 2. Try NBA CDN if pid exists
    if pid:
        url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    dest = os.path.join(ASSETS_DIR, f"player_{pid}.webp")
                    if save_image_bytes(resp.read(), dest):
                        return f"res://assets/images/nba/player_{pid}.webp"
        except Exception:
            pass

    # 3. Try Wikipedia search
    try:
        query = f"{name} basketball"
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            search = data.get("query", {}).get("search", [])
            if search:
                title = search[0]["title"]
                url2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=600"
                req2 = urllib.request.Request(url2, headers=WIKI_HEADERS)
                with urllib.request.urlopen(req2, timeout=4) as resp2:
                    data2 = json.loads(resp2.read().decode())
                    pages = data2.get("query", {}).get("pages", {})
                    for p in pages.values():
                        if "thumbnail" in p:
                            img_url = p["thumbnail"]["source"]
                            req3 = urllib.request.Request(img_url, headers=HEADERS)
                            with urllib.request.urlopen(req3, timeout=4) as r3:
                                dest = os.path.join(ASSETS_DIR, f"{clean_name}.webp")
                                if save_image_bytes(r3.read(), dest):
                                    return f"res://assets/images/nba/{clean_name}.webp"
    except Exception:
        pass

    # 4. Fallback to team card or league card
    t_clean = team_name.lower().strip()
    team_file = TEAM_MAP_FILES.get(t_clean, "nba_league.webp")
    return f"res://assets/images/nba/{team_file}"

def build_player_item(raw_name, stat_val, stat_display):
    name = clean_player_name(raw_name)
    key = name.lower().strip()
    
    # Check existing catalog
    if key in existing_catalog:
        cat_info = existing_catalog[key]
        image_res = cat_info.get("image", "")
        # verify image path on disk
        img_path = image_res.replace("res://", "")
        if not os.path.exists(img_path):
            image_res = ensure_player_image(name, team_name=cat_info.get("team", "NBA"))
        return {
            "name": name,
            "subtext": cat_info.get("subtext", f"{cat_info.get('position', 'Forward')} • {cat_info.get('team', 'NBA')}"),
            "value": stat_val,
            "display_value": stat_display,
            "position": cat_info.get("position", "Forward"),
            "positions": cat_info.get("positions", ["Forward"]),
            "team": cat_info.get("team", "NBA"),
            "team_full": cat_info.get("team_full", "NBA"),
            "decades": cat_info.get("decades", ["2010s"]),
            "status": cat_info.get("status", "Retired"),
            "from_year": cat_info.get("from_year", 2000),
            "to_year": cat_info.get("to_year", 2024),
            "image": image_res
        }

    # Check CPI
    if key in cpi_players:
        pinfo = cpi_players[key]
        pos = pinfo["position"]
        pos_list = [pos] if pos in ["Guard", "Forward", "Center"] else ["Forward"]
        short_team = pinfo["team_name"]
        full_team = TEAM_NAME_TO_FULL.get(short_team, short_team)
        image_res = ensure_player_image(name, pid=pinfo["pid"], team_name=short_team)
        decades = parse_decades(pinfo["from_year"], pinfo["to_year"])
        return {
            "name": name,
            "subtext": f"{pos} • {short_team}",
            "value": stat_val,
            "display_value": stat_display,
            "position": pos,
            "positions": pos_list,
            "team": short_team,
            "team_full": full_team,
            "decades": decades,
            "status": pinfo["status"],
            "from_year": int(pinfo["from_year"]),
            "to_year": int(pinfo["to_year"]),
            "image": image_res
        }

    # Check general player table & draft history
    pid = None
    status = "Retired"
    if key in all_players_table:
        pid, _, is_act = all_players_table[key]
        status = "Active" if is_act == 1 else "Retired"
    
    from_y = 1990
    short_team = "NBA"
    if key in draft_history_table:
        dpid, ssn, tname = draft_history_table[key]
        if not pid: pid = dpid
        if ssn and ssn.isdigit(): from_y = int(ssn)
        if tname: short_team = tname

    full_team = TEAM_NAME_TO_FULL.get(short_team, short_team)
    decades = parse_decades(from_y, 2026 if status == "Active" else from_y + 10)
    image_res = ensure_player_image(name, pid=pid, team_name=short_team)

    return {
        "name": name,
        "subtext": f"Forward • {short_team}",
        "value": stat_val,
        "display_value": stat_display,
        "position": "Forward",
        "positions": ["Forward"],
        "team": short_team,
        "team_full": full_team,
        "decades": decades,
        "status": status,
        "from_year": from_y,
        "to_year": 2026 if status == "Active" else from_y + 10,
        "image": image_res
    }

def scrape_bref_leaderboard(ep, vtype="int"):
    url = f"https://www.basketball-reference.com/leaders/{ep}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as resp:
        soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
        players = {}
        for tbl in soup.find_all("table"):
            for tr in tbl.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) == 3:
                    p = tds[1].find("a")
                    if p:
                        name = p.get_text().strip()
                        raw_val = tds[2].get_text().strip().replace(",", "")
                        try:
                            val = int(raw_val) if vtype == "int" else float(raw_val)
                            if name not in players or val > players[name]:
                                players[name] = val
                        except ValueError:
                            pass
        return players

def scrape_bref_single_table(ep, table_id="nba"):
    url = f"https://www.basketball-reference.com/leaders/{ep}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as resp:
        soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
        tbl = soup.find("table", {"id": table_id}) or soup.find("table", {"id": "tot"})
        res = {}
        if tbl:
            for tr in tbl.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) == 3:
                    p = tds[1].find("a")
                    if p:
                        name = p.get_text().strip()
                        raw_val = tds[2].get_text().strip().replace(",", "")
                        try:
                            res[name] = float(raw_val)
                        except ValueError:
                            pass
        return res

CATEGORIES_SPEC = [
    {
        "ep": "pts_career.html",
        "id": "nba_total_points",
        "title": "All-Time Total Points",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has scored MORE Total Career Points in NBA History?",
        "unit": "PTS",
        "value_format": "{value} PTS",
        "vtype": "int",
        "icon": "res://assets/icons/trophy.png",
        "theme_color": "#FFB703"
    },
    {
        "ep": "pts_per_g_career.html",
        "id": "nba_ppg",
        "title": "NBA Scoring Averages",
        "group": "career",
        "group_label": "Career & Draft",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Regular Season PPG?",
        "unit": "PPG",
        "value_format": "{value} PPG",
        "vtype": "float",
        "icon": "res://assets/icons/trophy.webp",
        "theme_color": "#FF8C00"
    },
    {
        "ep": "fg3_career.html",
        "id": "nba_total_3pm",
        "title": "All-Time 3-Pointers Made",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has made MORE Total 3-Pointers in NBA History?",
        "unit": "3PM",
        "value_format": "{value} 3PM",
        "vtype": "int",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#4CC9F0"
    },
    {
        "ep": "fg3_per_g_career.html",
        "id": "nba_3pm_pg",
        "title": "Career 3-Pointers Made Per Game",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career 3-Pointers Per Game?",
        "unit": "3PM/G",
        "value_format": "{value} 3PM/G",
        "vtype": "float",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#4361EE"
    },
    {
        "ep": "ast_career.html",
        "id": "nba_total_assists",
        "title": "All-Time Total Assists",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has dished MORE Total Career Assists in NBA History?",
        "unit": "AST",
        "value_format": "{value} AST",
        "vtype": "int",
        "icon": "res://assets/icons/trophy.png",
        "theme_color": "#48CAE4"
    },
    {
        "ep": "ast_per_g_career.html",
        "id": "nba_apg",
        "title": "Career Assists Per Game (APG)",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Assists Per Game?",
        "unit": "APG",
        "value_format": "{value} APG",
        "vtype": "float",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#4CC9F0"
    },
    {
        "ep": "trb_career.html",
        "id": "nba_total_rebounds",
        "title": "All-Time Total Rebounds",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who grabbed MORE Total Career Rebounds in NBA History?",
        "unit": "REB",
        "value_format": "{value} REB",
        "vtype": "int",
        "icon": "res://assets/icons/trophy.png",
        "theme_color": "#52B788"
    },
    {
        "ep": "trb_per_g_career.html",
        "id": "nba_rpg",
        "title": "Career Rebounds Per Game (RPG)",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Rebounds Per Game?",
        "unit": "RPG",
        "value_format": "{value} RPG",
        "vtype": "float",
        "icon": "res://assets/icons/trophy.png",
        "theme_color": "#2A9D8F"
    },
    {
        "ep": "blk_career.html",
        "id": "nba_total_blocks",
        "title": "All-Time Total Blocks",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who swatted MORE Total Career Blocks in NBA History?",
        "unit": "BLK",
        "value_format": "{value} BLK",
        "vtype": "int",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#D90429"
    },
    {
        "ep": "blk_per_g_career.html",
        "id": "nba_bpg",
        "title": "Career Blocks Per Game (BPG)",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Blocks Per Game?",
        "unit": "BPG",
        "value_format": "{value} BPG",
        "vtype": "float",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#E71D36"
    },
    {
        "ep": "stl_career.html",
        "id": "nba_total_steals",
        "title": "All-Time Total Steals",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who snatched MORE Total Career Steals in NBA History?",
        "unit": "STL",
        "value_format": "{value} STL",
        "vtype": "int",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#9D4EDD"
    },
    {
        "ep": "stl_per_g_career.html",
        "id": "nba_spg",
        "title": "Career Steals Per Game (SPG)",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Steals Per Game?",
        "unit": "SPG",
        "value_format": "{value} SPG",
        "vtype": "float",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#7209B7"
    },
    {
        "ep": "tov_career.html",
        "id": "nba_total_turnovers",
        "title": "All-Time Total Turnovers",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who committed MORE Total Career Turnovers in NBA History?",
        "unit": "TO",
        "value_format": "{value} TO",
        "vtype": "int",
        "icon": "res://assets/icons/flame.png",
        "theme_color": "#FB8500"
    },
    {
        "ep": "ft_career.html",
        "id": "nba_total_ftm",
        "title": "All-Time Free Throws Made",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who made MORE Total Career Free Throws in NBA History?",
        "unit": "FTM",
        "value_format": "{value} FTM",
        "vtype": "int",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#06D6A0"
    },
    {
        "ep": "ft_per_g_career.html",
        "id": "nba_ftm_pg",
        "title": "Career Free Throws Made Per Game",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career Free Throws Per Game?",
        "unit": "FTM/G",
        "value_format": "{value} FTM/G",
        "vtype": "float",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#38B000"
    },
    {
        "ep": "fg2_career.html",
        "id": "nba_total_2pm",
        "title": "All-Time 2-Pointers Made",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who made MORE Total 2-Point Field Goals in NBA History?",
        "unit": "2PM",
        "value_format": "{value} 2PM",
        "vtype": "int",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#F15BB5"
    },
    {
        "ep": "fg2_per_g_career.html",
        "id": "nba_2pm_pg",
        "title": "Career 2-Pointers Made Per Game",
        "group": "career",
        "group_label": "Career & Stats",
        "filter_type": "player",
        "prompt": "Who has the HIGHER Career 2-Pointers Per Game?",
        "unit": "2PM/G",
        "value_format": "{value} 2PM/G",
        "vtype": "float",
        "icon": "res://assets/icons/basketball.png",
        "theme_color": "#E63946"
    }
]

def run():
    print("\n========================================================")
    print("STARTING COMPREHENSIVE NBA STATS CATEGORIES GENERATION")
    print("========================================================\n")

    # Build 17 standard categories
    for spec in CATEGORIES_SPEC:
        cat_id = spec["id"]
        ep = spec["ep"]
        vtype = spec["vtype"]
        unit = spec["unit"]
        print(f"\nProcessing {cat_id} ({spec['title']}) from {ep}...")
        
        try:
            player_dict = scrape_bref_leaderboard(ep, vtype)
            items = []
            
            # Sort descending by value
            sorted_players = sorted(player_dict.items(), key=lambda x: x[1], reverse=True)
            for name, val in sorted_players:
                if vtype == "int":
                    display = f"{val:,} {unit}"
                else:
                    display = f"{val:.2f} {unit}"
                
                item = build_player_item(name, val, display)
                items.append(item)
            
            # Build Category JSON
            cat_data = {
                "id": cat_id,
                "title": spec["title"],
                "group": spec["group"],
                "group_label": spec["group_label"],
                "filter_type": spec["filter_type"],
                "prompt": spec["prompt"],
                "unit": spec["unit"],
                "value_format": spec["value_format"],
                "icon": spec["icon"],
                "theme_color": spec["theme_color"],
                "items": items
            }
            
            out_file = os.path.join(CAT_DIR, f"{cat_id}.json")
            with open(out_file, "w", encoding="utf-8") as fp:
                json.dump(cat_data, fp, indent=2)
            print(f" -> Successfully saved {cat_id}.json with {len(items)} items!")
        except Exception as e:
            print(f" -> ERROR building {cat_id}: {e}")
        
        time.sleep(0.5)

    # Build nba_topg (Turnovers per game)
    print("\nProcessing nba_topg (Career Turnovers Per Game)...")
    try:
        tov_dict = scrape_bref_single_table("tov_career.html", "nba")
        g_dict = scrape_bref_single_table("g_career.html", "nba")
        topg_items = []
        
        for name, tov_val in tov_dict.items():
            if name in g_dict and g_dict[name] >= 100:
                topg_val = round(tov_val / g_dict[name], 2)
                item = build_player_item(name, topg_val, f"{topg_val:.2f} TOPG")
                topg_items.append(item)
        
        topg_items.sort(key=lambda x: x["value"], reverse=True)
        topg_data = {
            "id": "nba_topg",
            "title": "Career Turnovers Per Game (TOPG)",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Turnovers Per Game?",
            "unit": "TOPG",
            "value_format": "{value} TOPG",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#F77F00",
            "items": topg_items
        }
        out_file = os.path.join(CAT_DIR, "nba_topg.json")
        with open(out_file, "w", encoding="utf-8") as fp:
            json.dump(topg_data, fp, indent=2)
        print(f" -> Successfully saved nba_topg.json with {len(topg_items)} items!")
    except Exception as e:
        print(f" -> ERROR building nba_topg: {e}")

    print("\n========================================================")
    print("FINISHED EXPANDING ALL NBA STATS CATEGORIES!")
    print("========================================================\n")

if __name__ == "__main__":
    run()
