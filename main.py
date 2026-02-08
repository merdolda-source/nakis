#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo Nakış Dönüştürücü (sadece logo işler)
- logo.png içindeki konturları çıkarır
- Alana (genişlik x yükseklik) otomatik sığdırır, merkeze yerleştirir
- Konturları running stitch ile çizer (JUMP → STITCH… → TRIM)
- Çıktılar: .dst, .jef ve önizleme .jpg
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


class NakisLogo:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()

    # ── Yardımcılar ──────────────────────────────────────────────
    def _mesafe(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    def _resample_polyline(self, pts, step):
        """Polylini yaklaşık eşit aralıklı noktalarla örnekle"""
        if len(pts) < 2:
            return pts
        res = [pts[0]]
        acc = 0.0
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
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

    # ── Logo Dikme ──────────────────────────────────────────────
    def logo_dik(
        self,
        image_path,
        baslangic_x,
        baslangic_y,
        genislik,
        yukseklik,
        birim="cm",
        threshold=200,
        simplify_epsilon=2.0,
        adim=8,  # 0.8 mm dikiş aralığı (adim birimi: 0.1 mm)
        min_contour_len=8,
    ):
        """
        Raster logo dosyasını kontur bazlı running stitch ile alana sığdırır.
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
        print(f"  📏 Ölçek: {sc / birim_carpan:.2f} {birim}")
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
                pyembroidery.JUMP, int(sampled[0][0]), int(sampled[0][1])
            )

            # Running stitch kontur boyunca
            for pt in sampled[1:]:
                self.pattern.add_stitch_absolute(
                    pyembroidery.STITCH, int(pt[0]), int(pt[1])
                )

            # TRIM kontur sonu
            last = sampled[-1]
            self.pattern.add_stitch_absolute(
                pyembroidery.TRIM, int(last[0]), int(last[1])
            )

    # ── Önizleme ─────────────────────────────────────────────────
    def onizleme(self, ad):
        plt.figure(figsize=(12, 6))
        plt.axis("equal")
        plt.axis("off")
        xs, ys = [], []
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd in (pyembroidery.JUMP, pyembroidery.TRIM):
                if xs:
                    plt.plot(xs, ys, color="navy", linewidth=0.6, alpha=0.9)
                xs, ys = [], []
            elif cmd == pyembroidery.STITCH:
                xs.append(s[0])
                ys.append(s[1])
        if xs:
            plt.plot(xs, ys, color="navy", linewidth=0.6, alpha=0.9)
        plt.title(ad, fontsize=13)
        plt.savefig(f"{ad}.jpg", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  Önizleme → {ad}.jpg")

    # ── Kaydet ───────────────────────────────────────────────────
    def kaydet(self, isim):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = isim.replace(" ", "_").lower()
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        self.onizleme(ad)
        print(f"✅ Hazır: {ad}.dst  /  {ad}.jef")


# ══════════════════════════════════════════════════════════════════
#  KULLANIM
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    m = NakisLogo()

    # Parametreler
    BIRIM = "cm"
    LOGO_DOSYA = "logo.png"
    GENISLIK = 15    # cm
    YUKSEKLIK = 5    # cm
    BASLANGIC_X = 0  # cm
    BASLANGIC_Y = 0  # cm

    # Kontur/işleme ayarları
    THRESHOLD = 200
    SIMPLIFY_EPS = 2.0
    ADIM = 8              # 0.8 mm dikiş aralığı
    MIN_CONTOUR_LEN = 8

    # Logo işle
    m.logo_dik(
        image_path=LOGO_DOSYA,
        baslangic_x=BASLANGIC_X,
        baslangic_y=BASLANGIC_Y,
        genislik=GENISLIK,
        yukseklik=YUKSEKLIK,
        birim=BIRIM,
        threshold=THRESHOLD,
        simplify_epsilon=SIMPLIFY_EPS,
        adim=ADIM,
        min_contour_len=MIN_CONTOUR_LEN,
    )

    # Kaydet
    m.kaydet("logo")
