from PIL import Image
import pyembroidery

MM = 10
MAX_WIDTH_MM = 130
STEP = 6  # büyüdükçe daha az kasma

def image_to_embroidery(img_path):
    pattern = pyembroidery.EmbPattern()

    img = Image.open(img_path).convert("L")  # grayscale
    w, h = img.size

    scale = (MAX_WIDTH_MM * MM) / w
    img = img.resize((int(w * scale), int(h * scale)))

    pixels = img.load()
    width, height = img.size

    for y in range(0, height, STEP):
        draw = False
        for x in range(0, width):
            if pixels[x, y] < 120:  # koyu alan
                if not draw:
                    pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                    draw = True
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            else:
                draw = False

    pattern.add_command(pyembroidery.END)
    pattern = pattern.get_normalized_pattern()

    pyembroidery.write(pattern, "tatli_duragi.dst")
    pyembroidery.write(pattern, "tatli_duragi.jef")
    print("✅ Optimize nakış üretildi")

if __name__ == "__main__":
    image_to_embroidery("logo.png")
