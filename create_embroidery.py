import pyembroidery
from PIL import Image, ImageFont, ImageDraw
import numpy as np

def profesyonel_nakis_uretimi(metin="PIVAZ", font_boyutu=100, siklik=3):
    pattern = pyembroidery.EmbPattern()
    
    # 1. Fontu Hazırla (Linux standart yolu)
    font_yolu = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_yolu, font_boyutu)
    except:
        font = ImageFont.load_default()

    # 2. Metin Analizi
    dummy_img = Image.new('L', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), metin, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    img = Image.new('L', (w + 40, h + 40), 0)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), metin, font=font, fill=255)
    
    data = np.array(img)
    yukseklik, genislik = data.shape

    # 3. Akıllı Nakış İşleme (Underlay + Satin)
    for x in range(0, genislik, siklik):
        sutun = data[:, x]
        dolu_indisler = np.where(sutun > 128)[0]
        
        if len(dolu_indisler) > 0:
            gruplar = np.split(dolu_indisler, np.where(np.diff(dolu_indisler) > 1)[0] + 1)
            
            for grup in gruplar:
                if len(grup) < 3: continue
                
                ust = grup[0]
                alt = grup[-1]
                nx = (x - genislik / 2) * 10
                ny_ust = (ust - yukseklik / 2) * 10
                ny_alt = (alt - yukseklik / 2) * 10

                # --- UNDERLAY (Alt Destek): Boğulmayı önleyen sihirli dikiş ---
                # Harfin tam ortasına tek bir dikiş atarak zemini sabitler
                orta_y = (ny_ust + ny_alt) / 2
                pattern.add_stitch_absolute(pyembroidery.JUMP, int(nx), int(ny_ust))
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx), int(orta_y))

                # --- SATIN (Üst Dolgu): Gerçek dolgun görünüm ---
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx), int(ny_ust))
                pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx + (siklik/2)), int(ny_alt))

    # 4. Kayıt (İsimleri YAML ile eşliyoruz)
    pattern = pattern.get_normalized_pattern()
    pyembroidery.write(pattern, "nakis_final.dst")
    pyembroidery.write(pattern, "nakis_final.jef")
    print(f"'{metin}' dosyası başarıyla oluşturuldu.")

if __name__ == "__main__":
    # Buradaki değerleri iş yerine göre manuel de değiştirebilirsin
    profesyonel_nakis_uretimi(metin="PIVAZ", font_boyutu=110, siklik=4)
