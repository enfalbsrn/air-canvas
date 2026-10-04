"""
Havada El Çizimi (Air Canvas / Parmakla Boyama) - Pro Sürüm
============================================================
Kütüphaneler: OpenCV, MediaPipe Hands (Tasks API), NumPy

Temel Özellikler:
1. Serbest & Pürüzsüz Çizim (İşaret Parmağı)
2. Geometrik Şekiller: Düz Çizgi, Dikdörtgen, Çember ([M] Tuşu veya Menü)
3. Fırça Efektleri: Klasik, Işıltılı Neon Glow, Gökkuşağı (Rainbow) ([B] Tuşu)
4. Sınırsız Geri Al (Undo [Z]) ve İleri Al (Redo [Y]) Geçmişi
5. Pinch (Başparmak + İşaret Kıstırma) ile Anında Menü Tıklama
6. Dwell (Bekleme Sayacı) ile Temassız Buton Seçimi
7. Dijital Tahtalarda (Beyaz/Siyah) PiP Canlı Mini Kamera ([P] Tuşu)
8. Parçacık (Sparkle) Efektleri ve Modern HUD Tasarımı
9. Yumruk ile Güvenli Tuval Temizleme (Clear Canvas)

Klavye Kısayolları:
- [Q] / [ESC] : Çıkış
- [Z] : Geri Al (Undo)
- [Y] : İleri Al (Redo)
- [B] : Fırça Efekti Değiştir (Klasik / Neon / Gökkuşağı)
- [M] : Şekil Modu Değiştir (Serbest / Çizgi / Dikdörtgen / Daire)
- [E] : Silgi Aç / Kapat
- [T] : Tahta Görünüm Modu (Kamera / Beyaz Tahta / Siyah Tahta)
- [P] : PiP Mini Kamera Aç / Kapat
- [S] : Çizimi PNG Olarak Kaydet
- [C] : Tuvali Temizle (Geri Alınabilir!)
- [H] : El İskeletini Aç / Kapat
"""

import os
import sys
import time
import math
import urllib.request
from datetime import datetime
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Model Dosya Yolu ve İndirme
MODEL_FILENAME = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, MODEL_FILENAME)


