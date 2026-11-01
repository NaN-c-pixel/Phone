# HungsOS PC Edition - landscape One UI-inspired desktop
# ESP32-S3 N16R8 / MicroPython / ILI9341 + XPT2046
# Display wiring retained from the user's working test:
# TFT SCK=12 MOSI=11 MISO=13 CS=10 DC=9 RST=14
# Touch CS=4 IRQ=7

from machine import Pin, SPI
import framebuf, time, network, socket, os, gc
from video_cast import CAST_PAGE, apply_packet

WIDTH, HEIGHT = 320, 240
STATIC_IP = "192.168.1.7"
GATEWAY = "192.168.1.1"
SUBNET = "255.255.255.0"
DNS = "8.8.8.8"

# Load local credentials from wifi-pass.py. Keep the real file off GitHub.
cfg = {}
try:
    with open("wifi-pass.py", "r") as f:
        exec(f.read(), cfg)
except Exception as e:
    print("Wi-Fi config not loaded:", e)
SSID = cfg.get("SSID", "YOUR_WIFI_NAME")
PASSWORD = cfg.get("PASSWORD", "PUT_YOUR_WIFI_PASSWORD_HERE")
STATIC_IP = cfg.get("STATIC_IP", STATIC_IP)
GATEWAY = cfg.get("GATEWAY", GATEWAY)
SUBNET = cfg.get("SUBNET", SUBNET)
DNS = cfg.get("DNS", DNS)

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
GRAY, RED, PURPLE = 0x8410, 0xF800, 0x801F
BG = 0x1082
buf = bytearray(WIDTH * HEIGHT * 2)
fb = framebuf.FrameBuffer(buf, WIDTH, HEIGHT, framebuf.RGB565)
current_app = "desktop"
note_text = ""
remote_text = ""

def cmd(c, data=None):
    tft_cs.value(0)
    dc.value(0)
    spi.write(bytes([c]))
    if data is not None:
        dc.value(1)
        spi.write(data)
    tft_cs.value(1)

def init_display():
    rst.value(1); time.sleep_ms(50); rst.value(0); time.sleep_ms(50)
    rst.value(1); time.sleep_ms(150)
    cmd(0x01); time.sleep_ms(150); cmd(0x28)
    cmd(0xCF, b'\x00\xC1\x30'); cmd(0xED, b'\x64\x03\x12\x81')
    cmd(0xE8, b'\x85\x00\x78'); cmd(0xCB, b'\x39\x2C\x00\x34\x02')
    cmd(0xF7, b'\x20'); cmd(0xEA, b'\x00\x00'); cmd(0xC0, b'\x23')
    cmd(0xC1, b'\x10'); cmd(0xC5, b'\x3E\x28'); cmd(0xC7, b'\x86')
    # MADCTL MV bit rotates the 240x320 panel into 320x240 landscape.
    cmd(0x36, b'\x28'); cmd(0x3A, b'\x55'); cmd(0xB1, b'\x00\x18')
    cmd(0xB6, b'\x08\x82\x27'); cmd(0xF2, b'\x00'); cmd(0x26, b'\x01')
    cmd(0xE0, bytes([15,49,43,12,14,8,78,241,55,7,16,3,14,9,0]))
    cmd(0xE1, bytes([0,14,20,3,17,7,49,193,72,8,15,12,49,54,15]))
    cmd(0x11); time.sleep_ms(120); cmd(0x29); time.sleep_ms(20)

def show():
    cmd(0x2A, b'\x00\x00\x01\x3F')
    cmd(0x2B, b'\x00\x00\x00\xEF')
    cmd(0x2C)
    tft_cs.value(0); dc.value(1)
    chunk = bytearray(1024)
    for start in range(0, len(buf), 1024):
        end = min(start + 1024, len(buf)); n = end - start
        for i in range(0, n, 2):
            chunk[i] = buf[start+i+1]
            chunk[i+1] = buf[start+i]
        spi.write(memoryview(chunk)[:n])
    tft_cs.value(1)

