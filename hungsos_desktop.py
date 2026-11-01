# HungsOS Desktop Edition
# ESP32-S3 + MicroPython + ILI9341/XPT2046
# Kept separate from app.py so the existing Pocket web OS is preserved.

from machine import Pin, SPI
import framebuf, time, network, socket, os, gc

WIDTH, HEIGHT = 240, 320
SSID = "Dong Bac."
PASSWORD = "PUT_WIFI_PASSWORD_HERE"  # keep your real password out of GitHub
STATIC_IP = "192.168.1.7"
GATEWAY = "192.168.1.1"
SUBNET = "255.255.255.0"
DNS = "8.8.8.8"

# Existing HungsOS display wiring
spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(12), mosi=Pin(11), miso=Pin(13))
tft_cs = Pin(10, Pin.OUT, value=1)
dc = Pin(9, Pin.OUT)
rst = Pin(14, Pin.OUT)
touch_cs = Pin(4, Pin.OUT, value=1)
touch_irq = Pin(7, Pin.IN, Pin.PULL_UP)

BLACK, WHITE = 0x0000, 0xFFFF
BLUE, DARK, PANEL = 0x239F, 0x10A3, 0x2128
CYAN, GREEN, YELLOW = 0x07FF, 0x07E0, 0xFFE0
GRAY, RED = 0x8410, 0xF800

buf = bytearray(WIDTH * HEIGHT * 2)
fb = framebuf.FrameBuffer(buf, WIDTH, HEIGHT, framebuf.RGB565)


def cmd(c, data=None):
    tft_cs.value(0); dc.value(0); spi.write(bytes([c]))
    if data is not None:
        dc.value(1); spi.write(data)
    tft_cs.value(1)


def init_display():
    rst.value(1); time.sleep_ms(50); rst.value(0); time.sleep_ms(50)
    rst.value(1); time.sleep_ms(150)
    cmd(0x01); time.sleep_ms(150); cmd(0x28)
    cmd(0xCF, b'\x00\xC1\x30'); cmd(0xED, b'\x64\x03\x12\x81')
    cmd(0xE8, b'\x85\x00\x78'); cmd(0xCB, b'\x39\x2C\x00\x34\x02')
    cmd(0xF7, b'\x20'); cmd(0xEA, b'\x00\x00'); cmd(0xC0, b'\x23')
    cmd(0xC1, b'\x10'); cmd(0xC5, b'\x3E\x28'); cmd(0xC7, b'\x86')
    cmd(0x36, b'\x48'); cmd(0x3A, b'\x55'); cmd(0xB1, b'\x00\x18')
    cmd(0xB6, b'\x08\x82\x27'); cmd(0xF2, b'\x00'); cmd(0x26, b'\x01')
    cmd(0xE0, bytes([15,49,43,12,14,8,78,241,55,7,16,3,14,9,0]))
    cmd(0xE1, bytes([0,14,20,3,17,7,49,193,72,8,15,12,49,54,15]))
    cmd(0x11); time.sleep_ms(120); cmd(0x29); time.sleep_ms(20)


def show():
    cmd(0x2A, b'\x00\x00\x00\xEF'); cmd(0x2B, b'\x00\x00\x01\x3F'); cmd(0x2C)
    tft_cs.value(0); dc.value(1)
    chunk = bytearray(1024)
    for start in range(0, len(buf), 1024):
        end = min(start + 1024, len(buf)); n = end - start
        for i in range(0, n, 2):
            chunk[i] = buf[start+i+1]; chunk[i+1] = buf[start+i]
        spi.write(memoryview(chunk)[:n])
    tft_cs.value(1)


