import pyembroidery
import math

def mb4_modern_pivaz():
    pattern = pyembroidery.EmbPattern()
    
    # Ayarlar
    KALINLIK = 30  # 3mm kalınlık (Satin genişliği)
    ADIM_SIKLIGI = 5 # Dikişler arası mesafe (Daha küçük = Daha sık/kaliteli)

    def satin_dik(x1, y1, x2, y2, genislik=KALINLIK):
        # Çizginin açısını hesapla
        angle = math.atan2(y2 - y1, x2 - x1)
        # Dik açı (90 derece) hesapla (Kalınlık vermek için)
        dx = math.sin(angle) * (genislik / 2)
        dy = math.cos(angle) * (genislik / 2)
        
        # Başlangıç noktasına git
        pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1 - dx), int(y1 + dy))
        
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        steps = int(distance / ADIM_SIKLIGI)
        if steps < 1: steps = 1
        
        for i in range(steps + 1):
            curr_x = x1 + (x2 - x1) * (i / steps)
            curr_y = y1 + (y2 - y1) * (i / steps)
            
            # Zig-zag yapısı: Bir sağ kenara bir sol kenara bat
            if i % 2 == 0:
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x - dx), int(curr_y + dy))
            else:
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(curr_x + dx), int(curr_y - dy))

    # PİVAZ Tasarımı (Merkezli)
    # P Harfi
    satin_dik(-500, 300, -500, -300) # Dikey
    satin_dik(-500, -300, -300, -300) # Üst
    satin_dik(-300, -300, -300, 0)    # Yan
    satin_dik(-300, 0, -500, 0)       # Orta
    
    # İ Harfi
    satin_dik(-200, 300, -200, -200) # Gövde
    satin_dik(-200, -280, -200, -320, genislik=40) # Nokta (Kalın bir vuruş)

    # V Harfi
    satin_dik(-100, -300, 0, 300)
    satin_dik(0, 300, 100, -300)

    # A Harfi
    satin_dik(200, 300, 350, -300)
    satin_dik(350, -300, 500, 300)
    satin_dik(275, 0, 425, 0)

    # Z Harfi
    satin_dik(600, -300, 800, -300)
    satin_dik(800, -300, 600, 300)
    satin_dik(600, 300, 800, 300)

    # Temizlik ve Kayıt
    pattern = pattern.get_normalized_pattern()
    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")
    print("Modern Satin dikiş dosyaları üretildi.")

if __name__ == "__main__":
    mb4_modern_pivaz()
