import pyembroidery
import math
import matplotlib.pyplot as plt

class ProfesyonelNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "UltraSargi"
        # İğne kırmayı önlemek için minimum dikiş mesafesi (mm)
        self.MIN_DIKIS_MESAFESI = 0.4 
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def guvenli_dikis_ekle(self, komut, x, y):
        """
        Bu fonksiyon, çok küçük dikişleri filtreler.
        İğnenin aynı yere defalarca batıp kırılmasını engeller.
        """
        if len(self.pattern.stitches) > 0:
            son_x = self.pattern.stitches[-1][0]
            son_y = self.pattern.stitches[-1][1]
            dist = self._mesafe(son_x, son_y, x, y)
            
            # Eğer dikiş çok kısaysa ve komut STITCH ise, atla (ATLA)
            # Ancak JUMP (atlama) ise izin ver.
            if komut == pyembroidery.STITCH and dist < (self.MIN_DIKIS_MESAFESI * 10):
                return # Dikiş ekleme, çok yakın!
        
        self.pattern.add_stitch_absolute(komut, int(x), int(y))

    def tam_sargi_yap(self, x1, y1, x2, y2, kalinlik_mm):
        # 1mm = 10 birim
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0: return

        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # === 1. ALT DOLGU (UNDERLAY) - ZEMİNİ GÜÇLENDİRİR ===
        # İğne kırılmasın diye alt dikişi biraz daha seyrek tutuyoruz
        self.guvenli_dikis_ekle(pyembroidery.JUMP, x1, y1)
        
        steps_alt = int(dist // 35) + 1 # 3.5mm adım (Rahat dikiş)
        for i in range(steps_alt + 1):
             self.guvenli_dikis_ekle(pyembroidery.STITCH, x1 + dx*i/steps_alt, y1 + dy*i/steps_alt)
        
        self.guvenli_dikis_ekle(pyembroidery.STITCH, x1, y1)

        # === 2. SÜPER SIKI SARGI (TOP SATIN) ===
        # Yoğunluk ayarı (3 = Çok sıkı). İğne kırmaması için min 3 tutuyoruz.
        YOGUNLUK = 3 
        
        steps_sargi = int(dist // YOGUNLUK)
        if steps_sargi < 2: steps_sargi = 2

        for i in range(steps_sargi + 1):
            ratio = i / steps_sargi
            cx = x1 + (dx * ratio)
            cy = y1 + (dy * ratio)
            
            if i % 2 == 0:
                self.guvenli_dikis_ekle(pyembroidery.STITCH, cx + nx, cy + ny)
            else:
                self.guvenli_dikis_ekle(pyembroidery.STITCH, cx - nx, cy - ny)

    def _harf_veritabani(self):
        # Koordinatlar: (x1, y1, x2, y2) -> Normalize (0-1 arası)
        return {
            # BÜYÜK HARFLER
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.2,0.4, 0.8,0.4)],
            'B': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.7,0.5), (0.7,0.5, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0)],
            'C': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0)],
            'Ç': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0.5,0, 0.5,-0.2)], # Çentik
            'D': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 1,0.5), (1,0.5, 0.7,0), (0.7,0, 0,0)],
            'E': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (0,0.5, 0.8,0.5)],
            'F': [(1,1, 0,1), (0,1, 0,0), (0,0.5, 0.8,0.5)],
            'G': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5)],
            'Ğ': [(1,1, 0,1), (0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0.5,0.5), (0.2,1.2, 0.8,1.2)], # Şapka
            'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
            'I': [(0.5,0, 0.5,1)],
            'İ': [(0.5,0, 0.5,0.65), (0.5,0.85, 0.5,1)], # Noktalı
            'J': [(0.6,1, 0.6,0.2), (0.6,0.2, 0,0)],
            'K': [(0,0, 0,1), (1,1, 0,0.5), (0,0.5, 1,0)],
            'L': [(0,1, 0,0), (0,0, 0.8,0)],
            'M': [(0,0, 0,1), (0,1, 0.5,0), (0.5,0, 1,1), (1,1, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
            'O': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0)],
            'Ö': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0), (0.3,1.2, 0.3,1.3), (0.7,1.2, 0.7,1.3)], # Noktalar
            'P': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5)],
            'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.5,0.5, 1,0)],
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'Ş': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0), (0.5,0, 0.5,-0.2)], # Çentik
            'T': [(0.5,0, 0.5,1), (0,1, 1,1)],
            'U': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1)],
            'Ü': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,1), (0.3,1.2, 0.3,1.3), (0.7,1.2, 0.7,1.3)], # Noktalar
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
            
            # KÜÇÜK HARFLER (Basitleştirilmiş Modern Stil)
            'a': [(0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0,0.5), (0,0.5, 0,0)], 
            'b': [(0,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0,0.5)],
            'c': [(1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0)],
            'ç': [(1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0), (0.5,0, 0.5,-0.2)],
            'd': [(1,1, 1,0), (1,0, 0,0), (0,0, 0,0.5), (0,0.5, 1,0.5)],
            'e': [(0,0.25, 1,0.25), (1,0.25, 1,0.5), (1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0)],
            'g': [(1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0), (1,0, 1,-0.3), (1,-0.3, 0,-0.3)],
            'ğ': [(1,0.5, 0,0.5), (0,0.5, 0,0), (0,0, 1,0), (1,0, 1,-0.3), (1,-0.3, 0,-0.3), (0.2,0.7, 0.8,0.7)],
            'h': [(0,1, 0,0), (0,0.5, 1,0.5), (1,0.5, 1,0)],
            'ı': [(0.5,0, 0.5,0.5)],
            'i': [(0.5,0, 0.5,0.5), (0.5,0.7, 0.5,0.8)],
            'k': [(0,1, 0,0), (1,0.5, 0,0.2), (0,0.2, 1,0)],
            'l': [(0.5,1, 0.5,0), (0.5,0, 1,0)],
            'm': [(0,0, 0,0.5), (0,0.5, 0.5,0.5), (0.5,0.5, 0.5,0), (0.5,0.5, 1,0.5), (1,0.5, 1,0)],
            'n': [(0,0, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0)],
            'o': [(0,0, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'ö': [(0,0, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0), (0.3,0.7, 0.3,0.8), (0.7,0.7, 0.7,0.8)],
            'p': [(0,-0.3, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            'r': [(0,0, 0,0.5), (0,0.5, 1,0.5)],
            's': [(1,0.5, 0,0.5), (0,0.5, 0,0.25), (0,0.25, 1,0.25), (1,0.25, 1,0), (1,0, 0,0)],
            'ş': [(1,0.5, 0,0.5), (0,0.5, 0,0.25), (0,0.25, 1,0.25), (1,0.25, 1,0), (1,0, 0,0), (0.5,0, 0.5,-0.2)],
            't': [(0.5,1, 0.5,0), (0,0.5, 1,0.5), (0.5,0, 1,0)],
            'u': [(0,0.5, 0,0), (0,0, 1,0), (1,0, 1,0.5)],
            'ü': [(0,0.5, 0,0), (0,0, 1,0), (1,0, 1,0.5), (0.3,0.7, 0.3,0.8), (0.7,0.7, 0.7,0.8)],
            'v': [(0,0.5, 0.5,0), (0.5,0, 1,0.5)],
            'y': [(0,0.5, 0.5,0), (0.5,0, 1,0.5), (0.5,0, 0.5,-0.3)],
            'z': [(0,0.5, 1,0.5), (1,0.5, 0,0), (0,0, 1,0)],

            # SAYILAR
            '0': [(0,0, 0,1), (0,1, 1,1), (1,1, 1,0), (1,0, 0,0), (0,0, 1,1)], # Sıfır çizgili
            '1': [(0.2,0.8, 0.5,1), (0.5,1, 0.5,0), (0.2,0, 0.8,0)],
            '2': [(0,0.8, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0), (0,0, 1,0)],
            '3': [(0,1, 1,1), (1,1, 0.5,0.5), (0.5,0.5, 1,0), (1,0, 0,0)],
            '4': [(0.8,0, 0.8,1), (0.8,1, 0,0.4), (0,0.4, 1,0.4)],
            '5': [(1,1, 0,1), (0,1, 0,0.6), (0,0.6, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)],
            '6': [(1,1, 0,0), (0,0, 1,0), (1,0, 1,0.5), (1,0.5, 0,0.5)],
            '7': [(0,1, 1,1), (1,1, 0.4,0)],
            '8': [(0,0, 1,0), (1,0, 1,1), (1,1, 0,1), (0,1, 0,0), (0,0.5, 1,0.5)],
            '9': [(1,0, 0,0.5), (0,0.5, 0,1), (0,1, 1,1), (1,1, 1,0)],

            ' ': [],
            '-': [(0,0.5, 1,0.5)],
            '.': [(0.4,0, 0.4,0.2), (0.4,0.2, 0.6,0.2), (0.6,0.2, 0.6,0), (0.6,0, 0.4,0)],
            '/': [(0,0, 1,1)]
        }

    def yaziyi_isle(self, metin, genislik_cm, yukseklik_cm):
        """
        Metni verilen CM kutusuna sığdırır.
        """
        alfabe = self._harf_veritabani()
        
        # 1. Önce metnin "doğal" en-boy oranını hesaplayalım
        toplam_dogal_genislik = 0
        max_dogal_yukseklik = 1.0 # Referans yüksekliği
        
        harf_araligi = 0.2
        
        for harf in metin:
            if harf == ' ':
                toplam_dogal_genislik += 0.5
            else:
                toplam_dogal_genislik += 0.7 # Ortalama harf genişliği (normalize)
            toplam_dogal_genislik += harf_araligi
        
        # 2. Ölçekleme Faktörünü Bul
        # Kullanıcının istediği alan (cm -> birim)
        target_w = genislik_cm * 10
        target_h = yukseklik_cm * 10
        
        # Yüksekliğe göre bir ölçek belirle
        scale = target_h # Çünkü harflerin boyu 0-1 arası, direkt yükseklik çarpanı olur.
        
        # Bu ölçekle genişlik sığıyor mu kontrol et
        olusan_genislik = toplam_dogal_genislik * scale
        
        if olusan_genislik > target_w:
            # Sığmıyor! Genişliğe göre küçült (Fit to Width)
            print(f"UYARI: Metin çok uzun, {genislik_cm}cm genişliğe sığdırılıyor.")
            scale = target_w / toplam_dogal_genislik
        
        # 3. Yazdırmaya Başla
        # Ortalamak için başlangıç noktası:
        mevcut_x = -(toplam_dogal_genislik * scale) / 2
        baslangic_y = 0
        
        # Kalınlık ayarı (Otomatik): Ölçek büyüdükçe kalınlık artmalı ama çok kaba olmamalı
        kalinlik_mm = scale / 30 # Deneyimsel oran
        if kalinlik_mm < 1.5: kalinlik_mm = 1.5 # Çok ince olmasın
        if kalinlik_mm > 4.0: kalinlik_mm = 4.0 # Çok kalın olmasın (Makine zorlanır)

        print(f"İşleniyor: '{metin}' -> Boyut: {scale/10:.1f}mm, Kalınlık: {kalinlik_mm:.1f}mm")

        for harf in metin:
            if harf == " ":
                mevcut_x += scale * 0.5
                continue
            
            # Harfi bul veya atla
            db_harf = harf if harf in alfabe else None
            # Küçük/Büyük harf duyarlılığı kontrolü (Basit fallback)
            if not db_harf and harf.upper() in alfabe: 
                print(f"Karakter '{harf}' bulunamadı, '{harf.upper()}' kullanılıyor.")
                db_harf = harf.upper() 
            
            if not db_harf: continue

            cizgiler = alfabe[db_harf]
            
            # Harf genişlik çarpanı (Bazı harfler ince: i, l, 1)
            dar_harfler = ['i', 'l', 'ı', '1', '.', 'I', 'İ']
            genislik_carpani = 0.4 if db_harf in dar_harfler else 0.7

            for (lx1, ly1, lx2, ly2) in cizgiler:
                gx1 = mevcut_x + (lx1 * scale * genislik_carpani)
                gy1 = baslangic_y + (ly1 * scale)
                gx2 = mevcut_x + (lx2 * scale * genislik_carpani)
                gy2 = baslangic_y + (ly2 * scale)
                
                self.tam_sargi_yap(gx1, gy1, gx2, gy2, kalinlik_mm)

            mevcut_x += (scale * genislik_carpani) + (scale * harf_araligi)

    def onizleme_olustur(self, dosya_adi):
        print("JPG Önizleme oluşturuluyor...")
        stitches = self.pattern.stitches
        plt.figure(figsize=(12, 6))
        plt.axis('equal'); plt.axis('off')
        
        x_list, y_list = [], []
        for stitch in stitches:
            x, y, cmd = stitch[0], stitch[1], stitch[2]
            if cmd == pyembroidery.JUMP or cmd == pyembroidery.TRIM:
                if x_list:
                    plt.plot(x_list, y_list, color='darkblue', linewidth=0.6, alpha=0.7)
                    x_list, y_list = [], []
            elif cmd == pyembroidery.STITCH:
                x_list.append(x); y_list.append(y)
        if x_list: plt.plot(x_list, y_list, color='darkblue', linewidth=0.6, alpha=0.7)

        plt.title(f"{dosya_adi}", fontsize=12)
        plt.savefig(f"{dosya_adi}_onizleme.jpg", dpi=150, bbox_inches='tight')
        plt.close()

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad_temiz = dosya_adi.replace(" ", "_").lower()
        pyembroidery.write(self.pattern, f"{ad_temiz}.dst")
        pyembroidery.write(self.pattern, f"{ad_temiz}.jef")
        self.onizleme_olustur(ad_temiz)
        print(f"✅ {ad_temiz} BİTTİ.")

# ==========================================
# KULLANICI KONTROL PANELİ
# ==========================================
if __name__ == "__main__":
    makine = ProfesyonelNakis()

    # ---------------------------------------------------------
    # BURAYI DOLDURMAN YETERLİ
    # ---------------------------------------------------------
    YAZILACAK_METIN = "Diyarbakır 21"  
    
    # Kutu Boyutları (CM Cinsinden)
    # Yazıyı bu kutunun içine sığdırır.
    GENISLIK_CM = 9   # Örn: 9 cm genişlik
    YUKSEKLIK_CM = 4  # Örn: 4 cm yükseklik
    # ---------------------------------------------------------

    makine.yaziyi_isle(YAZILACAK_METIN, GENISLIK_CM, YUKSEKLIK_CM)
    makine.kaydet(YAZILACAK_METIN)
