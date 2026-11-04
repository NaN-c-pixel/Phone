# ESP32-S3 Pocket PC (Windows Mobile 6 style)

Your ESP32-S3 N16R8 hosts its own Wi-Fi network and serves a Windows Mobile 6 style
interface (Today screen, Start menu, Notes, File Explorer, Wi-Fi manager, Calculator, About).
Use any phone or laptop as the screen and keyboard.

## Flash it
1. Install PlatformIO (VS Code extension or `pip install platformio`).
2. In this folder:
   - `pio run -t upload`     (firmware)
   - `pio run -t uploadfs`   (the web UI in `data/`)
3. Join the Wi-Fi **WM6-Pocket** (password `pocketpc1`).
4. Open **http://192.168.4.1** (or http://pocketpc.local).

Change the AP name/password at the top of `src/main.cpp`.

## What works
- Today screen with clock (synced from your browser), owner info, status rows
- Notes saved to flash (LittleFS)
- File Explorer: view, edit, delete files on the board
- Wireless Manager: scan and join your home Wi-Fi (saved, auto-reconnects)
- Messenger: one shared chat for everyone connected to the board (last 200 messages, kept in RAM, cleared on reboot)
- Internet Explorer: text-mode browser. The board downloads the page and the UI shows readable text and
  clickable links (no images, scripts or forms). It needs the board joined to a home Wi-Fi with internet
  via Wireless Manager. HTTPS certificates are not verified, so don't log in to anything with it.
  Address bar: type a URL or a search phrase (searches DuckDuckGo's HTML page).
- Calculator, About (CPU, temperature, heap, PSRAM, storage), Reboot

## Little display (ILI9341 2.8" 240x320, no touch)
`src/display.cpp` draws a WM6 style screen: Today, Start menu, Notes (read), Messenger (read),
Wi-Fi status, About. Typing, sending messages and browsing stay in the web UI.

| Display pin | ESP32-S3 | | Button (other leg to GND) | ESP32-S3 |
|---|---|---|---|---|
| VCC / GND | 3V3 / GND | | UP | GPIO4 |
| CS | GPIO10 | | DOWN | GPIO5 |
| RESET | GPIO8 | | LEFT softkey | GPIO6 |
| DC | GPIO9 | | RIGHT softkey | GPIO7 |
| MOSI (SDI) | GPIO11 | | OK | GPIO15 |
| SCK | GPIO12 | | | |
| LED (backlight) | GPIO14 | | | |
| MISO (SDO) | GPIO13 (optional) | | | |

Pins are at the top of `display.cpp`. If colors look inverted or red/blue are swapped,
flip `c.invert` / `c.rgb_order` in the same file. Clock uses UTC+7; change `TZ` in `main.cpp`.
The clock gets its time when you open the web UI once after each power-up (no battery clock yet).

## Next steps
USB keyboard on the S3's native USB port for typing on the device itself.
