#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TATLI DURAĞI LOGO - ÇOK RENKLİ NAKİŞ
Makineye zarar vermez - Güvenli ayarlar
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image

try:
    import cv2
except ImportError as e:
    raise ImportError("pip install opencv-python-headless") from e


class LogoNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.current_color_index = 0
        
    def _mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def _resample(self, pts, step):
        """Noktaları eşit aralıklarla örnekle"""
        if len(pts) < 2:
            return pts
        res = [pts[0]]
        for i in range(1, len(pts)):
            x0, y0 = pts[i-1]
            x1, y1 = pts[i]
            d = self._mesafe(x0, y0, x1, y1)
            if d < 0.5:
                continue
            n = max(1, int(d / step))
            for j in range(1, n + 1):
                t = j / n
                res.append((x0 + (x1-x0)*t, y0 + (y1-y0)*t))
        return res

    def _add_thread(self, color_hex, name):
        """Yeni iplik rengi ekle"""
        self.pattern.add_thread({
            "color": color_hex,
            "name": name
        })

    def _color_change(self):
        """Renk değiştir"""
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        self.current_color_index += 1

    def _safe_stitch(self, x, y, last_x, last_y, first=False):
        """Güvenli dikiş - maksimum 12.1mm atlama"""
        MAX_JUMP = 121  # 12.1mm = 121 unit (0.1mm)
        
        x = int(round(x))
        y = int(round(y))
        
        if first:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            return x, y
        
        dist = self._mesafe(last_x, last_y, x, y)
        
        if dist > MAX_JUMP:
            # Uzun mesafe = TRIM + JUMP
            self.pattern.add_command(pyembroidery.TRIM)
            
            # Ara noktalar ekle
            steps = int(dist / MAX_JUMP) + 1
            for i in range(1, steps):
                t = i / steps
                mx = int(last_x + (x - last_x) * t)
                my = int(last_y + (y - last_y) * t)
                self.pattern.add_stitch_absolute(pyembroidery.JUMP, mx, my)
            
            self.pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        elif dist > 30:  # 3mm üzeri = jump
            self.pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        else:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        return x, y

    def _stitch_outline(self, pts, last_pos):
        """Kontur dik"""
        if len(pts) < 2:
            return last_pos
        
        lx, ly = last_pos
        
        # İlk noktaya git
        lx, ly = self._safe_stitch(pts[0][0], pts[0][1], lx, ly)
        
        # Kontur boyunca dik
        for i in range(1, len(pts)):
            lx, ly = self._safe_stitch(pts[i][0], pts[i][1], lx, ly)
        
        return (lx, ly)

    def _stitch_satin(self, pts, width, last_pos):
        """Saten dikiş - kalın çizgiler için"""
        if len(pts) < 2:
            return last_pos
        
        lx, ly = last_pos
        half_w = width / 2
        
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            
            # Dik yön hesapla
            dx = x1 - x0
            dy = y1 - y0
            length = math.hypot(dx, dy)
            if length < 0.1:
                continue
            
            # Normal vektör
            nx = -dy / length * half_w
            ny = dx / length * half_w
            
            # Saten zigzag
            lx, ly = self._safe_stitch(x0 + nx, y0 + ny, lx, ly)
            lx, ly = self._safe_stitch(x0 - nx, y0 - ny, lx, ly)
        
        return (lx, ly)

    def _stitch_fill(self, mask, bbox, scale, offset, step_mm=0.8):
        """Dolgu dikiş - zigzag tarama"""
        min_x, min_y, src_w, src_h = bbox
        ox, oy = offset
        
        h, w = mask.shape
        step_px = max(2, int(step_mm * 10 / scale))  # Satır aralığı
        
        last_pos = None
        direction = 1
        
        for row in range(0, h, step_px):
            line = mask[row, :]
            
            # Segmentleri bul
            segments = []
            inside = False
            start = 0
            
            for col in range(w):
                if line[col] > 0 and not inside:
                    inside = True
                    start = col
                elif line[col] == 0 and inside:
                    inside = False
                    if col > start + 2:
                        segments.append((start, col))
            if inside and w > start + 2:
                segments.append((start, w))
            
            if not segments:
                continue
            
            # Zigzag yönü
            if direction < 0:
                segments = segments[::-1]
                segments = [(s[1], s[0]) for s in segments]
            
            for x0, x1 in segments:
                # Piksel → nakış koordinatı
                ex0 = ox + (x0 - min_x) * scale
                ex1 = ox + (x1 - min_x) * scale
                ey = oy + (src_h - (row - min_y)) * scale
                
                pts = [(ex0, ey), (ex1, ey)]
                pts = self._resample(pts, 25)  # 2.5mm
                
                if last_pos is None:
                    last_pos = self._safe_stitch(pts[0][0], pts[0][1], 0, 0, first=True)
                
                last_pos = self._stitch_outline(pts, last_pos)
            
            direction *= -1
        
        return last_pos

    def _extract_color(self, img_rgb, color_lower, color_upper):
        """Belirli renk aralığını çıkar"""
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, color_lower, color_upper)
        
        # Temizle
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask

    def logo_isle(
        self,
        image_path="logo.png",
        genislik_cm=15,
        yukseklik_cm=10,
    ):
        """Logo işle - 3 renk ayrı"""
        
        print(f"\n{'='*60}")
        print(f"🎨 TATLI DURAĞI LOGO NAKİŞ")
        print(f"{'='*60}")
        
        # Görüntü yükle
        img = Image.open(image_path).convert("RGB")
        img_rgb = np.array(img)
        
        print(f"📐 Görüntü: {img_rgb.shape[1]}x{img_rgb.shape[0]} px")
        
        # Hedef boyut (0.1mm biriminde)
        target_w = genislik_cm * 100
        target_h = yukseklik_cm * 100
        
        # Ölçek
        h, w = img_rgb.shape[:2]
        scale = min(target_w / w, target_h / h)
        ox = (target_w - w * scale) / 2
        oy = (target_h - h * scale) / 2
        
        bbox = (0, 0, w, h)
        offset = (ox, oy)
        
        print(f"📏 Hedef: {genislik_cm}x{yukseklik_cm} cm")
        print(f"📏 Ölçek: {scale:.4f}")
        
        # ═══════════════════════════════════════════════════════════
        # RENK 1: ALTIN/SARI SÜSLEMELER
        # ═══════════════════════════════════════════════════════════
        print(f"\n🟡 Renk 1: Altın süslemeler...")
        
        self._add_thread(0xD4A84B, "Gold")
        
        # Sarı/Altın renk aralığı (HSV)
        gold_lower = np.array([15, 80, 120])
        gold_upper = np.array([35, 255, 255])
        gold_mask = self._extract_color(img_rgb, gold_lower, gold_upper)
        
        # Konturları bul
        contours, _ = cv2.findContours(gold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   {len(contours)} kontur bulundu")
        
        last_pos = None
        
        for cnt in contours:
            if cv2.contourArea(cnt) < 50:  # Çok küçükleri atla
                continue
            
            # Basitleştir
            approx = cv2.approxPolyDP(cnt, 2.0, True)
            if len(approx) < 3:
                continue
            
            # Koordinat dönüşümü
            pts = []
            for p in approx:
                px, py = p[0]
                ex = ox + px * scale
                ey = oy + (h - py) * scale
                pts.append((ex, ey))
            pts.append(pts[0])  # Kapat
            
            pts = self._resample(pts, 25)  # 2.5mm
            
            if last_pos is None:
                last_pos = self._safe_stitch(pts[0][0], pts[0][1], 0, 0, first=True)
            
            last_pos = self._stitch_outline(pts, last_pos)
        
        # Dolgu
        last_pos = self._stitch_fill(gold_mask, bbox, scale, offset, step_mm=0.6)
        
        # ═══════════════════════════════════════════════════════════
        # RENK 2: KIRMIZI ZEMIN
        # ═══════════════════════════════════════════════════════════
        print(f"\n🔴 Renk 2: Kırmızı zemin...")
        
        self._color_change()
        self._add_thread(0x8B1A1A, "Dark Red")
        
        # Kırmızı renk aralığı
        red_lower1 = np.array([0, 80, 50])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([160, 80, 50])
        red_upper2 = np.array([180, 255, 255])
        
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   {len(contours)} kontur bulundu")
        
        # Dolgu
        last_pos = self._stitch_fill(red_mask, bbox, scale, offset, step_mm=0.7)
        
        # ═══════════════════════════════════════════════════════════
        # RENK 3: BEYAZ YAZI
        # ═══════════════════════════════════════════════════════════
        print(f"\n⚪ Renk 3: Beyaz yazı...")
        
        self._color_change()
        self._add_thread(0xFFFFFF, "White")
        
        # Beyaz renk aralığı
        white_lower = np.array([0, 0, 200])
        white_upper = np.array([180, 30, 255])
        white_mask = self._extract_color(img_rgb, white_lower, white_upper)
        
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   {len(contours)} kontur bulundu")
        
        for cnt in contours:
            if cv2.contourArea(cnt) < 30:
                continue
            
            approx = cv2.approxPolyDP(cnt, 1.5, True)
            if len(approx) < 3:
                continue
            
            pts = []
            for p in approx:
                px, py = p[0]
                ex = ox + px * scale
                ey = oy + (h - py) * scale
                pts.append((ex, ey))
            pts.append(pts[0])
            
            pts = self._resample(pts, 20)  # 2mm - yazı için daha ince
            
            if last_pos is None:
                last_pos = self._safe_stitch(pts[0][0], pts[0][1], 0, 0, first=True)
            
            # Saten dikiş - yazı için
            last_pos = self._stitch_satin(pts, 15, last_pos)  # 1.5mm genişlik
        
        # Bitir
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.END)
        
        # İstatistik
        stats = self.pattern.count_stitches()
        print(f"\n{'='*60}")
        print(f"📊 ÖZET")
        print(f"   Toplam dikiş: {stats}")
        print(f"   Renk sayısı: 3")
        print(f"{'='*60}")

    def onizleme(self, ad):
        """Önizleme kaydet"""
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_aspect('equal')
        ax.axis('off')
        
        colors = ['#D4A84B', '#8B1A1A', '#FFFFFF']
        color_idx = 0
        
        xs, ys = [], []
        
        for stitch in self.pattern.stitches:
            x, y, cmd = stitch
            
            if cmd == pyembroidery.COLOR_CHANGE:
                if xs:
                    ax.plot(xs, ys, color=colors[color_idx % 3], linewidth=0.5, alpha=0.8)
                xs, ys = [], []
                color_idx += 1
            elif cmd == pyembroidery.TRIM or cmd == pyembroidery.JUMP:
                if xs:
                    ax.plot(xs, ys, color=colors[color_idx % 3], linewidth=0.5, alpha=0.8)
                xs, ys = [x], [y]
            elif cmd == pyembroidery.STITCH:
                xs.append(x)
                ys.append(y)
            elif cmd == pyembroidery.END:
                if xs:
                    ax.plot(xs, ys, color=colors[color_idx % 3], linewidth=0.5, alpha=0.8)
        
        if xs:
            ax.plot(xs, ys, color=colors[color_idx % 3], linewidth=0.5, alpha=0.8)
        
        ax.set_facecolor('black')
        fig.patch.set_facecolor('black')
        
        plt.title(f"{ad} - Nakış Önizleme", color='white', fontsize=14)
        plt.savefig(f"{ad}_preview.png", dpi=200, bbox_inches='tight', 
                    facecolor='black', edgecolor='none')
        plt.close()
        print(f"🖼️  Önizleme: {ad}_preview.png")

    def kaydet(self, isim):
        """Dosyaları kaydet"""
        ad = isim.replace(" ", "_").lower()
        
        # Önizleme
        self.onizleme(ad)
        
        # Normalize
        self.pattern = self.pattern.get_normalized_pattern()
        
        # DST
        try:
            pyembroidery.write_dst(self.pattern, f"{ad}.dst")
            print(f"💾 DST: {ad}.dst")
        except Exception as e:
            print(f"❌ DST: {e}")
        
        # JEF (Janome)
        try:
            pyembroidery.write_jef(self.pattern, f"{ad}.jef")
            print(f"💾 JEF: {ad}.jef")
        except Exception as e:
            print(f"❌ JEF: {e}")
        
        # PES (Brother)
        try:
            pyembroidery.write_pes(self.pattern, f"{ad}.pes")
            print(f"💾 PES: {ad}.pes")
        except Exception as e:
            print(f"❌ PES: {e}")
        
        # EXP (Melco)
        try:
            pyembroidery.write_exp(self.pattern, f"{ad}.exp")
            print(f"💾 EXP: {ad}.exp")
        except Exception as e:
            print(f"❌ EXP: {e}")
        
        print(f"\n✅ TAMAMLANDI!")


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    
    m = LogoNakis()
    
    # ═══════════ AYARLAR ═══════════
    LOGO = "logo.png"          # Logo dosyası
    GENISLIK = 15              # cm
    YUKSEKLIK = 10             # cm
    # ═══════════════════════════════
    
    m.logo_isle(
        image_path=LOGO,
        genislik_cm=GENISLIK,
        yukseklik_cm=YUKSEKLIK,
    )
    
    m.kaydet("tatli_duragi")
