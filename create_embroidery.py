import pyembroidery
from PIL import Image, ImageFont, ImageDraw
import numpy as np

def profesyonel_nakis_sistemi(metin, font_yolu, font_boyutu=100, siklik=4):
    pattern = pyembroidery.EmbPattern()
    
    # 1. Font Yükleme
    try:
        font = ImageFont.truetype(font_yolu, font_boyutu)
    except:
        font = ImageFont.load_default()

    # 2. Metni Analiz Et (Hassas Render)
    dummy_img = Image.new('L', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), metin, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    img = Image.new('L', (w + 40, h + 40), 0)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), metin, font=font, fill=255)
    
    data = np.array(img)
    yukseklik, genislik = data.shape

    # 3. Akıllı Segment Tarama (Boğulmayı önleyen kısım)
    for x in range(0, genislik, siklik):
        sutun = data[:, x]
        # Sütundaki dolu piksellerin gruplarını bul (Örn: 'P' harfinde üst ve alt iki ayrı parça)
        dolu_indisler = np.where(sutun > 128)[0]
        
        if len(dolu_indisler) > 0:
            # Kesintisiz blokları bul (Harf boşluklarını korumak için)
            gruplar = np.split(dolu_indisler, np.where(np.diff(dolu_indisler) > 1)[0] + 1)
            
            for grup in gruplar:
                if len(grup) < 2: continue # Çok küçük noktaları dikme (temiz görünüm)
                
                ust = grup[0]
                alt = grup[-1]
                
                # Koordinat Dönüşümü (Janome MB-4 için)
                nx = (x - genislik / 2) * 10
                ny_ust = (ust - yukseklik / 2) * 10
                ny_alt = (alt - yukseklik / 2) * 10
                
                # Her yeni parça başlangıcında JUMP yap (Boğulmayı ve ip karışıklığını önler)
                pattern.add_stitch_absolute(pyembroidery.JUMP, int(nx), int(ny_ust))
                
                # Zigzag Dolgu (Satin benzeri yapı)
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx), int(ny_ust))
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx + 2), int(ny_alt)) # Hafif eğim netlik kazandırır

    # 4. Temizlik ve Kayıt
    pattern = pattern.get_normalized_pattern()
    
    # MB-4'ün tanıması için isim ve format
    pyembroidery.write(pattern, "pivaz_modern.dst")
    pyembroidery.write(pattern, "pivaz_modern.jef")
    print(f"'{metin}' için temiz ve profesyonel nakış dosyası hazırlandı.")

if __name__ == "__main__":
    # BURADAN AYARLARI YAPABİLİRSİN
    PROFESYONEL_AYARLAR = {
        "metin": "PIVAZ", 
        "font_yolu": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # GitHub Linux yolu
        "font_boyutu": 120, # Daha büyük harf = daha net sonuç
        "siklik": 3        # 3-4 idealdir. 2 yaparsan çok sıkışır, boğulma yapar.
    }
    profesyonel_nakis_sistemi(**PROFESYONEL_AYARLAR)
