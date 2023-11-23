import sys
import numpy as np
from ultralytics import YOLO

from multiprocessing import shared_memory
from shared_memory_dict import SharedMemoryDict
import time

from shapely import box, LineString
from play_sound import play_sound

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

is_event = False
event_counter = 0

sample_array = np.zeros((height, width, 3), dtype=np.uint8)
shm_raw_frame = shared_memory.SharedMemory(name=f"raw_frame_{ch_id}")
shm_annotated_frame = shared_memory.SharedMemory(name=f"annotated_frame_{ch_id}", create=True, size=sample_array.nbytes)
shm_status = shared_memory.SharedMemory(name="status")


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
            # print(xyxy)
            box_obj = box(xyxy[0], xyxy[1], xyxy[2], xyxy[3])
            sl_pts = smd['detectors'][ch_id]['event']['single']
            # print(sl_pts)
            sl_obj = LineString(sl_pts)
            # print(sl_obj.bounds)
            jointed = not box_obj.disjoint(sl_obj)
            print(jointed)

            if jointed and not is_event:
                print("hey")
                box_center_y = (xyxy[1] + xyxy[3]) / 2
                sl_center_y = (sl_pts[0][1] + sl_pts[1][1]) / 2
                if box_center_y < sl_center_y:
                    print("!!!!!!! REVERSE")
                    is_event = True
                    shm_status.buf[4] = 0x12
                    play_sound()

                else:
                    print("Right way^^")

        annotated_frame[:] = results[0].plot()

        time.sleep(0.1)

        if is_event:
            event_counter += 1
            if event_counter == 50:
                event_counter = 0
                is_event = False
                shm_status.buf[4] = 0x00
                print("event release")

except KeyboardInterrupt:
    print("KeyboardInterrupt!!!")

print("Quit detector process...")

shm_raw_frame.unlink()
shm_annotated_frame.unlink()

shm_raw_frame.close()
shm_annotated_frame.close()