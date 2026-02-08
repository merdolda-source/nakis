#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profesyonel Nakış Yazı Makinesi v6
- Metin: 1 JUMP → Underlay ileri → Sargı geri → 1 TRIM
- Harf içinde sıfır atlama, sıfır duraksama
- Alana sığdırma, ayarlanabilir harf aralığı, Normal / Bold / Italic
- YENİ: logo.png gibi raster görselleri kontur bazlı running stitch ile alana sığdırıp dikme
"""

import math
import pyembroidery
import matplotlib.pyplot as plt

import numpy as np
from PIL import Image
try:
    import cv2
except ImportError as e:
    raise ImportError(
        "OpenCV bulunamadı. Lütfen kurun: pip install opencv-python-headless"
    ) from e


class ProfesyonelNakis:

    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()

    # ── Yardımcılar ──────────────────────────────────────────────

    def _mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def _running(self, x1, y1, x2, y2, adim=30):
        """İki nokta arası düz running stitch — makine hiç duraksamaz"""
        d = self._mesafe(x1, y1, x2, y2)
        if d < 1:
            return (x2, y2)
        n = max(1, int(d / adim))
        for i in range(1, n + 1):
            t = i / n
            self.pattern.add_stitch_absolute(
                pyembroidery.STITCH,
                int(x1 + (x2 - x1) * t),
                int(y1 + (y2 - y1) * t),
            )
        return (x2, y2)

    def _satin(self, x1, y1, x2, y2, kalinlik_mm):
        """Segment boyunca satin zigzag sargı — sadece STITCH üretir"""
        gen = kalinlik_mm * 10
        dx, dy = x2 - x1, y2 - y1
        d = self._mesafe(x1, y1, x2, y2)
        if d < 1:
            return (x2, y2)
        nx = -dy / d * (gen / 2)
        ny = dx / d * (gen / 2)
        steps = max(2, int(d / 2.0))
        for i in range(steps + 1):
            t = i / steps
            cx = x1 + dx * t
            cy = y1 + dy * t
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(
                    pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(
                    pyembroidery.STITCH, int(cx - nx), int(cy - ny))
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))
        return (x2, y2)

    def _italic_donustur(self, cizgiler, egim=0.25):
        """Çizgileri italic (eğik) yapar - x += y * egim"""
        italic_cizgiler = []
        for a, b, c, d in cizgiler:
            a_new = a + b * egim
            c_new = c + d * egim
            italic_cizgiler.append((a_new, b, c_new, d))
        return italic_cizgiler

    def _resample_polyline(self, pts, step):
        """Polylini yaklaşık eşit aralıklı noktalarla örnekle"""
        if len(pts) < 2:
            return pts
        res = [pts[0]]
        acc = 0.0
        for i in range(1, len(pts)):
            x0, y0 = pts[i-1]
            x1, y1 = pts[i]
            seg_len = self._mesafe(x0, y0, x1, y1)
            if seg_len < 1e-6:
                continue
            dirx = (x1 - x0) / seg_len
            diry = (y1 - y0) / seg_len
            dist = seg_len
            while acc + dist >= step:
                need = step - acc
                nx = x0 + dirx * need
                ny = y0 + diry * need
                res.append((nx, ny))
                dist -= need
                x0, y0 = nx, ny
                acc = 0.0
            acc += dist
        if self._mesafe(res[-1][0], res[-1][1], pts[-1][0], pts[-1][1]) > 1e-3:
            res.append(pts[-1])
        return res

    # ── Harf Dikme ───────────────────────────────────────────────

    def _harf_dik(self, cizgiler, mx, by, scale, gx, yx, kalinlik):
        """
        JUMP → underlay ileri → sargı geri → TRIM
        Tek seferde biter, harf içinde 0 atlama
        """
        if not cizgiler:
            return

        segs = [
            (mx + a * scale * gx, by + b * scale * yx,
             mx + c * scale * gx, by + d * scale * yx)
            for a, b, c, d in cizgiler
        ]

        # 1) JUMP: ilk noktaya atla
        self.pattern.add_stitch_absolute(
            pyembroidery.JUMP, int(segs[0][0]), int(segs[0][1]))
        cx, cy = segs[0][0], segs[0][1]

        # 2) UNDERLAY: tüm segmentleri ileriye running stitch
        for sx, sy, ex, ey in segs:
            if self._mesafe(cx, cy, sx, sy) > 1:
                cx, cy = self._running(cx, cy, sx, sy)
            cx, cy = self._running(sx, sy, ex, ey)

        # 3) SARGI: ters sırada satin
        for sx, sy, ex, ey in reversed(segs):
            if self._mesafe(cx, cy, ex, ey) > 1:
                cx, cy = self._running(cx, cy, ex, ey)
            cx, cy = self._satin(ex, ey, sx, sy, kalinlik)

        # 4) TRIM
        self.pattern.add_stitch_absolute(
            pyembroidery.TRIM, int(cx), int(cy))

    # ── Metin Boyutları ──────────────────────────────────────────

    def _metin_boyut_hesapla(self, metin, harf_araligi_oran, italic=False):
        BG, KG, KY, SG = 0.70, 0.55, 0.60, 0.65

        buyuk_harfler = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        kucuk_harfler = set('abcdefghijklmnopqrstuvwxyz')
        tr_buyuk = set('ÇĞİÖŞÜ')
        tr_kucuk = set('çğıöşü')
        sayilar_set = set('0123456789')
        ozel_set = set('-.,!?/:#')

        toplam_genislik = 0
        max_yukseklik = 1.0
        min_y = 0
        max_y = 1.0
        harf_sayisi = 0

        for i, harf in enumerate(metin):
            if harf == ' ':
                toplam_genislik += 0.5
                continue

            gx = 0
            if harf in buyuk_harfler or harf in tr_buyuk:
                gx = BG
                max_y = max(max_y, 1.0)
                if harf in 'ĞİÖÜ':
                    max_y = max(max_y, 1.2)
                if harf in 'ÇŞ':
                    min_y = min(min_y, -0.3)
            elif harf in kucuk_harfler or harf in tr_kucuk:
                gx = KG
                if harf in 'gjyçğ':
                    min_y = min(min_y, -0.35)
                if harf in 'bdfhiklt':
                    max_y = max(max_y, 1.0)
                else:
                    max_y = max(max_y, 0.6)
                if harf in 'öü':
                    max_y = max(max_y, 0.78)
            elif harf in sayilar_set:
                gx = SG
            elif harf in ozel_set:
                gx = 0.5
                if harf == '!':
                    max_y = max(max_y, 1.0)
            else:
                gx = 0.3

            toplam_genislik += gx
            harf_sayisi += 1

        if harf_sayisi > 1:
            toplam_genislik += harf_araligi_oran * (harf_sayisi - 1)

        if italic:
            italic_ekstra = max_y * 0.25
            toplam_genislik += italic_ekstra

        toplam_yukseklik = max_y - min_y
        return toplam_genislik, toplam_yukseklik, min_y

    # ── Metin Yazma (Alana Sığdırma) ─────────────────────────────

    def isim_yaz(self, metin, baslangic_x, baslangic_y, boyut=None, birim="cm",
                 genislik=None, yukseklik=None, harf_araligi=None,
                 normal=True, bold=False, italic=False):

        if birim == "cm":
            birim_carpan = 100
        elif birim == "mm":
            birim_carpan = 10
        else:
            birim_carpan = 100

        bx = baslangic_x * birim_carpan
        by = baslangic_y * birim_carpan

        if bold:
            kalinlik_carpan = 1.8
        else:
            kalinlik_carpan = 1.0

        if genislik is not None and yukseklik is not None:
            gecici_olcek = min(genislik, yukseklik) * birim_carpan
        elif boyut is not None:
            gecici_olcek = boyut * (10 if birim == "cm" else 1) * 10
        else:
            gecici_olcek = 200

        if harf_araligi is not None:
            harf_araligi_px = harf_araligi * birim_carpan
            harf_araligi_oran = harf_araligi_px / gecici_olcek if gecici_olcek > 0 else 0.25
        else:
            harf_araligi_oran = 0.25

        metin_gen_oran, metin_yuk_oran, min_y_oran = self._metin_boyut_hesapla(
            metin, harf_araligi_oran, italic)

        if genislik is not None and yukseklik is not None:
            gen_px = genislik * birim_carpan
            yuk_px = yukseklik * birim_carpan

            olcek_gen = gen_px / metin_gen_oran if metin_gen_oran > 0 else gen_px
            olcek_yuk = yuk_px / metin_yuk_oran if metin_yuk_oran > 0 else yuk_px

            sc = min(olcek_gen, olcek_yuk)

            if harf_araligi is not None:
                ara = harf_araligi * birim_carpan
            else:
                ara = sc * 0.25

            gercek_gen = metin_gen_oran * sc
            gercek_yuk = metin_yuk_oran * sc

            x_offset = (gen_px - gercek_gen) / 2
            bx += x_offset

            y_offset = (yuk_px - gercek_yuk) / 2 - (min_y_oran * sc)
            by += y_offset

            harf_mm = sc / 10

            print(f"  📐 Alan: {genislik}x{yukseklik} {birim}")
            print(f"  📏 Hesaplanan ölçek: {sc/birim_carpan:.2f} {birim}")
            print(f"  📦 Gerçek boyut: {gercek_gen/birim_carpan:.2f}x{gercek_yuk/birim_carpan:.2f} {birim}")
            print(f"  📝 Harf aralığı: {ara/birim_carpan:.2f} {birim}")
            yazi_tipi = []
            if bold:
                yazi_tipi.append("Bold")
            if italic:
                yazi_tipi.append("Italic")
            if not yazi_tipi:
                yazi_tipi.append("Normal")
            print(f"  🔤 Yazı tipi: {' + '.join(yazi_tipi)}")

        elif boyut is not None:
            harf_mm = boyut * (10 if birim == "cm" else 1)
            sc = harf_mm * 10
            if harf_araligi is not None:
                ara = harf_araligi * birim_carpan
            else:
                ara = sc * 0.25
        else:
            harf_mm = 20
            sc = harf_mm * 10
            if harf_araligi is not None:
                ara = harf_araligi * birim_carpan
            else:
                ara = sc * 0.25

        mx = bx
        BG, KG, KY, SG = 0.70, 0.55, 0.60, 0.65

        # ── Harf şekilleri (aynı sözlükler) ──
        buyuk = {
            'A': [(0, 0, 0.5, 1), (0.5, 1, 1, 0), (0.2, 0.4, 0.8, 0.4)],
            'B': [(0, 0, 0, 1), (0, 1, 0.7, 1), (0.7, 1, 0.7, 0.55),
                  (0.7, 0.55, 0, 0.55), (0, 0.55, 0.75, 0.55),
                  (0.75, 0.55, 0.75, 0), (0.75, 0, 0, 0)],
            'C': [(1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1), (0.15, 1, 0, 0.85),
                  (0, 0.85, 0, 0.15), (0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0),
                  (0.85, 0, 1, 0.15)],
            'D': [(0, 0, 0, 1), (0, 1, 0.6, 1), (0.6, 1, 1, 0.7),
                  (1, 0.7, 1, 0.3), (1, 0.3, 0.6, 0), (0.6, 0, 0, 0)],
            'E': [(1, 1, 0, 1), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0.5, 0.8, 0.5)],
            'F': [(0.9, 1, 0, 1), (0, 1, 0, 0), (0, 0.5, 0.7, 0.5)],
            'G': [(1, 1, 0.15, 1), (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.15),
                  (0, 0.15, 0.15, 0), (0.15, 0, 1, 0), (1, 0, 1, 0.5),
                  (1, 0.5, 0.5, 0.5)],
            'H': [(0, 0, 0, 1), (0, 1, 0, 0.5), (0, 0.5, 1, 0.5),
                  (1, 0.5, 1, 0), (1, 0, 1, 1)],
            'I': [(0.5, 0, 0.5, 1)],
            'J': [(0.7, 1, 0.7, 0.2), (0.7, 0.2, 0.5, 0), (0.5, 0, 0.2, 0),
                  (0.2, 0, 0, 0.2)],
            'K': [(0, 0, 0, 1), (0, 1, 0, 0.45), (0, 0.45, 0.9, 1),
                  (0.9, 1, 0, 0.45), (0, 0.45, 0.9, 0)],
            'L': [(0, 1, 0, 0), (0, 0, 0.8, 0)],
            'M': [(0, 0, 0, 1), (0, 1, 0.5, 0.3), (0.5, 0.3, 1, 1), (1, 1, 1, 0)],
            'N': [(0, 0, 0, 1), (0, 1, 1, 0), (1, 0, 1, 1)],
            'O': [(0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0), (0.85, 0, 1, 0.15),
                  (1, 0.15, 1, 0.85), (1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1),
                  (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.15)],
            'P': [(0, 0, 0, 1), (0, 1, 0.75, 1), (0.75, 1, 0.75, 0.5),
                  (0.75, 0.5, 0, 0.5)],
            'Q': [(0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0), (0.85, 0, 1, 0.15),
                  (1, 0.15, 1, 0.85), (1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1),
                  (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.15), (0.7, 0.3, 1.05, 0)],
            'R': [(0, 0, 0, 1), (0, 1, 0.75, 1), (0.75, 1, 0.75, 0.5),
                  (0.75, 0.5, 0, 0.5), (0, 0.5, 0.45, 0.5), (0.45, 0.5, 0.9, 0)],
            'S': [(1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1), (0.15, 1, 0, 0.85),
                  (0, 0.85, 0, 0.55), (0, 0.55, 0.15, 0.5), (0.15, 0.5, 0.85, 0.5),
                  (0.85, 0.5, 1, 0.45), (1, 0.45, 1, 0.15), (1, 0.15, 0.85, 0),
                  (0.85, 0, 0.15, 0), (0.15, 0, 0, 0.15)],
            'T': [(0, 1, 0.5, 1), (0.5, 1, 1, 1), (1, 1, 0.5, 1), (0.5, 1, 0.5, 0)],
            'U': [(0, 1, 0, 0.15), (0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0),
                  (0.85, 0, 1, 0.15), (1, 0.15, 1, 1)],
            'V': [(0, 1, 0.5, 0), (0.5, 0, 1, 1)],
            'W': [(0, 1, 0.25, 0), (0.25, 0, 0.5, 0.6), (0.5, 0.6, 0.75, 0),
                  (0.75, 0, 1, 1)],
            'X': [(0, 0, 0.5, 0.5), (0.5, 0.5, 1, 1), (1, 1, 0.5, 0.5),
                  (0.5, 0.5, 0, 1), (0, 1, 0.5, 0.5), (0.5, 0.5, 1, 0)],
            'Y': [(0, 1, 0.5, 0.5), (0.5, 0.5, 1, 1), (1, 1, 0.5, 0.5),
                  (0.5, 0.5, 0.5, 0)],
            'Z': [(0, 1, 1, 1), (1, 1, 0, 0), (0, 0, 1, 0)],
        }

        kucuk = {
            'a': [(0.85, 0.6, 0.85, 0), (0.85, 0, 0.2, 0), (0.2, 0, 0, 0.2),
                  (0, 0.2, 0, 0.45), (0, 0.45, 0.2, 0.6), (0.2, 0.6, 0.65, 0.6),
                  (0.65, 0.6, 0.85, 0.5)],
            'b': [(0, 0, 0, 1), (0, 1, 0, 0.5), (0, 0.5, 0.2, 0.6),
                  (0.2, 0.6, 0.7, 0.6), (0.7, 0.6, 0.85, 0.45),
                  (0.85, 0.45, 0.85, 0.15), (0.85, 0.15, 0.7, 0), (0.7, 0, 0, 0)],
            'c': [(0.85, 0.6, 0.2, 0.6), (0.2, 0.6, 0, 0.45), (0, 0.45, 0, 0.15),
                  (0, 0.15, 0.2, 0), (0.2, 0, 0.85, 0)],
            'd': [(0.85, 0, 0.85, 1), (0.85, 1, 0.85, 0.5), (0.85, 0.5, 0.65, 0.6),
                  (0.65, 0.6, 0.2, 0.6), (0.2, 0.6, 0, 0.45), (0, 0.45, 0, 0.15),
                  (0, 0.15, 0.2, 0), (0.2, 0, 0.85, 0)],
            'e': [(0, 0.35, 0.85, 0.35), (0.85, 0.35, 0.85, 0.45),
                  (0.85, 0.45, 0.65, 0.6), (0.65, 0.6, 0.2, 0.6),
                  (0.2, 0.6, 0, 0.45), (0, 0.45, 0, 0.15),
                  (0, 0.15, 0.2, 0), (0.2, 0, 0.85, 0)],
            'f': [(0.65, 1, 0.35, 1), (0.35, 1, 0.2, 0.85), (0.2, 0.85, 0.2, 0.6),
                  (0.2, 0.6, 0, 0.6), (0, 0.6, 0.55, 0.6), (0.55, 0.6, 0.2, 0.6),
                  (0.2, 0.6, 0.2, 0)],
            'g': [(0.85, 0.6, 0.2, 0.6), (0.2, 0.6, 0, 0.45), (0, 0.45, 0, 0.2),
                  (0, 0.2, 0.2, 0.05), (0.2, 0.05, 0.85, 0.05),
                  (0.85, 0.05, 0.85, 0.6), (0.85, 0.6, 0.85, -0.2),
                  (0.85, -0.2, 0.65, -0.35), (0.65, -0.35, 0.15, -0.35)],
            'h': [(0, 0, 0, 1), (0, 1, 0, 0.5), (0, 0.5, 0.25, 0.6),
                  (0.25, 0.6, 0.65, 0.6), (0.65, 0.6, 0.85, 0.5),
                  (0.85, 0.5, 0.85, 0)],
            'i': [(0.4, 0, 0.4, 0.6), (0.4, 0.6, 0.4, 0.8),
                  (0.4, 0.8, 0.4, 0.85)],
            'j': [(0.5, 0.8, 0.5, 0.85), (0.5, 0.85, 0.5, 0.6),
                  (0.5, 0.6, 0.5, -0.15), (0.5, -0.15, 0.3, -0.35),
                  (0.3, -0.35, 0.05, -0.35)],
            'k': [(0, 0, 0, 1), (0, 1, 0, 0.25), (0, 0.25, 0.75, 0.6),
                  (0.75, 0.6, 0, 0.25), (0, 0.25, 0.75, 0)],
            'l': [(0.4, 0, 0.4, 1)],
            'm': [(0, 0, 0, 0.6), (0, 0.6, 0, 0.5), (0, 0.5, 0.15, 0.6),
                  (0.15, 0.6, 0.35, 0.6), (0.35, 0.6, 0.5, 0.5),
                  (0.5, 0.5, 0.5, 0), (0.5, 0, 0.5, 0.5),
                  (0.5, 0.5, 0.65, 0.6), (0.65, 0.6, 0.85, 0.6),
                  (0.85, 0.6, 1, 0.5), (1, 0.5, 1, 0)],
            'n': [(0, 0, 0, 0.6), (0, 0.6, 0, 0.5), (0, 0.5, 0.25, 0.6),
                  (0.25, 0.6, 0.65, 0.6), (0.65, 0.6, 0.85, 0.5),
                  (0.85, 0.5, 0.85, 0)],
            'o': [(0.2, 0, 0, 0.15), (0, 0.15, 0, 0.45), (0, 0.45, 0.2, 0.6),
                  (0.2, 0.6, 0.65, 0.6), (0.65, 0.6, 0.85, 0.45),
                  (0.85, 0.45, 0.85, 0.15), (0.85, 0.15, 0.65, 0),
                  (0.65, 0, 0.2, 0)],
            'p': [(0, 0, 0, 0.6), (0, 0.6, 0, 0.5), (0, 0.5, 0.2, 0.6),
                  (0.2, 0.6, 0.7, 0.6), (0.7, 0.6, 0.85, 0.45),
                  (0.85, 0.45, 0.85, 0.15), (0.85, 0.15, 0.7, 0),
                  (0.7, 0, 0, 0), (0, 0, 0, -0.35)],
            'q': [(0.85, 0, 0.85, 0.6), (0.85, 0.6, 0.85, 0.5),
                  (0.85, 0.5, 0.65, 0.6), (0.65, 0.6, 0.2, 0.6),
                  (0.2, 0.6, 0, 0.45), (0, 0.45, 0, 0.15),
                  (0, 0.15, 0.2, 0), (0.2, 0, 0.85, 0),
                  (0.85, 0, 0.85, -0.35)],
            'r': [(0, 0, 0, 0.6), (0, 0.6, 0, 0.45), (0, 0.45, 0.2, 0.6),
                  (0.2, 0.6, 0.6, 0.6), (0.6, 0.6, 0.8, 0.5)],
            's': [(0.8, 0.55, 0.6, 0.6), (0.6, 0.6, 0.2, 0.6),
                  (0.2, 0.6, 0, 0.5), (0, 0.5, 0, 0.38),
                  (0, 0.38, 0.15, 0.32), (0.15, 0.32, 0.7, 0.32),
                  (0.7, 0.32, 0.85, 0.22), (0.85, 0.22, 0.85, 0.1),
                  (0.85, 0.1, 0.65, 0), (0.65, 0, 0.2, 0), (0.2, 0, 0, 0.05)],
            't': [(0.25, 0, 0.25, 0.6), (0.25, 0.6, 0, 0.6), (0, 0.6, 0.6, 0.6),
                  (0.6, 0.6, 0.25, 0.6), (0.25, 0.6, 0.25, 0.9)],
            'u': [(0, 0.6, 0, 0.15), (0, 0.15, 0.2, 0), (0.2, 0, 0.65, 0),
                  (0.65, 0, 0.85, 0.1), (0.85, 0.1, 0.85, 0.6),
                  (0.85, 0.6, 0.85, 0), (0.85, 0, 0.85, 0)],
            'v': [(0, 0.6, 0.45, 0), (0.45, 0, 0.9, 0.6)],
            'w': [(0, 0.6, 0.2, 0), (0.2, 0, 0.45, 0.4), (0.45, 0.4, 0.7, 0),
                  (0.7, 0, 0.9, 0.6)],
            'x': [(0, 0, 0.425, 0.3), (0.425, 0.3, 0.85, 0.6),
                  (0.85, 0.6, 0.425, 0.3), (0.425, 0.3, 0, 0.6),
                  (0, 0.6, 0.425, 0.3), (0.425, 0.3, 0.85, 0)],
            'y': [(0, 0.6, 0.45, 0), (0.45, 0, 0.9, 0.6),
                  (0.9, 0.6, 0.45, 0), (0.45, 0, 0.2, -0.35)],
            'z': [(0, 0.6, 0.85, 0.6), (0.85, 0.6, 0, 0), (0, 0, 0.85, 0)],
        }

        sayilar = {
            '0': [(0.15, 0, 0, 0.15), (0, 0.15, 0, 0.85), (0, 0.85, 0.15, 1),
                  (0.15, 1, 0.75, 1), (0.75, 1, 0.9, 0.85), (0.9, 0.85, 0.9, 0.15),
                  (0.9, 0.15, 0.75, 0), (0.75, 0, 0.15, 0)],
            '1': [(0.2, 0.8, 0.5, 1), (0.5, 1, 0.5, 0), (0.5, 0, 0.2, 0),
                  (0.2, 0, 0.8, 0)],
            '2': [(0, 0.85, 0.15, 1), (0.15, 1, 0.75, 1), (0.75, 1, 0.9, 0.85),
                  (0.9, 0.85, 0.9, 0.6), (0.9, 0.6, 0.75, 0.5),
                  (0.75, 0.5, 0, 0), (0, 0, 0.9, 0)],
            '3': [(0, 0.85, 0.15, 1), (0.15, 1, 0.75, 1), (0.75, 1, 0.9, 0.85),
                  (0.9, 0.85, 0.9, 0.6), (0.9, 0.6, 0.75, 0.5),
                  (0.75, 0.5, 0.4, 0.5), (0.4, 0.5, 0.75, 0.5),
                  (0.75, 0.5, 0.9, 0.4), (0.9, 0.4, 0.9, 0.15),
                  (0.9, 0.15, 0.75, 0), (0.75, 0, 0.15, 0), (0.15, 0, 0, 0.15)],
            '4': [(0.7, 0, 0.7, 1), (0.7, 1, 0, 0.35), (0, 0.35, 0.9, 0.35)],
            '5': [(0.9, 1, 0, 1), (0, 1, 0, 0.55), (0, 0.55, 0.7, 0.55),
                  (0.7, 0.55, 0.9, 0.4), (0.9, 0.4, 0.9, 0.15),
                  (0.9, 0.15, 0.75, 0), (0.75, 0, 0.15, 0), (0.15, 0, 0, 0.15)],
            '6': [(0.8, 0.9, 0.6, 1), (0.6, 1, 0.2, 1), (0.2, 1, 0, 0.85),
                  (0, 0.85, 0, 0.15), (0, 0.15, 0.15, 0), (0.15, 0, 0.75, 0),
                  (0.75, 0, 0.9, 0.15), (0.9, 0.15, 0.9, 0.4),
                  (0.9, 0.4, 0.75, 0.55), (0.75, 0.55, 0.15, 0.55),
                  (0.15, 0.55, 0, 0.4)],
            '7': [(0, 1, 0.9, 1), (0.9, 1, 0.35, 0)],
            '8': [(0.15, 0.5, 0, 0.4), (0, 0.4, 0, 0.15), (0, 0.15, 0.15, 0),
                  (0.15, 0, 0.75, 0), (0.75, 0, 0.9, 0.15),
                  (0.9, 0.15, 0.9, 0.4), (0.9, 0.4, 0.75, 0.5),
                  (0.75, 0.5, 0.15, 0.5), (0.15, 0.5, 0, 0.6),
                  (0, 0.6, 0, 0.85), (0, 0.85, 0.15, 1), (0.15, 1, 0.75, 1),
                  (0.75, 1, 0.9, 0.85), (0.9, 0.85, 0.9, 0.6),
                  (0.9, 0.6, 0.75, 0.5)],
            '9': [(0.1, 0.1, 0.3, 0), (0.3, 0, 0.7, 0), (0.7, 0, 0.9, 0.15),
                  (0.9, 0.15, 0.9, 0.85), (0.9, 0.85, 0.75, 1),
                  (0.75, 1, 0.15, 1), (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.6),
                  (0, 0.6, 0.15, 0.45), (0.15, 0.45, 0.75, 0.45),
                  (0.75, 0.45, 0.9, 0.6)],
        }

        tr_b = {
            'Ç': [(1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1), (0.15, 1, 0, 0.85),
                  (0, 0.85, 0, 0.15), (0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0),
                  (0.85, 0, 1, 0.15), (1, 0.15, 0.5, 0.15),
                  (0.5, 0.15, 0.5, -0.05), (0.5, -0.05, 0.35, -0.15),
                  (0.35, -0.15, 0.5, -0.3), (0.5, -0.3, 0.65, -0.15)],
            'Ğ': [(1, 1, 0.15, 1), (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.15),
                  (0, 0.15, 0.15, 0), (0.15, 0, 1, 0), (1, 0, 1, 0.5),
                  (1, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 1),
                  (0.5, 1, 0.3, 1.1), (0.3, 1.1, 0.5, 1.2),
                  (0.5, 1.2, 0.7, 1.1)],
            'İ': [(0.5, 0, 0.5, 1), (0.5, 1, 0.5, 1.1), (0.5, 1.1, 0.5, 1.15)],
            'Ö': [(0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0), (0.85, 0, 1, 0.15),
                  (1, 0.15, 1, 0.85), (1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1),
                  (0.15, 1, 0, 0.85), (0, 0.85, 0, 0.15),
                  (0, 0.15, 0.3, 0.15), (0.3, 0.15, 0.3, 1.1),
                  (0.3, 1.1, 0.3, 1.18), (0.3, 1.18, 0.7, 1.18),
                  (0.7, 1.18, 0.7, 1.1)],
            'Ş': [(1, 0.85, 0.85, 1), (0.85, 1, 0.15, 1), (0.15, 1, 0, 0.85),
                  (0, 0.85, 0, 0.55), (0, 0.55, 0.15, 0.5),
                  (0.15, 0.5, 0.85, 0.5), (0.85, 0.5, 1, 0.45),
                  (1, 0.45, 1, 0.15), (1, 0.15, 0.85, 0), (0.85, 0, 0.15, 0),
                  (0.15, 0, 0, 0.15), (0, 0.15, 0.5, 0.15),
                  (0.5, 0.15, 0.5, -0.05), (0.5, -0.05, 0.35, -0.15),
                  (0.35, -0.15, 0.5, -0.3), (0.5, -0.3, 0.65, -0.15)],
            'Ü': [(0, 1, 0, 0.15), (0, 0.15, 0.15, 0), (0.15, 0, 0.85, 0),
                  (0.85, 0, 1, 0.15), (1, 0.15, 1, 1),
                  (1, 1, 0.7, 1), (0.7, 1, 0.7, 1.1), (0.7, 1.1, 0.7, 1.18),
                  (0.7, 1.18, 0.3, 1.18), (0.3, 1.18, 0.3, 1.1)],
        }

        tr_k = {
            'ç': [(0.85, 0.6, 0.2, 0.6), (0.2, 0.6, 0, 0.45),
                  (0, 0.45, 0, 0.15), (0, 0.15, 0.2, 0), (0.2, 0, 0.85, 0),
                  (0.85, 0, 0.45, 0), (0.45, 0, 0.45, -0.05),
                  (0.45, -0.05, 0.3, -0.12), (0.3, -0.12, 0.45, -0.25),
                  (0.45, -0.25, 0.6, -0.12)],
            'ğ': [(0.85, 0.6, 0.2, 0.6), (0.2, 0.6, 0, 0.45),
                  (0, 0.45, 0, 0.2), (0, 0.2, 0.2, 0.05),
                  (0.2, 0.05, 0.85, 0.05), (0.85, 0.05, 0.85, 0.6),
                  (0.85, 0.6, 0.85, -0.2), (0.85, -0.2, 0.65, -0.35),
                  (0.65, -0.35, 0.15, -0.35), (0.15, -0.35, 0.45, -0.35),
                  (0.45, -0.35, 0.45, 0.6), (0.45, 0.6, 0.25, 0.7),
                  (0.25, 0.7, 0.45, 0.8), (0.45, 0.8, 0.65, 0.7)],
            'ı': [(0.4, 0, 0.4, 0.6)],
            'ö': [(0.2, 0, 0, 0.15), (0, 0.15, 0, 0.45), (0, 0.45, 0.2, 0.6),
                  (0.2, 0.6, 0.65, 0.6), (0.65, 0.6, 0.85, 0.45),
                  (0.85, 0.45, 0.85, 0.15), (0.85, 0.15, 0.65, 0),
                  (0.65, 0, 0.2, 0), (0.2, 0, 0.25, 0),
                  (0.25, 0, 0.25, 0.72), (0.25, 0.72, 0.25, 0.78),
                  (0.25, 0.78, 0.6, 0.78), (0.6, 0.78, 0.6, 0.72)],
            'ş': [(0.8, 0.55, 0.6, 0.6), (0.6, 0.6, 0.2, 0.6),
                  (0.2, 0.6, 0, 0.5), (0, 0.5, 0, 0.38),
                  (0, 0.38, 0.15, 0.32), (0.15, 0.32, 0.7, 0.32),
                  (0.7, 0.32, 0.85, 0.22), (0.85, 0.22, 0.85, 0.1),
                  (0.85, 0.1, 0.65, 0), (0.65, 0, 0.2, 0), (0.2, 0, 0, 0.05),
                  (0, 0.05, 0.45, 0.05), (0.45, 0.05, 0.45, -0.05),
                  (0.45, -0.05, 0.3, -0.12), (0.3, -0.12, 0.45, -0.25),
                  (0.45, -0.25, 0.6, -0.12)],
            'ü': [(0, 0.6, 0, 0.15), (0, 0.15, 0.2, 0), (0.2, 0, 0.65, 0),
                  (0.65, 0, 0.85, 0.1), (0.85, 0.1, 0.85, 0.6),
                  (0.85, 0.6, 0.85, 0), (0.85, 0, 0.6, 0),
                  (0.6, 0, 0.6, 0.72), (0.6, 0.72, 0.6, 0.78),
                  (0.6, 0.78, 0.25, 0.78), (0.25, 0.78, 0.25, 0.72)],
        }

        ozel = {
            '-': [(0.1, 0.5, 0.9, 0.5)],
            '.': [(0.4, 0, 0.5, 0), (0.5, 0, 0.5, 0.08), (0.5, 0.08, 0.4, 0.08),
                  (0.4, 0.08, 0.4, 0)],
            ',': [(0.45, 0.08, 0.45, 0.02), (0.45, 0.02, 0.35, -0.15)],
            '!': [(0.45, 0.25, 0.45, 1), (0.45, 1, 0.45, 0.25),
                  (0.45, 0.25, 0.45, 0), (0.45, 0, 0.45, 0.08)],
            '?': [(0, 0.85, 0.15, 1), (0.15, 1, 0.75, 1), (0.75, 1, 0.9, 0.85),
                  (0.9, 0.85, 0.9, 0.6), (0.9, 0.6, 0.5, 0.4),
                  (0.5, 0.4, 0.5, 0.25), (0.5, 0.25, 0.5, 0),
                  (0.5, 0, 0.5, 0.08)],
            '/': [(0, 0, 1, 1)],
            ':': [(0.45, 0.15, 0.45, 0.22), (0.45, 0.22, 0.45, 0.45),
                  (0.45, 0.45, 0.45, 0.52)],
            '#': [(0.3, 0, 0.3, 1), (0.3, 1, 0.7, 1), (0.7, 1, 0.7, 0),
                  (0.7, 0, 0.05, 0), (0.05, 0, 0.05, 0.35),
                  (0.05, 0.35, 0.95, 0.35), (0.95, 0.35, 0.95, 0.65),
                  (0.95, 0.65, 0.05, 0.65)],
        }

        base_kalinlik = max(2.0, min(5.0, (sc / 10) * 0.13))
        kalinlik = base_kalinlik * kalinlik_carpan

        for harf in metin:
            if harf == ' ':
                mx += sc * 0.5
                continue

            ciz, gx, yx = None, BG, 1.0
            if harf in buyuk:
                ciz = buyuk[harf]
            elif harf in tr_b:
                ciz = tr_b[harf]
            elif harf in kucuk:
                ciz = kucuk[harf]; gx, yx = KG, KY
            elif harf in tr_k:
                ciz = tr_k[harf]; gx, yx = KG, KY
            elif harf in sayilar:
                ciz = sayilar[harf]; gx = SG
            elif harf in ozel:
                ciz = ozel[harf]; gx = 0.5
            else:
                mx += sc * 0.3
                continue

            if not ciz:
                mx += sc * 0.3
                continue

            if italic:
                ciz = self._italic_donustur(ciz, egim=0.25)

            self._harf_dik(ciz, mx, by, sc, gx, yx, kalinlik)
            mx += (sc * gx) + ara

    # ── Logo Dikme (Kontur Running) ──────────────────────────────

    def logo_dik(self, image_path, baslangic_x, baslangic_y,
                 genislik, yukseklik, birim="cm",
                 threshold=200, simplify_epsilon=2.0,
                 adim=8, min_contour_len=10):
        """
        Raster logo.png dosyasını kontur bazlı running stitch ile alana sığdırır.
        Parametreler:
            image_path: Logo dosya yolu
            baslangic_x, baslangic_y: Başlangıç koordinatı (birime göre)
            genislik, yukseklik: Hedef alan (birime göre)
            birim: "cm" veya "mm"
            threshold: Grayscale eşik (0-255)
            simplify_epsilon: Kontur basitleştirme piksel toleransı
            adim: Running stitch adımı (dikiş aralığı, birim: 0.1 mm)
            min_contour_len: Çok kısa konturları elemek için min nokta sayısı
        """
        if birim == "cm":
            birim_carpan = 100
        elif birim == "mm":
            birim_carpan = 10
        else:
            birim_carpan = 100

        target_w = genislik * birim_carpan
        target_h = yukseklik * birim_carpan
        bx = baslangic_x * birim_carpan
        by = baslangic_y * birim_carpan

        # Görüntüyü yükle ve griye çevir
        img = Image.open(image_path).convert("L")
        arr = np.array(img)

        # Eşikleme (beyaz zemin, siyah logo varsayımı)
        _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY_INV)

        # Kontur bul
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("⚠️ Kontur bulunamadı.")
            return

        # Tüm konturların birleşik bounding box'ı
        all_pts = []
        for cnt in contours:
            for p in cnt:
                all_pts.append((p[0][0], p[0][1]))
        min_x = min(p[0] for p in all_pts)
        max_x = max(p[0] for p in all_pts)
        min_y = min(p[1] for p in all_pts)
        max_y = max(p[1] for p in all_pts)

        src_w = max_x - min_x
        src_h = max_y - min_y
        if src_w < 1 or src_h < 1:
            print("⚠️ Görüntü boyutu geçersiz.")
            return

        sc = min(target_w / src_w, target_h / src_h)

        # Ortalamak için offset
        ox = bx + (target_w - src_w * sc) / 2.0
        oy = by + (target_h - src_h * sc) / 2.0

        print(f"  🖼️ Logo: {image_path}")
        print(f"  📏 Ölçek: {sc/birim_carpan:.2f} {birim}")
        print(f"  📦 Hedef: {genislik}x{yukseklik} {birim}")

        # Her konturu işle
        for cnt in contours:
            if len(cnt) < min_contour_len:
                continue
            approx = cv2.approxPolyDP(cnt, simplify_epsilon, True)
            pts = [(p[0][0], p[0][1]) for p in approx]

            # Kapalı konturu kapat
            if pts[0] != pts[-1]:
                pts.append(pts[0])

            # Ölçekle ve y-ekseni çevir (görüntüde y aşağı, alanda yukarı)
            scaled = []
            for x, y in pts:
                x_s = ox + (x - min_x) * sc
                y_s = oy + (src_h - (y - min_y)) * sc
                scaled.append((x_s, y_s))

            # Eşit aralıklı örnekleme
            sampled = self._resample_polyline(scaled, adim)
            if len(sampled) < 2:
                continue

            # JUMP ilk noktaya
            self.pattern.add_stitch_absolute(
                pyembroidery.JUMP, int(sampled[0][0]), int(sampled[0][1]))

            # Running stitch kontur boyunca
            for pt in sampled[1:]:
                self.pattern.add_stitch_absolute(
                    pyembroidery.STITCH, int(pt[0]), int(pt[1]))

            # TRIM kontur sonu
            last = sampled[-1]
            self.pattern.add_stitch_absolute(pyembroidery.TRIM, int(last[0]), int(last[1]))

    # ── Önizleme ─────────────────────────────────────────────────

    def onizleme(self, ad):
        plt.figure(figsize=(18, 6))
        plt.axis('equal')
        plt.axis('off')
        xs, ys = [], []
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd in (pyembroidery.JUMP, pyembroidery.TRIM):
                if xs:
                    plt.plot(xs, ys, color='navy', linewidth=0.5, alpha=0.8)
                xs, ys = [], []
            elif cmd == pyembroidery.STITCH:
                xs.append(s[0])
                ys.append(s[1])
        if xs:
            plt.plot(xs, ys, color='navy', linewidth=0.5, alpha=0.8)
        plt.title(ad, fontsize=14)
        plt.savefig(f"{ad}.jpg", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Önizleme → {ad}.jpg")

    # ── Kaydet ───────────────────────────────────────────────────

    def kaydet(self, isim):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = isim.replace(' ', '_').lower()
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        self.onizleme(ad)
        print(f"✅ Hazır: {ad}.dst  /  {ad}.jef")


# ══════════════════════════════════════════════════════════════════
#  KULLANIM ÖRNEĞİ
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':

    m = ProfesyonelNakis()

    # Metin örneği
    ISIM  = "SELMAN"
    BIRIM = "cm"

    GENISLIK = 15   # cm
    YUKSEKLIK = 3   # cm
    HARF_ARALIGI = 0.5
    NORMAL = False
    BOLD   = False
    ITALIC = True

    m.isim_yaz(
        ISIM,
        0, 0,
        genislik=GENISLIK,
        yukseklik=YUKSEKLIK,
        harf_araligi=HARF_ARALIGI,
        birim=BIRIM,
        normal=NORMAL,
        bold=BOLD,
        italic=ITALIC
    )

    # Logo örneği — logo.png dosyasını 15x5 cm alana sığdır
    LOGO_GENISLIK = 15  # cm
    LOGO_YUKSEKLIK = 5  # cm
    m.logo_dik(
        image_path="logo.png",
        baslangic_x=0,
        baslangic_y=4,    # metin altına koymak için 4 cm yukarıdan başlat
        genislik=LOGO_GENISLIK,
        yukseklik=LOGO_YUKSEKLIK,
        birim=BIRIM,
        threshold=200,
        simplify_epsilon=2.0,
        adim=8,           # 0.8 mm dikiş aralığı
        min_contour_len=8
    )

    m.kaydet("isim_ve_logo")
