#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TATLI DURAĞI LOGO - TEK GEÇİŞ SARGILAMA
- Her renk sadece 1 kez işlenir
- Tekrar yok, üst üste binme yok
- Temiz ve optimize edilmiş
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image
import cv2


class TatliDuragiNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.last_x = 0
        self.last_y = 0
        self.stitch_count = 0
        
    def mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def dikis_at(self, x, y):
        """Tek dikiş - max 7mm kontrollü"""
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist < 1:
            return
        
        MAX_STEP = 70  # 7mm
        
        if dist > MAX_STEP:
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

    def yeni_bolgeye_git(self, x, y):
        """Yeni bölgeye geçiş - STOP ile"""
        x = int(round(x))
        y = int(round(y))
        
        dist = self.mesafe(self.last_x, self.last_y, x, y)
        
        if dist > 50:  # 5mm üzeri = STOP
            self.pattern.add_command(pyembroidery.STOP)
        
        self.dikis_at(x, y)

    def tarama_dolgu(self, mask, scale, ox, oy, img_h, aralik=3):
        """
        Tek geçiş tarama dolgusu
        Zigzag şeklinde sürekli dikiş
        """
        h, w = mask.shape
        ilk_nokta = True
        yon = 1  # 1: sola->sağa, -1: sağa->sola
        
        for row in range(0, h, aralik):
            # Satırdaki aktif pikselleri bul
            line = mask[row, :]
            
            # Segment bul (kesintisiz bölgeler)
            segments = []
            start = -1
            
            for col in range(w):
                if line[col] > 0:
                    if start < 0:
                        start = col
                else:
                    if start >= 0:
                        if col - start >= 3:  # Min 3 piksel
                            segments.append((start, col - 1))
                        start = -1
            
            if start >= 0 and w - start >= 3:
                segments.append((start, w - 1))
            
            if not segments:
                continue
            
            # Yöne göre sırala
            if yon < 0:
                segments = segments[::-1]
            
            for seg in segments:
                s, e = seg
                
                # Yöne göre başlangıç/bitiş
                if yon < 0:
                    s, e = e, s
                
                # Koordinat dönüşümü
                x1 = ox + s * scale
                x2 = ox + e * scale
                y_coord = oy + (img_h - row) * scale
                
                if ilk_nokta:
                    self.yeni_bolgeye_git(x1, y_coord)
                    ilk_nokta = False
                else:
                    # Önceki noktaya yakınsa devam et, uzaksa STOP
                    dist = self.mesafe(self.last_x, self.last_y, x1, y_coord)
                    if dist > 100:  # 10mm üzeri
                        self.pattern.add_command(pyembroidery.STOP)
                    self.dikis_at(x1, y_coord)
                
                # Satırı dik
                self.dikis_at(x2, y_coord)
            
            # Sonraki satır için yön değiştir
            yon *= -1
        
        return not ilk_nokta  # Dikiş atıldı mı?

    def renk_maskesi(self, img_rgb, renk_adi):
        """Renk maskesi çıkar"""
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        
        if renk_adi == "gold":
            # Sarı/Altın tonları
            m1 = cv2.inRange(hsv, np.array([15, 80, 80]), np.array([35, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([10, 50, 100]), np.array([25, 255, 255]))
            mask = cv2.bitwise_or(m1, m2)
            
        elif renk_adi == "red":
            # Kırmızı tonları
            m1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([160, 70, 50]), np.array([180, 255, 255]))
            mask = cv2.bitwise_or(m1, m2)
            
        elif renk_adi == "white":
            # Beyaz/Açık tonlar
            mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
            
        elif renk_adi == "brown":
            # Kahverengi tonları
            mask = cv2.inRange(hsv, np.array([5, 50, 30]), np.array([20, 200, 180]))
            
        elif renk_adi == "dark":
            # Koyu tonlar (siyah, koyu gri)
            mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
            
        else:
            mask = np.zeros(img_rgb.shape[:2], dtype=np.uint8)
        
        # Temizle
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return mask

    def logo_isle(self, resim_yolu, en_cm=15, boy_cm=10):
        """Ana işlem - TEK GEÇİŞ"""
        
        print("\n" + "█" * 60)
        print("█  🍰 TATLI DURAĞI - TEK GEÇİŞ SARGILAMA")
        print("█" * 60)
        
        # Görüntü yükle
        img = Image.open(resim_yolu).convert("RGB")
        img_rgb = np.array(img)
        img_h, img_w = img_rgb.shape[:2]
        
        print(f"\n📷 Görüntü: {img_w} x {img_h} piksel")
        
        # Boyut hesapla (0.1mm birim)
        hedef_w = en_cm * 100
        hedef_h = boy_cm * 100
        
        scale = min(hedef_w / img_w, hedef_h / img_h)
        ox = (hedef_w - img_w * scale) / 2
        oy = (hedef_h - img_h * scale) / 2
        
        print(f"📐 Hedef: {en_cm} x {boy_cm} cm")
        
        # ═══════════════════════════════════════════════════════════
        # RENK MASKELERİ - ÖRTÜŞME OLMADAN
        # ═══════════════════════════════════════════════════════════
        
        print("\n🔬 Renk analizi...")
        
        # Her rengi ayrı çıkar
        gold_mask = self.renk_maskesi(img_rgb, "gold")
        red_mask = self.renk_maskesi(img_rgb, "red")
        white_mask = self.renk_maskesi(img_rgb, "white")
        brown_mask = self.renk_maskesi(img_rgb, "brown")
        dark_mask = self.renk_maskesi(img_rgb, "dark")
        
        # ÖRTÜŞME TEMİZLİĞİ - Her piksel sadece 1 renge ait
        # Öncelik: Beyaz > Altın > Kahve > Kırmızı > Koyu
        
        kullanilan = np.zeros_like(white_mask)
        
        # 1. Beyaz (en öncelikli)
        white_final = cv2.bitwise_and(white_mask, cv2.bitwise_not(kullanilan))
        kullanilan = cv2.bitwise_or(kullanilan, white_final)
        
        # 2. Altın
        gold_final = cv2.bitwise_and(gold_mask, cv2.bitwise_not(kullanilan))
        kullanilan = cv2.bitwise_or(kullanilan, gold_final)
        
        # 3. Kahverengi
        brown_final = cv2.bitwise_and(brown_mask, cv2.bitwise_not(kullanilan))
        kullanilan = cv2.bitwise_or(kullanilan, brown_final)
        
        # 4. Kırmızı
        red_final = cv2.bitwise_and(red_mask, cv2.bitwise_not(kullanilan))
        kullanilan = cv2.bitwise_or(kullanilan, red_final)
        
        # 5. Koyu
        dark_final = cv2.bitwise_and(dark_mask, cv2.bitwise_not(kullanilan))
        
        # Piksel sayıları
        print(f"   🟡 Altın:  {np.count_nonzero(gold_final):,} px")
        print(f"   🔴 Kırmızı: {np.count_nonzero(red_final):,} px")
        print(f"   ⚪ Beyaz:  {np.count_nonzero(white_final):,} px")
        print(f"   🟤 Kahve:  {np.count_nonzero(brown_final):,} px")
        print(f"   ⬛ Koyu:   {np.count_nonzero(dark_final):,} px")
        
        # Analiz görüntüsü
        analiz = np.zeros_like(img_rgb)
        analiz[gold_final > 0] = [212, 175, 55]
        analiz[red_final > 0] = [180, 30, 30]
        analiz[white_final > 0] = [255, 255, 255]
        analiz[brown_final > 0] = [139, 90, 43]
        analiz[dark_final > 0] = [40, 40, 40]
        Image.fromarray(analiz).save("renk_analizi.png")
        
        # ═══════════════════════════════════════════════════════════
        # İPLİK TANIMLARI
        # ═══════════════════════════════════════════════════════════
        
        self.pattern.add_thread({"color": 0xD4AF37, "name": "Altin"})
        self.pattern.add_thread({"color": 0xB41E1E, "name": "Kirmizi"})
        self.pattern.add_thread({"color": 0xFFFFFF, "name": "Beyaz"})
        self.pattern.add_thread({"color": 0x8B5A2B, "name": "Kahve"})
        self.pattern.add_thread({"color": 0x1A1A1A, "name": "Siyah"})
        
        # Başlangıç
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, 0, 0)
        
        renk_no = 0
        
        # ═══════════════════════════════════════════════════════════
        # SARGILAMA - HER RENK TEK GEÇİŞ
        # ═══════════════════════════════════════════════════════════
        
        renkler = [
            ("🟡 ALTIN", gold_final, 3),
            ("🔴 KIRMIZI", red_final, 3),
            ("⚪ BEYAZ", white_final, 3),
            ("🟤 KAHVE", brown_final, 3),
            ("⬛ KOYU", dark_final, 2),
        ]
        
        for renk_adi, mask, aralik in renkler:
            piksel = np.count_nonzero(mask)
            
            if piksel < 200:  # Çok az piksel varsa atla
                continue
            
            print(f"\n{'─' * 50}")
            print(f"{renk_adi} SARGILAMA")
            print(f"{'─' * 50}")
            
            if renk_no > 0:
                self.pattern.add_command(pyembroidery.STOP)
                self.pattern.add_command(pyembroidery.TRIM)
                self.pattern.add_command(pyembroidery.COLOR_CHANGE)
            
            onceki = self.stitch_count
            
            # TEK GEÇİŞ DOLGU
            basarili = self.tarama_dolgu(mask, scale, ox, oy, img_h, aralik=aralik)
            
            if basarili:
                print(f"   ✅ {self.stitch_count - onceki:,} dikiş")
                renk_no += 1
        
        # ═══════════════════════════════════════════════════════════
        # BİTİŞ
        # ═══════════════════════════════════════════════════════════
        
        self.pattern.add_command(pyembroidery.STOP)
        self.pattern.add_command(pyembroidery.TRIM)
        self.pattern.add_command(pyembroidery.END)
        
        print("\n" + "█" * 60)
        print(f"█  📊 TOPLAM: {self.stitch_count:,} dikiş")
        print(f"█  🎨 RENK: {renk_no} adet")
        print("█" * 60)

    def onizleme(self, dosya_adi):
        """Önizleme oluştur"""
        
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_aspect('equal')
        
        renkler = ['#D4AF37', '#B41E1E', '#FFFFFF', '#8B5A2B', '#1A1A1A']
        renk_idx = 0
        
        xs, ys = [], []
        segments = []
        
        for stitch in self.pattern.stitches:
            x, y, cmd = stitch
            
            if cmd == pyembroidery.COLOR_CHANGE:
                if len(xs) > 1:
                    segments.append((xs[:], ys[:], renkler[renk_idx % len(renkler)]))
                xs, ys = [], []
                renk_idx += 1
                
            elif cmd in (pyembroidery.TRIM, pyembroidery.STOP):
                if len(xs) > 1:
                    segments.append((xs[:], ys[:], renkler[renk_idx % len(renkler)]))
                xs, ys = [], []
                
            elif cmd == pyembroidery.STITCH:
                xs.append(x)
                ys.append(y)
        
        if len(xs) > 1:
            segments.append((xs, ys, renkler[renk_idx % len(renkler)]))
        
        # Çiz
        for sx, sy, color in segments:
            ax.plot(sx, sy, color=color, linewidth=0.4, alpha=0.9)
        
        ax.set_facecolor('#111')
        fig.patch.set_facecolor('#111')
        ax.set_title('TATLI DURAĞI - Nakış Önizleme', color='white', fontsize=16, pad=15)
        
        plt.tight_layout()
        plt.savefig(f"{dosya_adi}_onizleme.png", dpi=250, facecolor='#111')
        plt.close()
        
        print(f"\n🖼️  Önizleme: {dosya_adi}_onizleme.png")

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


# ══════════════════════════════════════════════════════════════════════
# ÇALIŞTIR
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    # AYARLAR
    LOGO = "logo.png"      # Logo dosyası
    EN = 15                 # cm
    BOY = 10                # cm
    CIKTI = "tatli_duragi"  # Çıktı adı
    
    # İşle
    nakis = TatliDuragiNakis()
    nakis.logo_isle(LOGO, en_cm=EN, boy_cm=BOY)
    nakis.kaydet(CIKTI)
