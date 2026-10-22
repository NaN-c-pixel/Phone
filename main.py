
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
    value = value.replace("+", " ")
    out = ""
    i = 0
    while i < len(value):
        if value[i] == "%" and i + 2 < len(value):
            try:
                out += chr(int(value[i+1:i+3], 16))
                i += 3
                continue
            except Exception:
                pass
        out += value[i]
        i += 1
    return out

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
    try:
        now = time.localtime()
        clock = "%02d:%02d" % (now[3], now[4])
        date = "%04d-%02d-%02d" % (now[0], now[1], now[2])
    except Exception:
        clock = "--:--"
        date = "Welcome to HungsOS"

    apps = (
        app("📝", "Notes", "/notes", "yellow") +
        app("📁", "Files", "/files", "blue") +
        app("⚙️", "Settings", "/system", "dark") +
        app("📶", "Wi-Fi", "/wifi", "green") +
        app("ᛒ", "Bluetooth", "/bluetooth", "purple") +
        app("🧮", "Calculator", "/calc", "orange") +
        app("🔄", "Reboot", "/reboot", "pink")
    )

    content = """
<div class="hero">
<div class="eyebrow">Welcome back</div>
<div class="clock">""" + clock + """</div>
<div class="date">""" + date + """</div>
<h1>Applications</h1>
<div class="sub">Your pocket-sized ESP32 computer.</div>
</div>
<div class="grid">""" + apps + """</div>
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
            items += '<a href="/view?name=' + name + '">Open</a></div>'
    except Exception as e:
        items = "<p>Could not list files: " + esc(e) + "</p>"

    content = "<h1>Files</h1><div class='sub'>Files stored on the device.</div>"
    content += card("Device storage", items or "No files found.")
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

        while len(body) < length:
            chunk = client.recv(min(1024, length - len(body)))
            if not chunk:
                break
            body += chunk

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
            client, address = server.accept()
        except OSError:
            continue

        try:
            handle(client)
        finally:
            try:
                client.close()
            except Exception:
                pass
            gc.collect()

# -------------------- START HUNGSOS -------------------------

if SSID == "YOUR_WIFI_NAME":
    print("WARNING: copy wifi_config_example.py to wifi_config.py and fill it in.")

IP = connect()

if IP != "0.0.0.0":
    serve()
else:
    print("HungsOS server not started because Wi-Fi is disconnected.")
    print("Check SSID and password, then run main.py again.")
