import pyembroidery
import math
from PIL import Image, ImageDraw, ImageFilter

# =====================
# AYARLAR
# =====================
PREVIEW_W = 1200
PREVIEW_H = 800

SEYREK = 10   # büyük alan (hızlı)
SIKI   = 5    # detay
KONTUR = 3

IMG_PATH = "logo.png"

pattern = pyembroidery.EmbPattern()

# =====================
# RESMİ HAZIRLA
# =====================
def load_logo(path):
    img = Image.open(path).convert("L")
    img = img.filter(ImageFilter.MedianFilter(3))
    img = img.point(lambda x: 0 if x < 150 else 255, "1")
    return img

# =====================
# BLOK DOLGU
# =====================
def blok_dolgu(img, step, yatay=True):
    px = img.load()
    w, h = img.size
    yon = 1

    if yatay:
        for y in range(0, h, step):
            drawing = False
            for x in range(0, w):
                if px[x, y] == 0:
                    if not drawing:
                        pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                        drawing = True
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
                else:
                    drawing = False
            yon *= -1
    else:
        for x in range(0, w, step):
            drawing = False
            for y in range(0, h):
                if px[x, y] == 0:
                    if not drawing:
                        pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                        drawing = True
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
                else:
                    drawing = False
            yon *= -1

# =====================
# KONTUR
# =====================
def kontur(img):
    px = img.load()
    w, h = img.size

    for y in range(1, h-1):
        for x in range(1, w-1):
            if px[x, y] == 0:
                if (
                    px[x-1,y] == 255 or px[x+1,y] == 255 or
                    px[x,y-1] == 255 or px[x,y+1] == 255
                ):
                    pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

# =====================
# ANA AKIŞ
# =====================
logo = load_logo(IMG_PATH)

# 1️⃣ Büyük alan – seyrek
blok_dolgu(logo, SEYREK, yatay=True)

# 2️⃣ Aynı alan – sık
blok_dolgu(logo, SIKI, yatay=False)

# 3️⃣ Kontur – en son
kontur(logo)

pattern.add_command(pyembroidery.END)
pattern = pattern.get_normalized_pattern()

# =====================
# NAKIŞ DOSYALARI
# =====================
pyembroidery.write(pattern, "logo_nakis.dst")
pyembroidery.write(pattern, "logo_nakis.jef")

# =====================
# JPG ÖNİZLEME
# =====================
img = Image.new("RGB", (PREVIEW_W, PREVIEW_H), "white")
draw = ImageDraw.Draw(img)

scale = 0.5
ox = PREVIEW_W // 2
oy = PREVIEW_H // 2

last = None
for s in pattern.stitches:
    x = int(s[0] * scale) + ox
    y = int(s[1] * scale) + oy
    if last:
        draw.line([last, (x, y)], fill="black", width=1)
    last = (x, y)

img.save("logo_onizleme.jpg", quality=95)

print("✅ logo.png repodan alındı, nakış + JPG önizleme üretildi")
