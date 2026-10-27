# Tiny launcher for HungsOS. All app code lives in app.py.
# Press Stop / Ctrl+C during the countdown to interrupt startup for editing.
import time
from machine import Pin

try:
    if Pin(0, Pin.IN, Pin.PULL_UP).value() == 0:
        print("BOOT held: edit mode, not starting HungsOS.")
    else:
        print("Starting HungsOS in 5 s... press Stop / Ctrl+C now for edit mode.")
        time.sleep(5)
        import app
except KeyboardInterrupt:
    print("Edit mode: HungsOS not started.")
