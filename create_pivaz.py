from PIL import Image, ImageFilter
import pyembroidery

MM = 10
MAX_WIDTH_MM = 120

# MAKİNEYE GÖRE AYAR
SEYREK = 10   # hızlı (büyük alan)
SIKI = 5      # yavaş (detay)
KONTUR = 3

def load_and_prepare(path):
    img = Image.open(path).convert("L")
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = img.point(lambda x: 0 if x < 140 else 255, "1")
    return img

def fill_area(pattern, img, step):
    px = img.load()
    w, h = img.size

    for y in range(0, h, step):
        drawing = False
        for x in range(0, w):
            if px[x, y] == 0:
                if not drawing:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                    drawing = True
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            else:
                drawing = False

def contour(pattern, img):
    px = img.load()
    w, h = img.size

    for y in range(1, h-1):
        for x in range(1, w-1):
            if px[x, y] == 0:
                if (
                    px[x-1,y] == 255 or px[x+1,y] == 255 or
                    px[x,y-1] == 255 or px[x,y+1] == 255
                ):
                    pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

def main():
    img = load_and_prepare("logo.png")

    scale = (MAX_WIDTH_MM * MM) / img.width
    img = img.resize((int(img.width * scale), int(img.height * scale)))

    pattern = pyembroidery.EmbPattern()

    # 1️⃣ Büyük alan – hızlı
    fill_area(pattern, img, SEYREK)

    # 2️⃣ Aynı alan – sık
    fill_area(pattern, img, SIKI)

    # 3️⃣ Kontur – en son
    contour(pattern, img)

    pattern.add_command(pyembroidery.END)
    pattern = pattern.get_normalized_pattern()

    pyembroidery.write(pattern, "tatli_duragi.dst")
    pyembroidery.write(pattern, "tatli_duragi.jef")

    print("✅ PROFESYONEL NAKIŞ ÜRETİLDİ")

if __name__ == "__main__":
    main()
