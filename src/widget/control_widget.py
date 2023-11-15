import os
import yaml
import pickle
import serial.tools.list_ports as lp

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QTextEdit,
    QHBoxLayout, QLabel, QComboBox, QGridLayout,
    QLineEdit, qApp, QStackedWidget, QRadioButton, QGroupBox
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QSize

import cv2
from multiprocessing import shared_memory

from play_sound import play_sound

shm_config = shared_memory.SharedMemory(name='config')
bytes_config = bytes(shm_config.buf[:])
config = pickle.loads(bytes_config)



