
# ============================================================
# HungsOS Pocket Edition
# ESP32-S3 + MicroPython
# iPhone-inspired web interface
# ============================================================

import network
import socket
import time
import os
import gc
import machine
import sys
import json

# Optional feature modules fail closed so a missing module won't stop boot.
try:
    import social_apps
except ImportError:
    social_apps = None

try:
    import bluetooth
except ImportError:
    bluetooth = None

# -------------------- WIFI SETTINGS --------------------------

try:
    from wifi_config import SSID, PASSWORD   # your private file, not in git
except ImportError:
    SSID = "YOUR_WIFI_NAME"
    PASSWORD = "YOUR_WIFI_PASSWORD"

try:
    from wifi_config import WEATHER_LAT, WEATHER_LON, WEATHER_NAME
except ImportError:
    WEATHER_LAT, WEATHER_LON, WEATHER_NAME = 10.82, 106.63, "Ho Chi Minh City"

try:
    from wifi_config import WIKI_LANG     # e.g. "vi" for Vietnamese Wikipedia
except ImportError:
    WIKI_LANG = "en"

try:
    from wifi_config import KALI_URL      # optional: address of a real Kali web terminal
except ImportError:
    KALI_URL = ""

try:
    from wifi_config import TERM_PIN      # optional: PIN that unlocks the Python prompt
except ImportError:
    TERM_PIN = ""

TZ_HOURS = 7          # Vietnam (UTC+7); change for other time zones
SYNCED = False        # becomes True once the clock is set from the internet

# -------------------- HTML / CSS -----------------------------

CSS = r"""
:root {
 --bg:#f2f2f7; --card:#fff; --ink:#17171b;
 --muted:#85858f; --blue:#087fff; --line:#e7e7ed;
 --green:#30c76a; --purple:#a58af5;
}
* { box-sizing:border-box; }
body {
 margin:0; background:var(--bg); color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
 -webkit-font-smoothing:antialiased;
}
.wrap { max-width:560px; margin:auto; padding:18px 18px 105px; }
.status {
 display:flex; justify-content:space-between; gap:12px;
 font-size:12px; font-weight:650; padding:5px 3px;
}
.brand { font-size:14px; font-weight:750; letter-spacing:-.3px; }
.hero { padding:27px 2px 23px; }
.eyebrow { font-size:13px; color:var(--muted); font-weight:600; }
.clock { font-size:62px; font-weight:300; letter-spacing:-3px; line-height:1.15; }
.date { font-size:15px; color:var(--muted); margin-top:5px; }
h1 { font-size:32px; letter-spacing:-1.2px; margin:20px 0 5px; }
h2 { font-size:23px; letter-spacing:-.6px; margin:8px 0 16px; }
h3 { font-size:16px; margin:23px 0 10px; }
.sub { color:var(--muted); font-size:14px; line-height:1.5; }
.section-title {
 font-size:13px; font-weight:750; color:var(--muted);
 letter-spacing:.5px; text-transform:uppercase; margin:25px 2px 12px;
}
.grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:19px 13px; }
.app-pages {
 display:flex; width:100%; overflow-x:auto; overflow-y:hidden;
 scroll-snap-type:x mandatory; scroll-behavior:smooth;
 -webkit-overflow-scrolling:touch; overscroll-behavior-x:contain;
 scrollbar-width:none; touch-action:pan-x pan-y;
}
.app-pages::-webkit-scrollbar { display:none; }
.app-page { flex:0 0 100%; min-width:100%; scroll-snap-align:start; scroll-snap-stop:always; }
.app-page .grid { grid-template-rows:repeat(4,auto); align-content:start; min-height:280px; }
.page-dots { display:flex; justify-content:center; align-items:center; gap:7px; margin:18px 0 8px; }
.page-dot { width:7px; height:7px; border-radius:50%; background:#c7c7d0; transition:all .18s ease; }
.page-dot.active { width:19px; border-radius:5px; background:var(--blue); }
.app { text-decoration:none; color:var(--ink); text-align:center; min-width:0; }
.icon {
 aspect-ratio:1; border-radius:23%; display:grid; place-items:center;
 font-size:31px; color:white; box-shadow:0 5px 12px #10102010;
}
.appname { font-size:12px; font-weight:600; margin-top:8px; overflow-wrap:anywhere; }
.blue { background:linear-gradient(145deg,#57b6ff,#087fff); }
.green { background:linear-gradient(145deg,#62e89b,#20b85e); }
.orange { background:linear-gradient(145deg,#ffcb71,#ff8734); }
.purple { background:linear-gradient(145deg,#c1a8ff,#8760e9); }
.pink { background:linear-gradient(145deg,#ff9bc5,#ed4c88); }
.dark { background:linear-gradient(145deg,#60616d,#282932); }
.yellow { background:linear-gradient(145deg,#ffe38a,#f5b800); }
.teal { background:linear-gradient(145deg,#65e4dc,#12a9b2); }
.card {
 background:var(--card); border-radius:20px; padding:16px;
 margin:10px 0; box-shadow:0 2px 8px #15152b06; overflow-wrap:anywhere;
}
.card-title { font-weight:700; font-size:15px; margin-bottom:5px; }
.row {
 display:flex; justify-content:space-between; align-items:center;
 gap:12px; padding:13px 0; border-bottom:1px solid var(--line);
}
.row:last-child { border-bottom:0; }
.value { text-align:right; overflow-wrap:anywhere; font-size:14px; }
.muted { color:var(--muted); font-size:13px; }
a { color:var(--blue); text-decoration:none; }
.back { display:inline-block; margin:8px 0 15px; font-size:14px; font-weight:650; }
input,textarea {
 width:100%; font:inherit; background:#f5f5fa; color:var(--ink);
 border:1px solid #e4e4ec; border-radius:13px; padding:13px;
 outline:none; margin:5px 0;
}
textarea { height:230px; resize:vertical; line-height:1.5; }
input:focus,textarea:focus { border-color:#77b8ff; }
button,.button {
 border:0; border-radius:13px; padding:12px 16px;
 background:var(--blue); color:white; font-size:14px;
 font-weight:700; cursor:pointer; display:inline-block; text-align:center;
}
button:active,.button:active { opacity:.7; }
.secondary { background:#e8f2ff; color:var(--blue); }
.danger { background:#ffe9e9; color:#dc3434; }
.full { width:100%; }
.bottom {
 position:fixed; bottom:0; left:0; right:0; z-index:10;
 background:#ffffffee; border-top:1px solid #e4e4eb;
 padding:10px 12px calc(10px + env(safe-area-inset-bottom));
 display:flex; justify-content:center;
}
.bottom-inner { width:100%; max-width:520px; display:flex; justify-content:space-around; }
.tab { color:var(--muted); font-size:10px; text-align:center; min-width:55px; font-weight:600; }
.tabicon { font-size:22px; display:block; margin-bottom:3px; }
.tab.active { color:var(--blue); }
pre { white-space:pre-wrap; word-break:break-word; font-size:13px; }
.calc-display {
 background:#fff; border-radius:20px; padding:20px 15px;
 text-align:right; font-size:30px; min-height:80px; overflow-wrap:anywhere;
}
.calc-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:12px; }
.calc-grid button { aspect-ratio:1; border-radius:50%; padding:4px; font-size:20px; background:#e4e4eb; color:#17171b; }
.calc-grid button.op { background:#087fff; color:white; }
.calc-grid button.eq { background:#30c76a; color:white; }
.calc-grid button.fn { background:#d1d1d8; color:#17171b; }
@media(max-width:370px) {
 .wrap { padding-left:13px; padding-right:13px; }
 .clock { font-size:53px; }
 .grid { gap:16px 9px; }
 .icon { font-size:27px; }
}
"""

# -------------------- HTML HELPERS ---------------------------

def esc(value):
    value = str(value)
    return (value.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace('"', "&quot;")
                 .replace("'", "&#x27;"))

def decode(value):
    # URL-decode as UTF-8 bytes so Vietnamese letters etc. survive
    value = value.replace("+", " ")
    if "%" not in value:
        return value
    out = bytearray()
    i = 0
    n = len(value)
    while i < n:
        c = value[i]
        if c == "%" and i + 2 < n:
            try:
                out.append(int(value[i+1:i+3], 16))
                i += 3
                continue
            except Exception:
                pass
        out.extend(c.encode())
        i += 1
    try:
        return out.decode()
    except Exception:
        return value

def form_value(body, name):
    try:
        text = body.decode("utf-8")
    except Exception:
        text = str(body)
    for item in text.split("&"):
        parts = item.split("=", 1)
        if len(parts) == 2 and decode(parts[0]) == name:
            return decode(parts[1])
    return ""

def page(title, content, active="home"):
    tabs = [
        ("home", "/", "⌂", "Home"),
        ("wifi", "/wifi", "◉", "Wi-Fi"),
        ("system", "/system", "⚙", "System"),
        ("files", "/files", "▤", "Files")
    ]
    nav = ""
    for key, url, icon, label in tabs:
        cls = "tab active" if key == active else "tab"
        nav += '<a class="' + cls + '" href="' + url + '">'
        nav += '<span class="tabicon">' + icon + '</span>'
        nav += esc(label) + '</a>'

    # CSS is deliberately wrapped in <style> tags.
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f2f2f7">
<title>HungsOS - """ + esc(title) + """</title>
<style>
""" + CSS + """
</style>
</head>
<body>
<div class="wrap">
<div class="status">
<span>● HungsOS</span><span>●●● Wi-Fi</span>
</div>
<div class="brand">HungsOS <span style="color:#087fff">Pocket Edition</span></div>
<a class="back" href="/">‹ Home</a>
""" + content + """
</div>
<div class="bottom"><div class="bottom-inner">""" + nav + """</div></div>
</body>
</html>"""

def app(icon, name, url, color):
    return ('<a class="app" href="' + url + '">'
            '<div class="icon ' + color + '">' + icon + '</div>'
            '<div class="appname">' + name + '</div></a>')

def row(label, value):
    return ('<div class="row"><span class="muted">' + esc(label) +
            '</span><span class="value">' + esc(value) + '</span></div>')

def card(title, body):
    return ('<div class="card"><div class="card-title">' +
            esc(title) + '</div>' + body + '</div>')

# -------------------- WIFI -----------------------------------

wlan = network.WLAN(network.STA_IF)

def wifi_reset():
    # clears a stuck Wi-Fi driver ("Wifi Internal State Error")
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)

def connect():
    if SSID == "YOUR_WIFI_NAME":
        print("Set your Wi-Fi name and password first (see README).")
        return "0.0.0.0"
    print("Connecting to Wi-Fi:", SSID)
    wifi_reset()
    for attempt in range(1, 4):
        print("Attempt", attempt, "of 3...")
        try:
            wlan.connect(SSID, PASSWORD)
        except OSError as e:
            print("Wi-Fi error, retrying:", e)
            wifi_reset()
            continue
        for _ in range(20):
            if wlan.isconnected():
                try:
                    wlan.config(pm=wlan.PM_NONE)  # no Wi-Fi sleep -> no page timeouts
                except Exception:
                    pass
                config = wlan.ifconfig()
                print("Connected!", config)
                return config[0]
            time.sleep(1)
        wifi_reset()
    print("Wi-Fi did not connect. Check SSID/password (2.4 GHz only).")
    return "0.0.0.0"

# -------------------- PAGES ----------------------------------

def page_home():
    if SYNCED:
        now = time.localtime(time.time() + TZ_HOURS * 3600)
        clock = "%02d:%02d" % (now[3], now[4])
        date = "%04d-%02d-%02d" % (now[0], now[1], now[2])
    else:
        clock = "--:--"
        date = "Time not synced (no internet?)"

    app_items = (
        app("📝", "Notes", "/notes", "yellow"),
        app("🤖", "Assistant", "/assistant", "purple"),
        app("🌐", "Web Apps", "/social", "blue"),
        app("💹", "Bank", "/bank", "green"),
        app("☀️", "Weather", "/weather", "teal"),
        app("👤", "Contacts", "/contacts", "green"),
        app("📅", "Calendar", "/calendar", "pink"),
        app("⚖️", "Convert", "/convert", "orange"),
        app("🧠", "DOPE AI", "/dope", "purple"),
        app("🐍", "Snake", "/snake", "green"),
        app("🎮", "Games", "/games", "purple"),
        app("🔑", "Passwords", "/passgen", "purple"),
        app("🌍", "World", "/world", "blue"),
        app("🛜", "Net Tools", "/nettools", "dark"),
        app("✅", "Tasks", "/todo", "orange"),
        app("📁", "Files", "/files", "blue"),
        app("⏱", "Timer", "/timer", "teal"),
        app("📈", "Monitor", "/monitor", "green"),
        app("🔌", "GPIO", "/gpio", "purple"),
        app("📶", "Wi-Fi", "/wifi", "green"),
        app("ᛒ", "Bluetooth", "/bluetooth", "purple"),
        app("⌨", "Terminal", "/terminal", "dark"),
        app("🐉", "Kali", "/kali", "blue"),
        app("🧮", "Calculator", "/calc", "orange"),
        app("⚙️", "Settings", "/system", "dark"),
        app("🔄", "Reboot", "/reboot", "pink")
    )

    app_pages = ""
    page_dots = ""
    page_count = (len(app_items) + 11) // 12
    for page_index in range(page_count):
        first = page_index * 12
        page_apps = "".join(app_items[first:first + 12])
        app_pages += '<section class="app-page"><div class="grid">' + page_apps + '</div></section>'
        active = " active" if page_index == 0 else ""
        page_dots += '<span class="page-dot' + active + '"></span>'

    content = """
