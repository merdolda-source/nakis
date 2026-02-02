import pyembroidery
from PIL import Image, ImageDraw

def nakis_uret_full_paket():
    pattern = pyembroidery.EmbPattern()
    
    # MB-4 için 13x8 cm (1300x800 birim)
    # Görsel önizleme için tuval
    img = Image.new('RGB', (1300, 800), color='white')
    draw = ImageDraw.Draw(img)

    def cizgi_ekle(x1, y1, x2, y2):
        # Nakış Komutu: JUMP (Atla) ve STITCH (Dik)
        # Koordinatları merkeze göre ofsetliyoruz (Janome Standardı)
        pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        pattern.add_stitch_absolute(pyembroidery.STITCH, x2, y2)
        # Önizleme resmi çizimi
        draw.line([x1, y1, x2, y2], fill='black', width=6)

    # PİVAZ Tasarımı (Merkezlenmiş Koordinatlar)
    # P
    cizgi_ekle(100, 150, 100, 650)
    cizgi_ekle(100, 150, 250, 150)
    cizgi_ekle(250, 150, 250, 350)
    cizgi_ekle(250, 350, 100, 350)
    # I
    cizgi_ekle(350, 150, 350, 650)
    # V
    cizgi_ekle(450, 150, 550, 650)
    cizgi_ekle(550, 650, 650, 150)
    # A
    cizgi_ekle(750, 650, 850, 150)
    cizgi_ekle(850, 150, 950, 650)
    cizgi_ekle(800, 450, 900, 450)
    # Z
    cizgi_ekle(1050, 150, 1200, 150)
    cizgi_ekle(1200, 150, 1050, 650)
    cizgi_ekle(1050, 650, 1200, 650)

    pattern.add_command(pyembroidery.END)

    # Dosyaları Kaydet
    pyembroidery.write(pattern, "pivaz_final.dst") # Endüstriyel / MB-4
    pyembroidery.write(pattern, "pivaz_final.jef") # Janome Ev Tipi / MB-4
    img.save("onizleme.png")
    print("Üretim tamam: DST, JEF ve PNG hazır.")

if __name__ == "__main__":
    nakis_uret_full_paket()
