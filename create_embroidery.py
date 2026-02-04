import pyembroidery

def create_satin_stitch(pattern, x1, y1, x2, y2, width=30):
    """
    Basit bir çizgiyi saten dolguya (zigzag) dönüştürür.
    width: Harf kalınlığı (10 birim = 1mm)
    """
    import math
    
    # Çizginin açısını hesapla
    angle = math.atan2(y2 - y1, x2 - x1)
    # Dik açıyı bul (Saten dikiş için sağa sola kayma)
    perp_angle = angle + math.pi / 2
    
    dx = math.cos(perp_angle) * width
    dy = math.sin(perp_angle) * width
    
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    steps = int(distance // 10)  # Her 1mm'de bir iğne vuruşu (Yüksek kalite)
    
    for i in range(steps + 1):
        ratio = i / steps
        curr_x = x1 + (x2 - x1) * ratio
        curr_y = y1 + (y2 - y1) * ratio
        
        # Zigzag hareketleri
        if i % 2 == 0:
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x + dx), int(curr_y + dy))
        else:
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x - dx), int(curr_y - dy))

def mb4_modern_pivaz():
    pattern = pyembroidery.EmbPattern()
    w = 40  # Harf kalınlığı (4mm)

    # P Harfi
    pattern.add_stitch_absolute(pyembroidery.JUMP, -500, 300)
    create_satin_stitch(pattern, -500, 300, -500, -300, w)
    create_satin_stitch(pattern, -500, -300, -300, -300, w)
    create_satin_stitch(pattern, -300, -300, -300, 0, w)
    create_satin_stitch(pattern, -300, 0, -500, 0, w)

    # I Harfi
    pattern.add_stitch_absolute(pyembroidery.JUMP, -200, 300)
    create_satin_stitch(pattern, -200, 300, -200, -300, w)

    # V Harfi
    pattern.add_stitch_absolute(pyembroidery.JUMP, -100, -300)
    create_satin_stitch(pattern, -100, -300, 0, 300, w)
    create_satin_stitch(pattern, 0, 300, 100, -300, w)

    # A Harfi
    pattern.add_stitch_absolute(pyembroidery.JUMP, 200, 300)
    create_satin_stitch(pattern, 200, 300, 350, -300, w)
    create_satin_stitch(pattern, 350, -300, 500, 300, w)
    # Orta çizgi
    pattern.add_stitch_absolute(pyembroidery.JUMP, 275, 0)
    create_satin_stitch(pattern, 275, 0, 425, 0, w)

    # Z Harfi
    pattern.add_stitch_absolute(pyembroidery.JUMP, 600, -300)
    create_satin_stitch(pattern, 600, -300, 800, -300, w)
    create_satin_stitch(pattern, 800, -300, 600, 300, w)
    create_satin_stitch(pattern, 600, 300, 800, 300, w)

    pattern.end()
    
    # MB-4 uyumluluğu için normalize et
    final_pattern = pattern.get_normalized_pattern()
    
    pyembroidery.write(final_pattern, "pivaz_modern.dst")
    pyembroidery.write(final_pattern, "pivaz_modern.jef")
    print("Modern Saten Nakis Dosyalari Uretildi.")

if __name__ == "__main__":
    mb4_modern_pivaz()