def centered(text, y, color=WHITE):
    fb.text(text, max(0, (WIDTH-len(text)*8)//2), y, color)


def splash():
    fb.fill(BLACK); centered("HungsOS", 105, CYAN); centered("POCKET COMPUTER", 135)
    centered("Starting system...", 180, GRAY); show()
    for n in range(0, 161, 5):
        fb.fill_rect(40, 220, 160, 6, PANEL); fb.fill_rect(40, 220, n, 6, CYAN)
        show(); time.sleep_ms(60)


def welcome():
    # Smooth-looking slide/reveal without requiring extra libraries.
    for y in range(HEIGHT, 40, -16):
        fb.fill(BLACK); fb.fill_rect(0, y, WIDTH, HEIGHT-y, BLUE)
        fb.text("HungsOS", 10, max(8, y+10), WHITE); show(); time.sleep_ms(18)
    fb.fill(BLUE); centered("Welcome", 85, WHITE); centered("HungsOS", 120, CYAN)
    centered("Pocket Computer", 150, WHITE); centered("Press LOGIN", 205, GRAY); show()
    time.sleep_ms(1200)


def login():
    fb.fill(BLUE); centered("HungsOS", 55, CYAN); centered("Welcome back", 95, WHITE)
    fb.rect(55, 125, 130, 48, WHITE); centered("HUNG", 145, WHITE)
    centered("LOGIN", 210, YELLOW); centered("Press joystick / tap", 245, GRAY); show()
    # Until joystick wiring is added, the login screen advances automatically.
    time.sleep_ms(1200)


def icon(x, y, label, symbol, color):
    fb.fill_rect(x, y, 48, 48, PANEL); fb.rect(x, y, 48, 48, color)
    fb.text(symbol, x+5, y+17, color); fb.text(label, x-2, y+54, WHITE)


def desktop():
    fb.fill(BLUE); fb.fill_rect(0, 0, WIDTH, 26, DARK)
    fb.text("HungsOS", 8, 8, WHITE); fb.text("DESKTOP", 167, 8, CYAN)
    icon(22, 55, "Bin", "BIN", RED); icon(137, 55, "Notepad", "TXT", YELLOW)
    icon(22, 150, "Files", "DIR", CYAN); icon(137, 150, "Games", "PLY", GREEN)
    icon(22, 245, "Settings", "CFG", WHITE)
    fb.fill_rect(0, 296, WIDTH, 24, DARK); fb.text("START", 8, 304, WHITE)
    fb.text("HungsOS", 97, 304, WHITE); fb.text("WiFi", 195, 304, GREEN); show()


def settings():
    fb.fill(BLACK); fb.fill_rect(0,0,WIDTH,28,DARK); fb.text("< Settings",8,9,WHITE)
    items = ["Wi-Fi", "Bluetooth", "Display", "Controls", "Remote", "Storage", "About"]
    y = 45
    for item in items:
        fb.fill_rect(8,y-4,224,28,PANEL); fb.text(item,18,y+4,WHITE); fb.text(">",216,y+4,GRAY); y += 35
    show()


def files():
    fb.fill(BLACK); fb.text("< File Manager",8,10,WHITE); y=45
    try: names=os.listdir("/")
    except: names=[]
    for name in names[:14]:
        fb.text(str(name)[:27],10,y,WHITE); y += 17
    show()


def notepad():
    fb.fill(BLACK); fb.text("< Notepad",8,10,WHITE); fb.text("Use the remote keyboard",10,55,CYAN)
    fb.text("Notes are coming next",10,85,WHITE); show()


def games():
    fb.fill(BLACK); centered("Games",40,CYAN); centered("Built-in games",90,WHITE)
    centered("More coming soon",150,GRAY); show()


def wifi_connect():
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    try: wlan.ifconfig((STATIC_IP, SUBNET, GATEWAY, DNS))
    except Exception as e: print("Static IP:", e)
    if PASSWORD == "PUT_WIFI_PASSWORD_HERE":
        print("Set PASSWORD locally before using Wi-Fi."); return wlan
    try:
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                print("HungsOS Wi-Fi:", wlan.ifconfig()); return wlan
            time.sleep_ms(500)
    except Exception as e: print("Wi-Fi:", e)
    return wlan


PAGE = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>HungsOS Remote</title><style>
body{font-family:Arial;background:#101827;color:white;text-align:center;padding:15px}button{font-size:18px;padding:13px;margin:4px;border:0;border-radius:10px;background:#287fc0;color:white}.box{background:#202d40;border-radius:16px;padding:15px;margin:12px auto;max-width:430px}.keys{display:grid;grid-template-columns:repeat(7,1fr)}.keys button{padding:11px 3px;font-size:15px}.pad{display:grid;grid-template-columns:repeat(3,1fr);max-width:260px;margin:auto}input{padding:12px;width:80%;font-size:16px}
</style></head><body><h2>HungsOS Remote</h2>
<div class="box"><h3>Mouse</h3><div class="pad"><button onclick="c('up')">▲</button><button onclick="c('click')">●</button><button onclick="c('right')">▶</button><button onclick="c('left')">◀</button><button onclick="c('down')">▼</button><button onclick="c('home')">⌂</button></div></div>
<div class="box"><h3>Keyboard</h3><input id="t" placeholder="Type text"><button onclick="txt()">Send</button><div class="keys">''' + ''.join('<button onclick="k(\''+x+'\')">'+x+'</button>' for x in 'QWERTYUIOPASDFGHJKLZXCVBNM') + '''</div><button onclick="k('SPACE')">SPACE</button><button onclick="k('BACKSPACE')">⌫</button><button onclick="k('ENTER')">ENTER</button></div>
<div class="box"><button onclick="c('notepad')">Notepad</button><button onclick="c('files')">Files</button><button onclick="c('games')">Games</button><button onclick="c('settings')">Settings</button></div>
<script>function c(x){fetch('/cmd?c='+x)}function k(x){fetch('/cmd?c=key&v='+x)}function txt(){fetch('/cmd?c=text&v='+encodeURIComponent(document.getElementById('t').value));document.getElementById('t').value=''}</script></body></html>'''


def query(path):
    d={}
    if '?' not in path:return d
    for p in path.split('?',1)[1].split('&'):
        if '=' in p:
            k,v=p.split('=',1); d[k]=v.replace('+',' ')
    return d


def server_loop(wlan):
    if not wlan.isconnected(): return
    s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(('0.0.0.0',80)); s.listen(1); s.settimeout(.1)
    print('HungsOS Remote: http://'+STATIC_IP)
    while True:
        try: c,_=s.accept()
        except OSError: continue
        try:
            c.settimeout(2); req=c.recv(2048); line=req.split(b'\r\n',1)[0].decode(); path=line.split(' ')[1]
            if path.startswith('/cmd'):
                q=query(path); action=q.get('c','')
                if action=='home': desktop()
                elif action=='settings': settings()
                elif action=='files': files()
                elif action=='notepad': notepad()
                elif action=='games': games()
                c.send(b'HTTP/1.1 200 OK\r\nContent-Type:text/plain\r\nConnection:close\r\n\r\nOK')
            else:
                data=PAGE.encode(); c.send(b'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n'); c.send(data)
        except Exception as e: print('HTTP:',e)
        try:c.close()
        except:pass


init_display(); splash(); time.sleep(3); welcome(); login(); desktop()
wlan=wifi_connect(); gc.collect()
server_loop(wlan)
