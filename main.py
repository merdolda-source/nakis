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

        # Vektör hesaplamaları (Dik açı)
        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # === 1. BAŞLANGIÇ (JUMP) ===
        # Örümcek ağı olmasın diye buraya atlama koyuyoruz
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1), int(y1))

        # === 2. ALT DOLGU (UNDERLAY) ===
        # Kumaşı tutması için zemine dikiş atar
        kucultme = 0.7
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))
        
        steps_alt = int(dist // 30) + 1
        for i in range(steps_alt + 1):
             self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1 + dx*i/steps_alt), int(y1 + dy*i/steps_alt))
        
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # === 3. SÜPER SIKI SARGI (TOP SATIN) ===
        # Yoğunluk: 3 (Çok sıkı, kumaş görünmez)
        YOGUNLUK = 3.0 
        
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
        
        # Bitiş noktasına sabitleme
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))

    def _harf_veritabani(self):
        """
        GELİŞTİRİLMİŞ FULL ALFABE (Senin istediğin kalın tarzda)
        """
        return {
            # BÜYÜK HARFLER
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.2,0.4, 0.8,0.4)],
            'B': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.7,0.5), (0.7,0.5, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'C': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0)],
            'Ç': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0.5,0, 0.5,-0.3)],
            'D': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 1,0.5), (1,0.5, 0.7,0), (0.7,0, 0,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.8,0.5)],
            'F': [(1,1, 0,1), (0,1, 0,0), (0,0.5, 0.8,0.5)],
            'G': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5)],
            'Ğ': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5), (0.2,1.2, 0.8,1.2)],
            'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
            'I': [(0.5,0, 0.5,1)],
            'İ': [(0.5,0, 0.5,0.65), (0.5,0.85, 0.5,1)],
            'J': [(0.6,1, 0.6,0.2), (0.6,0.2, 0,0)],
            'K': [(0,0, 0,1), (1,1, 0,0.5), (0,0.5, 1,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'M': [(0,0, 0,1), (0,1, 0.5,0), (0.5,0, 1,1), (1,1, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
            'O': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            'Ö': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0), (0.2,1.2, 0.2,1.3), (0.8,1.2, 0.8,1.3)],
            'P': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5)],
            'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.5,0.5, 1,0)],
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'Ş': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0), (0.5,0, 0.5,-0.3)],
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            'U': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1)],
            'Ü': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1), (0.2,1.2, 0.2,1.3), (0.8,1.2, 0.8,1.3)],
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
            
            # KÜÇÜK HARFLER (Senin istediğin tarzda eklendi)
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

            ' ': [], '-': [(0,0.5, 1,0.5)], '.': [(0.4,0, 0.4,0.2)], '/': [(0,0, 1,1)]
        }

    def yazdir_ve_olcekle(self, metin, genislik_cm, yukseklik_cm):
        """
        Metni 9x4 cm kutusuna sığdırır.
        """
        alfabe = self._harf_veritabani()
        
        # 1. Metnin doğal genişliğini hesapla
        toplam_birim = 0
        for h in metin:
            if h == ' ': toplam_birim += 0.5
            elif h in 'iı1l': toplam_birim += 0.4
            else: toplam_birim += 0.85 
            toplam_birim += 0.15 # Boşluk
        
        # 2. Ölçekleme (Scale) Hesabı
        hedef_w = genislik_cm * 10
        hedef_h = yukseklik_cm * 10
        
        # Genişliğe ve yüksekliğe göre scale hesapla, küçük olanı seç (sığdırmak için)
        scale_w = hedef_w / toplam_birim if toplam_birim > 0 else 10
        scale_h = hedef_h # Harfler 0-1 arası olduğu için direkt yükseklik
        
        # Kutuya sığması için en küçük ölçeği al
        scale = min(scale_w, scale_h)
        
        # Kalınlık ayarı (Otomatik)
        kalinlik = scale / 8
        if kalinlik < 2.0: kalinlik = 2.0
        if kalinlik > 4.5: kalinlik = 4.5

        print(f"Yazı: '{metin}' | Ölçek: {scale/10:.1f} cm | Kalınlık: {kalinlik:.1f}")

        # Başlangıç noktası (Ortala)
        curr_x = - (toplam_birim * scale) / 2
        baslangic_y = 0
        
        for harf in metin:
            h_key = harf
            # Veritabanında yoksa büyük harfe bak
            if h_key not in alfabe:
                if h_key.upper() in alfabe: h_key = h_key.upper()
                else: 
                    curr_x += 0.5 * scale
                    continue
            
            cizgiler = alfabe[h_key]
            
            # İnce harf genişlik ayarı
            w_factor = 0.5 if h_key in 'iı1l' else 0.85
            if h_key == ' ': w_factor = 0.5

            for line in cizgiler:
                lx1, ly1, lx2, ly2 = line
                
                # Koordinat Dönüşümü
                x1 = curr_x + (lx1 * scale * w_factor)
                y1 = baslangic_y + (ly1 * scale)
                x2 = curr_x + (lx2 * scale * w_factor)
                y2 = baslangic_y + (ly2 * scale)
                
                # SENİN SEVDİĞİN SARGI FONKSİYONU
                self.tam_sargi_yap(x1, y1, x2, y2, kalinlik)
            
            # Sonraki harfe geç
            curr_x += (scale * w_factor) + (scale * 0.15)

    def onizleme_yap(self, dosya_adi):
        plt.figure(figsize=(12, 5))
        plt.axis('equal'); plt.axis('off')
        
        x_list, y_list = [], []
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd == pyembroidery.STITCH:
                x_list.append(s[0])
                y_list.append(s[1])
            elif cmd == pyembroidery.JUMP:
                # JUMP görünmesin, sadece dikişler görünsün
                if x_list:
                    plt.plot(x_list, y_list, color='darkblue', linewidth=0.6, alpha=0.7)
                x_list, y_list = [], []
        
        if x_list: plt.plot(x_list, y_list, color='darkblue', linewidth=0.6, alpha=0.7)

        plt.title(f"{dosya_adi} - Full Sargi")
        plt.savefig(f"{dosya_adi}_onizleme.jpg", dpi=150, bbox_inches='tight')
        print(f"RESİM OLUŞTU: {dosya_adi}_onizleme.jpg")

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = dosya_adi.replace(" ", "_").replace("ı", "i").lower()
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        self.onizleme_yap(ad)
        print(f"✅ DOSYALAR HAZIR: {ad}.jef")

# ==========================================
# AYARLAR (BURAYI DEĞİŞTİR)
# ==========================================
if __name__ == "__main__":
    makine = ProfesyonelNakis()
    
    # İSTEDİĞİN YAZI VE BOYUT (CM)
    YAZI = "Diyarbakır 21" 
    GENISLIK_CM = 9
    YUKSEKLIK_CM = 4

    makine.yazdir_ve_olcekle(YAZI, GENISLIK_CM, YUKSEKLIK_CM)
    makine.kaydet("Diyarbakir_21")
