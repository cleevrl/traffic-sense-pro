from PyQt5.QtWidgets import *
from PyQt5.QtCore import  QTimer, QSize, Qt
from PyQt5.QtGui import QImage, QPixmap

import yaml
import numpy as np
import time
import cv2
import os

import qimage2ndarray
from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict

from play_sound import play_sound

list_shm_raw_frame = []
list_shm_annotated_frame =[]
list_raw_frame = []
list_annotated_frame = []

shm_status = shared_memory.SharedMemory(name="status")
smd = SharedMemoryDict(name="smd", size=2048)

while True:

    try:
        for i in range(smd['ch_num']):
            
            width = smd['cameras'][i]['width']
            height = smd['cameras'][i]['height']

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
        self.width = smd['cameras'][ch_id]['width']
        self.height = smd['cameras'][ch_id]['height']
        
        self.mode = "normal"

        self.init_sl()
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

    def init_sl(self):
        self.single = smd['detectors'][self.id]['event']['single']
        self.sl_pts = []
        for pt in self.single:
            cal_pt = [int(pt[0] * 800), int(pt[1] * 600)]
            self.sl_pts.append(cal_pt)

    def update_frame(self):

        frame_type = self.parent().frame_type

        if frame_type == "annotated":
            frame = cv2.resize(list_annotated_frame[self.id], (800, 600), interpolation=cv2.INTER_CUBIC)
        elif frame_type == "raw":
            frame = cv2.resize(list_raw_frame[self.id], (800, 600), interpolation=cv2.INTER_CUBIC)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.polylines(frame, [np.array(self.sl_pts)], True, (255, 255, 0), 3)

        image = qimage2ndarray.array2qimage(frame)
        self.lb_frame.setPixmap(QPixmap.fromImage(image))
    
    def mousePressEvent(self, event) -> None:

        if self.parent().mode == "run" or self.mode == "normal":
            print("RUN or NORMAL MODE")
        
            return super().mousePressEvent(event)

        if event.button() & Qt.LeftButton:
            if len(self.sl_pts) >= 2:
                print("cannot add more pts for single line")
            else:
                self.sl_pts.append([event.x(), event.y()])
                print(f"add single line pt -> [{event.x()}, {event.y()}]")

        elif event.button() & Qt.RightButton:
            self.sl_pts.clear()

        return super().mousePressEvent(event)
    
    def check_draw_mode(self):
        
        if self.mode == "sl":
            return len(self.sl_pts) == 2

    def get_norm_sl(self):

        norms = []
        for pt in self.sl_pts:
            norms.append([round(pt[0] / 800, 3), round(pt[1] / 600, 3)])
        
        return norms
        
