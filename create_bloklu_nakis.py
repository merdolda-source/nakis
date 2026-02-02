import pyembroidery

MM = 10

pattern = pyembroidery.EmbPattern()

# ===============================
# BLOK DOLGU FONKSİYONU
# ===============================
def blok_dolgu(x1, y1, x2, y2, step, yatay=True):
    """
    Dikdörtgen alanı tek yönlü doldurur
    """
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


# ===============================
# 1️⃣ ÜST BLOK (MOR ALAN)
# ===============================
blok_dolgu(
    x1=-600, y1=-300,
    x2=600,  y2=-100,
    step=6,           # orta hız
    yatay=True
)

# ===============================
# 2️⃣ ORTA BLOK (TURKUAZ)
# ===============================
blok_dolgu(
    x1=-600, y1=-100,
    x2=600,  y2=100,
    step=6,
    yatay=False       # yön değiştir (makine rahatlar)
)

# ===============================
# 3️⃣ ALT BLOK (SARI)
# ===============================
blok_dolgu(
    x1=-600, y1=100,
    x2=600,  y2=300,
    step=6,
    yatay=True
)

# ===============================
# 4️⃣ MERKEZ DAİRE (GÜNEŞ GİBİ)
# ===============================
import math

def daire(cx, cy, r):
    pattern.add_stitch_absolute(pyembroidery.JUMP, cx + r, cy)
    for a in range(0, 360, 5):
        x = cx + int(r * math.cos(math.radians(a)))
        y = cy + int(r * math.sin(math.radians(a)))
        pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

daire(0, 0, 80)
daire(0, 0, 60)
daire(0, 0, 40)

# ===============================
# 5️⃣ DIŞ ÇERÇEVE (EN SON)
# ===============================
pattern.add_stitch_absolute(pyembroidery.JUMP, -620, -320)
pattern.add_stitch_absolute(pyembroidery.STITCH, 620, -320)
pattern.add_stitch_absolute(pyembroidery.STITCH, 620, 320)
pattern.add_stitch_absolute(pyembroidery.STITCH, -620, 320)
pattern.add_stitch_absolute(pyembroidery.STITCH, -620, -320)

# ===============================
# KAPAT
# ===============================
pattern.add_command(pyembroidery.END)
pattern = pattern.get_normalized_pattern()

# ===============================
# ÇIKTILAR
# ===============================
pyembroidery.write(pattern, "bloklu_nakis.dst")
pyembroidery.write(pattern, "bloklu_nakis.jef")

# 🔥 ÖNİZLEME
pyembroidery.write(pattern, "bloklu_nakis.svg")

print("✅ BLOKLU NAKIŞ + ÖNİZLEME OLUŞTURULDU")
