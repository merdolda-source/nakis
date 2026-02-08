import pyembroidery
import math
import matplotlib.pyplot as plt

class ProfesyonelNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "UltraSargi"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def tam_sargi_yap(self, x1, y1, x2, y2, kalinlik_mm):
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0:
            return

        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # === 1. ALT DOLGU (UNDERLAY) ===
        kucultme = 0.7
        nx_alt = nx * kucultme
        ny_alt = ny * kucultme

        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1), int(y1))
        
        steps_alt = int(dist // 30) + 1
        for i in range(steps_alt + 1):
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1 + dx * i / steps_alt), int(y1 + dy * i / steps_alt))
        
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # === 2. SARGI (TOP SATIN) ===
        # Maksimum dikiş uzunluğu (iğne kırılmasın): 7mm = 70 birim
        MAX_DIKIŞ = 70
        
        # Eğer genişlik çok fazlaysa, iğne kırılmasın diye adım sayısını artır
        if genislik > MAX_DIKIŞ:
            ara_adim = int(math.ceil(genislik / MAX_DIKIŞ))
        else:
            ara_adim = 1

        YOGUNLUK = 3
        steps_sargi = int(dist // YOGUNLUK)
        if steps_sargi < 2:
            steps_sargi = 2

        for i in range(steps_sargi + 1):
            ratio = i / steps_sargi
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

    def _kavis_ciz(self, cx, cy, r, baslangic_aci, bitis_aci, scale, adim=12):
        """Yay (arc) noktaları üretir. Açılar derece cinsindendir."""
        noktalar = []
        for i in range(adim + 1):
            t = i / adim
            aci = math.radians(baslangic_aci + (bitis_aci - baslangic_aci) * t)
            x = cx + r * math.cos(aci)
            y = cy + r * math.sin(aci)
            noktalar.append((x, y))
        return noktalar

    def _kavis_cizgiler(self, cx, cy, r, baslangic_aci, bitis_aci, scale, adim=12):
        """Kavisten çizgi segmentleri döndürür."""
        noktalar = self._kavis_ciz(cx, cy, r, baslangic_aci, bitis_aci, scale, adim)
        cizgiler = []
        for i in range(len(noktalar) - 1):
            cizgiler.append((noktalar[i][0], noktalar[i][1], noktalar[i+1][0], noktalar[i+1][1]))
        return cizgiler

    def isim_yaz(self, metin, baslangic_x, baslangic_y, boyut_cm, birim="cm"):
        """
        metin: Yazılacak metin
        baslangic_x, baslangic_y: Başlangıç koordinatları (birim cinsinden)
        boyut_cm: Harf boyutu
        birim: "cm" veya "mm" (varsayılan cm)
        """
        if birim == "cm":
            harf_boyu_mm = boyut_cm * 10
        elif birim == "mm":
            harf_boyu_mm = boyut_cm
        else:
            harf_boyu_mm = boyut_cm * 10

        # Başlangıç koordinatlarını da birime göre çevir
        if birim == "cm":
            bx = baslangic_x * 100  # cm -> nakış birimi (1cm = 100 birim)
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

        # Büyük harf genişlik çarpanı
        bh_gen = 0.7
        # Küçük harf yükseklik (scale'in %60'ı)
        kh_yuk = 0.6
        # Küçük harf genişlik çarpanı
        kh_gen = 0.55
        # Sayı genişlik çarpanı
        sy_gen = 0.65

        # --- BÜYÜK HARFLER ---
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

        # --- KÜÇÜK HARFLER ---
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

        # --- SAYILAR ---
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

        # --- TÜRKÇE KARAKTERLER (BÜYÜK) ---
        turkce_buyuk = {
            'Ç': buyuk_harfler['C'] + [(0.35,-0.15, 0.5,-0.3), (0.5,-0.3, 0.65,-0.15)],
            'Ğ': buyuk_harfler['G'] + [(0.3,1.1, 0.5,1.2), (0.5,1.2, 0.7,1.1)],
            'İ': [(0.5,0, 0.5,1), (0.5,1.1, 0.5,1.15)],
            'Ö': buyuk_harfler['O'] + [(0.3,1.1, 0.3,1.18), (0.7,1.1, 0.7,1.18)],
            'Ş': buyuk_harfler['S'] + [(0.35,-0.15, 0.5,-0.3), (0.5,-0.3, 0.65,-0.15)],
            'Ü': buyuk_harfler['U'] + [(0.3,1.1, 0.3,1.18), (0.7,1.1, 0.7,1.18)],
        }

        # --- TÜRKÇE KARAKTERLER (KÜÇÜK) ---
        turkce_kucuk = {
            'ç': kucuk_harfler['c'] + [(0.3,-0.12, 0.45,-0.25), (0.45,-0.25, 0.6,-0.12)],
            'ğ': kucuk_harfler['g'] + [(0.25,0.7, 0.45,0.8), (0.45,0.8, 0.65,0.7)],
            'ı': [(0.4,0, 0.4,0.6)],
            'ö': kucuk_harfler['o'] + [(0.25,0.72, 0.25,0.78), (0.6,0.72, 0.6,0.78)],
            'ş': kucuk_harfler['s'] + [(0.3,-0.12, 0.45,-0.25), (0.45,-0.25, 0.6,-0.12)],
            'ü': kucuk_harfler['u'] + [(0.25,0.72, 0.25,0.78), (0.6,0.72, 0.6,0.78)],
        }

        # --- ÖZEL KARAKTERLER ---
        ozel = {
            ' ': [],
            '-': [(0.1,0.5, 0.9,0.5)],
            '.': [(0.4,0, 0.4,0.05), (0.4,0.05, 0.45,0.05), (0.45,0.05, 0.45,0), (0.45,0, 0.4,0)],
            ',': [(0.4,0.05, 0.35,-0.15)],
            '!': [(0.45,0.25, 0.45,1), (0.45,0, 0.45,0.08)],
            '?': [(0,0.85, 0.15,1), (0.15,1, 0.75,1), (0.75,1, 0.9,0.85), (0.9,0.85, 0.9,0.6), (0.9,0.6, 0.5,0.4), (0.5,0.4, 0.5,0.25), (0.5,0, 0.5,0.08)],
            '/': [(0,0, 1,1)],
            ':': [(0.45,0.15, 0.45,0.22), (0.45,0.45, 0.45,0.52)],
            '@': [(0.7,0.3, 0.55,0.3), (0.55,0.3, 0.45,0.4), (0.45,0.4, 0.45,0.55), (0.45,0.55, 0.55,0.65), (0.55,0.65, 0.7,0.65), (0.7,0.65, 0.8,0.55), (0.8,0.55, 0.8,0.3), (0.8,0.15, 0.65,0), (0.65,0, 0.25,0), (0.25,0, 0.05,0.2), (0.05,0.2, 0.05,0.8), (0.05,0.8, 0.25,1), (0.25,1, 0.75,1), (0.75,1, 0.95,0.8)],
            '#': [(0.3,0, 0.3,1), (0.7,0, 0.7,1), (0.05,0.35, 0.95,0.35), (0.05,0.65, 0.95,0.65)],
        }

        sargi_kalinligi = harf_boyu_mm * 0.12
        if sargi_kalinligi < 2.0:
            sargi_kalinligi = 2.0
        if sargi_kalinligi > 5.0:
            sargi_kalinligi = 5.0

        for harf in metin:
            if harf == " ":
                mevcut_x += scale * 0.5
                continue

            # Hangi sette olduğunu bul
            cizgiler = None
            gen_carpan = bh_gen
            yuk_carpan = 1.0
            y_offset = 0

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
                # Bilinmeyen karakter, atla
                mevcut_x += scale * 0.3
                continue

            if cizgiler is None or len(cizgiler) == 0:
                mevcut_x += scale * 0.3
                continue

            for (lx1, ly1, lx2, ly2) in cizgiler:
                gx1 = mevcut_x + (lx1 * scale * gen_carpan)
                gy1 = by + (ly1 * scale * yuk_carpan)
                gx2 = mevcut_x + (lx2 * scale * gen_carpan)
                gy2 = by + (ly2 * scale * yuk_carpan)
                self.tam_sargi_yap(gx1, gy1, gx2, gy2, sargi_kalinligi)

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
    
    MUSTERI_ISMI = "Mehmet Öz 2025"   # Büyük/küçük harf, Türkçe karakter, sayı hepsi desteklenir
    BOYUT = 2.5                        # Harf boyutu
    BIRIM = "cm"                       # "cm" veya "mm"
    
    # ========================================
    
    # Otomatik ortalama hesabı
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