<div class="hero">
<div class="eyebrow">Welcome back</div>
<div class="clock">""" + clock + """</div>
<div class="date">""" + date + """</div>
<h1>Applications</h1>
<div class="sub">Your pocket-sized ESP32 computer.</div>
</div>
<div class="app-pages" id="appPages">""" + app_pages + """</div>
<div class="page-dots" id="pageDots">""" + page_dots + """</div>
<script>
(function(){
 var strip=document.getElementById("appPages");
 var dots=document.getElementById("pageDots");
 if(!strip||!dots)return;
 var items=dots.children;
 var update=function(){
  var page=Math.round(strip.scrollLeft/(strip.clientWidth||1));
  for(var i=0;i<items.length;i++){
   if(i===page)items[i].classList.add("active");
   else items[i].classList.remove("active");
  }
 };
 strip.addEventListener("scroll",update);
 window.addEventListener("resize",update);
})();
</script>
<div class="section-title">Device</div>
""" + card("HungsOS Pocket Edition",
    row("Hardware", "ESP32-S3") +
    row("Firmware", "MicroPython") +
    row("Wi-Fi address", IP) +
    row("Free RAM", "%d KB" % (gc.mem_free() // 1024)))
    return page("Home", content, "home")

def page_notes(message=""):
    try:
        with open("note.txt", "r") as f:
            note = f.read()
    except Exception:
        note = ""

    content = """
<h1>Notes</h1>
<div class="sub">A small place for your thoughts.</div>
""" + card("My note", """
<form method="POST" action="/notes">
<textarea name="note" maxlength="4000" placeholder="Write something...">""" + esc(note) + """</textarea>
<button class="full" type="submit">Save Note</button>
</form>
""" + ('<p class="muted">' + esc(message) + '</p>' if message else ''))
    return page("Notes", content)

def page_files():
    items = ""
    try:
        names = os.listdir("/")
        for name in names:
            if name.startswith("."):
                continue
            safe = esc(name)
            items += '<div class="row"><span>📄 ' + safe + '</span>'
            items += '<span><a href="/view?name=' + name + '">Open</a> &nbsp; <a href="/edit?name=' + name + '">Edit</a></span></div>'
    except Exception as e:
        items = "<p>Could not list files: " + esc(e) + "</p>"

    content = "<h1>Files</h1><div class='sub'>Files stored on the device.</div>"
    content += card("Device storage", items or "No files found.")
    content += card("New file", '<form method="GET" action="/edit"><input name="name" placeholder="example.txt" maxlength="32"><button class="full" type="submit">Create / open</button></form>')
    return page("Files", content, "files")

def page_view(name):
    if "/" in name or "\\" in name or name.startswith("."):
        return page("File", "<h1>File</h1><p>Invalid filename.</p>", "files")
    try:
        with open(name, "r") as f:
            data = f.read(6000)
        body = "<h1>" + esc(name) + "</h1>"
        body += card("Contents", "<pre>" + esc(data) + "</pre>")
    except Exception as e:
        body = "<h1>Cannot open file</h1><p>" + esc(e) + "</p>"
    return page("File", body, "files")

def page_system():
    gc.collect()
    try:
        free = gc.mem_free()
        alloc = gc.mem_alloc()
    except Exception:
        free, alloc = 0, 0

    try:
        ip = wlan.ifconfig()[0] if wlan.isconnected() else "Disconnected"
    except Exception:
        ip = "Unknown"

    content = "<h1>Settings</h1><div class='sub'>Your HungsOS device.</div>"
    content += card("About this device",
        row("Name", "HungsOS Pocket Edition") +
        row("Board", "ESP32-S3") +
        row("Firmware", "MicroPython") +
        row("Wi-Fi", ip) +
        row("Free RAM", str(free // 1024) + " KB") +
        row("Used RAM", str(alloc // 1024) + " KB"))
    content += card("Power",
        '<a class="button full" href="/reboot">Restart HungsOS</a>')
    return page("Settings", content, "system")

def page_wifi():
    try:
        connected = wlan.isconnected()
        ip = wlan.ifconfig()[0] if connected else "Not connected"
    except Exception:
        connected, ip = False, "Unavailable"

    body = row("Network", SSID)
    body += row("Status", "Connected" if connected else "Disconnected")
    body += row("IP address", ip)
    content = "<h1>Wi-Fi</h1><div class='sub'>Network connection status.</div>"
    content += card("Connection", body)
    content += card("Actions", """
<form method="POST" action="/wifi">
<button class="full" name="action" value="reconnect">Reconnect Wi-Fi</button>
</form>
""")
    return page("Wi-Fi", content, "wifi")

def page_bluetooth():
    content = "<h1>Bluetooth</h1>"
    content += "<div class='sub'>Bluetooth Low Energy scanner.</div>"

    if bluetooth is None:
        content += card("Unavailable",
            "This MicroPython firmware does not provide the bluetooth module.")
    else:
        content += card("Scan nearby devices", """
<p class="muted">Scanning can take several seconds.</p>
<form method="POST" action="/bluetooth">
<button class="full" type="submit">Scan for BLE devices</button>
</form>
""")
    return page("Bluetooth", content)

def scan_ble():
    if bluetooth is None:
        return "Bluetooth module unavailable."

    try:
        ble = bluetooth.BLE()
        ble.active(True)
        found = []

        def irq(event, data):
            if event == 5:
                addr_type, addr, adv_type, rssi, adv_data = data
                address = ":".join("%02X" % b for b in bytes(addr))
                if address not in found and len(found) < 15:
                    found.append(address + " (RSSI " + str(rssi) + ")")

        ble.irq(irq)
        ble.gap_scan(5000, 30000, 30000)
        time.sleep(5)
        ble.gap_scan(None)
        ble.active(False)

        if not found:
            return "No devices found. Try scanning again."
        return "\n".join(found)
    except Exception as e:
        try:
            ble.active(False)
        except Exception:
            pass
        return "BLE scan error: " + str(e)

def page_calc():
    content = """
<h1>Calculator</h1>
<div class="sub">Simple arithmetic calculator.</div>
<div class="card">
<input id="display" class="calc-display" value="0" readonly>
<div class="calc-grid">
<button class="fn" onclick="clr()">AC</button>
<button class="fn" onclick="del()">⌫</button>
<button class="fn" onclick="add('%')">%</button>
<button class="op" onclick="add('/')">÷</button>
<button onclick="add('7')">7</button><button onclick="add('8')">8</button>
<button onclick="add('9')">9</button><button class="op" onclick="add('*')">×</button>
<button onclick="add('4')">4</button><button onclick="add('5')">5</button>
<button onclick="add('6')">6</button><button class="op" onclick="add('-')">−</button>
<button onclick="add('1')">1</button><button onclick="add('2')">2</button>
<button onclick="add('3')">3</button><button class="op" onclick="add('+')">+</button>
<button onclick="add('0')">0</button><button onclick="add('.')">.</button>
<button class="fn" onclick="sign()">±</button><button class="eq" onclick="calc()">=</button>
</div></div>
<script>
let exp='';
const d=document.getElementById('display');
function add(v){exp+=v;d.value=exp||'0';}
function clr(){exp='';d.value='0';}
function del(){exp=exp.slice(0,-1);d.value=exp||'0';}
function sign(){if(exp.startsWith('-'))exp=exp.slice(1);else exp='-'+exp;d.value=exp;}
function calc(){
 try{
  if(!/^[0-9+*/%.() -]+$/.test(exp))throw 0;
  let result=Function('"use strict";return ('+exp+')')();
  if(!Number.isFinite(result))throw 0;
  exp=String(result);d.value=exp;
 }catch(e){d.value='Error';exp='';}
}
</script>
"""
    return page("Calculator", content)


# -------------------- EXTRA APPS ------------------------------

TODO_FILE = "todo.txt"
PROTECTED = ("main.py", "boot.py", "app.py")
GPIO_OK = (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,21,38,39,40,41,42,47)
gpio_state = {}

def valid_name(name):
    return (0 < len(name) <= 32 and "/" not in name and "\\" not in name
            and not name.startswith("."))

def todo_load():
    items = []
    try:
        with open(TODO_FILE) as f:
            for line in f:
                line = line.strip()
                if len(line) > 2 and line[1] == "|":
                    items.append([line[0] == "1", line[2:]])
    except OSError:
        pass
    return items[:50]

def todo_save(items):
    with open(TODO_FILE, "w") as f:
        for done, text in items:
            f.write(("1|" if done else "0|") + text + "\n")

def page_todo():
    items = todo_load()
    rows = ""
    for i, (done, text) in enumerate(items):
        label = ("<s class=muted>" + esc(text) + "</s>") if done else esc(text)
        rows += ('<form method="POST" action="/todo" class="row">'
                 '<span>' + label + '</span><span>'
                 '<button name="act" value="t%d" class="secondary">%s</button> '
                 '<button name="act" value="d%d" class="danger">&times;</button>'
                 '</span></form>') % (i, "Undo" if done else "Done", i)
    left = len([1 for d, t in items if not d])
    content = "<h1>Tasks</h1><div class='sub'>%d to do, %d total.</div>" % (left, len(items))
    content += card("Add a task", '<form method="POST" action="/todo">'
                    '<input name="text" maxlength="100" placeholder="What needs doing?">'
                    '<button class="full" name="act" value="add">Add</button></form>')
    content += card("Your list", rows or "<span class=muted>Nothing yet.</span>")
    return page("Tasks", content)

def page_timer():
    content = """
<h1>Timer</h1><div class="sub">Stopwatch and countdown (runs in your browser).</div>
<div class="card"><div class="card-title">Stopwatch</div>
<div class="calc-display" id="sw">00:00.0</div><br>
<button onclick="swGo()" id="swb">Start</button>
<button class="secondary" onclick="swLap()">Lap</button>
<button class="danger" onclick="swReset()">Reset</button>
<pre id="laps"></pre></div>
<div class="card"><div class="card-title">Countdown</div>
<input id="mins" type="number" min="0" max="600" value="5">
<div class="calc-display" id="cd">05:00</div><br>
<button onclick="cdGo()" id="cdb">Start</button>
<button class="danger" onclick="cdReset()">Reset</button></div>
<script>
var st=0,el=0,run=false,ti=null,laps=[];
function f(ms){var t=Math.floor(ms/100),d=t%10,s=Math.floor(t/10)%60,m=Math.floor(t/600);
 return (m<10?'0':'')+m+':'+(s<10?'0':'')+s+'.'+d;}
function swGo(){if(!run){st=Date.now()-el;ti=setInterval(function(){el=Date.now()-st;
 document.getElementById('sw').textContent=f(el);},100);run=true;swb.textContent='Pause';}
 else{clearInterval(ti);run=false;swb.textContent='Start';}}
function swLap(){if(el){laps.push(f(el));document.getElementById('laps').textContent=
 laps.map(function(x,i){return (i+1)+'. '+x;}).join('\\n');}}
function swReset(){clearInterval(ti);run=false;el=0;laps=[];swb.textContent='Start';
 document.getElementById('sw').textContent='00:00.0';document.getElementById('laps').textContent='';}
var cdt=null,left=0;
function cf(s){var m=Math.floor(s/60),x=s%60;return (m<10?'0':'')+m+':'+(x<10?'0':'')+x;}
function cdGo(){if(cdt){clearInterval(cdt);cdt=null;cdb.textContent='Start';return;}
 if(!left)left=Math.round(parseFloat(document.getElementById('mins').value||0)*60);
 if(!left)return;cdb.textContent='Pause';
 cdt=setInterval(function(){left--;document.getElementById('cd').textContent=cf(left);
 if(left<=0){clearInterval(cdt);cdt=null;left=0;cdb.textContent='Start';
 try{navigator.vibrate(500)}catch(e){}alert("Time's up!");}},1000);}
function cdReset(){clearInterval(cdt);cdt=null;left=0;cdb.textContent='Start';
 document.getElementById('cd').textContent=cf(Math.round(parseFloat(document.getElementById('mins').value||0)*60));}
</script>
"""
    return page("Timer", content)

def temp_c():
    try:
        import esp32
        return round(esp32.mcu_temperature(), 1)
    except Exception:
        return None

def api_stats():
    # Return a compact telemetry snapshot for the Task Manager page.
    gc.collect()
    free = gc.mem_free()
    used = gc.mem_alloc()
    connected = False
    rssi = -100
    ip = ""
    mac = ""
    try:
        connected = wlan.isconnected()
    except Exception:
        pass
    if connected:
        try:
            rssi = wlan.status("rssi")
        except Exception:
            rssi = -100
        try:
            ip = wlan.ifconfig()[0]
        except Exception:
            ip = ""
    try:
        raw_mac = wlan.config("mac")
        mac = ":".join("%02x" % b for b in raw_mac)
    except Exception:
        mac = ""
    temp = temp_c()
    try:
        freq = machine.freq()
    except Exception:
        freq = 0
    try:
        up = time.ticks_ms() // 1000
    except Exception:
        up = 0
    try:
        reset = machine.reset_cause()
    except Exception:
        reset = -1
    flash_total = 0
    flash_free = 0
    try:
        st = os.statvfs("/")
        block_size = st[0]
        flash_total = st[2] * block_size
        flash_free = st[3] * block_size
    except Exception:
        pass
    data = {
        "free": free,
        "used": used,
        "heap_total": free + used,
        "wifi": connected,
        "rssi": rssi,
        "ip": ip,
        "mac": mac,
        "temp": temp,
        "freq": freq,
        "up": up,
        "reset": reset,
        "version": sys.version,
        "platform": sys.platform,
        "flash_total": flash_total,
        "flash_free": flash_free
    }
    return json.dumps(data)

def page_monitor():
    content = """
