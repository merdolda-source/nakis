import pyembroidery

def metni_dst_yap(metin, genislik_mm, yukseklik_mm):
    # Yeni bir nakış deseni oluştur
    pattern = pyembroidery.EmbPattern()

    # Ölçü birimi: 1 birim = 0.1 mm (DST standartı)
    # 130mm x 80mm için koordinatları hesaplıyoruz
    w = genislik_mm * 10
    h = yukseklik_mm * 10

    # Basit bir örnek: Metni temsil eden bir çerçeve ve 
    # dikiş noktaları ekleyelim (Pyembroidery ile yazı yazmak için 
    # manuel koordinat veya bir font dosyası işleme gerekir)
    
    # Burada basit bir 'Z' çizimi gibi nokta ekleyelim (Örnek amaçlı)
    pattern.add_stitch_relative(0, 0) # Başlangıç
    pattern.add_stitch_relative(w, 0) # Alt kenar
    pattern.add_stitch_relative(-w, h) # Çapraz
    pattern.add_stitch_relative(w, 0) # Üst kenar

    # Dosyayı kaydet
    pyembroidery.write(pattern, "pivaz_13x8.dst")
    print("DST dosyası başarıyla oluşturuldu!")

if __name__ == "__main__":
    metni_dst_yap("PIVAZ", 130, 80)
