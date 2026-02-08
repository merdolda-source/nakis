#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TATLI DURAĞI LOGO - PROFESYONEL NAKİŞ
- Tam desen görme (edge detection + renk)
- Atlama yok - STOP ile durdurma
- Önce kontur çiz, sonra sargıla
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
        self.last_x = 0
        self.last_y = 0
        
    def mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def safe_stitch(self, x, y):
        """Güvenli dikiş - max 7mm, atlama varsa STOP"""
        MAX_STITCH = 70  # 7mm
        JUMP_LIMIT = 30  # 3mm üzeri = potansiyel atlama
        
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist > MAX_STITCH:
            # Uzun mesafe - ara noktalar + STOP
            steps = int(dist / MAX_STITCH) + 1
            
            # ÖNCE STOP - makine durur, kullanıcı ipliği kontrol eder
            if dist > 100:  # 10mm üzeri atlama
                self.pattern.add_command(pyembroidery.STOP)
            
            for i in range(1, steps + 1):
                t = i / steps
                mx = int(self.last_x + (x - self.last_x) * t)
                my = int(self.last_y + (y - self.last_y) * t)
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, mx, my)
                self.last_x, self.last_y = mx, my
        else:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            self.last_x, self.last_y = x, y

    def move_to(self, x, y):
        """Pozisyon değiştir - STOP ile durdur"""
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist > 50:  # 5mm üzeri hareket = STOP
            self.pattern.add_command(pyembroidery.STOP)
        
        # Küçük dikişlerle git
        if dist > 30:
            steps = int(dist / 30) + 1
            for i in range(1, steps + 1):
                t = i / steps
                mx = int(self.last_x + (x - self.last_x) * t)
                my = int(self.last_y + (y - self.last_y) * t)
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, mx, my)
                self.last_x, self.last_y = mx, my
        else:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            self.last_x, self.last_y = x, y

    def resample_points(self, pts, step=25):
        """Noktaları eşit aralıkla örnekle"""
        if len(pts) < 2:
            return pts
        
        result = [pts[0]]
        accum = 0
        
        for i in range(1, len(pts)):
            x0, y0 = result[-1]
            x1, y1 = pts[i]
            d = self.mesafe(x0, y0, x1, y1)
            
            if d < 1:
                continue
            
            while accum + d >= step:
                ratio = (step - accum) / d
                nx = x0 + (x1 - x0) * ratio
                ny = y0 + (y1 - y0) * ratio
                result.append((nx, ny))
                x0, y0 = nx, ny
                d = self.mesafe(x0, y0, x1, y1)
                accum = 0
            
            accum += d
        
        # Son noktayı ekle
        if self.mesafe(result[-1][0], result[-1][1], pts[-1][0], pts[-1][1]) > 5:
            result.append(pts[-1])
        
        return result

    def kontur_ciz(self, pts):
        """Kontur dikişi - düz çizgi"""
        if len(pts) < 2:
            return
        
        pts = self.resample_points(pts, 25)  # 2.5mm aralık
        
        # İlk noktaya git
        self.move_to(pts[0][0], pts[0][1])
        
        # Tüm noktaları dik
        for x, y in pts[1:]:
            self.safe_stitch(x, y)

    def saten_dolgu(self, pts, genislik=20):
        """Saten dikiş - zigzag dolgu"""
        if len(pts) < 2:
            return
        
        pts = self.resample_points(pts, 15)  # 1.5mm aralık (sık)
        half_w = genislik / 2
        
        # İlk noktaya git
        self.move_to(pts[0][0], pts[0][1])
        
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            
            dx = x1 - x0
            dy = y1 - y0
            length = math.hypot(dx, dy)
            
            if length < 1:
                continue
            
            # Dik yön
            nx = -dy / length * half_w
            ny = dx / length * half_w
            
            # Zigzag
            self.safe_stitch(x0 + nx, y0 + ny)
            self.safe_stitch(x0 - nx, y0 - ny)

    def alan_doldur(self, mask, scale, offset_x, offset_y, img_h, satir_aralik=6):
        """Alan dolgu - yatay tarama çizgileri"""
        h, w = mask.shape
        direction = 1
        first_point = True
        
        for row in range(0, h, satir_aralik):
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
                    if col - start > 2:
                        segments.append((start, col))
            
            if inside and w - start > 2:
                segments.append((start, w))
            
            if not segments:
                continue
            
            # Yön değiştir
            if direction < 0:
                segments = segments[::-1]
            
            for seg in segments:
                s, e = seg
                if direction < 0:
                    s, e = e, s
                
                # Koordinat dönüşümü
                ex1 = offset_x + s * scale
                ex2 = offset_x + e * scale
                ey = offset_y + (img_h - row) * scale
                
                if first_point:
                    self.move_to(ex1, ey)
                    first_point = False
                else:
                    # Satır başına git
                    self.safe_stitch(ex1, ey)
                
                # Satır sonu
                self.safe_stitch(ex2, ey)
            
            direction *= -1

    def tum_kenarlar_bul(self, img_rgb):
        """Tüm kenarları bul - Canny + morfoloji"""
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # Gürültü azalt
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Canny kenar tespiti (düşük eşik = daha fazla detay)
        edges = cv2.Canny(blur, 30, 100)
        
        # Kalınlaştır
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        return edges

    def renk_maskesi(self, img_rgb, renk):
        """Renk maskesi oluştur"""
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        
        if renk == "gold":
            # Sarı/Altın - geniş aralık
            lower = np.array([15, 40, 80])
            upper = np.array([45, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Turuncu tonları da ekle
            lower2 = np.array([10, 50, 100])
            upper2 = np.array([20, 255, 255])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask, mask2)
            
        elif renk == "red":
            # Kırmızı (iki aralık)
            lower1 = np.array([0, 50, 50])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([160, 50, 50])
            upper2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            # Bordo/koyu kırmızı
            lower3 = np.array([0, 30, 30])
            upper3 = np.array([15, 200, 150])
            mask3 = cv2.inRange(hsv, lower3, upper3)
            mask = cv2.bitwise_or(mask, mask3)
            
        elif renk == "white":
            # Beyaz/Açık gri
            lower = np.array([0, 0, 150])
            upper = np.array([180, 60, 255])
            mask = cv2.inRange(hsv, lower, upper)
            
        else:
            mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
        
        # Temizle
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return mask

    def konturlari_cikart(self, mask, scale, offset_x, offset_y, img_h, min_alan=30):
        """Mask'tan kontur listesi çıkar"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        result = []
        
        for cnt in contours:
            alan = cv2.contourArea(cnt)
            if alan < min_alan:
                continue
            
            # Basitleştir ama fazla değil
            epsilon = 0.003 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            if len(approx) < 3:
                continue
            
            # Nakış koordinatına çevir
            pts = []
            for p in approx:
                px, py = p[0]
                ex = offset_x + px * scale
                ey = offset_y + (img_h - py) * scale
                pts.append((ex, ey))
            
            # Kapat
            pts.append(pts[0])
            result.append(pts)
        
        return result

    def kenar_konturlari(self, edges, scale, offset_x, offset_y, img_h, min_uzunluk=20):
        """Kenar görüntüsünden konturlar"""
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        result = []
        
        for cnt in contours:
            uzunluk = cv2.arcLength(cnt, False)
            if uzunluk < min_uzunluk:
                continue
            
            # Basitleştir
            epsilon = 0.005 * uzunluk
            approx = cv2.approxPolyDP(cnt, epsilon, False)
            
            if len(approx) < 2:
                continue
            
            pts = []
            for p in approx:
                px, py = p[0]
                ex = offset_x + px * scale
                ey = offset_y + (img_h - py) * scale
                pts.append((ex, ey))
            
            result.append(pts)
        
        return result

    def sirala_yakin(self, konturlar):
        """Konturları en yakından başlayarak sırala"""
        if not konturlar:
            return []
        
        result = []
        remaining = list(konturlar)
        cx, cy = self.last_x, self.last_y
        
        while remaining:
            best_idx = 0
            best_dist = float('inf')
            reverse = False
            
            for i, cnt in enumerate(remaining):
                if not cnt:
                    continue
                
                # Baştan mesafe
                d1 = self.mesafe(cx, cy, cnt[0][0], cnt[0][1])
                # Sondan mesafe
                d2 = self.mesafe(cx, cy, cnt[-1][0], cnt[-1][1])
                
                if d1 < best_dist:
                    best_dist = d1
                    best_idx = i
                    reverse = False
                
                if d2 < best_dist:
                    best_dist = d2
                    best_idx = i
                    reverse = True
            
            cnt = remaining.pop(best_idx)
            if reverse:
                cnt = cnt[::-1]
            
            result.append(cnt)
            
            if cnt:
                cx, cy = cnt[-1]
        
        return result

    def logo_isle(self, image_path, genislik_cm=15, yukseklik_cm=10):
        """Ana işlem"""
        
        print("\n" + "="*70)
        print("🍰 TATLI DURAĞI LOGO - TAM DESEN NAKİŞ")
        print("="*70)
        
        # Yükle
        img = Image.open(image_path).convert("RGB")
        img_rgb = np.array(img)
        img_h, img_w = img_rgb.shape[:2]
        
        print(f"📐 Görüntü: {img_w} x {img_h} piksel")
        
        # Boyut hesapla
        target_w = genislik_cm * 100  # 0.1mm
        target_h = yukseklik_cm * 100
        
        scale = min(target_w / img_w, target_h / img_h)
        offset_x = (target_w - img_w * scale) / 2
        offset_y = (target_h - img_h * scale) / 2
        
        print(f"📏 Hedef: {genislik_cm} x {yukseklik_cm} cm")
        print(f"📏 Ölçek: {scale:.4f}")
        
        # ═══════════════════════════════════════════════════════════
        # GÖRÜNTÜ ANALİZİ
        # ═══════════════════════════════════════════════════════════
        
        print("\n🔍 Görüntü analiz ediliyor...")
        
        # Kenarlar
        edges = self.tum_kenarlar_bul(img_rgb)
        
        # Renk maskeleri
        gold_mask = self.renk_maskesi(img_rgb, "gold")
        red_mask = self.renk_maskesi(img_rgb, "red")
        white_mask = self.renk_maskesi(img_rgb, "white")
        
        # Kenar konturları (tüm detaylar)
        edge_konturs = self.kenar_konturlari(edges, scale, offset_x, offset_y, img_h, min_uzunluk=15)
        
        # Renk konturları
        gold_konturs = self.konturlari_cikart(gold_mask, scale, offset_x, offset_y, img_h, min_alan=30)
        red_konturs = self.konturlari_cikart(red_mask, scale, offset_x, offset_y, img_h, min_alan=50)
        white_konturs = self.konturlari_cikart(white_mask, scale, offset_x, offset_y, img_h, min_alan=20)
        
        print(f"   📍 Kenar konturları: {len(edge_konturs)}")
        print(f"   🟡 Altın konturları: {len(gold_konturs)}")
        print(f"   🔴 Kırmızı konturları: {len(red_konturs)}")
        print(f"   ⚪ Beyaz konturları: {len(white_konturs)}")
        
        # ═══════════════════════════════════════════════════════════
        # İPLİK RENKLERİ
        # ═══════════════════════════════════════════════════════════
        
        self.pattern.add_thread({"color": 0xD4AF37, "name": "Gold"})
        self.pattern.add_thread({"color": 0x8B0000, "name": "DarkRed"})
        self.pattern.add_thread({"color": 0xFFFFFF, "name": "White"})
        
        # Başlangıç
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, 0, 0)
        self.last_x, self.last_y = 0, 0
        
        # ═══════════════════════════════════════════════════════════
        # 1. ALTIN - KONTUR ÇİZ
        # ═══════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🟡 AŞAMA 1: ALTIN KONTURLARI ÇİZİLİYOR...")
        print("-"*70)
        
        gold_konturs = self.sirala_yakin(gold_konturs)
        
        for i, kontur in enumerate(gold_konturs):
            print(f"   Kontur {i+1}/{len(gold_konturs)}")
            self.kontur_ciz(kontur)
        
        # Kenar detayları (altın bölgelerde)
        print("   Kenar detayları ekleniyor...")
        gold_edges = []
        for cnt in edge_konturs:
            if not cnt:
                continue
            # Altın mask içinde mi kontrol et (basit)
            px = int((cnt[0][0] - offset_x) / scale)
            py = int(img_h - (cnt[0][1] - offset_y) / scale)
            if 0 <= px < img_w and 0 <= py < img_h:
                if gold_mask[py, px] > 0:
                    gold_edges.append(cnt)
        
        gold_edges = self.sirala_yakin(gold_edges)
        for kontur in gold_edges[:50]:  # İlk 50 detay
            self.kontur_ciz(kontur)
        
        # ═══════════════════════════════════════════════════════════
        # 2. ALTIN - SATEN DOLGU
        # ═══════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🟡 AŞAMA 2: ALTIN SATEN DOLGU...")
        print("-"*70)
        
        gold_konturs = self.sirala_yakin(
            self.konturlari_cikart(gold_mask, scale, offset_x, offset_y, img_h, min_alan=30)
        )
        
        for i, kontur in enumerate(gold_konturs):
            print(f"   Saten {i+1}/{len(gold_konturs)}")
            self.saten_dolgu(kontur, genislik=18)
        
        # ═══════════════════════════════════════════════════════════
        # RENK DEĞİŞİM - KIRMIZI
        # ═══════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("🔴 AŞAMA 3: KIRMIZI ZEMİN...")
        print("-"*70)
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        # Konturlar
        red_konturs = self.sirala_yakin(red_konturs)
        
        for i, kontur in enumerate(red_konturs):
            print(f"   Kontur {i+1}/{len(red_konturs)}")
            self.kontur_ciz(kontur)
        
        # Alan dolgu
        print("   Alan dolgu yapılıyor...")
        self.alan_doldur(red_mask, scale, offset_x, offset_y, img_h, satir_aralik=5)
        
        # ═══════════════════════════════════════════════════════════
        # RENK DEĞİŞİM - BEYAZ
        # ═══════════════════════════════════════════════════════════
        
        print("\n" + "-"*70)
        print("⚪ AŞAMA 4: BEYAZ YAZI ve DETAYLAR...")
        print("-"*70)
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        # Konturlar
        white_konturs = self.sirala_yakin(white_konturs)
        
        for i, kontur in enumerate(white_konturs):
            print(f"   Kontur {i+1}/{len(white_konturs)}")
            self.kontur_ciz(kontur)
        
        # Saten dolgu
        print("   Saten dolgu yapılıyor...")
        white_konturs = self.sirala_yakin(
            self.konturlari_cikart(white_mask, scale, offset_x, offset_y, img_h, min_alan=20)
        )
        
        for kontur in white_konturs:
            self.saten_dolgu(kontur, genislik=22)
        
        # Beyaz kenar detayları
        print("   Beyaz detaylar ekleniyor...")
        white_edges = []
        for cnt in edge_konturs:
            if not cnt:
                continue
            px = int((cnt[0][0] - offset_x) / scale)
            py = int(img_h - (cnt[0][1] - offset_y) / scale)
            if 0 <= px < img_w and 0 <= py < img_h:
                if white_mask[py, px] > 0:
                    white_edges.append(cnt)
        
        white_edges = self.sirala_yakin(white_edges)
        for kontur in white_edges[:30]:
            self.kontur_ciz(kontur)
        
        # ═══════════════════════════════════════════════════════════
        # BİTİŞ
        # ═══════════════════════════════════════════════════════════
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.END)
        
        # İstatistik
        stitch_count = len([s for s in self.pattern.stitches if s[2] == pyembroidery.STITCH])
        stop_count = len([s for s in self.pattern.stitches if s[2] == pyembroidery.STOP])
        
        print("\n" + "="*70)
        print("📊 SONUÇ")
        print("="*70)
        print(f"   ✅ Toplam dikiş: {stitch_count:,}")
        print(f"   ⏸️  Stop sayısı: {stop_count}")
        print(f"   🎨 Renk sayısı: 3")
        print(f"   📐 Boyut: {genislik_cm} x {yukseklik_cm} cm")
        print("="*70)

    def onizleme(self, dosya_adi):
        """Detaylı önizleme kaydet"""
        fig, ax = plt.subplots(figsize=(18, 14))
        ax.set_aspect('equal')
        
        renkler = ['#D4AF37', '#8B0000', '#FFFFFF']
        renk_idx = 0
        
        segments = []
        xs, ys = [], []
        stops = []
        
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
                
            elif cmd == pyembroidery.STOP:
                stops.append((x, y))
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
        
        # Segmentleri çiz
        for xs, ys, color in segments:
            if len(xs) > 1:
                ax.plot(xs, ys, color=color, linewidth=0.5, alpha=0.9)
        
        # Stop noktalarını göster
        if stops:
            sx, sy = zip(*stops)
            ax.scatter(sx, sy, c='cyan', s=15, marker='s', zorder=10, label='STOP')
        
        ax.set_facecolor('#1a1a1a')
        fig.patch.set_facecolor('#1a1a1a')
        
        ax.set_title('TATLI DURAĞI - Nakış Önizleme (STOP noktaları cyan)', 
                     color='white', fontsize=16, fontweight='bold')
        ax.tick_params(colors='gray')
        ax.legend(loc='upper right', facecolor='#333', edgecolor='white', labelcolor='white')
        
        for spine in ax.spines.values():
            spine.set_color('gray')
        
        plt.tight_layout()
        plt.savefig(f"{dosya_adi}_onizleme.png", dpi=300, facecolor='#1a1a1a')
        plt.close()
        
        print(f"🖼️  Önizleme: {dosya_adi}_onizleme.png")

    def kaydet(self, dosya_adi):
        """Dosyaları kaydet"""
        
        self.onizleme(dosya_adi)
        
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
        
        print("\n✅ TAMAMLANDI!")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA PROGRAM
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    nakis = LogoNakis()
    
    # ╔═════════════════════════════════════════════════════════════════════════╗
    # ║                              AYARLAR                                     ║
    # ╠═════════════════════════════════════════════════════════════════════════╣
    # ║  LOGO_DOSYASI  : Logo görüntü dosyanızın yolu                           ║
    # ║  GENISLIK_CM   : Nakış genişliği (cm)                                   ║
    # ║  YUKSEKLIK_CM  : Nakış yüksekliği (cm)                                  ║
    # ╚═════════════════════════════════════════════════════════════════════════╝
    
    LOGO_DOSYASI = "logo.png"      # ← Logo dosyanızın adı
    GENISLIK_CM = 12               # ← Genişlik (cm)
    YUKSEKLIK_CM = 7              # ← Yükseklik (cm)
    
    # İşle
    nakis.logo_isle(
        image_path=LOGO_DOSYASI,
        genislik_cm=GENISLIK_CM,
        yukseklik_cm=YUKSEKLIK_CM
    )
    
    # Kaydet
    nakis.kaydet("tatli_duragi")
