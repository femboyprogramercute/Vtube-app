import sys
import math
import struct
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
        self.initUI()
        self.initAudio()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        self.img_closed = QPixmap("avatar_cerrado.png")
        self.img_open = QPixmap("avatar_abierto.png")

        self.img_closed = self.img_closed.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_open = self.img_open.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.label.setPixmap(self.img_closed)
        self.resize(250, 250)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_avatar)
        self.timer.start(30)

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

            if rms > THRESHOLD:
                self.label.setPixmap(self.img_open)
            else:
                self.label.setPixmap(self.img_closed)
        except Exception:
            pass

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
