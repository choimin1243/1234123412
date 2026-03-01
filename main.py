import sys
import os
import yaml
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QColorDialog
from PyQt5.QtGui import QPainter, QPen, QImage, QColor
from PyQt5.QtCore import Qt, QPoint

def resource_path(relative_path):
    """ PyInstaller로 빌드 시 리소스 경로를 찾는 함수 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class TransparentBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        # YAML 설정 로드
        conf_path = resource_path('config.yaml')
        try:
            with open(conf_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except:
            self.config = {'pen': {'color': '#FF0000', 'size': 5}, 'eraser': {'size': 40}}

        self.init_ui()
        
        # 캔버스 초기화
        self.image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.transparent)
        
        self.drawing = False
        self.eraser_mode = False
        self.last_point = QPoint()

    def init_ui(self):
        self.setWindowTitle("교사용 투명 칠판")
        # 테두리 제거, 항상 위, 배경 투명 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showMaximized()

        # 툴바 생성 (드래그하여 이동 가능한 바 역할)
        self.toolbar = QToolBar("Tools")
        self.toolbar.setStyleSheet("background: rgba(240, 240, 240, 200); border-radius: 10px; padding: 5px;")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # 도구 액션 추가
        actions = [
            ("🖊️ 펜", self.set_pen),
            ("🧽 지우개", self.set_eraser),
            ("🎨 색상", self.change_color),
            ("🗑️ 전체 삭제", self.clear_board),
            ("❌ 종료", self.close)
        ]

        for text, slot in actions:
            act = QAction(text, self)
            act.triggered.connect(slot)
            self.toolbar.addAction(act)

    def set_pen(self): self.eraser_mode = False
    def set_eraser(self): self.eraser_mode = True
    
    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config['pen']['color'] = color.name()
            self.eraser_mode = False

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
    sys.exit(app.exec_())
