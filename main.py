#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TATLI DURAĞI LOGO - PROFESYONEL NAKİŞ
- Görüntüyü birebir işler
- Sadece sargılama (dolgu) kullanır
- Atlama yerine STOP
- Tam desen çıktısı
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image
import cv2
from collections import deque


class TatliDuragiNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.last_x = 0
        self.last_y = 0
        self.stitch_count = 0
        
    def mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def dikis_at(self, x, y):
        """Tek dikiş at - max 7mm kontrollü"""
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist < 1:
            return
        
        MAX_STEP = 70  # 7mm
        
        if dist > MAX_STEP:
            # Ara dikişler
            steps = int(dist / MAX_STEP) + 1
            for i in range(1, steps + 1):
                t = i / steps
                mx = int(self.last_x + (x - self.last_x) * t)
                my = int(self.last_y + (y - self.last_y) * t)
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, mx, my)
                self.last_x, self.last_y = mx, my
                self.stitch_count += 1
        else:
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            self.last_x, self.last_y = x, y
            self.stitch_count += 1

    def pozisyon_git(self, x, y):
        """Pozisyona git - uzaksa STOP ekle"""
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist > 100:  # 10mm üzeri = STOP
            self.pattern.add_command(pyembroidery.STOP)
        
        # Dikişlerle git
        self.dikis_at(x, y)

    def yatay_sargi(self, mask, scale, ox, oy, img_h, aralik=4, yon_degistir=True):
        """
        Yatay sargılama - tarama dolgu
        Her satırı soldan sağa veya sağdan sola diker
        """
        h, w = mask.shape
        direction = 1
        ilk = True
        
        for row in range(0, h, aralik):
            # Bu satırdaki aktif pikselleri bul
            line = mask[row, :]
            
            # Segment bul
            segments = []
            start = -1
            
            for col in range(w):
                if line[col] > 0:
                    if start < 0:
                        start = col
                else:
                    if start >= 0:
                        if col - start >= 2:
                            segments.append((start, col - 1))
                        start = -1
            
            if start >= 0 and w - start >= 2:
                segments.append((start, w - 1))
            
            if not segments:
                continue
            
            # Yön kontrolü
            if yon_degistir and direction < 0:
                segments = segments[::-1]
            
            for seg in segments:
                s, e = seg
                
                if yon_degistir and direction < 0:
                    s, e = e, s
                
                # Piksel -> nakış koordinatı
                x1 = ox + s * scale
                x2 = ox + e * scale
                y_coord = oy + (img_h - row) * scale
                
                if ilk:
                    self.pozisyon_git(x1, y_coord)
                    ilk = False
                else:
                    self.dikis_at(x1, y_coord)
                
                self.dikis_at(x2, y_coord)
            
            if yon_degistir:
                direction *= -1

    def saten_sargi(self, mask, scale, ox, oy, img_h, genislik=3, adim=2):
        """
        Saten sargılama - kontur boyunca zigzag
        Daha kaliteli kenar dolgusu
        """
        # Konturları bul
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        for cnt in contours:
            if len(cnt) < 10:
                continue
            
            # Kontur noktalarını düzleştir
            pts = []
            for i in range(0, len(cnt), adim):
                px, py = cnt[i][0]
                ex = ox + px * scale
                ey = oy + (img_h - py) * scale
                pts.append((ex, ey))
            
            if len(pts) < 5:
                continue
            
            # İlk noktaya git
            self.pozisyon_git(pts[0][0], pts[0][1])
            
            half_w = genislik * scale / 2
            
            # Zigzag dik
            for i in range(len(pts) - 1):
                x0, y0 = pts[i]
                x1, y1 = pts[i + 1]
                
                dx = x1 - x0
                dy = y1 - y0
                length = math.hypot(dx, dy)
                
                if length < 1:
                    continue
                
                # Normal vektör
                nx = -dy / length * half_w
                ny = dx / length * half_w
                
                # Zigzag
                self.dikis_at(x0 + nx, y0 + ny)
                self.dikis_at(x0 - nx, y0 - ny)
            
            # Kapat
            self.dikis_at(pts[0][0], pts[0][1])

    def tam_dolgu(self, mask, scale, ox, oy, img_h, mod="yatay", aralik=4):
        """
        Tam alan dolgusu
        mod: "yatay", "dikey", "capraz", "cift"
        """
        if mod == "yatay":
            self.yatay_sargi(mask, scale, ox, oy, img_h, aralik=aralik)
            
        elif mod == "dikey":
            # Dikey tarama
            h, w = mask.shape
            direction = 1
            ilk = True
            
            for col in range(0, w, aralik):
                line = mask[:, col]
                segments = []
                start = -1
                
                for row in range(h):
                    if line[row] > 0:
                        if start < 0:
                            start = row
                    else:
                        if start >= 0:
                            if row - start >= 2:
                                segments.append((start, row - 1))
                            start = -1
                
                if start >= 0:
                    segments.append((start, h - 1))
                
                if not segments:
                    continue
                
                if direction < 0:
                    segments = segments[::-1]
                
                for seg in segments:
                    s, e = seg
                    if direction < 0:
                        s, e = e, s
                    
                    x_coord = ox + col * scale
                    y1 = oy + (img_h - s) * scale
                    y2 = oy + (img_h - e) * scale
                    
                    if ilk:
                        self.pozisyon_git(x_coord, y1)
                        ilk = False
                    else:
                        self.dikis_at(x_coord, y1)
                    
                    self.dikis_at(x_coord, y2)
                
                direction *= -1
                
        elif mod == "cift":
            # Önce yatay, sonra dikey (çapraz etki)
            self.yatay_sargi(mask, scale, ox, oy, img_h, aralik=aralik * 2)
            self.tam_dolgu(mask, scale, ox, oy, img_h, mod="dikey", aralik=aralik * 2)

    def renk_cikar(self, img_rgb, hedef_renk):
        """
        Renk maskesi çıkar - hassas ayarlar
        """
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        
        if hedef_renk == "gold":
            # Sarı/Altın/Turuncu tonları
            m1 = cv2.inRange(hsv, np.array([10, 50, 80]), np.array([35, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([35, 30, 100]), np.array([50, 255, 255]))
            # Kahverengi tonları (koyu altın)
            m3 = cv2.inRange(hsv, np.array([5, 50, 50]), np.array([20, 200, 200]))
            mask = cv2.bitwise_or(m1, m2)
            mask = cv2.bitwise_or(mask, m3)
            
        elif hedef_renk == "red":
            # Kırmızı tonları (geniş)
            m1 = cv2.inRange(hsv, np.array([0, 40, 40]), np.array([12, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([160, 40, 40]), np.array([180, 255, 255]))
            # Bordo
            m3 = cv2.inRange(hsv, np.array([0, 30, 20]), np.array([10, 255, 180]))
            mask = cv2.bitwise_or(m1, m2)
            mask = cv2.bitwise_or(mask, m3)
            
        elif hedef_renk == "white":
            # Beyaz ve açık tonlar
            m1 = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 40, 255]))
            # Krem
            m2 = cv2.inRange(hsv, np.array([15, 10, 200]), np.array([35, 50, 255]))
            mask = cv2.bitwise_or(m1, m2)
            
        elif hedef_renk == "dark":
            # Koyu renkler (siyah, koyu gri)
            mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60]))
            
        else:
            mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
        
        # Morfolojik işlemler
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Küçük gürültüleri temizle
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        clean_mask = np.zeros_like(mask)
        for cnt in contours:
            if cv2.contourArea(cnt) > 50:
                cv2.drawContours(clean_mask, [cnt], -1, 255, -1)
        
        return clean_mask

    def kenar_bul(self, img_rgb):
        """Tüm kenarları tespit et"""
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # Çoklu kenar tespiti
        edges1 = cv2.Canny(gray, 50, 150)
        edges2 = cv2.Canny(gray, 30, 100)
        
        # Birleştir
        edges = cv2.bitwise_or(edges1, edges2)
        
        # Kalınlaştır
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        return edges

    def logo_isle(self, resim_yolu, en_cm=15, boy_cm=10):
        """Ana işlem fonksiyonu"""
        
        print("\n" + "█" * 70)
        print("█  🍰 TATLI DURAĞI LOGO - TAM DESEN SARGILAMA")
        print("█" * 70)
        
        # Görüntü yükle
        img = Image.open(resim_yolu).convert("RGB")
        img_rgb = np.array(img)
        img_h, img_w = img_rgb.shape[:2]
        
        print(f"\n📷 Görüntü: {img_w} x {img_h} piksel")
        
        # Boyut hesapla (0.1mm biriminde)
        hedef_w = en_cm * 100
        hedef_h = boy_cm * 100
        
        scale = min(hedef_w / img_w, hedef_h / img_h)
        ox = (hedef_w - img_w * scale) / 2
        oy = (hedef_h - img_h * scale) / 2
        
        print(f"📐 Hedef: {en_cm} x {boy_cm} cm")
        print(f"📏 Ölçek: {scale:.4f}")
        
        # ══════════════════════════════════════════════════════════════════
        # RENK ANALİZİ
        # ══════════════════════════════════════════════════════════════════
        
        print("\n🔬 Renk analizi...")
        
        gold_mask = self.renk_cikar(img_rgb, "gold")
        red_mask = self.renk_cikar(img_rgb, "red")
        white_mask = self.renk_cikar(img_rgb, "white")
        dark_mask = self.renk_cikar(img_rgb, "dark")
        edges = self.kenar_bul(img_rgb)
        
        # Örtüşmeleri düzelt
        # Beyaz öncelikli, sonra altın, sonra kırmızı
        red_mask = cv2.bitwise_and(red_mask, cv2.bitwise_not(white_mask))
        red_mask = cv2.bitwise_and(red_mask, cv2.bitwise_not(gold_mask))
        
        gold_pix = np.count_nonzero(gold_mask)
        red_pix = np.count_nonzero(red_mask)
        white_pix = np.count_nonzero(white_mask)
        dark_pix = np.count_nonzero(dark_mask)
        
        print(f"   🟡 Altın: {gold_pix:,} piksel")
        print(f"   🔴 Kırmızı: {red_pix:,} piksel")
        print(f"   ⚪ Beyaz: {white_pix:,} piksel")
        print(f"   ⬛ Koyu: {dark_pix:,} piksel")
        
        # Analiz görüntüsü kaydet
        analiz = np.zeros_like(img_rgb)
        analiz[gold_mask > 0] = [212, 175, 55]
        analiz[red_mask > 0] = [139, 0, 0]
        analiz[white_mask > 0] = [255, 255, 255]
        analiz[dark_mask > 0] = [50, 50, 50]
        
        Image.fromarray(analiz).save("renk_analizi.png")
        print("   💾 renk_analizi.png kaydedildi")
        
        # ══════════════════════════════════════════════════════════════════
        # İPLİK RENKLERİ
        # ══════════════════════════════════════════════════════════════════
        
        self.pattern.add_thread({"color": 0xD4AF37, "name": "Gold"})
        self.pattern.add_thread({"color": 0x8B0000, "name": "DarkRed"})
        self.pattern.add_thread({"color": 0xFFFFFF, "name": "White"})
        self.pattern.add_thread({"color": 0x1A1A1A, "name": "Black"})
        
        # Başlangıç noktası
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, 0, 0)
        self.last_x, self.last_y = 0, 0
        
        # ══════════════════════════════════════════════════════════════════
        # 1. ALTIN SARGILAMA
        # ══════════════════════════════════════════════════════════════════
        
        print("\n" + "─" * 70)
        print("🟡 AŞAMA 1: ALTIN SARGILAMA")
        print("─" * 70)
        
        if gold_pix > 100:
            print("   📍 Yatay dolgu...")
            self.yatay_sargi(gold_mask, scale, ox, oy, img_h, aralik=3)
            
            print("   📍 Saten kenar...")
            self.saten_sargi(gold_mask, scale, ox, oy, img_h, genislik=2, adim=3)
            
            print(f"   ✅ {self.stitch_count:,} dikiş")
        
        # ══════════════════════════════════════════════════════════════════
        # 2. KIRMIZI SARGILAMA
        # ══════════════════════════════════════════════════════════════════
        
        print("\n" + "─" * 70)
        print("🔴 AŞAMA 2: KIRMIZI SARGILAMA")
        print("─" * 70)
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        if red_pix > 100:
            onceki = self.stitch_count
            
            print("   📍 Çift yönlü dolgu...")
            self.tam_dolgu(red_mask, scale, ox, oy, img_h, mod="cift", aralik=4)
            
            print(f"   ✅ {self.stitch_count - onceki:,} dikiş")
        
        # ══════════════════════════════════════════════════════════════════
        # 3. BEYAZ SARGILAMA
        # ══════════════════════════════════════════════════════════════════
        
        print("\n" + "─" * 70)
        print("⚪ AŞAMA 3: BEYAZ SARGILAMA")
        print("─" * 70)
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        if white_pix > 100:
            onceki = self.stitch_count
            
            print("   📍 Yatay dolgu...")
            self.yatay_sargi(white_mask, scale, ox, oy, img_h, aralik=3)
            
            print("   📍 Saten kenar...")
            self.saten_sargi(white_mask, scale, ox, oy, img_h, genislik=2, adim=2)
            
            print(f"   ✅ {self.stitch_count - onceki:,} dikiş")
        
        # ══════════════════════════════════════════════════════════════════
        # 4. KOYU DETAYLAR (Opsiyonel)
        # ══════════════════════════════════════════════════════════════════
        
        if dark_pix > 500:
            print("\n" + "─" * 70)
            print("⬛ AŞAMA 4: KOYU DETAYLAR")
            print("─" * 70)
            
            self.pattern.add_command(pyembroidery.STOP)
            self.pattern.add_command(pyembroidery.TRIM)
            self.pattern.add_command(pyembroidery.COLOR_CHANGE)
            
            onceki = self.stitch_count
            
            print("   📍 İnce dolgu...")
            self.yatay_sargi(dark_mask, scale, ox, oy, img_h, aralik=2)
            
            print(f"   ✅ {self.stitch_count - onceki:,} dikiş")
        
        # ══════════════════════════════════════════════════════════════════
        # 5. KENAR GÜÇLENDİRME
        # ══════════════════════════════════════════════════════════════════
        
        print("\n" + "─" * 70)
        print("✏️  AŞAMA 5: KENAR GÜÇLENDİRME")
        print("─" * 70)
        
        # Kenarları altın ile güçlendir
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)
        
        # Altın kenarlar
        gold_edges = cv2.bitwise_and(edges, gold_mask)
        if np.count_nonzero(gold_edges) > 100:
            onceki = self.stitch_count
            self.yatay_sargi(gold_edges, scale, ox, oy, img_h, aralik=2)
            print(f"   ✅ Altın kenar: {self.stitch_count - onceki:,} dikiş")
        
        # ══════════════════════════════════════════════════════════════════
        # BİTİŞ
        # ══════════════════════════════════════════════════════════════════
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.END)
        
        # İstatistik
        print("\n" + "█" * 70)
        print("█  📊 SONUÇ")
        print("█" * 70)
        print(f"   🧵 Toplam dikiş: {self.stitch_count:,}")
        print(f"   🎨 Renk sayısı: 4-5")
        print(f"   📐 Boyut: {en_cm} x {boy_cm} cm")
        print("█" * 70)

    def onizleme_olustur(self, dosya_adi):
        """Detaylı önizleme"""
        
        fig, ax = plt.subplots(figsize=(20, 16))
        ax.set_aspect('equal')
        
        renkler = ['#D4AF37', '#8B0000', '#FFFFFF', '#1A1A1A', '#D4AF37']
        renk_idx = 0
        
        tum_x, tum_y = [], []
        segments = []
        xs, ys = [], []
        stop_noktalari = []
        
        for stitch in self.pattern.stitches:
            x, y, cmd = stitch
            
            if cmd == pyembroidery.COLOR_CHANGE:
                if xs and len(xs) > 1:
                    segments.append((list(xs), list(ys), renkler[renk_idx % len(renkler)]))
                xs, ys = [], []
                renk_idx += 1
                
            elif cmd == pyembroidery.TRIM:
                if xs and len(xs) > 1:
                    segments.append((list(xs), list(ys), renkler[renk_idx % len(renkler)]))
                xs, ys = [], []
                
            elif cmd == pyembroidery.STOP:
                stop_noktalari.append((x, y))
                if xs and len(xs) > 1:
                    segments.append((list(xs), list(ys), renkler[renk_idx % len(renkler)]))
                xs, ys = [], []
                
            elif cmd == pyembroidery.STITCH:
                xs.append(x)
                ys.append(y)
                tum_x.append(x)
                tum_y.append(y)
        
        if xs and len(xs) > 1:
            segments.append((xs, ys, renkler[renk_idx % len(renkler)]))
        
        # Çiz
        for xs, ys, color in segments:
            if len(xs) > 1:
                ax.plot(xs, ys, color=color, linewidth=0.3, alpha=0.85)
        
        # Stop noktaları
        if stop_noktalari:
            sx, sy = zip(*stop_noktalari)
            ax.scatter(sx, sy, c='cyan', s=25, marker='s', zorder=15, 
                      label=f'STOP ({len(stop_noktalari)} adet)', edgecolors='white', linewidths=0.5)
        
        ax.set_facecolor('#0d0d0d')
        fig.patch.set_facecolor('#0d0d0d')
        
        ax.set_title('TATLI DURAĞI - Tam Desen Nakış Önizleme', 
                     color='white', fontsize=18, fontweight='bold', pad=20)
        
        ax.tick_params(colors='#666')
        for spine in ax.spines.values():
            spine.set_color('#333')
        
        ax.legend(loc='upper right', facecolor='#222', edgecolor='#666', 
                 labelcolor='white', fontsize=10)
        
        # Boyut bilgisi
        if tum_x and tum_y:
            w_mm = (max(tum_x) - min(tum_x)) / 10
            h_mm = (max(tum_y) - min(tum_y)) / 10
            ax.text(0.02, 0.02, f'Boyut: {w_mm:.1f} x {h_mm:.1f} mm', 
                   transform=ax.transAxes, color='#888', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f"{dosya_adi}_onizleme.png", dpi=300, facecolor='#0d0d0d', 
                   edgecolor='none', bbox_inches='tight')
        plt.close()
        
        print(f"\n🖼️  Önizleme: {dosya_adi}_onizleme.png")

    def kaydet(self, dosya_adi):
        """Tüm formatları kaydet"""
        
        # Önizleme
        self.onizleme_olustur(dosya_adi)
        
        # Normalize
        pattern = self.pattern.get_normalized_pattern()
        
        # Formatlar
        formatlar = [
            ("dst", pyembroidery.write_dst),
            ("pes", pyembroidery.write_pes),
            ("jef", pyembroidery.write_jef),
            ("exp", pyembroidery.write_exp),
            ("vp3", pyembroidery.write_vp3),
            ("xxx", pyembroidery.write_xxx),
        ]
        
        print("\n💾 Nakış dosyaları kaydediliyor...")
        
        for ext, writer in formatlar:
            try:
                writer(pattern, f"{dosya_adi}.{ext}")
                print(f"   ✅ {dosya_adi}.{ext}")
            except Exception as e:
                print(f"   ❌ {ext}: {str(e)[:50]}")
        
        print("\n" + "═" * 70)
        print("✅ İŞLEM TAMAMLANDI!")
        print("═" * 70)


# ════════════════════════════════════════════════════════════════════════════════
# ANA PROGRAM
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    # ╔══════════════════════════════════════════════════════════════════════════╗
    # ║                              AYARLAR                                      ║
    # ╠══════════════════════════════════════════════════════════════════════════╣
    # ║  LOGO_DOSYASI  : Logo görüntü dosyası (PNG, JPG)                         ║
    # ║  EN_CM         : Nakış genişliği (cm)                                    ║
    # ║  BOY_CM        : Nakış yüksekliği (cm)                                   ║
    # ║  CIKTI_ADI     : Çıktı dosyalarının adı                                  ║
    # ╚══════════════════════════════════════════════════════════════════════════╝
    
    LOGO_DOSYASI = "logo.png"
    EN_CM = 12
    BOY_CM = 8
    CIKTI_ADI = "tatli_duragi"
    
    # ────────────────────────────────────────────────────────────────────────────
    
    nakis = TatliDuragiNakis()
    
    # İşle
    nakis.logo_isle(
        resim_yolu=LOGO_DOSYASI,
        en_cm=EN_CM,
        boy_cm=BOY_CM
    )
    
    # Kaydet
    nakis.kaydet(CIKTI_ADI)
