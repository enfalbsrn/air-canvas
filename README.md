# 🎨 Havada El Çizimi (Air Canvas Pro / Parmakla Boyama)

Fiziksel bir ekrana veya kaleme dokunmadan, tamamen boşlukta el ve parmak hareketlerinizle canlı çizim yapabileceğiniz yeni nesil bilgisayarla görme (Computer Vision) uygulaması.

Proje, **OpenCV** ve Google'ın en güncel **MediaPipe Hand Landmarker (Tasks API)** kütüphanesini kullanarak elinizdeki 21 eklem noktasını gerçek zamanlı (100+ FPS) takip eder.

---

## ✨ Yeni Nesil Pro Özellikler

1. **Sınırsız Geri Al (Undo) & İleri Al (Redo):** Yanlış bir çizgi çektiğinizde tuvali silmek zorunda kalmadan `Z` tuşuyla geri, `Y` tuşuyla ileri alabilirsiniz. Tuval temizleme işlemi de geri alınabilir!
2. **Işıltılı Fırça Efektleri:**
   - **Klasik:** Kesintisiz, pürüzsüz hatlar.
   - **Neon Glow:** Işıkla boyama hissi veren çok katmanlı parlayan neon fırça.
   - **Gökkuşağı (Rainbow):** Çizim yaptıkça renk geçişi sağlayan dinamik spektrum.
3. **Geometrik Şekil Araçları:** Havada elinizi kaydırarak kusursuz **Düz Çizgi**, **Dikdörtgen** ve **Çember** çizme modu (canlı boyut ve yarıçap göstergesiyle).
4. **Pinch (Kıstırma) ile Anında Tıklama:** Başparmak ve işaret parmağınızı birleştirerek üst menüdeki butonları beklemeden tıklayabilirsiniz.
5. **Dwell (Bekleme Sayacı) ile Temassız Seçim:** Menü butonunun üzerinde iki parmakla beklediğinizde dolan animasyonlu sayaç sayesinde temassız tetikleme.
6. **PiP (Picture-in-Picture) Canlı Mini Kamera:** Beyaz ve Siyah tahta modlarında sağ altta canlı webcam görüntüsü ile elinizin ve iskeletinizin konumunu kaybetmezsiniz (`P` tuşu ile açılıp kapatılabilir).
7. **Parçacık Saçılımı (Sparkle Particles):** Çizim yaparken parmak ucundan dökülen mini ışık parçacıkları.

---

## ✋ El Hareketleri (Gestures) ve Kullanım

| Hareket | Mod | Açıklama |
| :--- | :--- | :--- |
| ☝️ **Yalnızca İşaret Parmağı** | **Çizim / Şekil Modu** | Parmağınızı havada gezdirdiğinizde seçili fırça efektinde ve şekilde çizim yapar. |
| ✌️ **İşaret + Orta Parmak** | **Seçim / Menü Modu** | Çizimi durdurur. İki parmağınızı üst menüdeki araç kutularına götürerek seçim yapabilirsiniz. |
| 🤏 **Pinch (Başparmak + İşaret)** | **Hızlı Tıklama** | Menü butonu üzerindeyken parmaklarınızı kıstırarak anında tıklama yapabilirsiniz. |
| ✊ **Yumruk Yapma** | **Tuvali Temizle** | Yumruk yapıp yarım saniye tuttuğunuzda geri sayım dairesi dolar ve tuval temizlenir (Geri alınabilir!). |

---

## 🎨 Menü Araç Çubuğu

Üst menüye **✌️ Seçim Modu** veya **🤏 Pinch** ile erişebilirsiniz:

- **Renk Paleti (7 Renk):** Mavi, Yeşil, Kırmızı, Sarı, Mor, Turkuaz, Beyaz.
- **FIRCA:** Klasik ➔ Neon Glow ➔ Gökkuşağı efektleri arasında geçiş.
- **SEKIL:** Serbest ➔ Düz Çizgi ➔ Dikdörtgen ➔ Daire çizim modları.
- **BOYUT:** Fırça kalınlığı (İnce: 6px, Orta: 14px, Kalın: 26px).
- **SILGI:** Silgi modunu açar / kapatır.
- **GERI [Z]:** Son hamleyi geri alır (Undo).
- **ILERI [Y]:** Geri alınan hamleyi yineler (Redo).
- **TAHTA [T]:** Kamera (Artırılmış Gerçeklik) / Beyaz Tahta / Siyah Tahta görünümleri.
- **KAYDET [S]:** Çizimi anlık olarak PNG formatında kaydeder.
- **TEMIZLE [C]:** Tuvali anında sıfırlar.

---

## ⌨️ Klavye Kısayolları

Kamera penceresi aktifken klavyenizden de tüm kontrolleri sağlayabilirsiniz:

| Tuş | İşlev |
| :---: | :--- |
| `Z` | Geri Al (Undo) |
| `Y` | İleri Al (Redo) |
| `B` | Fırça Efektini Değiştir (Klasik / Neon / Gökkuşağı) |
| `M` | Şekil Modunu Değiştir (Serbest / Çizgi / Dikdörtgen / Daire) |
| `E` | Silgiyi Aç / Kapat |
| `T` | Tahta Görünüm Modunu Değiştir (Kamera / Beyaz / Siyah) |
| `P` | Dijital Tahtada PiP Mini Kamerayı Aç / Kapat |
| `S` | Çizimi PNG Olarak Kaydet |
| `C` | Tuvali Temizle |
| `H` | El İskeletini Aç / Kapat |
| `Q` / `ESC` | Uygulamadan Çıkış |

---

## 🚀 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleme
```bash
python -m pip install -r requirements.txt
```

### 2. Uygulamayı Başlatma
```bash
python air_canvas.py
```

> **Not:** `hand_landmarker.task` modeli ilk çalıştırmada mevcut değilse otomatik olarak Google'ın resmi deposundan güvenle indirilir.

---

## 💡 İpuçları
1. **İyi Işıklandırma:** Kameranızın elinizi net görebileceği aydınlık bir ortamda en iyi takip performansını elde edersiniz.
2. **Kamera Mesafesi:** Kameradan 40-80 cm mesafede durmanız idealdir.
3. **Pürüzsüz Çizim:** Algoritma içindeki EMA filtresi sayesinde el titremeleri yumuşatılır ve kesintisiz hatlar elde edilir.
