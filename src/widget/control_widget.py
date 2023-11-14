import os
import yaml
import pickle
import serial.tools.list_ports as lp

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QTextEdit,
    QHBoxLayout, QLabel, QComboBox, QGridLayout,
    QLineEdit, qApp, QStackedWidget
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QSize

import cv2
from multiprocessing import shared_memory

from play_sound import play_sound

shm_config = shared_memory.SharedMemory(name='config')
bytes_config = bytes(shm_config.buf[:])
config = pickle.loads(bytes_config)

shm_status = shared_memory.SharedMemory(name='status')

STATUS_NORMAL = 0
STATUS_EDITING = 1

class ReverseWidget(QWidget):

    def __init__(self):

        super(ReverseWidget, self).__init__()

        self.init_ui()

    def init_ui(self):

        layout = QGridLayout(self)

        self.setLayout(layout)

class ControlWidget(QWidget):

    def __init__(self, ch_id):

        super(ControlWidget, self).__init__()

        self.setFixedSize(QSize(400, 600))
        self.id = ch_id
        self.url = config['cameras'][ch_id]['url']
        self.type = config['cameras'][ch_id]['type']
        self.status = STATUS_NORMAL
        self.vms_status = ['OFF', 'NO ENTRY', 'F.NO ENTRY', 'SAFE']

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
        self.cb_model = QComboBox(self)
        self.cb_model.setEnabled(False)

        self.t_btn_edit_event = QPushButton("ADD EVENT", self)
        self.t_btn_edit_event.setCheckable(True)
        self.t_btn_edit_event.adjustSize()
        self.t_btn_edit_event.clicked[bool].connect(self.add_event)

        self.btn_save_event = QPushButton("SAVE EVENT", self)
        self.btn_save_event.adjustSize()
        self.btn_save_event.clicked.connect(self.save_event)
        self.btn_save_event.clicked

        self.cb_event_list = QComboBox(self)
        self.cb_event_list.setEnabled(False)

        detector_layout = QGridLayout()
        detector_layout.addWidget(QLabel("Model : "), 0, 0)
        detector_layout.addWidget(self.cb_model, 0, 1)
        detector_layout.addWidget(self.t_btn_edit_event, 1, 0)
        detector_layout.addWidget(self.btn_save_event, 1, 1)
        detector_layout.addWidget(self.cb_event_list, 2, 0)

        self.qw_reverse_event = QWidget(self)
        self.sw_event_edit = QStackedWidget(self)


        # COMM CONFIG
        self.cb_comm_driver = QComboBox(self)
        self.btn_comm_connect = QPushButton("CONNECT")
        self.btn_comm_connect.clicked.connect(self.connect_serial)

        list_driver = []
        ports = lp.comports()
        for port in ports:
            self.cb_comm_driver.addItem(port.device)
            list_driver.append(port.device)
        
        driver = config['comm']['driver']

        if driver in list_driver:
            self.cb_comm_driver.setEnabled(False)
            self.btn_comm_connect.setEnabled(False)
            self.cb_comm_driver.setCurrentText(driver)
            os.system(f"pm2 start src/uart.py --name serial -- {driver}")
        else:
            self.cb_comm_driver.setEnabled(True)
            self.btn_comm_connect.setEnabled(True)

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

        self.btn_test_speaker = QPushButton("SPK ON", self)
        self.btn_test_speaker.adjustSize()
        self.btn_test_speaker.clicked.connect(self.play_sound)

        self.t_btn_test_vms = QPushButton("VMS ON", self)
        self.t_btn_test_vms.setCheckable(True)
        self.t_btn_test_vms.adjustSize()
        self.t_btn_test_vms.clicked[bool].connect(self.test_vms)
        
        self.btn_change_vms = QPushButton("CHANGE", self)
        self.btn_change_vms.adjustSize()
        self.btn_change_vms.setEnabled(False)
        self.btn_change_vms.clicked.connect(self.change_vms)

        self.lb_vms_status = QLabel(f"{self.vms_status[0]}")

        test_layout = QGridLayout()
        test_layout.addWidget(self.t_btn_test_detect, 0, 0)
        test_layout.addWidget(self.btn_test_speaker, 0, 1)
        test_layout.addWidget(self.t_btn_test_vms, 1, 0)
        test_layout.addWidget(self.btn_change_vms, 1, 1)
        test_layout.addWidget(self.lb_vms_status, 1, 2)

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
        self.btn_exit.clicked.connect(qApp.quit)

        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.addWidget(self.btn_edit)
        edit_btn_layout.addWidget(self.btn_save)
        edit_btn_layout.addWidget(self.btn_cancel)
        edit_btn_layout.addWidget(self.btn_exit)

        layout = QVBoxLayout()
        layout.addLayout(camera_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(detector_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(comm_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(test_layout)
        layout.addWidget(QLabel("================================"))
        layout.addLayout(edit_btn_layout)

        self.setLayout(layout)

    def add_event(self, e):
        ...
    
    def save_event(self):
        ...

    def connect_serial(self):
        os.system(f"pm2 start src/uart.py --name serial -- {self.cb_comm_driver.currentText()}")
        config['comm']['driver'] = self.cb_comm_driver.currentText()

        with open('config/config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        self.cb_comm_driver.setEnabled(False)
        self.btn_comm_connect.setEnabled(False)

    def test_detect(self, e):
        if e:
            shm_status.buf[self.id] = 1
        else:
            shm_status.buf[self.id] = 0
    
    def play_sound(self):
        play_sound()

    def test_vms(self, e):

        if e:
            self.btn_change_vms.setEnabled(True)
            shm_status.buf[4] = 1

        else:
            self.btn_change_vms.setEnabled(False)
            shm_status.buf[4] = 0

        self.lb_vms_status.setText(self.vms_status[shm_status.buf[4]])
    
    def change_vms(self):
        cur_vms = shm_status.buf[4]
        if cur_vms == 3:
            shm_status.buf[4] = 1
        else:
            shm_status.buf[4] = cur_vms + 1

        self.lb_vms_status.setText(self.vms_status[shm_status.buf[4]])

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
            
            print("Change config -> restart program")

        else:
            cap.release()
            self.le_url.setText(self.url)
            self.cb_camera_type.setCurrentText(self.type)
            print("Failed Save ... Wrong URL")
      
    def change_type(self, e):
        print(f"change type -> {e}")
    