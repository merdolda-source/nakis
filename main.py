import pyembroidery
import math
import matplotlib.pyplot as plt

class SaglamNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "NetBlokYazi"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def sargi_cizgi_yap(self, x1, y1, x2, y2, kalinlik):
        """
        Bu fonksiyon, iki nokta arasına (x1,y1 -> x2,y2) 
        kalın bir sargı (satin stitch) çeker.
        """
        dist = self._mesafe(x1, y1, x2, y2)
        if dist == 0: return

        # Dikiş Sıklığı (Düşük sayı = Daha Sıkı)
        # 3.0 idealdir. Çok sıkı istersen 2.5 yapabilirsin.
        SIKLIK = 3.0 
        
        dx = x2 - x1
        dy = y2 - y1
        
        # Çizgiye dik olan vektörü bul (Kalınlık vermek için)
        nx = -dy / dist * (kalinlik / 2)
        ny = dx / dist * (kalinlik / 2)
        
        # Adım sayısını hesapla
        steps = int(dist // SIKLIK)
        if steps < 2: steps = 2

        # 1. Başlangıç noktasına atla (JUMP)
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, int(x1), int(y1))
        
        # 2. Alt Dikiş (Underlay) - İpin kumaşa tutunması için
        # Önce sona git, sonra başa dön (İskelet oluştur)
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # 3. Sargı Dikişi (ZigZag) - Esas Kalınlık
        for i in range(steps + 1):
            t = i / steps
            # Çizgi üzerindeki merkez nokta
            cx = x1 + (dx * t)
            cy = y1 + (dy * t)
            
            # Sağa ve sola zig-zag at
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))
        
        # İp kesme veya sabitleme için bitiş noktasına dikiş
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x2), int(y2))

    def get_alfabe(self):
        """
        GARANTİLİ BLOK ALFABE
        Her harf, basit çizgi koordinatlarından oluşur.
        (x1, y1, x2, y2) -> Çizginin başı ve sonu
        """
        return {
            # BÜYÜK HARFLER
            'D': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 1,0.5), (1,0.5, 0.7,0), (0.7,0, 0,0)],
            'I': [(0.5,0, 0.5,1)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.25,0.4, 0.75,0.4)],
            'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.4,0.5, 0.8,0)],
            'B': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'K': [(0,0, 0,1), (0.8,1, 0,0.4), (0,0.4, 0.8,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.7,0.5)],
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            
            # KÜÇÜK HARFLER (Düzleştirilmiş ve Basitleştirilmiş)
            'a': [(0,0, 1,0), (1,0, 1,0.7), (1,0.7, 0,0.7), (0,0.7, 0,0), (0,0.35, 1,0.35)],
            'b': [(0,0, 0,1), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'ı': [(0.5,0, 0.5,0.7)], # Noktasız
            'i': [(0.5,0, 0.5,0.7), (0.5,0.9, 0.5,1.0)], # Noktalı (Üstte küçük çizgi)
            'r': [(0,0, 0,0.7), (0,0.6, 0.5,0.7), (0.5,0.7, 0.8,0.7)],
            'k': [(0,0, 0,1), (0.8,0.7, 0,0.3), (0,0.3, 0.8,0)],
            
            # SAYILAR
            '0': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            '1': [(0.3,0.8, 0.5,1), (0.5,1, 0.5,0), (0.2,0, 0.8,0)],
            '2': [(0,0.8, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0)],
            '3': [(0,1, 1,1), (1,1, 0.5,0.5), (0.5,0.5, 1,0), (1,0, 0,0)],
            '4': [(0.8,0, 0.8,1), (0.8,1, 0,0.4), (0,0.4, 1,0.4)],
            '5': [(1,1, 0,1), (0,1, 0,0.6), (0,0.6, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            '6': [(1,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0,0.5)],
            '7': [(0,1, 1,1), (1,1, 0.4,0)],
            '8': [(0,0, 1,0), (1,0, 1,1), (1,1, 0,1), (0,1, 0,0), (0,0.5, 1,0.5)],
            '9': [(1,0, 1,1), (1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5)],

            ' ': [],
            '-': [(0,0.5, 1,0.5)]
        }

    def yazdir(self, metin, cm_genislik, cm_yukseklik):
        alfabe = self.get_alfabe()
        
        # 1. Metin Uzunluğunu Hesapla (Birim cinsinden)
        toplam_uzunluk = 0
        for harf in metin:
            if harf == ' ': toplam_uzunluk += 0.5
            elif harf in 'iı1l': toplam_uzunluk += 0.4 # İnce harfler
            else: toplam_uzunluk += 0.85 # Normal harfler
            toplam_uzunluk += 0.15 # Harf arası boşluk
        
        # 2. Ölçekleme (Makine 10x çalışır)
        hedef_w = cm_genislik * 10
        hedef_h = cm_yukseklik * 10
        
        # Harf boyutu (Scale)
        # Genişliğe sığması için scale hesabı:
        scale = hedef_w / toplam_uzunluk
        
        # Eğer hesaplanan scale, yükseklikten büyükse, yüksekliğe göre sınırla
        if scale > hedef_h:
            scale = hedef_h
            
        print(f"Yazı: '{metin}' | Boyut: {scale/10:.1f}cm | Toplam En: {cm_genislik}cm")

        # 3. Yazdırma Döngüsü
        # Yazıyı ortalamak için başlangıç noktası
        curr_x = - (toplam_uzunluk * scale) / 2
        
        # Kalınlık Ayarı (Otomatik)
        # Harf büyüdükçe kalınlaşır ama 4mm'yi geçmez
        kalinlik = scale / 7
        if kalinlik < 2.0: kalinlik = 2.0
        if kalinlik > 4.5: kalinlik = 4.5

        for harf in metin:
            # Harf veritabanında var mı?
            h_kod = harf
            if harf not in alfabe:
                if harf.upper() in alfabe: h_kod = harf.upper()
                else: 
                    curr_x += 0.5 * scale
                    continue
            
            cizgiler = alfabe[h_kod]
            
            # Harf genişlik çarpanı
            w_factor = 1.0 # Normal
            if h_kod in 'iı1l': w_factor = 0.5 # İnce harfler daha dar
            
            # Çizgileri işle
            for line in cizgiler:
                lx1, ly1, lx2, ly2 = line
                
                # Koordinat Dönüşümü
                x1 = curr_x + (lx1 * scale * 0.8) # 0.8 daraltma faktörü
                y1 = ly1 * scale
                x2 = curr_x + (lx2 * scale * 0.8)
                y2 = ly2 * scale
                
                # SADE VE NET SARGI ÇİZ
                self.sargi_cizgi_yap(x1, y1, x2, y2, kalinlik)
            
            # Bir sonraki harfe geç
            curr_x += (scale * 0.8) + (scale * 0.15)

    def onizleme_yap(self, dosya_adi):
        plt.figure(figsize=(10, 4))
        plt.axis('equal'); plt.axis('off')
        
        # Sadece dikiş noktalarını çiz (JUMP çizgilerini çizme)
        stitch_x, stitch_y = [], []
        
        for s in self.pattern.stitches:
            cmd = s[2]
            if cmd == pyembroidery.STITCH:
                stitch_x.append(s[0])
                stitch_y.append(s[1])
            elif cmd == pyembroidery.JUMP:
                # JUMP gelince elindeki çizgiyi çiz ve listeyi sıfırla
                if stitch_x:
                    plt.plot(stitch_x, stitch_y, color='darkblue', linewidth=0.5, alpha=0.6)
                stitch_x, stitch_y = [], []
        
        if stitch_x:
            plt.plot(stitch_x, stitch_y, color='darkblue', linewidth=0.5, alpha=0.6)

        plt.title(f"{dosya_adi} - Temiz Onizleme")
        plt.savefig(f"{dosya_adi}_preview.png", dpi=150, bbox_inches='tight')
        print(f"RESİM OLUŞTU: {dosya_adi}_preview.png")

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad = dosya_adi.replace(" ", "_").replace("ı", "i").lower()
        
        pyembroidery.write(self.pattern, f"{ad}.dst")
        pyembroidery.write(self.pattern, f"{ad}.jef")
        
        self.onizleme_yap(ad)
        print(f"✅ DOSYALAR HAZIR: {ad}.jef")

# ==========================================
# AYARLAR (Burayı değiştirmen yeterli)
# ==========================================
if __name__ == "__main__":
    makine = SaglamNakis()
    
    # İSTEDİĞİN METİN VE BOYUTLAR
    YAZI = "Diyarbakır 21"
    
    # 9cm Genişlik, 4cm Yükseklik kutusuna sığdırır
    GENISLIK_CM = 9  
    YUKSEKLIK_CM = 4 

    makine.yazdir(YAZI, GENISLIK_CM, YUKSEKLIK_CM)
    makine.kaydet("Diyarbakir_21")
