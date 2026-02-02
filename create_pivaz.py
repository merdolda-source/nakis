import pyembroidery

MM = 10  # 1mm = 10 embroidery unit

def dolu_dik(x1, y1, x2, y2, step_mm=0.45):
    """
    Dikdörtgen alanı satır satır doldurur (Tatami Fill benzeri)
    """
    step = int(step_mm * MM)
    direction = 1

    for y in range(y1, y2, step):
        if direction == 1:
            pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y)
        else:
            pattern.add_stitch_absolute(pyembroidery.JUMP, x2, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, x1, y)
        direction *= -1


def mb4_full_nakis():
    global pattern
    pattern = pyembroidery.EmbPattern()

    # === P HARFİ ===
    dolu_dik(-520, -300, -480, 300)     # Dikey gövde
    dolu_dik(-500, -300, -300, -250)    # Alt
    dolu_dik(-320, -250, -280, 0)       # Sağ dikey
    dolu_dik(-500, -20, -300, 20)       # Orta çizgi

    # === I HARFİ ===
    dolu_dik(-220, -300, -180, 300)

    # === V HARFİ (2 üçgen alan) ===
    dolu_dik(-100, -300, -50, 300)
    dolu_dik(50, -300, 100, 300)

    # === A HARFİ ===
    dolu_dik(200, -300, 240, 300)
    dolu_dik(360, -300, 400, 300)
    dolu_dik(240, -20, 360, 20)

    # === Z HARFİ ===
    dolu_dik(600, -300, 800, -260)
    dolu_dik(760, -260, 800, 300)
    dolu_dik(600, 260, 800, 300)

    pattern.add_command(pyembroidery.END)
    pattern = pattern.get_normalized_pattern()

    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")

    print("✅ FULL NAKIŞ ÜRETİLDİ (MB-4 UYUMLU)")

if __name__ == "__main__":
    mb4_full_nakis()
