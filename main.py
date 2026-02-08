#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TATLI DURAĞI LOGO - PROFESYONEL NAKİŞ
1. Önce tüm konturları çizer
2. Sonra dolgu/sargılama yapar
3. Atlama yok - sürekli dikiş
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image
import cv2


class LogoNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        
    def mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def noktalar_sirala(self, contours, last_x, last_y):
        """Konturları en yakından başlayarak sırala - atlama azalt"""
        if not contours:
            return []
        
        sorted_list = []
        remaining = list(contours)
        cx, cy = last_x, last_y
        
        while remaining:
            best_idx = 0
            best_dist = float('inf')
            best_start = 0
            
            for i, cnt in enumerate(remaining):
                if len(cnt) < 2:
                    continue
                # En yakın başlangıç noktası
                for j, pt in enumerate(cnt):
                    d = self.mesafe(cx, cy, pt[0], pt[1])
                    if d < best_dist:
                        best_dist = d
                        best_idx = i
                        best_start = j
            
            cnt = remaining.pop(best_idx)
            # Başlangıç noktasından başlayacak şekilde döndür
            if best_start > 0:
                cnt = cnt[best_start:] + cnt[:best_start]
            
            sorted_list.append(cnt)
            if cnt:
                cx, cy = cnt[-1]
        
        return sorted_list

    def resample(self, pts, step):
        """Noktaları eşit aralıklarla örnekle"""
        if len(pts) < 2:
            return pts
        
        result = [pts[0]]
        for i in range(1, len(pts)):
            x0, y0 = pts[i-1]
            x1, y1 = pts[i]
            d = self.mesafe(x0, y0, x1, y1)
            
            if d < 1:
                continue
            
            n_steps = max(1, int(d / step))
            for j in range(1, n_steps + 1):
                t = j / n_steps
                nx = x0 + (x1 - x0) * t
                ny = y0 + (y1 - y0) * t
                result.append((nx, ny))
        
        return result

    def safe_stitch(self, x, y, last_x, last_y, first=False):
        """Güvenli dikiş - 12mm max"""
        MAX_JUMP = 120
        
        x = int(round(x))
        y = int(round(y))
        
        if first:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            return x, y
        
        dist = self.mesafe(last_x, last_y, x, y)
        
        if dist > MAX_JUMP:
            # Ara noktalar ekle (STITCH olarak - atlama değil)
            steps = int(dist / MAX_JUMP) + 1
            for i in range(1, steps + 1):
                t = i / steps
                mx = int(last_x + (x - last_x) * t)
                my = int(last_y + (y - last_y) * t)
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, mx, my)
            return x, y
        else:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            return x, y

    def kontur_ciz(self, pts, last_x, last_y):
        """Tek kontur çiz - sürekli dikiş"""
        if len(pts) < 2:
            return last_x, last_y
        
        for i, (x, y) in enumerate(pts):
            if i == 0 and last_x is None:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))
                last_x, last_y = int(x), int(y)
            else:
                last_x, last_y = self.safe_stitch(x, y, last_x, last_y)
        
        return last_x, last_y

    def saten_doldur(self, pts, genislik, last_x, last_y):
        """Saten dolgu - kontur boyunca zigzag"""
        if len(pts) < 2:
            return last_x, last_y
        
        half_w = genislik / 2
        
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            
            dx = x1 - x0
            dy = y1 - y0
            length = math.hypot(dx, dy)
            
            if length < 1:
                continue
            
            # Normal vektör (dik)
            nx = -dy / length * half_w
            ny = dx / length * half_w
            
            # Zigzag - sol ve sağ
            px1, py1 = x0 + nx, y0 + ny
            px2, py2 = x0 - nx, y0 - ny
            
            if last_x is None:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(px1), int(py1))
                last_x, last_y = int(px1), int(py1)
            
            last_x, last_y = self.safe_stitch(px1, py1, last_x, last_y)
            last_x, last_y = self.safe_stitch(px2, py2, last_x, last_y)
        
        return last_x, last_y

    def alan_doldur(self, mask, scale, offset_x, offset_y, satir_aralik=8):
        """Alan dolgu - yatay tarama"""
        h, w = mask.shape
        last_x, last_y = None, None
        direction = 1
        
        for row in range(0, h, satir_aralik):
            # Bu satırdaki pikselleri bul
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
                    if col - start > 3:
                        segments.append((start, col))
            
            if inside and w - start > 3:
                segments.append((start, w))
            
            if not segments:
                continue
            
            # Yön değiştir (zigzag için)
            if direction < 0:
                segments = segments[::-1]
            
            for seg_start, seg_end in segments:
                if direction < 0:
                    seg_start, seg_end = seg_end, seg_start
                
                # Piksel -> nakış koordinatı
                ex1 = offset_x + seg_start * scale
                ex2 = offset_x + seg_end * scale
                ey = offset_y + (h - row) * scale
                
                if last_x is None:
                    self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(ex1), int(ey))
                    last_x, last_y = int(ex1), int(ey)
                else:
                    last_x, last_y = self.safe_stitch(ex1, ey, last_x, last_y)
                
                last_x, last_y = self.safe_stitch(ex2, ey, last_x, last_y)
            
            direction *= -1
        
        return last_x, last_y

    def renk_ayikla(self, img_rgb, renk_adi):
        """Renkleri ayıkla - daha hassas"""
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        
        if renk_adi == "gold":
            # Altın/Sarı - geniş aralık
            lower1 = np.array([15, 50, 100])
            upper1 = np.array([40, 255, 255])
            mask = cv2.inRange(hsv, lower1, upper1)
            
        elif renk_adi == "red":
            # Kırmızı - iki aralık (0 ve 180 civarı)
            lower1 = np.array([0, 70, 50])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([160, 70, 50])
            upper2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
            
        elif renk_adi == "white":
            # Beyaz
            lower = np.array([0, 0, 180])
            upper = np.array([180, 50, 255])
            mask = cv2.inRange(hsv, lower, upper)
        
        else:
            mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
        
        # Morfolojik temizlik
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return mask

    def konturlari_al(self, mask, scale, offset_x, offset_y, img_h, min_alan=100):
        """Mask'tan konturları çıkar ve nakış koordinatına çevir"""
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        nakis_konturlar = []
        
        for i, cnt in enumerate(contours):
            alan = cv2.contourArea(cnt)
            if alan < min_alan:
                continue
            
            # Basitleştir
            epsilon = 0.005 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            if len(approx) < 3:
                continue
            
            # Piksel -> nakış koordinatı
            pts = []
            for p in approx:
                px, py = p[0]
                ex = offset_x + px * scale
                ey = offset_y + (img_h - py) * scale
                pts.append((ex, ey))
            
            # Kapat
            pts.append(pts[0])
            
            nakis_konturlar.append(pts)
        
        return nakis_konturlar

    def logo_isle(self, image_path, genislik_cm=15, yukseklik_cm=10):
        """Ana işlem fonksiyonu"""
        
        print("\n" + "="*70)
        print("🎨 TATLI DURAĞI LOGO - PROFESYONEL NAKİŞ")
        print("="*70)
        
        # Görüntü yükle
        img = Image.open(image_path).convert("RGB")
        img_rgb = np.array(img)
        img_h, img_w = img_rgb.shape[:2]
        
        print(f"📐 Görüntü: {img_w} x {img_h} piksel")
        
        # Hedef boyut (0.1mm biriminde)
        target_w = genislik_cm * 100
        target_h = yukseklik_cm * 100
        
        # Ölçek hesapla
        scale = min(target_w / img_w, target_h / img_h)
        offset_x = (target_w - img_w * scale) / 2
        offset_y = (target_h - img_h * scale) / 2
        
        print(f"📏 Hedef boyut: {genislik_cm} x {yukseklik_cm} cm")
        print(f"📏 Ölçek faktörü: {scale:.4f}")
        
        # ══════════════════════════════════════════════════════════════
        # RENK MASKELARI OLUŞTUR
        # ══════════════════════════════════════════════════════════════
        
        print("\n🔍 Renk analizi yapılıyor...")
        
        gold_mask = self.renk_ayikla(img_rgb, "gold")
        red_mask = self.renk_ayikla(img_rgb, "red")
        white_mask = self.renk_ayikla(img_rgb, "white")
        
        gold_px = np.count_nonzero(gold_mask)
        red_px = np.count_nonzero(red_mask)
        white_px = np.count_nonzero(white_mask)
        
        print(f"   🟡 Altın: {gold_px:,} piksel")
        print(f"   🔴 Kırmızı: {red_px:,} piksel")
        print(f"   ⚪ Beyaz: {white_px:,} piksel")
        
        # ══════════════════════════════════════════════════════════════
        # KONTURLARI ÇIKAR
        # ══════════════════════════════════════════════════════════════
        
        print("\n📐 Konturlar çıkarılıyor...")
        
        gold_konturs = self.konturlari_al(gold_mask, scale, offset_x, offset_y, img_h, min_alan=50)
        red_konturs = self.konturlari_al(red_mask, scale, offset_x, offset_y, img_h, min_alan=100)
        white_konturs = self.konturlari_al(white_mask, scale, offset_x, offset_y, img_h, min_alan=30)
        
        print(f"   🟡 Altın kontur: {len(gold_konturs)}")
        print(f"   🔴 Kırmızı kontur: {len(red_konturs)}")
        print(f"   ⚪ Beyaz kontur: {len(white_konturs)}")
        
        # ══════════════════════════════════════════════════════════════
        # İPLİK RENKLERİ EKLE
        # ══════════════════════════════════════════════════════════════
        
        self.pattern.add_thread({"color": 0xD4AF37, "name": "Gold"})
        self.pattern.add_thread({"color": 0x8B0000, "name": "Dark Red"})
        self.pattern.add_thread({"color": 0xFFFFFF, "name": "White"})
        
        # ══════════════════════════════════════════════════════════════
        # AŞAMA 1: TÜM KONTURLARI ÇİZ (ALTIN)
        # ══════════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🟡 AŞAMA 1: ALTIN KONTURLARI ÇİZİLİYOR...")
        print("-"*70)
        
        last_x, last_y = None, None
        
        # Konturları sırala (atlama azalt)
        gold_konturs = self.noktalar_sirala(gold_konturs, 0, 0)
        
        for idx, kontur in enumerate(gold_konturs):
            # Noktaları örnekle (2.5mm aralık)
            pts = self.resample(kontur, 25)
            
            if len(pts) < 3:
                continue
            
            print(f"   Kontur {idx+1}/{len(gold_konturs)}: {len(pts)} nokta")
            
            # Çiz
            last_x, last_y = self.kontur_ciz(pts, last_x, last_y)
        
        # ══════════════════════════════════════════════════════════════
        # AŞAMA 2: ALTIN DOLGU (SATEN)
        # ══════════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🟡 AŞAMA 2: ALTIN SATEN DOLGU...")
        print("-"*70)
        
        gold_konturs2 = self.noktalar_sirala(
            self.konturlari_al(gold_mask, scale, offset_x, offset_y, img_h, min_alan=50),
            last_x if last_x else 0,
            last_y if last_y else 0
        )
        
        for idx, kontur in enumerate(gold_konturs2):
            pts = self.resample(kontur, 20)  # Daha sık
            
            if len(pts) < 3:
                continue
            
            print(f"   Saten {idx+1}/{len(gold_konturs2)}")
            
            # Saten dolgu (1.5mm genişlik)
            last_x, last_y = self.saten_doldur(pts, 15, last_x, last_y)
        
        # ══════════════════════════════════════════════════════════════
        # RENK DEĞİŞTİR -> KIRMIZI
        # ══════════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🔴 AŞAMA 3: KIRMIZI ZEMİN...")
        print("-"*70)
        
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        # Önce konturlar
        red_konturs = self.noktalar_sirala(red_konturs, last_x if last_x else 0, last_y if last_y else 0)
        
        for idx, kontur in enumerate(red_konturs):
            pts = self.resample(kontur, 30)
            if len(pts) < 3:
                continue
            print(f"   Kontur {idx+1}/{len(red_konturs)}")
            last_x, last_y = self.kontur_ciz(pts, last_x, last_y)
        
        # Sonra dolgu
        print("   Alan dolgu yapılıyor...")
        last_x, last_y = self.alan_doldur(red_mask, scale, offset_x, offset_y, satir_aralik=6)
        
        # ══════════════════════════════════════════════════════════════
        # RENK DEĞİŞTİR -> BEYAZ
        # ══════════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("⚪ AŞAMA 4: BEYAZ YAZI...")
        print("-"*70)
        
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        # Beyaz konturlar
        white_konturs = self.noktalar_sirala(white_konturs, last_x if last_x else 0, last_y if last_y else 0)
        
        for idx, kontur in enumerate(white_konturs):
            pts = self.resample(kontur, 15)  # Yazı için daha ince
            if len(pts) < 3:
                continue
            print(f"   Kontur {idx+1}/{len(white_konturs)}")
            last_x, last_y = self.kontur_ciz(pts, last_x, last_y)
        
        # Beyaz saten dolgu
        print("   Saten dolgu yapılıyor...")
        white_konturs2 = self.noktalar_sirala(
            self.konturlari_al(white_mask, scale, offset_x, offset_y, img_h, min_alan=30),
            last_x if last_x else 0, last_y if last_y else 0
        )
        
        for kontur in white_konturs2:
            pts = self.resample(kontur, 12)
            if len(pts) < 3:
                continue
            last_x, last_y = self.saten_doldur(pts, 20, last_x, last_y)  # 2mm genişlik
        
        # ══════════════════════════════════════════════════════════════
        # BİTİR
        # ══════════════════════════════════════════════════════════════
        
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.END)
        
        # İstatistik
        total_stitches = len([s for s in self.pattern.stitches if s[2] == pyembroidery.STITCH])
        
        print("\n" + "="*70)
        print("📊 SONUÇ")
        print("="*70)
        print(f"   Toplam dikiş: {total_stitches:,}")
        print(f"   Renk sayısı: 3")
        print(f"   Boyut: {genislik_cm} x {yukseklik_cm} cm")
        print("="*70)

    def onizleme_kaydet(self, dosya_adi):
        """Detaylı önizleme"""
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_aspect('equal')
        
        renkler = ['#D4AF37', '#8B0000', '#FFFFFF']
        renk_idx = 0
        
        xs, ys = [], []
        segments = []
        
        for stitch in self.pattern.stitches:
            x, y, cmd = stitch
            
            if cmd == pyembroidery.COLOR_CHANGE:
                if xs:
                    segments.append((list(xs), list(ys), renkler[renk_idx % 3]))
                xs, ys = [], []
                renk_idx += 1
                
            elif cmd == pyembroidery.TRIM:
                if xs:
                    segments.append((list(xs), list(ys), renkler[renk_idx % 3]))
                xs, ys = [], []
                
            elif cmd == pyembroidery.STITCH:
                xs.append(x)
                ys.append(y)
                
            elif cmd == pyembroidery.END:
                if xs:
                    segments.append((list(xs), list(ys), renkler[renk_idx % 3]))
        
        if xs:
            segments.append((xs, ys, renkler[renk_idx % 3]))
        
        # Çiz
        for xs, ys, color in segments:
            if len(xs) > 1:
                ax.plot(xs, ys, color=color, linewidth=0.4, alpha=0.9)
        
        ax.set_facecolor('#1a1a1a')
        fig.patch.set_facecolor('#1a1a1a')
        
        ax.set_title('TATLI DURAĞI - Nakış Önizleme', color='white', fontsize=16, fontweight='bold')
        ax.tick_params(colors='gray')
        
        for spine in ax.spines.values():
            spine.set_color('gray')
        
        plt.tight_layout()
        plt.savefig(f"{dosya_adi}_onizleme.png", dpi=250, facecolor='#1a1a1a', edgecolor='none')
        plt.close()
        
        print(f"🖼️  Önizleme kaydedildi: {dosya_adi}_onizleme.png")

    def kaydet(self, dosya_adi):
        """Tüm formatları kaydet"""
        
        # Önizleme
        self.onizleme_kaydet(dosya_adi)
        
        # Pattern normalize
        pattern = self.pattern.get_normalized_pattern()
        
        formatlar = [
            ("dst", pyembroidery.write_dst),
            ("pes", pyembroidery.write_pes),
            ("jef", pyembroidery.write_jef),
            ("exp", pyembroidery.write_exp),
            ("vp3", pyembroidery.write_vp3),
        ]
        
        print("\n💾 Dosyalar kaydediliyor...")
        
        for ext, writer in formatlar:
            try:
                writer(pattern, f"{dosya_adi}.{ext}")
                print(f"   ✅ {dosya_adi}.{ext}")
            except Exception as e:
                print(f"   ❌ {ext}: {e}")
        
        print("\n✅ İŞLEM TAMAMLANDI!")


# ══════════════════════════════════════════════════════════════════════════════
# ANA PROGRAM
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    nakis = LogoNakis()
    
    # ╔════════════════════════════════════════════════════════════════════════╗
    # ║                           AYARLAR                                       ║
    # ╠════════════════════════════════════════════════════════════════════════╣
    # ║  LOGO_DOSYASI  : Logo görüntü dosyası                                  ║
    # ║  GENISLIK_CM   : Nakış genişliği (cm)                                  ║
    # ║  YUKSEKLIK_CM  : Nakış yüksekliği (cm)                                 ║
    # ╚════════════════════════════════════════════════════════════════════════╝
    
    LOGO_DOSYASI = "logo.png"
    GENISLIK_CM = 15
    YUKSEKLIK_CM = 10
    
    # İşle
    nakis.logo_isle(
        image_path=LOGO_DOSYASI,
        genislik_cm=GENISLIK_CM,
        yukseklik_cm=YUKSEKLIK_CM
    )
    
    # Kaydet
    nakis.kaydet("tatli_duragi")
