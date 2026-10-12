#!/usr/bin/env python3
import os
import io
import re
import glob
import json
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from PIL import Image

ASSETS_DIR = "/run/media/system/Games/Workbench/Over and Under Game/assets/images/nba"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/jpeg,image/png,*/*;q=0.8"
}
WIKI_HEADERS = {
    "User-Agent": "OverAndUnderTriviaGame/2.0 (contact: dev@overundergame.org)"
}

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

# 1. Build cache of existing player metadata & images from current categories
existing_catalog = {}
for path in glob.glob(os.path.join(CAT_DIR, "*.json")):
    with open(path) as fp:
        d = json.load(fp)
    for it in d.get("items", []):
        name = it.get("name", "")
        if name and name not in existing_catalog:
            existing_catalog[name] = it

class WikiTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.rows = []
        self.curr_row = []
        self.curr_text = ""
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_row = True
            self.curr_row = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.curr_text = ""
    def handle_endtag(self, tag):
        if tag == "tr":
            if self.curr_row:
                self.rows.append(self.curr_row)
            self.in_row = False
        elif tag in ("td", "th"):
            self.curr_row.append(self.curr_text.strip())
            self.in_cell = False
    def handle_data(self, data):
        if self.in_cell:
            self.curr_text += data

def fetch_wiki_table(page_name):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_name)}&redirects=1&prop=text&format=json"
    req = urllib.request.Request(url, headers=WIKI_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode())
        tp = WikiTableParser()
        tp.feed(d.get("parse", {}).get("text", {}).get("*", ""))
        return [row for row in tp.rows if row and row[0].isdigit()]

def clean_player_name(raw_name):
    name = re.sub(r"[\*\^\†\§\[\d\]#]", "", raw_name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def parse_positions(pos_str):
    pos_upper = pos_str.upper()
    positions = []
    if "PG" in pos_upper or "SG" in pos_upper or "G" in pos_upper:
        positions.append("Guard")
    if "SF" in pos_upper or "PF" in pos_upper or "F" in pos_upper:
        positions.append("Forward")
    if "C" in pos_upper:
        positions.append("Center")
    if not positions:
        positions = ["Forward"]
    primary = positions[0]
    return primary, positions

def parse_teams(teams_str):
    parts = re.split(r"(?<=\))\s*", teams_str)
    best_team = None
    max_years = -1
    earliest = 9999
    latest = 0
    is_active = False

    for p in parts:
        m = re.match(r"([A-Za-z0-9\s/]+)\s*\((.+)\)", p.strip())
        if m:
            tname = m.group(1).strip()
            years_str = m.group(2)
            if "present" in years_str:
                is_active = True
                latest = max(latest, 2026)
            years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", years_str)]
            if years:
                earliest = min(earliest, min(years))
                latest = max(latest, max(years))
                span = (max(years) - min(years) + 1)
                if span > max_years:
                    max_years = span
                    best_team = tname

    if not best_team:
        best_team = "NBA"
    if "/" in best_team:
        best_team = best_team.split("/")[-1].strip()
    short_name = best_team.split()[-1]
    return short_name, best_team, (earliest if earliest < 9000 else 1990), (latest if latest > 0 else 2024), is_active

def get_decades(from_yr, to_yr):
    decades = set()
    for yr in range(from_yr, to_yr + 1, 5):
        d = (yr // 10) * 10
        if d <= 1980: decades.add("1980s & Prior")
        elif d == 1990: decades.add("1990s")
        elif d == 2000: decades.add("2000s")
        elif d == 2010: decades.add("2010s")
        elif d >= 2020: decades.add("2020s")
    for yr in (from_yr, to_yr):
        d = (yr // 10) * 10
        if d <= 1980: decades.add("1980s & Prior")
        elif d == 1990: decades.add("1990s")
        elif d == 2000: decades.add("2000s")
        elif d == 2010: decades.add("2010s")
        elif d >= 2020: decades.add("2020s")
    order = ["1980s & Prior", "1990s", "2000s", "2010s", "2020s"]
    return [d for d in order if d in decades]

def ensure_player_image(name, team):
    clean_name = name.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("'", "")
    cand1 = os.path.join(ASSETS_DIR, f"{clean_name}.webp")
    if os.path.exists(cand1):
        return f"res://assets/images/nba/{clean_name}.webp"

    # Check existing catalog
    if name in existing_catalog and "image" in existing_catalog[name]:
        img_p = existing_catalog[name]["image"].replace("res://", "")
        if os.path.exists(img_p):
            return existing_catalog[name]["image"]

    # Try Wikipedia fetch
    try:
        query = f"{name} basketball"
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            search = data.get("query", {}).get("search", [])
            if search:
                title = search[0]["title"]
                url2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=600"
                req2 = urllib.request.Request(url2, headers=WIKI_HEADERS)
                with urllib.request.urlopen(req2, timeout=5) as resp2:
                    data2 = json.loads(resp2.read().decode())
                    pages = data2.get("query", {}).get("pages", {})
                    for p in pages.values():
                        if "thumbnail" in p:
                            img_url = p["thumbnail"]["source"]
                            req3 = urllib.request.Request(img_url, headers=HEADERS)
                            with urllib.request.urlopen(req3, timeout=5) as r3:
                                im = Image.open(io.BytesIO(r3.read()))
                                im = im.convert("RGBA").resize((360, 450), Image.Resampling.LANCZOS)
                                im.save(cand1, "WEBP", quality=82)
                                return f"res://assets/images/nba/{clean_name}.webp"
    except Exception:
        pass

    # Fallback to team card
    team_clean = team.lower().strip()
    team_file = TEAM_MAP.get(team_clean, "nba_league.webp")
    return f"res://assets/images/nba/{team_file}"

def build_player_item(name, pos_str, teams_str, stat_val, stat_display):
    clean_name = clean_player_name(name)
    primary_pos, positions = parse_positions(pos_str)
    short_team, full_team, from_yr, to_yr, is_active = parse_teams(teams_str)
    
    # Check if catalog has richer info
    if clean_name in existing_catalog:
        cat_info = existing_catalog[clean_name]
        primary_pos = cat_info.get("position", primary_pos)
        positions = cat_info.get("positions", positions)
        short_team = cat_info.get("team", short_team)
        full_team = cat_info.get("team_full", full_team)
        from_yr = cat_info.get("from_year", from_yr)
        to_yr = cat_info.get("to_year", to_yr)
        status = cat_info.get("status", "Active" if is_active else "Retired")
        image_res = cat_info.get("image", "")
    else:
        status = "Active" if is_active else "Retired"
        image_res = ""

    if not image_res or not os.path.exists(image_res.replace("res://", "")):
        image_res = ensure_player_image(clean_name, short_team)

    decades = get_decades(from_yr, to_yr)
    subtext = f"{primary_pos} • {short_team}"

    return {
        "name": clean_name,
        "subtext": subtext,
        "value": stat_val,
        "display_value": stat_display,
        "position": primary_pos,
        "positions": positions,
        "team": short_team,
        "team_full": full_team,
        "decades": decades,
        "status": status,
        "from_year": from_yr,
        "to_year": to_yr,
        "image": image_res
    }

def generate_categories():
    print("=== Scraping Official All-Time NBA Stat Leaders ===")
    
    # 1. SCORING & 2-POINTERS
    print("Fetching career scoring leaders...")
    scoring_rows = fetch_wiki_table("List of NBA career scoring leaders")
    
    items_total_pts = []
    items_total_2pm = []
    items_2pm_pg = []
    
    for r in scoring_rows:
        try:
            name = r[1]
            pos = r[2]
            teams = r[3]
            pts = int(r[4].replace(",", ""))
            games = int(r[5].replace(",", ""))
            fgm = int(r[7].replace(",", ""))
            threes = int(r[8].replace(",", "")) if len(r) > 8 and r[8].replace(",", "").isdigit() else 0
            twos = fgm - threes
            twos_pg = round(twos / games, 2)
            
            items_total_pts.append(build_player_item(name, pos, teams, pts, f"{pts:,} PTS"))
            items_total_2pm.append(build_player_item(name, pos, teams, twos, f"{twos:,} 2PM"))
            items_2pm_pg.append(build_player_item(name, pos, teams, twos_pg, f"{twos_pg:.2f} 2PM/G"))
        except Exception as e:
            print(f"Error parsing scoring row: {r}: {e}")

    # 2. ASSISTS
    print("Fetching career assists leaders...")
    assists_rows = fetch_wiki_table("List of NBA career assists leaders")
    items_total_ast = []
    items_apg = []
    for r in assists_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            ast = int(r[4].replace(",", ""))
            apg = float(r[6].replace(",", ""))
            items_total_ast.append(build_player_item(name, pos, teams, ast, f"{ast:,} AST"))
            items_apg.append(build_player_item(name, pos, teams, apg, f"{apg:.2f} APG"))
        except Exception as e:
            print(f"Error parsing assist row: {e}")

    # 3. REBOUNDS
    print("Fetching career rebounding leaders...")
    reb_rows = fetch_wiki_table("List of NBA career rebounding leaders")
    items_total_reb = []
    items_rpg = []
    for r in reb_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            reb = int(r[4].replace(",", ""))
            rpg = float(r[6].replace(",", ""))
            items_total_reb.append(build_player_item(name, pos, teams, reb, f"{reb:,} REB"))
            items_rpg.append(build_player_item(name, pos, teams, rpg, f"{rpg:.2f} RPG"))
        except Exception as e:
            print(f"Error parsing reb row: {e}")

    # 4. BLOCKS
    print("Fetching career blocks leaders...")
    blk_rows = fetch_wiki_table("List of NBA career blocks leaders")
    items_total_blk = []
    items_bpg = []
    for r in blk_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            blk = int(r[4].replace(",", ""))
            bpg = float(r[6].replace(",", ""))
            items_total_blk.append(build_player_item(name, pos, teams, blk, f"{blk:,} BLK"))
            items_bpg.append(build_player_item(name, pos, teams, bpg, f"{bpg:.2f} BPG"))
        except Exception as e:
            print(f"Error parsing blk row: {e}")

    # 5. STEALS
    print("Fetching career steals leaders...")
    stl_rows = fetch_wiki_table("List of NBA career steals leaders")
    items_total_stl = []
    items_spg = []
    for r in stl_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            stl = int(r[4].replace(",", ""))
            spg = float(r[6].replace(",", ""))
            items_total_stl.append(build_player_item(name, pos, teams, stl, f"{stl:,} STL"))
            items_spg.append(build_player_item(name, pos, teams, spg, f"{spg:.2f} SPG"))
        except Exception as e:
            print(f"Error parsing stl row: {e}")

    # 6. TURNOVERS
    print("Fetching career turnovers leaders...")
    to_rows = fetch_wiki_table("List of NBA career turnovers leaders")
    items_total_to = []
    items_topg = []
    for r in to_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            to_val = int(r[4].replace(",", ""))
            topg = float(r[6].replace(",", ""))
            items_total_to.append(build_player_item(name, pos, teams, to_val, f"{to_val:,} TO"))
            items_topg.append(build_player_item(name, pos, teams, topg, f"{topg:.2f} TOPG"))
        except Exception as e:
            print(f"Error parsing to row: {e}")

    # 7. 3-POINTERS
    print("Fetching career 3-point leaders...")
    threes_rows = fetch_wiki_table("List of NBA career 3-point scoring leaders")
    items_total_3pm = []
    items_3pm_pg = []
    for r in threes_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            threes_val = int(r[4].replace(",", ""))
            tpg = float(r[7].replace(",", ""))
            items_total_3pm.append(build_player_item(name, pos, teams, threes_val, f"{threes_val:,} 3PM"))
            items_3pm_pg.append(build_player_item(name, pos, teams, tpg, f"{tpg:.2f} 3PM/G"))
        except Exception as e:
            print(f"Error parsing 3pt row: {e}")

    # 8. FREE THROWS
    print("Fetching career free throw leaders...")
    ft_rows = fetch_wiki_table("List of NBA career free throw scoring leaders")
    items_total_ftm = []
    items_ftm_pg = []
    for r in ft_rows:
        try:
            name, pos, teams = r[1], r[2], r[3]
            ftm = int(r[4].replace(",", ""))
            ft_pg = float(r[7].replace(",", ""))
            items_total_ftm.append(build_player_item(name, pos, teams, ftm, f"{ftm:,} FTM"))
            items_ftm_pg.append(build_player_item(name, pos, teams, ft_pg, f"{ft_pg:.2f} FTM/G"))
        except Exception as e:
            print(f"Error parsing ft row: {e}")

    # Dictionary of all categories to write
    categories_def = [
        # --- PER-GAME CATEGORIES ---
        {
            "id": "nba_apg",
            "title": "Career Assists Per Game (APG)",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Assists Per Game?",
            "unit": "APG",
            "value_format": "{value} APG",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#00B4D8",
            "items": items_apg
        },
        {
            "id": "nba_rpg",
            "title": "Career Rebounds Per Game (RPG)",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Rebounds Per Game?",
            "unit": "RPG",
            "value_format": "{value} RPG",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#2EC4B6",
            "items": items_rpg
        },
        {
            "id": "nba_bpg",
            "title": "Career Blocks Per Game (BPG)",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Blocks Per Game?",
            "unit": "BPG",
            "value_format": "{value} BPG",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#E71D36",
            "items": items_bpg
        },
        {
            "id": "nba_spg",
            "title": "Career Steals Per Game (SPG)",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Steals Per Game?",
            "unit": "SPG",
            "value_format": "{value} SPG",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#7209B7",
            "items": items_spg
        },
        {
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
            "items": items_topg
        },
        {
            "id": "nba_3pm_pg",
            "title": "Career 3-Pointers Made Per Game",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career 3-Pointers Per Game?",
            "unit": "3PM/G",
            "value_format": "{value} 3PM/G",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#4361EE",
            "items": items_3pm_pg
        },
        {
            "id": "nba_2pm_pg",
            "title": "Career 2-Pointers Made Per Game",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career 2-Pointers Per Game?",
            "unit": "2PM/G",
            "value_format": "{value} 2PM/G",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#E63946",
            "items": items_2pm_pg
        },
        {
            "id": "nba_ftm_pg",
            "title": "Career Free Throws Made Per Game",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has the HIGHER Career Free Throws Per Game?",
            "unit": "FTM/G",
            "value_format": "{value} FTM/G",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#38B000",
            "items": items_ftm_pg
        },
        # --- TOTALS CATEGORIES ---
        {
            "id": "nba_total_points",
            "title": "All-Time Total Points",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has scored MORE Total Career Points in NBA History?",
            "unit": "PTS",
            "value_format": "{value} PTS",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FFB703",
            "items": items_total_pts
        },
        {
            "id": "nba_total_3pm",
            "title": "All-Time 3-Pointers Made",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has made MORE Total 3-Pointers in NBA History?",
            "unit": "3PM",
            "value_format": "{value} 3PM",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#4CC9F0",
            "items": items_total_3pm
        },
        {
            "id": "nba_total_assists",
            "title": "All-Time Total Assists",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who has dished MORE Total Career Assists in NBA History?",
            "unit": "AST",
            "value_format": "{value} AST",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#48CAE4",
            "items": items_total_ast
        },
        {
            "id": "nba_total_rebounds",
            "title": "All-Time Total Rebounds",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who grabbed MORE Total Career Rebounds in NBA History?",
            "unit": "REB",
            "value_format": "{value} REB",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#52B788",
            "items": items_total_reb
        },
        {
            "id": "nba_total_blocks",
            "title": "All-Time Total Blocks",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who swatted MORE Total Career Blocks in NBA History?",
            "unit": "BLK",
            "value_format": "{value} BLK",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#D90429",
            "items": items_total_blk
        },
        {
            "id": "nba_total_steals",
            "title": "All-Time Total Steals",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who snatched MORE Total Career Steals in NBA History?",
            "unit": "STL",
            "value_format": "{value} STL",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#9D4EDD",
            "items": items_total_stl
        },
        {
            "id": "nba_total_turnovers",
            "title": "All-Time Total Turnovers",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who committed MORE Total Career Turnovers in NBA History?",
            "unit": "TO",
            "value_format": "{value} TO",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#FB8500",
            "items": items_total_to
        },
        {
            "id": "nba_total_ftm",
            "title": "All-Time Free Throws Made",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who made MORE Total Career Free Throws in NBA History?",
            "unit": "FTM",
            "value_format": "{value} FTM",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#06D6A0",
            "items": items_total_ftm
        },
        {
            "id": "nba_total_2pm",
            "title": "All-Time 2-Pointers Made",
            "group": "career",
            "group_label": "Career & Stats",
            "filter_type": "player",
            "prompt": "Who made MORE Total 2-Point Field Goals in NBA History?",
            "unit": "2PM",
            "value_format": "{value} 2PM",
            "icon": "res://assets/icons/basketball.png",
            "theme_color": "#F15BB5",
            "items": items_total_2pm
        }
    ]

    print("\nWriting category files to disk...")
    for cat in categories_def:
        out_path = os.path.join(CAT_DIR, f"{cat['id']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cat, f, indent=2)
        print(f"  Saved {os.path.basename(out_path)} with {len(cat['items'])} items")

    print("\n=== Done building all stats categories! ===")

if __name__ == "__main__":
    generate_categories()
