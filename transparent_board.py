import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QToolBar,
                             QAction, QColorDialog, QSlider, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QCursor, QIcon


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.drawing = False
        self.last_point = QPoint()
        self.tool = "pen"  # "pen" or "eraser"
        self.pen_color = QColor(255, 0, 0)  # 기본 빨간색
        self.pen_width = 3
        self.eraser_width = 30
        self.pixmap = None

    def resizeEvent(self, event):
        if self.pixmap is None or self.pixmap.size() != self.size():
            new_pixmap = QPixmap(self.size())
            new_pixmap.fill(Qt.transparent)
            if self.pixmap:
                painter = QPainter(new_pixmap)
                painter.drawPixmap(0, 0, self.pixmap)
                painter.end()
            self.pixmap = new_pixmap
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and self.pixmap:
            painter = QPainter(self.pixmap)
            if self.tool == "pen":
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.last_point, event.pos())
            elif self.tool == "eraser":
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.setPen(QPen(Qt.transparent, self.eraser_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(self.last_point, event.pos())
            painter.end()
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def clear(self):
        if self.pixmap:
            self.pixmap.fill(Qt.transparent)
            self.update()


class TransparentBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("투명 칠판")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 1200, 700)

        # 드래그 관련 변수
        self._drag_pos = None
        self._resizing = False

        self._init_ui()

    def _init_ui(self):
        # 메인 위젯
        self.central = QWidget(self)
        self.central.setObjectName("central")
        self.central.setStyleSheet("""
            #central {
                background: transparent;
                border: 2px solid rgba(100, 149, 237, 180);
                border-radius: 8px;
            }
        """)
        self.setCentralWidget(self.central)

        from PyQt5.QtWidgets import QVBoxLayout
        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 툴바 (드래그 핸들 겸) ──
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(44)
        self.toolbar.setStyleSheet("""
            background: rgba(30, 30, 60, 210);
            border-radius: 6px;
        """)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(6)

        def btn(text, tooltip, slot, checked=False):
            from PyQt5.QtWidgets import QPushButton
            b = QPushButton(text)
            b.setToolTip(tooltip)
            b.setCheckable(True)
            b.setChecked(checked)
            b.setFixedSize(70, 32)
            b.setStyleSheet("""
                QPushButton {
                    background: rgba(80,80,120,200);
                    color: white; border-radius: 5px;
                    font-size: 13px; font-weight: bold;
                }
                QPushButton:checked { background: rgba(100,180,255,220); color: #111; }
                QPushButton:hover   { background: rgba(120,120,180,220); }
            """)
            b.clicked.connect(slot)
            return b

        self.pen_btn = btn("✏️ 펜", "펜 도구", self._use_pen, checked=True)
        self.eraser_btn = btn("🧹 지우개", "지우개 도구", self._use_eraser)

        # 색상 버튼
        from PyQt5.QtWidgets import QPushButton
        self.color_btn = QPushButton("🎨 색상")
        self.color_btn.setFixedSize(70, 32)
        self.color_btn.setToolTip("펜 색상 선택")
        self.color_btn.setStyleSheet("""
            QPushButton {
                background: rgba(80,80,120,200);
                color: white; border-radius: 5px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(120,120,180,220); }
        """)
        self.color_btn.clicked.connect(self._pick_color)

        # 굵기 슬라이더
        size_label = QLabel("굵기:")
        size_label.setStyleSheet("color: white; font-size: 12px;")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 20)
        self.size_slider.setValue(3)
        self.size_slider.setFixedWidth(80)
        self.size_slider.setStyleSheet("QSlider::handle:horizontal { background: #64b5f6; }")
        self.size_slider.valueChanged.connect(self._change_size)

        # 지우개 크기 슬라이더
        esize_label = QLabel("지우개:")
        esize_label.setStyleSheet("color: white; font-size: 12px;")
        self.esize_slider = QSlider(Qt.Horizontal)
        self.esize_slider.setRange(10, 80)
        self.esize_slider.setValue(30)
        self.esize_slider.setFixedWidth(80)
        self.esize_slider.setStyleSheet("QSlider::handle:horizontal { background: #ffb74d; }")
        self.esize_slider.valueChanged.connect(self._change_esize)

        # 전체 지우기
        clear_btn = QPushButton("🗑️ 전체")
        clear_btn.setFixedSize(70, 32)
        clear_btn.setToolTip("전체 지우기")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180,60,60,200);
                color: white; border-radius: 5px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(220,80,80,220); }
        """)
        clear_btn.clicked.connect(self._clear)

        # 닫기
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setToolTip("닫기")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180,60,60,200);
                color: white; border-radius: 5px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(220,80,80,220); }
        """)
        close_btn.clicked.connect(self.close)

        toolbar_layout.addWidget(self.pen_btn)
        toolbar_layout.addWidget(self.eraser_btn)
        toolbar_layout.addWidget(self.color_btn)
        toolbar_layout.addWidget(size_label)
        toolbar_layout.addWidget(self.size_slider)
        toolbar_layout.addWidget(esize_label)
        toolbar_layout.addWidget(self.esize_slider)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(clear_btn)
        toolbar_layout.addWidget(close_btn)

        # 드래그 이벤트 툴바에 설치
        self.toolbar.mousePressEvent = self._tb_press
        self.toolbar.mouseMoveEvent = self._tb_move
        self.toolbar.mouseReleaseEvent = self._tb_release

        # 캔버스
        self.canvas = Canvas()

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas, 1)

        # 색상 미리보기 표시
        self._update_color_btn()

    # ── 툴바 드래그 ──
    def _tb_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _tb_move(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def _tb_release(self, event):
        self._drag_pos = None

    # ── 도구 선택 ──
    def _use_pen(self):
        self.canvas.tool = "pen"
        self.pen_btn.setChecked(True)
        self.eraser_btn.setChecked(False)

    def _use_eraser(self):
        self.canvas.tool = "eraser"
        self.eraser_btn.setChecked(True)
        self.pen_btn.setChecked(False)

    def _pick_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self, "펜 색상 선택")
        if color.isValid():
            self.canvas.pen_color = color
            self._update_color_btn()
            self._use_pen()

    def _update_color_btn(self):
        c = self.canvas.pen_color
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({c.red()},{c.green()},{c.blue()},200);
                color: {'black' if c.lightness() > 128 else 'white'};
                border-radius: 5px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba({c.red()},{c.green()},{c.blue()},255);
            }}
        """)

    def _change_size(self, val):
        self.canvas.pen_width = val

    def _change_esize(self, val):
        self.canvas.eraser_width = val

    def _clear(self):
        self.canvas.clear()

    # ── 마우스 통과 (캔버스 영역) ──
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("투명 칠판")
    window = TransparentBoard()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
