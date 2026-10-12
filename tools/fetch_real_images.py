import os
import json
import io
import time
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw

API_HEADERS = {
    'User-Agent': 'OverAndUnderTriviaGame/2.0 (Godot trivia game; contact: dev@overundergame.org)'
}
MEDIA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
}

def safe_api_get(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=API_HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            wait = 1.0 * (attempt + 1)
            print(f"API retry ({attempt+1}) for {url}: {e}, waiting {wait}s...")
            time.sleep(wait)
    return None

def safe_download_image(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=MEDIA_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            wait = 1.0 * (attempt + 1)
            print(f"Media download retry ({attempt+1}) for {url}: {e}, waiting {wait}s...")
            time.sleep(wait)
    return None

def get_page_image_url(wiki_title):
    # 1. Try pageimages property
    api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(wiki_title)}&prop=pageimages&format=json&pithumbsize=900"
    data = safe_api_get(api_url)
    if data:
        pages = data.get('query', {}).get('pages', {})
        for p in pages.values():
            if 'thumbnail' in p:
                return p['thumbnail']['source']

    # 2. Try images list for posters or lead image
    api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(wiki_title)}&prop=images&format=json"
    data = safe_api_get(api_url)
    if data:
        pages = data.get('query', {}).get('pages', {})
        for p in pages.values():
            images = [img['title'] for img in p.get('images', [])]
            # Prioritize poster, teaser, or cover
            candidates = [img for img in images if any(k in img.lower() for k in ['poster', 'teaser', 'cover', 'theatrical'])]
            target_file = candidates[0] if candidates else None
            if target_file:
                time.sleep(0.3)
                file_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(target_file)}&prop=imageinfo&iiprop=url&format=json"
                fdata = safe_api_get(file_url)
                if fdata:
                    fpages = fdata.get('query', {}).get('pages', {})
                    for fp in fpages.values():
                        infos = fp.get('imageinfo', [])
                        if infos and 'url' in infos[0]:
                            return infos[0]['url']
    return None

def process_and_save_card_image(img_bytes, dest_path, target_size=(480, 600)):
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    target_aspect = target_size[0] / target_size[1]
    curr_aspect = im.width / im.height

    if curr_aspect > target_aspect:
        # Crop left/right
        new_width = int(im.height * target_aspect)
        offset = (im.width - new_width) // 2
        im = im.crop((offset, 0, offset + new_width, im.height))
    else:
        # Crop top/bottom
        new_height = int(im.width / target_aspect)
        offset = max(0, int((im.height - new_height) * 0.2))
        if offset + new_height > im.height:
            offset = im.height - new_height
        im = im.crop((0, offset, im.width, offset + new_height))

    im = im.resize(target_size, Image.Resampling.LANCZOS)

    # Gradient for bottom text readability
    gradient = Image.new("RGBA", target_size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(gradient)
    start_y = int(target_size[1] * 0.52)
    for y in range(start_y, target_size[1]):
        ratio = (y - start_y) / float(target_size[1] - start_y)
        alpha = int(225 * (ratio ** 1.35))
        gdraw.line([(0, y), (target_size[0], y)], fill=(8, 11, 18, alpha))

    final_card = Image.alpha_composite(im, gradient)

    mask = Image.new("L", target_size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), target_size], radius=24, fill=255)
    final_card.putalpha(mask)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    final_card.save(dest_path, "PNG")

NBA_ITEMS = [
    ("michael_jordan", "Michael Jordan"),
    ("wilt_chamberlain", "Wilt Chamberlain"),
    ("luka_doncic", "Luka Dončić"),
    ("joel_embiid", "Joel Embiid"),
    ("kevin_durant", "Kevin Durant"),
    ("lebron_james", "LeBron James"),
    ("allen_iverson", "Allen Iverson"),
    ("damian_lillard", "Damian Lillard"),
    ("kobe_bryant", "Kobe Bryant"),
    ("stephen_curry", "Stephen Curry"),
    ("kareem_abdul_jabbar", "Kareem Abdul-Jabbar"),
    ("larry_bird", "Larry Bird"),
    ("james_harden", "James Harden"),
    ("shaquille_oneal", "Shaquille O'Neal"),
    ("giannis_antetokounmpo", "Giannis Antetokounmpo")
]

