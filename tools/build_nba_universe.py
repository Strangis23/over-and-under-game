import sqlite3
import json
import os

DB_PATH = "/run/media/system/Games/Workbench/Over and Under Game/data/categories/nba data/nba.sqlite"
CAT_DIR = "/run/media/system/Games/Workbench/Over and Under Game/data/categories"

os.makedirs(CAT_DIR, exist_ok=True)

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

    # 1. Height Category (NO height spoiler in subtext!)
    cur.execute('''
    SELECT person_id, display_first_last, height, weight, team_name, position
    FROM common_player_info
    WHERE height IS NOT NULL AND height != '' AND (greatest_75_flag = 'Y' OR rosterstatus = 'Active' OR season_exp >= 10)
    GROUP BY display_first_last
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    height_items = []
    seen = set()
    for pid, name, ht_str, wt, team_name, pos in rows:
        inches = parse_height_to_inches(ht_str)
        if inches and name not in seen:
            seen.add(name)
            feet = inches // 12
            rem_inches = inches % 12
            height_items.append({
                "name": name,
                "subtext": f"{pos or 'Player'} • {team_name or 'NBA'}",
                "value": inches,
                "display_value": f"{feet} ft {rem_inches} in",
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(height_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_height.json"), "w") as f:
        json.dump({
            "id": "nba_height",
            "title": "Player Height",
            "group": "physical",
            "group_label": "Physical Attributes",
            "prompt": "Who is TALLER (Feet & Inches)?",
            "unit": "ft/in",
            "value_format": "{feet} ft {inches} in",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#00BFFF",
            "items": height_items
        }, f, indent=2)
    print(f"Created nba_height.json with {len(height_items)} items")

    # 2. Weight Category (NO weight spoiler in subtext!)
    cur.execute('''
    SELECT person_id, display_first_last, height, weight, team_name, position
    FROM common_player_info
    WHERE weight IS NOT NULL AND weight != '' AND (greatest_75_flag = 'Y' OR rosterstatus = 'Active' OR season_exp >= 10)
    GROUP BY display_first_last
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    weight_items = []
    seen = set()
    for pid, name, ht_str, wt_str, team_name, pos in rows:
        try:
            wt = float(wt_str)
        except Exception:
            continue
        if wt and name not in seen:
            seen.add(name)
            weight_items.append({
                "name": name,
                "subtext": f"{pos or 'Player'} • {team_name or 'NBA'}",
                "value": wt,
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(weight_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_weight.json"), "w") as f:
        json.dump({
            "id": "nba_weight",
            "title": "Player Weight",
            "group": "physical",
            "group_label": "Physical Attributes",
            "prompt": "Who is HEAVIER (Weight in LBS)?",
            "unit": "lbs",
            "value_format": "{value} lbs",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF4500",
            "items": weight_items
        }, f, indent=2)
    print(f"Created nba_weight.json with {len(weight_items)} items")

    # 3. Wingspan (inches) (NO wingspan spoiler in subtext!)
    cur.execute('''
    SELECT c.player_id, c.player_name, c.wingspan, c.position, c.season
    FROM draft_combine_stats c
    WHERE c.wingspan IS NOT NULL AND c.wingspan > 70
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    wingspan_items = []
    seen = set()
    for pid, name, ws, pos, season in rows:
        if name not in seen:
            seen.add(name)
            wingspan_items.append({
                "name": name,
                "subtext": f"{pos or 'NBA'} • Draft Combine {season}",
                "value": round(float(ws), 1),
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(wingspan_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_wingspan.json"), "w") as f:
        json.dump({
            "id": "nba_wingspan",
            "title": "Combine Wingspan",
            "group": "physical",
            "group_label": "Physical Attributes",
            "prompt": "Who has the LONGER Wingspan (Inches)?",
            "unit": "in",
            "value_format": "{value}\" Wingspan",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#9370DB",
            "items": wingspan_items
        }, f, indent=2)
    print(f"Created nba_wingspan.json with {len(wingspan_items)} items")

    # 4. Max Vertical Leap (inches) (NO vertical leap spoiler in subtext!)
    cur.execute('''
    SELECT c.player_id, c.player_name, c.max_vertical_leap, c.position, c.season
    FROM draft_combine_stats c
    WHERE c.max_vertical_leap IS NOT NULL AND c.max_vertical_leap > 28
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    vertical_items = []
    seen = set()
    for pid, name, vert, pos, season in rows:
        if name not in seen:
            seen.add(name)
            vertical_items.append({
                "name": name,
                "subtext": f"{pos or 'NBA'} • Draft Combine {season}",
                "value": round(float(vert), 1),
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(vertical_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_vertical_leap.json"), "w") as f:
        json.dump({
            "id": "nba_vertical_leap",
            "title": "Combine Max Vertical Leap",
            "group": "physical",
            "group_label": "Physical Attributes",
            "prompt": "Who recorded the HIGHER Max Vertical Leap?",
            "unit": "in",
            "value_format": "{value}\" Vertical",
            "icon": "res://assets/icons/flame.png",
            "theme_color": "#FFD700",
            "items": vertical_items
        }, f, indent=2)
    print(f"Created nba_vertical_leap.json with {len(vertical_items)} items")

    # 5. Combine Bench Press Reps (NO reps spoiler in subtext!)
    cur.execute('''
    SELECT c.player_id, c.player_name, c.bench_press, c.position, c.season
    FROM draft_combine_stats c
    WHERE c.bench_press IS NOT NULL AND c.bench_press > 0
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    bench_items = []
    seen = set()
    for pid, name, bp, pos, season in rows:
        if name not in seen:
            seen.add(name)
            bench_items.append({
                "name": name,
                "subtext": f"{pos or 'NBA'} • Draft Combine {season}",
                "value": int(bp),
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(bench_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_bench_press.json"), "w") as f:
        json.dump({
            "id": "nba_bench_press",
            "title": "Combine Bench Press (185 lbs)",
            "group": "physical",
            "group_label": "Physical Attributes",
            "prompt": "Who benched MORE Reps (185 lbs) at the Combine?",
            "unit": "reps",
            "value_format": "{value} Reps",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#32CD32",
            "items": bench_items
        }, f, indent=2)
    print(f"Created nba_bench_press.json with {len(bench_items)} items")

    # 6. Career Longevity / Seasons Played (NO years or season count in subtext!)
    cur.execute('''
    SELECT person_id, display_first_last, season_exp, team_name, position
    FROM common_player_info
    WHERE season_exp IS NOT NULL AND season_exp > 0 AND (greatest_75_flag = 'Y' OR season_exp >= 10 OR rosterstatus = 'Active')
    GROUP BY display_first_last
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    seasons_items = []
    seen = set()
    for pid, name, exp, team_name, pos in rows:
        if name not in seen:
            seen.add(name)
            seasons_items.append({
                "name": name,
                "subtext": f"{pos or 'Player'} • {team_name or 'NBA'}",
                "value": int(exp),
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(seasons_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_seasons_played.json"), "w") as f:
        json.dump({
            "id": "nba_seasons_played",
            "title": "Seasons Played (Longevity)",
            "group": "career",
            "group_label": "Career & Draft",
            "prompt": "Who played MORE Seasons in the NBA?",
            "unit": "seasons",
            "value_format": "{value} Seasons",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF8C00",
            "items": seasons_items
        }, f, indent=2)
    print(f"Created nba_seasons_played.json with {len(seasons_items)} items")

    # 7. Overall Draft Pick (NO pick number in subtext!)
    cur.execute('''
    SELECT person_id, display_first_last, draft_number, draft_year, team_name, position
    FROM common_player_info
    WHERE draft_number IS NOT NULL AND draft_number != 'Undrafted' AND CAST(draft_number AS INTEGER) > 0
    AND (greatest_75_flag = 'Y' OR season_exp >= 8 OR rosterstatus = 'Active')
    GROUP BY display_first_last
    ORDER BY RANDOM();
    ''')
    rows = cur.fetchall()
    draft_items = []
    seen = set()
    for pid, name, dnum, dyear, team_name, pos in rows:
        try:
            pick_num = int(dnum)
        except Exception:
            continue
        if name not in seen:
            seen.add(name)
            draft_items.append({
                "name": name,
                "subtext": f"{pos or 'Player'} • Draft Class {dyear or ''}",
                "value": pick_num,
                "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png"
            })
            if len(draft_items) >= 30:
                break

    with open(os.path.join(CAT_DIR, "nba_draft_pick.json"), "w") as f:
        json.dump({
            "id": "nba_draft_pick",
            "title": "Overall Draft Pick Number",
            "group": "career",
            "group_label": "Career & Draft",
            "prompt": "Who had the HIGHER Overall Draft Pick Number (Drafted Later)?",
            "unit": "pick",
            "value_format": "Pick #{value}",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#DA70D6",
            "items": draft_items
        }, f, indent=2)
    print(f"Created nba_draft_pick.json with {len(draft_items)} items")

    # 8. All-Time Regular Season Wins (Franchises - NO wins in subtext!)
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
        wins_items.append({
            "name": full_name,
            "subtext": f"{city} • NBA Franchise",
            "value": int(total_wins),
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg"
        })
        pct_items.append({
            "name": full_name,
            "subtext": f"{city} • NBA Franchise",
            "value": float(win_pct),
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg"
        })

    with open(os.path.join(CAT_DIR, "nba_franchise_wins.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_wins",
            "title": "All-Time Franchise Wins",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "prompt": "Which franchise has MORE All-Time Regular Season Wins?",
            "unit": "wins",
            "value_format": "{value} Wins",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#1E90FF",
            "items": wins_items
        }, f, indent=2)
    print(f"Created nba_franchise_wins.json with {len(wins_items)} items")

    # 9. All-Time Franchise Win Percentage (NO win rate in subtext!)
    with open(os.path.join(CAT_DIR, "nba_franchise_win_pct.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_win_pct",
            "title": "All-Time Franchise Win %",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "prompt": "Which franchise has the HIGHER All-Time Win Percentage?",
            "unit": "%",
            "value_format": "{value}% Win Rate",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#20B2AA",
            "items": pct_items
        }, f, indent=2)
    print(f"Created nba_franchise_win_pct.json with {len(pct_items)} items")

    # 10. Arena Seating Capacity (NO seat count in subtext!)
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
        arena_items.append({
            "name": full_name,
            "subtext": f"{arena or 'Arena'} • {city}",
            "value": int(cap),
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg"
        })

    with open(os.path.join(CAT_DIR, "nba_arena_capacity.json"), "w") as f:
        json.dump({
            "id": "nba_arena_capacity",
            "title": "Arena Seating Capacity",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "prompt": "Which NBA team plays in the LARGER Arena (Seating Capacity)?",
            "unit": "seats",
            "value_format": "{value} Seats",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#FF6347",
            "items": arena_items
        }, f, indent=2)
    print(f"Created nba_arena_capacity.json with {len(arena_items)} items")

    # 11. Year Founded (NO year in subtext!)
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
        age = 2026 - int(yf)
        founded_items.append({
            "name": full_name,
            "subtext": f"{city} • NBA Franchise",
            "value": age,
            "image_url": f"https://cdn.nba.com/logos/nba/{tid}/global/L/logo.svg"
        })

    with open(os.path.join(CAT_DIR, "nba_franchise_founded.json"), "w") as f:
        json.dump({
            "id": "nba_franchise_founded",
            "title": "Franchise Age (Years Established)",
            "group": "franchise",
            "group_label": "Teams & Franchises",
            "prompt": "Which franchise is OLDER (More Years Established)?",
            "unit": "years",
            "value_format": "{value} Years Old",
            "icon": "res://assets/icons/trophy.png",
            "theme_color": "#8A2BE2",
            "items": founded_items
        }, f, indent=2)
    print(f"Created nba_franchise_founded.json with {len(founded_items)} items")

    # 12. NBA PPG (NO PPG in subtext!)
    ppg_path = os.path.join(CAT_DIR, "nba_ppg.json")
    if os.path.exists(ppg_path):
        with open(ppg_path, "r") as f:
            ppg_data = json.load(f)
        for it in ppg_data.get("items", []):
            if "PPG" in it.get("subtext", ""):
                it["subtext"] = it["subtext"].split("•")[0].strip()
        ppg_data["group"] = "career"
        ppg_data["group_label"] = "Career & Draft"
        with open(ppg_path, "w") as f:
            json.dump(ppg_data, f, indent=2)

    print("=== Successfully rebuilt all NBA categories (NO spoilers + live web image URLs)! ===")

if __name__ == "__main__":
    build()
