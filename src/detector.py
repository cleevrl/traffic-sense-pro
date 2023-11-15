import sys
import pickle
import numpy as np
from ultralytics import YOLO

from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict
import time

smd = SharedMemoryDict(name="smd", size=2048)

# while True:

#     try:
#         shm_config = shared_memory.SharedMemory(name='config')
#         bytes_config = bytes(shm_config.buf)
#         config = pickle.loads(bytes_config)
#         break

#     except FileNotFoundError:
#         print("Not found shm, try 1 sec later...")
#         time.sleep(1)

from ultralytics import YOLO

ch_id = int(sys.argv[1])

model_name = "yolov8s_coco_pretrained.pt"
model = YOLO(f"./data/pt/{model_name}")

width = smd['cameras'][ch_id]['width']
height = smd['cameras'][ch_id]['height']

sample_array = np.zeros((height, width, 3), dtype=np.uint8)
shm_raw_frame = shared_memory.SharedMemory(name=f"raw_frame_{ch_id}")
shm_annotated_frame = shared_memory.SharedMemory(name=f"annotated_frame_{ch_id}", create=True, size=sample_array.nbytes)

raw_frame = np.ndarray((height, width, 3), dtype=np.uint8, buffer=shm_raw_frame.buf)
annotated_frame = np.ndarray((height, width, 3), dtype=np.uint8, buffer=shm_annotated_frame.buf)

print("Start Detector Process...")

try:

    while True:
        results = model(raw_frame)
        # print(results)
        annotated_frame[:] = results[0].plot()

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")

print("Quit detector process...")

shm_raw_frame.unlink()
shm_annotated_frame.unlink()

shm_raw_frame.close()
shm_annotated_frame.close()