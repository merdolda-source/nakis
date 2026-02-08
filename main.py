#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profesyonel Nakış Yazı Makinesi v6
Her harf: JUMP → Underlay ileri → Sargı geri → TRIM
Harf arası geçişlerde dikiş yok, sadece JUMP
YENİ: 
  - Harf geçişlerinde dikiş atma sorunu düzeltildi
  - Belirtilen alana (genişlik x yükseklik) otomatik sığdırma
  - Ayarlanabilir harf aralığı
  - Yazı tipi: Normal, Bold, Italic
"""

import pyembroidery
import math
import matplotlib.pyplot as plt


class ProfesyonelNakis:

    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.son_x = None
        self.son_y = None

    # ── Yardımcılar ──────────────────────────────────────────────

    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

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
        self.son_x = int(x2)
        self.son_y = int(y2)
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
                self.son_x = int(cx + nx)
                self.son_y = int(cy + ny)
            else:
                self.pattern.add_stitch_absolute(
                    pyembroidery.STITCH, int(cx - nx), int(cy - ny))
                self.son_x = int(cx - nx)
                self.son_y = int(cy - ny)
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))
        self.son_x = int(x2)
        self.son_y = int(y2)
        return (x2, y2)

    # ── Italic Dönüşümü ──────────────────────────────────────────

    def _italic_donustur(self, cizgiler, egim=0.25):
        """Çizgileri italic (eğik) yapar - x += y * egim"""
        italic_cizgiler = []
        for a, b, c, d in cizgiler:
            a_new = a + b * egim
            c_new = c + d * egim
            italic_cizgiler.append((a_new, b, c_new, d))
        return italic_cizgiler

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

        # ── 1) JUMP: ilk noktaya atla (dikiş atmadan) ──
        ilk_x, ilk_y = int(segs[0][0]), int(segs[0][1])
        
        # Önceki konumdan uzaksa TRIM ekle
        if self.son_x is not None and self.son_y is not None:
            if self._mesafe(self.son_x, self.son_y, ilk_x, ilk_y) > 50:
                # Önce mevcut konumda TRIM
                self.pattern.add_stitch_absolute(
                    pyembroidery.TRIM, self.son_x, self.son_y)
        
        # Yeni harfin başına JUMP
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, ilk_x, ilk_y)
        cx, cy = segs[0][0], segs[0][1]

        # ── 2) UNDERLAY: tüm segmentleri ileriye running stitch ──
        for sx, sy, ex, ey in segs:
            if self._mesafe(cx, cy, sx, sy) > 1:
                cx, cy = self._running(cx, cy, sx, sy)
            cx, cy = self._running(sx, sy, ex, ey)

        # ── 3) SARGI: ters sırada satin (geri dönüş gereksiz) ──
        for sx, sy, ex, ey in reversed(segs):
            if self._mesafe(cx, cy, ex, ey) > 1:
                cx, cy = self._running(cx, cy, ex, ey)
            cx, cy = self._satin(ex, ey, sx, sy, kalinlik)

        # ── 4) TRIM: harf bitti, iplik kes ──
        self.pattern.add_stitch_absolute(
            pyembroidery.TRIM, int(cx), int(cy))
        self.son_x = int(cx)
        self.son_y = int(cy)

    # ── Metin Boyutlarını Hesapla ────────────────────────────────

    def _metin_boyut_hesapla(self, metin, harf_araligi_oran, italic=False):
        """Metnin normalize edilmiş genişlik ve yükseklik oranlarını hesapla"""
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

    # ── İsim Yazma (Alana Sığdırmalı) ────────────────────────────

    def isim_yaz(self, metin, baslangic_x, baslangic_y, boyut=None, birim="cm",
                 genislik=None, yukseklik=None, harf_araligi=None,
                 normal=True, bold=False, italic=False):
        """
        Metin yazar.
        
        Parametreler:
            metin: Yazılacak metin
            baslangic_x, baslangic_y: Başlangıç koordinatları
            boyut: Harf yüksekliği (eski yöntem)
            birim: "cm" veya "mm"
            genislik: İstenen toplam genişlik
            yukseklik: İstenen toplam yükseklik
            harf_araligi: Harfler arası mesafe (cm veya mm, birime göre)
            normal: Normal yazı tipi (True/False)
            bold: Kalın yazı tipi (True/False)
            italic: Eğik yazı tipi (True/False)
        """
        
        # Birim dönüşümü
        if birim == "cm":
            birim_carpan = 100
        elif birim == "mm":
            birim_carpan = 10
        else:
            birim_carpan = 100
        
        bx = baslangic_x * birim_carpan
        by = baslangic_y * birim_carpan
        
        # Yazı tipi kalınlık çarpanı
        if bold:
            kalinlik_carpan = 1.8
        else:
            kalinlik_carpan = 1.0
        
        # Harf aralığı hesaplama
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
        
        # Metin boyutlarını hesapla
        metin_gen_oran, metin_yuk_oran, min_y_oran = self._metin_boyut_hesapla(
            metin, harf_araligi_oran, italic)
        
        # Boyut hesaplama
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

        # ═══════════════════════════════════════════════════════════
        #  BÜYÜK HARFLER
        # ═══════════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════════
        #  KÜÇÜK HARFLER
        # ═══════════════════════════════════════════════════════════
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
                  (0.85, 0.6, 0.85, 0)],
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

        # ═══════════════════════════════════════════════════════════
        #  SAYILAR
        # ═══════════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════════
        #  TÜRKÇE BÜYÜK
        # ═══════════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════════
        #  TÜRKÇE KÜÇÜK
        # ═══════════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════════
        #  ÖZEL KARAKTERLER
        # ═══════════════════════════════════════════════════════════
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

        # ── Sargı kalınlığı (Bold için artır) ──
        base_kalinlik = max(2.0, min(5.0, harf_mm * 0.13))
        kalinlik = base_kalinlik * kalinlik_carpan

        # İlk harften önce başlangıç konumunu ayarla
        self.son_x = None
        self.son_y = None

        # ── Harf harf dik ──
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

            # Italic dönüşümü uygula
            if italic:
                ciz = self._italic_donustur(ciz, egim=0.25)

            self._harf_dik(ciz, mx, by, sc, gx, yx, kalinlik)
            mx += (sc * gx) + ara

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
#  KULLANIM
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':

    m = ProfesyonelNakis()

    # ═══════════════════════════════════════════════════════════════
    #  AYARLAR
    # ═══════════════════════════════════════════════════════════════
    
    ISIM  = "SELMAN"
    BIRIM = "cm"              # "cm" veya "mm"
    
    # Alan ayarları
    GENISLIK = 15             # Toplam genişlik (cm veya mm)
    YUKSEKLIK = 7             # Toplam yükseklik (cm veya mm)
    
    # Harf aralığı ayarı
    HARF_ARALIGI = 0.5        # Harfler arası mesafe (cm veya mm)
                              # None yaparsanız otomatik hesaplar
    
    # Yazı tipi ayarları (sadece birini True yapın, veya bold+italic birlikte)
    NORMAL = True            # Normal yazı
    BOLD   = False             # Kalın yazı
    ITALIC = False            # Eğik yazı
    
    # ═══════════════════════════════════════════════════════════════
    
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
    
    m.kaydet(ISIM)
