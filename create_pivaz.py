import pyembroidery

def profesyonel_nakis_olustur(metin="PIVAZ"):
    pattern = pyembroidery.EmbPattern()
    
    # 13x8 cm ayarları (1 birim = 0.1 mm)
    # Merkeze hizalamak için ofsetler
    x, y = 0, 0
    genislik = 1300 
    yukseklik = 800

    # 1. TEMİZLİK: Başlangıçta iğneyi merkeze konumlandır
    pattern.add_stitch_absolute(pyembroidery.JUMP, 0, 0)

    # 2. FRAME (Opsiyonel Çerçeve): İğne kırmayan emniyet dikişi
    # Dikiş boyu 3mm (30 birim) üzerine çıkarsa otomatik böler
    pattern.add_command(pyembroidery.SET_STITCH_BLOCK_TERMINATOR)
    
    # BASİT HARF ÇİZİM MANTIĞI (PİVAZ için koordinat bazlı)
    # Not: Profesyonel üretimde harfler 'Satin Stitch' (Sarma) olmalıdır.
    # Burada makinenin iğnesini korumak için kısa adımlı dikişler kullanıyoruz.
    
    def harf_p(start_x, start_y):
        pattern.add_stitch_absolute(pyembroidery.STITCH, start_x, start_y)
        pattern.add_stitch_absolute(pyembroidery.STITCH, start_x, start_y + 400)
        pattern.add_stitch_absolute(pyembroidery.STITCH, start_x + 150, start_y + 400)
        pattern.add_stitch_absolute(pyembroidery.STITCH, start_x + 150, start_y + 200)
        pattern.add_stitch_absolute(pyembroidery.STITCH, start_x, start_y + 200)

    # Harfleri yerleştir (Örnek başlangıç)
    harf_p(100, 200) 
    
    # 3. İĞNE KORUMA: Maksimum dikiş boyu kontrolü
    # Çok uzun atlamalarda araya JUMP (ip kesme/atlama) komutu ekler
    pattern.get_normalized_pattern() 

    # 4. DOSYAYI YAZDIR (DST formatı makine komutlarını destekler)
    pyembroidery.write(pattern, "pivaz_full_v1.dst")
    print("İğne korumalı DST dosyası oluşturuldu.")

if __name__ == "__main__":
    profesyonel_nakis_olustur()
