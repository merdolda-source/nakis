import pyembroidery
import sys

def uret_satin_nakis(metin, genislik_mm, yukseklik_mm):
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 Birimi: 1mm = 10 birim
    w = genislik_mm * 10
    h = yukseklik_mm * 10
    
    # Harf başı genişlik (Basit bölme)
    harf_genislik = w / len(metin)
    
    def sarma_dikiş_ciz(x, y, harf):
        # Bu fonksiyon harfleri sembolik sarma dikişe çevirir
        # Her harf için zikzak dikiş mantığı (Satin Stitch)
        offset_x = x - (w / 2)
        offset_y = y - (h / 2)
        
        # Harf iskeletine göre sık zikzaklar atar (İğne kırmaz, dolgun görünür)
        for i in range(0, int(h), 5): # 0.5mm aralıkla zikzak
            # Sol taraf
            pattern.add_stitch_absolute(pyembroidery.STITCH, offset_x, offset_y + i)
            # Sağ taraf (3mm genişlikte sarma)
            pattern.add_stitch_absolute(pyembroidery.STITCH, offset_x + 30, offset_y + i)
        
        pattern.add_command(pyembroidery.JUMP)

    # Metni işle
    for i, harf in enumerate(metin):
        sarma_dikiş_ciz(i * harf_genislik, 0, harf)

    pattern = pattern.get_normalized_pattern()
    pyembroidery.write(pattern, "pivaz_ozel.dst")
    pyembroidery.write(pattern, "pivaz_ozel.jef")

if __name__ == "__main__":
    # GitHub'dan gelen argümanları oku
    m = sys.argv[1] if len(sys.argv) > 1 else "PIVAZ"
    g = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    y = int(sys.argv[3]) if len(sys.argv) > 3 else 70
    uret_satin_nakis(m, g, y)
