import pyembroidery
import math

class ProfesyonelNakis:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        self.pattern.name = "UltraSargi"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def tam_sargi_yap(self, x1, y1, x2, y2, kalinlik_mm):
        """
        BU FONKSİYON "SIKIRTIRS" GÖRÜNTÜYÜ SAĞLAR.
        Hem alt dolgu yapar hem de üst sargıyı çok sık atar.
        """
        # 1mm = 10 birim
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0: return

        # Vektör hesaplamaları (Dik açı)
        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # === 1. AŞAMA: ALT DOLGU (UNDERLAY) ===
        # Nakışın kabarık durması için alta zemin hazırlarız.
        # Kenarlardan biraz içeriden giden bir hat çiziyoruz.
        
        kucultme_faktoru = 0.7 # Alt dikiş sargıdan daha dar olsun
        nx_alt = nx * kucultme_faktoru
        ny_alt = ny * kucultme_faktoru

        self.pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        # Ortadan bir dikiş git
        steps_alt = int(dist // 30) + 1
        for i in range(steps_alt + 1):
             self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1 + dx*i/steps_alt), int(y1 + dy*i/steps_alt))
        
        # Geri dön (Çift kat alt dikiş = Daha kabarık)
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))


        # === 2. AŞAMA: SÜPER SIKI SARGI (TOP SATIN) ===
        # Buradaki "3" sayısı yoğunluktur. Sayı küçüldükçe dikiş sıklaşır.
        # Normalde 4 veya 5 kullanılır. Biz 3 yaptık (Çok Sıkı).
        YOGUNLUK = 3 
        
        steps_sargi = int(dist // YOGUNLUK)
        if steps_sargi < 2: steps_sargi = 2

        for i in range(steps_sargi + 1):
            ratio = i / steps_sargi
            cx = x1 + (dx * ratio)
            cy = y1 + (dy * ratio)
            
            # Zikzak at (Sargı)
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))

    def isim_yaz(self, metin, baslangic_x, baslangic_y, harf_boyu_mm):
        mevcut_x = baslangic_x
        scale = harf_boyu_mm * 10
        bosluk = scale * 0.25 # Harfler birbirine girmesin diye %25 boşluk

        # --- GELİŞMİŞ ALFABE ---
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

        # Kalınlığı harf boyuna göre "Tok" duracak şekilde ayarla
        # Harf boyunun %12'si kadar kalınlık (Normalden daha kalın)
        sargi_kalinligi = harf_boyu_mm * 0.12
        if sargi_kalinligi < 2.5: sargi_kalinligi = 2.5 # Minimum kalınlık

        for harf in metin.upper():
            if harf == " ":
                mevcut_x += scale * 0.6
                continue
            
            if harf not in alfabe:
                print(f"Uyarı: {harf} yok.")
                continue

            cizgiler = alfabe[harf]
            
            for (lx1, ly1, lx2, ly2) in cizgiler:
                # Koordinat hesapla
                gx1 = mevcut_x + (lx1 * scale * 0.7)
                gy1 = baslangic_y + (ly1 * scale)
                gx2 = mevcut_x + (lx2 * scale * 0.7)
                gy2 = baslangic_y + (ly2 * scale)
                
                self.tam_sargi_yap(gx1, gy1, gx2, gy2, sargi_kalinligi)

            # Bir sonraki harfe geç
            mevcut_x += (scale * 0.7) + bosluk

    def kaydet(self, dosya_adi):
        self.pattern = self.pattern.get_normalized_pattern()
        ad_temiz = dosya_adi.replace(" ", "_").lower()
        pyembroidery.write(self.pattern, f"{ad_temiz}.dst")
        pyembroidery.write(self.pattern, f"{ad_temiz}.jef")
        print(f"✅ {dosya_adi} İÇİN DOSYALAR HAZIR: {ad_temiz}.jef")

# ==========================================
# BURAYI DEĞİŞTİR (MÜŞTERİ PANELİ)
# ==========================================
if __name__ == "__main__":
    
    makine = ProfesyonelNakis()

    # ---------------------------------------
    # SADECE BURADAKİ 2 SATIRI DEĞİŞTİR
    # ---------------------------------------
    MUSTERI_ISMI = "MEHMET"  
    ISTENEN_BOYUT = 120      # mm cinsinden (Örn: 12cm)
    # ---------------------------------------

    # Yazıyı ortalamak için hesap (Otomatik)
    baslama_yeri = len(MUSTERI_ISMI) * ISTENEN_BOYUT * -0.35
    
    # İşlemi Başlat
    makine.isim_yaz(MUSTERI_ISMI, baslama_yeri, 0, ISTENEN_BOYUT)
    makine.kaydet(MUSTERI_ISMI)
