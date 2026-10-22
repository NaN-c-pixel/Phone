# Tiny launcher. It gives Thonny a few seconds to interrupt the board
# so you can always edit and save files, then starts the real program (app.py).
#
# Edit mode:  press Stop (Ctrl+C) in Thonny during the countdown,
#             or hold the BOOT button while pressing RST.
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
