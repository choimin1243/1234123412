import sys
import yaml
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QVBoxLayout, QWidget
from PyQt5.QtGui import QPainter, QPen, QImage, QColor, QCursor
from PyQt5.QtCore import Qt, QPoint

class TransparentBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        # 설정 로드
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except:
            self.config = {'pen': {'color': '#FF0000', 'size': 3}, 'eraser': {'size': 30}}

        self.init_ui()
        
        self.image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.transparent)
        
        self.drawing = False
        self.eraser_mode = False
        self.last_point = QPoint()

    def init_ui(self):
        self.setWindowTitle("Teacher's Clear Board")
        # 투명 창 및 항상 위 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showMaximized()

        # 상단 조작 바 (ToolBar)
        self.toolbar = QToolBar("Controls", self)
        self.toolbar.setStyleSheet("background: rgba(50, 50, 50, 180); color: white; border-radius: 10px;")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        actions = [
            ("연필", self.set_pen),
            ("지우개", self.set_eraser),
            ("전체삭제", self.clear_board),
            ("종료", self.close)
        ]

        for text, slot in actions:
            act = QAction(text, self)
            act.triggered.connect(slot)
            self.toolbar.addAction(act)

    def set_pen(self): self.eraser_mode = False
    def set_eraser(self): self.eraser_mode = True
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
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TransparentBoard()
    window.show()
    sys.exit(app.exec_())
