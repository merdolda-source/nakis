import pyembroidery
import math

class NakisMotoru:
    def __init__(self):
        self.pattern = pyembroidery.EmbPattern()
        # DÜZELTME: set_metadata yerine doğrudan isim atıyoruz
        self.pattern.name = "ModernNakis"
    
    def _mesafe(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def sargi_ve_alt_dikis(self, x1, y1, x2, y2, kalinlik_mm=3.0):
        """
        1. Önce altına 'running stitch' (alt dikiş) atar.
        2. Sonra üzerine 'satin stitch' (sargı) atar.
        """
        # Nakış birimi (1mm = 10 birim)
        genislik = kalinlik_mm * 10
        dx = x2 - x1
        dy = y2 - y1
        dist = self._mesafe(x1, y1, x2, y2)
        
        if dist == 0: return

        # Vektör hesaplamaları (Dik açı bulmak için)
        nx = -dy / dist * (genislik / 2)
        ny = dx / dist * (genislik / 2)

        # --- ADIM 1: ALT DİKİŞ (UNDERLAY) ---
        self.pattern.add_stitch_absolute(pyembroidery.JUMP, x1, y1)
        
        adim_sayisi_alt = int(dist // 20)
        if adim_sayisi_alt < 1: adim_sayisi_alt = 1
        
        for i in range(1, adim_sayisi_alt + 1):
            cx = x1 + (dx * i / adim_sayisi_alt)
            cy = y1 + (dy * i / adim_sayisi_alt)
            self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx), int(cy))
        
        # Geri dön
        self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(x1), int(y1))

        # --- ADIM 2: SARGI (SATIN STITCH) ---
        # 0.4mm (4 birim) yoğunluk
        adim_sayisi_sargi = int(dist // 4)
        if adim_sayisi_sargi < 2: adim_sayisi_sargi = 2

        for i in range(adim_sayisi_sargi + 1):
            ratio = i / adim_sayisi_sargi
            cx = x1 + (dx * ratio)
            cy = y1 + (dy * ratio)
            
            # Zikzak
            if i % 2 == 0:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx + nx), int(cy + ny))
            else:
                self.pattern.add_stitch_absolute(pyembroidery.STITCH, int(cx - nx), int(cy - ny))

    def yazi_yaz(self, metin, baslangic_x, baslangic_y, harf_boyu_mm):
        mevcut_x = baslangic_x
        scale = harf_boyu_mm * 10
        bosluk = scale * 0.2 

        # HARF VEKTÖR VERİTABANI (Genişletildi)
        alfabe = {
            'P': [(0,0, 0,1), (0,1, 0.5,1), (0.5,1, 0.5,0.5), (0.5,0.5, 0,0.5)],
            'I': [(0.25,0, 0.25,1)],
            'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
            'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.2,0.4, 0.8,0.4)],
            'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
            'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)], # N harfi eklendi
            'K': [(0,0, 0,1), (0,0.5, 0.8,1), (0,0.5, 0.8,0)], # K harfi eklendi
            'S': [(1,1, 0,1), (0,1, 0,0.5), (0,0.5, 1,0.5), (1,0.5, 1,0), (1,0, 0,0)], # S harfi (köşeli) eklendi
            '-': [(0,0.5, 1,0.5)],
            ' ': [] # Boşluk
        }

        for harf in metin.upper():
            if harf == " ":
                mevcut_x += scale * 0.5
                continue
            
            if harf not in alfabe:
                print(f"Uyarı: '{harf}' harfi veritabanında yok, atlanıyor.")
                continue

            cizgiler = alfabe[harf]
            
            # Harf kalınlığını boyuta göre ayarla (Min 2mm, Max 4mm)
            kalinlik = max(2.0, min(4.0, harf_boyu_mm / 8))

            for (lx1, ly1, lx2, ly2) in cizgiler:
                gercek_x1 = mevcut_x + (lx1 * scale * 0.6)
                gercek_y1 = baslangic_y + (ly1 * scale)
                gercek_x2 = mevcut_x + (lx2 * scale * 0.6)
                gercek_y2 = baslangic_y + (ly2 * scale)
                
                self.sargi_ve_alt_dikis(gercek_x1, gercek_y1, gercek_x2, gercek_y2, kalinlik_mm=kalinlik)

            mevcut_x += (scale * 0.6) + bosluk

    def kaydet(self, dosya_adi):
        # Son bir temizlik ve ortalama
        self.pattern = self.pattern.get_normalized_pattern()
        
        # Dosyaları yaz
        pyembroidery.write(self.pattern, f"{dosya_adi}.dst")
        pyembroidery.write(self.pattern, f"{dosya_adi}.jef")
        print(f"--- {dosya_adi} BASARIYLA URETILDI ---")

# --- SENARYO ---
def uretim_senaryosu():
    motor = NakisMotoru()
    
    # SENARYO:
    # 1. PIVAZ yazısı (Büyük, Üstte)
    motor.yazi_yaz("PIVAZ", -400, 100, 40) 
    
    # 2. NAKIS yazısı (Orta, Altta) - Artık N, K, S harfleri tanımlı!
    motor.yazi_yaz("NAKIS", -400, -400, 30)

    motor.kaydet("modern_tasarim")

if __name__ == "__main__":
    uretim_senaryosu()
