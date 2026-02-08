#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG → Nakış (DST/JEF) — Logoyu eksiksiz doldur + kontur
DÜZELTME: İğne çalışmama sorunu giderildi
- Gereksiz JUMP/TRIM komutları azaltıldı
- Tie-in/Tie-out eklendi
- Segment bağlantıları optimize edildi

Gerekli kütüphaneler:
  pip install pyembroidery pillow numpy opencv-python-headless matplotlib
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image

try:
    import cv2
except ImportError as e:
    raise ImportError(
        "OpenCV bulunamadı. Lütfen kurun: pip install opencv-python-headless"
    ) from e


class LogoNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.last_x = 0
        self.last_y = 0
        self.is_first_stitch = True

    # ── Yardımcılar ──────────────────────────────────────────────
    def _mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def _resample_polyline(self, pts, step):
        """Polylini (emb biriminde) eşit aralıklı örnekle."""
        if len(pts) < 2 or step <= 0:
            return pts
        res = [pts[0]]
        acc = 0.0
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            seg = self._mesafe(x0, y0, x1, y1)
            if seg < 1e-6:
                continue
            ux = (x1 - x0) / seg
            uy = (y1 - y0) / seg
            dist = seg
            while acc + dist >= step:
                need = step - acc
                nx = x0 + ux * need
                ny = y0 + uy * need
                res.append((nx, ny))
                dist -= need
                x0, y0 = nx, ny
                acc = 0.0
            acc += dist
        if self._mesafe(res[-1][0], res[-1][1], pts[-1][0], pts[-1][1]) > 1e-3:
            res.append(pts[-1])
        return res

    # ── DİKİŞ KOMUTLARI (DÜZELTİLMİŞ) ──────────────────────────
    def _move_to(self, x, y):
        """
        Yeni pozisyona git. Mesafe kısa ise STITCH, uzun ise JUMP kullan.
        """
        x, y = int(round(x)), int(round(y))
        dist = self._mesafe(self.last_x, self.last_y, x, y)
        
        if self.is_first_stitch:
            # İlk dikiş - sadece pozisyon ayarla
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
            self.is_first_stitch = False
        elif dist > 50:  # 5mm'den uzun mesafe → JUMP
            # Uzun mesafe - jump yap ama çok fazla jump olmasın
            self.pattern.add_stitch_absolute(pyembroidery.JUMP, x, y)
        else:
            # Kısa mesafe - normal dikiş ile git
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        self.last_x = x
        self.last_y = y

    def _stitch_to(self, x, y):
        """Normal dikiş ekle."""
        x, y = int(round(x)), int(round(y))
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        self.last_x = x
        self.last_y = y

    def _tie_in(self, x, y, step=3):
        """
        İplik tutturma dikişi (başlangıç).
        Küçük ileri-geri dikişlerle ipliği sabitler.
        """
        x, y = int(round(x)), int(round(y))
        self._stitch_to(x, y)
        self._stitch_to(x + step, y)
        self._stitch_to(x, y)
        self._stitch_to(x + step, y + step)
        self._stitch_to(x, y)

    def _tie_off(self, x, y, step=3):
        """
        İplik kesme dikişi (bitiş).
        Küçük ileri-geri dikişlerle ipliği sabitler.
        """
        x, y = int(round(x)), int(round(y))
        self._stitch_to(x, y)
        self._stitch_to(x - step, y)
        self._stitch_to(x, y)
        self._stitch_to(x - step, y - step)
        self._stitch_to(x, y)

    def _trim(self):
        """İplik kes (sadece gerektiğinde)."""
        self.pattern.add_stitch_absolute(
            pyembroidery.TRIM, self.last_x, self.last_y
        )

    # ── Kontur Çizimi (Outline) - DÜZELTİLMİŞ ────────────────────
    def _ciz_outline(self, contours, min_x, min_y, src_w, src_h,
                     scale, ox, oy, resample_step, simplify_epsilon, min_contour_len):
        
        # Konturları alana göre sırala (büyükten küçüğe)
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        for cnt in sorted_contours:
            if len(cnt) < min_contour_len:
                continue
            
            # Basitleştirme
            if simplify_epsilon > 0:
                approx = cv2.approxPolyDP(cnt, epsilon=simplify_epsilon, closed=True)
            else:
                approx = cnt

            if len(approx) < 3:
                continue

            pts_img = [(p[0][0], p[0][1]) for p in approx]

            # Kapalı yap
            if pts_img[0] != pts_img[-1]:
                pts_img.append(pts_img[0])

            # Piksel → nakış (y ekseni ters)
            pts_emb = []
            for x, y in pts_img:
                ex = ox + (x - min_x) * scale
                ey = oy + (src_h - (y - min_y)) * scale
                pts_emb.append((ex, ey))

            # Yeniden örnekle
            pts_emb = self._resample_polyline(pts_emb, resample_step)
            if len(pts_emb) < 2:
                continue

            # Başlangıç noktasına git
            self._move_to(pts_emb[0][0], pts_emb[0][1])
            
            # Tie-in (iplik tuttur)
            self._tie_in(pts_emb[0][0], pts_emb[0][1])
            
            # Tüm noktaları dik
            for pt in pts_emb[1:]:
                self._stitch_to(pt[0], pt[1])
            
            # Tie-off (iplik bitir)
            self._tie_off(pts_emb[-1][0], pts_emb[-1][1])

    # ── Dolgu (Hatch) - DÜZELTİLMİŞ ──────────────────────────────
    def _ciz_hatch(self, mask, min_x, min_y, src_w, src_h,
                   scale, ox, oy, hatch_step_px, stitch_step_emb):
        """
        Optimize edilmiş dolgu - sürekli dikiş, minimum jump
        """
        h, w = mask.shape
        all_segments = []
        
        # Tüm satırları tara ve segmentleri topla
        for row in range(0, h, hatch_step_px):
            line = mask[row, :]
            inside = False
            segments = []
            start = 0
            
            for col in range(w):
                val = line[col] > 0
                if val and not inside:
                    inside = True
                    start = col
                if not val and inside:
                    inside = False
                    end = col - 1
                    if end > start:
                        segments.append((start, end, row))
            if inside and w - 1 > start:
                segments.append((start, w - 1, row))
            
            all_segments.extend(segments)
        
        if not all_segments:
            return
        
        # Segmentleri Y koordinatına göre sırala
        all_segments.sort(key=lambda s: s[2])
        
        # Zigzag pattern için alternatif yön
        direction = 1
        current_row = -1
        
        print(f"   📊 Dolgu: {len(all_segments)} segment bulundu")
        
        first_segment = True
        
        for seg in all_segments:
            x0, x1, row = seg
            
            # Yön değiştir (her satırda zigzag)
            if row != current_row:
                direction *= -1
                current_row = row
            
            # Yöne göre başlangıç ve bitiş noktalarını ayarla
            if direction > 0:
                start_x, end_x = x0, x1
            else:
                start_x, end_x = x1, x0
            
            # Piksel → nakış koordinatları
            ex0 = ox + (start_x - min_x) * scale
            ey0 = oy + (src_h - (row - min_y)) * scale
            ex1 = ox + (end_x - min_x) * scale
            ey1 = oy + (src_h - (row - min_y)) * scale
            
            # Çizgiyi örnekle
            pts = [(ex0, ey0), (ex1, ey1)]
            pts = self._resample_polyline(pts, stitch_step_emb)
            
            if len(pts) < 2:
                continue
            
            # Başlangıç noktasına git
            self._move_to(pts[0][0], pts[0][1])
            
            # İlk segment için tie-in
            if first_segment:
                self._tie_in(pts[0][0], pts[0][1])
                first_segment = False
            
            # Tüm noktaları dik
            for p in pts[1:]:
                self._stitch_to(p[0], p[1])
        
        # Son tie-off
        if all_segments:
            self._tie_off(self.last_x, self.last_y)

    # ── Ana İşlev ────────────────────────────────────────────────
    def logo_isle(
        self,
        image_path="logo.png",
        baslangic_x=0,
        baslangic_y=0,
        genislik=15,
        yukseklik=5,
        birim="cm",
        threshold=None,
        outline=True,
        fill=True,
        hatch_step_mm=0.8,
        stitch_step_mm=2.5,       # ÖNEMLİ: Daha uzun dikiş adımı
        simplify_epsilon=1.0,
        min_contour_len=3,
        invert=False,             # Renkleri tersle
    ):
        """
        PNG logoyu alana sığdırıp, dolgu + kontur ile eksiksiz işler.
        """
        # Birim dönüşümü: emb grid 0.1 mm → 1 cm = 100, 1 mm = 10
        if birim == "cm":
            k = 100
        elif birim == "mm":
            k = 10
        else:
            k = 100

        target_w = genislik * k
        target_h = yukseklik * k
        bx = baslangic_x * k
        by = baslangic_y * k

        # Görüntü yükle
        print(f"\n{'='*60}")
        print(f"🖼️  Logo yükleniyor: {image_path}")
        img = Image.open(image_path).convert("L")
        arr = np.array(img)
        print(f"📐 Görüntü boyutu: {arr.shape[1]} x {arr.shape[0]} piksel")

        # Eşikleme
        if threshold is None:
            _, binary = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            print(f"🎯 Otsu eşikleme kullanıldı")
        else:
            _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY_INV)
            print(f"🎯 Sabit eşik: {threshold}")

        # Renkleri tersle (opsiyonel)
        if invert:
            binary = 255 - binary
            print(f"🔄 Renkler ters çevrildi")

        # Gürültü temizleme
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Kontur bul
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("⚠️  Kontur bulunamadı!")
            return

        print(f"🔍 {len(contours)} kontur bulundu")

        # Birleşik bbox
        pts_all = [(p[0][0], p[0][1]) for c in contours for p in c]
        min_x = min(p[0] for p in pts_all)
        max_x = max(p[0] for p in pts_all)
        min_y = min(p[1] for p in pts_all)
        max_y = max(p[1] for p in pts_all)
        src_w = max_x - min_x
        src_h = max_y - min_y
        
        if src_w < 1 or src_h < 1:
            print("⚠️  Görüntü boyutu geçersiz!")
            return

        # Ölçek ve ortalama
        scale = min(target_w / src_w, target_h / src_h)
        ox = bx + (target_w - src_w * scale) / 2.0
        oy = by + (target_h - src_h * scale) / 2.0

        print(f"📏 Ölçek: {scale / k:.3f} {birim}/piksel")
        print(f"📦 Hedef: {genislik} x {yukseklik} {birim}")
        print(f"📍 Gerçek boyut: {src_w * scale / k:.2f} x {src_h * scale / k:.2f} {birim}")

        # Adımlar (emb birimi: 0.1 mm)
        stitch_step_emb = max(10, stitch_step_mm * 10)  # Minimum 1mm dikiş
        hatch_step_px = max(2, int(round(hatch_step_mm * 10 / scale)))

        print(f"\n⚙️  Dikiş ayarları:")
        print(f"   Dikiş adımı: {stitch_step_mm} mm ({stitch_step_emb} emb)")
        print(f"   Dolgu aralığı: {hatch_step_mm} mm ({hatch_step_px} px)")
        print(f"{'='*60}\n")

        # İplik ekle
        thread = pyembroidery.EmbThread()
        thread.color = 0x000000  # Siyah
        thread.description = "Black"
        thread.catalog_number = "Black"
        self.pattern.add_thread(thread)

        # Başlangıç noktası
        start_x = ox + src_w * scale / 2
        start_y = oy + src_h * scale / 2
        self._move_to(start_x, start_y)

        # Dolgu (hatch)
        if fill:
            print("🧵 Dolgu dikişleri oluşturuluyor...")
            self._ciz_hatch(
                mask=binary,
                min_x=min_x,
                min_y=min_y,
                src_w=src_w,
                src_h=src_h,
                scale=scale,
                ox=ox,
                oy=oy,
                hatch_step_px=hatch_step_px,
                stitch_step_emb=stitch_step_emb,
            )
            print("   ✅ Dolgu tamamlandı")

        # Kontur
        if outline:
            print("🧵 Kontur dikişleri oluşturuluyor...")
            self._ciz_outline(
                contours=contours,
                min_x=min_x,
                min_y=min_y,
                src_w=src_w,
                src_h=src_h,
                scale=scale,
                ox=ox,
                oy=oy,
                resample_step=stitch_step_emb,
                simplify_epsilon=simplify_epsilon,
                min_contour_len=min_contour_len,
            )
            print("   ✅ Kontur tamamlandı")

        # Pattern'i sonlandır
        self.pattern.add_stitch_absolute(pyembroidery.END, self.last_x, self.last_y)

    # ── Önizleme ─────────────────────────────────────────────────
    def onizleme(self, ad):
        plt.figure(figsize=(14, 8))
        plt.subplot(1, 1, 1)
        plt.axis("equal")
        plt.axis("off")
        
        xs, ys = [], []
        stitch_count = 0
        jump_count = 0
        
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd == pyembroidery.JUMP:
                if xs:
                    plt.plot(xs, ys, color="navy", linewidth=0.4, alpha=0.8)
                xs, ys = [s[0]], [s[1]]
                jump_count += 1
            elif cmd == pyembroidery.TRIM:
                if xs:
                    plt.plot(xs, ys, color="navy", linewidth=0.4, alpha=0.8)
                xs, ys = [], []
            elif cmd == pyembroidery.STITCH:
                xs.append(s[0])
                ys.append(s[1])
                stitch_count += 1
            elif cmd == pyembroidery.END:
                if xs:
                    plt.plot(xs, ys, color="navy", linewidth=0.4, alpha=0.8)
                break
        
        if xs:
            plt.plot(xs, ys, color="navy", linewidth=0.4, alpha=0.8)
        
        plt.title(f"{ad}\nDikiş: {stitch_count}, Jump: {jump_count}", fontsize=12)
        plt.savefig(f"{ad}.jpg", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"🖼️  Önizleme → {ad}.jpg")
        print(f"📊 İstatistik: {stitch_count} dikiş, {jump_count} jump")

    # ── Kaydet ───────────────────────────────────────────────────
    def kaydet(self, isim):
        # Pattern'i normalize et
        self.pattern = self.pattern.get_normalized_pattern()
        
        ad = isim.replace(" ", "_").lower()
        
        # DST kaydet
        pyembroidery.write_dst(self.pattern, f"{ad}.dst")
        print(f"💾 DST kaydedildi: {ad}.dst")
        
        # JEF kaydet  
        pyembroidery.write_jef(self.pattern, f"{ad}.jef")
        print(f"💾 JEF kaydedildi: {ad}.jef")
        
        # PES kaydet (alternatif format)
        pyembroidery.write_pes(self.pattern, f"{ad}.pes")
        print(f"💾 PES kaydedildi: {ad}.pes")
        
        # Önizleme
        self.onizleme(ad)
        
        print(f"\n✅ Tamamlandı: {ad}.dst / {ad}.jef / {ad}.pes")


