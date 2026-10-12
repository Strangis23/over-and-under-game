import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    # Try system fonts or default
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_card_image(filename, title, subtitle, bg_color1, bg_color2, accent_color, symbol_text=""):
    w, h = 480, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background with gradient
    for y in range(h):
        t = y / float(h)
        r = int(bg_color1[0] * (1 - t) + bg_color2[0] * t)
        g = int(bg_color1[1] * (1 - t) + bg_color2[1] * t)
        b = int(bg_color1[2] * (1 - t) + bg_color2[2] * t)
        draw.line([(24, y), (w - 24, y)], fill=(r, g, b, 255))

    # Corner caps
    draw.rounded_rectangle([(0, 0), (w, h)], radius=32, outline=accent_color, width=4)

    # Decorative geometric pattern / rings in center
    cx, cy = w // 2, 230
    for r in range(140, 40, -25):
        alpha = int(40 * (r / 140))
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(accent_color[0], accent_color[1], accent_color[2], alpha), width=2)

    # Center emblem / badge
    badge_r = 75
    draw.ellipse([(cx - badge_r, cy - badge_r), (cx + badge_r, cy + badge_r)], fill=(20, 24, 38, 220), outline=accent_color, width=3)

    # Symbol text in badge
    sym_font = get_font(46)
    if symbol_text:
        sym_bbox = sym_font.getbbox(symbol_text)
        sym_w = sym_bbox[2] - sym_bbox[0]
        sym_h = sym_bbox[3] - sym_bbox[1]
        draw.text((cx - sym_w // 2, cy - sym_h // 2 - 4), symbol_text, font=sym_font, fill=accent_color)

    # Name and Subtitle banner at bottom
    banner_y = 390
    draw.rounded_rectangle([(24, banner_y), (w - 24, h - 28)], radius=18, fill=(15, 18, 30, 235), outline=(255, 255, 255, 30), width=1)

    # Accent stripe
    draw.rounded_rectangle([(36, banner_y + 12), (42, h - 40)], radius=3, fill=accent_color)

    font_title = get_font(28)
    font_sub = get_font(18)

    # Split title if too long
    words = title.split()
    line1 = title
    line2 = ""
    if len(title) > 18 and len(words) > 1:
        half = len(words) // 2
        line1 = " ".join(words[:half])
        line2 = " ".join(words[half:])

    draw.text((56, banner_y + 20), line1, font=font_title, fill=(255, 255, 255, 255))
    if line2:
        draw.text((56, banner_y + 55), line2, font=font_title, fill=(255, 255, 255, 255))
        draw.text((56, banner_y + 98), subtitle, font=font_sub, fill=(180, 195, 220, 240))
    else:
        draw.text((56, banner_y + 65), subtitle, font=font_sub, fill=(180, 195, 220, 240))

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)

def generate_all():
    # 1. NBA
    nba_players = [
        ("michael_jordan", "Michael Jordan", "#23 • SG • Bulls", (180, 20, 30), (40, 10, 15), (255, 215, 0), "MJ"),
        ("wilt_chamberlain", "Wilt Chamberlain", "#13 • C • Warriors", (250, 160, 20), (50, 30, 5), (255, 235, 120), "100"),
        ("luka_doncic", "Luka Dončić", "#77 • PG • Mavericks", (10, 70, 160), (5, 20, 60), (0, 210, 255), "LD77"),
        ("lebron_james", "LeBron James", "#23 • SF • Lakers", (85, 37, 130), (25, 10, 45), (253, 185, 39), "LBJ"),
        ("kevin_durant", "Kevin Durant", "#35 • SF • Suns", (227, 82, 5), (60, 20, 5), (255, 175, 40), "KD"),
        ("allen_iverson", "Allen Iverson", "#3 • PG • 76ers", (0, 43, 92), (10, 20, 40), (237, 23, 76), "AI3"),
        ("kobe_bryant", "Kobe Bryant", "#24 • SG • Lakers", (85, 37, 130), (20, 5, 35), (253, 185, 39), "KB24"),
        ("stephen_curry", "Stephen Curry", "#30 • PG • Warriors", (29, 66, 138), (10, 25, 60), (255, 199, 44), "SC30"),
        ("james_harden", "James Harden", "#1 • SG • Clippers", (200, 16, 46), (40, 5, 15), (0, 200, 240), "JH1"),
        ("shaquille_oneal", "Shaquille O'Neal", "#34 • C • Lakers/Magic", (0, 119, 139), (5, 35, 45), (255, 200, 50), "SHAQ"),
        ("giannis_antetokounmpo", "Giannis Antetokounmpo", "#34 • PF • Bucks", (0, 71, 27), (5, 35, 15), (238, 222, 174), "GA34"),
        ("joel_embiid", "Joel Embiid", "#21 • C • 76ers", (0, 43, 92), (10, 20, 40), (237, 23, 76), "JE21"),
        ("larry_bird", "Larry Bird", "#33 • SF • Celtics", (0, 122, 51), (5, 40, 15), (255, 220, 80), "LB33"),
        ("kareem_abdul_jabbar", "Kareem Abdul-Jabbar", "#33 • C • Lakers/Bucks", (85, 37, 130), (20, 5, 35), (253, 185, 39), "CAP"),
        ("damian_lillard", "Damian Lillard", "#0 • PG • Bucks/Blazers", (224, 58, 62), (40, 10, 15), (255, 255, 255), "DAME")
    ]
    for key, name, sub, c1, c2, acc, sym in nba_players:
        create_card_image(f"assets/images/nba/{key}.png", name, sub, c1, c2, acc, sym)

    # 2. Countries
    countries = [
        ("india", "India", "Asia • 3.28M km²", (255, 153, 51), (19, 136, 8), (255, 255, 255), "IND"),
        ("china", "China", "Asia • 9.60M km²", (222, 41, 16), (100, 10, 5), (255, 222, 0), "CHN"),
        ("usa", "United States", "North America • 9.83M km²", (60, 59, 110), (178, 34, 52), (255, 255, 255), "USA"),
        ("indonesia", "Indonesia", "Southeast Asia • 1.90M km²", (200, 20, 20), (60, 10, 10), (255, 255, 255), "IDN"),
        ("pakistan", "Pakistan", "South Asia • 881k km²", (17, 87, 64), (5, 35, 25), (255, 255, 255), "PAK"),
        ("nigeria", "Nigeria", "West Africa • 923k km²", (0, 135, 83), (5, 45, 25), (255, 255, 255), "NGA"),
        ("brazil", "Brazil", "South America • 8.51M km²", (0, 156, 59), (10, 60, 25), (255, 223, 0), "BRA"),
        ("japan", "Japan", "East Asia • 377k km²", (188, 0, 45), (50, 10, 20), (255, 255, 255), "JPN"),
        ("mexico", "Mexico", "North America • 1.96M km²", (0, 104, 71), (206, 17, 38), (255, 255, 255), "MEX"),
        ("germany", "Germany", "Central Europe • 357k km²", (30, 30, 30), (221, 0, 0), (255, 206, 0), "DEU"),
        ("uk", "United Kingdom", "Western Europe • 243k km²", (1, 33, 105), (200, 16, 46), (255, 255, 255), "GBR"),
        ("france", "France", "Western Europe • 551k km²", (0, 85, 164), (239, 65, 53), (255, 255, 255), "FRA"),
        ("australia", "Australia", "Oceania • 7.69M km²", (0, 30, 90), (10, 15, 40), (255, 200, 0), "AUS"),
        ("canada", "Canada", "North America • 9.98M km²", (216, 6, 33), (60, 5, 10), (255, 255, 255), "CAN"),
        ("italy", "Italy", "Southern Europe • 301k km²", (0, 140, 69), (205, 33, 42), (255, 255, 255), "ITA"),
        ("south_korea", "South Korea", "East Asia • 100k km²", (20, 60, 140), (180, 20, 30), (255, 255, 255), "KOR")
    ]
    for key, name, sub, c1, c2, acc, sym in countries:
        create_card_image(f"assets/images/countries/{key}.png", name, sub, c1, c2, acc, sym)

    # 3. Movies
    movies = [
        ("avatar", "Avatar", "Dir. James Cameron • 2009", (10, 110, 160), (5, 30, 50), (60, 240, 255), "2009"),
        ("avengers_endgame", "Avengers: Endgame", "Marvel Studios • 2019", (90, 20, 110), (30, 5, 40), (240, 180, 40), "2019"),
        ("avatar_2", "Avatar 2: Way of Water", "Dir. James Cameron • 2022", (0, 130, 180), (0, 40, 70), (120, 255, 220), "2022"),
        ("titanic", "Titanic", "Dir. James Cameron • 1997", (20, 50, 100), (10, 20, 40), (210, 180, 120), "1997"),
        ("star_wars_7", "Star Wars: Force Awakens", "Lucasfilm • 2015", (220, 170, 20), (30, 30, 35), (255, 230, 100), "2015"),
        ("avengers_infinity_war", "Avengers: Infinity War", "Marvel Studios • 2018", (130, 30, 80), (40, 10, 30), (255, 140, 0), "2018"),
        ("spiderman_no_way_home", "Spider-Man: No Way Home", "Marvel / Sony • 2021", (180, 20, 30), (20, 40, 120), (255, 215, 0), "2021"),
        ("inside_out_2", "Inside Out 2", "Pixar Animation • 2024", (240, 140, 20), (100, 20, 120), (0, 230, 255), "2024"),
        ("jurassic_world", "Jurassic World", "Universal Pictures • 2015", (60, 100, 60), (20, 30, 20), (180, 210, 100), "2015"),
        ("the_lion_king_2019", "The Lion King", "Walt Disney Pictures • 2019", (190, 100, 20), (60, 30, 10), (255, 210, 80), "2019"),
        ("barbie", "Barbie", "Warner Bros. • 2023", (230, 60, 150), (90, 15, 55), (255, 200, 230), "2023"),
        ("frozen_2", "Frozen II", "Walt Disney Animation • 2019", (60, 120, 200), (20, 40, 80), (180, 240, 255), "2019"),
        ("mario_bros", "Super Mario Bros. Movie", "Illumination / Nintendo • 2023", (220, 30, 30), (30, 70, 180), (255, 220, 0), "2023"),
        ("top_gun_maverick", "Top Gun: Maverick", "Paramount Pictures • 2022", (180, 120, 40), (25, 40, 60), (255, 200, 100), "2022"),
        ("oppenheimer", "Oppenheimer", "Dir. Christopher Nolan • 2023", (220, 80, 20), (30, 20, 20), (255, 140, 30), "2023")
    ]
    for key, name, sub, c1, c2, acc, sym in movies:
        create_card_image(f"assets/images/movies/{key}.png", name, sub, c1, c2, acc, sym)

    # 4. Animals
    animals = [
        ("peregrine_falcon", "Peregrine Falcon", "Bird of Prey • Aerial Dive", (40, 70, 110), (15, 25, 45), (100, 210, 255), "FALC"),
        ("golden_eagle", "Golden Eagle", "Accipitridae • Hunting Dive", (110, 75, 35), (35, 25, 15), (240, 190, 80), "EAGL"),
        ("black_marlin", "Black Marlin", "Ocean Fish • Billfish", (15, 50, 100), (5, 20, 45), (0, 220, 255), "MARL"),
        ("cheetah", "Cheetah", "Acinonyx jubatus • Land Sprint", (200, 140, 30), (60, 40, 10), (255, 215, 90), "CHTH"),
        ("sailfish", "Sailfish", "Istiophoridae • Ocean Predator", (20, 70, 120), (10, 30, 50), (70, 230, 255), "SAIL"),
        ("pronghorn", "Pronghorn Antelope", "North America • Endurance", (160, 110, 60), (50, 35, 20), (240, 200, 120), "PRNG"),
        ("lion", "African Lion", "Panthera leo • Apex Predator", (180, 100, 25), (55, 30, 10), (255, 190, 70), "LION"),
        ("greyhound", "Greyhound", "Canis lupus • Racing Breed", (100, 90, 85), (30, 28, 25), (200, 190, 180), "HND"),
        ("ostrich", "Common Ostrich", "Struthio camelus • Flightless", (120, 80, 60), (40, 25, 20), (230, 170, 130), "OSTR"),
        ("kangaroo", "Red Kangaroo", "Macropodidae • Hopping Leap", (170, 90, 40), (50, 25, 15), (255, 160, 90), "ROO"),
        ("grizzly_bear", "Grizzly Bear", "Ursus arctos • Heavy Sprint", (80, 50, 30), (25, 15, 10), (210, 160, 110), "BEAR"),
        ("elephant", "African Elephant", "Loxodonta • Giant Charge", (85, 90, 100), (25, 28, 32), (180, 190, 205), "ELEP"),
        ("sloth", "Three-Toed Sloth", "Bradypodidae • Canopy Crawler", (70, 95, 60), (20, 35, 20), (150, 210, 140), "SLOW")
    ]
    for key, name, sub, c1, c2, acc, sym in animals:
        create_card_image(f"assets/images/animals/{key}.png", name, sub, c1, c2, acc, sym)

    print("All item cards successfully generated!")

if __name__ == "__main__":
    generate_all()
