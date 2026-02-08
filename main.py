import pyembroidery
import math
import matplotlib.pyplot as plt

class ProfesyonelNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "UltraSargi"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def _sargi_dik(self, x1, y1, x2, y2, kalinlik_mm):
        """Saf satin sargı - sadece STITCH üretir, JUMP/TRIM yok"""
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0:
            return

        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        MAX_DIKIŞ = 70
        if genislik > MAX_DIKIŞ:
            ara_adim = int(math.ceil(genislik / MAX_DIKIŞ))
        else:
            ara_adim = 1

        YOGUNLUK = 2
        steps = int(dist // YOGUNLUK)
        if steps < 2:
            steps = 2

        for i in range(steps + 1):
            ratio = i / steps
            cx = x1 + (dx * ratio)
            cy = y1 + (dy * ratio)
            
            if ara_adim > 1:
                if i % 2 == 0:
                    for j in range(ara_adim + 1):
                        t = j / ara_adim
                        px = cx - nx + (2 * nx * t)
                        py = cy - ny + (2 * ny * t)
                        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(px), int(py))
                else:
                    for j in range(ara_adim + 1):
                        t = j / ara_adim
                        px = cx + nx - (2 * nx * t)
                        py = cy + ny - (2 * ny * t)
                        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(px), int(py))
            else:
                if i % 2 == 0:
                    self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
                else:
                    self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))

    def _harf_dik(self, cizgiler, mevcut_x, by, scale, gen_carpan, yuk_carpan, sargi_kalinligi):
        """Tek bir harfi kesintisiz olarak diker: 1 JUMP -> underlay -> sargı -> 1 TRIM"""
        
        if not cizgiler or len(cizgiler) == 0:
            return

        # ===== 1. JUMP: Harfin ilk noktasına atla =====
        ilk = cizgiler[0]
        gx = mevcut_x + (ilk[0] * scale * gen_carpan)
        gy = by + (ilk[1] * scale * yuk_carpan)
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(gx), int(gy))

        # ===== 2. UNDERLAY: Tüm segmentleri düz çizgi olarak tek geçişte dik =====
        for (lx1, ly1, lx2, ly2) in cizgiler:
            sx = mevcut_x + (lx1 * scale * gen_carpan)
            sy = by + (ly1 * scale * yuk_carpan)
            ex = mevcut_x + (lx2 * scale * gen_carpan)
            ey = by + (ly2 * scale * yuk_carpan)
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(sx), int(sy))
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(ex), int(ey))

        # ===== 3. SARGI: İlk segmentin başına dön, sonra tüm segmentleri sargıla =====
        ilk_sx = mevcut_x + (cizgiler[0][0] * scale * gen_carpan)
        ilk_sy = by + (cizgiler[0][1] * scale * yuk_carpan)
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(ilk_sx), int(ilk_sy))

        for (lx1, ly1, lx2, ly2) in cizgiler:
            sx = mevcut_x + (lx1 * scale * gen_carpan)
            sy = by + (ly1 * scale * yuk_carpan)
            ex = mevcut_x + (lx2 * scale * gen_carpan)
            ey = by + (ly2 * scale * yuk_carpan)
            # Segment başlangıcına STITCH ile git
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(sx), int(sy))
            # Satin sargı yap
            self._sargi_dik(sx, sy, ex, ey, sargi_kalinligi)

        # ===== 4. TRIM: Harf bitti, iplik kes =====
        self.pattern.add_stitch_absolute(pyembroidery.TRIM, 0, 0)

    def isim_yaz(self, metin, baslangic_x, baslangic_y, boyut_cm, birim="cm"):
        if birim == "cm":
            harf_boyu_mm = boyut_cm * 10
        elif birim == "mm":
            harf_boyu_mm = boyut_cm
        else:
            harf_boyu_mm = boyut_cm * 10

        if birim == "cm":
            bx = baslangic_x * 100
            by = baslangic_y * 100
        elif birim == "mm":
            bx = baslangic_x * 10
            by = baslangic_y * 10
        else:
            bx = baslangic_x * 100
            by = baslangic_y * 100

        mevcut_x = bx
        scale = harf_boyu_mm * 10
        bosluk = scale * 0.25

        bh_gen = 0.7
        kh_yuk = 0.6
        kh_gen = 0.55
        sy_gen = 0.65

        buyuk_harfler = {
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.2,0.4, 0.8,0.4)],
            'B': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.7,0.55), (0.7,0.55, 0,0.55), (0,0.55, 0.75,0.55), (0.75,0.55, 0.75,0), (0.75,0, 0,0)],
            'C': [(1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15)],
            'D': [(0,0, 0,1), (0,1, 0.6,1), (0.6,1, 1,0.7), (1,0.7, 1,0.3), (1,0.3, 0.6,0), (0.6,0, 0,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.8,0.5)],
            'F': [(0.9,1, 0,1), (0,1, 0,0), (0,0.5, 0.7,0.5)],
            'G': [(1,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5)],
            'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
            'I': [(0.5,0, 0.5,1)],
            'J': [(0.7,1, 0.7,0.2), (0.7,0.2, 0.5,0), (0.5,0, 0.2,0), (0.2,0, 0,0.2)],
            'K': [(0,0, 0,1), (0.9,1, 0,0.45), (0,0.45, 0.9,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'M': [(0,0, 0,1), (0,1, 0.5,0.3), (0.5,0.3, 1,1), (1,1, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
            'O': [(0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15), (1,0.15, 1,0.85), (1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15)],
            'P': [(0,0, 0,1), (0,1, 0.75,1), (0.75,1, 0.75,0.5), (0.75,0.5, 0,0.5)],
            'Q': [(0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15), (1,0.15, 1,0.85), (1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15), (0.7,0.3, 1.05,0)],
            'R': [(0,0, 0,1), (0,1, 0.75,1), (0.75,1, 0.75,0.5), (0.75,0.5, 0,0.5), (0.45,0.5, 0.9,0)],
            'S': [(1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.55), (0,0.55, 0.15,0.5), (0.15,0.5, 0.85,0.5), (0.85,0.5, 1,0.45), (1,0.45, 1,0.15), (1,0.15, 0.85,0), (0.85,0, 0.15,0), (0.15,0, 0,0.15)],
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            'U': [(0,1, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15), (1,0.15, 1,1)],
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'W': [(0,1, 0.25,0), (0.25,0, 0.5,0.6), (0.5,0.6, 0.75,0), (0.75,0, 1,1)],
            'X': [(0,0, 1,1), (0,1, 1,0)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
        }

        kucuk_harfler = {
            'a': [(0.85,0.6, 0.85,0), (0.85,0.5, 0.65,0.6), (0.65,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.2), (0,0.2, 0.2,0), (0.2,0, 0.85,0)],
            'b': [(0,0, 0,1), (0,0.5, 0.2,0.6), (0.2,0.6, 0.7,0.6), (0.7,0.6, 0.85,0.45), (0.85,0.45, 0.85,0.15), (0.85,0.15, 0.7,0), (0.7,0, 0,0)],
            'c': [(0.85,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.85,0)],
            'd': [(0.85,0, 0.85,1), (0.85,0.5, 0.65,0.6), (0.65,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.85,0)],
            'e': [(0,0.35, 0.85,0.35), (0.85,0.35, 0.85,0.45), (0.85,0.45, 0.65,0.6), (0.65,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.85,0)],
            'f': [(0.2,0, 0.2,0.85), (0.2,0.85, 0.35,1), (0.35,1, 0.65,1), (0,0.6, 0.55,0.6)],
            'g': [(0.85,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.2), (0,0.2, 0.2,0.05), (0.2,0.05, 0.85,0.05), (0.85,0.6, 0.85,-0.2), (0.85,-0.2, 0.65,-0.35), (0.65,-0.35, 0.15,-0.35)],
            'h': [(0,0, 0,1), (0,0.5, 0.25,0.6), (0.25,0.6, 0.65,0.6), (0.65,0.6, 0.85,0.5), (0.85,0.5, 0.85,0)],
            'i': [(0.4,0, 0.4,0.6), (0.4,0.8, 0.4,0.85)],
            'j': [(0.5,0.8, 0.5,0.85), (0.5,0.6, 0.5,-0.15), (0.5,-0.15, 0.3,-0.35), (0.3,-0.35, 0.05,-0.35)],
            'k': [(0,0, 0,1), (0.75,0.6, 0,0.25), (0,0.25, 0.75,0)],
            'l': [(0.4,0, 0.4,1)],
            'm': [(0,0, 0,0.6), (0,0.5, 0.15,0.6), (0.15,0.6, 0.35,0.6), (0.35,0.6, 0.5,0.5), (0.5,0.5, 0.5,0), (0.5,0.5, 0.65,0.6), (0.65,0.6, 0.85,0.6), (0.85,0.6, 1,0.5), (1,0.5, 1,0)],
            'n': [(0,0, 0,0.6), (0,0.5, 0.25,0.6), (0.25,0.6, 0.65,0.6), (0.65,0.6, 0.85,0.5), (0.85,0.5, 0.85,0)],
            'o': [(0.2,0, 0,0.15), (0,0.15, 0,0.45), (0,0.45, 0.2,0.6), (0.2,0.6, 0.65,0.6), (0.65,0.6, 0.85,0.45), (0.85,0.45, 0.85,0.15), (0.85,0.15, 0.65,0), (0.65,0, 0.2,0)],
            'p': [(0,0.6, 0,-0.35), (0,0.5, 0.2,0.6), (0.2,0.6, 0.7,0.6), (0.7,0.6, 0.85,0.45), (0.85,0.45, 0.85,0.15), (0.85,0.15, 0.7,0), (0.7,0, 0,0)],
            'q': [(0.85,0.6, 0.85,-0.35), (0.85,0.5, 0.65,0.6), (0.65,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.85,0)],
            'r': [(0,0, 0,0.6), (0,0.45, 0.2,0.6), (0.2,0.6, 0.6,0.6), (0.6,0.6, 0.8,0.5)],
            's': [(0.8,0.55, 0.6,0.6), (0.6,0.6, 0.2,0.6), (0.2,0.6, 0,0.5), (0,0.5, 0,0.38), (0,0.38, 0.15,0.32), (0.15,0.32, 0.7,0.32), (0.7,0.32, 0.85,0.22), (0.85,0.22, 0.85,0.1), (0.85,0.1, 0.65,0), (0.65,0, 0.2,0), (0.2,0, 0,0.05)],
            't': [(0.25,0, 0.25,0.9), (0,0.6, 0.6,0.6), (0.25,0.05, 0.45,0), (0.45,0, 0.6,0.05)],
            'u': [(0,0.6, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.65,0), (0.65,0, 0.85,0.1), (0.85,0.6, 0.85,0)],
            'v': [(0,0.6, 0.45,0), (0.45,0, 0.9,0.6)],
            'w': [(0,0.6, 0.2,0), (0.2,0, 0.45,0.4), (0.45,0.4, 0.7,0), (0.7,0, 0.9,0.6)],
            'x': [(0,0, 0.85,0.6), (0,0.6, 0.85,0)],
            'y': [(0,0.6, 0.45,0), (0.9,0.6, 0.2,-0.35)],
            'z': [(0,0.6, 0.85,0.6), (0.85,0.6, 0,0), (0,0, 0.85,0)],
        }

        sayilar = {
            '0': [(0.15,0, 0,0.15), (0,0.15, 0,0.85), (0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.15), (0.9,0.15, 0.75,0), (0.75,0, 0.15,0)],
            '1': [(0.2,0.8, 0.5,1), (0.5,1, 0.5,0), (0.2,0, 0.8,0)],
            '2': [(0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.6), (0.9,0.6, 0.75,0.5), (0.75,0.5, 0,0), (0,0, 0.9,0)],
            '3': [(0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.6), (0.9,0.6, 0.75,0.5), (0.75,0.5, 0.4,0.5), (0.75,0.5, 0.9,0.4), (0.9,0.4, 0.9,0.15), (0.9,0.15, 0.75,0), (0.75,0, 0.15,0), (0.15,0, 0,0.15)],
            '4': [(0.7,0, 0.7,1), (0.7,1, 0,0.35), (0,0.35, 0.9,0.35)],
            '5': [(0.9,1, 0,1), (0,1, 0,0.55), (0,0.55, 0.7,0.55), (0.7,0.55, 0.9,0.4), (0.9,0.4, 0.9,0.15), (0.9,0.15, 0.75,0), (0.75,0, 0.15,0), (0.15,0, 0,0.15)],
            '6': [(0.8,0.9, 0.6,1), (0.6,1, 0.2,1), (0.2,1, 0,0.85), (0,0.85, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 0.75,0), (0.75,0, 0.9,0.15), (0.9,0.15, 0.9,0.4), (0.9,0.4, 0.75,0.55), (0.75,0.55, 0.15,0.55), (0.15,0.55, 0,0.4)],
            '7': [(0,1, 0.9,1), (0.9,1, 0.35,0)],
            '8': [(0.15,0.5, 0,0.4), (0,0.4, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 0.75,0), (0.75,0, 0.9,0.15), (0.9,0.15, 0.9,0.4), (0.9,0.4, 0.75,0.5), (0.75,0.5, 0.15,0.5), (0.15,0.5, 0,0.6), (0,0.6, 0,0.85), (0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.6), (0.9,0.6, 0.75,0.5)],
            '9': [(0.1,0.1, 0.3,0), (0.3,0, 0.7,0), (0.7,0, 0.9,0.15), (0.9,0.15, 0.9,0.85), (0.9,0.85, 0.75,1), (0.75,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.6), (0,0.6, 0.15,0.45), (0.15,0.45, 0.75,0.45), (0.75,0.45, 0.9,0.6)],
        }

        turkce_buyuk = {
            'Ç': [
                (1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15),
                (0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15),
                (0.35,-0.15, 0.5,-0.3), (0.5,-0.3, 0.65,-0.15)
            ],
            'Ğ': [
                (1,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15), (0,0.15, 0.15,0),
                (0.15,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5),
                (0.3,1.1, 0.5,1.2), (0.5,1.2, 0.7,1.1)
            ],
            'İ': [(0.5,0, 0.5,1), (0.5,1.1, 0.5,1.15)],
            'Ö': [
                (0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15), (1,0.15, 1,0.85),
                (1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.15),
                (0.3,1.1, 0.3,1.18), (0.7,1.1, 0.7,1.18)
            ],
            'Ş': [
                (1,0.85, 0.85,1), (0.85,1, 0.15,1), (0.15,1, 0,0.85), (0,0.85, 0,0.55),
                (0,0.55, 0.15,0.5), (0.15,0.5, 0.85,0.5), (0.85,0.5, 1,0.45),
                (1,0.45, 1,0.15), (1,0.15, 0.85,0), (0.85,0, 0.15,0), (0.15,0, 0,0.15),
                (0.35,-0.15, 0.5,-0.3), (0.5,-0.3, 0.65,-0.15)
            ],
            'Ü': [
                (0,1, 0,0.15), (0,0.15, 0.15,0), (0.15,0, 0.85,0), (0.85,0, 1,0.15), (1,0.15, 1,1),
                (0.3,1.1, 0.3,1.18), (0.7,1.1, 0.7,1.18)
            ],
        }

        turkce_kucuk = {
            'ç': [
                (0.85,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.85,0),
                (0.3,-0.12, 0.45,-0.25), (0.45,-0.25, 0.6,-0.12)
            ],
            'ğ': [
                (0.85,0.6, 0.2,0.6), (0.2,0.6, 0,0.45), (0,0.45, 0,0.2), (0,0.2, 0.2,0.05),
                (0.2,0.05, 0.85,0.05), (0.85,0.6, 0.85,-0.2), (0.85,-0.2, 0.65,-0.35), (0.65,-0.35, 0.15,-0.35),
                (0.25,0.7, 0.45,0.8), (0.45,0.8, 0.65,0.7)
            ],
            'ı': [(0.4,0, 0.4,0.6)],
            'ö': [
                (0.2,0, 0,0.15), (0,0.15, 0,0.45), (0,0.45, 0.2,0.6), (0.2,0.6, 0.65,0.6),
                (0.65,0.6, 0.85,0.45), (0.85,0.45, 0.85,0.15), (0.85,0.15, 0.65,0), (0.65,0, 0.2,0),
                (0.25,0.72, 0.25,0.78), (0.6,0.72, 0.6,0.78)
            ],
            'ş': [
                (0.8,0.55, 0.6,0.6), (0.6,0.6, 0.2,0.6), (0.2,0.6, 0,0.5), (0,0.5, 0,0.38),
                (0,0.38, 0.15,0.32), (0.15,0.32, 0.7,0.32), (0.7,0.32, 0.85,0.22),
                (0.85,0.22, 0.85,0.1), (0.85,0.1, 0.65,0), (0.65,0, 0.2,0), (0.2,0, 0,0.05),
                (0.3,-0.12, 0.45,-0.25), (0.45,-0.25, 0.6,-0.12)
            ],
            'ü': [
                (0,0.6, 0,0.15), (0,0.15, 0.2,0), (0.2,0, 0.65,0), (0.65,0, 0.85,0.1), (0.85,0.6, 0.85,0),
                (0.25,0.72, 0.25,0.78), (0.6,0.72, 0.6,0.78)
            ],
        }

        ozel = {
            ' ': [],
            '-': [(0.1,0.5, 0.9,0.5)],
            '.': [(0.4,0, 0.4,0.05), (0.4,0.05, 0.45,0.05), (0.45,0.05, 0.45,0), (0.45,0, 0.4,0)],
            ',': [(0.4,0.05, 0.35,-0.15)],
            '!': [(0.45,0.25, 0.45,1), (0.45,0, 0.45,0.08)],
            '?': [(0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.6), (0.9,0.6, 0.5,0.4), (0.5,0.4, 0.5,0.25), (0.5,0, 0.5,0.08)],
            '/': [(0,0, 1,1)],
            ':': [(0.45,0.15, 0.45,0.22), (0.45,0.45, 0.45,0.52)],
            '#': [(0.3,0, 0.3,1), (0.7,0, 0.7,1), (0.05,0.35, 0.95,0.35), (0.05,0.65, 0.95,0.65)],
        }

        sargi_kalinligi = harf_boyu_mm * 0.13
        if sargi_kalinligi < 2.0:
            sargi_kalinligi = 2.0
        if sargi_kalinligi > 5.0:
            sargi_kalinligi = 5.0

        for harf in metin:
            if harf == " ":
                mevcut_x += scale * 0.5
                continue

            cizgiler = None
            gen_carpan = bh_gen
            yuk_carpan = 1.0

            if harf in buyuk_harfler:
                cizgiler = buyuk_harfler[harf]
                gen_carpan = bh_gen
                yuk_carpan = 1.0
            elif harf in turkce_buyuk:
                cizgiler = turkce_buyuk[harf]
                gen_carpan = bh_gen
                yuk_carpan = 1.0
            elif harf in kucuk_harfler:
                cizgiler = kucuk_harfler[harf]
                gen_carpan = kh_gen
                yuk_carpan = kh_yuk
            elif harf in turkce_kucuk:
                cizgiler = turkce_kucuk[harf]
                gen_carpan = kh_gen
                yuk_carpan = kh_yuk
            elif harf in sayilar:
                cizgiler = sayilar[harf]
                gen_carpan = sy_gen
                yuk_carpan = 1.0
            elif harf in ozel:
                cizgiler = ozel[harf]
                gen_carpan = 0.5
                yuk_carpan = 1.0
            else:
                mevcut_x += scale * 0.3
                continue

            if cizgiler is None or len(cizgiler) == 0:
                mevcut_x += scale * 0.3
                continue

            # Harfi tek seferde dik
            self._harf_dik(cizgiler, mevcut_x, by, scale, gen_carpan, yuk_carpan, sargi_kalinligi)

            mevcut_x += (scale * gen_carpan) + bosluk

    def onizleme_olustur(self, dosya_adi):
        print("JPG Önizleme oluşturuluyor...")
        stitches = self.pattern.stitches
        
        plt.figure(figsize=(18, 6))
        plt.axis('equal')
        plt.axis('off')
        
        x_list = []
        y_list = []

        for stitch in stitches:
            x, y = stitch[0], stitch[1]
            cmd = stitch[2]
            
            if cmd == pyembroidery.JUMP or cmd == pyembroidery.TRIM:
                if x_list:
                    plt.plot(x_list, y_list, color='darkblue', linewidth=0.5, alpha=0.8)
                    x_list = []
                    y_list = []
            elif cmd == pyembroidery.STITCH:
                x_list.append(x)
                y_list.append(y)

        if x_list:
            plt.plot(x_list, y_list, color='darkblue', linewidth=0.5, alpha=0.8)

        plt.title(f"{dosya_adi} - Nakis Onizleme", fontsize=15)
        plt.savefig(f"{dosya_adi}_onizleme.jpg", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ RESİM ÜRETİLDİ: {dosya_adi}_onizleme.jpg")

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad_temiz = dosya_adi.replace(" ", "_").lower()
        
        pyembroidery.write(self.pattern, f"{ad_temiz}.dst")
        pyembroidery.write(self.pattern, f"{ad_temiz}.jef")
        
        self.onizleme_olustur(ad_temiz)
        
        print(f"✅ NAKIŞ DOSYALARI HAZIR: {ad_temiz}.dst / {ad_temiz}.jef")


# ==========================================
# MÜŞTERİ PANELİ
# ==========================================
if __name__ == "__main__":
    
    makine = ProfesyonelNakis()

    # ========================================
    # AYARLAR (İSTEDİĞİNİZ GİBİ DEĞİŞTİRİN)
    # ========================================
    
    MUSTERI_ISMI = "SELMAN"
    BOYUT = .7
    BIRIM = "cm"
    
    # ========================================
    
    harf_sayisi = len(MUSTERI_ISMI.replace(" ", ""))
    bosluk_sayisi = MUSTERI_ISMI.count(" ")
    
    if BIRIM == "cm":
        toplam_genislik_cm = harf_sayisi * BOYUT * 0.7 + bosluk_sayisi * BOYUT * 0.5
        baslama_x = -toplam_genislik_cm / 2
    else:
        toplam_genislik_mm = harf_sayisi * BOYUT * 0.7 + bosluk_sayisi * BOYUT * 0.5
        baslama_x = -toplam_genislik_mm / 2
    
    baslama_y = 0
    
    makine.isim_yaz(MUSTERI_ISMI, baslama_x, baslama_y, BOYUT, birim=BIRIM)
    makine.kaydet(MUSTERI_ISMI)
