import sys
import os
import yaml
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction
from PyQt5.QtGui import QPainter, QPen, QImage, QColor
from PyQt5.QtCore import Qt, QPoint

def resource_path(relative_path):
    """ 실행 파일 내 임시 폴더(MEIPASS) 또는 로컬 경로에서 파일을 찾음 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TransparentBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 안전한 경로로 설정 로드
        conf_path = resource_path('config.yaml')
        if os.path.exists(conf_path):
            with open(conf_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 파일이 없을 경우 대비한 기본값
            self.config = {'pen': {'color': '#FF0000', 'size': 5}, 'eraser': {'size': 40}}

        self.init_ui()
        self.image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.transparent)
        self.drawing = False
        self.eraser_mode = False
        self.last_point = QPoint()

    def init_ui(self):
        self.setWindowTitle("Teacher's Board")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showMaximized()

        # 툴바 (바를 잡고 창 이동은 전체화면이라 의미가 적지만 도구 선택 창으로 활용)
        toolbar = QToolBar("Tools")
        toolbar.setStyleSheet("background: rgba(255, 255, 255, 180); border: 1px solid gray;")
        self.addToolBar(toolbar)

        actions = [
            ("🖊️ 펜", lambda: self.set_eraser(False)),
            ("🧽 지우개", lambda: self.set_eraser(True)),
            ("🗑️ 삭제", self.clear_board),
            ("❌ 종료", self.close)
        ]

        for text, slot in actions:
            act = QAction(text, self)
            act.triggered.connect(slot)
            toolbar.addAction(act)

    def set_eraser(self, mode):
        self.eraser_mode = mode

    def clear_board(self):
        self.image.fill(Qt.transparent)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            if self.eraser_mode:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                pen = QPen(Qt.transparent, self.config['eraser']['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else:
                pen = QPen(QColor(self.config['pen']['color']), self.config['pen']['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TransparentBoard()
    window.show()
    sys.exit(app.exec_())
