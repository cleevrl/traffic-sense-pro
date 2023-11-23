import sys
import numpy as np
from ultralytics import YOLO

from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict
import time

from shapely import box, LineString

while True:
    
    try:
          smd = SharedMemoryDict(name="smd", size=2048)
          break

    except FileNotFoundError:
        print("Not found smd, try 1 sec later ...")
        time.sleep(1)


from ultralytics import YOLO

ch_id = int(sys.argv[1])

model_name = smd['detectors'][ch_id]['model']
model = YOLO(f"./data/pt/{model_name}")

width = smd['cameras'][ch_id]['width']
height = smd['cameras'][ch_id]['height']

is_jointed = False
jointed_y_at = 0
disjointed_y_at = 0

sample_array = np.zeros((height, width, 3), dtype=np.uint8)
shm_raw_frame = shared_memory.SharedMemory(name=f"raw_frame_{ch_id}")
shm_annotated_frame = shared_memory.SharedMemory(name=f"annotated_frame_{ch_id}", create=True, size=sample_array.nbytes)

raw_frame = np.ndarray((height, width, 3), dtype=np.uint8, buffer=shm_raw_frame.buf)
annotated_frame = np.ndarray((height, width, 3), dtype=np.uint8, buffer=shm_annotated_frame.buf)

print("Start Detector Process...")

try:

    while True:
        
        # if not smd['detectors'][ch_id]['enable']:
        #     annotated_frame[:] = sample_array
        # else:        
        results = model(raw_frame)
        # results = model.track(raw_frame)
        for res in results[0]:
            xyxy = res.boxes.xyxyn.numpy()[0]
            xywh = res.boxes.xywhn.numpy()[0]
            # print(xyxy)
            print(xywh)
            box_obj = box(xyxy[0], xyxy[1], xyxy[2], xyxy[3])
            sl_pts = smd['detectors'][ch_id]['event']['single']
            # print(sl_pts)
            sl_obj = LineString(sl_pts)
            # print(sl_obj.bounds)
            jointed = box_obj.disjoint(sl_obj)
            print(jointed)

            if jointed:
                if is_jointed:
                    ...
                else:
                    print("-> joint status")
            else:
                if is_jointed:
                    print("-> joint release")
                    is_jointed = False
                else:
                    ...

        annotated_frame[:] = results[0].plot()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")

print("Quit detector process...")

shm_raw_frame.unlink()
shm_annotated_frame.unlink()

shm_raw_frame.close()
shm_annotated_frame.close()