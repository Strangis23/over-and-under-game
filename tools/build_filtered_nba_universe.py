import sqlite3
import json
import os

DB_PATH = "/run/media/system/Games/Workbench/Over and Under Game/data/categories/nba data/nba.sqlite"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

os.makedirs(CAT_DIR, exist_ok=True)

TEAMS_CONFERENCE = {
    'Atlanta Hawks': ('Eastern', 'Southeast', 'Hawks'),
    'Boston Celtics': ('Eastern', 'Atlantic', 'Celtics'),
    'Brooklyn Nets': ('Eastern', 'Atlantic', 'Nets'),
    'Charlotte Hornets': ('Eastern', 'Southeast', 'Hornets'),
    'Chicago Bulls': ('Eastern', 'Central', 'Bulls'),
    'Cleveland Cavaliers': ('Eastern', 'Central', 'Cavaliers'),
    'Dallas Mavericks': ('Western', 'Southwest', 'Mavericks'),
    'Denver Nuggets': ('Western', 'Northwest', 'Nuggets'),
    'Detroit Pistons': ('Eastern', 'Central', 'Pistons'),
    'Golden State Warriors': ('Western', 'Pacific', 'Warriors'),
    'Houston Rockets': ('Western', 'Southwest', 'Rockets'),
    'Indiana Pacers': ('Eastern', 'Central', 'Pacers'),
    'LA Clippers': ('Western', 'Pacific', 'Clippers'),
    'Los Angeles Clippers': ('Western', 'Pacific', 'Clippers'),
    'Los Angeles Lakers': ('Western', 'Pacific', 'Lakers'),
    'Memphis Grizzlies': ('Western', 'Southwest', 'Grizzlies'),
    'Miami Heat': ('Eastern', 'Southeast', 'Heat'),
    'Milwaukee Bucks': ('Eastern', 'Central', 'Bucks'),
    'Minnesota Timberwolves': ('Western', 'Northwest', 'Timberwolves'),
    'New Orleans Pelicans': ('Western', 'Southwest', 'Pelicans'),
    'New York Knicks': ('Eastern', 'Atlantic', 'Knicks'),
    'Oklahoma City Thunder': ('Western', 'Northwest', 'Thunder'),
    'Orlando Magic': ('Eastern', 'Southeast', 'Magic'),
    'Philadelphia 76ers': ('Eastern', 'Atlantic', '76ers'),
    'Phoenix Suns': ('Western', 'Pacific', 'Suns'),
    'Portland Trail Blazers': ('Western', 'Northwest', 'Trail Blazers'),
    'Sacramento Kings': ('Western', 'Pacific', 'Kings'),
    'San Antonio Spurs': ('Western', 'Southwest', 'Spurs'),
    'Toronto Raptors': ('Eastern', 'Atlantic', 'Raptors'),
    'Utah Jazz': ('Western', 'Northwest', 'Jazz'),
    'Washington Wizards': ('Eastern', 'Southeast', 'Wizards'),
}

NICKNAME_TO_FULL = {v[2]: k for k, v in TEAMS_CONFERENCE.items()}

def get_decades(from_y, to_y):
    if not from_y:
        return ['2020s']
    decs = set()
    fy = int(from_y)
    ty = int(to_y) if to_y else fy
    for y in range(fy, ty + 1):
        if y < 1980:
            decs.add('1980s & Prior')
        elif y <= 1989:
            decs.add('1980s & Prior')
        elif y <= 1999:
            decs.add('1990s')
        elif y <= 2009:
            decs.add('2000s')
        elif y <= 2019:
            decs.add('2010s')
        else:
            decs.add('2020s')
    return sorted(list(decs))

def get_positions(pos_str):
    if not pos_str:
        return ['Forward']
    p = pos_str.lower()
    res = []
    if 'guard' in p:
        res.append('Guard')
    if 'forward' in p:
        res.append('Forward')
    if 'center' in p:
        res.append('Center')
    return res if res else ['Forward']

def parse_height_to_inches(ht_str):
    if not ht_str or '-' not in ht_str:
        return None
    try:
        parts = ht_str.split('-')
        return int(parts[0]) * 12 + int(parts[1])
    except Exception:
        return None

