import pyembroidery
import sys

def dolgu_harf_ureti(metin, genislik_mm, yukseklik_mm):
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 Birimi: 1mm = 10 birim. Tasarımı merkeze (0,0) odaklıyoruz.
    w = genislik_mm * 10
    h = yukseklik_mm * 10
    harf_sayisi = len(metin)
    harf_genisligi = w / harf_sayisi

    def sarma_blok_ekle(baslangic_x, y, harf_w, harf_h):
        # Harfin iskeletini doldurmak için zikzak (Satin) simülasyonu
        # Her 0.4mm'de bir iğne batırarak dolgu oluşturur
        for i in range(0, int(harf_h), 4):
            # Sol vuruş
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(baslangic_x), int(y + i))
            # Sağ vuruş (Harf kalınlığı yaklaşık 3mm)
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(baslangic_x + 30), int(y + i))
        pattern.add_command(pyembroidery.JUMP)

    # Her harf için bir dolgu bloğu oluştur
    for i in range(harf_sayisi):
        x_merkez = (i * harf_genisligi) - (w / 2)
        y_merkez = -(h / 2)
        sarma_blok_ekle(x_merkez, y_merkez, harf_genisligi, h)

    pattern = pattern.get_normalized_pattern()
    # Hem JEF hem DST üret
    pyembroidery.write(pattern, "ozel_tasarim.dst")
    pyembroidery.write(pattern, "ozel_tasarim.jef")

if __name__ == "__main__":
    # GitHub'dan gelen: Metin, Genişlik, Yükseklik
    args = sys.argv
    metin = args[1] if len(args) > 1 else "ISMAIL"
    g = int(args[2]) if len(args) > 2 else 120
    y = int(args[3]) if len(args) > 3 else 65
    dolgu_harf_ureti(metin, g, y)
