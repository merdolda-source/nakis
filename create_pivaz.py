import pyembroidery

MM = 10  # 1mm = 10 unit
pattern = pyembroidery.EmbPattern()

def cizgi(x1, y1, x2, y2, step=5):
    pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
    for i in range(step + 1):
        x = x1 + (x2 - x1) * i / step
        y = y1 + (y2 - y1) * i / step
        pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))

def dikdortgen_dolgu(x1, y1, x2, y2, aralik=4):
    yon = 1
    for y in range(y1, y2, aralik):
        if yon == 1:
            pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y)
        else:
            pattern.add_stitch_absolute(pyembroidery.JUMP, x2, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, x1, y)
        yon *= -1

# === P HARFİ ===
dikdortgen_dolgu(-520, -300, -480, 300)
dikdortgen_dolgu(-500, -300, -300, -250)
dikdortgen_dolgu(-300, -250, -260, 0)
dikdortgen_dolgu(-500, -20, -300, 20)

cizgi(-520, -300, -520, 300)
cizgi(-520, -300, -300, -300)
cizgi(-300, -300, -300, 0)
cizgi(-300, 0, -520, 0)

# === I HARFİ ===
dikdortgen_dolgu(-220, -300, -180, 300)
cizgi(-220, -300, -220, 300)

# === V HARFİ ===
cizgi(-100, -300, 0, 300)
cizgi(0, 300, 100, -300)

# === A HARFİ ===
cizgi(200, -300, 300, 300)
cizgi(300, 300, 400, -300)
cizgi(250, 0, 350, 0)

# === Z HARFİ ===
cizgi(600, -300, 800, -300)
cizgi(800, -300, 600, 300)
cizgi(600, 300, 800, 300)

pattern.add_command(pyembroidery.END)
pattern = pattern.get_normalized_pattern()

pyembroidery.write(pattern, "pivaz_cikti.dst")
pyembroidery.write(pattern, "pivaz_cikti.jef")

print("✅ YAZI OLARAK NAKIŞ ÜRETİLDİ")
