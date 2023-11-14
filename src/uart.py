from serial import Serial

from multiprocessing import shared_memory

ser = Serial("/dev/ttyTHS1", baudrate=115200)
