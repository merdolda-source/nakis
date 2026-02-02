import pyembroidery

def mb4_final_fix():
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 için koordinatları mm'den nakış birimine çeviriyoruz (10x)
    # Merkeze (0,0) konumlandırıyoruz.
    
    def cizgi_olustur(x1, y1, x2, y2):
        # Başlangıca JUMP (atlama) yap
        pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        # Çizgi boyunca her 2mm'de bir iğne batır (Böylece makine 'tek vuruş' yapamaz)
        steps = max(abs(x2 - x1), abs(y2 - y1)) // 20  # Her 2mm (20 birim)
        if steps < 1: steps = 1
        
        for i in range(1, int(steps) + 1):
            curr_x = x1 + (x2 - x1) * i / steps
            curr_y = y1 + (y2 - y1) * i / steps
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x), int(curr_y))

    # PİVAZ Tasarımı (120x70mm alanı içinde)
    # P
    cizgi_olustur(-500, -300, -500, 300)
    cizgi_olustur(-500, -300, -300, -300)
    cizgi_olustur(-300, -300, -300, 0)
    cizgi_olustur(-300, 0, -500, 0)
    
    # I
    cizgi_olustur(-150, -300, -150, 300)
    
    # V
    cizgi_olustur(-50, -300, 100, 300)
    cizgi_olustur(100, 300, 250, -300)
    
    # A
    cizgi_olustur(350, 300, 500, -300)
    cizgi_olustur(500, -300, 650, 300)
    cizgi_olustur(425, 0, 575, 0)
    
    # Z
    cizgi_olustur(750, -300, 950, -300)
    cizgi_olustur(950, -300, 750, 300)
    cizgi_olustur(750, 300, 950, 300)

    # ÖNEMLİ: Janome MB-4'ün ekranında görünmesi için dikişleri normalize et
    pattern = pattern.get_normalized_pattern()
    
    # Dosyaları yaz
    # JEF formatı Janome için daha fazla görsel veri taşır.
    pyembroidery.write(pattern, "pivaz_mb4_v3.dst")
    pyembroidery.write(pattern, "pivaz_mb4_v3.jef")
    print("İşlem tamam! Dikiş sayısı artırıldı.")

if __name__ == "__main__":
    mb4_final_fix()