def show_tile(x, y, w, h, tile):
    # Fast partial ILI9341 update for HVID playback.
    if x < 0 or y < 0 or x + w > WIDTH or y + h > HEIGHT:
        return
    cmd(0x2A, bytes((x >> 8, x & 255, (x+w-1) >> 8, (x+w-1) & 255)))
    cmd(0x2B, bytes((y >> 8, y & 255, (y+h-1) >> 8, (y+h-1) & 255)))
    cmd(0x2C)
    swapped = bytearray(len(tile))
    for i in range(0, len(tile), 2):
        swapped[i] = tile[i+1]
        swapped[i+1] = tile[i]
    tft_cs.value(0)
    dc.value(1)
    spi.write(swapped)
    tft_cs.value(1)


def centered(text, y, color=WHITE):
    fb.text(text, max(0, (WIDTH-len(text)*8)//2), y, color)

def topbar(title):
    fb.fill(BG)
    fb.fill_rect(0, 0, WIDTH, 27, DARK)
    fb.text(title[:18], 10, 9, WHITE)
    fb.text("WiFi", 248, 9, CYAN)
    fb.text("100%", 284, 9, GREEN)

def splash():
    fb.fill(BLACK); centered("HungsOS PC", 76, CYAN)
    centered("Starting your workspace", 108, WHITE)
    fb.fill_rect(48, 157, 224, 8, PANEL)
    show()
    for n in range(0, 225, 7):
        fb.fill_rect(48, 157, 224, 8, PANEL)
        fb.fill_rect(48, 157, n, 8, CYAN)
        show(); time.sleep_ms(35)

def welcome():
    for x in range(-160, 25, 12):
        fb.fill(BLACK)
        fb.fill_rect(x, 0, 320-x, 240, BLUE)
        fb.text("HungsOS PC", max(8, x+24), 91, WHITE)
        show(); time.sleep_ms(15)
    fb.fill(BLUE)
    centered("Welcome", 75, WHITE)
    centered("Your little PC is ready", 108, CYAN)
    centered("Starting desktop...", 158, WHITE)
    show(); time.sleep_ms(900)

def login():
    fb.fill(BG); fb.fill_rect(0, 0, 320, 240, BG)
    fb.fill_rect(70, 34, 180, 172, DARK)
    fb.fill_rect(135, 53, 50, 50, BLUE)
    centered("H", 73, WHITE)
    centered("Welcome back", 119, WHITE)
    centered("HUNG  |  LOGIN", 151, CYAN)
    centered("Remote control ready", 181, GRAY)
    show(); time.sleep_ms(1000)

def app_icon(x, y, label, glyph, color):
    fb.fill_rect(x, y, 42, 38, PANEL)
    fb.rect(x, y, 42, 38, color)
    fb.text(glyph, x+8, y+14, color)
    fb.text(label, x-3, y+43, WHITE)

def desktop():
    global current_app
    current_app = "desktop"
    topbar("HungsOS PC")
    fb.text("Good day, HUNG", 13, 39, WHITE)
    fb.text("Your workspace", 13, 55, GRAY)
    app_icon(18, 82, "Files", "DIR", CYAN)
    app_icon(88, 82, "Notes", "TXT", YELLOW)
    app_icon(158, 82, "Games", "PLY", GREEN)
    app_icon(228, 82, "Settings", "CFG", PURPLE)
    app_icon(18, 151, "Bin", "BIN", RED)
    # Tablet-style bottom dock / taskbar
    fb.fill_rect(0, 211, 320, 29, DARK)
    fb.fill_rect(105, 216, 110, 19, PANEL)
    fb.text("HOME", 143, 222, WHITE)
    fb.text("H", 14, 222, CYAN)
    fb.text("Apps", 267, 222, WHITE)
    show()

def page(title, lines):
    topbar(title)
    y = 43
    for line in lines:
        fb.fill_rect(9, y-5, 302, 25, PANEL)
        fb.text(str(line)[:36], 18, y+3, WHITE)
        y += 33
    fb.fill_rect(0, 211, 320, 29, DARK)
    fb.text("< HOME", 12, 222, CYAN)
    show()

def settings():
    global current_app
    current_app = "settings"
    page("Settings", ["Wi-Fi and network", "Bluetooth", "Display: Landscape",
                      "Remote keyboard and mouse", "Storage", "About HungsOS PC"])

def files():
    global current_app
    current_app = "files"
    try:
        names = os.listdir("/")
    except:
        names = []
    page("File Manager", names[:6] if names else ["No files found"])

def notepad():
    global current_app
    current_app = "notes"
    page("Notepad", ["Notes are stored in RAM for now",
                     note_text[:34] if note_text else "Use the remote keyboard",
                     "SD-card saving: coming next"])

def games():
    global current_app
    current_app = "games"
    page("Games", ["Game Center", "More mini-games coming soon"])

def open_app(name):
    if name == "home": desktop()
    elif name == "settings": settings()
    elif name == "files": files()
    elif name == "notepad": notepad()
    elif name == "games": games()
    elif name == "bin": page("Recycle Bin", ["The bin is empty"])
    elif name == "apps": page("Apps", ["Files", "Notepad", "Games", "Settings"])

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.ifconfig((STATIC_IP, SUBNET, GATEWAY, DNS))
    except Exception as e:
        print("Static IP config:", e)
    if PASSWORD == "PUT_YOUR_WIFI_PASSWORD_HERE" or SSID == "YOUR_WIFI_NAME":
        print("Add your real Wi-Fi details to wifi-pass.py on the ESP32.")
        return wlan
    try:
        wlan.connect(SSID, PASSWORD)
        for _ in range(30):
            if wlan.isconnected():
                print("HungsOS Wi-Fi:", wlan.ifconfig())
                return wlan
            time.sleep_ms(500)
    except Exception as e:
        print("Wi-Fi:", e)
    return wlan

PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HungsOS PC Remote</title><style>
*{box-sizing:border-box}body{margin:0;padding:18px;background:#101827;color:#f5f7ff;font:16px Arial}
main{max-width:560px;margin:auto}h2{margin:8px 0 16px}.card{background:#202d40;border-radius:20px;padding:16px;margin:12px 0}
button{border:0;border-radius:13px;padding:13px 15px;margin:4px;background:#347fbd;color:white;font-size:16px}
.pad{display:grid;grid-template-columns:repeat(3,1fr);max-width:280px;margin:auto}.pad button{font-size:21px}
.apps{display:grid;grid-template-columns:repeat(3,1fr)}.apps button{font-size:14px}
input{width:100%;padding:14px;border:0;border-radius:12px;font-size:17px;margin:6px 0}
.keys{display:grid;grid-template-columns:repeat(7,1fr)}.keys button{padding:10px 2px;margin:2px;font-size:14px}
small{color:#aab8ce}
</style></head><body><main><h2>HungsOS PC <small>· Remote</small></h2>
<p><a style="color:#7dd3fc" href="/cast">Open Video Cast</a></p>
<div class="card"><b>Touchpad / mouse</b><div class="pad">
<button onclick="send('up')">▲</button><button onclick="send('click')">●</button><button onclick="send('right')">▶</button>
<button onclick="send('left')">◀</button><button onclick="send('down')">▼</button><button onclick="send('home')">⌂</button></div></div>
<div class="card"><b>Apps</b><div class="apps">
<button onclick="send('files')">Files</button><button onclick="send('notepad')">Notepad</button><button onclick="send('games')">Games</button>
<button onclick="send('settings')">Settings</button><button onclick="send('bin')">Recycle Bin</button><button onclick="send('home')">Desktop</button></div></div>
<div class="card"><b>Keyboard</b><input id="t" placeholder="Type here, then Send">
<button onclick="sendText()">Send text</button><div class="keys" id="keys"></div>
<button onclick="key('SPACE')">Space</button><button onclick="key('BACKSPACE')">⌫</button><button onclick="key('ENTER')">Enter</button></div>
<script>
const letters='QWERTYUIOPASDFGHJKLZXCVBNM';
document.getElementById('keys').innerHTML=[...letters].map(x=>'<button onclick="key(\''+x+'\')">'+x+'</button>').join('');
function send(x){fetch('/cmd?c='+x)}
function key(x){fetch('/cmd?c=key&v='+encodeURIComponent(x))}
function sendText(){let e=document.getElementById('t');fetch('/cmd?c=text&v='+encodeURIComponent(e.value));e.value=''}
</script></main></body></html>"""

def decode(v):
    return v.replace("%20", " ").replace("%21", "!").replace("%3F", "?").replace("%2C", ",").replace("%2E", ".")

def query(path):
    result = {}
    if "?" not in path:
        return result
    for part in path.split("?", 1)[1].split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k] = decode(v.replace("+", " "))
    return result

def server_loop(wlan):
    if not wlan.isconnected():
        print("Remote server not started: Wi-Fi is offline.")
        return
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 80)); s.listen(1); s.settimeout(0.2)
    print("HungsOS PC Remote: http://" + STATIC_IP)
    while True:
        try:
            client, _ = s.accept()
        except OSError:
            continue
        try:
            client.settimeout(4)
            req = client.recv(2048)
            if not req:
                client.close()
                continue
            header_end = req.find(b"\r\n\r\n")
            while header_end < 0 and len(req) < 8192:
                more = client.recv(1024)
                if not more: break
                req += more
                header_end = req.find(b"\r\n\r\n")
            if header_end < 0:
                raise ValueError("HTTP headers incomplete")
            header = req[:header_end]
            body = req[header_end+4:]
            method_path = header.split(b"\r\n", 1)[0].decode()
            method, path, _ = method_path.split(" ", 2)
            content_length = 0
            for hline in header.split(b"\r\n")[1:]:
                if hline.lower().startswith(b"content-length:"):
                    content_length = int(hline.split(b":",1)[1].strip())
            while len(body) < content_length:
                more = client.recv(min(2048, content_length-len(body)))
                if not more: break
                body += more
            if len(body) != content_length:
                raise ValueError("HTTP body incomplete")
            if not req:
                client.close()
                continue
            line = req.split(b"\r\n", 1)[0].decode()
            path = line.split(" ")[1]
            if method == "POST" and path.startswith("/video/frame"):
                ok = apply_packet(body, buf, show)
                response = b"OK" if ok else b"BAD PACKET"
                status = b"200 OK" if ok else b"400 Bad Request"
                client.send(b"HTTP/1.1 " + status + b"\r\nContent-Type:text/plain\r\nContent-Length:" + str(len(response)).encode() + b"\r\nConnection:close\r\n\r\n" + response)
            elif method == "GET" and path.startswith("/cast"):
                body_out = CAST_PAGE.encode()
                client.send(b"HTTP/1.1 200 OK\r\nContent-Type:text/html\r\nContent-Length:" + str(len(body_out)).encode() + b"\r\nConnection:close\r\n\r\n" + body_out)
            elif path.startswith("/cmd"):
                q = query(path)
                action = q.get("c", "")
                if action in ("home", "settings", "files", "notepad", "games", "bin", "apps"):
                    open_app(action)
                elif action == "text":
                    global note_text
                    note_text = (note_text + q.get("v", ""))[-120:]
                    if current_app == "notes":
                        notepad()
                elif action == "key":
                    value = q.get("v", "")
                    if value == "BACKSPACE":
                        note_text = note_text[:-1]
                    elif value == "SPACE":
                        note_text += " "
                    elif value == "ENTER":
                        note_text += " "
                    elif len(value) == 1:
                        note_text += value
                    note_text = note_text[-120:]
                    if current_app == "notes":
                        notepad()
                body = b"OK"
                client.send(b"HTTP/1.1 200 OK\r\nContent-Type:text/plain\r\nConnection:close\r\n\r\n" + body)
            else:
                body = PAGE.encode()
                client.send(b"HTTP/1.1 200 OK\r\nContent-Type:text/html\r\nConnection:close\r\nContent-Length:" + str(len(body)).encode() + b"\r\n\r\n")
                client.send(body)
        except Exception as e:
            print("HTTP:", e)
        try:
            client.close()
        except:
            pass

init_display()
splash()
welcome()
login()
desktop()
wlan = wifi_connect()
gc.collect()
server_loop(wlan)