class ControlWidget(QWidget): 

    def __init__(self, ch_id):

        super(ControlWidget, self).__init__()

        self.setFixedSize(QSize(400, 600))
        self.id = ch_id
        self.url = smd['cameras'][ch_id]['url']
        self.type = smd['cameras'][ch_id]['type']
        self.vms_status = ['OFF', '(F)진입금지', '진입금지', '안\전운전', '금지', '안전']

        self.width = smd['cameras'][self.id]['width']
        self.height = smd['cameras'][self.id]['height']
        
        self.init_ui()


    def init_ui(self):

        # Channel Info
        self.le_url = QLineEdit(self.url)
        self.le_url.setEnabled(False)

        self.cb_camera_type = QComboBox(self)
        self.cb_camera_type.setEnabled(False)
        self.cb_camera_type.addItem("thermal")
        self.cb_camera_type.addItem("color")
        self.cb_camera_type.setCurrentText(self.type)
        self.cb_camera_type.currentTextChanged.connect(self.change_type)

        gl_channel_info = QGridLayout()
        gl_channel_info.addWidget(QLabel("ID : "), 0, 0)
        gl_channel_info.addWidget(QLabel("URL : "), 1, 0)
        gl_channel_info.addWidget(QLabel("Raw Size : "), 2, 0)
        gl_channel_info.addWidget(QLabel("Type : "), 3, 0)

        gl_channel_info.addWidget(QLabel(f"{self.id}"), 0, 1)
        gl_channel_info.addWidget(self.le_url, 1, 1)
        gl_channel_info.addWidget(QLabel(f"{self.width} * {self.height}"), 2, 1)
        gl_channel_info.addWidget(self.cb_camera_type, 3, 1)

        gb_channel_info = QGroupBox("Channel Info")
        gb_channel_info.setLayout(gl_channel_info)

        # Detector Config
        self.cb_model = QComboBox(self)
        self.cb_model.setEnabled(False)

        self.cb_event_list = QComboBox(self)
        self.cb_event_list.addItem("")
        self.cb_event_list.addItem("reverse")
        self.cb_event_list.addItem("left")
        self.cb_event_list.setCurrentText(smd['detectors'][self.id]['event']['type'])
        self.cb_event_list.setEnabled(False)
        
        self.r_btn_start_line = QRadioButton("Start Line")
        self.r_btn_start_line.setEnabled(False)
        self.r_btn_end_line = QRadioButton("End Line")
        self.r_btn_end_line.setEnabled(False)
        self.r_btn_single_line = QRadioButton("Single Line")
        self.r_btn_single_line.setEnabled(False)
        self.r_btn_single_line.clicked.connect(self.draw_single_line)
        self.r_btn_roi = QRadioButton("ROI")
        self.r_btn_roi.setEnabled(False)
        self.r_btn_normal = QRadioButton("Normal")
        self.r_btn_normal.setEnabled(False)

        if smd['detectors'][self.id]['enable']:
            self.t_btn_detector_enable = QPushButton("ACTIVE")
            self.t_btn_detector_enable.setCheckable(True)
            self.t_btn_detector_enable.setChecked(True)
        else:
            self.t_btn_detector_enable = QPushButton("DISABLE")
            self.t_btn_detector_enable.setCheckable(True)
            self.t_btn_detector_enable.setChecked(False)
        self.t_btn_detector_enable.adjustSize()
        self.t_btn_detector_enable.clicked[bool].connect(self.activate_detector)

        self.t_btn_frame_swap = QPushButton("ANNOTATED")
        self.t_btn_frame_swap.adjustSize()
        self.t_btn_frame_swap.setCheckable(True)
        self.t_btn_frame_swap.setChecked(True)
        self.t_btn_frame_swap.clicked[bool].connect(self.swap_frame)

        gl_detector_config = QGridLayout()
        gl_detector_config.addWidget(QLabel("Model : "), 0, 0)
        gl_detector_config.addWidget(self.cb_model, 0, 1)
        gl_detector_config.addWidget(QLabel("Event Type : "), 1, 0)
        gl_detector_config.addWidget(self.cb_event_list, 1, 1)
        gl_detector_config.addWidget(self.r_btn_start_line, 2, 0)
        gl_detector_config.addWidget(self.r_btn_end_line, 2, 1)
        gl_detector_config.addWidget(self.r_btn_roi, 3, 0)
        gl_detector_config.addWidget(self.r_btn_single_line, 3, 1)
        gl_detector_config.addWidget(self.r_btn_normal, 4, 0)
        gl_detector_config.addWidget(self.t_btn_detector_enable, 5, 0)
        gl_detector_config.addWidget(self.t_btn_frame_swap, 5, 1)

        gb_detector_config = QGroupBox("Detector Config")
        gb_detector_config.setLayout(gl_detector_config)

        # Hardware UI
        self.lb_comm_status = QLabel("NO DATA")
        self.cb_comm_driver = QComboBox(self)
        self.btn_comm_connect = QPushButton("CONNECT")
        self.btn_comm_connect.clicked.connect(self.connect_serial)

        # list_driver = os.popen("ls /dev/ttyTHS*").read().split('\n')
        # for driver in list_driver:
        #     self.cb_comm_driver.addItem(driver)
        
        # save_driver = smd['hardware']['uart']['driver']

        # if save_driver in list_driver:
        #     self.cb_comm_driver.setEnabled(False)
        self.btn_comm_connect.setEnabled(False)
        #     self.cb_comm_driver.setCurrentText(save_driver)
        os.system(f"pm2 start src/uart.py --name serial")
        self.lb_comm_status.setText("Connected")
        # else:
        #     self.cb_comm_driver.setEnabled(True)
        #     self.cb_comm_driver.setCurrentText("")
        #     self.btn_comm_connect.setEnabled(True)
        #     self.lb_comm_status.setText("Disconnected")

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
        
        self.btn_change_vms = QPushButton("OFF", self)
        self.btn_change_vms.adjustSize()
        self.btn_change_vms.setEnabled(False)
        self.btn_change_vms.clicked.connect(self.change_vms)

        self.t_btn_test_event = QPushButton("EVENT ON", self)
        self.t_btn_test_event.setCheckable(True)
        self.t_btn_test_event.adjustSize()
        self.t_btn_test_event.clicked[bool].connect(self.test_event)

        gl_hardware_ui = QGridLayout()
        gl_hardware_ui.addWidget(QLabel("Serial : ") , 0, 0)
        gl_hardware_ui.addWidget(self.lb_comm_status, 0, 1)
        gl_hardware_ui.addWidget(QLabel("Driver : "), 1, 0)
        gl_hardware_ui.addWidget(self.cb_comm_driver, 1, 1)
        gl_hardware_ui.addWidget(self.btn_comm_connect, 1, 2)
        gl_hardware_ui.addWidget(QLabel("VMS : "), 2, 0)
        gl_hardware_ui.addWidget(self.t_btn_test_vms, 2, 1)
        gl_hardware_ui.addWidget(self.btn_change_vms, 2, 2)
        gl_hardware_ui.addWidget(QLabel("SPK : "), 3, 0)
        gl_hardware_ui.addWidget(self.btn_test_speaker, 3, 1)
        gl_hardware_ui.addWidget(QLabel("FUNC : "), 4, 0)
        gl_hardware_ui.addWidget(self.t_btn_test_detect, 4, 1)
        gl_hardware_ui.addWidget(self.t_btn_test_event, 4, 2)

        gb_hardware_ui = QGroupBox("Hardware UI")
        gb_hardware_ui.setLayout(gl_hardware_ui)

        # BOTTOM BTNS
        self.t_btn_edit = QPushButton("EDIT", self)
        self.t_btn_edit.setCheckable(True)
        self.btn_save = QPushButton("SAVE", self)
        self.btn_exit = QPushButton("EXIT", self)
        
        self.t_btn_edit.adjustSize()
        self.btn_save.adjustSize()
        self.btn_exit.adjustSize()

        self.btn_save.setEnabled(False)
        
        self.t_btn_edit.clicked[bool].connect(self.edit_settings)
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_exit.clicked.connect(qApp.quit)

        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.addWidget(self.t_btn_edit)
        edit_btn_layout.addWidget(self.btn_save)
        edit_btn_layout.addWidget(self.btn_exit)

        layout = QVBoxLayout()
        layout.addWidget(gb_channel_info)
        layout.addWidget(gb_detector_config)
        layout.addWidget(gb_hardware_ui)
        layout.addLayout(edit_btn_layout)

        self.setLayout(layout)

    def draw_single_line(self):
        self.parent().set_draw_mode("sl")

    def update_ui(self):
        ...

    def activate_detector(self, e):

        if e:
            self.t_btn_detector_enable.setText("ACTIVE")
            smd['detectors'][self.id]['enable'] = True
        else:
            self.t_btn_detector_enable.setText("DISABLE")
            smd['detectors'][self.id]['enable'] = False
            print("???")
            print(smd['detectors'][self.id]['enable'])

    def swap_frame(self, e):
        
        if e:
            self.parent().frame_type = "annotated"
            self.t_btn_frame_swap.setText("ANNOTATED")
        else:
            self.parent().frame_type = "raw"
            self.t_btn_frame_swap.setText("RAW")

    def edit_settings(self, e):

        if e:
            self.t_btn_edit.setText("CANCEL")
            self.parent().mode = "edit"
        
        else:
            self.t_btn_edit.setText("EDIT")
            self.parent().frame_label.init_sl()
            self.parent().mode = "run"
            self.parent().set_draw_mode("normal")

        self.ui_enable(e)

    def ui_enable(self, enable):

        self.le_url.setEnabled(enable)
        self.cb_camera_type.setEnabled(enable)
        self.cb_model.setEnabled(enable)
        self.cb_event_list.setEnabled(enable)

        self.r_btn_start_line.setEnabled(False)
        self.r_btn_end_line.setEnabled(False)
        self.r_btn_roi.setEnabled(False)
        self.r_btn_single_line.setEnabled(enable)
        self.r_btn_normal.setChecked(True)

        self.btn_save.setEnabled(enable)

    def test_event(self, e):
        
        if e: 
            if smd['detectors'][self.id]['event']['type'] == 'reverse':
                shm_status.buf[4] = 0x12
        else:
            shm_status.buf[4] = 0x00

    def connect_serial(self):
        os.system(f"pm2 start src/uart.py --name serial -- {self.cb_comm_driver.currentText()}")
        smd['hardware']['uart']['driver'] = self.cb_comm_driver.currentText()

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
        
        self.btn_change_vms.setText(self.vms_status[shm_status.buf[4]])
    
    def change_vms(self):
        cur_vms = shm_status.buf[4]
        if cur_vms == 5:
            shm_status.buf[4] = 1
        else:
            shm_status.buf[4] = cur_vms + 1

        self.btn_change_vms.setText(self.vms_status[shm_status.buf[4]])

    def save_settings(self):

        if self.parent().is_setting_valid():
            print("settings saved")
            self.parent().mode = "run"
            self.parent().set_draw_mode("normal")
            self.ui_enable(False)

            detectors = smd['detectors']
            detectors[self.id]['event']['single'] = self.parent().frame_label.get_norm_sl()
            smd['detectors'] = detectors

            with open('config/config.yaml', 'w') as f:
                yaml.dump(dict(smd), f, default_flow_style=False)
            
            self.t_btn_edit.setChecked(False)
            self.t_btn_edit.setText("EDIT")

        else:
            print("invalid setting... check settings")
        

      
    def change_type(self, e):
        print(f"change type -> {e}")

class ChannelWidget(QWidget):

    def __init__(self, ch_id):

        super().__init__()
        self.ch_id = ch_id
        self.mode = "run"
        if smd['detectors'][ch_id]['enable']:
            self.frame_type = "annotated"
        else:
            self.frame_type = "raw"
        self.init_ui()

    def init_ui(self):
        
        self.frame_label = FrameLabel(self.ch_id)
        
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.frame_label)
        self.main_layout.addWidget(ControlWidget(self.ch_id))

        self.setLayout(self.main_layout)

    def is_setting_valid(self):

        return self.frame_label.check_draw_mode()

    def set_draw_mode(self, draw_mode):

        self.frame_label.mode = draw_mode