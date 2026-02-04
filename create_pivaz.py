import pyembroidery

def mb4_kesin_cozum():
    pattern = pyembroidery.EmbPattern()
    
    # Nakış parametreleri
    STITCH_LENGTH = 25  # 2.5mm dikiş uzunluğu
    FILL_ANGLE = 45     # Dolgu açısı
    UNDERLAY = True     # Alt kat kullan (daha sağlam)
    
    def satin_cizgi(x1, y1, x2, y2, genislik=50):
        """Satin stitch (ipek dikiş) - kalın çizgiler için"""
        import math
        
        # Çizgi açısını hesapla
        angle = math.atan2(y2 - y1, x2 - x1)
        perpendicular = angle + math.pi / 2
        
        # Genişlik için offset hesapla
        dx = math.cos(perpendicular) * genislik / 2
        dy = math.sin(perpendicular) * genislik / 2
        
        # Başlangıca JUMP
        pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1 + dx), int(y1 + dy))
        
        # Zigzag şeklinde satin dikiş
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        steps = int(distance / STITCH_LENGTH)
        if steps < 2: steps = 2
        
        for i in range(steps + 1):
            t = i / steps
            curr_x = x1 + (x2 - x1) * t
            curr_y = y1 + (y2 - y1) * t
            
            # Zigzag için alternatif kenarlar
            if i % 2 == 0:
                pattern.add_stitch_absolute(pyembroidery.STITCH, 
                    int(curr_x + dx), int(curr_y + dy))
            else:
                pattern.add_stitch_absolute(pyembroidery.STITCH, 
                    int(curr_x - dx), int(curr_y - dy))
    
    def dolu_harf(noktalar, genislik=50):
        """Kapalı şekilleri dolgulu nakış yap"""
        if len(noktalar) < 3:
            return
        
        # Önce kontür çiz (underlay)
        if UNDERLAY:
            pattern.add_stitch_absolute(pyembroidery.JUMP, noktalar[0][0], noktalar[0][1])
            for x, y in noktalar[1:]:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            pattern.add_stitch_absolute(pyembroidery.STITCH, noktalar[0][0], noktalar[0][1])
        
        # Y koordinatlarını bul
        min_y = min(p[1] for p in noktalar)
        max_y = max(p[1] for p in noktalar)
        
        # Yatay çizgilerle doldur
        y = min_y
        yon = 1  # Zigzag için yön
        
        while y <= max_y:
            kesisimler = []
            
            # Bu y seviyesinde çokgenle kesişimleri bul
            for i in range(len(noktalar)):
                x1, y1 = noktalar[i]
                x2, y2 = noktalar[(i + 1) % len(noktalar)]
                
                if (y1 <= y < y2) or (y2 <= y < y1):
                    # Kesişim noktasını hesapla
                    if y2 != y1:
                        x = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
                        kesisimler.append(int(x))
            
            # Kesişimleri sırala
            kesisimler.sort()
            
            # Çiftler halinde çizgiler çiz
            for i in range(0, len(kesisimler) - 1, 2):
                if yon == 1:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, kesisimler[i], int(y))
                    pattern.add_stitch_absolute(pyembroidery.STITCH, kesisimler[i + 1], int(y))
                else:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, kesisimler[i + 1], int(y))
                    pattern.add_stitch_absolute(pyembroidery.STITCH, kesisimler[i], int(y))
                yon *= -1  # Yönü değiştir
            
            y += STITCH_LENGTH

    # Modern PIVAZ Tasarımı - Dolgulu Nakış
    print("🧵 PIVAZ nakış deseni oluşturuluyor...")
    
    # P harfi (dolgulu)
    p_noktalar = [
        (-550, -350), (-550, 350), (-250, 350),
        (-250, 50), (-450, 50), (-450, -50),
        (-250, -50), (-250, -350)
    ]
    dolu_harf(p_noktalar, 60)
    
    # I harfi (kalın çizgi)
    satin_cizgi(-150, -350, -150, 350, 80)
    
    # V harfi (dolgulu)
    v_noktalar = [
        (-50, -350), (-20, -350), (50, 350),
        (50, 350), (80, 350), (150, -350)
    ]
    for i in range(len(v_noktalar) - 1):
        satin_cizgi(v_noktalar[i][0], v_noktalar[i][1], 
                   v_noktalar[i+1][0], v_noktalar[i+1][1], 70)
    
    # A harfi (dolgulu üçgen + yatay çizgi)
    a_noktalar = [
        (250, 350), (350, -350), (450, 350)
    ]
    for i in range(len(a_noktalar) - 1):
        satin_cizgi(a_noktalar[i][0], a_noktalar[i][1], 
                   a_noktalar[i+1][0], a_noktalar[i+1][1], 70)
    # A'nın ortası
    satin_cizgi(300, 50, 400, 50, 60)
    
    # Z harfi (dolgulu)
    satin_cizgi(550, -350, 750, -350, 80)  # Üst çizgi
    satin_cizgi(750, -350, 550, 350, 70)   # Çapraz
    satin_cizgi(550, 350, 750, 350, 80)    # Alt çizgi

    # Normalizasyon ve kaydetme
    pattern = pattern.get_normalized_pattern()
    
    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")
    
    print("✅ Dosyalar başarıyla oluşturuldu!")
    print(f"📊 Toplam dikiş sayısı: {len(pattern.stitches)}")
    print("📁 Çıktılar: pivaz_cikti.dst, pivaz_cikti.jef")

if __name__ == "__main__":
    mb4_kesin_cozum()
