import pyembroidery
import sys

def profesyonel_sarma_nakis(metin, genislik_mm, yukseklik_mm):
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 Birimi: 1mm = 10 birim.
    w = genislik_mm * 10
    h = yukseklik_mm * 10
    harf_sayisi = len(metin)
    harf_genisligi = w / harf_sayisi

    def dolgu_olustur(x_basla, y_basla, h_genislik, h_yukseklik):
        # Harf iskeletini doldurmak için zikzak (Satin) dikiş
        # 0.4mm (4 birim) aralıkla sık dikiş atarak 'kalın' görünüm sağlar
        offset_x = x_basla - (w / 2)
        offset_y = y_basla - (h / 2)
        
        # Başlangıca zıpla
        pattern.add_stitch_absolute(pyembroidery.JUMP, int(offset_x), int(offset_y))
        
        # Sarma dikiş simülasyonu (Zigzag)
        for i in range(0, int(h_yukseklik), 4):
            # Sol taraf vuruşu
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(offset_x), int(offset_y + i))
            # Sağ taraf vuruşu (3mm kalınlığında sarma yapar)
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(offset_x + 30), int(offset_y + i))
        
        pattern.add_command(pyembroidery.JUMP)

    # Her harf için bir dolgu alanı oluştur
    for i in range(harf_sayisi):
        dolgu_olustur(i * harf_genisligi, 0, harf_genisligi, h)

    pattern = pattern.get_normalized_pattern()
    
    # Çıktı isimlerini YML ile uyumlu yapıyoruz
    pyembroidery.write(pattern, "pivaz_cikti.dst")
    pyembroidery.write(pattern, "pivaz_cikti.jef")
    print(f"Tamamlandı: {metin} için {genislik_mm}x{yukseklik_mm} ölçüsünde dolgu nakış üretildi.")

if __name__ == "__main__":
    # GitHub'dan gelen: Metin, Genişlik, Yükseklik
    args = sys.argv
    user_text = args[1] if len(args) > 1 else "ISMAIL"
    user_w = int(args[2]) if len(args) > 2 else 120
    user_h = int(args[3]) if len(args) > 3 else 65
    profesyonel_sarma_nakis(user_text, user_w, user_h)