<h1>Task Manager</h1><div class="sub">HungsOS System Monitor · live device telemetry</div>
<div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">
 <div class="card"><div class="card-title">Heap memory</div><div class="clock" id="memnow" style="font-size:26px">--</div><div class="muted" id="memplus">Waiting for data…</div><div class="meter"><div id="membar"></div></div></div>
 <div class="card"><div class="card-title">Wi-Fi signal</div><div class="clock" id="wifinow" style="font-size:26px">--</div><div class="muted" id="wifitxt">Signal strength</div><div class="meter"><div id="wifibar"></div></div></div>
 <div class="card"><div class="card-title">Chip temperature</div><div class="clock" id="tempnow" style="font-size:26px">--</div><div class="muted">Internal estimate, if supported</div></div>
 <div class="card"><div class="card-title">CPU frequency</div><div class="clock" id="cpunow" style="font-size:26px">--</div><div class="muted">Clock speed, not CPU utilization</div></div>
</div>
<div class="card"><div class="card-title">Memory history</div><div class="muted">Last 60 samples · every 3 seconds</div><canvas id="memchart" width="500" height="130" style="width:100%;height:130px"></canvas><div class="muted" id="memlegend"></div></div>
<div class="card"><div class="card-title">Wi-Fi signal history</div><canvas id="wifichart" width="500" height="110" style="width:100%;height:110px"></canvas></div>
<div class="card"><div class="card-title">Temperature history</div><canvas id="tempchart" width="500" height="110" style="width:100%;height:110px"></canvas></div>
<div class="card"><div class="card-title">Storage</div><div class="row"><span class="muted">Filesystem used</span><span class="value" id="fsused">--</span></div><div class="meter"><div id="fsbar"></div></div><div class="muted" id="fsdetail">Flash filesystem stats, when available</div></div>
<div class="card"><div class="card-title">Network</div><div class="row"><span class="muted">Connection</span><span class="value" id="netstate">--</span></div><div class="row"><span class="muted">IP address</span><span class="value" id="ipaddr">--</span></div><div class="row"><span class="muted">Wi-Fi MAC</span><span class="value" id="macaddr">--</span></div><div class="row"><span class="muted">Signal quality</span><span class="value" id="quality">--</span></div></div>
<div class="card"><div class="card-title">System details</div><div class="row"><span class="muted">Uptime</span><span class="value" id="uptime">--</span></div><div class="row"><span class="muted">Firmware</span><span class="value" id="firmware">--</span></div><div class="row"><span class="muted">Platform</span><span class="value" id="platform">--</span></div><div class="row"><span class="muted">Reset cause code</span><span class="value" id="resetcause">--</span></div><div class="row"><span class="muted">Last successful update</span><span class="value" id="lastupdate">--</span></div><div class="row"><span class="muted">Monitor status</span><span class="value" id="monstatus">Starting…</span></div></div>
<div class="muted" style="padding:8px 2px">Note: this reports the ESP32-S3 itself, not Windows Task Manager. MicroPython does not expose a reliable per-process CPU usage percentage here.</div>
<script>
var series={mem:[],wifi:[],temp:[]},samples=60,lastGood=0;
function byid(id){return document.getElementById(id);}
function fmtBytes(n){if(!n)return 'Unavailable';if(n<1024)return n+' B';if(n<1048576)return (n/1024).toFixed(1)+' KB';return (n/1048576).toFixed(2)+' MB';}
function fmtTime(s){s=Math.max(0,Math.floor(s||0));return Math.floor(s/86400)+'d '+Math.floor(s%86400/3600)+'h '+Math.floor(s%3600/60)+'m '+s%60+'s';}
function draw(id,values,color,min,max){
 var cv=byid(id),ctx=cv.getContext('2d'),w=500,h=cv.height;
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#f7f8fc';ctx.fillRect(0,0,w,h);
 ctx.strokeStyle='#e2e5ed';ctx.lineWidth=1;
 for(var g=1;g<4;g++){ctx.beginPath();ctx.moveTo(0,g*h/4);ctx.lineTo(w,g*h/4);ctx.stroke();}
 if(values.length<2)return;
 var vals=values.slice(),lo=min,hi=max;
 if(lo===null||lo===undefined){lo=Math.min.apply(null,vals);hi=Math.max.apply(null,vals);if(hi===lo){hi+=1;lo-=1;}var pad=(hi-lo)*0.12;lo-=pad;hi+=pad;}
 ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();
 vals.forEach(function(v,i){var x=i*(w-8)/(samples-1)+4,y=h-5-((v-lo)/(hi-lo))*(h-10);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);});ctx.stroke();
}
function tick(){
 fetch('/api/stats',{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(function(d){
  lastGood=Date.now();byid('monstatus').textContent='Live';byid('lastupdate').textContent=new Date().toLocaleTimeString();
  var total=d.heap_total||((d.free||0)+(d.used||0)),pct=total?Math.round(d.used*100/total):0;
  byid('memnow').textContent=pct+'%';byid('memplus').textContent=fmtBytes(d.used)+' used · '+fmtBytes(d.free)+' free';
  byid('membar').style.width=Math.min(100,pct)+'%';
  byid('wifinow').textContent=d.wifi?d.rssi+' dBm':'Offline';
  var q=d.rssi<=-90?0:d.rssi>=-50?100:Math.round((d.rssi+90)/40*100);
  byid('wifitxt').textContent=d.wifi?'Signal estimate':'Not connected';byid('wifibar').style.width=q+'%';byid('quality').textContent=d.wifi?(q>=70?'Strong':q>=40?'Fair':'Weak'):'Offline';
  byid('tempnow').textContent=d.temp===null?'N/A':d.temp+' °C';
  byid('cpunow').textContent=d.freq?Math.round(d.freq/1000000)+' MHz':'N/A';
  byid('fsused').textContent=d.flash_total?Math.round((d.flash_total-d.flash_free)*100/d.flash_total)+'% used':'N/A';
  var fp=d.flash_total?Math.round((d.flash_total-d.flash_free)*100/d.flash_total):0;byid('fsbar').style.width=Math.min(100,fp)+'%';
  byid('fsdetail').textContent=d.flash_total?fmtBytes(d.flash_total-d.flash_free)+' used of '+fmtBytes(d.flash_total)+' total · '+fmtBytes(d.flash_free)+' free':'Filesystem usage unavailable';
  byid('netstate').textContent=d.wifi?'Connected':'Disconnected';byid('ipaddr').textContent=d.ip||'--';byid('macaddr').textContent=d.mac||'--';
  byid('uptime').textContent=fmtTime(d.up);byid('firmware').textContent=d.version||'Unknown';byid('platform').textContent=d.platform||'MicroPython';byid('resetcause').textContent=d.reset;
  series.mem.push(total?Math.round(d.used*100/total):0);series.wifi.push(typeof d.rssi==='number'?d.rssi:-100);
  if(d.temp!==null&&typeof d.temp==='number')series.temp.push(d.temp);
  ['mem','wifi','temp'].forEach(function(k){if(series[k].length>samples)series[k].shift();});
  draw('memchart',series.mem,'#087fff',0,100);draw('wifichart',series.wifi,'#30a46c',-100,-30);draw('tempchart',series.temp,'#a05af5',null,null);
  byid('memlegend').textContent='Heap allocation percentage · '+series.mem.length+' samples';
 }).catch(function(){byid('monstatus').textContent='Waiting for device…';});
}
tick();setInterval(tick,3000);
</script>
"""
    return page("Task Manager", content)
def page_gpio(msg=""):
    rows = ""
    for p in sorted(gpio_state):
        rows += row("GPIO %d" % p, "HIGH" if gpio_state[p] else "LOW")
    content = "<h1>GPIO</h1><div class='sub'>Control pins on the board. Safe pins only.</div>"
    content += card("Set a pin", '<form method="POST" action="/gpio">'
        '<input name="pin" type="number" placeholder="Pin number (e.g. 4)">'
        '<button name="act" value="1">HIGH</button> '
        '<button name="act" value="0" class="secondary">LOW</button> '
        '<button name="act" value="r" class="secondary">Read</button></form>'
        + ('<p class="muted">' + esc(msg) + '</p>' if msg else ''))
    content += card("Pins you've set", rows or "<span class=muted>None yet.</span>")
    content += card("Allowed pins", "<span class=muted>" +
                    ", ".join(str(x) for x in GPIO_OK) + "<br>Other pins are used by flash, PSRAM or USB.</span>")
    return page("GPIO", content)

def gpio_act(body):
    try:
        pin = int(form_value(body, "pin"))
    except Exception:
        return "Enter a pin number."
    if pin not in GPIO_OK:
        return "GPIO %d is not allowed." % pin
    act = form_value(body, "act")
    try:
        if act == "r":
            return "GPIO %d reads %d" % (pin, machine.Pin(pin, machine.Pin.IN).value())
        p = machine.Pin(pin, machine.Pin.OUT)
        p.value(1 if act == "1" else 0)
        gpio_state[pin] = 1 if act == "1" else 0
        return "GPIO %d set %s" % (pin, "HIGH" if act == "1" else "LOW")
    except Exception as e:
        return "Error: " + str(e)

def page_edit(name, msg=""):
    if not valid_name(name):
        return page("Edit", "<h1>Invalid file name</h1>", "files")
    try:
        with open(name) as f:
            text = f.read(8000)
    except Exception:
        text = ""
    content = "<h1>" + esc(name) + "</h1>"
    content += card("Editor", '<form method="POST" action="/edit">'
        '<input type="hidden" name="name" value="' + esc(name) + '">'
        '<textarea name="content" style="height:300px;font-family:monospace;font-size:13px">' +
        esc(text) + '</textarea>'
        '<button class="full" name="act" value="save">Save</button><br><br>'
        + ('' if name in PROTECTED else
           '<button class="danger full" name="act" value="delete">Delete file</button>')
        + '</form>' + ('<p class="muted">' + esc(msg) + '</p>' if msg else ''))
    return page("Edit", content, "files")

def route_extra(client, method, path, query, body):
    """Returns True if the request was handled here."""
    if path == "/social" and social_apps is not None:
        respond(client, page("Web Apps", social_apps.content()))
        return True
    if route_more(client, method, path, body):
        return True
    if path == "/api/stats":
        respond(client, api_stats(), content_type="application/json")
        return True
    if path == "/todo":
        if method == "POST":
            items = todo_load()
            act = form_value(body, "act")
            try:
                if act == "add":
                    t = form_value(body, "text").strip()[:100].replace("\n", " ")
                    if t and len(items) < 50:
                        items.append([False, t])
                elif act[:1] == "t":
                    items[int(act[1:])][0] = not items[int(act[1:])][0]
                elif act[:1] == "d":
                    items.pop(int(act[1:]))
                todo_save(items)
            except Exception as e:
                print("todo error:", e)
        respond(client, page_todo())
        return True
    if path == "/kali":
        respond(client, page_kali())
        return True
    if path == "/terminal":
        respond(client, page_terminal())
        return True
    if path == "/api/term":
        if method != "POST":
            respond(client, "POST only", "405 Method Not Allowed", "text/plain")
            return True
        out = run_cmd(form_value(body, "cmd"))
        respond(client, out, content_type="text/plain; charset=utf-8")
        if REBOOT:
            time.sleep(1)
            machine.reset()
        return True
    if path == "/timer":
        respond(client, page_timer())
        return True
    if path == "/monitor":
        respond(client, page_monitor())
        return True
    if path == "/gpio":
        msg = gpio_act(body) if method == "POST" else ""
        respond(client, page_gpio(msg))
        return True
    if path == "/edit":
        if method == "POST":
            name = form_value(body, "name")
            act = form_value(body, "act")
            if not valid_name(name):
                respond(client, page_edit(name))
            elif act == "delete":
                if name in PROTECTED:
                    respond(client, page_edit(name, "That file is protected."))
                else:
                    try:
                        os.remove(name)
                    except Exception:
                        pass
                    respond(client, page_files())
            else:
                try:
                    with open(name, "w") as f:
                        f.write(form_value(body, "content").replace("\r\n", "\n")[:8000])
                    respond(client, page_edit(name, "Saved ✓"))
                except Exception as e:
                    respond(client, page_edit(name, "Save error: " + str(e)))
        else:
            name = ""
            for item in query.split("&"):
                p = item.split("=", 1)
                if len(p) == 2 and p[0] == "name":
                    name = decode(p[1])
            respond(client, page_edit(name))
        return True
    return False

def sync_time():
    global SYNCED
    try:
        import ntptime
        ntptime.settime()
        SYNCED = True
        print("Time synced from the internet.")
    except Exception as e:
        print("Time sync failed (clock stays blank):", e)


# -------------------- TERMINAL --------------------------------

CLIENT_IP = ""
term_ok_ip = ""      # IP address that unlocked the Python prompt
term_ns = {}
REBOOT = False

TERM_HELP = """Commands:
  help                 this list
  ls [dir]             list files
  cat FILE             show a file
  echo TEXT > FILE     write (>>  to append)
  cp A B | mv A B      copy / rename
  rm FILE              delete a file
  mkdir D | rmdir D    make / remove a folder
  pwd  df  free  uptime  ip  temp  date
  whoami id hostname uname neofetch ifconfig
  sudo CMD  (runs CMD; the board has one user)
  wifi [scan]          Wi-Fi status / networks
  gpio PIN [1|0|r]     set or read a pin
  reboot               restart the board
  login PIN            unlock the Python prompt
  py CODE              run Python (needs login)
Tip: Up/Down arrows recall history."""

def term_path_ok(name):
    return name not in PROTECTED

def run_cmd(line):
    global term_ok_ip, REBOOT
    out = []

    def p(*a):
        out.append(" ".join(str(x) for x in a))

    line = line.strip()
    if not line:
        return ""
    parts = line.split()
    c = parts[0]
    args = parts[1:]
    try:
        if c == "help":
            p(TERM_HELP)
        elif c == "ls":
            d = args[0] if args else "."
            for n in sorted(os.listdir(d)):
                full = n if d in (".", "/") else d.rstrip("/") + "/" + n
                st = os.stat(full)
                p(("d  " if st[0] & 0x4000 else "-  ") + n +
                  ("" if st[0] & 0x4000 else "  (%d B)" % st[6]))
        elif c == "cat":
            with open(args[0]) as f:
                t = f.read(4000)
                more = f.read(1)
            p(t + ("\n...(truncated)" if more else ""))
        elif c == "rm":
            if not term_path_ok(args[0]):
                p("protected file")
            else:
                os.remove(args[0])
        elif c == "mkdir":
            os.mkdir(args[0])
        elif c == "rmdir":
            os.rmdir(args[0])
        elif c == "mv":
            if not term_path_ok(args[0]) or not term_path_ok(args[1]):
                p("protected file")
            else:
                os.rename(args[0], args[1])
        elif c == "cp":
            if not term_path_ok(args[1]):
                p("protected file")
            else:
                with open(args[0], "rb") as a, open(args[1], "wb") as b:
                    while True:
                        chunk = a.read(512)
                        if not chunk:
                            break
                        b.write(chunk)
        elif c == "echo":
            rest = line[4:].strip()
            mode = None
            if ">>" in rest:
                text, _, name = rest.partition(">>")
                mode = "a"
            elif ">" in rest:
                text, _, name = rest.partition(">")
                mode = "w"
            if mode:
                name = name.strip()
                if not valid_name(name):
                    p("bad file name")
                elif not term_path_ok(name):
                    p("protected file")
                else:
                    with open(name, mode) as f:
                        f.write(text.strip() + "\n")
            else:
                p(rest)
        elif c == "sudo":
            return run_cmd(line[4:])
        elif c in ("ll", "dir"):
            return run_cmd("ls " + " ".join(args))
        elif c in ("ifconfig", "ip"):
            ifc = wlan.ifconfig()
            p("wlan0: inet %s  netmask %s" % (ifc[0], ifc[1]))
            p("        gateway %s  dns %s" % (ifc[2], ifc[3]))
            p("        ssid %s  signal %s dBm" % (SSID, wlan.status("rssi")))
        elif c in ("iwlist", "iwscan"):
            return run_cmd("wifi scan")
        elif c == "whoami":
            p("kali")
        elif c == "id":
            p("uid=1000(kali) gid=1000(kali) groups=1000(kali),27(sudo)")
        elif c == "hostname":
            p("esp32")
        elif c == "uname":
            u = os.uname()
            if args and args[0] == "-a":
                p("MicroPython esp32 %s %s %s" % (u[2], u[3], u[4]))
            else:
                p("MicroPython")
        elif c == "neofetch":
            gc.collect()
            u = os.uname()
            sec = time.ticks_ms() // 1000
            v = os.statvfs("/")
            p("kali@esp32")
            p("-----------")
            p("OS:      MicroPython %s" % u[2])
            p("Host:    %s" % u[4])
            p("Uptime:  %dh %dm" % (sec // 3600, sec % 3600 // 60))
            p("CPU:     ESP32-S3 @ %d MHz" % (machine.freq() // 1000000))
            p("Memory:  %d / %d KB" % (gc.mem_alloc() // 1024,
                                        (gc.mem_alloc() + gc.mem_free()) // 1024))
            p("Disk:    %d / %d KB" % ((v[2] - v[3]) * v[0] // 1024, v[2] * v[0] // 1024))
            p("Network: %s" % wlan.ifconfig()[0])
        elif c == "pwd":
            p(os.getcwd())
        elif c == "df":
            v = os.statvfs("/")
            p("total %d KB, free %d KB" % (v[0] * v[2] // 1024, v[0] * v[3] // 1024))
        elif c == "free":
            gc.collect()
            p("free %d KB, used %d KB" % (gc.mem_free() // 1024, gc.mem_alloc() // 1024))
        elif c == "uptime":
            sec = time.ticks_ms() // 1000
            p("%dh %dm %ds" % (sec // 3600, sec % 3600 // 60, sec % 60))
        elif c == "ip":
            p(" ".join(wlan.ifconfig()))
        elif c == "temp":
            t = temp_c()
            p("n/a" if t is None else "%s C" % t)
        elif c == "date":
            if SYNCED:
                n = time.localtime(time.time() + TZ_HOURS * 3600)
                p("%04d-%02d-%02d %02d:%02d:%02d" % n[:6])
            else:
                p("clock not synced")
        elif c == "wifi":
            if args and args[0] == "scan":
                nets = wlan.scan()
                nets.sort(key=lambda n: -n[3])
                for n in nets[:12]:
                    p("%4d dBm  ch%-2d  %s" % (n[3], n[2], n[0].decode()))
            else:
                p("connected" if wlan.isconnected() else "disconnected",
                  SSID, "rssi", wlan.status("rssi"))
        elif c == "gpio":
            pin = int(args[0])
            if pin not in GPIO_OK:
                p("GPIO %d not allowed" % pin)
            elif len(args) < 2 or args[1] == "r":
                p("GPIO %d = %d" % (pin, machine.Pin(pin, machine.Pin.IN).value()))
            else:
                v = 1 if args[1] == "1" else 0
                machine.Pin(pin, machine.Pin.OUT).value(v)
                gpio_state[pin] = v
                p("GPIO %d = %d" % (pin, v))
        elif c == "reboot":
            REBOOT = True
            p("Rebooting... reload the page in ~15 s.")
        elif c == "login":
            if not TERM_PIN:
                p("No PIN set. Add TERM_PIN = \"1234\" to wifi_config.py on the board.")
            elif args and args[0] == TERM_PIN:
                term_ok_ip = CLIENT_IP
                p("Python prompt unlocked for", CLIENT_IP, "(until reboot).")
            else:
                p("Wrong PIN.")
        elif c == "py":
            if not TERM_PIN or term_ok_ip != CLIENT_IP:
                p("Locked. Set TERM_PIN in wifi_config.py, then: login PIN")
            else:
                code = line[2:].strip()
                if not term_ns:
                    term_ns.update({"os": os, "gc": gc, "time": time, "machine": machine})
                term_ns["print"] = p
                try:
                    r = eval(code, term_ns)
                    if r is not None:
                        p(repr(r))
                except SyntaxError:
                    exec(code, term_ns)
        else:
            p("unknown command: " + c + "  (type help)")
    except IndexError:
        p("missing argument  (type help)")
    except Exception as e:
        p("error:", repr(e))
    return "\n".join(out)[:4000]

def page_kali():
    if not KALI_URL:
        content = """
<h1>Kali Linux</h1>
<div class="sub">A real Kali shell, running on a computer you own and shown on this screen.</div>
""" + card("Set it up (one time)", """
<p><b>1.</b> On your PC, install Kali in WSL (PowerShell):<br>
<code>wsl --install -d kali-linux</code></p>
<p><b>2.</b> In Kali, start a web terminal protected by a login:<br>
<code>sudo apt install ttyd<br>ttyd -p 7681 -c kali:YOUR_PASSWORD bash</code></p>
<p><b>3.</b> Find your PC's address (<code>ipconfig</code>, e.g. 192.168.1.10), then add to
<code>wifi_config.py</code> on the board:<br>
<code>KALI_URL = "http://192.168.1.10:7681"</code></p>
<p class="muted">Use it on your home Wi-Fi only. Never expose that port to the internet.</p>
""")
        return page("Kali", content)
    content = ("<h1>Kali Linux</h1>"
               '<a class="button full" target="_blank" href="' + esc(KALI_URL) + '">Open full screen</a>'
               '<iframe src="' + esc(KALI_URL) + '" style="width:100%;height:65vh;border:0;'
               'border-radius:16px;background:#000;margin-top:12px"></iframe>'
               '<p class="muted">Blank? Start <code>ttyd</code> on the Kali machine, then reload.</p>')
    return page("Kali", content)

def page_terminal():
    content = """
<h1>Terminal</h1><div class="sub">Kali-style shell on an ESP32. Type <b>help</b>.</div>
<style>
.kt{background:#0c0f14;color:#d6dbe3;border-radius:14px;padding:12px;margin-top:12px;
font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;line-height:1.35}
.kt pre{margin:0;white-space:pre-wrap;word-break:break-word;min-height:240px;max-height:58vh;overflow:auto;font:inherit}
.kb{color:#3b8eea}.ku{color:#5fb3ff;font-weight:700}.kw{color:#d6dbe3}
.kt input{flex:1;background:transparent;border:0;color:#fff;margin:0;padding:0;font:inherit;outline:none}
</style>
<div class="kt"><pre id="o"></pre>
<div><span class="kb">&#9484;&#9472;&#9472;(</span><span class="ku">kali&#12847;esp32</span><span class="kb">)-[</span><span class="kw">~</span><span class="kb">]</span></div>
<div style="display:flex;gap:6px"><span class="kb">&#9492;&#9472;</span><span class="ku">$</span>
<input id="i" autocomplete="off" autocapitalize="off" spellcheck="false"></div></div>
<script>
var o=document.getElementById('o'),i=document.getElementById('i'),h=[],hi=0;
function sp(c,t){var e=document.createElement('span');e.className=c;e.textContent=t;o.appendChild(e);}
function say(t){o.appendChild(document.createTextNode(t+'\\n'));o.scrollTop=o.scrollHeight;}
function prompt(c){sp('kb','\u250c\u2500\u2500(');sp('ku','kali\u322fesp32');sp('kb',')-[');sp('kw','~');sp('kb',']\\n');
 sp('kb','\u2514\u2500');sp('ku','$ ');say(c);}
say('  Kali-style shell on ESP32-S3 / MicroPython');
say('  Type help for commands, neofetch for system info.\\n');
i.addEventListener('keydown',function(e){
 if(e.key=='ArrowUp'){if(hi>0)hi--;i.value=h[hi]||'';e.preventDefault();}
 else if(e.key=='ArrowDown'){if(hi<h.length)hi++;i.value=h[hi]||'';e.preventDefault();}
 else if(e.key=='Enter'){var c=i.value;i.value='';if(!c.trim())return;
  h.push(c);hi=h.length;prompt(c);
  if(c.trim()=='clear'){o.textContent='';return;}
  fetch('/api/term',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
   body:'cmd='+encodeURIComponent(c)}).then(function(r){return r.text()})
  .then(function(t){if(t)say(t);}).catch(function(){say('(no answer: board busy or rebooting)');});}});
i.focus();
</script>
"""
    return page("Terminal", content)


# -------------------- MORE APPS -------------------------------

CONTACTS_FILE = "contacts.txt"

def contacts_load():
    items = []
    try:
        with open(CONTACTS_FILE) as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    n, _, ph = line.partition("|")
                    items.append((n, ph))
    except OSError:
        pass
    return items[:100]

def contacts_save(items):
    with open(CONTACTS_FILE, "w") as f:
        for n, ph in items:
            f.write(n + "|" + ph + "\n")

def clean(t, n):
    return t.replace("|", " ").replace("\n", " ").replace("\r", " ").strip()[:n]

def page_contacts():
    items = contacts_load()
    items.sort(key=lambda x: x[0].lower())
    rows = ""
    for i, (n, ph) in enumerate(items):
        rows += ('<form method="POST" action="/contacts" class="row"><span><b>' + esc(n) +
                 '</b><br><a href="tel:' + esc(ph) + '">' + esc(ph) + '</a></span>'
                 '<button name="act" value="d' + esc(n) + '|' + esc(ph) + '" class="danger">&times;</button></form>')
    content = "<h1>Contacts</h1><div class='sub'>%d saved.</div>" % len(items)
    content += card("Add contact", '<form method="POST" action="/contacts">'
                    '<input name="name" maxlength="40" placeholder="Name">'
                    '<input name="phone" maxlength="25" placeholder="Phone number" inputmode="tel">'
                    '<button class="full" name="act" value="add">Save</button></form>')
    content += card("Your contacts", rows or "<span class=muted>Nothing yet.</span>")
    return page("Contacts", content)

WX = {0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog",
      48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain",
      63: "Rain", 65: "Heavy rain", 80: "Showers", 81: "Showers", 82: "Heavy showers",
      95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"}

UA = {"User-Agent": "HungsOS-ESP32/1.0 (https://github.com/NaN-c-pixel/Phone)"}

def http_get(url, timeout=8):
    try:
        import requests
    except ImportError:
        import urequests as requests
    gc.collect()
    r = requests.get(url, headers=UA, timeout=timeout)
    try:
        return r.status_code, r.text
    finally:
        r.close()

def page_weather():
    content = "<h1>Weather</h1><div class='sub'>" + esc(WEATHER_NAME) + "</div>"
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
               "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
               "&daily=temperature_2m_max,temperature_2m_min&forecast_days=4&timezone=auto"
               % (WEATHER_LAT, WEATHER_LON))
        code, text = http_get(url)
        import json
        d = json.loads(text)
        c = d["current"]
        content += card("Now", '<div class="clock" style="font-size:54px;letter-spacing:-2px">%s&deg;C</div>'
                        '<div class="sub">%s</div>' % (c["temperature_2m"], WX.get(c["weather_code"], "Weather code %s" % c["weather_code"])))
        content += card("Details", row("Humidity", "%s %%" % c["relative_humidity_2m"]) +
                        row("Wind", "%s km/h" % c["wind_speed_10m"]))
        dl = d["daily"]
        rows = ""
        for i in range(len(dl["time"])):
            rows += row(dl["time"][i], "%s / %s C" % (round(dl["temperature_2m_max"][i]), round(dl["temperature_2m_min"][i])))
        content += card("Next days (high / low)", rows)
    except Exception as e:
        content += card("Could not load weather", "<span class=muted>Needs internet on the board. " +
                        esc(repr(e)) + "</span>")
    return page("Weather", content)

def host_ok(h):
    if not (0 < len(h) <= 100):
        return False
    for ch in h:
        if not (ch.isalpha() or ch.isdigit() or ch in ".-"):
            return False
    return True

def net_run(act, host, port):
    if act == "ip":
        code, text = http_get("https://api.ipify.org", 6)
        return "Public IP: " + text.strip()
    if not host_ok(host):
        return "Enter a host name like example.com"
    if act == "dns":
        return host + " -> " + socket.getaddrinfo(host, 80)[0][-1][0]
    if act == "tcp":
        try:
            port = int(port)
        except Exception:
            port = 80
        if not 1 <= port <= 65535:
            return "Port must be 1-65535"
        addr = socket.getaddrinfo(host, port)[0][-1]
        t0 = time.ticks_ms()
        sk = socket.socket()
        sk.settimeout(4)
        try:
            sk.connect(addr)
        finally:
            sk.close()
        return "%s:%d reachable in %d ms" % (host, port, time.ticks_diff(time.ticks_ms(), t0))
    return "Unknown action"

def page_nettools(result=""):
    content = "<h1>Net Tools</h1><div class='sub'>Check that your connection and a site are working.</div>"
    content += card("Check a host", '<form method="POST" action="/nettools">'
                    '<input name="host" placeholder="example.com" maxlength="100" autocapitalize="off">'
                    '<input name="port" placeholder="Port (default 80)" inputmode="numeric" maxlength="5">'
                    '<button name="act" value="dns">DNS lookup</button> '
                    '<button name="act" value="tcp" class="secondary">Port check</button> '
                    '<button name="act" value="ip" class="secondary">My public IP</button></form>')
    if result:
        content += card("Result", "<pre>" + esc(result) + "</pre>")
    return page("Net Tools", content)

CAL_HTML = """
<style>.cg{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;text-align:center;margin-top:12px}
.cd{padding:11px 0;border-radius:12px;background:#fff}.td{background:#087fff;color:#fff;font-weight:700}</style>
<h1 id="t">Calendar</h1>
<button onclick="mv(-1)" class="secondary">&lsaquo; Prev</button> <button onclick="mv(1)" class="secondary">Next &rsaquo;</button>
<div class="cg" id="g"></div>
<script>
var d=new Date(),y=d.getFullYear(),m=d.getMonth();
function mv(n){m+=n;if(m<0){m=11;y--;}if(m>11){m=0;y++;}draw();}
function draw(){var f=new Date(y,m,1).getDay(),n=new Date(y,m+1,0).getDate(),now=new Date(),h='';
 ['Su','Mo','Tu','We','Th','Fr','Sa'].forEach(function(x){h+='<div style="opacity:.5;font-size:12px">'+x+'</div>';});
 for(var i=0;i<f;i++)h+='<div></div>';
 for(var k=1;k<=n;k++){var t=(k==now.getDate()&&m==now.getMonth()&&y==now.getFullYear());
  h+='<div class="cd'+(t?' td':'')+'">'+k+'</div>';}
 document.getElementById('g').innerHTML=h;
 document.getElementById('t').textContent=new Date(y,m,1).toLocaleDateString([],{month:'long',year:'numeric'});}
draw();
</script>
"""

CONV_HTML = """
<h1>Converter</h1><div class="sub">Length, weight, data size and temperature.</div>
<div class="card"><select id="c" onchange="fill()" style="width:100%;padding:12px;border-radius:12px;border:1px solid #e4e4ec"></select>
<input id="v" type="number" value="1" oninput="go()" step="any">
<select id="a" onchange="go()" style="width:100%;padding:12px;border-radius:12px;border:1px solid #e4e4ec;margin:5px 0"></select>
<div class="calc-display" id="r" style="font-size:24px;min-height:60px"></div>
<select id="b" onchange="go()" style="width:100%;padding:12px;border-radius:12px;border:1px solid #e4e4ec;margin-top:5px"></select></div>
<script>
var U={Length:{mm:.001,cm:.01,m:1,km:1000,inch:.0254,foot:.3048,yard:.9144,mile:1609.344},
Weight:{g:.001,kg:1,ounce:.028349523,pound:.45359237,tonne:1000},
Data:{B:1,KB:1024,MB:1048576,GB:1073741824},Temperature:{'C':1,'F':1,'K':1}};
var c=document.getElementById('c'),a=document.getElementById('a'),b=document.getElementById('b'),v=document.getElementById('v'),r=document.getElementById('r');
Object.keys(U).forEach(function(k){c.add(new Option(k,k));});
function fill(){a.innerHTML='';b.innerHTML='';Object.keys(U[c.value]).forEach(function(k,i){a.add(new Option(k,k));b.add(new Option(k,k));});
 b.selectedIndex=Math.min(1,b.options.length-1);go();}
function go(){var x=parseFloat(v.value);if(isNaN(x)){r.textContent='';return;}var o;
 if(c.value=='Temperature'){var k=a.value=='C'?x+273.15:a.value=='F'?(x-32)*5/9+273.15:x;
  o=b.value=='C'?k-273.15:b.value=='F'?(k-273.15)*9/5+32:k;}
 else{o=x*U[c.value][a.value]/U[c.value][b.value];}
 r.textContent=(Math.round(o*1e6)/1e6)+' '+b.value;}
fill();
</script>
"""

SNAKE_HTML = """
<h1>Snake</h1><div class="sub" id="s">Score: 0. Use arrow keys, swipe, or the buttons.</div>
<canvas id="cv" width="300" height="300" style="width:100%;max-width:340px;background:#0b0f14;border-radius:16px;touch-action:none;display:block;margin:12px auto"></canvas>
<div style="text-align:center"><button onclick="dir(0,-1)">&uarr;</button><br>
<button onclick="dir(-1,0)">&larr;</button> <button onclick="start()" class="secondary">Start</button> <button onclick="dir(1,0)">&rarr;</button><br>
<button onclick="dir(0,1)">&darr;</button></div>
<script>
var cv=document.getElementById('cv'),x=cv.getContext('2d'),N=15,S=20,sn,dx,dy,f,sc,tm=null;
function start(){sn=[{x:7,y:7}];dx=1;dy=0;sc=0;food();clearInterval(tm);tm=setInterval(step,130);draw();}
function food(){f={x:Math.floor(Math.random()*N),y:Math.floor(Math.random()*N)};
 sn.forEach(function(p){if(p.x==f.x&&p.y==f.y)food();});}
function dir(a,b){if(a==-dx&&b==-dy&&sn&&sn.length>1)return;dx=a;dy=b;}
function step(){var h={x:sn[0].x+dx,y:sn[0].y+dy};
 if(h.x<0||h.y<0||h.x>=N||h.y>=N||sn.some(function(p){return p.x==h.x&&p.y==h.y;})){
  clearInterval(tm);document.getElementById('s').textContent='Game over! Score: '+sc;return;}
 sn.unshift(h);if(h.x==f.x&&h.y==f.y){sc++;document.getElementById('s').textContent='Score: '+sc;food();}else sn.pop();draw();}
function draw(){x.fillStyle='#0b0f14';x.fillRect(0,0,300,300);x.fillStyle='#ff5a6a';x.fillRect(f.x*S+2,f.y*S+2,S-4,S-4);
 x.fillStyle='#4cd964';sn.forEach(function(p,i){x.fillRect(p.x*S+1,p.y*S+1,S-2,S-2);});}
document.addEventListener('keydown',function(e){var k={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]}[e.key];
 if(k){dir(k[0],k[1]);e.preventDefault();}});
var t0=null;cv.addEventListener('touchstart',function(e){t0=e.touches[0];},{passive:true});
cv.addEventListener('touchend',function(e){if(!t0)return;var t=e.changedTouches[0],a=t.clientX-t0.clientX,b=t.clientY-t0.clientY;
 if(Math.abs(a)>Math.abs(b))dir(a>0?1:-1,0);else dir(0,b>0?1:-1);});
sn=[{x:7,y:7}];dx=1;dy=0;sc=0;food();draw();
</script>
"""

PASS_HTML = """
<h1>Passwords</h1><div class="sub">Made in your browser; nothing is sent or saved.</div>
<div class="card"><input id="o" readonly style="font-family:monospace;font-size:18px">
<p class="muted">Length: <b id="ln">16</b></p><input id="l" type="range" min="8" max="64" value="16" oninput="ln.textContent=this.value;gen()">
<p><label><input type="checkbox" id="u" checked onchange="gen()" style="width:auto"> A-Z</label> &nbsp;
<label><input type="checkbox" id="d" checked onchange="gen()" style="width:auto"> 0-9</label> &nbsp;
<label><input type="checkbox" id="s" checked onchange="gen()" style="width:auto"> !@#</label></p>
<button onclick="gen()">Generate</button> <button class="secondary" onclick="cp()">Copy</button></div>
<script>
function gen(){var set='abcdefghijkmnopqrstuvwxyz';if(u.checked)set+='ABCDEFGHJKLMNPQRSTUVWXYZ';
 if(d.checked)set+='23456789';if(s.checked)set+='!@#$%^&*-_=+?';
 var n=parseInt(l.value),a=new Uint32Array(n),o='';crypto.getRandomValues(a);
 for(var i=0;i<n;i++)o+=set[a[i]%set.length];document.getElementById('o').value=o;}
function cp(){var e=document.getElementById('o');e.select();try{document.execCommand('copy');}catch(x){}}
gen();
</script>
"""

DOPE_HTML = r"""
<h1>🧠 DOPE AI</h1>
<div class="sub">Neural Reaction Lab · a no-money learning experiment</div>
<div class="card" style="text-align:center">
  <div class="muted">AI REACTION</div>
  <div id="face" style="font-size:64px;margin:12px">🤔</div>
  <div id="reaction" style="font-size:19px;font-weight:750">Ready to learn?</div>
  <div id="detail" class="muted" style="margin-top:7px">Run a round to observe a random outcome.</div>
</div>
<div class="card">
  <div class="card-title">Next-outcome guess</div>
  <div class="row"><span class="muted">AI predicts</span><span id="guess" class="value">—</span></div>
  <div class="row"><span class="muted">Confidence</span><span id="confidence" class="value">No data yet</span></div>
  <div class="row"><span class="muted">Last outcome</span><span id="last" class="value">—</span></div>
  <button class="full" id="run">⚡ Run reaction</button>
  <button class="full secondary" id="reset" style="margin-top:9px">Reset experiment</button>
</div>
<div class="grid">
  <div class="card"><div class="muted">ROUNDS</div><div id="rounds" style="font-size:28px;font-weight:750">0</div></div>
  <div class="card"><div class="muted">CORRECT GUESSES</div><div id="correct" style="font-size:28px;font-weight:750">0</div></div>
  <div class="card"><div class="muted">ACCURACY</div><div id="accuracy" style="font-size:28px;font-weight:750">—</div></div>
</div>
<div class="card">
  <div class="card-title">🧪 How the tiny model learns</div>
  <p class="muted">It counts which emoji tends to follow the previous emoji, then guesses the most frequent next one. Each round updates its transition table. Outcomes are random, so the model may not predict better than chance.</p>
  <p class="muted">Educational simulation only: no bets, money, purchases, or prizes. This is a small adaptive rule, not a trained neural network.</p>
</div>
<div class="card">
  <div class="card-title">Recent lab log</div>
  <div id="log" class="muted">No rounds yet.</div>
</div>
<script>
(function(){
  var symbols = ["🍎","🌙","⭐","🪐"];
  var labels = {"🍎":"Apple","🌙":"Moon","⭐":"Star","🪐":"Planet"};
  var key = "dope_neural_reaction_lab_v1";
  var state = {rounds:0,correct:0,last:"",transitions:{},log:[]};
  try {
    var saved = localStorage.getItem(key);
    if(saved) {
      var parsed = JSON.parse(saved);
      if(parsed && parsed.transitions && Array.isArray(parsed.log)) state = parsed;
    }
  } catch(e) {}
  function save(){try{localStorage.setItem(key,JSON.stringify(state));}catch(e){}}
  function predict(from){
    if(!from || !state.transitions[from]) return {symbol:symbols[Math.floor(Math.random()*symbols.length)],confidence:25,known:false};
    var counts = state.transitions[from], best = symbols[0], total = 0, high = -1;
    for(var i=0;i<symbols.length;i++){
      var n = counts[symbols[i]] || 0; total += n;
      if(n > high){high=n;best=symbols[i];}
    }
    return {symbol:best,confidence:total ? Math.round(high/total*100) : 25,known:total>0};
  }
  function render(){
    document.getElementById("rounds").textContent=state.rounds;
    document.getElementById("correct").textContent=state.correct;
    document.getElementById("accuracy").textContent=state.rounds ? Math.round(state.correct/state.rounds*100)+"%" : "—";
    document.getElementById("last").textContent=state.last || "—";
    var html="";
    for(var i=0;i<state.log.length;i++) html += "<div style='padding:7px 0;border-bottom:1px solid #e7e7ed'>"+state.log[i]+"</div>";
    document.getElementById("log").innerHTML=html || "No rounds yet.";
    var p=predict(state.last);
    document.getElementById("guess").textContent=p.symbol+" "+labels[p.symbol];
    document.getElementById("confidence").textContent=p.known ? p.confidence+"% of observed transitions" : "Cold start";
  }
  document.getElementById("run").addEventListener("click",function(){
    var p=predict(state.last);
    var outcome=symbols[Math.floor(Math.random()*symbols.length)];
    var hit=p.symbol===outcome;
    state.rounds++;
    if(hit) state.correct++;
    var face=hit?"🤩":(state.rounds%3===0?"😮":"🤔");
    document.getElementById("face").textContent=face;
    document.getElementById("reaction").textContent=hit?"Prediction matched!":"Unexpected outcome!";
    document.getElementById("detail").textContent="AI guessed "+p.symbol+"; the random outcome was "+outcome+".";
    if(state.last){
      if(!state.transitions[state.last]) state.transitions[state.last]={};
      state.transitions[state.last][outcome]=(state.transitions[state.last][outcome]||0)+1;
    }
    state.last=outcome;
    state.log.unshift("#"+state.rounds+" · guess "+p.symbol+" · result "+outcome+" · "+(hit?"match":"miss"));
    if(state.log.length>8)state.log.length=8;
    save();render();
  });
  document.getElementById("reset").addEventListener("click",function(){
    state={rounds:0,correct:0,last:"",transitions:{},log:[]};
    document.getElementById("face").textContent="🤔";
    document.getElementById("reaction").textContent="Ready to learn?";
    document.getElementById("detail").textContent="Run a round to observe a random outcome.";
    save();render();
  });
  render();
})();
</script>
"""

GAMES_HTML = r"""
<h1>🎮 HungsOS Arcade</h1>
<div class="sub">Tiny games built for your phone · scores stay in this browser</div>
<div class="grid" style="grid-template-columns:repeat(3,minmax(0,1fr));gap:8px">
 <button onclick="showGame('snake')">🐍 AI Snake</button>
 <button onclick="showGame('2048')">🔢 2048</button>
 <button onclick="showGame('memory')">🧠 Memory</button>
</div>
<section id="snake" class="card">
 <h2>🐍 DOPE AI Snake</h2>
 <p class="muted">Autopilot uses safe-path heuristics and adapts its caution based on previous runs. It is a small game AI, not a neural network.</p>
 <div class="row"><span>Score <b id="ss">0</b></span><span>Best <b id="sb">0</b></span><span>Runs <b id="sr">0</b></span></div>
 <canvas id="scv" width="300" height="300" style="width:100%;max-width:340px;background:#0b0f14;border-radius:14px;touch-action:none;display:block;margin:12px auto"></canvas>
 <div class="row"><button onclick="snakeStart(true)">▶ Start AI</button><button class="secondary" onclick="snakeStart(false)">Manual</button><button class="secondary" onclick="snakeStop()">Stop</button></div>
 <div class="row" style="justify-content:center;gap:6px"><button onclick="snakeDir(0,-1)">⬆️</button></div>
 <div class="row" style="justify-content:center;gap:6px"><button onclick="snakeDir(-1,0)">⬅️</button><button onclick="snakeDir(0,1)">⬇️</button><button onclick="snakeDir(1,0)">➡️</button></div>
 <p id="smsg" class="muted">Press Start AI to watch the snake play.</p>
</section>
<section id="2048" class="card" style="display:none">
 <h2>🔢 2048</h2><p class="muted">Join matching tiles to reach 2048. Use arrow keys, swipe, or buttons.</p>
 <div class="row"><b>Score: <span id="ts">0</span></b><button onclick="tileStart()">New game</button></div>
 <div id="tiles" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:12px 0"></div>
 <div class="row" style="justify-content:center"><button onclick="tileMove('up')">⬆️</button></div>
 <div class="row" style="justify-content:center"><button onclick="tileMove('left')">⬅️</button><button onclick="tileMove('down')">⬇️</button><button onclick="tileMove('right')">➡️</button></div>
 <p id="tmsg" class="muted">Make 2048!</p>
</section>
<section id="memory" class="card" style="display:none">
 <h2>🧠 Memory Match</h2><p class="muted">Find all matching pairs with as few moves as possible.</p>
 <div class="row"><span>Moves <b id="mmoves">0</b></span><span>Pairs <b id="mpairs">0/8</b></span><button onclick="memoryStart()">Restart</button></div>
 <div id="memgrid" style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:12px"></div>
 <p id="mmsg" class="muted">Tap two cards to find a pair.</p>
</section>
<script>
(function(){
 var sections=['snake','2048','memory'];
 window.showGame=function(id){sections.forEach(function(x){document.getElementById(x).style.display=x===id?'block':'none';});};
 var cv=document.getElementById('scv'),ctx=cv.getContext('2d'),N=15,C=20,snake=[],food={x:10,y:7},dx=1,dy=0,st=null,ai=true,score=0,runs=0,best=0,caution=0;
 try{var z=JSON.parse(localStorage.getItem('hungos_arcade_snake')||'{}');best=z.best||0;runs=z.runs||0;caution=z.caution||0;}catch(e){}
 function saveSnake(){try{localStorage.setItem('hungos_arcade_snake',JSON.stringify({best:best,runs:runs,caution:caution}));}catch(e){}}
 function foodNew(){var tries=0;do{food={x:Math.floor(Math.random()*N),y:Math.floor(Math.random()*N)};tries++;}while(tries<500&&snake.some(function(p){return p.x===food.x&&p.y===food.y;}));}
 function drawSnake(){ctx.fillStyle='#0b0f14';ctx.fillRect(0,0,300,300);ctx.fillStyle='#ff5a6a';ctx.fillRect(food.x*C+2,food.y*C+2,C-4,C-4);snake.forEach(function(p,i){ctx.fillStyle=i?'#27ae60':'#a3ff68';ctx.fillRect(p.x*C+1,p.y*C+1,C-2,C-2);});}
 function snakeStats(){document.getElementById('ss').textContent=score;document.getElementById('sb').textContent=best;document.getElementById('sr').textContent=runs;}
 window.snakeStop=function(){clearInterval(st);st=null;};
 window.snakeStart=function(useAI){snakeStop();ai=useAI;snake=[{x:7,y:7},{x:6,y:7},{x:5,y:7}];dx=1;dy=0;score=0;foodNew();snakeStats();document.getElementById('smsg').textContent=ai?'AI autopilot is running…':'Manual mode: use arrows or swipe.';st=setInterval(snakeStep,ai?115:145);drawSnake();};
 window.snakeDir=function(a,b){if(a===-dx&&b===-dy&&snake.length>1)return;dx=a;dy=b;};
 function safe(x,y,body){return x>=0&&y>=0&&x<N&&y<N&&!body.some(function(p,i){return i<body.length-1&&p.x===x&&p.y===y;});}
 function aiMove(){
   var opts=[[1,0],[-1,0],[0,1],[0,-1]],bestMove=null,bestVal=-1e9;
   opts.forEach(function(d){if(d[0]===-dx&&d[1]===-dy&&snake.length>1)return;var h={x:snake[0].x+d[0],y:snake[0].y+d[1]},body=snake.slice();if(h.x===food.x&&h.y===food.y){}else body.pop();if(!safe(h.x,h.y,body))return;
     var dist=Math.abs(h.x-food.x)+Math.abs(h.y-food.y),edge=Math.min(h.x,h.y,N-1-h.x,N-1-h.y);
     var area=0;[[1,0],[-1,0],[0,1],[0,-1]].forEach(function(q){if(safe(h.x+q[0],h.y+q[1],body))area++;});
     var val=-dist+(area*1.5)+(edge*caution*0.25)+(Math.random()*0.12);
     if(val>bestVal){bestVal=val;bestMove=d;}
   });
   if(bestMove){dx=bestMove[0];dy=bestMove[1];}else{var fallback=opts.find(function(d){var h={x:snake[0].x+d[0],y:snake[0].y+d[1]},b=snake.slice();b.pop();return safe(h.x,h.y,b);});if(fallback){dx=fallback[0];dy=fallback[1];}}
 }
 function snakeStep(){if(ai)aiMove();var h={x:snake[0].x+dx,y:snake[0].y+dy},grow=h.x===food.x&&h.y===food.y,body=snake.slice();if(!grow)body.pop();
   if(!safe(h.x,h.y,body)){snakeStop();runs++;if(score>best)best=score;caution=Math.min(8,caution+0.5);saveSnake();snakeStats();document.getElementById('smsg').textContent='Game over at '+score+'. AI caution adjusted for the next run.';return;}
   snake.unshift(h);if(grow){score++;if(score>best)best=score;foodNew();}else snake.pop();snakeStats();drawSnake();}
 var touch=null;cv.addEventListener('touchstart',function(e){touch=e.touches[0];},{passive:true});cv.addEventListener('touchend',function(e){if(!touch)return;var t=e.changedTouches[0],a=t.clientX-touch.clientX,b=t.clientY-touch.clientY;if(Math.abs(a)>Math.abs(b))snakeDir(a>0?1:-1,0);else snakeDir(0,b>0?1:-1);touch=null;});
 document.addEventListener('keydown',function(e){var d={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]}[e.key];if(d&&document.getElementById('snake').style.display!=='none'){snakeDir(d[0],d[1]);e.preventDefault();}else if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].indexOf(e.key)>=0&&document.getElementById('2048').style.display!=='none'){tileMove(({ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right'})[e.key]);e.preventDefault();}});
 snake=[{x:7,y:7},{x:6,y:7}];drawSnake();snakeStats();
 var board=[],tscore=0;
 window.tileStart=function(){board=Array(16).fill(0);tscore=0;tileSpawn();tileSpawn();tileRender();document.getElementById('tmsg').textContent='Make 2048!';};
 function tileSpawn(){var e=[];board.forEach(function(v,i){if(!v)e.push(i);});if(e.length)board[e[Math.floor(Math.random()*e.length)]]=Math.random()<0.9?2:4;}
 function tileRender(){document.getElementById('ts').textContent=tscore;var h='';board.forEach(function(v){var bg=v===0?'#d9d4cc':v===2?'#eee4da':v===4?'#ede0c8':v===8?'#f2b179':v===16?'#f59563':v===32?'#f67c5f':'#edcf72';h+='<div style="height:56px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:'+bg+';color:#292521;font-weight:800;font-size:20px">'+(v||'')+'</div>';});document.getElementById('tiles').innerHTML=h;}
 window.tileMove=function(dir){var old=board.join(','),lines=[];for(var n=0;n<4;n++){var ids=[];for(var k=0;k<4;k++)ids.push(dir==='left'?n*4+k:dir==='right'?n*4+(3-k):dir==='up'?k*4+n:(3-k)*4+n);lines.push(ids);}lines.forEach(function(ids){var a=ids.map(function(i){return board[i];}).filter(Boolean),out=[];for(var j=0;j<a.length;j++){if(a[j]===a[j+1]){out.push(a[j]*2);tscore+=a[j]*2;j++;}else out.push(a[j]);}while(out.length<4)out.push(0);ids.forEach(function(id,j){board[id]=out[j];});});if(old!==board.join(',')){tileSpawn();tileRender();if(board.indexOf(2048)>=0)document.getElementById('tmsg').textContent='🎉 You reached 2048!';else if(!board.some(function(v){return v===0;})&&!['left','right','up','down'].some(function(d){return canMove(d);}))document.getElementById('tmsg').textContent='No moves left — start a new game.';}};
 function canMove(d){var old=board.join(','),copy=board.slice();tileMoveSim(d);var changed=old!==board.join(',');board=copy;return changed;}
 function tileMoveSim(d){for(var n=0;n<4;n++){var ids=[];for(var k=0;k<4;k++)ids.push(d==='left'?n*4+k:d==='right'?n*4+(3-k):d==='up'?k*4+n:(3-k)*4+n);var a=ids.map(function(i){return board[i];}).filter(Boolean),o=[];for(var j=0;j<a.length;j++){if(a[j]===a[j+1]){o.push(a[j]*2);j++;}else o.push(a[j]);}while(o.length<4)o.push(0);ids.forEach(function(id,j){board[id]=o[j];});}}
 var cards=[],first=-1,lock=false,mmoves=0,mpairs=0;
 window.memoryStart=function(){var icons=['🍎','🌙','⭐','🐸','🎈','🍀','🚀','🎵'];cards=icons.concat(icons).sort(function(){return Math.random()-0.5;}).map(function(v){return {v:v,open:false,done:false};});first=-1;lock=false;mmoves=0;mpairs=0;memoryRender();document.getElementById('mmsg').textContent='Tap two cards to find a pair.';};
 function memoryRender(){document.getElementById('mmoves').textContent=mmoves;document.getElementById('mpairs').textContent=mpairs+'/8';document.getElementById('memgrid').innerHTML=cards.map(function(c,i){return '<button style="height:54px;font-size:24px;padding:4px" '+(c.done?'disabled':'')+' onclick="memoryFlip('+i+')">'+(c.open||c.done?c.v:'❔')+'</button>';}).join('');}
 window.memoryFlip=function(i){if(lock||cards[i].done||cards[i].open)return;cards[i].open=true;if(first<0){first=i;memoryRender();return;}mmoves++;var a=first;first=-1;if(cards[a].v===cards[i].v){cards[a].done=true;cards[i].done=true;mpairs++;memoryRender();if(mpairs===8)document.getElementById('mmsg').textContent='🎉 All pairs found in '+mmoves+' moves!';}else{lock=true;memoryRender();setTimeout(function(){cards[a].open=false;cards[i].open=false;lock=false;memoryRender();},650);}};
 window.addEventListener('pagehide',function(){snakeStop();});tileStart();memoryStart();
})();
</script>
"""

WORLD_HTML = """
<h1>World clock</h1><div class="sub">Times around the world.</div><div id="w"></div>
<script>
var Z=[['Ho Chi Minh','Asia/Ho_Chi_Minh'],['Tokyo','Asia/Tokyo'],['Sydney','Australia/Sydney'],
['London','Europe/London'],['Paris','Europe/Paris'],['New York','America/New_York'],['Los Angeles','America/Los_Angeles']];
function tick(){var h='';Z.forEach(function(z){var n=new Date();
 h+='<div class="card row"><span><b>'+z[0]+'</b><br><span class="muted">'+
 n.toLocaleDateString([],{timeZone:z[1],weekday:'short',day:'numeric',month:'short'})+'</span></span>'+
 '<span style="font-size:26px;font-weight:300">'+n.toLocaleTimeString([],{timeZone:z[1],hour:'2-digit',minute:'2-digit'})+'</span></div>';});
 document.getElementById('w').innerHTML=h;}
tick();setInterval(tick,5000);
</script>
"""

JS_APPS = {"/games": ("HungsOS Arcade", GAMES_HTML),
           "/dope": ("DOPE AI — Neural Reaction Lab", DOPE_HTML),
           "/calendar": ("Calendar", CAL_HTML), "/convert": ("Converter", CONV_HTML),
           "/snake": ("Snake", SNAKE_HTML), "/passgen": ("Passwords", PASS_HTML),
           "/world": ("World clock", WORLD_HTML)}

def route_more(client, method, path, body):
    if path == "/bank":
        respond(client, page_bank())
        return True
    if path == "/assistant":
        respond(client, page_assistant())
        return True
    if path == "/api/ask":
        if method != "POST":
            respond(client, "POST only", "405 Method Not Allowed", "text/plain")
        else:
            try:
                ans = assist(form_value(body, "q"))
            except Exception as e:
                ans = "Oops: " + repr(e)
            respond(client, ans, content_type="text/plain; charset=utf-8")
        return True
    if path in JS_APPS:
        title, html = JS_APPS[path]
        respond(client, page(title, html))
        return True
    if path == "/contacts":
        if method == "POST":
            act = form_value(body, "act")
            items = contacts_load()
            if act == "add":
                n = clean(form_value(body, "name"), 40)
                ph = clean(form_value(body, "phone"), 25)
                if n and ph and len(items) < 100:
                    items.append((n, ph))
                    contacts_save(items)
            elif act[:1] == "d":
                n, _, ph = act[1:].partition("|")
                items = [x for x in items if not (x[0] == n and x[1] == ph)]
                contacts_save(items)
        respond(client, page_contacts())
        return True
    if path == "/weather":
        respond(client, page_weather())
        return True
    if path == "/nettools":
        result = ""
        if method == "POST":
            try:
                result = net_run(form_value(body, "act"), form_value(body, "host").strip(),
                                 form_value(body, "port").strip())
            except Exception as e:
                result = "Error: " + repr(e)
        respond(client, page_nettools(result))
        return True
    return False




BANK_URL = "https://liveboard.cafef.vn/"

def page_bank():
    content = ("<h1>Bank</h1><div class='sub'>Live stock board from CafeF (loaded by your browser, not the board).</div>"
               '<a class="button full" target="_blank" href="' + BANK_URL + '">Open full screen</a>'
               '<iframe src="' + BANK_URL + '" style="width:100%;height:72vh;border:0;border-radius:16px;'
               'background:#fff;margin-top:12px"></iframe>'
               '<p class="muted">If the board above stays blank, the site does not allow embedding. '
               'Use <b>Open full screen</b>.</p>')
    return page("Bank", content)

# -------------------- WEB LOOKUPS (direct APIs, no LLM) -------

web_cache = {}

def urlenc(txt):
    out = ""
    for b in txt.encode():
        c = chr(b)
        if (b < 128 and (c.isalpha() or c.isdigit())) or c in "-_.~":
            out += c
        else:
            out += "%%%02X" % b
    return out

def strip_tags(t):
    out = ""
    skip = False
    for ch in t:
        if ch == "<":
            skip = True
        elif ch == ">":
            skip = False
        elif not skip:
            out += ch
    return out.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")

def web_json(url):
    import json
    code, text = http_get(url)
    if code != 200:
        raise OSError("HTTP %d" % code)
    return json.loads(text)

def clip(t, n=650):
    t = t.strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "..."

def wiki_lookup(q):
    d = web_json("https://%s.wikipedia.org/w/api.php?action=query&format=json&generator=search"
                 "&gsrsearch=%s&gsrlimit=1&prop=extracts&exintro=1&explaintext=1&exsentences=4&redirects=1"
                 % (WIKI_LANG, urlenc(q)))
    pages = d.get("query", {}).get("pages")
    if not pages:
        return None
    pg = list(pages.values())[0]
    ext = pg.get("extract", "")
    if not ext:
        return None
    title = pg.get("title", q)
    return "%s\n%s\n(Source: %s.wikipedia.org/wiki/%s)" % (title, clip(ext), WIKI_LANG, urlenc(title.replace(" ", "_")))

def search_lookup(q):
    d = web_json("https://api.duckduckgo.com/?q=%s&format=json&no_html=1&skip_disambig=1" % urlenc(q))
    ans = d.get("Answer") or d.get("AbstractText") or d.get("Definition")
    if ans:
        src = d.get("AbstractURL") or d.get("DefinitionURL") or "duckduckgo.com"
        return "%s\n(Source: %s)" % (clip(str(ans)), src)
    w = web_json("https://%s.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=%s&srlimit=3"
                 % (WIKI_LANG, urlenc(q)))
    hits = w.get("query", {}).get("search", [])
    if not hits:
        return None
    lines = []
    for h in hits:
        lines.append("- %s: %s" % (h["title"], clip(strip_tags(h.get("snippet", "")), 140)))
    return "Top results (Wikipedia):\n" + "\n".join(lines) + "\nAsk: wiki <title> for details."

def define_lookup(word):
    import json
    code, text = http_get("https://api.dictionaryapi.dev/v2/entries/en/" + urlenc(word.split(" ")[0]))
    if code != 200:
        return None
    e = json.loads(text)[0]
    m = e["meanings"][0]
    return "%s (%s): %s" % (e["word"], m["partOfSpeech"], m["definitions"][0]["definition"])

def weather_city(city):
    g = web_json("https://geocoding-api.open-meteo.com/v1/search?name=%s&count=1" % urlenc(city))
    res = g.get("results")
    if not res:
        return None
    r = res[0]
    return weather_text(r["latitude"], r["longitude"], "%s, %s" % (r["name"], r.get("country", "")))

def weather_text(lat, lon, name):
    d = web_json("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
                 "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                 "&daily=temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto" % (lat, lon))
    c = d["current"]
    dl = d["daily"]
    return "%s: %s C, %s. Humidity %s%%, wind %s km/h. Today %s / %s C." % (
        name, c["temperature_2m"], WX.get(c["weather_code"], "weather code %s" % c["weather_code"]),
        c["relative_humidity_2m"], c["wind_speed_10m"],
        round(dl["temperature_2m_max"][0]), round(dl["temperature_2m_min"][0]))

def currency_lookup(t):
    amt = 1.0
    codes = []
    for w in t.replace(",", "").split():
        try:
            amt = float(w)
            continue
        except ValueError:
            pass
        if len(w) == 3 and w.isalpha() and w not in ("how", "much", "the", "for"):
            codes.append(w.upper())
    if len(codes) < 2:
        return None
    d = web_json("https://open.er-api.com/v6/latest/" + codes[0])
    rate = d["rates"].get(codes[1])
    if rate is None:
        return "I don't know the currency " + codes[1]
    return "%s %s = %s %s\n(Rates: open.er-api.com)" % (
        ("%g" % amt), codes[0], ("{:,.2f}".format(amt * rate)), codes[1])


COINS = {"bitcoin": "bitcoin", "btc": "bitcoin", "ethereum": "ethereum", "eth": "ethereum",
         "bnb": "binancecoin", "doge": "dogecoin", "dogecoin": "dogecoin", "sol": "solana",
         "solana": "solana", "xrp": "ripple", "ada": "cardano", "ton": "the-open-network"}

def unent(t):
    return (t.replace("<![CDATA[", "").replace("]]>", "").replace("&amp;", "&").replace("&quot;", '"')
            .replace("&#39;", "'").replace("&apos;", "'").replace("&lt;", "<").replace("&gt;", ">").strip())

def rss_titles(url, n=6):
    code, text = http_get(url)
    if code != 200:
        raise OSError("HTTP %d" % code)
    out = []
    pos = 0
    while len(out) < n:
        i = text.find("<item>", pos)
        if i < 0:
            break
        j = text.find("<title>", i)
        k = text.find("</title>", j)
        if j < 0 or k < 0:
            break
        out.append(unent(text[j + 7:k]))
        pos = k
    return out

def news_lookup(kind):
    if kind == "world":
        url, src = "https://feeds.bbci.co.uk/news/rss.xml", "BBC News"
    else:
        url, src = "https://vnexpress.net/rss/tin-moi-nhat.rss", "VnExpress"
    titles = rss_titles(url)
    if not titles:
        return None
    return "Latest from %s:\n" % src + "\n".join("- " + t for t in titles)

def quote_lookup(_):
    d = web_json("https://zenquotes.io/api/random")
    return '"%s" - %s\n(Quotes by ZenQuotes.io)' % (d[0]["q"], d[0]["a"])

def price_lookup(coin):
    cid = COINS.get(coin.lower().strip())
    if not cid:
        return "I know these coins: " + ", ".join(sorted(COINS))
    d = web_json("https://api.coingecko.com/api/v3/simple/price?ids=%s&vs_currencies=usd,vnd"
                 "&include_24hr_change=true" % cid)[cid]
    return "%s: $%s (%s VND), 24h %+.1f%%\n(Data: CoinGecko)" % (
        cid, "{:,.2f}".format(d["usd"]), "{:,.0f}".format(d["vnd"]), d.get("usd_24h_change", 0))

def aqi_text(lat, lon, name):
    d = web_json("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=%s&longitude=%s"
                 "&current=us_aqi,pm2_5" % (lat, lon))["current"]
    a = d["us_aqi"]
    lvl = ("Good" if a <= 50 else "Moderate" if a <= 100 else "Unhealthy for sensitive groups" if a <= 150
           else "Unhealthy" if a <= 200 else "Very unhealthy" if a <= 300 else "Hazardous")
    return "%s: AQI %s (%s), PM2.5 %s ug/m3\n(Data: Open-Meteo)" % (name, a, lvl, d["pm2_5"])

def aqi_lookup(city):
    if not city:
        return aqi_text(WEATHER_LAT, WEATHER_LON, WEATHER_NAME)
    g = web_json("https://geocoding-api.open-meteo.com/v1/search?name=%s&count=1" % urlenc(city))
    res = g.get("results")
    if not res:
        return None
    r = res[0]
    return aqi_text(r["latitude"], r["longitude"], "%s, %s" % (r["name"], r.get("country", "")))

def web_answer(kind, arg):
    key = kind + ":" + arg.lower()
    if key in web_cache:
        return web_cache[key]
    try:
        fn = {"wiki": wiki_lookup, "search": search_lookup, "define": define_lookup,
              "city": weather_city, "money": currency_lookup, "news": news_lookup,
              "quote": quote_lookup, "price": price_lookup, "aqi": aqi_lookup}[kind]
        out = fn(arg)
    except OSError as e:
        if str(e).startswith("HTTP"):
            return "That web service answered with an error (%s). Try again later." % e
        return "I can't reach the internet right now (%s)." % e
    except Exception as e:
        return "The web lookup failed: " + repr(e)
    if out is None:
        return "I couldn't find anything for: " + arg
    if len(web_cache) >= 8:
        web_cache.pop(list(web_cache)[0])
    web_cache[key] = out
    gc.collect()
    return out

def looks_money(t):
    if t.startswith(("convert ", "exchange ")):
        return True
    if not any(ch.isdigit() for ch in t) or not (" to " in t or " in " in t):
        return False
    skip = ("how", "the", "for", "and", "are", "you", "can", "its", "not", "min", "sec", "day")
    n = 0
    for w in t.split():
        if len(w) == 3 and w.isalpha() and w not in skip:
            n += 1
    return n >= 2

def web_intent(t, raw):
    """Return an answer if t is a web request, else None."""
    tt = t.strip("? !.")
    if tt in ("news", "headlines", "latest news", "tin tuc", "news vietnam"):
        return web_answer("news", "vn")
    if tt in ("world news", "news world", "bbc", "bbc news"):
        return web_answer("news", "world")
    if tt in ("quote", "quote of the day", "inspire me", "motivation"):
        return web_answer("quote", "x")
    if tt in ("air quality", "aqi", "pollution", "how is the air"):
        return web_answer("aqi", "")
    for pre in ("air quality in ", "aqi in ", "aqi "):
        if t.startswith(pre):
            return web_answer("aqi", raw[len(pre):].strip())
    for pre in ("price of ", "price ", "how much is "):
        if t.startswith(pre) and raw[len(pre):].strip().lower() in COINS:
            return web_answer("price", raw[len(pre):].strip())
    parts = tt.split()
    if len(parts) == 2 and parts[1] in ("price", "usd") and parts[0] in COINS:
        return web_answer("price", parts[0])
    if tt in COINS:
        return web_answer("price", tt)
    for pre in ("wikipedia ", "wiki "):
        if t.startswith(pre):
            return web_answer("wiki", raw[len(pre):].strip())
    for pre in ("search for ", "search ", "google ", "look up ", "lookup ", "find out "):
        if t.startswith(pre):
            return web_answer("search", raw[len(pre):].strip())
    for pre in ("define ", "meaning of ", "definition of "):
        if t.startswith(pre):
            return web_answer("define", raw[len(pre):].strip())
    if t.startswith(("weather in ", "weather at ", "weather for ")):
        return web_answer("city", raw.split(" ", 2)[2].strip())
    if t.strip("? ") == "weather" or t.startswith(("what's the weather", "whats the weather", "how's the weather")):
        try:
            return weather_text(WEATHER_LAT, WEATHER_LON, WEATHER_NAME)
        except OSError as e:
            return "I can't reach the internet right now (%s)." % e
        except Exception as e:
            return "The weather lookup failed: " + repr(e)
    if looks_money(t):
        r = web_answer("money", t)
        if not r.startswith("I couldn't find"):
            return r
    if t.startswith(("who is ", "who was ", "what is ", "what are ", "what was ", "tell me about ",
                     "when did ", "where is ", "why is ", "how does ", "how do ")):
        subj = t
        for pre in ("tell me about ", "who is ", "who was ", "what is ", "what are ", "what was ", "where is "):
            if subj.startswith(pre):
                subj = raw[len(pre):]
                break
        else:
            subj = raw
        return web_answer("wiki", subj.strip(" ?"))
    return None

# -------------------- ASSISTANT (tiny, offline) ---------------

OPEN_MAP = (("note", "/notes", "Notes"), ("task", "/todo", "Tasks"), ("todo", "/todo", "Tasks"),
            ("file", "/files", "Files"), ("timer", "/timer", "Timer"), ("stopwatch", "/timer", "Timer"),
            ("monitor", "/monitor", "Monitor"), ("gpio", "/gpio", "GPIO"), ("terminal", "/terminal", "Terminal"),
            ("kali", "/kali", "Kali"), ("weather", "/weather", "Weather"), ("contact", "/contacts", "Contacts"),
            ("calendar", "/calendar", "Calendar"), ("convert", "/convert", "Converter"),
            ("snake", "/snake", "Snake"), ("game", "/snake", "Snake"), ("password", "/passgen", "Passwords"),
            ("world", "/world", "World clock"), ("net", "/nettools", "Net Tools"),
            ("wifi", "/wifi", "Wi-Fi"), ("bluetooth", "/bluetooth", "Bluetooth"),
            ("calculator", "/calc", "Calculator"), ("setting", "/system", "Settings"))

JOKES = ("Why do programmers prefer dark mode? Because light attracts bugs.",
         "There are 10 kinds of people: those who know binary and those who don't.",
         "A microcontroller walks into a bar. The bartender says: you look tense. It says: I just need a reset.",
         "I would tell you a UDP joke, but you might not get it.")

def _has(t, *words):
    for w in words:
        if w in t:
            return True
    return False

def assist(text):
    import random
    t = text.lower().strip()
    if not t:
        return ""
    gc.collect()
    # math: "what is 12*7", "calculate (3+4)/2"
    expr = t
    for w in ("what is", "what's", "whats", "calculate", "calc", "compute", "="):
        expr = expr.replace(w, " ")
    expr = expr.replace("x", "*").replace("times", "*").replace("plus", "+").replace("minus", "-")
    expr = expr.replace("divided by", "/").replace("^", "**").strip().rstrip("?")
    if expr and all(ch in "0123456789+-*/(). %" for ch in expr) and any(ch.isdigit() for ch in expr):
        try:
            r = eval(expr)
            return "%s = %s" % (expr.strip(), r)
        except Exception:
            return "I couldn't work that out."
    if t.startswith(("open ", "go to ", "launch ", "start ", "show me ")) or t.startswith("open"):
        for key, link, name in OPEN_MAP:
            if key in t:
                return "@%s|Opening %s" % (link, name)
        return "I don't know that app. Try: open notes, open weather, open terminal..."
    if t.startswith(("add task", "task ", "todo ", "remind me to ", "add todo")):
        for pre in ("add task", "add todo", "remind me to", "task", "todo"):
            if t.startswith(pre):
                item = text.strip()[len(pre):].strip(" :-")
                break
        item = item[:100]
        if not item:
            return "What should the task say? Example: add task buy milk"
        items = todo_load()
        if len(items) >= 50:
            return "Your task list is full (50)."
        items.append([False, item])
        todo_save(items)
        return "Added task: " + item
    if t.startswith(("wiki", "search", "google", "look up", "lookup", "find out", "define", "meaning of",
                     "definition of", "weather", "what's the weather", "whats the weather", "how's the weather",
                     "convert", "exchange", "news", "headlines", "world news", "bbc", "quote", "inspire",
                     "air quality", "aqi", "pollution", "how is the air", "price", "bitcoin", "btc", "eth",
                     "ethereum", "doge", "sol", "bnb", "xrp", "ada", "ton", "tin tuc", "motivation")) or (" to " in t and any(ch.isdigit() for ch in t) and len(t) < 40):
        r = web_intent(t, text.strip())
        if r is not None:
            return r
    if _has(t, "my tasks", "how many tasks", "list tasks", "what do i have to do"):
        items = todo_load()
        left = [x[1] for x in items if not x[0]]
        if not left:
            return "No open tasks."
        return "%d open: %s" % (len(left), "; ".join(left[:8]))
    if t.startswith(("note ", "write down ")):
        item = text.strip().split(" ", 1)[1].strip()[:200]
        with open("assistant_notes.txt", "a") as f:
            f.write(item + "\n")
        return "Saved to assistant_notes.txt"
    if _has(t, "uptime", "how long"):
        sec = time.ticks_ms() // 1000
        return "Up for %dh %dm %ds" % (sec // 3600, sec % 3600 // 60, sec % 60)
    if _has(t, "time", "what day", "date", "today"):
        if SYNCED:
            n = time.localtime(time.time() + TZ_HOURS * 3600)
            days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
            return "%s %04d-%02d-%02d, %02d:%02d" % (days[n[6]], n[0], n[1], n[2], n[3], n[4])
        return "My clock isn't synced yet (no internet at boot)."
    if _has(t, "ram", "memory"):
        return "%d KB free, %d KB used" % (gc.mem_free() // 1024, gc.mem_alloc() // 1024)
    if _has(t, "temperature", "how hot", "temp"):
        v = temp_c()
        return "Chip temperature: " + ("unknown" if v is None else "%s C" % v)
    if _has(t, "ip address", "my ip", "your ip"):
        return "I'm at " + wlan.ifconfig()[0]
    if _has(t, "wifi", "signal", "network"):
        return "%s, signal %s dBm" % (SSID, wlan.status("rssi"))
    if _has(t, "storage", "disk", "space", "flash"):
        v = os.statvfs("/")
        return "%d MB free of %d MB" % (v[0] * v[3] // 1048576, v[0] * v[2] // 1048576)
    if _has(t, "coin", "flip"):
        return random.choice(("Heads", "Tails"))
    if _has(t, "dice", "roll"):
        return "You rolled a %d" % random.randint(1, 6)
    if _has(t, "random number", "pick a number"):
        return "Your number: %d" % random.randint(1, 100)
    if _has(t, "joke", "funny"):
        return random.choice(JOKES)
    if _has(t, "thank"):
        return "Any time!"
    if _has(t, "who are you", "your name", "what are you"):
        return "I'm a tiny offline assistant on an ESP32-S3. No cloud, no AI model, just a few rules."
    if t in ("hi", "hello", "hey", "yo") or t.startswith(("hi ", "hello", "hey ")):
        return "Hi! Ask me for the time, RAM, temperature, a calculation, or say: open notes."
    if _has(t, "help", "what can you do", "commands"):
        return ("Try:\n- what time is it\n- 12*7  /  what is (3+4)/2\n- how much ram / temperature / ip\n"
                "- add task buy milk  /  my tasks\n- note remember the wifi code\n- open weather\n"
                "- flip a coin / roll a dice / tell me a joke\n"
                "Online (direct to free web APIs):\n- wiki Ho Chi Minh City\n- search quantum computing\n"
                "- weather in Hanoi  /  weather\n- define serendipity\n- 100 usd to vnd\n- who is Ada Lovelace\n"
                "- news  /  world news  /  quote\n- air quality  /  aqi in Hanoi\n- bitcoin  /  price of eth")
    r = web_intent(t, text.strip())
    if r is not None:
        return r
    return "I don't understand that yet. Type help to see what I can do."

def page_assistant():
    content = """
<h1>Assistant</h1><div class="sub">Local logic on the board; web facts fetched directly. No cloud AI. Type <b>help</b>.</div>
<div class="card"><div id="m" style="min-height:200px;max-height:55vh;overflow:auto"></div>
<div style="display:flex;gap:8px"><input id="q" placeholder="Ask me something..." autocomplete="off" maxlength="200">
<button onclick="go()">Send</button></div></div>
<script>
var m=document.getElementById('m'),q=document.getElementById('q');
function bub(t,me){var d=document.createElement('div');d.style.cssText='margin:6px 0;padding:9px 12px;border-radius:16px;white-space:pre-wrap;max-width:88%;'+
 (me?'background:#087fff;color:#fff;margin-left:auto':'background:#eef0f5');
 if(t.charAt(0)=='@'){var p=t.slice(1).split('|'),a=document.createElement('a');a.href=p[0];a.textContent=p[1]+' →';d.appendChild(a);
  setTimeout(function(){location.href=p[0];},900);}
 else d.textContent=t;m.appendChild(d);m.scrollTop=m.scrollHeight;}
function go(){var t=q.value.trim();if(!t)return;q.value='';bub(t,true);
 fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'q='+encodeURIComponent(t)})
 .then(function(r){return r.text()}).then(function(x){bub(x,false);}).catch(function(){bub('(board busy, try again)',false);});}
q.addEventListener('keydown',function(e){if(e.key=='Enter')go();});
bub('Hi! I answer locally, and look up Wikipedia, search, weather, definitions and exchange rates directly online. Type help.',false);
</script>
"""
    return page("Assistant", content)

# -------------------- HTTP SERVER ----------------------------


def respond(client, body, status="200 OK",
            content_type="text/html; charset=utf-8"):
    try:
        if isinstance(body, str):
            body = body.encode("utf-8")
        header = (
            "HTTP/1.1 " + status + "\r\n"
            "Content-Type: " + content_type + "\r\n"
            "Connection: close\r\n"
            "Cache-Control: no-store\r\n"
            "Content-Length: " + str(len(body)) + "\r\n\r\n"
        )
        client.settimeout(10)
        client.sendall(header.encode("ascii"))
        mv = memoryview(body)
        for pos in range(0, len(body), 1024):
            client.sendall(mv[pos:pos + 1024])
            time.sleep_ms(5)   # let the Wi-Fi stack drain its buffers
        print("Sent", len(body), "bytes")
    except Exception as e:
        print("Response error:", repr(e))


def handle(client):
    try:
        client.settimeout(3)
        print("Waiting for HTTP request...")
        data = client.recv(4096)
        print("Received request:", len(data), "bytes")
        if not data:
            return

        header, sep, body = data.partition(b"\r\n\r\n")
        lines = header.decode("utf-8", "ignore").split("\r\n")
        parts = lines[0].split()
        if len(parts) < 2:
            respond(client, "Bad request", "400 Bad Request", "text/plain")
            return

        method = parts[0]
        target = parts[1]
        path = target.split("?", 1)[0]
        query = target.split("?", 1)[1] if "?" in target else ""

        length = 0
        for line in lines[1:]:
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                except Exception:
                    length = 0

        if length > 30000:
            respond(client, "Too large", "413 Payload Too Large", "text/plain")
            return
        while len(body) < length:
            chunk = client.recv(min(1024, length - len(body)))
            if not chunk:
                break
            body += chunk

        if route_extra(client, method, path, query, body):
            return

        if method == "POST" and path == "/notes":
            note = form_value(body, "note")[:4000]
            try:
                with open("note.txt", "w") as f:
                    f.write(note)
                output = page_notes("Saved successfully ✓")
            except Exception as e:
                output = page_notes("Save error: " + str(e))
            respond(client, output)
            return

        if method == "POST" and path == "/wifi":
            try:
                wlan.disconnect()
            except Exception:
                pass
            time.sleep(1)
            try:
                wlan.connect(SSID, PASSWORD)
            except Exception as e:
                print("Reconnect error:", e)
            output = page_wifi()
            respond(client, output)
            return

        if method == "POST" and path == "/bluetooth":
            result = scan_ble()
            output = page("Bluetooth", "<h1>Scan results</h1>" +
                          card("Nearby BLE devices", "<pre>" + esc(result) + "</pre>"))
            respond(client, output)
            return

        if path == "/":
            output = page_home()
        elif path == "/notes":
            output = page_notes()
        elif path == "/files":
            output = page_files()
        elif path == "/system":
            output = page_system()
        elif path == "/wifi":
            output = page_wifi()
        elif path == "/bluetooth":
            output = page_bluetooth()
        elif path == "/calc":
            output = page_calc()
        elif path == "/view":
            name = ""
            for item in query.split("&"):
                p = item.split("=", 1)
                if len(p) == 2 and p[0] == "name":
                    name = decode(p[1])
            output = page_view(name)
        elif path == "/reboot":
            output = page("Restarting", """
<h1>Restarting...</h1>
<div class="card">HungsOS is restarting. Wait a few seconds, then reload the page.</div>
""")
            respond(client, output)
            time.sleep(1)
            machine.reset()
            return
        else:
            output = page("Not found", "<h1>404</h1><p>Page not found.</p>")

        respond(client, output)

    except Exception as e:
        print("Request error:", repr(e))
        try:
            sys.print_exception(e)
        except Exception:
            pass

def serve():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass

    server.bind(addr)
    server.listen(3)
    server.settimeout(1)
    print("HungsOS web server started!")
    print("Open http://" + IP)

    while True:
        try:
            try:
                client, address = server.accept()
                global CLIENT_IP
                CLIENT_IP = address[0]
            except OSError:
                continue
            try:
                handle(client)
            except Exception as e:
                print("handler error:", repr(e))
            try:
                client.close()
            except Exception:
                pass
            try:
                gc.collect()
            except Exception:
                pass
        except Exception as e:
            # never let one bad request stop the server
            print("server loop error:", repr(e))
            time.sleep_ms(100)

# -------------------- START HUNGSOS -------------------------

if SSID == "YOUR_WIFI_NAME":
    print("WARNING: copy wifi_config_example.py to wifi_config.py and fill it in.")

IP = connect()
if IP != "0.0.0.0":
    sync_time()

if IP != "0.0.0.0":
    serve()
else:
    print("HungsOS server not started because Wi-Fi is disconnected.")
    print("Check SSID and password, then run main.py again.")
