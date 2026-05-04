import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FRAME_W, FRAME_H = 300, 400

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def make_housebg(path):
    # simple gradient background 800x600
    w, h = 800, 600
    img = Image.new("RGB", (w, h), "#2b2b2b")
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(40 + 80 * t)
        g = int(70 + 40 * t)
        b = int(90 + 60 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    draw.text((20, 20), "HOUSE BACKGROUND (placeholder)", fill=(240,240,240))
    img.save(path, "JPEG", quality=85)

def make_sprite_sheet(filename, frames, out_path, label):
    sheet_w = frames * FRAME_W
    sheet_h = FRAME_H
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0,0,0,0))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    for i in range(frames):
        # simple colored frame
        frame = Image.new("RGBA", (FRAME_W, FRAME_H), (40 + i*20 % 200, 80 + i*10 % 160, 120 + i*15 % 120, 255))
        fdraw = ImageDraw.Draw(frame)
        text = f"{label} {i+1}"
        w, h = fdraw.textsize(text, font=font)
        fdraw.text(((FRAME_W-w)//2, (FRAME_H-h)//2), text, font=font, fill=(255,255,255,255))
        sheet.paste(frame, (i*FRAME_W, 0), frame)
    sheet.save(out_path, "PNG")

def main():
    ensure_dir(ASSETS_DIR)
    print("Creating assets in:", ASSETS_DIR)
    try:
        make_housebg(os.path.join(ASSETS_DIR, "housebg.jpg"))
        make_sprite_sheet("Rigby8.png", 8, os.path.join(ASSETS_DIR, "Rigby8.png"), "Rigby")
        make_sprite_sheet("Mordecai6.png", 6, os.path.join(ASSETS_DIR, "Mordecai6.png"), "Mordecai")
        make_sprite_sheet("Benson4.png", 4, os.path.join(ASSETS_DIR, "Benson4.png"), "Benson")
        print("Assets created: housebg.jpg, Rigby8.png, Mordecai6.png, Benson4.png")
    except Exception as e:
        print("Failed to create assets:", e)

if __name__ == "__main__":
    main()
