import pyembroidery
import math
from PIL import Image, ImageDraw

# =====================
# GENEL AYARLAR
# =====================
MM = 10
WIDTH = 1200
HEIGHT = 800

SEYREK = 10   # büyük alan (hızlı)
SIKI   = 5    # detay
KONTUR = 3

# =====================
# PATTERN
# =====================
pattern = pyembroidery.EmbPattern()

# =====================
# BLOK DOLGU
# =====================
def blok_dolgu(x1, y1, x2, y2, step, yatay=True):
    yon = 1
    if yatay:
        for y in range(y1, y2, step):
            if yon == 1:
                pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y)
                pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y)
            else:
                pattern.add_stitch_absolute(pyembroidery.JUMP, x2, y)
                pattern.add_stitch_absolute(pyembroidery.STITCH, x1, y)
            yon *= -1
    else:
        for x in range(x1, x2, step):
            if yon == 1:
                pattern.add_stitch_absolute(pyembroidery.JUMP, x, y1)
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y2)
            else:
                pattern.add_stitch_absolute(pyembroidery.JUMP, x, y2)
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y1)
            yon *= -1

# =====================
# DAİRE (MERKEZ OBJE)
# =====================
def daire(cx, cy, r):
    pattern.add_stitch_absolute(pyembroidery.JUMP, cx + r, cy)
    for a in range(0, 361, 4):
        x = cx + int(r * math.cos(math.radians(a)))
        y = cy + int(r * math.sin(math.radians(a)))
        pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

# =====================
# 1️⃣ ÜST BLOK
# =====================
blok_dolgu(-600, -300, 600, -100, SEYREK, yatay=True)

# =====================
# 2️⃣ ORTA BLOK
# =====================
blok_dolgu(-600, -100, 600, 100, SEYREK, yatay=False)

# =====================
# 3️⃣ ALT BLOK
# =====================
blok_dolgu(-600, 100, 600, 300, SEYREK, yatay=True)

# =====================
# 4️⃣ MERKEZ OBJE
# =====================
daire(0, 0, 80)
daire(0, 0, 60)
daire(0, 0, 40)

# =====================
# 5️⃣ DIŞ KONTUR (EN SON)
# =====================
pattern.add_stitch_absolute(pyembroidery.JUMP, -620, -320)
pattern.add_stitch_absolute(pyembroidery.STITCH, 620, -320)
pattern.add_stitch_absolute(pyembroidery.STITCH, 620, 320)
pattern.add_stitch_absolute(pyembroidery.STITCH, -620, 320)
pattern.add_stitch_absolute(pyembroidery.STITCH, -620, -320)

# =====================
# KAPAT
# =====================
pattern.add_command(pyembroidery.END)
pattern = pattern.get_normalized_pattern()

# =====================
# DOSYA ÇIKTILARI
# =====================
pyembroidery.write(pattern, "bloklu_nakis.dst")
pyembroidery.write(pattern, "bloklu_nakis.jef")

# =====================
# JPG ÖNİZLEME (MAKİNE GİBİ)
# =====================
img = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(img)

scale = 0.4
ox = WIDTH // 2
oy = HEIGHT // 2

last = None
for s in pattern.stitches:
    x = int(s[0] * scale) + ox
    y = int(s[1] * scale) + oy
    if last:
        draw.line([last, (x, y)], fill="black", width=1)
    last = (x, y)

img.save("bloklu_nakis.jpg", quality=95)

print("✅ DST + JEF + JPG önizleme üretildi")
