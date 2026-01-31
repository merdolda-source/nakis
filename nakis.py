import pyembroidery
from PIL import Image, ImageFont, ImageDraw

# 13x8 cm ölçülerini belirle (Yüksek çözünürlüklü bir canvas)
width, height = 1300, 800 
text = "PİVAZ"

# Yazıyı oluştur ve dikiş noktalarına çevir
# Not: Profesyonel sonuç için "vfont" kütüphaneleri tercih edilir.
pattern = pyembroidery.EmbPattern()
# Yazı karakterlerini dikiş bloklarına ekleme işlemleri burada yapılır...

pyembroidery.write(pattern, "pivaz_nakis.dst")
