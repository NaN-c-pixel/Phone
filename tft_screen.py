# HungsOS optional ILI9341 SPI TFT support (MicroPython / ESP32-S3)
# Configure GPIO numbers in screen_config.py. This module does not guess pins.
import time
from machine import Pin, SPI

try:
    import screen_config as cfg
except ImportError:
    cfg = None

class ILI9341:
    def __init__(self, spi, cs, dc, rst, width=240, height=320, rotation=0):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=1)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.width = width
        self.height = height
        self.rotation = rotation
        self._reset()
        self._init_display()

    def _cmd(self, value):
        self.cs(0); self.dc(0); self.spi.write(bytes((value,))); self.cs(1)

    def _data(self, data):
        self.cs(0); self.dc(1); self.spi.write(data); self.cs(1)

    def _reset(self):
        self.rst(1); time.sleep_ms(20); self.rst(0); time.sleep_ms(50); self.rst(1); time.sleep_ms(120)

    def _init_display(self):
        self._cmd(0x01); time.sleep_ms(120)
        self._cmd(0x28)
        self._cmd(0x3A); self._data(b'\\x55')
        self._cmd(0x36); self._data(bytes((0x48 if self.rotation == 0 else 0x28,)))
        self._cmd(0x11); time.sleep_ms(120)
        self._cmd(0x13); self._cmd(0x29); time.sleep_ms(20)
        self.fill(0x0000)

    def _window(self, x0, y0, x1, y1):
        self._cmd(0x2A); self._data(bytes((x0 >> 8, x0 & 255, x1 >> 8, x1 & 255)))
        self._cmd(0x2B); self._data(bytes((y0 >> 8, y0 & 255, y1 >> 8, y1 & 255)))
        self._cmd(0x2C)

    def fill(self, color):
        self._window(0, 0, self.width - 1, self.height - 1)
        hi, lo = (color >> 8) & 255, color & 255
        block = bytes((hi, lo)) * 256
        remaining = self.width * self.height
        self.cs(0); self.dc(1)
        while remaining:
            count = min(remaining, 256)
            self.spi.write(block if count == 256 else bytes((hi, lo)) * count)
            remaining -= count
        self.cs(1)

    def rect(self, x, y, w, h, color):
        x0=max(0,int(x)); y0=max(0,int(y)); x1=min(self.width,int(x+w)); y1=min(self.height,int(y+h))
        if x0 >= x1 or y0 >= y1: return
        self._window(x0,y0,x1-1,y1-1)
        hi,lo=(color>>8)&255,color&255
        block=bytes((hi,lo))*min(256,x1-x0)
        self.cs(0); self.dc(1)
        for _ in range(y1-y0):
            left=x1-x0
            while left:
                n=min(left,256); self.spi.write(block if n==256 else bytes((hi,lo))*n); left-=n
        self.cs(1)

    def text(self, text, x, y, color=0xFFFF, scale=1):
        # Compact built-in 5x7 ASCII font; unsupported characters become '?'.
        for ch in str(text):
            glyph = _FONT.get(ch, _FONT['?'])
            for col, bits in enumerate(glyph):
                for row in range(7):
                    if bits & (1 << row):
                        if scale == 1: self.rect(x+col,y+row,1,1,color)
                        else: self.rect(x+col*scale,y+row*scale,scale,scale,color)
            x += 6 * scale
            if x > self.width - 6*scale: break

    def show_home(self, subtitle="Pocket Edition"):
        self.fill(0xF79E)
        self.rect(0,0,self.width,48,0x087F)
        self.text("HungsOS",12,16,0xFFFF,2)
        self.rect(12,70,self.width-24,56,0xFFFF)
        self.text("Welcome!",22,84,0x087F,2)
        self.text(subtitle[:28],12,148,0x0000,1)
        self.rect(12,180,self.width-24,42,0xFFFF)
        self.text("Wi-Fi / Web UI",22,195,0x087F,1)
        self.text("TFT ready",12,244,0x07E0,2)

    def show_status(self, title, subtitle=""):
        self.fill(0xF79E)
        self.rect(0,0,self.width,48,0x087F)
        self.text(str(title)[:18],12,16,0xFFFF,2)
        self.rect(12,76,self.width-24,68,0xFFFF)
        self.text(str(subtitle)[:30],20,94,0x0000,1)
        self.text("HungsOS Pocket",12,170,0x087F,1)
        self.text("ILI9341 display",12,190,0x087F,1)

