import os
import sys
import yaml
import pprint
import numpy as np

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QWidget
)
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

import pickle
from multiprocessing import shared_memory

app_version = '1.0'

shm_config = shared_memory.SharedMemory(name="config", create=True, size=2048)
shm_status = shared_memory.SharedMemory(name="status", create=True, size=5)
shm_status.buf[:5] = bytes([0, 0, 0, 0, 0])

with open('config/config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    serialized = pickle.dumps(config)
    shm_config.buf[:len(serialized)] = serialized

for i in range(config['ch_num']):

    camera = config['cameras'][i]
    camera_url = camera['url']
    
    os.system(f"pm2 start src/video_capture.py --name cam_{i} -- {camera_url} {i}")
    os.system(f"pm2 start src/detector.py --name det_{i} -- {i}")

import widget.camera_widget as camera
import widget.log_widget as log
import widget.color_widget as color

class MainWindow(QMainWindow):

    def __init__(self):
        
        super(MainWindow, self).__init__()

        self.setWindowTitle(f"Traffic Sense Pro V{app_version}")

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setMovable(True)

        for i in range(config['ch_num']):
            tabs.addTab(camera.CameraWidget(i), f"ch_{i}")

        self.setCentralWidget(tabs)

        h_layout_1 = QHBoxLayout()
        h_layout_2 = QHBoxLayout()

        v_layout_1 = QVBoxLayout()
        v_layout_2 = QVBoxLayout()

        v_layout_1.addWidget(tabs)

        h_layout_2.addWidget(color.ColorWidget('black', QSize(1200, 300)))

        h_layout_1.addLayout(v_layout_1)
        h_layout_1.addLayout(v_layout_2)

        layout = QVBoxLayout()
        layout.addLayout(h_layout_1)
        layout.addLayout(h_layout_2)
        # layout.addWidget(log_widget)
        
        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

# QML Code 
# app = QGuiApplication()

# engine = QQmlApplicationEngine()
# engine.quit.connect(app.quit)
# engine.load('src/layout/main.qml')

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

print("Quit Application...")
os.system("pm2 kill")