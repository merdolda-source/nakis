import pyembroidery

def mb4_kesin_cozum():
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 için koordinatları mm'den nakış birimine çeviriyoruz (10x)
    # Merkeze (0,0) konumlandırıyoruz.
    
    def cizgi_dik(x1, y1, x2, y2):
        # Başlangıca JUMP (atlama) yap
        pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        # Çizgi boyunca her 2mm'de bir iğne batır (Böylece makine 'tek vuruş' yapamaz)
        distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        steps = int(distance // 20)  # Her 2mm (20 birim) bir dikiş
        if steps < 1: steps = 1
        
        for i in range(1, steps + 1):
            curr_x = x1 + (x2 - x1) * i / steps
            curr_y = y1 + (y2 - y1) * i / steps
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x), int(curr_y))

    # PİVAZ Tasarımı (120x70mm alanı içinde merkezli)
    # P
    cizgi_dik(-500, 300, -500, -300)
    cizgi_dik(-500, -300, -300, -300)
    cizgi_dik(-300, -300, -300, 0)
    cizgi_dik(-300, 0, -500, 0)
    # I
    cizgi_dik(-200, 300, -200, -300)
    # V
    cizgi_dik(-100, -300, 0, 300)
    cizgi_dik(0, 300, 100, -300)
    # A
    cizgi_dik(200, 300, 350, -300)
    cizgi_dik(350, -300, 500, 300)
    cizgi_dik(275, 0, 425, 0)
    # Z
    cizgi_dik(600, -300, 800, -300)
    cizgi_dik(800, -300, 600, 300)
    cizgi_dik(600, 300, 800, 300)

    pattern = pattern.get_normalized_pattern()
    
    # YML İLE AYNI İSİMLERİ KULLANIYORUZ:
    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")
    print("Dosyalar uretildi.")

if __name__ == "__main__":
    mb4_kesin_cozum()