# Tiny 5x7 glyph columns. Text is ASCII-only; Vietnamese text is simplified to '?'.
_FONT = {
' ': (0,0,0,0,0), '?': (2,1,81,9,6), '!': (0,0,95,0,0), '.': (0,96,96,0,0), ':': (0,54,54,0,0), '-': (8,8,8,8,8), '/': (32,16,8,4,2),
'A': (126,17,17,17,126), 'B': (127,73,73,73,54), 'C': (62,65,65,65,34), 'D': (127,65,65,34,28), 'E': (127,73,73,73,65), 'F': (127,9,9,9,1), 'G': (62,65,73,73,122), 'H': (127,8,8,8,127), 'I': (0,65,127,65,0), 'J': (32,64,65,63,1), 'K': (127,8,20,34,65), 'L': (127,64,64,64,64), 'M': (127,2,12,2,127), 'N': (127,4,8,16,127), 'O': (62,65,65,65,62), 'P': (127,9,9,9,6), 'Q': (62,65,81,33,94), 'R': (127,9,25,41,70), 'S': (38,73,73,73,50), 'T': (1,1,127,1,1), 'U': (63,64,64,64,63), 'V': (31,32,64,32,31), 'W': (63,64,56,64,63), 'X': (99,20,8,20,99), 'Y': (7,8,112,8,7), 'Z': (97,81,73,69,67),
'a': (32,84,84,84,120), 'b': (127,72,68,68,56), 'c': (56,68,68,68,32), 'd': (56,68,68,72,127), 'e': (56,84,84,84,24), 'f': (8,126,9,1,2), 'g': (12,82,82,82,62), 'h': (127,8,4,4,120), 'i': (0,68,125,64,0), 'j': (32,64,68,61,0), 'k': (127,16,40,68,0), 'l': (0,65,127,64,0), 'm': (124,4,24,4,120), 'n': (124,8,4,4,120), 'o': (56,68,68,68,56), 'p': (124,20,20,20,8), 'q': (8,20,20,24,124), 'r': (124,8,4,4,8), 's': (72,84,84,84,32), 't': (4,63,68,64,32), 'u': (60,64,64,32,124), 'v': (28,32,64,32,28), 'w': (60,64,48,64,60), 'x': (68,40,16,40,68), 'y': (12,80,80,80,60), 'z': (68,100,84,76,68), '0': (62,81,73,69,62), '1': (0,66,127,64,0), '2': (66,97,81,73,70), '3': (33,65,69,75,49), '4': (24,20,18,127,16), '5': (39,69,69,69,57), '6': (60,74,73,73,48), '7': (1,113,9,5,3), '8': (54,73,73,73,54), '9': (6,73,73,41,30),
}

def init():
    if cfg is None:
        print("TFT disabled: create screen_config.py from screen_config_example.py and set pins.")
        return None
    required = ("SCK", "MOSI", "CS", "DC", "RST")
    if any(not isinstance(getattr(cfg, key, None), int) for key in required):
        print("TFT disabled: screen_config.py has unset/invalid GPIO pins.")
        return None
    try:
        spi_id = getattr(cfg, "SPI_ID", 2)
        baudrate = getattr(cfg, "BAUDRATE", 40000000)
        spi = SPI(spi_id, baudrate=baudrate, polarity=0, phase=0,
                  sck=Pin(cfg.SCK), mosi=Pin(cfg.MOSI), miso=Pin(getattr(cfg, "MISO", cfg.SCK)))
        display = ILI9341(spi, cfg.CS, cfg.DC, cfg.RST,
                          getattr(cfg, "WIDTH", 240), getattr(cfg, "HEIGHT", 320),
                          getattr(cfg, "ROTATION", 0))
        display.show_home()
        print("ILI9341 TFT initialized.")
        return display
    except Exception as e:
        print("TFT initialization failed:", repr(e))
        return None

_display = None
def show_status(title, subtitle=""):
    global _display
    if _display is None:
        _display = init()
    if _display is not None:
        _display.show_status(title, subtitle)
