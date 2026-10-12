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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

FILES = [
    ("star_wars_7", "File:Star Wars The Force Awakens Theatrical Poster.jpg"),
    ("spiderman_no_way_home", "File:Spider-Man No Way Home poster.jpg"),
    ("the_lion_king_2019", "File:Disney The Lion King 2019.jpg"),
    ("top_gun_maverick", "File:Top Gun Maverick Poster.jpg"),
    ("frozen_2", "File:Frozen II (2019 animated film).jpg"),
    ("mario_bros", "File:The Super Mario Bros. Movie poster.jpg"),
    ("oppenheimer", "File:Oppenheimer (film).jpg")
]

def process_card(img_bytes, dest_path, target_size=(480, 600)):
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    target_aspect = target_size[0] / target_size[1]
    curr_aspect = im.width / im.height

    if curr_aspect > target_aspect:
        new_width = int(im.height * target_aspect)
        offset = (im.width - new_width) // 2
        im = im.crop((offset, 0, offset + new_width, im.height))
    else:
        new_height = int(im.width / target_aspect)
        offset = max(0, int((im.height - new_height) * 0.2))
        if offset + new_height > im.height:
            offset = im.height - new_height
        im = im.crop((0, offset, im.width, offset + new_height))

    im = im.resize(target_size, Image.Resampling.LANCZOS)

    # Subtle bottom gradient for label contrast
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
    print(f"Successfully processed: {dest_path}")

def run():
    for key, file_title in FILES:
        dest_path = f"assets/images/movies/{key}.png"
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(file_title)}&prop=imageinfo&iiprop=url&format=json"
        req = urllib.request.Request(api_url, headers=API_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
                pages = data.get('query', {}).get('pages', {})
                img_url = None
                for p in pages.values():
                    infos = p.get('imageinfo', [])
                    if infos and 'url' in infos[0]:
                        img_url = infos[0]['url']
                        break

                if img_url:
                    time.sleep(0.3)
                    mreq = urllib.request.Request(img_url, headers=MEDIA_HEADERS)
                    with urllib.request.urlopen(mreq, timeout=15) as mresp:
                        process_card(mresp.read(), dest_path)
                else:
                    print(f"Could not get URL for {file_title}")
        except Exception as e:
            print(f"Error fetching {file_title}: {e}")
        time.sleep(0.4)

if __name__ == "__main__":
    run()
