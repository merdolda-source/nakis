#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG → Nakış (DST/JEF) — Logoyu eksiksiz doldur + kontur
- Siyah (ve koyu) pikselleri logo olarak alır, beyaz zemin varsayar.
- Alana (genişlik x yükseklik) otomatik sığdırır, ortalar.
- Dolgu: yatay hatch (running stitch) ile içi tamamen kapatır.
- Kontur: tüm dış ve iç konturları running stitch ile çizer.
- Çıktılar: .dst, .jef, .jpg önizleme.

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

    def _jump(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x), int(y))

    def _stitch(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))

    def _trim(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.TRIM, int(x), int(y))

    # ── Kontur Çizimi (Outline) ──────────────────────────────────
    def _ciz_outline(self, contours, min_x, min_y, src_w, src_h,
                     scale, ox, oy, resample_step, simplify_epsilon, min_contour_len):
        for cnt in contours:
            if len(cnt) < min_contour_len:
                continue
            # Basitleştirme
            if simplify_epsilon > 0:
                approx = cv2.approxPolyDP(cnt, epsilon=simplify_epsilon, closed=True)
            else:
                approx = cnt  # hiç basitleştirme yapma

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

            # JUMP → STITCH… → TRIM
            self._jump(pts_emb[0][0], pts_emb[0][1])
            for pt in pts_emb[1:]:
                self._stitch(pt[0], pt[1])
            self._trim(pts_emb[-1][0], pts_emb[-1][1])

    # ── Dolgu (Hatch) ────────────────────────────────────────────
    def _ciz_hatch(self, mask, min_x, min_y, src_w, src_h,
                   scale, ox, oy, hatch_step_px, stitch_step_emb):
        """
        mask: binary (255 iç, 0 dış). Hatch satırlarıyla alanı doldurur.
        hatch_step_px: piksel cinsinden satır aralığı
        stitch_step_emb: emb biriminde dikiş adımı
        """
        h, w = mask.shape
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
                    segments.append((start, end))
            if inside:
                segments.append((start, w - 1))

            for seg in segments:
                x0, x1 = seg
                if x1 <= x0:
                    continue
                # Piksel → nakış
                ex0 = ox + (x0 - min_x) * scale
                ey0 = oy + (src_h - (row - min_y)) * scale
                ex1 = ox + (x1 - min_x) * scale
                ey1 = oy + (src_h - (row - min_y)) * scale
                pts = [(ex0, ey0), (ex1, ey1)]
                pts = self._resample_polyline(pts, stitch_step_emb)
                if len(pts) < 2:
                    continue
                self._jump(pts[0][0], pts[0][1])
                for p in pts[1:]:
                    self._stitch(p[0], p[1])
                self._trim(pts[-1][0], pts[-1][1])

    # ── Ana İşlev ────────────────────────────────────────────────
    def logo_isle(
        self,
        image_path="logo.png",
        baslangic_x=0,
        baslangic_y=0,
        genislik=15,
        yukseklik=5,
        birim="cm",
        threshold=None,          # None → Otsu; sayı (0-255) → sabit eşik
        outline=True,
        fill=True,
        hatch_step_mm=0.6,       # daha sık dolgu için 0.6 mm
        stitch_step_mm=0.6,      # dikiş adımı 0.6 mm
        simplify_epsilon=0.5,    # kontur basitleştirme (piksel). 0 → tam detay
        min_contour_len=2,
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
        img = Image.open(image_path).convert("L")
        arr = np.array(img)

        # Eşikleme
        if threshold is None:
            # Otsu ile otomatik
            _, binary = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY_INV)

        # Kontur bul (iç delikler dahil)
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("⚠️ Kontur bulunamadı.")
            return

        # Birleşik bbox
        pts_all = [(p[0][0], p[0][1]) for c in contours for p in c]
        min_x = min(p[0] for p in pts_all)
        max_x = max(p[0] for p in pts_all)
        min_y = min(p[1] for p in pts_all)
        max_y = max(p[1] for p in pts_all)
        src_w = max_x - min_x
        src_h = max_y - min_y
        if src_w < 1 or src_h < 1:
            print("⚠️ Görüntü boyutu geçersiz.")
            return

        # Ölçek ve ortalama
        scale = min(target_w / src_w, target_h / src_h)
        ox = bx + (target_w - src_w * scale) / 2.0
        oy = by + (target_h - src_h * scale) / 2.0

        print(f"🖼️ Logo: {image_path}")
        print(f"📏 Ölçek: {scale / k:.2f} {birim}")
        print(f"📦 Hedef: {genislik} x {yukseklik} {birim}")

        # Adımlar (emb birimi: 0.1 mm)
        stitch_step_emb = max(1, stitch_step_mm * 10)  # en az 0.1 mm
        # Hatch satır aralığı pikselde: emb aralığını px'e çevir, en az 1 px
        hatch_step_px = max(1, int(round(hatch_step_mm * 10 / scale)))

        # Dolgu (hatch)
        if fill:
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

        # Kontur
        if outline:
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
        print(f"🖼️ Önizleme → {ad}.jpg")

    # ── Kaydet ───────────────────────────────────────────────────
    def kaydet(self, isim):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = isim.replace(" ", "_").lower()
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        self.onizleme(ad)
        print(f"✅ Hazır: {ad}.dst  /  {ad}.jef")


# ══════════════════════════════════════════════════════════════════
#  ÇALIŞTIRMA
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    m = LogoNakis()

    # Parametreler
    LOGO_DOSYA   = "logo.png"
    BIRIM        = "cm"
    GENISLIK_CM  = 15   # hedef genişlik
    YUKSEKLIK_CM = 5    # hedef yükseklik
    BAS_X        = 0
    BAS_Y        = 0

    # Dolgu ve kontur ayarları (eksiksiz kapatma için sık ayarlar)
    THRESHOLD = None         # None → Otsu; istersen 200 gibi sabit ver
    OUTLINE   = True
    FILL      = True
    HATCH_STEP_MM   = 0.6    # daha sık dolgu
    STITCH_STEP_MM  = 0.6    # daha sık dikiş
    SIMPLIFY_EPS    = 0.5    # 0 → hiç basitleştirme (daha detay)
    MIN_CONTOUR_LEN = 2

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
    )

    m.kaydet("logo")
