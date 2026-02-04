import pyembroidery

def mb4_kesin_cozum():
    pattern = pyembroidery.EmbPattern()
    
    # Nakış parametreleri
    KONTUR_GENISLIK = 30      # Kontür çizgisi kalınlığı
    DOLGU_MESAFE = 15         # Dolgu çizgileri arası mesafe
    DOLGU_ACI = 0             # Dolgu açısı (0=yatay, 45=çapraz)
    
    def kontur_ciz(noktalar, kapalı=True):
        """Önce dış konturu çiz (outline)"""
        if len(noktalar) < 2:
            return
            
        # İlk noktaya git
        pattern.add_stitch_absolute(pyembroidery.JUMP, noktalar[0][0], noktalar[0][1])
        
        # Tüm noktaları birleştir
        for x, y in noktalar[1:]:
            # Her 2mm'de bir dikiş
            pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        # Kapalı şekillerde başa dön
        if kapalı:
            pattern.add_stitch_absolute(pyembroidery.STITCH, noktalar[0][0], noktalar[0][1])
    
    def dolgu_yap(noktalar, aci=0):
        """Konturun içini dolgulu nakış yap"""
        import math
        
        if len(noktalar) < 3:
            return
        
        # Min/Max koordinatları bul
        min_x = min(p[0] for p in noktalar)
        max_x = max(p[0] for p in noktalar)
        min_y = min(p[1] for p in noktalar)
        max_y = max(p[1] for p in noktalar)
        
        # Yatay çizgilerle doldur
        y = min_y + DOLGU_MESAFE
        yön = 1
        
        while y <= max_y:
            kesişimler = []
            
            # Bu y seviyesinde çokgenle kesişim noktalarını bul
            for i in range(len(noktalar)):
                x1, y1 = noktalar[i]
                x2, y2 = noktalar[(i + 1) % len(noktalar)]
                
                # Kenar bu y seviyesini kesiyorsa
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if y2 != y1:
                        x = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
                        kesişimler.append(int(x))
            
            # Kesişimleri sırala
            kesişimler.sort()
            
            # Çiftler halinde yatay çizgiler çiz
            for i in range(0, len(kesişimler) - 1, 2):
                if yön == 1:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, kesişimler[i], int(y))
                    # Çizgi boyunca dikiş
                    steps = abs(kesişimler[i+1] - kesişimler[i]) // 20
                    if steps < 1: steps = 1
                    for s in range(1, steps + 1):
                        x = kesişimler[i] + (kesişimler[i+1] - kesişimler[i]) * s // steps
                        pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))
                else:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, kesişimler[i+1], int(y))
                    steps = abs(kesişimler[i+1] - kesişimler[i]) // 20
                    if steps < 1: steps = 1
                    for s in range(1, steps + 1):
                        x = kesişimler[i+1] - (kesişimler[i+1] - kesişimler[i]) * s // steps
                        pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))
                
                yön *= -1
            
            y += DOLGU_MESAFE
    
    def harf_yap(noktalar):
        """1) Kontür çiz, 2) İçini doldur"""
        kontur_ciz(noktalar, kapalı=True)
        dolgu_yap(noktalar)

    print("🧵 PIVAZ nakış deseni oluşturuluyor...")
    
    # ===== P Harfi =====
    p_noktalar = [
        (-600, -350),  # Sol alt
        (-600, 350),   # Sol üst
        (-350, 350),   # Sağ üst
        (-350, 50),    # Sağ orta üst
        (-500, 50),    # İç sol orta üst
        (-500, -50),   # İç sol orta alt
        (-350, -50),   # Sağ orta alt
        (-350, -350),  # Sağ alt
    ]
    harf_yap(p_noktalar)
    
    # ===== I Harfi =====
    i_noktalar = [
        (-200, -350),
        (-200, 350),
        (-100, 350),
        (-100, -350),
    ]
    harf_yap(i_noktalar)
    
    # ===== V Harfi =====
    v_noktalar = [
        (-50, -350),   # Sol üst
        (0, 350),      # Orta alt
        (50, -350),    # Sağ üst
        (100, -350),   # Sağ üst dış
        (50, 250),     # Sağ orta
        (0, 250),      # Orta
        (-50, 250),    # Sol orta
        (-100, -350),  # Sol üst dış
    ]
    harf_yap(v_noktalar)
    
    # ===== A Harfi =====
    # Dış üçgen
    a_noktalar = [
        (200, 350),    # Sol alt
        (300, -350),   # Tepe
        (400, 350),    # Sağ alt
        (350, 350),    # Sağ alt iç
        (300, -250),   # Tepe iç
        (250, 350),    # Sol alt iç
    ]
    harf_yap(a_noktalar)
    
    # A'nın yatay çizgisi
    a_cizgi = [
        (250, 100),
        (250, 50),
        (350, 50),
        (350, 100),
    ]
    harf_yap(a_cizgi)
    
    # ===== Z Harfi =====
    # Üst yatay
    z_ust = [
        (500, -350),
        (500, -280),
        (700, -280),
        (700, -350),
    ]
    harf_yap(z_ust)
    
    # Çapraz
    z_capraz = [
        (680, -280),
        (520, 280),
        (500, 250),
        (660, -310),
    ]
    harf_yap(z_capraz)
    
    # Alt yatay
    z_alt = [
        (500, 280),
        (500, 350),
        (700, 350),
        (700, 280),
    ]
    harf_yap(z_alt)

    # Normalizasyon ve kaydetme
    pattern = pattern.get_normalized_pattern()
    
    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")
    
    print("✅ Dosyalar başarıyla oluşturuldu!")
    print(f"📊 Toplam dikiş sayısı: {len(pattern.stitches)}")
    print("📁 Çıktılar: pivaz_cikti.dst, pivaz_cikti.jef")

if __name__ == "__main__":
    mb4_kesin_cozum()
