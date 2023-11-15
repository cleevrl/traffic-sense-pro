import sys
import time
from serial import Serial

from multiprocessing import shared_memory

shm_status = shared_memory.SharedMemory(name="status")

# driver = sys.argv[1]
ser = Serial("/dev/ttyTHS0", baudrate=115200)

frame_num = 0

def cal_lrc(msg):
    lrc = 0
    for v in msg:
        lrc ^= v
    
    return lrc

while True:

    header = [0x7E, 0x7E]
    msg_info = [10, 1, 0x00, frame_num]
    status_code = list(shm_status.buf[:5])
    data_array = msg_info + status_code
    lrc_code = cal_lrc(data_array)
    send_array = header + data_array + [lrc_code, 0x7F]
    ser.write(send_array)

    print(f"send msg -> {send_array}")

    time.sleep(0.2)

    frame_num += 1
    if frame_num == 0x40:
        frame_num = 0x00









