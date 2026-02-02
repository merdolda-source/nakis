import pyembroidery
from PIL import Image, ImageDraw

def mb4_full_v2():
    pattern = pyembroidery.EmbPattern()
    
    # 13x8 cm alanı için tuval (Önizleme amaçlı)
    img = Image.new('RGB', (1300, 800), color='white')
    draw = ImageDraw.Draw(img)

    def dikiş_at(x1, y1, x2, y2):
        # Janome MB-4 merkez koordinat kullanır. 
        # Yazıyı merkeze çekmek için değerlerden 600 ve 400 çıkarıyoruz.
        nx1, ny1 = x1 - 650, y1 - 400
        nx2, ny2 = x2 - 650, y2 - 400
        
        pattern.add_stitch_absolute(pyembroidery.JUMP, nx1, ny1)
        # İğne kırmasın diye araya küçük adımlar ekler
        pattern.add_stitch_absolute(pyembroidery.STITCH, nx2, ny2)
        # Resim önizlemesi
        draw.line([x1, y1, x2, y2], fill='black', width=10)

    # PİVAZ (Daha net görünsün diye koordinatlar büyütüldü)
    dikiş_at(200, 200, 200, 600) # P
    dikiş_at(200, 200, 400, 200)
    dikiş_at(400, 200, 400, 400)
    dikiş_at(400, 400, 200, 400)
    
    dikiş_at(500, 200, 500, 600) # I
    
    dikiş_at(600, 200, 750, 600) # V
    dikiş_at(750, 650, 900, 200)
    
    dikiş_at(1000, 600, 1100, 200) # A
    dikiş_at(1100, 200, 1200, 600)
    dikiş_at(1050, 400, 1150, 400)

    pattern.add_command(pyembroidery.END)

    # MB-4'ün en sevdiği formatlar
    pyembroidery.write(pattern, "pivaz_mb4.dst")
    pyembroidery.write(pattern, "pivaz_mb4.jef")
    img.save("onizleme.png")

if __name__ == "__main__":
    mb4_full_v2()
