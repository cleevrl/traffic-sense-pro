import os
import yaml
import pickle
import serial.tools.list_ports as lp

from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QTextEdit,
    QHBoxLayout, QLabel, QComboBox, QGridLayout,
    QLineEdit
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QSize, SLOT, SIGNAL

import cv2
from multiprocessing import shared_memory

from play_sound import play_sound

shm_config = shared_memory.SharedMemory(name='config')
bytes_config = bytes(shm_config.buf[:])
config = pickle.loads(bytes_config)


STATUS_NORMAL = 0
STATUS_EDITING = 1


class ControlWidget(QWidget):

    def __init__(self, ch_id):

        super(ControlWidget, self).__init__()

        self.setFixedSize(QSize(400, 600))
        self.id = ch_id
        self.url = config['cameras'][ch_id]['url']
        self.type = config['cameras'][ch_id]['type']
        self.status = STATUS_NORMAL

        self.width = config['cameras'][self.id]['width']
        self.height = config['cameras'][self.id]['height']
        
        self.init_ui()


    def init_ui(self):

        # CAMERA CONFIG

        self.le_url = QLineEdit(self.url)
        self.le_url.setEnabled(False)

        self.cb_camera_type = QComboBox(self)
        self.cb_camera_type.setEnabled(False)
        self.cb_camera_type.addItem("thermal")
        self.cb_camera_type.addItem("color")
        self.cb_camera_type.setCurrentText(self.type)
        self.cb_camera_type.currentTextChanged.connect(self.change_type)

        camera_layout = QGridLayout()
        camera_layout.addWidget(QLabel("ID : "), 0, 0)
        camera_layout.addWidget(QLabel("URL : "), 1, 0)
        camera_layout.addWidget(QLabel("Raw Size : "), 2, 0)
        camera_layout.addWidget(QLabel("Type : "), 3, 0)

        camera_layout.addWidget(QLabel(f"{self.id}"), 0, 1)
        camera_layout.addWidget(self.le_url, 1, 1)
        camera_layout.addWidget(QLabel(f"{self.width} * {self.height}"), 2, 1)
        camera_layout.addWidget(self.cb_camera_type, 3, 1)

        # DETECTOR CONFIG

        # COMM CONFIG
        self.cb_comm_driver = QComboBox(self)
        self.cb_comm_driver.setEnabled(True)
        self.btn_comm_connect = QPushButton("CONNECT")
        self.btn_comm_connect.clicked.connect(self.comm_connect)

        ports = lp.comports()
        for port in ports:
            self.cb_comm_driver.addItem(port.device)

        comm_layout = QGridLayout()
        comm_layout.addWidget(QLabel("Status : ") , 0, 0)
        comm_layout.addWidget(QLabel("Connected"), 0, 1)
        comm_layout.addWidget(QLabel("Driver : "), 1, 0)
        comm_layout.addWidget(self.cb_comm_driver, 1, 1)
        comm_layout.addWidget(self.btn_comm_connect, 1, 2)


        # TEST PANNEL
        self.t_btn_test_detect = QPushButton("DETECT", self)
        self.t_btn_test_detect.setCheckable(True)
        self.t_btn_test_detect.adjustSize()
        self.t_btn_test_detect.clicked[bool].connect(self.test_detect)

        self.t_btn_test_speaker = QPushButton("SPK ON", self)
        self.t_btn_test_speaker.adjustSize()
        self.t_btn_test_speaker.clicked.connect(self.play_sound)

        test_layout = QHBoxLayout()
        test_layout.addWidget(self.t_btn_test_detect)
        test_layout.addWidget(self.t_btn_test_speaker)

        # BOTTOM BTNS
        self.btn_edit = QPushButton("EDIT", self)
        self.btn_save = QPushButton("SAVE", self)
        self.btn_cancel = QPushButton("CANCEL", self)
        self.btn_exit = QPushButton("EXIT", self)
        
        self.btn_edit.adjustSize()
        self.btn_save.adjustSize()
        self.btn_cancel.adjustSize()
        self.btn_exit.adjustSize()

        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        
        self.btn_edit.clicked.connect(self.push_btn_edit)
        self.btn_save.clicked.connect(self.push_btn_save_and_cancel)
        self.btn_cancel.clicked.connect(self.push_btn_save_and_cancel)
        self.connect(self.btn_exit, SIGNAL("clicked()"), qApp, SLOT("quit()"))

        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.addWidget(self.btn_edit)
        edit_btn_layout.addWidget(self.btn_save)
        edit_btn_layout.addWidget(self.btn_cancel)
        edit_btn_layout.addWidget(self.btn_exit)

        layout = QVBoxLayout()
        layout.addLayout(camera_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(comm_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(test_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(edit_btn_layout)

        self.setLayout(layout)


    def comm_connect(self):
        print("")


    def test_detect(self, e):
        print(f"push {e}")

    
    def play_sound(self):
        play_sound()


    def push_btn_edit(self):
        self.status = STATUS_EDITING
        self.btn_edit.setEnabled(False)
        self.btn_save.setEnabled(True)
        self.btn_cancel.setEnabled(True)

        self.le_url.setEnabled(True)
        self.cb_camera_type.setEnabled(True)


    def push_btn_save_and_cancel(self):
        self.status = STATUS_NORMAL
        self.btn_edit.setEnabled(True)
        self.cb_camera_type.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        
        self.le_url.setEnabled(False)
        self.cb_camera_type.setEnabled(False)

        cap = cv2.VideoCapture(self.le_url.text())

        if cap.isOpened():
            self.url = self.le_url.text()
            self.type = self.cb_camera_type.currentText()

            config['cameras'][self.id]['url'] = self.url
            config['cameras'][self.id]['type'] = self.type

            with open('config/config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print("Change config -> restart progrma")

        else:
            cap.release()
            self.le_url.setText(self.url)
            self.cb_camera_type.setCurrentText(self.type)
            print("Failed Save ... Wrong URL")
      
    def change_type(self, e):
        print(f"change type -> {e}")
    