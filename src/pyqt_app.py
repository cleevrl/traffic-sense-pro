import os
import sys
import yaml
import time
import numpy as np

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import *

from shared_memory_dict import SharedMemoryDict
from multiprocessing import shared_memory

os.system(f"pm2 kill")
app_version = '1.0'

smd= SharedMemoryDict(name="smd", size=2048)
shm_status = shared_memory.SharedMemory(name="status", create=True, size=5)
shm_status.buf[:5] = bytes([0, 0, 0, 0, 0])

with open('config/config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    smd['ch_num'] = config['ch_num']
    smd['cameras'] = config['cameras']
    smd['detectors'] = config['detectors']
    smd['hardware'] = config['hardware']

for i in range(smd['ch_num']):
    os.system(f"pm2 start src/video_capture.py --no-autorestart --name cam_{i} -- {smd['cameras'][i]['url']} {i}")
    os.system(f"pm2 start src/detector.py --no-autorestart --name det_{i} -- {i}")

import widget.channel_widget as channel
import widget.log_widget as log
import widget.color_widget as color

class MainWindow(QMainWindow):

    def __init__(self):
        
        super(MainWindow, self).__init__()

        self.setWindowTitle(f"Traffic Sense Pro V{app_version}")

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setMovable(True)

        for i in range(smd['ch_num']):
            tabs.addTab(channel.ChannelWidget(i), f"ch_{i}")

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

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()

print("Quit Application...")
os.system("pm2 kill")