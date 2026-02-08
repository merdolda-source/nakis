#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG → Nakış (DST/JEF) — DÜZGÜN ÇALIŞAN VERSİYON
Sorun: JPG'de görünüp makinede boş çıkma - DÜZELTİLDİ
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image

try:
    import cv2
except ImportError as e:
    raise ImportError("OpenCV kurun: pip install opencv-python-headless") from e


class LogoNakis:
    def __init__(self):
        self.pattern = None
        self.stitches = []  # Tüm dikişleri önce buraya topluyoruz
        
    def _mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def _resample_polyline(self, pts, step):
        if len(pts) < 2 or step <= 0:
            return pts
        res = [pts[0]]
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            seg = self._mesafe(x0, y0, x1, y1)
            if seg < 1e-6:
                continue
            num_points = max(1, int(seg / step))
            for j in range(1, num_points + 1):
                t = j / num_points
                nx = x0 + (x1 - x0) * t
                ny = y0 + (y1 - y0) * t
                res.append((nx, ny))
        return res

    def _add_stitch(self, x, y, cmd="stitch"):
        """Dikişi listeye ekle"""
        self.stitches.append((float(x), float(y), cmd))

    def _add_move(self, x, y):
        """Atlama ekle"""
        self.stitches.append((float(x), float(y), "move"))

    def _stitch_line(self, pts):
        """Bir çizgiyi dik - İLK NOKTAYA MOVE, GERİSİ STITCH"""
        if len(pts) < 2:
            return
        
        # İlk noktaya atla
        self._add_move(pts[0][0], pts[0][1])
        
        # Geri kalan noktaları dik
        for i in range(1, len(pts)):
            self._add_stitch(pts[i][0], pts[i][1])

    def _ciz_outline(self, contours, transform):
        """Konturları çiz"""
        min_x, min_y, src_w, src_h, scale, ox, oy, step = transform
        
        for cnt in contours:
            if len(cnt) < 3:
                continue
            
            # Basitleştir
            approx = cv2.approxPolyDP(cnt, epsilon=1.0, closed=True)
            if len(approx) < 3:
                continue

            pts_img = [(p[0][0], p[0][1]) for p in approx]
            pts_img.append(pts_img[0])  # Kapat

            # Piksel → nakış
            pts_emb = []
            for x, y in pts_img:
                ex = ox + (x - min_x) * scale
                ey = oy + (src_h - (y - min_y)) * scale
                pts_emb.append((ex, ey))

            # Örnekle ve dik
            pts_emb = self._resample_polyline(pts_emb, step)
            if len(pts_emb) >= 2:
                self._stitch_line(pts_emb)

    def _ciz_hatch(self, mask, transform):
        """Dolgu çiz - ZIGZAG PATTERN"""
        min_x, min_y, src_w, src_h, scale, ox, oy, step = transform
        
        h, w = mask.shape
        hatch_px = max(2, int(8 / scale))  # Satır aralığı
        
        rows_data = []
        
        # Tüm satırları tara
        for row in range(0, h, hatch_px):
            line = mask[row, :]
            segments = []
            inside = False
            start = 0
            
            for col in range(w):
                if line[col] > 0 and not inside:
                    inside = True
                    start = col
                elif line[col] == 0 and inside:
                    inside = False
                    if col - 1 > start:
                        segments.append((start, col - 1))
            
            if inside and w - 1 > start:
                segments.append((start, w - 1))
            
            if segments:
                rows_data.append((row, segments))
        
        # Zigzag için yön
        direction = 1
        
        for row, segments in rows_data:
            for seg in segments:
                x0, x1 = seg
                
                if direction < 0:
                    x0, x1 = x1, x0
                
                # Piksel → nakış
                ex0 = ox + (x0 - min_x) * scale
                ey = oy + (src_h - (row - min_y)) * scale
                ex1 = ox + (x1 - min_x) * scale
                
                pts = [(ex0, ey), (ex1, ey)]
                pts = self._resample_polyline(pts, step)
                
                if len(pts) >= 2:
                    self._stitch_line(pts)
            
            direction *= -1

    def logo_isle(
        self,
        image_path="logo.png",
        genislik=10,
        yukseklik=10,
        birim="cm",
        threshold=128,
        outline=True,
        fill=True,
        stitch_len_mm=2.5,
        invert=False,
    ):
        # Sıfırla
        self.stitches = []
        
        # Birim
        k = 100 if birim == "cm" else 10
        target_w = genislik * k
        target_h = yukseklik * k
        
        # Görüntü
        print(f"\n{'='*50}")
        print(f"📂 Dosya: {image_path}")
        
        img = Image.open(image_path).convert("L")
        arr = np.array(img)
        print(f"📐 Boyut: {arr.shape[1]}x{arr.shape[0]} px")
        
        # Binary
        if threshold is None:
            _, binary = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY_INV)
        
        if invert:
            binary = 255 - binary
        
        # Temizle
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Kontur
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print("❌ Kontur bulunamadı!")
            return
        
        print(f"🔍 {len(contours)} kontur bulundu")
        
        # Bbox
        all_pts = [(p[0][0], p[0][1]) for c in contours for p in c]
        min_x = min(p[0] for p in all_pts)
        max_x = max(p[0] for p in all_pts)
        min_y = min(p[1] for p in all_pts)
        max_y = max(p[1] for p in all_pts)
        src_w = max(1, max_x - min_x)
        src_h = max(1, max_y - min_y)
        
        # Ölçek
        scale = min(target_w / src_w, target_h / src_h)
        ox = (target_w - src_w * scale) / 2
        oy = (target_h - src_h * scale) / 2
        
        step = stitch_len_mm * 10  # mm → 0.1mm
        
        transform = (min_x, min_y, src_w, src_h, scale, ox, oy, step)
        
        print(f"📏 Ölçek: {scale:.4f}")
        print(f"📦 Hedef: {genislik}x{yukseklik} {birim}")
        print(f"🧵 Dikiş: {stitch_len_mm} mm")
        
        # Dolgu
        if fill:
            print("⏳ Dolgu oluşturuluyor...")
            self._ciz_hatch(binary, transform)
        
        # Kontur
        if outline:
            print("⏳ Kontur oluşturuluyor...")
            self._ciz_outline(contours, transform)
        
        print(f"✅ Toplam {len(self.stitches)} nokta")
        print(f"{'='*50}\n")

    def _build_pattern(self):
        """Dikişleri pyembroidery pattern'e çevir"""
        self.pattern = pyembroidery.EmbPattern()
        
        # İplik
        self.pattern.add_thread({
            "color": 0x000000,
            "name": "Black"
        })
        
        if not self.stitches:
            print("❌ Dikiş yok!")
            return
        
        # İlk nokta
        first = self.stitches[0]
        self.pattern.add_stitch_absolute(
            pyembroidery.STITCH,
            int(round(first[0])),
            int(round(first[1]))
        )
        
        last_x, last_y = first[0], first[1]
        stitch_count = 0
        jump_count = 0
        
        for i in range(1, len(self.stitches)):
            x, y, cmd = self.stitches[i]
            x = int(round(x))
            y = int(round(y))
            
            dist = self._mesafe(last_x, last_y, x, y)
            
            if cmd == "move" or dist > 100:  # 10mm'den uzak = jump
                self.pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
                jump_count += 1
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
                stitch_count += 1
            
            last_x, last_y = x, y
        
        # Bitir
        self.pattern.add_stitch_absolute(pyembroidery.END, int(last_x), int(last_y))
        
        print(f"📊 Pattern: {stitch_count} dikiş, {jump_count} atlama")

    def onizleme(self, ad):
        """Önizleme kaydet"""
        if not self.stitches:
            print("❌ Önizleme için dikiş yok!")
            return
            
        plt.figure(figsize=(12, 12))
        plt.axis("equal")
        plt.axis("off")
        
        xs, ys = [], []
        
        for i, (x, y, cmd) in enumerate(self.stitches):
            if cmd == "move":
                if len(xs) > 1:
                    plt.plot(xs, ys, 'b-', linewidth=0.5, alpha=0.8)
                xs, ys = [x], [y]
            else:
                xs.append(x)
                ys.append(y)
        
        if len(xs) > 1:
            plt.plot(xs, ys, 'b-', linewidth=0.5, alpha=0.8)
        
        plt.title(f"{ad} - {len(self.stitches)} nokta", fontsize=14)
        plt.savefig(f"{ad}_preview.jpg", dpi=200, bbox_inches="tight")
        plt.close()
        print(f"🖼️  Önizleme: {ad}_preview.jpg")

    def kaydet(self, isim):
        """DST ve JEF kaydet"""
        if not self.stitches:
            print("❌ Kaydedilecek dikiş yok!")
            return
        
        ad = isim.replace(" ", "_").lower()
        
        # Pattern oluştur
        self._build_pattern()
        
        if self.pattern is None:
            return
        
        # Önizleme
        self.onizleme(ad)
        
        # Normalize et (ÖNEMLİ!)
        self.pattern = self.pattern.get_normalized_pattern()
        
        # DST
        try:
            pyembroidery.write_dst(self.pattern, f"{ad}.dst")
            print(f"💾 DST: {ad}.dst")
        except Exception as e:
            print(f"❌ DST hatası: {e}")
        
        # JEF
        try:
            pyembroidery.write_jef(self.pattern, f"{ad}.jef")
            print(f"💾 JEF: {ad}.jef")
        except Exception as e:
            print(f"❌ JEF hatası: {e}")
        
        # PES
        try:
            pyembroidery.write_pes(self.pattern, f"{ad}.pes")
            print(f"💾 PES: {ad}.pes")
        except Exception as e:
            print(f"❌ PES hatası: {e}")
        
        # EXP (Melco)
        try:
            pyembroidery.write_exp(self.pattern, f"{ad}.exp")
            print(f"💾 EXP: {ad}.exp")
        except Exception as e:
            print(f"❌ EXP hatası: {e}")
        
        print(f"\n✅ TAMAMLANDI!")
        print(f"📁 Dosyalar: {ad}.dst, {ad}.jef, {ad}.pes, {ad}.exp")


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    
    m = LogoNakis()
    
    # ══════════ AYARLAR ══════════
    LOGO = "logo.png"
    
    GENISLIK = 10      # cm
    YUKSEKLIK = 10     # cm
    
    THRESHOLD = 128    # 0-255 (None = otomatik)
    INVERT = False     # True = renkleri tersle
    
    DOLGU = True       # İç dolgu
    KONTUR = True      # Dış çizgi
    
    DIKIŞ_MM = 2.5     # Dikiş uzunluğu (mm)
    # ═════════════════════════════
    
    m.logo_isle(
        image_path=LOGO,
        genislik=GENISLIK,
        yukseklik=YUKSEKLIK,
        birim="cm",
        threshold=THRESHOLD,
        outline=KONTUR,
        fill=DOLGU,
        stitch_len_mm=DIKIŞ_MM,
        invert=INVERT,
    )
    
    m.kaydet("logo")