COUNTRY_ITEMS = [
    ("india", "India"),
    ("china", "China"),
    ("usa", "United States"),
    ("indonesia", "Indonesia"),
    ("pakistan", "Pakistan"),
    ("nigeria", "Nigeria"),
    ("brazil", "Brazil"),
    ("mexico", "Mexico"),
    ("japan", "Japan"),
    ("germany", "Germany"),
    ("uk", "United Kingdom"),
    ("france", "France"),
    ("italy", "Italy"),
    ("south_korea", "South Korea"),
    ("canada", "Canada"),
    ("australia", "Australia")
]

MOVIE_ITEMS = [
    ("avatar", "Avatar (2009 film)"),
    ("avengers_endgame", "Avengers: Endgame"),
    ("avatar_2", "Avatar: The Way of Water"),
    ("titanic", "Titanic (1997 film)"),
    ("star_wars_7", "Star Wars: The Force Awakens"),
    ("avengers_infinity_war", "Avengers: Infinity War"),
    ("spiderman_no_way_home", "Spider-Man: No Way Home"),
    ("inside_out_2", "Inside Out 2"),
    ("jurassic_world", "Jurassic World"),
    ("the_lion_king_2019", "The Lion King (2019 film)"),
    ("top_gun_maverick", "Top Gun: Maverick"),
    ("frozen_2", "Frozen II"),
    ("barbie", "Barbie (film)"),
    ("mario_bros", "The Super Mario Bros. Movie"),
    ("oppenheimer", "Oppenheimer (film)")
]

ANIMAL_ITEMS = [
    ("peregrine_falcon", "Peregrine falcon"),
    ("golden_eagle", "Golden eagle"),
    ("black_marlin", "Black marlin"),
    ("cheetah", "Cheetah"),
    ("sailfish", "Sailfish"),
    ("pronghorn", "Pronghorn"),
    ("lion", "Lion"),
    ("greyhound", "Greyhound"),
    ("ostrich", "Common ostrich"),
    ("kangaroo", "Red kangaroo"),
    ("grizzly_bear", "Grizzly bear"),
    ("elephant", "African elephant"),
    ("sloth", "Brown-throated sloth")
]

def run():
    categories = [
        ("nba", NBA_ITEMS),
        ("countries", COUNTRY_ITEMS),
        ("movies", MOVIE_ITEMS),
        ("animals", ANIMAL_ITEMS)
    ]

    total = sum(len(items) for _, items in categories)
    count = 0

    print(f"=== Downloading {total} Real Reference Images from Wikipedia ===")

    for cat_name, items in categories:
        print(f"\n--- Category: {cat_name} ({len(items)} items) ---")
        for key, wiki_title in items:
            dest_path = f"assets/images/{cat_name}/{key}.png"
            print(f"[{count+1}/{total}] Fetching '{wiki_title}'...")

            img_url = get_page_image_url(wiki_title)
            if not img_url and "(" in wiki_title:
                alt_title = wiki_title.split("(")[0].strip()
                time.sleep(0.3)
                img_url = get_page_image_url(alt_title)

            if img_url:
                time.sleep(0.2)
                img_bytes = safe_download_image(img_url)
                if img_bytes:
                    process_and_save_card_image(img_bytes, dest_path)
                    print(f"  ✓ Saved to {dest_path}")
                    count += 1
                else:
                    print(f"  ✗ Failed to download bytes from {img_url}")
            else:
                print(f"  ✗ No image URL found for {wiki_title}")

            time.sleep(0.4) # Respectful API pacing

    print(f"\n=== Completed: {count}/{total} images downloaded and processed ===")

if __name__ == "__main__":
    run()
