from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QThread, QTimer, QSize, Qt
from PyQt5.QtGui import QImage, QPixmap

import numpy as np
import pickle
import time
import cv2

import qimage2ndarray
from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict

import widget.control_widget as control
from multiprocessing import shared_memory

list_shm_raw_frame = []
list_shm_annotated_frame =[]
list_raw_frame = []
list_annotated_frame = []

shm_config = shared_memory.SharedMemory(name='config')
bytes_config = bytes(shm_config.buf[:])
config = pickle.loads(bytes_config)

while True:

    try:
        for i in range(config['ch_num']):
            
            camera = config['cameras'][i]
            width = camera['width']
            height = camera['height']

            list_shm_raw_frame.append(shared_memory.SharedMemory(name=f"raw_frame_{i}"))
            list_shm_annotated_frame.append(shared_memory.SharedMemory(name=f"annotated_frame_{i}"))

            list_raw_frame.append(np.ndarray((height, width, 3), dtype=np.uint8, buffer=list_shm_raw_frame[i].buf))
            list_annotated_frame.append(np.ndarray((height, width, 3), dtype=np.uint8, buffer=list_shm_annotated_frame[i].buf))

        break

    except FileNotFoundError:
        print("Not found shm, try 1 sec later...")
        time.sleep(1)
        continue


class FrameLabel(QWidget):

    def __init__(self, ch_id):

        super().__init__()
        self.id = ch_id
        self.width = config['cameras'][ch_id]['width']
        self.height = config['cameras'][ch_id]['height']
        self.init_ui()

        timer = QTimer(self)
        timer.timeout.connect(self.update_frame)
        timer.start(100)

    def init_ui(self):
        
        self.lb_frame = QLabel()
        self.lb_frame.setAlignment(Qt.AlignCenter)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.lb_frame)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


    def update_frame(self):
        frame = cv2.resize(list_annotated_frame[self.id], (800, 600), interpolation=cv2.INTER_CUBIC)
        # frame = cv2.resize(self.raw_frame, (800, 600), interpolation=cv2.INTER_CUBIC)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = qimage2ndarray.array2qimage(frame)
        self.lb_frame.setPixmap(QPixmap.fromImage(image))
    
    def mousePressEvent(self, event) -> None:
        print(event.position())
        return super().mousePressEvent(event)
        

class CameraWidget(QWidget):

    def __init__(self, ch_id):

        super().__init__()
        self.ch_id = ch_id
        self.init_ui()

    def init_ui(self):
        
        self.frame_label = FrameLabel(self.ch_id)
        
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.frame_label)
        self.main_layout.addWidget(control.ControlWidget(self.ch_id))

        self.setLayout(self.main_layout)
