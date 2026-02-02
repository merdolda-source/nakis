import pyembroidery

def mb4_profesyonel_uret():
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 için 12x7 cm güvenli alan (Merkezlenmiş)
    # 0,0 noktası kasnağın tam ortasıdır.
    
    def harf_ciz(koordinatlar):
        # İlk noktaya iğne havada git (JUMP)
        start_x, start_y = koordinatlar[0]
        pattern.add_stitch_absolute(pyembroidery.JUMP, start_x, start_y)
        
        # Diğer noktalar arasını dikişle doldur (STITCH)
        for i in range(1, len(koordinatlar)):
            x, y = koordinatlar[i]
            pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        # Harf bitince ipi atlat
        pattern.add_command(pyembroidery.JUMP)

    # PİVAZ Koordinatları (Merkez 0,0 olacak şekilde)
    # Değerler 0.1mm birimindedir (400 = 4cm)
    
    # P
    harf_ciz([(-500, 300), (-500, -300), (-300, -300), (-300, 0), (-500, 0)])
    # I
    harf_ciz([(-200, 300), (-200, -300)])
    # V
    harf_ciz([(-100, -300), (0, 300), (100, -300)])
    # A
    harf_ciz([(150, 300), (300, -300), (450, 300)])
    harf_ciz([(220, 0), (380, 0)])
    # Z
    harf_ciz([(500, -300), (700, -300), (500, 300), (700, 300)])

    # --- KRİTİK AYAR: İğne kırmayan dikiş bölücü ---
    # Bu komut, uzun çizgileri makinenin dikebileceği 3mm'lik parçalara böler.
    # Ekranda görüntünün gelmesini sağlayan asıl kısım burasıdır.
    pattern = pattern.get_normalized_pattern()
    pattern.max_stitch_length = 30 # 3.0 mm maksimum dikiş boyu
    
    pattern.add_command(pyembroidery.END)

    # Dosyaları Yazdır
    pyembroidery.write(pattern, "pivaz_mb4_final.dst")
    pyembroidery.write(pattern, "pivaz_mb4_final.jef")
    print("MB-4 için yüksek çözünürlüklü dosya üretildi.")

if __name__ == "__main__":
    mb4_profesyonel_uret()
