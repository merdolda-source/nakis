import pyembroidery
import math
import matplotlib.pyplot as plt

class ProfesyonelNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "UltraSargi"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def tam_sargi_yap(self, x1, y1, x2, y2, kalinlik_mm):
        # 1mm = 10 birim
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0: return

        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # === 1. ALT DOLGU (UNDERLAY) ===
        kucultme = 0.7
        nx_alt = nx * kucultme
        ny_alt = ny * kucultme

        self.pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        steps_alt = int(dist // 30) + 1
        for i in range(steps_alt + 1):
             self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1 + dx*i/steps_alt), int(y1 + dy*i/steps_alt))
        
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # === 2. SÜPER SIKI SARGI (TOP SATIN) ===
        # Yoğunluk: 3 (Çok sıkı, kumaş görünmez)
        YOGUNLUK = 3 
        
        steps_sargi = int(dist // YOGUNLUK)
        if steps_sargi < 2: steps_sargi = 2

        for i in range(steps_sargi + 1):
            ratio = i / steps_sargi
            cx = x1 + (dx * ratio)
            cy = y1 + (dy * ratio)
            
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))

    def isim_yaz(self, metin, baslangic_x, baslangic_y, harf_boyu_mm):
        mevcut_x = baslangic_x
        scale = harf_boyu_mm * 10
        bosluk = scale * 0.25 

        # --- ALFABE ---
        alfabe = {
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.2,0.4, 0.8,0.4)],
            'B': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.7,0.5), (0.7,0.5, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'C': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0)],
            'D': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 1,0.5), (1,0.5, 0.7,0), (0.7,0, 0,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.8,0.5)],
            'F': [(1,1, 0,1), (0,1, 0,0), (0,0.5, 0.8,0.5)],
            'G': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5)],
            'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
            'I': [(0.5,0, 0.5,1)],
            'J': [(0.5,1, 0.5,0.2), (0.5,0.2, 0,0)],
            'K': [(0,0, 0,1), (1,1, 0,0.5), (0,0.5, 1,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'M': [(0,0, 0,1), (0,1, 0.5,0), (0.5,0, 1,1), (1,1, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
            'O': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            'P': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5)],
            'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.5,0.5, 1,0)],
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            'U': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1)],
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
            ' ': [], 
            '-': [(0,0.5, 1,0.5)]
        }

        sargi_kalinligi = harf_boyu_mm * 0.13 # Tok görünüm
        if sargi_kalinligi < 2.5: sargi_kalinligi = 2.5

        for harf in metin.upper():
            if harf == " ":
                mevcut_x += scale * 0.6
                continue
            
            if harf not in alfabe: continue

            cizgiler = alfabe[harf]
            for (lx1, ly1, lx2, ly2) in cizgiler:
                gx1 = mevcut_x + (lx1 * scale * 0.7)
                gy1 = baslangic_y + (ly1 * scale)
                gx2 = mevcut_x + (lx2 * scale * 0.7)
                gy2 = baslangic_y + (ly2 * scale)
                self.tam_sargi_yap(gx1, gy1, gx2, gy2, sargi_kalinligi)

            mevcut_x += (scale * 0.7) + bosluk

    def onizleme_olustur(self, dosya_adi):
        """
        Dikişleri JPG olarak çizer ve kaydeder.
        """
        print("JPG Önizleme oluşturuluyor...")
        stitches = self.pattern.stitches
        
        plt.figure(figsize=(15, 5))
        plt.axis('equal') # Harfler uzamasın diye
        plt.axis('off')   # Kenarlıkları kaldır
        
        current_x, current_y = 0, 0
        
        # Dikişleri parçalara ayır (JUMP olan yerlerde çizgiyi kopar)
        x_list = []
        y_list = []

        for stitch in stitches:
            x, y = stitch[0], stitch[1]
            cmd = stitch[2]
            
            # Eğer atlama (JUMP) veya kesme (TRIM) varsa, önceki biriken çizgiyi çiz
            if cmd == pyembroidery.JUMP or cmd == pyembroidery.TRIM:
                if x_list:
                    # Koyu mavi renk, hafif şeffaf (gerçek iplik gibi dursun)
                    plt.plot(x_list, y_list, color='darkblue', linewidth=0.5, alpha=0.8)
                    x_list = []
                    y_list = []
                current_x, current_y = x, y
            
            elif cmd == pyembroidery.STITCH:
                x_list.append(x)
                y_list.append(y)
                current_x, current_y = x, y

        # Son kalan parçayı çiz
        if x_list:
            plt.plot(x_list, y_list, color='darkblue', linewidth=0.5, alpha=0.8)

        plt.title(f"{dosya_adi} - Nakis Onizleme", fontsize=15)
        plt.savefig(f"{dosya_adi}_onizleme.jpg", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ RESİM ÜRETİLDİ: {dosya_adi}_onizleme.jpg")

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad_temiz = dosya_adi.replace(" ", "_").lower()
        
        # Nakış Dosyaları
        pyembroidery.write(self.pattern, f"{ad_temiz}.dst")
        pyembroidery.write(self.pattern, f"{ad_temiz}.jef")
        
        # JPG Resim Dosyası (Bu yeni eklenen özellik)
        self.onizleme_olustur(ad_temiz)
        
        print(f"✅ NAKIŞ DOSYALARI HAZIR: {ad_temiz}.jef")

# ==========================================
# MÜŞTERİ PANELİ
# ==========================================
if __name__ == "__main__":
    
    makine = ProfesyonelNakis()

    # MÜŞTERİ BİLGİLERİ:
    MUSTERI_ISMI = "MEHMET"  
    ISTENEN_BOYUT = 100      # mm
    
    # Ortalama Hesabı
    baslama_yeri = len(MUSTERI_ISMI) * ISTENEN_BOYUT * -0.35
    
    # İşle
    makine.isim_yaz(MUSTERI_ISMI, baslama_yeri, 0, ISTENEN_BOYUT)
    makine.kaydet(MUSTERI_ISMI)
