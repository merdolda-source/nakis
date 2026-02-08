#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG → Nakış (DST/JEF) – Siyah arka planı otomatik atla, sadece desene odaklan
Tatlı Durağı logosu için optimize edilmiş versiyon.

Gerekenler:
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
    raise ImportError("OpenCV yok. Kurun: pip install opencv-python-headless") from e


# Tatlı Durağı logosu için özel iplik paleti (Kırmızı, Altın, Beyaz)
THREAD_PALETTE = [
    ("DarkRed",    (139, 0, 0)),       # Koyu kırmızı - ana zemin
    ("Gold",       (218, 165, 32)),    # Altın - süslemeler ve çerçeve
    ("White",      (255, 255, 255)),   # Beyaz - yazı
    ("Maroon",     (128, 0, 0)),       # Bordo - detaylar
    ("DarkGold",   (184, 134, 11)),    # Koyu altın
]


def set_thread_color(thread: pyembroidery.EmbThread, rgb):
    """pyembroidery sürümleri için renk ataması."""
    r, g, b = rgb
    if hasattr(thread, "set_color"):
        try:
            thread.set_color(r, g, b)
            return
        except Exception:
            pass
    thread.red = r
    thread.green = g
    thread.blue = b
    thread.color = (int(r) << 16) | (int(g) << 8) | int(b)


def is_black_or_dark(rgb, threshold=50):
    """Bir rengin siyah/çok koyu olup olmadığını kontrol et."""
    return np.mean(rgb) <= threshold


def color_distance(c1, c2):
    """İki renk arasındaki Öklid mesafesi."""
    return np.sqrt(np.sum((np.array(c1, dtype=float) - np.array(c2, dtype=float)) ** 2))


def find_best_thread(rgb, palette):
    """Verilen RGB için en yakın iplik rengini bul."""
    best_idx = 0
    best_dist = float('inf')
    for i, (name, pal_rgb) in enumerate(palette):
        dist = color_distance(rgb, pal_rgb)
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    return best_idx


class LogoNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()

    # ---------- yardımcılar ----------
    def _resample(self, pts, step):
        """Noktaları belirli adım aralığında yeniden örnekle."""
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
        direction = 1  # Alternatif yön için
        
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

            # Alternatif yönde dikiş (daha düzgün dolgu)
            if direction < 0:
                segs = segs[::-1]
                segs = [(x1, x0) for x0, x1 in segs]
            direction *= -1

            for x0, x1 in segs:
                if abs(x1 - x0) < 2:
                    continue
                ex0 = ox + (min(x0, x1) - min_x) * scale
                ey0 = oy + (src_h - (row - min_y)) * scale
                ex1 = ox + (max(x0, x1) - min_x) * scale
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

    # ---------- siyah arka planı otomatik algıla ve atla ----------
    def _segment_colors_ignore_black(self, img_rgb, k, black_threshold=50):
        """
        K-means ile renk segmentasyonu yap, siyah/koyu renkleri otomatik atla.
        
        Returns:
            color_masks: [(cluster_idx, mask, area, center_rgb), ...]
            bg_mask: arka plan maskesi
        """
        h, w, _ = img_rgb.shape
        data = img_rgb.reshape((-1, 3)).astype(np.float32)
        
        # K-means kümeleme
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
        K = max(2, min(k, 8))
        _, labels, centers = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        labels = labels.reshape((h, w))
        centers = centers.astype(np.uint8)

        print(f"\n{'='*60}")
        print(f"🎨 K-means Kümeleme Sonuçları (K={K})")
        print(f"{'='*60}")

        # Her kümeyi analiz et
        valid_masks = []
        bg_mask = np.zeros((h, w), dtype=np.uint8)
        
        for i in range(K):
            mask = (labels == i).astype(np.uint8) * 255
            area = int(mask.sum() // 255)
            center_rgb = centers[i].tolist()
            brightness = np.mean(center_rgb)
            
            # Siyah/koyu mu kontrol et
            is_dark = brightness <= black_threshold
            
            status = "⛔ ATLA (Siyah/Koyu)" if is_dark else "✅ KULLAN"
            print(f"  Küme {i}: RGB={center_rgb}, Parlaklık={brightness:.1f}, Alan={area}px → {status}")
            
            if is_dark:
                bg_mask |= mask
            else:
                if area > 100:  # Minimum alan filtresi
                    valid_masks.append((i, mask, area, center_rgb))
        
        # Alana göre sırala (büyükten küçüğe)
        valid_masks.sort(key=lambda x: x[2], reverse=True)
        
        print(f"\n📊 Toplam {len(valid_masks)} renk işlenecek")
        print(f"{'='*60}\n")
        
        return valid_masks, bg_mask

    # ---------- ana işleme ----------
    def logo_isle(
        self,
        image_path="logo.png",
        baslangic_x=0,
        baslangic_y=0,
        genislik=15,
        yukseklik=5,
        birim="cm",
        n_colors=4,
        min_area_px=100,
        outline=True,
        fill=True,
        hatch_step_mm=0.6,
        stitch_step_mm=0.5,
        simplify_epsilon=1.0,
        min_contour_len=3,
        black_threshold=50,
    ):
        """
        Logo görüntüsünü nakış desenine dönüştür.
        Siyah arka plan otomatik algılanır ve atlanır.
        """
        # Birim dönüşümü (emb birimi = 0.1 mm)
        k = 100 if birim == "cm" else 10 if birim == "mm" else 100
        target_w = genislik * k
        target_h = yukseklik * k
        bx = baslangic_x * k
        by = baslangic_y * k

        # Görüntüyü yükle
        print(f"\n🖼️ Logo yükleniyor: {image_path}")
        img = Image.open(image_path).convert("RGB")
        rgb = np.array(img)
        print(f"📐 Görüntü boyutu: {rgb.shape[1]} x {rgb.shape[0]} piksel")

        # Renk segmentasyonu (siyah otomatik atlanır)
        color_masks, bg_mask = self._segment_colors_ignore_black(
            rgb, n_colors, black_threshold=black_threshold
        )

        if not color_masks:
            print("⚠️ İşlenecek renk bulunamadı! Siyah eşiğini düşürmeyi deneyin.")
            return

        # Sadece desen alanını hesapla (siyah hariç)
        combined = np.zeros((rgb.shape[0], rgb.shape[1]), dtype=np.uint8)
        for _, mk, _, _ in color_masks:
            combined |= (mk > 0).astype(np.uint8)
        
        pts_y, pts_x = np.nonzero(combined)
        if len(pts_y) == 0:
            print("⚠️ Desen bulunamadı!")
            return
            
        min_x, max_x = pts_x.min(), pts_x.max()
        min_y, max_y = pts_y.min(), pts_y.max()
        src_w = max_x - min_x
        src_h = max_y - min_y
        
        if src_w < 1 or src_h < 1:
            print("⚠️ Desen boyutu geçersiz!")
            return

        # Ölçekleme hesapla
        scale = min(target_w / src_w, target_h / src_h)
        ox = bx + (target_w - src_w * scale) / 2.0
        oy = by + (target_h - src_h * scale) / 2.0

        print(f"\n📦 Hedef Boyut: {genislik} x {yukseklik} {birim}")
        print(f"🔧 Desen Alanı: {src_w} x {src_h} piksel")
        print(f"📏 Ölçek Faktörü: {scale:.4f}")
        print(f"📍 Gerçek Boyut: {src_w * scale / k:.2f} x {src_h * scale / k:.2f} {birim}")

        stitch_step_emb = max(1, stitch_step_mm * 10)
        hatch_step_px = max(1, int(round(hatch_step_mm * 10 / scale)))

        # İplikleri pattern'e ekle
        for i in range(min(len(THREAD_PALETTE), len(color_masks))):
            name, rgb_t = THREAD_PALETTE[i]
            th = pyembroidery.EmbThread()
            set_thread_color(th, rgb_t)
            th.description = name
            th.catalog_number = name
            self.pattern.add_thread(th)

        print(f"\n🧵 Dikiş Başlıyor...")
        print(f"{'='*60}")

        # Her renk için işle
        total_stitches = 0
        for color_idx, (cluster_idx, mask, area, center_rgb) in enumerate(color_masks):
            # En yakın iplik rengini bul
            thread_idx = find_best_thread(center_rgb, THREAD_PALETTE)
            thread_name = THREAD_PALETTE[thread_idx][0]
            
            print(f"\n🎨 Renk {color_idx + 1}/{len(color_masks)}:")
            print(f"   Küme: {cluster_idx}, RGB: {center_rgb}")
            print(f"   İplik: {thread_name}, Alan: {area} piksel")

            if color_idx > 0:
                self._color_change()

            # Konturları bul
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Dolgu dikiş
            n_fill = 0
            if fill and area >= min_area_px:
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

            # Kontur dikiş
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

            print(f"   ✅ Dolgu: {n_fill} dikiş, Kontur: {n_out} dikiş")
            total_stitches += n_fill + n_out

        self.pattern.end()
        
        print(f"\n{'='*60}")
        print(f"📊 TOPLAM: {total_stitches} dikiş")
        print(f"{'='*60}")

    # ---------- önizleme ----------
    def onizleme(self, ad):
        """Dikiş deseninin önizlemesini oluştur."""
        plt.figure(figsize=(12, 8))
        plt.axis("equal")
        plt.axis("off")
        
        colors = ['darkred', 'goldenrod', 'white', 'maroon', 'darkgoldenrod']
        current_color_idx = 0
        
        xs, ys = [], []
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd == pyembroidery.COLOR_CHANGE:
                if xs:
                    plt.plot(xs, ys, color=colors[current_color_idx % len(colors)], 
                            linewidth=0.5, alpha=0.8)
                xs, ys = [], []
                current_color_idx += 1
            elif cmd in (pyembroidery.JUMP, pyembroidery.TRIM, pyembroidery.STOP):
                if xs:
                    plt.plot(xs, ys, color=colors[current_color_idx % len(colors)], 
                            linewidth=0.5, alpha=0.8)
                xs, ys = [], []
            elif cmd == pyembroidery.STITCH:
                xs.append(s[0])
                ys.append(s[1])
        
        if xs:
            plt.plot(xs, ys, color=colors[current_color_idx % len(colors)], 
                    linewidth=0.5, alpha=0.8)
        
        plt.gca().set_facecolor('black')
        plt.title(f"{ad} - Nakış Önizleme", fontsize=14, color='white')
        plt.savefig(f"{ad}_preview.png", dpi=300, bbox_inches="tight", 
                   facecolor='black', edgecolor='none')
        plt.close()
        print(f"\n🖼️ Önizleme kaydedildi: {ad}_preview.png")

    # ---------- kaydet ----------
    def kaydet(self, isim):
        """Pattern'i DST ve JEF formatlarında kaydet."""
        self.pattern = self.pattern.get_normalized_pattern()
        ad = isim.replace(" ", "_").lower()
        
        # DST kaydet
        pyembroidery.write_dst(self.pattern, f"{ad}.dst")
        print(f"💾 DST kaydedildi: {ad}.dst")
        
        # JEF kaydet
        pyembroidery.write_jef(self.pattern, f"{ad}.jef")
        print(f"💾 JEF kaydedildi: {ad}.jef")
        
        # Önizleme oluştur
        self.onizleme(ad)
        
        print(f"\n✅ İşlem tamamlandı!")


# ============================================================
# ÇALIŞTIRMA
# ============================================================
if __name__ == "__main__":
    
    m = LogoNakis()

    # -------------------- AYARLAR --------------------
    
    LOGO_DOSYA = "logo.png"      # Logo dosyası
    
    # Boyut ayarları
    BIRIM = "cm"
    GENISLIK = 15                # Genişlik (cm)
    YUKSEKLIK = 5                # Yükseklik (cm)  
    BAS_X = 0                    # Başlangıç X
    BAS_Y = 0                    # Başlangıç Y
    
    # Renk ve segmentasyon
    N_COLORS = 4                 # Algılanacak renk sayısı
    BLACK_THRESHOLD = 60         # Siyah eşiği (0-255, bu değerin altı siyah sayılır)
    MIN_AREA_PX = 100            # Minimum alan (piksel)
    
    # Dikiş ayarları
    OUTLINE = True               # Kontur dikişi
    FILL = True                  # Dolgu dikişi
    HATCH_STEP_MM = 0.6          # Dolgu satır aralığı (mm)
    STITCH_STEP_MM = 0.5         # Dikiş adım uzunluğu (mm)
    SIMPLIFY_EPS = 1.0           # Kontur sadeleştirme
    MIN_CONTOUR_LEN = 3          # Minimum kontur noktası
    
    # -------------------------------------------------

    print("\n" + "="*60)
    print("🧵 TATLI DURAĞI LOGO NAKİŞ DÖNÜŞTÜRÜCÜ")
    print("="*60)
    print("⚙️ Siyah arka plan otomatik algılanacak ve atlanacak")
    print(f"⚙️ Siyah eşiği: {BLACK_THRESHOLD} (RGB ortalaması)")
    
    m.logo_isle(
        image_path=LOGO_DOSYA,
        baslangic_x=BAS_X,
        baslangic_y=BAS_Y,
        genislik=GENISLIK,
        yukseklik=YUKSEKLIK,
        birim=BIRIM,
        n_colors=N_COLORS,
        min_area_px=MIN_AREA_PX,
        outline=OUTLINE,
        fill=FILL,
        hatch_step_mm=HATCH_STEP_MM,
        stitch_step_mm=STITCH_STEP_MM,
        simplify_epsilon=SIMPLIFY_EPS,
        min_contour_len=MIN_CONTOUR_LEN,
        black_threshold=BLACK_THRESHOLD,
    )

    m.kaydet("tatli_duragi")