# ══════════════════════════════════════════════════════════════════
#  ÇALIŞTIRMA
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    m = LogoNakis()

    # ─────────────── AYARLAR ───────────────
    LOGO_DOSYA   = "logo.png"
    BIRIM        = "cm"
    GENISLIK_CM  = 10        # Hedef genişlik
    YUKSEKLIK_CM = 10        # Hedef yükseklik
    BAS_X        = 0
    BAS_Y        = 0

    # ─────────────── DİKİŞ AYARLARI ───────────────
    # ÖNEMLİ: Bu değerler iğne çalışması için kritik!
    
    THRESHOLD       = 127       # Eşik değeri (None=Otsu, veya 0-255 arası)
    INVERT          = True      # True: Beyaz arka plan, siyah desen
                                # False: Siyah arka plan, beyaz desen
    
    OUTLINE         = True      # Kontur dikişi
    FILL            = True      # Dolgu dikişi
    
    HATCH_STEP_MM   = 0.8       # Dolgu satır aralığı (mm) - daha sık için küçült
    STITCH_STEP_MM  = 2.5       # Dikiş uzunluğu (mm) - ÖNEMLİ: 2-3mm ideal
    
    SIMPLIFY_EPS    = 1.5       # Kontur sadeleştirme (piksel)
    MIN_CONTOUR_LEN = 5         # Minimum kontur noktası

    # ─────────────────────────────────────────────

    print("\n" + "="*60)
    print("🧵 LOGO NAKİŞ DÖNÜŞTÜRÜCÜ")
    print("="*60)
    print(f"⚠️  İğne çalışmıyorsa:")
    print(f"   1. STITCH_STEP_MM değerini artırın (2.5-3.0 mm)")
    print(f"   2. INVERT ayarını değiştirin")
    print(f"   3. THRESHOLD değerini ayarlayın")
    print("="*60)

    m.logo_isle(
        image_path=LOGO_DOSYA,
        baslangic_x=BAS_X,
        baslangic_y=BAS_Y,
        genislik=GENISLIK_CM,
        yukseklik=YUKSEKLIK_CM,
        birim=BIRIM,
        threshold=THRESHOLD,
        outline=OUTLINE,
        fill=FILL,
        hatch_step_mm=HATCH_STEP_MM,
        stitch_step_mm=STITCH_STEP_MM,
        simplify_epsilon=SIMPLIFY_EPS,
        min_contour_len=MIN_CONTOUR_LEN,
        invert=INVERT,
    )

    m.kaydet("logo")
