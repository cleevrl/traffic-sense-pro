import sys
import cv2
import time
import numpy as np

from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict

cam_url = sys.argv[1]
ch_id = int(sys.argv[2])
print(ch_id)
cap = cv2.VideoCapture(cam_url)

smd = SharedMemoryDict(name="smd", size=2048)

if not cap.isOpened:  
    print("Cannot connect Camera")
    exit
else:

    print("Camera Connected!")
    ret, frame = cap.read()
    
    smd['cameras'][ch_id]['width'] = frame.shape[1]
    smd['cameras'][ch_id]['height'] = frame.shape[0]

    sample_array = np.zeros(frame.shape, dtype=np.uint8)
    shm_raw_frame = shared_memory.SharedMemory(name=f"raw_frame_{ch_id}", create=True, size=sample_array.nbytes) 
    np_raw_frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=shm_raw_frame.buf) 

try:

    pre_time = time.time()

    while True: 

        ret, frame = cap.read()

        if not ret:
            continue

        cur_time = time.time()
        gap = cur_time - pre_time
        fps = 1 / gap
        pre_time = cur_time

        np_raw_frame[:] = frame
        # print(f"frame updated... (fps : {fps})")

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")

print("Quit image process...")

cap.release()

shm_raw_frame.unlink()
shm_raw_frame.close()