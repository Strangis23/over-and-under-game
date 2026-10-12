import os
import math
from PIL import Image, ImageDraw

def create_hardwood_texture():
    w, h = 720, 1280
    img = Image.new("RGBA", (w, h), (18, 14, 24, 255))
    draw = ImageDraw.Draw(img)

    # Base dark arena floor with subtle warm maple wood tone
    # Parquet plank height: ~36px
    plank_h = 36
    num_planks = (h // plank_h) + 2

    for i in range(num_planks):
        y = i * plank_h
        # Alternating subtle warmth
        is_alt = (i % 2 == 0)
        base_r = 26 if is_alt else 21
        base_g = 19 if is_alt else 15
        base_b = 28 if is_alt else 23
        
        # Subtle horizontal plank
        draw.rectangle([(0, y), (w, y + plank_h - 1)], fill=(base_r, base_g, base_b, 255))
        # Plank seam line
        draw.line([(0, y + plank_h - 1), (w, y + plank_h - 1)], fill=(12, 9, 16, 180), width=1)

        # Staggered vertical seams every 180px
        stagger = 90 if is_alt else 0
        for x in range(stagger, w + 180, 180):
            draw.line([(x, y), (x, y + plank_h - 1)], fill=(12, 9, 16, 140), width=1)

    # Subtle court center circle & key line markings (stadium glow)
    cx, cy = w // 2, h // 2
    # Outer center court circle
    draw.ellipse([(cx - 240, cy - 240), (cx + 240, cy + 240)], outline=(240, 130, 40, 28), width=3)
    # Inner center circle
    draw.ellipse([(cx - 90, cy - 90), (cx + 90, cy + 90)], outline=(240, 130, 40, 38), width=2)
    # Center court line
    draw.line([(0, cy), (w, cy)], fill=(240, 130, 40, 24), width=2)

    # Top & bottom free throw line arcs
    draw.arc([(cx - 160, 40), (cx + 160, 360)], 0, 180, fill=(240, 130, 40, 20), width=2)
    draw.arc([(cx - 160, h - 360), (cx + 160, h - 40)], 180, 360, fill=(240, 130, 40, 20), width=2)

    # Radial vignette / stadium arena shadow around edges
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    max_dist = math.hypot(w // 2, h // 2)
    
    # Simple edge darkening
    for step in range(30):
        t = step / 30.0
        alpha = int(140 * t)
        inset_x = int((1.0 - t) * 60)
        inset_y = int((1.0 - t) * 100)
        # dark border
        ov_draw.rectangle([(0, 0), (w, inset_y)], fill=(8, 6, 12, int(alpha * 0.7)))
        ov_draw.rectangle([(0, h - inset_y), (w, h)], fill=(8, 6, 12, int(alpha * 0.7)))

    img = Image.alpha_composite(img, overlay)
    out_path = os.path.abspath("assets/images/court_floor.png")
    img.save(out_path)
    print("Saved court_floor.png to " + out_path)

if __name__ == "__main__":
    create_hardwood_texture()
