import sys
import cv2
import time
import yaml
import pickle
import numpy as np

from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict

cam_url = sys.argv[1]
ch_id = int(sys.argv[2])
print(ch_id)
cap = cv2.VideoCapture(cam_url)
print("Camera Connected...")

# smd_config = SharedMemoryDict(name="config", size=2048)
smd = SharedMemoryDict(name="smd", size=2048)

# shm_config = shared_memory.SharedMemory(name='config')

if not cap.isOpened:  
    print("Cannot connect Camera")
    exit
else:
    ret, frame = cap.read()
    
    # bytes_config = bytes(shm_config.buf[:])
    # config = pickle.loads(bytes_config)
    smd['cameras'][ch_id]['width'] = frame.shape[1]
    smd['cameras'][ch_id]['height'] = frame.shape[0]

    # serialized = pickle.dumps(config)
    # shm_config.buf[:len(serialized)] = serialized

    sample_array = np.zeros(frame.shape, dtype=np.uint8)
    shm_raw_frame = shared_memory.SharedMemory(name=f"raw_frame_{ch_id}", create=True, size=sample_array.nbytes) 
    np_raw_frame = np.ndarray(frame.shape, dtype=np.uint8, buffer=shm_raw_frame.buf) 

try:

    pre_time = time.time()

    while True: 

        ret, frame = cap.read()

        cur_time = time.time()
        gap = cur_time - pre_time
        fps = 1 / gap
        pre_time = cur_time

        if not ret:
            print("Read frame failed...")
            break

        np_raw_frame[:] = frame
        # print(f"frame updated... (fps : {fps})")

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")

print("Quit image process...")

cap.release()

shm_raw_frame.unlink()
shm_raw_frame.close()