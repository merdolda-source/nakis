import pyembroidery
from PIL import Image, ImageDraw

def nakis_uret():
    pattern = pyembroidery.EmbPattern()
    
    # 13x8 cm Görsel Önizleme Tuvali (1300x800 pixel)
    img = Image.new('RGB', (1300, 800), color='white')
    draw = ImageDraw.Draw(img)

    def cizgi_ekle(x1, y1, x2, y2):
        # Nakış Komutu (DST için)
        pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y2)
        # Önizleme Çizimi (PNG için)
        draw.line([x1, y1, x2, y2], fill='black', width=8)

    # PİVAZ Koordinat Tasarımı (1300x800 sınırlarında)
    # P
    cizgi_ekle(100, 100, 100, 700)
    cizgi_ekle(100, 100, 300, 100)
    cizgi_ekle(300, 100, 300, 400)
    cizgi_ekle(300, 400, 100, 400)
    
    # I
    cizgi_ekle(450, 100, 450, 700)
    
    # V
    cizgi_ekle(550, 100, 700, 700)
    cizgi_ekle(700, 700, 850, 100)
    
    # A
    cizgi_ekle(950, 700, 1100, 100)
    cizgi_ekle(1100, 100, 1250, 700)
    cizgi_ekle(1025, 400, 1175, 400)

    # 1. Nakış Dosyasını Kaydet
    pattern.add_command(pyembroidery.END)
    pyembroidery.write(pattern, "pivaz_13x8.dst")
    
    # 2. Önizleme Resmini Kaydet
    img.save("onizleme.png")
    print("İşlem Başarılı: DST ve PNG üretildi.")

if __name__ == "__main__":
    nakis_uret()
