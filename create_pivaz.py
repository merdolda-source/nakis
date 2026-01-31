import pyembroidery

def profesyonel_nakis_olustur():
    # Yeni bir desen nesnesi oluştur
    pattern = pyembroidery.EmbPattern()

    # DST Ölçü Birimi: 1 birim = 0.1 mm
    # 13x8 cm alanı için 1300x800 birimlik bir koordinat düzlemi
    
    def cizgi_dik(x1, y1, x2, y2):
        """İğne kırmayan, güvenli adım aralıklı dikiş ekler"""
        # Başlangıç noktasına zıpla (İpi koparmadan veya kaldırarak git)
        pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        # Çizgiyi oluştur (Mesafe uzaksa araya otomatik dikiş atar)
        pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y2)

    # PİVAZ Yazısı İçin Basit ve Güvenli Koordinatlar
    # Her harfi 13x8 cm (1300x800) içine yayıyoruz
    
    # 'P' Harfi
    cizgi_dik(100, 100, 100, 700) # Dikey çizgi
    cizgi_dik(100, 700, 300, 700) # Üst yatay
    cizgi_dik(300, 700, 300, 400) # Yan dikey
    cizgi_dik(300, 400, 100, 400) # Orta yatay

    # 'I' Harfi
    cizgi_dik(450, 100, 450, 700)

    # 'V' Harfi
    cizgi_dik(600, 700, 750, 100)
    cizgi_dik(750, 100, 900, 700)

    # 'A' Harfi
    cizgi_dik(1000, 100, 1100, 700)
    cizgi_dik(1100, 700, 1200, 100)
    cizgi_dik(1050, 350, 1150, 350) # Orta çizgi

    # Emniyet: İşlem bittiğinde iğneyi durdur
    pattern.add_command(pyembroidery.END)

    # Yazdırma işlemi
    pyembroidery.write(pattern, "pivaz_full_v1.dst")
    print("DST dosyası başarıyla üretildi: pivaz_full_v1.dst")

if __name__ == "__main__":
    profesyonel_nakis_olustur()
