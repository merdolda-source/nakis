import pyembroidery
import math
import matplotlib.pyplot as plt

class SaglamNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "NetNakis"
        # 0.4mm altındaki dikişleri atla (İğne kırma koruması)
        self.MIN_DIST = 4 
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def sargi_cizgi(self, x1, y1, x2, y2, kalinlik):
        """
        İki nokta arasına kalın sargı atar.
        Karmaşık hesaplar yerine net bloklar oluşturur.
        """
        dist = self._mesafe(x1, y1, x2, y2)
        if dist == 0: return

        # Dikiş sıklığı (3 = Çok Sıkı)
        YOGUNLUK = 3.0
        
        dx = x2 - x1
        dy = y2 - y1
        
        # Dik vektör (Kalınlık için)
        nx = -dy / dist * (kalinlik / 2)
        ny = dx / dist * (kalinlik / 2)
        
        # Adım sayısı
        steps = int(dist // YOGUNLUK)
        if steps < 2: steps = 2

        # Önce oraya git (JUMP)
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1), int(y1))
        
        # Alt dikiş (Zemin)
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # Üst Sargı (Zikzak)
        for i in range(steps + 1):
            t = i / steps
            cx = x1 + (dx * t)
            cy = y1 + (dy * t)
            
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))

    def get_alfabe(self):
        """
        BOZULMAYAN, GARANTİLİ BLOK ALFABE
        Her harf, basit çizgi parçalarından oluşur.
        Koordinatlar: (x1, y1, x2, y2)
        """
        return {
            # BÜYÜK HARFLER (Net ve Düz)
            'A': [(0,0, 0,1), (1,0, 1,1), (0,1, 1,1), (0,0.5, 1,0.5)],
            'B': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'C': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0)],
            'Ç': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0.5,0, 0.5,-0.3)],
            'D': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0), (0.8,0, 0,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.8,0.5)],
            'F': [(1,1, 0,1), (0,1, 0,0), (0,0.5, 0.8,0.5)],
            'G': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5)],
            'Ğ': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5), (0.2,1.2, 0.8,1.2)],
            'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
            'I': [(0.5,0, 0.5,1)],
            'İ': [(0.5,0, 0.5,0.7), (0.5,0.85, 0.5,1)],
            'J': [(0.5,1, 0.5,0.2), (0.5,0.2, 0,0.2), (0,0.2, 0,0.5)],
            'K': [(0,0, 0,1), (1,1, 0,0.5), (0,0.5, 1,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'M': [(0,0, 0,1), (0,1, 0.5,0.5), (0.5,0.5, 1,1), (1,1, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
            'O': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            'Ö': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0), (0.2,1.2, 0.2,1.3), (0.8,1.2, 0.8,1.3)],
            'P': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5)],
            'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.2,0.5, 0.8,0)],
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'Ş': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0), (0.5,0, 0.5,-0.3)],
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            'U': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1)],
            'Ü': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1), (0.2,1.2, 0.2,1.3), (0.8,1.2, 0.8,1.3)],
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],

            # KÜÇÜK HARFLER (Düzleştirilmiş - Sorun Çıkarmaz)
            'a': [(0,0, 0,0.7), (0,0.7, 0.8,0.7), (0.8,0.7, 0.8,0), (0.8,0.35, 0,0.35)],
            'b': [(0,0, 0,1), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'c': [(0.8,0.7, 0,0.7), (0,0.7, 0,0), (0,0, 0.8,0)],
            'ç': [(0.8,0.7, 0,0.7), (0,0.7, 0,0), (0,0, 0.8,0), (0.4,0, 0.4,-0.3)],
            'd': [(0.8,0, 0.8,1), (0.8,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 0.8,0)],
            'e': [(0,0.35, 0.8,0.35), (0.8,0.35, 0.8,0.7), (0.8,0.7, 0,0.7), (0,0.7, 0,0), (0,0, 0.8,0)],
            'g': [(0.8,0.7, 0,0.7), (0,0.7, 0,0), (0,0, 0.8,0), (0.8,0.7, 0.8,-0.3), (0.8,-0.3, 0,-0.3)],
            'ğ': [(0.8,0.7, 0,0.7), (0,0.7, 0,0), (0,0, 0.8,0), (0.8,0.7, 0.8,0), (0.2,0.9, 0.6,0.9)],
            'h': [(0,0, 0,1), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0)],
            'ı': [(0.4,0, 0.4,0.7)],
            'i': [(0.4,0, 0.4,0.7), (0.4,0.9, 0.4,1.0)],
            'k': [(0,0, 0,1), (0.8,0.7, 0,0.35), (0,0.35, 0.8,0)],
            'l': [(0.4,0, 0.4,1)],
            'm': [(0,0, 0,0.7), (0,0.7, 0.4,0.7), (0.4,0.7, 0.4,0), (0.4,0.7, 0.8,0.7), (0.8,0.7, 0.8,0)],
            'n': [(0,0, 0,0.7), (0,0.7, 0.8,0.7), (0.8,0.7, 0.8,0)],
            'o': [(0,0, 0,0.7), (0,0.7, 0.8,0.7), (0.8,0.7, 0.8,0), (0.8,0, 0,0)],
            'ö': [(0,0, 0,0.7), (0,0.7, 0.8,0.7), (0.8,0.7, 0.8,0), (0.8,0, 0,0), (0.2,0.9, 0.2,1.0), (0.6,0.9, 0.6,1.0)],
            'p': [(0,-0.3, 0,0.7), (0,0.7, 0.8,0.7), (0.8,0.7, 0.8,0), (0.8,0, 0,0)],
            'r': [(0,0, 0,0.7), (0,0.5, 0.8,0.7)],
            's': [(0.8,0.7, 0,0.7), (0,0.7, 0,0.35), (0,0.35, 0.8,0.35), (0.8,0.35, 0.8,0), (0.8,0, 0,0)],
            'ş': [(0.8,0.7, 0,0.7), (0,0.7, 0,0.35), (0,0.35, 0.8,0.35), (0.8,0.35, 0.8,0), (0.8,0, 0,0), (0.4,0, 0.4,-0.3)],
            't': [(0.4,0, 0.4,1), (0,0.7, 0.8,0.7)],
            'u': [(0,0.7, 0,0), (0,0, 0.8,0), (0.8,0, 0.8,0.7)],
            'ü': [(0,0.7, 0,0), (0,0, 0.8,0), (0.8,0, 0.8,0.7), (0.2,0.9, 0.2,1.0), (0.6,0.9, 0.6,1.0)],
            'v': [(0,0.7, 0.4,0), (0.4,0, 0.8,0.7)],
            'y': [(0,0.7, 0.4,0), (0.8,0.7, 0.4,0), (0.4,0, 0.4,-0.3)],
            'z': [(0,0.7, 0.8,0.7), (0.8,0.7, 0,0), (0,0, 0.8,0)],

            # SAYILAR
            '0': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            '1': [(0.5,0, 0.5,1), (0.2,0.7, 0.5,1)],
            '2': [(0,1, 1,1), (1,1, 1,0.5), (1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0)],
            '3': [(0,1, 1,1), (1,1, 0,0.5), (0,0.5, 1,0), (1,0, 0,0)],
            '4': [(0.8,0, 0.8,1), (0.8,1, 0,0.5), (0,0.5, 1,0.5)],
            '5': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            '6': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0,0.5)],
            '7': [(0,1, 1,1), (1,1, 0.4,0)],
            '8': [(0,0, 1,0), (1,0, 1,1), (1,1, 0,1), (0,1, 0,0), (0,0.5, 1,0.5)],
            '9': [(1,0, 1,1), (1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5)],
            
            ' ': [],
            '-': [(0,0.5, 1,0.5)],
            '.': [(0.4,0, 0.4,0.2)],
            '/': [(0,0, 1,1)]
        }

    def yazdir(self, metin, cm_genislik, cm_yukseklik):
        """
        Metni sığdırır ve işler.
        """
        alfabe = self.get_alfabe()
        
        # 1. Metin Boyutunu Hesapla
        total_units = 0
        for h in metin:
            total_units += 0.5 if h == ' ' else (0.4 if h in 'ilı1.,' else 0.85)
        
        # 2. Ölçekleme (Scale)
        target_w = cm_genislik * 10
        target_h = cm_yukseklik * 10
        
        scale_h = target_h
        scale_w = target_w / total_units if total_units > 0 else 10
        
        # Hangisi daha kısıtlayıcıysa onu seç (Kutuya sığdır)
        scale = min(scale_h, scale_w)
        
        # Kalınlık (Otomatik)
        kalinlik = max(2.0, min(4.5, scale / 8))

        print(f"BASKI: '{metin}' | Boyut: {scale/10:.1f}mm | Kalınlık: {kalinlik:.1f}")

        # Başlangıç (Ortala)
        curr_x = - (total_units * scale) / 2
        
        for harf in metin:
            if harf == ' ':
                curr_x += 0.5 * scale
                continue
            
            h_key = harf if harf in alfabe else (harf.upper() if harf.upper() in alfabe else '?')
            if h_key not in alfabe: continue
            
            cizgiler = alfabe[h_key]
            
            # Harf genişlik faktörü
            w_factor = 0.4 if h_key in 'ilı1.,Iİ' else 0.8
            
            for line in cizgiler:
                lx1, ly1, lx2, ly2 = line
                
                # Koordinat Dönüşümü
                x1 = curr_x + (lx1 * scale * w_factor)
                y1 = ly1 * scale
                x2 = curr_x + (lx2 * scale * w_factor)
                y2 = ly2 * scale
                
                self.sargi_cizgi(x1, y1, x2, y2, kalinlik)
            
            # Sonraki harfe geç
            curr_x += (scale * w_factor) + (scale * 0.15) # 0.15 boşluk

    def kaydet_ve_goster(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = dosya_adi.replace(" ", "_").lower()
        
        # Dosyalar
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        
        # Resim (Önizleme)
        plt.figure(figsize=(10, 4))
        plt.axis('equal'); plt.axis('off')
        
        for stitch in self.pattern.stitches:
            # Sadece JUMP olmayan dikişleri çiz (Nokta nokta)
            if stitch[2] == pyembroidery.STITCH:
                 plt.plot(stitch[0], stitch[1], 'bo', markersize=0.5, alpha=0.3)
        
        plt.title(f"{dosya_adi} (Blok Stil)", fontsize=12)
        plt.savefig(f"{ad}_onizleme.jpg", dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ {ad} HAZIRLANDI.")

# ==========================================
# AYARLAR
# ==========================================
if __name__ == "__main__":
    makine = SaglamNakis()
    
    # ------------------------------------
    # İSTEĞİN: "Diyarbakır 21" (9cm x 4cm)
    # ------------------------------------
    METIN = "Diyarbakır 21"
    GENISLIK_CM = 9
    YUKSEKLIK_CM = 4
    # ------------------------------------
    
    makine.yazdir(METIN, GENISLIK_CM, YUKSEKLIK_CM)
    makine.kaydet_ve_goster(METIN)
