from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPalette, QColor

from shared_memory_dict import SharedMemoryDict


class ColorWidget(QWidget):

    def __init__(self, color, size):

        super(ColorWidget, self).__init__()

        self.setAutoFillBackground(True)
        self.setFixedSize(size)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)
