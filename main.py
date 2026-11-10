import sys
import math
import struct
import random
import pyaudio
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 800

class VTuberOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.is_talking = False
        self.is_blinking = False
        self.initUI()
        self.initAudio()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        
        # Cargar las 4 imágenes
        self.img_closed = QPixmap("avatar_cerrado.png")
        self.img_open = QPixmap("avatar_abierto.png")
        self.img_blink = QPixmap("avatar_parpadeo.png")
        self.img_talk_blink = QPixmap("avatar_hablando_parpadeo.png")

        # Reescalar imágenes
        size = 250
        self.img_closed = self.img_closed.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_open = self.img_open.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_blink = self.img_blink.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_talk_blink = self.img_talk_blink.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.label.setPixmap(self.img_closed)
        self.resize(size, size)

        # Timer principal para detectar voz (~30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_avatar)
        self.timer.start(30)

        # Timer para parpadeo aleatorio
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.trigger_blink)
        self.schedule_next_blink()

    def schedule_next_blink(self):
        # Parpadea aleatoriamente entre cada 2 y 5 segundos
        next_interval = random.randint(2000, 5000)
        self.blink_timer.start(next_interval)

    def trigger_blink(self):
        self.is_blinking = True
        self.update_sprite()
        # El parpadeo dura 150 milisegundos
        QTimer.singleShot(150, self.stop_blink)

    def stop_blink(self):
        self.is_blinking = False
        self.update_sprite()
        self.schedule_next_blink()

    def initAudio(self):
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
        except Exception:
            self.stream = None

    def update_avatar(self):
        if not self.stream:
            return
        try:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            count = len(data) // 2
            format_str = f"<{count}h"
            ints = struct.unpack(format_str, data)
            sum_squares = sum(val**2 for val in ints)
            rms = math.sqrt(sum_squares / count)

            self.is_talking = rms > THRESHOLD
            self.update_sprite()
        except Exception:
            pass

    def update_sprite(self):
        # Seleccionar la imagen adecuada según si habla y si parpadea
        if self.is_talking and self.is_blinking:
            self.label.setPixmap(self.img_talk_blink)
        elif self.is_talking:
            self.label.setPixmap(self.img_open)
        elif self.is_blinking:
            self.label.setPixmap(self.img_blink)
        else:
            self.label.setPixmap(self.img_closed)

    def closeEvent(self, event):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = VTuberOverlay()
    overlay.show()
    sys.exit(app.exec())
