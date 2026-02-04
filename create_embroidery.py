import pyembroidery
from PIL import Image, ImageFont, ImageDraw
import numpy as np

def metni_nakisa_cevir(metin, font_yolu, font_boyutu=60, dikis_sikligi=2, dolgu_kalinligi=3):
    pattern = pyembroidery.EmbPattern()
    
    # 1. Metni Görsele Çevir (Yazı tipini analiz etmek için)
    # Varsayılan bir font yükle veya belirtilen yolu kullan
    try:
        font = ImageFont.truetype(font_yolu, font_boyutu)
    except:
        print("Font bulunamadı, varsayılan yükleniyor.")
        font = ImageFont.load_default()

    # Metin boyutunu hesapla
    dummy_img = Image.new('L', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), metin, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Metni siyah-beyaz bir görsele çiz
    img = Image.new('L', (w + 20, h + 20), 0)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), metin, font=font, fill=255)
    
    data = np.array(img)
    yukseklik, genislik = data.shape

    # 2. Tarama Algoritması (Satin Fill / Sık Dolgu)
    # Görseli dikeyde tarayarak dolu pikselleri dikişe çevirir
    for x in range(0, genislik, dikis_sikligi):
        sutun = data[:, x]
        dolu_pikseller = np.where(sutun > 128)[0]
        
        if len(dolu_pikseller) > 0:
            ust_nokta = dolu_pikseller[0]
            alt_nokta = dolu_pikseller[-1]
            
            # Koordinatları nakış birimine (10x) ve merkeze göre ayarla
            nx = (x - genislik / 2) * 10
            ny_ust = (ust_nokta - yukseklik / 2) * 10
            ny_alt = (alt_nokta - yukseklik / 2) * 10
            
            # JUMP (Atlama) kontrolü: Eğer çok uzaktaysa iğneyi kaldır
            if x == 0 or (x > 0 and len(np.where(data[:, x-dikis_sikligi] > 128)[0]) == 0):
                pattern.add_stitch_absolute(pyembroidery.JUMP, int(nx), int(ny_ust))
            
            # Sık dolgu (Zikzak) dikişi
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx), int(ny_ust))
            pattern.add_stitch_absolute(pyembroidery.STITCH, int(nx), int(ny_alt))

    # Dosyaları Kaydet
    pattern = pattern.get_normalized_pattern()
    pyembroidery.write(pattern, "ozel_tasarim.dst")
    pyembroidery.write(pattern, "ozel_tasarim.jef")
    print(f"'{metin}' yazısı başarıyla üretildi.")

if __name__ == "__main__":
    # BURAYI İŞ YERİNDEKİ İHTİYACA GÖRE DEĞİŞTİREBİLİRSİN:
    AYARLAR = {
        "metin": "SELMAN", 
        "font_yolu": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # GitHub Actions Linux font yolu
        "font_boyutu": 80,   # Yazı büyüklüğü
        "dikis_sikligi": 3,  # NE KADAR KÜÇÜKSE O KADAR SIK (2 veya 3 ideal dolgudur)
    }
    
    metni_nakisa_cevir(**AYARLAR)
