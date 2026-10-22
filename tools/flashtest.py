"""Check which parts of the ESP32 flash are reliable.

Usage (board connected, Thonny/VS Code closed):
    python tools/flashtest.py COM6

It writes 64 KB of random data at 2 MB, 3 MB ... 15 MB and at the very end,
reads it back and compares. Afterwards the filesystem area is garbage, so run
`python -m esptool --port COMx erase_flash` and flash MicroPython again.
"""
import os
import subprocess
import sys

port = sys.argv[1]
SIZE = 65536
data = os.urandom(SIZE)
with open("ft_write.bin", "wb") as f:
    f.write(data)


def esp(*args):
    return subprocess.run([sys.executable, "-m", "esptool", "--port", port, *args],
                          capture_output=True, text=True)


offsets = [mb * 0x100000 for mb in range(2, 16)] + [0xFF0000]
bad = []
for off in offsets:
    w = esp("--after", "no_reset", "write_flash", hex(off), "ft_write.bin")
    r = esp("--after", "no_reset", "read_flash", hex(off), str(SIZE), "ft_read.bin")
    ok = False
    if w.returncode == 0 and r.returncode == 0 and os.path.exists("ft_read.bin"):
        with open("ft_read.bin", "rb") as f:
            ok = f.read() == data
    print("%-10s %s" % (hex(off), "OK" if ok else "BAD  <-- unreliable"))
    if not ok:
        bad.append(hex(off))
    if os.path.exists("ft_read.bin"):
        os.remove("ft_read.bin")

os.remove("ft_write.bin")
print()
print("All areas OK" if not bad else "Bad areas: " + ", ".join(bad))
