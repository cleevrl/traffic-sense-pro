import cv2
import numpy as np
import time

from multiprocessing import shared_memory


print("Waiting for building shared memory...")
time.sleep(3)

shm_raw_frame = shared_memory.SharedMemory(name="raw_frame")
shm_annotated_frame = shared_memory.SharedMemory(name="annotated_frame")

raw_frame = np.ndarray((240, 320, 3), dtype=np.uint8, buffer=shm_raw_frame.buf)
annotated_frame = np.ndarray((240, 320, 3), dtype=np.uint8, buffer=shm_annotated_frame.buf)

print("Start Raw Frame Player...")

try:
   
    while True:

        cv2.imshow("raw_frame", raw_frame)
        cv2.imshow("annotated_frame", annotated_frame)
        cv2.waitKey(10)

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")


print("Quit Raw Frame Player...")

cv2.destroyAllWindows()
shm_raw_frame.unlink()
shm_raw_frame.close()