def ensure_model_exists():
    """Model dosyası mevcut değilse otomatik olarak indirir."""
    if not os.path.exists(MODEL_PATH):
        print(f"[*] MediaPipe el takip modeli ({MODEL_FILENAME}) indiriliyor...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print(f"[+] Model basariyla indirildi: {MODEL_PATH}")
        except Exception as e:
            print(f"[-] Model indirilirken hata olustu: {e}")
            sys.exit(1)


# Renk Tanımları (BGR Formatında)
COLORS = [
    {"name": "Mavi",    "bgr": (255, 140, 0),   "hex": "#008CFF"},
    {"name": "Yesil",   "bgr": (30, 220, 50),   "hex": "#32DC1E"},
    {"name": "Kirmizi", "bgr": (50, 50, 255),   "hex": "#FF3232"},
    {"name": "Sari",    "bgr": (0, 230, 255),   "hex": "#FFE600"},
    {"name": "Mor",     "bgr": (230, 50, 220),  "hex": "#DC32E6"},
    {"name": "Turkuaz", "bgr": (240, 210, 0),   "hex": "#00D2F0"},
    {"name": "Beyaz",   "bgr": (250, 250, 250), "hex": "#FAFAFA"}
]

BRUSH_SIZES = [
    {"name": "Ince",  "size": 6},
    {"name": "Orta",  "size": 14},
    {"name": "Kalin", "size": 26}
]
ERASER_SIZE = 55

BRUSH_STYLES = ["Klasik", "Neon", "Gokkusagi"]
SHAPE_MODES = ["Serbest", "Cizgi", "Dikdortgen", "Daire"]


class ParticleSystem:
    """Çizim yaparken parmak ucundan saçılan ışıltılı parçacık efekti."""
    def __init__(self, max_particles=45):
        self.particles = []
        self.max_particles = max_particles

    def emit(self, x, y, color, count=2):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                self.particles.pop(0)
            angle = np.random.uniform(0, 2 * math.pi)
            speed = np.random.uniform(1.2, 3.8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = np.random.uniform(0.25, 0.55)
            radius = np.random.randint(2, 5)
            self.particles.append({
                "x": float(x),
                "y": float(y),
                "vx": vx,
                "vy": vy,
                "color": color,
                "radius": radius,
                "birth": time.time(),
                "life": life
            })

    def update_and_draw(self, img):
        now = time.time()
        alive = []
        for p in self.particles:
            age = now - p["birth"]
            if age < p["life"]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                alpha = 1.0 - (age / p["life"])
                ix, iy = int(p["x"]), int(p["y"])
                if 0 <= ix < img.shape[1] and 0 <= iy < img.shape[0]:
                    r = max(1, int(p["radius"] * alpha))
                    cv2.circle(img, (ix, iy), r, p["color"], -1, cv2.LINE_AA)
                alive.append(p)
        self.particles = alive


class ToastNotification:
    """Ekranda kısa süreli şık bildirimler gösterir."""
    def __init__(self):
        self.message = ""
        self.end_time = 0
        self.color = (0, 255, 200)

    def show(self, message, duration=1.6, color=(0, 255, 200)):
        self.message = message
        self.end_time = time.time() + duration
        self.color = color

    def draw(self, img):
        if time.time() < self.end_time and self.message:
            h, w = img.shape[:2]
            text = self.message
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.72
            thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)

            box_x1 = max(10, (w - text_w) // 2 - 22)
            box_y1 = 98
            box_x2 = min(w - 10, (w + text_w) // 2 + 22)
            box_y2 = 98 + text_h + 20

            sub_img = img[box_y1:box_y2, box_x1:box_x2]
            if sub_img.shape[0] > 0 and sub_img.shape[1] > 0:
                overlay = np.zeros_like(sub_img)
                cv2.rectangle(overlay, (0, 0), (box_x2 - box_x1, box_y2 - box_y1), (22, 26, 32), -1)
                cv2.addWeighted(sub_img, 0.25, overlay, 0.75, 0, sub_img)
                cv2.rectangle(img, (box_x1, box_y1), (box_x2, box_y2), self.color, 2, cv2.LINE_AA)
                cv2.putText(img, text, (box_x1 + 22, box_y1 + text_h + 10),
                            font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


class AirCanvas:
    def __init__(self, camera_idx=0):
        ensure_model_exists()

        # Kamera Başlatma
        self.cap = cv2.VideoCapture(camera_idx)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        ret, frame = self.cap.read()
        if not ret:
            print("[-] Kamera acilamadi! Lutfen kamera baglantinizi kontrol edin.")
            sys.exit(1)

        self.height, self.width = frame.shape[:2]
        print(f"[+] Kamera hazir: {self.width}x{self.height}")

        # MediaPipe HandLandmarker Başlatma
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            running_mode=vision.RunningMode.IMAGE
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        # Çizim Tuvali (Siyah zemin - çizgiler buraya eklenir)
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Geri Al / İleri Al (Undo / Redo) Yığınları
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 18

        # Durum Değişkenleri
        self.selected_color_idx = 0
        self.is_eraser = False
        self.brush_size_idx = 1  # Varsayılan: Orta (14px)
        self.current_color = COLORS[self.selected_color_idx]["bgr"]

        # Fırça ve Şekil Modları
        self.brush_style = "Klasik"  # "Klasik", "Neon", "Gokkusagi"
        self.shape_mode = "Serbest"   # "Serbest", "Cizgi", "Dikdortgen", "Daire"
        self.shape_start = None       # Şekil başlangıç koordinatı (x, y)
        self.shape_preview_end = None # Şekil canlı önizleme sonu (x, y)

        # Gökkuşağı Renk Döngüsü
        self.rainbow_hue = 0.0

        # Çizim Koordinatları ve Yumuşatma (Smoothing)
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 0.55
        self.is_drawing_stroke = False

        # Yumruk ile Tuval Temizleme Sayacı
        self.fist_frames = 0
        self.FIST_THRESHOLD = 18

        # Menü Etkileşimi (Dwell & Pinch)
        self.hovered_btn = None
        self.hover_start_time = 0.0
        self.DWELL_TIME = 0.42  # Hover ile tıklama için gereken süre (sn)
        self.last_action_time = 0.0
        self.ACTION_COOLDOWN = 0.35

        # Görünüm Modu: 'camera', 'whiteboard', 'blackboard'
        self.view_mode = "camera"
        self.show_skeleton = True
        self.show_pip = True  # Dijital tahtada canlı mini kamera

        # Parçacık ve Bildirim Yöneticisi
        self.particles = ParticleSystem(max_particles=40)
        self.toast = ToastNotification()
        self.toast.show("Air Canvas Pro Hazir! Isaret parmagiyla cizin.", duration=2.5)

        # Menü Çubuğu Boyutu ve Butonlar
        self.header_height = 84
        self.buttons = []
        self._setup_toolbar()

    def _setup_toolbar(self):
        """Üst menü araç çubuğu butonlarının konumlarını ekrana göre dinamik hesaplar."""
        self.buttons = []
        btn_y1 = 8
        btn_y2 = self.header_height - 8

        scale = max(0.55, min(1.15, self.width / 1280.0))
        btn_h = btn_y2 - btn_y1

        # Renk Butonları
        color_w = int(45 * scale)
        color_gap = int(5 * scale)
        cur_x = 12

        for i, c in enumerate(COLORS):
            x1 = cur_x
            x2 = x1 + color_w
            self.buttons.append({
                "type": "color",
                "index": i,
                "label": c["name"],
                "color": c["bgr"],
                "rect": (x1, btn_y1, x2, btn_y2)
            })
            cur_x += color_w + color_gap

        cur_x += int(8 * scale)
        gap = int(6 * scale)

        # Fırça Efekti Butonu
        brush_w = int(82 * scale)
        self.buttons.append({
            "type": "brush_style",
            "label": "FIRCA",
            "rect": (cur_x, btn_y1, cur_x + brush_w, btn_y2)
        })
        cur_x += brush_w + gap

        # Şekil Seçim Butonu
        shape_w = int(84 * scale)
        self.buttons.append({
            "type": "shape_mode",
            "label": "SEKIL",
            "rect": (cur_x, btn_y1, cur_x + shape_w, btn_y2)
        })
        cur_x += shape_w + gap

        # Boyut Butonu
        size_w = int(76 * scale)
        self.buttons.append({
            "type": "size",
            "label": "BOYUT",
            "rect": (cur_x, btn_y1, cur_x + size_w, btn_y2)
        })
        cur_x += size_w + gap

        # Silgi Butonu
        eraser_w = int(72 * scale)
        self.buttons.append({
            "type": "eraser",
            "label": "SILGI",
            "rect": (cur_x, btn_y1, cur_x + eraser_w, btn_y2)
        })
        cur_x += eraser_w + gap

        # Geri Al Butonu
        undo_w = int(68 * scale)
        self.buttons.append({
            "type": "undo",
            "label": "GERI",
            "rect": (cur_x, btn_y1, cur_x + undo_w, btn_y2)
        })
        cur_x += undo_w + gap

        # İleri Al Butonu
        redo_w = int(68 * scale)
        self.buttons.append({
            "type": "redo",
            "label": "ILERI",
            "rect": (cur_x, btn_y1, cur_x + redo_w, btn_y2)
        })
        cur_x += redo_w + gap

        # Tahta Modu Butonu
        view_w = int(78 * scale)
        self.buttons.append({
            "type": "view_mode",
            "label": "TAHTA",
            "rect": (cur_x, btn_y1, cur_x + view_w, btn_y2)
        })
        cur_x += view_w + gap

        # Kaydet Butonu
        save_w = int(76 * scale)
        self.buttons.append({
            "type": "save",
            "label": "KAYDET",
            "rect": (cur_x, btn_y1, cur_x + save_w, btn_y2)
        })
        cur_x += save_w + gap

        # Temizle Butonu
        clear_w = int(82 * scale)
        self.buttons.append({
            "type": "clear",
            "label": "TEMIZLE",
            "rect": (cur_x, btn_y1, cur_x + clear_w, btn_y2)
        })

    def save_undo_state(self):
        """Tuvalin anlık kopyasını geri alma yığınına ekler."""
        self.undo_stack.append(self.canvas.copy())
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        """Son yapılan çizimi veya işlemi geri alır."""
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.canvas[:] = self.undo_stack.pop()
            self.toast.show("Geri Alindi (Undo) [Z]", duration=1.2, color=(255, 180, 50))
        else:
            self.toast.show("Geri alinacak islem yok", duration=1.0, color=(140, 140, 140))

    def redo(self):
        """Geri alınan işlemi tekrar uygular."""
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas[:] = self.redo_stack.pop()
            self.toast.show("Ileri Alindi (Redo) [Y]", duration=1.2, color=(50, 200, 255))
        else:
            self.toast.show("Ileri alinacak islem yok", duration=1.0, color=(140, 140, 140))

    def get_brush_thickness(self):
        if self.is_eraser:
            return ERASER_SIZE
        return BRUSH_SIZES[self.brush_size_idx]["size"]

    def get_rainbow_color(self):
        """HSV renk dairesi üzerinden sürekli değişen gökkuşağı rengi üretir."""
        self.rainbow_hue = (self.rainbow_hue + 3.2) % 180.0
        hsv_mat = np.uint8([[[int(self.rainbow_hue), 245, 255]]])
        bgr = cv2.cvtColor(hsv_mat, cv2.COLOR_HSV2BGR)[0][0]
        return (int(bgr[0]), int(bgr[1]), int(bgr[2]))

    def draw_neon_segment(self, target_img, pt1, pt2, color, thickness):
        """Işıltılı ve parlayan (Neon Glow) hat çizer."""
        # Dış ışıma katmanı
        glow1 = (color[0] // 3, color[1] // 3, color[2] // 3)
        cv2.line(target_img, pt1, pt2, glow1, thickness * 3, cv2.LINE_AA)
        cv2.circle(target_img, pt2, (thickness * 3) // 2, glow1, -1, cv2.LINE_AA)

        # Orta ışıma katmanı
        cv2.line(target_img, pt1, pt2, color, thickness * 2, cv2.LINE_AA)
        cv2.circle(target_img, pt2, thickness, color, -1, cv2.LINE_AA)

        # Parlak çekirdek katmanı
        core = (
            min(255, int(color[0] * 0.4 + 180)),
            min(255, int(color[1] * 0.4 + 180)),
            min(255, int(color[2] * 0.4 + 180))
        )
        t_core = max(2, thickness // 2)
        cv2.line(target_img, pt1, pt2, core, t_core, cv2.LINE_AA)
        cv2.circle(target_img, pt2, t_core // 2, core, -1, cv2.LINE_AA)

    def commit_shape(self, start_pt, end_pt):
        """Geometrik şekli tuvale işler ve geri alma noktası kaydeder."""
        self.save_undo_state()
        color = self.get_rainbow_color() if self.brush_style == "Gokkusagi" else self.current_color
        thickness = self.get_brush_thickness()

        if self.shape_mode == "Cizgi":
            if self.brush_style == "Neon":
                self.draw_neon_segment(self.canvas, start_pt, end_pt, color, thickness)
            else:
                cv2.line(self.canvas, start_pt, end_pt, color, thickness, cv2.LINE_AA)

        elif self.shape_mode == "Dikdortgen":
            if self.brush_style == "Neon":
                glow1 = (color[0] // 3, color[1] // 3, color[2] // 3)
                cv2.rectangle(self.canvas, start_pt, end_pt, glow1, thickness * 3, cv2.LINE_AA)
                cv2.rectangle(self.canvas, start_pt, end_pt, color, thickness * 2, cv2.LINE_AA)
                core = (min(255, int(color[0] * 0.4 + 180)), min(255, int(color[1] * 0.4 + 180)), min(255, int(color[2] * 0.4 + 180)))
                cv2.rectangle(self.canvas, start_pt, end_pt, core, max(2, thickness // 2), cv2.LINE_AA)
            else:
                cv2.rectangle(self.canvas, start_pt, end_pt, color, thickness, cv2.LINE_AA)

        elif self.shape_mode == "Daire":
            rad = int(math.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1]))
            if rad > 3:
                if self.brush_style == "Neon":
                    glow1 = (color[0] // 3, color[1] // 3, color[2] // 3)
                    cv2.circle(self.canvas, start_pt, rad, glow1, thickness * 3, cv2.LINE_AA)
                    cv2.circle(self.canvas, start_pt, rad, color, thickness * 2, cv2.LINE_AA)
                    core = (min(255, int(color[0] * 0.4 + 180)), min(255, int(color[1] * 0.4 + 180)), min(255, int(color[2] * 0.4 + 180)))
                    cv2.circle(self.canvas, start_pt, rad, core, max(2, thickness // 2), cv2.LINE_AA)
                else:
                    cv2.circle(self.canvas, start_pt, rad, color, thickness, cv2.LINE_AA)

        self.toast.show(f"{self.shape_mode} Cizildi!", duration=1.1, color=(0, 255, 120))

    def process_finger_states(self, landmarks):
        """Parmakların açık/kapalı durumunu, yumruk ve pinch hareketini tespit eder."""
        pts = [(int(lm.x * self.width), int(lm.y * self.height)) for lm in landmarks]

        # Açık parmak kontrolleri
        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y
        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y

        # Yumruk kontrolü
        w_x, w_y = landmarks[0].x, landmarks[0].y
        palm_dist = math.hypot(landmarks[9].x - w_x, landmarks[9].y - w_y)

        def tip_dist(idx):
            return math.hypot(landmarks[idx].x - w_x, landmarks[idx].y - w_y)

        fist_by_dist = (
            tip_dist(8) < palm_dist * 1.25 and
            tip_dist(12) < palm_dist * 1.25 and
            tip_dist(16) < palm_dist * 1.25 and
            tip_dist(20) < palm_dist * 1.25
        )
        fist_by_y = (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up)
        is_fist = fist_by_dist or fist_by_y

        # Pinch (Kıstırma: Başparmak ucu 4 ve İşaret parmağı ucu 8 yakınlığı)
        ref_hand_scale = max(1.0, math.hypot(pts[9][0] - pts[0][0], pts[9][1] - pts[0][1]))
        pinch_dist = math.hypot(pts[4][0] - pts[8][0], pts[4][1] - pts[8][1])
        is_pinch = (pinch_dist / ref_hand_scale) < 0.35

        return index_up, middle_up, ring_up, pinky_up, is_fist, is_pinch, pts

    def draw_skeleton(self, img, pts):
        """El iskeletini ve eklem noktalarını görselleştirir."""
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # Başparmak
            (0, 5), (5, 6), (6, 7), (7, 8),        # İşaret
            (5, 9), (9, 10), (10, 11), (11, 12),    # Orta
            (9, 13), (13, 14), (14, 15), (15, 16), # Yüzük
            (13, 17), (17, 18), (18, 19), (19, 20),# Serçe
            (0, 17)                                # Avuç tabanı
        ]
        overlay = img.copy()
        for p1, p2 in connections:
            cv2.line(overlay, pts[p1], pts[p2], (220, 220, 220), 2, cv2.LINE_AA)
        for pt in pts:
            cv2.circle(overlay, pt, 4, (0, 240, 255), -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)

    def draw_toolbar(self, img, hover_btn=None, hover_progress=0.0):
        """Modern cam efektli menü çubuğunu çizer."""
        header_sub = img[0:self.header_height, 0:self.width]
        overlay = np.zeros_like(header_sub)
        cv2.rectangle(overlay, (0, 0), (self.width, self.header_height), (16, 20, 25), -1)
        cv2.addWeighted(header_sub, 0.22, overlay, 0.78, 0, header_sub)
        cv2.line(img, (0, self.header_height), (self.width, self.header_height), (50, 58, 68), 2)

        for btn in self.buttons:
            x1, y1, x2, y2 = btn["rect"]
            is_hover = (hover_btn == btn)

            if btn["type"] == "color":
                idx = btn["index"]
                is_selected = (not self.is_eraser) and (self.selected_color_idx == idx)
                color = btn["color"]

                cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
                if is_selected:
                    cv2.rectangle(img, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.circle(img, ((x1 + x2) // 2, (y1 + y2) // 2), 6, (255, 255, 255), -1)
                elif is_hover:
                    cv2.rectangle(img, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (240, 240, 240), 2, cv2.LINE_AA)
                else:
                    cv2.rectangle(img, (x1, y1), (x2, y2), (65, 72, 82), 1)

                text_color = (10, 10, 10) if (color[0] + color[1] + color[2] > 420) else (255, 255, 255)
                cv2.putText(img, btn["label"][:4], (x1 + 6, y2 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, text_color, 1, cv2.LINE_AA)

            elif btn["type"] == "brush_style":
                bg = (45, 50, 62) if not is_hover else (65, 72, 90)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 220) if is_hover else (90, 95, 105), 1, cv2.LINE_AA)
                cv2.putText(img, "FIRCA", (x1 + 10, y1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, self.brush_style, (x1 + 8, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 220), 1, cv2.LINE_AA)

            elif btn["type"] == "shape_mode":
                bg = (45, 50, 62) if not is_hover else (65, 72, 90)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 200, 50) if is_hover else (90, 95, 105), 1, cv2.LINE_AA)
                cv2.putText(img, "SEKIL", (x1 + 12, y1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, self.shape_mode[:6], (x1 + 8, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 200, 50), 1, cv2.LINE_AA)

            elif btn["type"] == "size":
                bg = (45, 50, 62) if not is_hover else (65, 72, 90)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 150) if is_hover else (90, 95, 105), 1, cv2.LINE_AA)
                cur = BRUSH_SIZES[self.brush_size_idx]
                cv2.putText(img, "BOYUT", (x1 + 10, y1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, f"{cur['size']}px", (x1 + 14, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 150), 1, cv2.LINE_AA)

            elif btn["type"] == "eraser":
                is_selected = self.is_eraser
                bg = (60, 90, 160) if is_selected else ((45, 50, 62) if not is_hover else (65, 72, 90))
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                border = (0, 255, 255) if is_selected else ((255, 255, 255) if is_hover else (90, 95, 105))
                cv2.rectangle(img, (x1, y1), (x2, y2), border, 2 if is_selected else 1, cv2.LINE_AA)
                cv2.putText(img, "SILGI", (x1 + 10, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)
                st = "AKTIF" if is_selected else "KAPALI"
                cv2.putText(img, st, (x1 + 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255) if is_selected else (170, 175, 185), 1, cv2.LINE_AA)

            elif btn["type"] == "undo":
                bg = (40, 48, 58) if not is_hover else (60, 70, 85)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 180, 50) if is_hover else (85, 92, 102), 1, cv2.LINE_AA)
                cv2.putText(img, "GERI", (x1 + 12, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, "[Z]", (x1 + 18, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 180, 50), 1, cv2.LINE_AA)

            elif btn["type"] == "redo":
                bg = (40, 48, 58) if not is_hover else (60, 70, 85)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (50, 200, 255) if is_hover else (85, 92, 102), 1, cv2.LINE_AA)
                cv2.putText(img, "ILERI", (x1 + 10, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, "[Y]", (x1 + 16, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (50, 200, 255), 1, cv2.LINE_AA)

            elif btn["type"] == "view_mode":
                bg = (45, 50, 62) if not is_hover else (65, 72, 90)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255) if is_hover else (90, 95, 105), 1, cv2.LINE_AA)
                labels = {"camera": "Kamera", "whiteboard": "Beyaz", "blackboard": "Siyah"}
                cv2.putText(img, "TAHTA", (x1 + 10, y1 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, labels.get(self.view_mode, "")[:6], (x1 + 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 200, 80), 1, cv2.LINE_AA)

            elif btn["type"] == "save":
                bg = (30, 65, 40) if is_hover else (25, 50, 32)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (80, 255, 120) if is_hover else (60, 110, 70), 1, cv2.LINE_AA)
                cv2.putText(img, "KAYDET", (x1 + 8, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 255, 150), 1, cv2.LINE_AA)
                cv2.putText(img, "[S]", (x1 + 22, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 220, 190), 1, cv2.LINE_AA)

            elif btn["type"] == "clear":
                bg = (60, 30, 35) if is_hover else (45, 25, 30)
                cv2.rectangle(img, (x1, y1), (x2, y2), bg, -1)
                cv2.rectangle(img, (x1, y1), (x2, y2), (100, 100, 255) if is_hover else (110, 55, 65), 1, cv2.LINE_AA)
                cv2.putText(img, "TEMIZLE", (x1 + 6, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 140, 255), 1, cv2.LINE_AA)
                cv2.putText(img, "[C]/Yumruk", (x1 + 4, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (180, 180, 210), 1, cv2.LINE_AA)

            # Dwell Bekleme İlerleme Çubuğu (Hover animasyonu)
            if is_hover and hover_progress > 0.0:
                prog_w = int((x2 - x1) * min(1.0, hover_progress))
                cv2.rectangle(img, (x1, y2 - 4), (x1 + prog_w, y2), (0, 255, 230), -1)

    def draw_status_bar(self, img, mode_text, mode_color):
        """Ekranın alt kısmında durum bilgisi, aktif araçlar ve kısayolları gösterir."""
        bar_h = 36
        y1 = self.height - bar_h
        y2 = self.height

        sub = img[y1:y2, 0:self.width]
        overlay = np.zeros_like(sub)
        cv2.rectangle(overlay, (0, 0), (self.width, bar_h), (14, 17, 21), -1)
        cv2.addWeighted(sub, 0.3, overlay, 0.7, 0, sub)
        cv2.line(img, (0, y1), (self.width, y1), (45, 52, 62), 1)

        # Aktif Hareket Modu
        cv2.circle(img, (18, y1 + 18), 6, mode_color, -1, cv2.LINE_AA)
        cv2.putText(img, f"MOD: {mode_text}", (32, y1 + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        # Aktif Araçlar Özeti
        tool_info = f"Firca: {self.brush_style} | Sekil: {self.shape_mode}"
        cv2.putText(img, tool_info, (int(self.width * 0.28), y1 + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 200), 1, cv2.LINE_AA)

        # Kısayol Tuşları Bilgisi
        shortcuts = "[Z] Geri | [Y] Ileri | [B] Firca | [M] Sekil | [T] Tahta | [P] PiP | [S] Kaydet | [Q] Cikis"
        (sw, _), _ = cv2.getTextSize(shortcuts, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.putText(img, shortcuts, (self.width - sw - 12, y1 + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140, 150, 165), 1, cv2.LINE_AA)

    def draw_fist_progress(self, img, center_pt):
        """Yumruk yapıldığında temizleme geri sayım halkasını çizer."""
        progress = min(1.0, self.fist_frames / self.FIST_THRESHOLD)
        cx, cy = center_pt
        radius = 55

        cv2.circle(img, (cx, cy), radius, (55, 55, 60), 4, cv2.LINE_AA)
        end_angle = int(360 * progress)
        if end_angle > 0:
            cv2.ellipse(img, (cx, cy), (radius, radius), -90, 0, end_angle, (0, 70, 255), 6, cv2.LINE_AA)

        pct_txt = f"{int(progress * 100)}%"
        (tw, th), _ = cv2.getTextSize(pct_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.putText(img, pct_txt, (cx - tw // 2, cy + th // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        label = "TEMIZLENIYOR..."
        (lw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        cv2.putText(img, label, (cx - lw // 2, cy - radius - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 100, 255), 2, cv2.LINE_AA)

    def draw_pip_window(self, display_img, camera_img):
        """Dijital tahta modlarında sağ altta canlı mini webcam önizlemesi sunar."""
        if not self.show_pip:
            return

        pip_w = 210
        pip_h = int(pip_w * (self.height / self.width))
        pip_x2 = self.width - 16
        pip_x1 = pip_x2 - pip_w
        pip_y2 = self.height - 44
        pip_y1 = pip_y2 - pip_h

        if pip_y1 < self.header_height:
            return

        small_cam = cv2.resize(camera_img, (pip_w, pip_h), interpolation=cv2.INTER_AREA)

        # Çerçeve ve etiket
        cv2.rectangle(display_img, (pip_x1 - 2, pip_y1 - 2), (pip_x2 + 2, pip_y2 + 2), (0, 230, 255), 2)
        display_img[pip_y1:pip_y2, pip_x1:pip_x2] = small_cam

        cv2.rectangle(display_img, (pip_x1, pip_y1), (pip_x1 + 92, pip_y1 + 18), (18, 22, 28), -1)
        cv2.putText(display_img, "PiP KAMERA [P]", (pip_x1 + 5, pip_y1 + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 200), 1, cv2.LINE_AA)

    def trigger_button(self, btn):
        """Butona tıklandığında ilgili eylemi çalıştırır."""
        btype = btn["type"]

        if btype == "color":
            self.selected_color_idx = btn["index"]
            self.is_eraser = False
            self.current_color = COLORS[self.selected_color_idx]["bgr"]
            self.toast.show(f"Renk: {btn['label']}", duration=1.2, color=self.current_color)

        elif btype == "brush_style":
            curr_idx = BRUSH_STYLES.index(self.brush_style)
            self.brush_style = BRUSH_STYLES[(curr_idx + 1) % len(BRUSH_STYLES)]
            self.toast.show(f"Firca: {self.brush_style}", duration=1.3, color=(0, 255, 220))

        elif btype == "shape_mode":
            curr_idx = SHAPE_MODES.index(self.shape_mode)
            self.shape_mode = SHAPE_MODES[(curr_idx + 1) % len(SHAPE_MODES)]
            self.shape_start = None
            self.shape_preview_end = None
            self.toast.show(f"Sekil: {self.shape_mode}", duration=1.3, color=(255, 200, 50))

        elif btype == "size":
            self.brush_size_idx = (self.brush_size_idx + 1) % len(BRUSH_SIZES)
            cur = BRUSH_SIZES[self.brush_size_idx]
            self.toast.show(f"Boyut: {cur['name']} ({cur['size']}px)", duration=1.2)

        elif btype == "eraser":
            self.is_eraser = not self.is_eraser
            st = "AKTIF" if self.is_eraser else "KAPALI"
            self.toast.show(f"Silgi: {st}", duration=1.2, color=(0, 255, 255))

        elif btype == "undo":
            self.undo()

        elif btype == "redo":
            self.redo()

        elif btype == "view_mode":
            modes = ["camera", "whiteboard", "blackboard"]
            curr_idx = modes.index(self.view_mode)
            self.view_mode = modes[(curr_idx + 1) % len(modes)]
            lbls = {"camera": "KAMERA", "whiteboard": "BEYAZ TAHTA", "blackboard": "SIYAH TAHTA"}
            self.toast.show(f"Tahta: {lbls.get(self.view_mode, '')}", duration=1.3)

        elif btype == "save":
            self.save_canvas()

        elif btype == "clear":
            self.save_undo_state()
            self.canvas[:] = 0
            self.toast.show("Tuval Temizlendi! (Geri Al [Z])", duration=1.8, color=(0, 100, 255))

    def save_canvas(self):
        """Çizimi PNG dosyası olarak kaydeder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"air_canvas_{timestamp}.png"
        filepath = os.path.join(CURRENT_DIR, filename)

        if self.view_mode == "whiteboard":
            gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
            inv_mask = cv2.bitwise_not(mask)
            white_bg = np.full_like(self.canvas, 255)
            save_img = cv2.bitwise_and(white_bg, white_bg, mask=inv_mask)
            fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
            save_img = cv2.add(save_img, fg)
        else:
            save_img = self.canvas

        cv2.imwrite(filepath, save_img)
        print(f"[+] Cizim kaydedildi: {filepath}")
        self.toast.show(f"Kaydedildi: {filename}", duration=2.2, color=(0, 255, 100))

    def run(self):
        """Uygulamanın ana işlem döngüsü."""
        print("\n" + "=" * 60)
        print("  HAVADA EL CIZIMI (AIR CANVAS PRO) BASLATILDI")
        print("=" * 60)
        print(" [!] Isaret Parmagi: Cizim / Sekil Cizme")
        print(" [!] Isaret + Orta Parmak: Secim / Menu Modu")
        print(" [!] Pinch (Kistirma): Menude Aninda Buton Tiklama")
        print(" [!] Yumruk Yapma: Tuvali Temizleme (Geri Alinabilir)")
        print(" [!] [Z]: Geri Al | [Y]: Ileri Al | [B]: Firca | [M]: Sekil")
        print(" [!] [P]: PiP Kamera | [T]: Tahta Modu | [S]: Kaydet")
        print("=" * 60 + "\n")

        fps_time = time.time()
        fps = 0

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # Doğal ayna efekti
            frame = cv2.flip(frame, 1)

            # FPS Hesaplama
            cur_time = time.time()
            if cur_time - fps_time > 0:
                fps = int(0.9 * fps + 0.1 * (1.0 / (cur_time - fps_time)))
            fps_time = cur_time

            # MediaPipe Tespit
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.landmarker.detect(mp_image)

            mode_text = "EL BEKLENIYOR"
            mode_color = (140, 140, 140)
            hovered_button = None
            hover_progress = 0.0

            active_cursor_pt = None
            active_cursor_color = None

            if detection_result.hand_landmarks:
                landmarks = detection_result.hand_landmarks[0]
                index_up, middle_up, ring_up, pinky_up, is_fist, is_pinch, pts = self.process_finger_states(landmarks)

                x8, y8 = pts[8]      # İşaret parmağı ucu
                x12, y12 = pts[12]   # Orta parmak ucu

                if self.show_skeleton:
                    self.draw_skeleton(frame, pts)

                # -------------------------------------------------------------
                # 1. YUMRUK MODU: Tuval Temizleme
                # -------------------------------------------------------------
                if is_fist:
                    mode_text = "YUMRUK: TEMIZLENIYOR"
                    mode_color = (0, 70, 255)
                    self.prev_x, self.prev_y = 0, 0
                    self.is_drawing_stroke = False
                    self.shape_start = None
                    self.fist_frames += 1

                    palm_center = ((pts[0][0] + pts[9][0]) // 2, (pts[0][1] + pts[9][1]) // 2)
                    self.draw_fist_progress(frame, palm_center)

                    if self.fist_frames >= self.FIST_THRESHOLD:
                        self.save_undo_state()
                        self.canvas[:] = 0
                        self.fist_frames = 0
                        self.toast.show("Tuval Temizlendi! (Geri Al [Z])", duration=1.8, color=(0, 100, 255))
                else:
                    self.fist_frames = 0

                # -------------------------------------------------------------
                # 2. SEÇİM & MENÜ MODU: İşaret + Orta Parmak Açık
                # -------------------------------------------------------------
                if index_up and middle_up and not ring_up and not pinky_up and not is_fist:
                    mode_text = "PINCH / SECIM MODU" if is_pinch else "SECIM / MENU MODU"
                    mode_color = (0, 240, 255)
                    self.prev_x, self.prev_y = 0, 0
                    self.is_drawing_stroke = False

                    # Eğer şekil çiziliyorduysa iptal et
                    self.shape_start = None
                    self.shape_preview_end = None

                    sel_x = (x8 + x12) // 2
                    sel_y = (y8 + y12) // 2
                    active_cursor_pt = (sel_x, sel_y)
                    active_cursor_color = (0, 240, 255)

                    # Üst menü buton kontrolü
                    if sel_y < self.header_height:
                        for btn in self.buttons:
                            bx1, by1, bx2, by2 = btn["rect"]
                            if bx1 <= sel_x <= bx2 and by1 <= sel_y <= by2:
                                hovered_button = btn
                                now = time.time()

                                if self.hovered_btn != btn:
                                    self.hovered_btn = btn
                                    self.hover_start_time = now

                                hover_elapsed = now - self.hover_start_time
                                hover_progress = min(1.0, hover_elapsed / self.DWELL_TIME)

                                # Dwell süresi dolduysa veya Pinch (kıstırma) yapıldıysa tetikle
                                can_click = (now - self.last_action_time > self.ACTION_COOLDOWN)
                                if can_click and (hover_progress >= 1.0 or is_pinch):
                                    self.last_action_time = now
                                    self.hover_start_time = now + 0.3
                                    self.trigger_button(btn)
                                break
                        else:
                            self.hovered_btn = None
                    else:
                        self.hovered_btn = None

                # -------------------------------------------------------------
                # 3. ÇİZİM MODU: Yalnızca İşaret Parmağı Açık
                # -------------------------------------------------------------
                elif index_up and not middle_up and not ring_up and not pinky_up and not is_fist:
                    mode_text = f"CIZIM ({self.shape_mode})"
                    mode_color = (0, 255, 0)
                    thickness = self.get_brush_thickness()

                    # Renk seçimi
                    if self.is_eraser:
                        draw_color = (0, 0, 0)
                        cursor_color = (255, 255, 255)
                    elif self.brush_style == "Gokkusagi":
                        draw_color = self.get_rainbow_color()
                        cursor_color = draw_color
                    else:
                        draw_color = self.current_color
                        cursor_color = self.current_color

                    active_cursor_pt = (x8, y8)
                    active_cursor_color = cursor_color

                    # Menü çubuğunun altında ise çizim yap
                    if y8 > self.header_height:
                        # Yumuşatma filtresi
                        if self.prev_x == 0 and self.prev_y == 0:
                            curr_x, curr_y = x8, y8
                        else:
                            curr_x = int(self.smooth_factor * x8 + (1 - self.smooth_factor) * self.prev_x)
                            curr_y = int(self.smooth_factor * y8 + (1 - self.smooth_factor) * self.prev_y)

                        # Şekil Modu: Serbest Çizim
                        if self.shape_mode == "Serbest":
                            if not self.is_drawing_stroke:
                                self.save_undo_state()
                                self.is_drawing_stroke = True

                            if self.prev_x != 0 and self.prev_y != 0:
                                if self.is_eraser:
                                    cv2.line(self.canvas, (self.prev_x, self.prev_y), (curr_x, curr_y), (0, 0, 0), thickness, cv2.LINE_AA)
                                    cv2.circle(self.canvas, (curr_x, curr_y), thickness // 2, (0, 0, 0), -1, cv2.LINE_AA)
                                elif self.brush_style == "Neon":
                                    self.draw_neon_segment(self.canvas, (self.prev_x, self.prev_y), (curr_x, curr_y), draw_color, thickness)
                                else:
                                    cv2.line(self.canvas, (self.prev_x, self.prev_y), (curr_x, curr_y), draw_color, thickness, cv2.LINE_AA)
                                    cv2.circle(self.canvas, (curr_x, curr_y), thickness // 2, draw_color, -1, cv2.LINE_AA)

                                # Parçacık saçılımı
                                if not self.is_eraser:
                                    self.particles.emit(curr_x, curr_y, cursor_color, count=2)

                            self.prev_x, self.prev_y = curr_x, curr_y

                        # Şekil Modları: Düz Çizgi, Dikdörtgen, Daire
                        else:
                            if self.shape_start is None:
                                self.shape_start = (curr_x, curr_y)
                            self.shape_preview_end = (curr_x, curr_y)
                            self.prev_x, self.prev_y = curr_x, curr_y

                    else:
                        self.prev_x, self.prev_y = 0, 0
                else:
                    # Parmak indirildiğinde şekli tuvale aktar
                    if self.shape_start is not None and self.shape_preview_end is not None:
                        self.commit_shape(self.shape_start, self.shape_preview_end)
                        self.shape_start = None
                        self.shape_preview_end = None

                    self.prev_x, self.prev_y = 0, 0
                    self.is_drawing_stroke = False
                    self.hovered_btn = None
            else:
                if self.shape_start is not None and self.shape_preview_end is not None:
                    self.commit_shape(self.shape_start, self.shape_preview_end)
                    self.shape_start = None
                    self.shape_preview_end = None

                self.prev_x, self.prev_y = 0, 0
                self.fist_frames = 0
                self.is_drawing_stroke = False
                self.hovered_btn = None

            # -----------------------------------------------------------------
            # TUVAL VE GÖRÜNTÜ BİRLEŞTİRME (BLENDING)
            # -----------------------------------------------------------------
            gray_canvas = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray_canvas, 10, 255, cv2.THRESH_BINARY)
            inv_mask = cv2.bitwise_not(mask)

            if self.view_mode == "camera":
                frame_bg = cv2.bitwise_and(frame, frame, mask=inv_mask)
                frame_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
                display_frame = cv2.add(frame_bg, frame_fg)
            elif self.view_mode == "whiteboard":
                white_bg = np.full_like(frame, 255)
                white_bg = cv2.bitwise_and(white_bg, white_bg, mask=inv_mask)
                frame_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
                display_frame = cv2.add(white_bg, frame_fg)
            else:  # "blackboard"
                display_frame = self.canvas.copy()

            # Dijital Tahtada PiP Mini Kamera ve İskelet
            if self.view_mode in ["whiteboard", "blackboard"]:
                self.draw_pip_window(display_frame, frame)
                if self.show_skeleton and detection_result.hand_landmarks:
                    self.draw_skeleton(display_frame, pts)

            # Şekil Canlı Önizlemesi
            if self.shape_start is not None and self.shape_preview_end is not None:
                p_col = (0, 240, 255) if self.brush_style == "Gokkusagi" else self.current_color
                p_th = self.get_brush_thickness()
                s_pt = self.shape_start
                e_pt = self.shape_preview_end

                if self.shape_mode == "Cizgi":
                    cv2.line(display_frame, s_pt, e_pt, p_col, p_th, cv2.LINE_AA)
                elif self.shape_mode == "Dikdortgen":
                    cv2.rectangle(display_frame, s_pt, e_pt, p_col, p_th, cv2.LINE_AA)
                    w_box = abs(e_pt[0] - s_pt[0])
                    h_box = abs(e_pt[1] - s_pt[1])
                    cv2.putText(display_frame, f"{w_box}x{h_box}px", (e_pt[0] + 8, e_pt[1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 230), 1, cv2.LINE_AA)
                elif self.shape_mode == "Daire":
                    rad = int(math.hypot(e_pt[0] - s_pt[0], e_pt[1] - s_pt[1]))
                    cv2.circle(display_frame, s_pt, rad, p_col, p_th, cv2.LINE_AA)
                    cv2.circle(display_frame, s_pt, 3, p_col, -1)
                    cv2.putText(display_frame, f"r={rad}px", (e_pt[0] + 8, e_pt[1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 230), 1, cv2.LINE_AA)

            # Parçacık Animasyonunu Güncelle ve Çiz
            self.particles.update_and_draw(display_frame)

            # İmleç Çizimi
            if active_cursor_pt is not None and active_cursor_color is not None:
                cx, cy = active_cursor_pt
                if mode_text.startswith("SECIM"):
                    cv2.circle(display_frame, (cx, cy), 18, active_cursor_color, 2, cv2.LINE_AA)
                    cv2.circle(display_frame, (cx, cy), 4, active_cursor_color, -1, cv2.LINE_AA)
                else:
                    t_size = self.get_brush_thickness()
                    cv2.circle(display_frame, (cx, cy), t_size // 2 + 2, active_cursor_color, 2, cv2.LINE_AA)
                    cv2.circle(display_frame, (cx, cy), 3, active_cursor_color, -1, cv2.LINE_AA)

            # Üst Menü Çubuğunu Çiz
            self.draw_toolbar(display_frame, hover_btn=hovered_button, hover_progress=hover_progress)

            # Alt Durum Çubuğunu Çiz
            self.draw_status_bar(display_frame, mode_text, mode_color)

            # Bildirimleri Çiz
            self.toast.draw(display_frame)

            # FPS Göstergesi
            cv2.putText(display_frame, f"FPS: {fps}", (self.width - 95, self.header_height + 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 100), 1, cv2.LINE_AA)

            # Görüntüyü Ekrana Ver
            cv2.imshow("Air Canvas Pro - Havada El Cizimi", display_frame)

            # Klavye Girdileri
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('z') or key == ord('Z'):
                self.undo()
            elif key == ord('y') or key == ord('Y'):
                self.redo()
            elif key == ord('b') or key == ord('B'):
                curr_idx = BRUSH_STYLES.index(self.brush_style)
                self.brush_style = BRUSH_STYLES[(curr_idx + 1) % len(BRUSH_STYLES)]
                self.toast.show(f"Firca: {self.brush_style}", duration=1.3, color=(0, 255, 220))
            elif key == ord('m') or key == ord('M'):
                curr_idx = SHAPE_MODES.index(self.shape_mode)
                self.shape_mode = SHAPE_MODES[(curr_idx + 1) % len(SHAPE_MODES)]
                self.shape_start = None
                self.shape_preview_end = None
                self.toast.show(f"Sekil: {self.shape_mode}", duration=1.3, color=(255, 200, 50))
            elif key == ord('e') or key == ord('E'):
                self.is_eraser = not self.is_eraser
                st = "AKTIF" if self.is_eraser else "KAPALI"
                self.toast.show(f"Silgi: {st}", duration=1.2, color=(0, 255, 255))
            elif key == ord('c') or key == ord('C'):
                self.save_undo_state()
                self.canvas[:] = 0
                self.toast.show("Tuval Temizlendi! (Geri Al [Z])", duration=1.8, color=(0, 100, 255))
            elif key == ord('s') or key == ord('S'):
                self.save_canvas()
            elif key == ord('t') or key == ord('T'):
                modes = ["camera", "whiteboard", "blackboard"]
                curr_idx = modes.index(self.view_mode)
                self.view_mode = modes[(curr_idx + 1) % len(modes)]
                lbls = {"camera": "KAMERA", "whiteboard": "BEYAZ TAHTA", "blackboard": "SIYAH TAHTA"}
                self.toast.show(f"Tahta: {lbls.get(self.view_mode, '')}", duration=1.3)
            elif key == ord('p') or key == ord('P'):
                self.show_pip = not self.show_pip
                st = "Acik" if self.show_pip else "Kapali"
                self.toast.show(f"PiP Mini Kamera: {st}", duration=1.2)
            elif key == ord('h') or key == ord('H'):
                self.show_skeleton = not self.show_skeleton
                status = "Acik" if self.show_skeleton else "Kapali"
                self.toast.show(f"El Iskeleti: {status}", duration=1.2)

        self.cap.release()
        cv2.destroyAllWindows()
        self.landmarker.close()
        print("[+] Air Canvas basariyla kapatildi.")


if __name__ == "__main__":
    app = AirCanvas(camera_idx=0)
    app.run()
