#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG → Nakış (DST/JEF) – Renkli, dolgu + kontur, tie-in/out, renk değişimi

Gerekenler:
    pip install pyembroidery pillow numpy opencv-python-headless matplotlib

Özellikler:
- En fazla 3 rengi k-means ile otomatik algılar; en parlak kümeyi arka plan sayar.
- Her renk için: dolgu (hatch, running stitch) + kontur (running stitch)
- Tie-in / tie-out kilit dikişleri, TRIM ve COLOR_CHANGE komutları
- Alanı (genişlik x yükseklik) otomatik sığdırır, ortalar
- Çıktılar: .dst, .jef, .jpg önizleme
"""

import math
import numpy as np
import pyembroidery
import matplotlib.pyplot as plt
from PIL import Image

try:
    import cv2
except ImportError as e:
    raise ImportError("OpenCV yok. Kurun: pip install opencv-python-headless") from e


# Basit iplik paleti (RGB)
THREAD_PALETTE = [
    ("Black",   (0, 0, 0)),
    ("Red",     (200, 0, 0)),
    ("Blue",    (0, 70, 200)),
    ("Green",   (0, 150, 0)),
    ("Yellow",  (230, 200, 0)),
    ("White",   (255, 255, 255)),
]


def set_thread_color(thread: pyembroidery.EmbThread, rgb):
    """pyembroidery sürümleri için renk ataması (compat)."""
    r, g, b = rgb
    if hasattr(thread, "set_color"):
        try:
            thread.set_color(r, g, b)
            return
        except Exception:
            pass
    # Doğrudan alanlara yaz
    thread.red = r
    thread.green = g
    thread.blue = b
    # 0xRRGGBB
    thread.color = (int(r) << 16) | (int(g) << 8) | int(b)


class LogoNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()

    # ---------- yardımcılar ----------
    def _resample(self, pts, step):
        if len(pts) < 2 or step <= 0:
            return pts
        out = [pts[0]]
        acc = 0.0
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            seg = math.hypot(x1 - x0, y1 - y0)
            if seg < 1e-6:
                continue
            ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
            rem = seg
            while acc + rem >= step:
                need = step - acc
                nx, ny = x0 + ux * need, y0 + uy * need
                out.append((nx, ny))
                rem -= need
                x0, y0 = nx, ny
                acc = 0.0
            acc += rem
        if math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > 1e-3:
            out.append(pts[-1])
        return out

    def _jump(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x), int(y))

    def _stitch(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x), int(y))

    def _trim(self, x, y):
        self.pattern.add_stitch_absolute(pyembroidery.TRIM, int(x), int(y))

    def _color_change(self):
        self.pattern.add_command(pyembroidery.COLOR_CHANGE)

    # ---------- tie-in / tie-out ----------
    def _tie_in(self, pt, step=4):
        x, y = pt
        self._stitch(x, y)
        self._stitch(x + step, y)
        self._stitch(x - step, y)

    def _tie_out(self, pt, step=4):
        x, y = pt
        self._stitch(x + step, y)
        self._stitch(x - step, y)

    # ---------- kontur ----------
    def _draw_outline(self, contours, min_x, min_y, src_w, src_h,
                      scale, ox, oy, resample_step, simplify_eps, min_len):
        total = 0
        for cnt in contours:
            if len(cnt) < min_len:
                continue
            if simplify_eps > 0:
                approx = cv2.approxPolyDP(cnt, epsilon=simplify_eps, closed=True)
            else:
                approx = cnt
            pts_img = [(p[0][0], p[0][1]) for p in approx]
            if pts_img[0] != pts_img[-1]:
                pts_img.append(pts_img[0])

            pts_emb = []
            for x, y in pts_img:
                ex = ox + (x - min_x) * scale
                ey = oy + (src_h - (y - min_y)) * scale
                pts_emb.append((ex, ey))

            pts_emb = self._resample(pts_emb, resample_step)
            if len(pts_emb) < 2:
                continue

            self._jump(*pts_emb[0])
            self._tie_in(pts_emb[0], step=4)
            for p in pts_emb[1:]:
                self._stitch(*p)
            self._tie_out(pts_emb[-1], step=4)
            self._trim(*pts_emb[-1])
            total += len(pts_emb)
        return total

    # ---------- dolgu (hatch) ----------
    def _draw_hatch(self, mask, min_x, min_y, src_w, src_h,
                    scale, ox, oy, hatch_step_px, stitch_step_emb):
        h, w = mask.shape
        total = 0
        for row in range(0, h, hatch_step_px):
            line = mask[row, :]
            inside = False
            segs = []
            start = 0
            for col in range(w):
                val = line[col] > 0
                if val and not inside:
                    inside = True
                    start = col
                if not val and inside:
                    inside = False
                    segs.append((start, col - 1))
            if inside:
                segs.append((start, w - 1))

            for x0, x1 in segs:
                if x1 <= x0:
                    continue
                ex0 = ox + (x0 - min_x) * scale
                ey0 = oy + (src_h - (row - min_y)) * scale
                ex1 = ox + (x1 - min_x) * scale
                ey1 = oy + (src_h - (row - min_y)) * scale
                pts = [(ex0, ey0), (ex1, ey1)]
                pts = self._resample(pts, stitch_step_emb)
                if len(pts) < 2:
                    continue
                self._jump(*pts[0])
                self._tie_in(pts[0], step=4)
                for p in pts[1:]:
                    self._stitch(*p)
                self._tie_out(pts[-1], step=4)
                self._trim(*pts[-1])
                total += len(pts)
        return total

    # ---------- renk kümelemesi ----------
    def _segment_colors(self, img_rgb, k):
        h, w, _ = img_rgb.shape
        data = img_rgb.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        K = max(1, min(k, 6))
        _, labels, centers = cv2.kmeans(data, K, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
        labels = labels.reshape((h, w))
        centers = centers.astype(np.uint8)
        bg_idx = int(np.argmax(centers.sum(axis=1)))  # en parlak arka plan
        areas = []
        for i in range(K):
            area = int((labels == i).sum())
            areas.append((area, i))
        areas.sort(reverse=True)
        ordered = [i for _, i in areas if i != bg_idx] + [bg_idx]
        return labels, centers, ordered, bg_idx

    # ---------- ana iş ----------
    def logo_isle(
        self,
        image_path="logo.png",
        baslangic_x=0,
        baslangic_y=0,
        genislik=15,
        yukseklik=5,
        birim="cm",
        n_colors=3,
        min_area_px=50,
        outline=True,
        fill=True,
        hatch_step_mm=0.7,
        stitch_step_mm=0.6,
        simplify_epsilon=0.4,
        min_contour_len=2,
    ):
        # Birim → emb (0.1 mm)
        k = 100 if birim == "cm" else 10 if birim == "mm" else 100
        target_w = genislik * k
        target_h = yukseklik * k
        bx = baslangic_x * k
        by = baslangic_y * k

        img = Image.open(image_path).convert("RGB")
        rgb = np.array(img)

        labels, centers, ordered, bg_idx = self._segment_colors(rgb, n_colors)
        print(f"🎨 Bulunan küme sayısı: {len(centers)}, arka plan kümesi: {bg_idx}")

        color_masks = []
        for idx in ordered:
            if idx == bg_idx:
                continue
            mask = (labels == idx).astype(np.uint8) * 255
            area = int(mask.sum() // 255)
            if area < min_area_px:
                continue
            color_masks.append((idx, mask, area))

        if not color_masks:
            print("⚠️ Dikiş atılacak renk bulunamadı.")
            return

        combined = np.zeros_like(color_masks[0][1], dtype=np.uint8)
        for _, mk, _ in color_masks:
            combined |= (mk > 0).astype(np.uint8)
        pts_y, pts_x = np.nonzero(combined)
        min_x, max_x = pts_x.min(), pts_x.max()
        min_y, max_y = pts_y.min(), pts_y.max()
        src_w = max_x - min_x
        src_h = max_y - min_y
        if src_w < 1 or src_h < 1:
            print("⚠️ Görüntü boyutu geçersiz.")
            return

        scale = min(target_w / src_w, target_h / src_h)
        ox = bx + (target_w - src_w * scale) / 2.0
        oy = by + (target_h - src_h * scale) / 2.0

        print(f"🖼️ Logo: {image_path}")
        print(f"📦 Hedef: {genislik} x {yukseklik} {birim}")
        print(f"🔧 Ölçek: {scale / k:.2f} {birim}")

        stitch_step_emb = max(1, stitch_step_mm * 10)
        hatch_step_px = max(1, int(round(hatch_step_mm * 10 / scale)))

        # İplikleri ekle
        for i in range(min(len(THREAD_PALETTE), len(color_masks))):
            name, rgb_t = THREAD_PALETTE[i]
            th = pyembroidery.EmbThread()
            set_thread_color(th, rgb_t)
            th.description = name
            th.catalog_number = name
            self.pattern.add_thread(th)

        # Renk blokları
        color_block = 0
        for idx, mask, area in color_masks:
            col_rgb = centers[idx].tolist()
            name = THREAD_PALETTE[color_block % len(THREAD_PALETTE)][0]
            print(f"🧵 Renk {color_block+1}: küme {idx}, alan {area}px, renk {col_rgb}, isim {name}")

            if color_block > 0:
                self._color_change()

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            n_fill = 0
            if fill:
                n_fill = self._draw_hatch(
                    mask=mask,
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

            n_out = 0
            if outline:
                n_out = self._draw_outline(
                    contours=contours,
                    min_x=min_x,
                    min_y=min_y,
                    src_w=src_w,
                    src_h=src_h,
                    scale=scale,
                    ox=ox,
                    oy=oy,
                    resample_step=stitch_step_emb,
                    simplify_eps=simplify_epsilon,
                    min_len=min_contour_len,
                )

            print(f"   ➜ Dolgu dikiş: {n_fill}, Kontur dikiş: {n_out}")
            color_block += 1

        self.pattern.end()

    # ---------- önizleme ----------
    def onizleme(self, ad):
        plt.figure(figsize=(10, 6))
        plt.axis("equal")
        plt.axis("off")
        xs, ys = [], []
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd in (pyembroidery.JUMP, pyembroidery.TRIM, pyembroidery.COLOR_CHANGE, pyembroidery.STOP):
                if xs:
                    plt.plot(xs, ys, color="navy", linewidth=0.6, alpha=0.9)
                xs, ys = [], []
            elif cmd == pyembroidery.STITCH:
                xs.append(s[0])
                ys.append(s[1])
        if xs:
            plt.plot(xs, ys, color="navy", linewidth=0.6, alpha=0.9)
        plt.title(ad, fontsize=12)
        plt.savefig(f"{ad}.jpg", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"🖼️ Önizleme → {ad}.jpg")

    # ---------- kaydet ----------
    def kaydet(self, isim):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = isim.replace(" ", "_").lower()
        pyembroidery.write_dst(self.pattern, f"{ad}.dst")
        pyembroidery.write_jef(self.pattern, f"{ad}.jef")
        self.onizleme(ad)
        print(f"✅ Hazır: {ad}.dst  /  {ad}.jef")


# ------------------------------------------------------------
# ÇALIŞTIRMA
# ------------------------------------------------------------
if __name__ == "__main__":
    m = LogoNakis()

    LOGO_DOSYA   = "logo.png"
    BIRIM        = "cm"
    GENISLIK_CM  = 10
    YUKSEKLIK_CM = 7
    BAS_X        = 0
    BAS_Y        = 0

    N_COLORS         = 3
    MIN_AREA_PX      = 50
    OUTLINE          = True
    FILL             = True
    HATCH_STEP_MM    = 0.3
    STITCH_STEP_MM   = 0.4
    SIMPLIFY_EPS     = 0.2
    MIN_CONTOUR_LEN  = 2

    m.logo_isle(
        image_path=LOGO_DOSYA,
        baslangic_x=BAS_X,
        baslangic_y=BAS_Y,
        genislik=GENISLIK_CM,
        yukseklik=YUKSEKLIK_CM,
        birim=BIRIM,
        n_colors=N_COLORS,
        min_area_px=MIN_AREA_PX,
        outline=OUTLINE,
        fill=FILL,
        hatch_step_mm=HATCH_STEP_MM,
        stitch_step_mm=STITCH_STEP_MM,
        simplify_epsilon=SIMPLIFY_EPS,
        min_contour_len=MIN_CONTOUR_LEN,
    )

    m.kaydet("logo")