def build():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1. Height Category (Feet & Inches)
    cur.execute('''
    SELECT person_id, display_first_last, height, weight, team_name, position, from_year, to_year, rosterstatus
    FROM common_player_info
    WHERE height IS NOT NULL AND height != '' AND (greatest_75_flag = 'Y' OR rosterstatus = 'Active' OR season_exp >= 4)
    GROUP BY display_first_last
    ORDER BY greatest_75_flag DESC, season_exp DESC, RANDOM();
    ''')
    rows = cur.fetchall()
    height_items = []
    seen = set()
    for pid, name, ht_str, wt, team_name, pos, from_y, to_y, status in rows:
        inches = parse_height_to_inches(ht_str)
        if inches and name not in seen:
            seen.add(name)
            feet = inches // 12
            rem = inches % 12
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            height_items.append({
                "name": name,
                "subtext": f"{positions[0]} • {t_name}",
                "value": inches,
                "display_value": f"{feet} ft {rem} in",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y, to_y),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else 2000,
                "to_year": int(to_y) if to_y else 2024
            })
            if len(height_items) >= 200:
                break

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
    print(f"Created nba_height.json with {len(height_items)} items")

    # 2. Weight Category
    cur.execute('''
    SELECT person_id, display_first_last, height, weight, team_name, position, from_year, to_year, rosterstatus
    FROM common_player_info
    WHERE weight IS NOT NULL AND weight != '' AND (greatest_75_flag = 'Y' OR rosterstatus = 'Active' OR season_exp >= 4)
    GROUP BY display_first_last
    ORDER BY greatest_75_flag DESC, season_exp DESC, RANDOM();
    ''')
    rows = cur.fetchall()
    weight_items = []
    seen = set()
    for pid, name, ht_str, wt_str, team_name, pos, from_y, to_y, status in rows:
        try:
            wt = float(wt_str)
        except Exception:
            continue
        if wt and name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            weight_items.append({
                "name": name,
                "subtext": f"{positions[0]} • {t_name}",
                "value": wt,
                "display_value": f"{int(wt)} lbs",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y, to_y),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else 2000,
                "to_year": int(to_y) if to_y else 2024
            })
            if len(weight_items) >= 200:
                break

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
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF4500",
            "items": weight_items
        }, f, indent=2)
    print(f"Created nba_weight.json with {len(weight_items)} items")

    # 3. Combine Wingspan
    cur.execute('''
    SELECT c.player_id, c.player_name, c.wingspan, c.position, c.season, p.team_name, p.from_year, p.to_year, p.rosterstatus
    FROM draft_combine_stats c
    LEFT JOIN common_player_info p ON c.player_id = p.person_id
    WHERE c.wingspan IS NOT NULL AND c.wingspan > 70
    ORDER BY c.wingspan DESC;
    ''')
    rows = cur.fetchall()
    wingspan_items = []
    seen = set()
    for pid, name, ws, pos, season, team_name, from_y, to_y, status in rows:
        if name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            wingspan_items.append({
                "name": name,
                "subtext": f"{positions[0]} • Draft Combine {season}",
                "value": round(float(ws), 1),
                "display_value": f"{round(float(ws), 1)}\" Wingspan",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y or season, to_y or season),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else (int(season) if season else 2010),
                "to_year": int(to_y) if to_y else (int(season) if season else 2024)
            })
            if len(wingspan_items) >= 150:
                break

    with open(os.path.join(CAT_DIR, "nba_wingspan.json"), "w") as f:
        json.dump({
            "id": "nba_wingspan",
            "title": "Combine Wingspan",
            "group": "physical",
            "group_label": "Physical Attributes",
            "filter_type": "player",
            "prompt": "Who has the LONGER Wingspan (Inches)?",
            "unit": "in",
            "value_format": "{value}\" Wingspan",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#9370DB",
            "items": wingspan_items
        }, f, indent=2)
    print(f"Created nba_wingspan.json with {len(wingspan_items)} items")

    # 4. Combine Max Vertical Leap
    cur.execute('''
    SELECT c.player_id, c.player_name, c.max_vertical_leap, c.position, c.season, p.team_name, p.from_year, p.to_year, p.rosterstatus
    FROM draft_combine_stats c
    LEFT JOIN common_player_info p ON c.player_id = p.person_id
    WHERE c.max_vertical_leap IS NOT NULL AND c.max_vertical_leap > 28
    ORDER BY c.max_vertical_leap DESC;
    ''')
    rows = cur.fetchall()
    vertical_items = []
    seen = set()
    for pid, name, vert, pos, season, team_name, from_y, to_y, status in rows:
        if name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            vertical_items.append({
                "name": name,
                "subtext": f"{positions[0]} • Draft Combine {season}",
                "value": round(float(vert), 1),
                "display_value": f"{round(float(vert), 1)}\" Vertical",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y or season, to_y or season),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else (int(season) if season else 2010),
                "to_year": int(to_y) if to_y else (int(season) if season else 2024)
            })
            if len(vertical_items) >= 150:
                break

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
            "items": vertical_items
        }, f, indent=2)
    print(f"Created nba_vertical_leap.json with {len(vertical_items)} items")

    # 5. Combine Bench Press Reps
    cur.execute('''
    SELECT c.player_id, c.player_name, c.bench_press, c.position, c.season, p.team_name, p.from_year, p.to_year, p.rosterstatus
    FROM draft_combine_stats c
    LEFT JOIN common_player_info p ON c.player_id = p.person_id
    WHERE c.bench_press IS NOT NULL AND c.bench_press > 0
    ORDER BY c.bench_press DESC;
    ''')
    rows = cur.fetchall()
    bench_items = []
    seen = set()
    for pid, name, bp, pos, season, team_name, from_y, to_y, status in rows:
        if name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            bench_items.append({
                "name": name,
                "subtext": f"{positions[0]} • Draft Combine {season}",
                "value": int(bp),
                "display_value": f"{int(bp)} Reps",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y or season, to_y or season),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else (int(season) if season else 2010),
                "to_year": int(to_y) if to_y else (int(season) if season else 2024)
            })
            if len(bench_items) >= 150:
                break

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
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#32CD32",
            "items": bench_items
        }, f, indent=2)
    print(f"Created nba_bench_press.json with {len(bench_items)} items")

    # 6. Career Longevity / Seasons Played
    cur.execute('''
    SELECT person_id, display_first_last, season_exp, team_name, position, from_year, to_year, rosterstatus
    FROM common_player_info
    WHERE season_exp IS NOT NULL AND season_exp >= 3 AND (greatest_75_flag = 'Y' OR season_exp >= 8 OR rosterstatus = 'Active')
    GROUP BY display_first_last
    ORDER BY season_exp DESC, RANDOM();
    ''')
    rows = cur.fetchall()
    seasons_items = []
    seen = set()
    for pid, name, exp, team_name, pos, from_y, to_y, status in rows:
        if name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            seasons_items.append({
                "name": name,
                "subtext": f"{positions[0]} • {t_name}",
                "value": int(exp),
                "display_value": f"{int(exp)} Seasons",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y, to_y),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else 2000,
                "to_year": int(to_y) if to_y else 2024
            })
            if len(seasons_items) >= 200:
                break

    with open(os.path.join(CAT_DIR, "nba_seasons_played.json"), "w") as f:
        json.dump({
            "id": "nba_seasons_played",
            "title": "Seasons Played (Longevity)",
            "group": "career",
            "group_label": "Career & Draft",
            "filter_type": "player",
            "prompt": "Who played MORE Seasons in the NBA?",
            "unit": "seasons",
            "value_format": "{value} Seasons",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF8C00",
            "items": seasons_items
        }, f, indent=2)
    print(f"Created nba_seasons_played.json with {len(seasons_items)} items")

    # 7. Overall Draft Pick
    cur.execute('''
    SELECT person_id, display_first_last, draft_number, draft_year, team_name, position, from_year, to_year, rosterstatus
    FROM common_player_info
    WHERE draft_number IS NOT NULL AND draft_number != 'Undrafted' AND CAST(draft_number AS INTEGER) > 0
    AND (greatest_75_flag = 'Y' OR season_exp >= 5 OR rosterstatus = 'Active')
    GROUP BY display_first_last
    ORDER BY draft_year DESC, RANDOM();
    ''')
    rows = cur.fetchall()
    draft_items = []
    seen = set()
    for pid, name, dnum, dyear, team_name, pos, from_y, to_y, status in rows:
        try:
            pick_num = int(dnum)
        except Exception:
            continue
        if name not in seen:
            seen.add(name)
            t_name = team_name or 'NBA'
            full_team = NICKNAME_TO_FULL.get(t_name, t_name)
            positions = get_positions(pos)
            draft_items.append({
                "name": name,
                "subtext": f"{positions[0]} • Draft Class {dyear or ''}",
                "value": pick_num,
                "display_value": f"Pick #{pick_num}",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png",
                "position": positions[0],
                "positions": positions,
                "team": t_name,
                "team_full": full_team,
                "decades": get_decades(from_y or dyear, to_y or dyear),
                "status": "Active" if status == "Active" else "Retired",
                "from_year": int(from_y) if from_y else 2000,
                "to_year": int(to_y) if to_y else 2024
            })
            if len(draft_items) >= 200:
                break

    with open(os.path.join(CAT_DIR, "nba_draft_pick.json"), "w") as f:
        json.dump({
            "id": "nba_draft_pick",
            "title": "Overall Draft Pick Number",
            "group": "career",
            "group_label": "Career & Draft",
            "filter_type": "player",
            "prompt": "Who had the HIGHER Overall Draft Pick Number (Drafted Later)?",
            "unit": "pick",
            "value_format": "Pick #{value}",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#DA70D6",
            "items": draft_items
        }, f, indent=2)
    print(f"Created nba_draft_pick.json with {len(draft_items)} items")

    # 8. NBA PPG
    ppg_path = os.path.join(CAT_DIR, "nba_ppg.json")
    if os.path.exists(ppg_path):
        with open(ppg_path, "r") as f:
            ppg_data = json.load(f)
        for it in ppg_data.get("items", []):
            name = it["name"]
            cur.execute("SELECT team_name, position, from_year, to_year, rosterstatus, person_id FROM common_player_info WHERE display_first_last = ? LIMIT 1;", (name,))
            r = cur.fetchone()
            if r:
                t_name = r[0] or 'NBA'
                it["team"] = t_name
                it["team_full"] = NICKNAME_TO_FULL.get(t_name, t_name)
                it["positions"] = get_positions(r[1])
                it["position"] = it["positions"][0]
                it["decades"] = get_decades(r[2], r[3])
                it["status"] = "Active" if r[4] == "Active" else "Retired"
                it["from_year"] = int(r[2]) if r[2] else 1990
                it["to_year"] = int(r[3]) if r[3] else 2024
                if not it.get("image_url") and r[5]:
                    it["image_url"] = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{r[5]}.png"
            else:
                it["positions"] = ["Guard"]
                it["position"] = "Guard"
                it["team"] = "NBA"
                it["team_full"] = "NBA"
                it["decades"] = ["1990s", "2000s"]
                it["status"] = "Retired"
            it["display_value"] = f"{it['value']} PPG"

        ppg_data["filter_type"] = "player"
        with open(ppg_path, "w") as f:
            json.dump(ppg_data, f, indent=2)
        print(f"Updated nba_ppg.json with filter metadata ({len(ppg_data['items'])} items)")

    # 9. All-Time Regular Season Wins (Franchises)
    cur.execute('''
    WITH home_stats AS (
        SELECT team_id_home as team_id, COUNT(*) as g_home, SUM(CASE WHEN wl_home='W' THEN 1 ELSE 0 END) as w_home
        FROM game WHERE season_type = 'Regular Season' GROUP BY team_id_home
    ),
    away_stats AS (
        SELECT team_id_away as team_id, COUNT(*) as g_away, SUM(CASE WHEN wl_away='W' THEN 1 ELSE 0 END) as w_away
        FROM game WHERE season_type = 'Regular Season' GROUP BY team_id_away
    )
    SELECT t.id, t.full_name, t.city, t.abbreviation,
           (h.w_home + a.w_away) as total_wins,
           ROUND(CAST((h.w_home + a.w_away) AS FLOAT) / (h.g_home + a.g_away) * 100, 1) as win_pct
    FROM team t
    JOIN home_stats h ON t.id = h.team_id
    JOIN away_stats a ON t.id = a.team_id
    ORDER BY total_wins DESC;
    ''')
    rows = cur.fetchall()
    wins_items = []
    pct_items = []
    for tid, full_name, city, abbrev, total_wins, win_pct in rows:
        conf, div, nick = TEAMS_CONFERENCE.get(full_name, ('Eastern', 'Atlantic', full_name))
        wins_items.append({
            "name": full_name,
            "subtext": f"{city} • {conf} Conference",
            "value": int(total_wins),
            "display_value": f"{int(total_wins)} Wins",
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg",
            "conference": conf,
            "division": div,
            "team": nick
        })
        pct_items.append({
            "name": full_name,
            "subtext": f"{city} • {conf} Conference",
            "value": float(win_pct),
            "display_value": f"{float(win_pct)}% Win Rate",
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg",
            "conference": conf,
            "division": div,
            "team": nick
        })

    with open(os.path.join(CAT_DIR, "nba_franchise_wins.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_wins",
            "title": "All-Time Franchise Wins",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "filter_type": "team",
            "prompt": "Which franchise has MORE All-Time Regular Season Wins?",
            "unit": "wins",
            "value_format": "{value} Wins",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#1E90FF",
            "items": wins_items
        }, f, indent=2)

    with open(os.path.join(CAT_DIR, "nba_franchise_win_pct.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_win_pct",
            "title": "All-Time Franchise Win %",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "filter_type": "team",
            "prompt": "Which franchise has the HIGHER All-Time Win Percentage?",
            "unit": "%",
            "value_format": "{value}% Win Rate",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#20B2AA",
            "items": pct_items
        }, f, indent=2)

    # 11. Arena Seating Capacity
    cur.execute('''
    SELECT t.id, t.full_name, t.city, t.abbreviation, td.arena, td.arenacapacity
    FROM team t
    JOIN team_details td ON t.id = td.team_id
    WHERE td.arenacapacity IS NOT NULL AND td.arenacapacity > 10000
    ORDER BY td.arenacapacity DESC;
    ''')
    rows = cur.fetchall()
    arena_items = []
    for tid, full_name, city, abbrev, arena, cap in rows:
        conf, div, nick = TEAMS_CONFERENCE.get(full_name, ('Eastern', 'Atlantic', full_name))
        arena_items.append({
            "name": full_name,
            "subtext": f"{arena or 'Arena'} • {conf} Conf",
            "value": int(cap),
            "display_value": f"{int(cap):,} Seats",
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg",
            "conference": conf,
            "division": div,
            "team": nick
        })

    with open(os.path.join(CAT_DIR, "nba_arena_capacity.json"), "w") as f:
        json.dump({
            "id": "nba_arena_capacity",
            "title": "Arena Seating Capacity",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "filter_type": "team",
            "prompt": "Which NBA team plays in the LARGER Arena (Seating Capacity)?",
            "unit": "seats",
            "value_format": "{value} Seats",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF6347",
            "items": arena_items
        }, f, indent=2)

    # 12. Year Founded
    cur.execute('''
    SELECT t.id, t.full_name, t.city, t.abbreviation, td.yearfounded
    FROM team t
    JOIN team_details td ON t.id = td.team_id
    WHERE td.yearfounded IS NOT NULL
    ORDER BY td.yearfounded ASC;
    ''')
    rows = cur.fetchall()
    founded_items = []
    for tid, full_name, city, abbrev, yf in rows:
        conf, div, nick = TEAMS_CONFERENCE.get(full_name, ('Eastern', 'Atlantic', full_name))
        age = 2026 - int(yf)
        founded_items.append({
            "name": full_name,
            "subtext": f"Founded {int(yf)} • {conf} Conf",
            "value": age,
            "display_value": f"{age} Years Old (Est. {int(yf)})",
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg",
            "conference": conf,
            "division": div,
            "team": nick
        })

    with open(os.path.join(CAT_DIR, "nba_franchise_founded.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_founded",
            "title": "Franchise Age (Years Established)",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "filter_type": "team",
            "prompt": "Which franchise is OLDER (More Years Established)?",
            "unit": "years",
            "value_format": "{value} Years Old",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#8A2BE2",
            "items": founded_items
        }, f, indent=2)

    print("=== Successfully rebuilt all categories with rich filtering metadata! ===")

if __name__ == "__main__":
    build()
