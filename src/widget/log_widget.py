from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor


class LogWidget(QWidget):

    def __init__(self):

        super().__init__()
        self.init_ui()

    def init_ui(self):
        print("init ui ...")
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('yellow'))
        self.setPalette(palette)
