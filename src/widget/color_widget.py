from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor

class ColorWidget(QWidget):

    def __init__(self, color, size):

        super(ColorWidget, self).__init__()

        self.setAutoFillBackground(True)
        self.setFixedSize(size)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)
