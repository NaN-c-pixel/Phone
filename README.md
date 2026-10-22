# Phone

A pocket computer on an **ESP32-S3 (N16R8)** running MicroPython. It serves an iPhone-style
home screen over Wi-Fi; open it from any phone or PC browser on the same network.

**Apps:**
- **Notes**, **Tasks** (to-do list with done/delete)
- **Files** (view, create, edit, delete files on the board)
- **Timer** (stopwatch with laps + countdown)
- **Monitor** (live RAM, Wi-Fi signal graph, chip temperature)
- **GPIO** (set/read safe pins, e.g. to drive an LED)
- **Wi-Fi**, **Bluetooth** scanner, **Calculator**, **Settings**, **Reboot**

The clock is set from the internet (NTP); change `TZ_HOURS` at the top of `main.py` for your time zone.

## Roadmap
- [x] Wi-Fi web UI (HungsOS Pocket Edition)
- [ ] Small screen (OLED / TFT) + buttons
- [ ] Battery (LiPo + charger)
- [ ] SIM module (A7670 / SIM7600) for calls and SMS

## Setup
1. **Flash MicroPython** (Octal-SPIRAM build for ESP32_GENERIC_S3):
   ```
   esptool.py --chip esp32s3 erase_flash
   esptool.py --chip esp32s3 write_flash 0 firmware.bin
   ```
2. **Open Thonny** → Interpreter: *MicroPython (ESP32)* → pick the COM port.
3. **Save the files to the board** (File → Save as → *MicroPython device*): `main.py` (tiny launcher),
   `app.py` (the real program) and `wifi_config.py`. For the last one, copy
   `wifi_config_example.py`, fill in your 2.4 GHz network name and password.
4. Press RESET. The shell prints `Open http://192.168.x.x` — visit that address.

## Troubleshooting
| Problem | Fix |
|---|---|
| Can't save: `backend isn't ready` | Press Stop/Ctrl+C during the 5-second countdown after RST, or hold **BOOT** while pressing **RST** for edit mode |
| `Device is busy` / `backend isn't ready` | Press Stop (Ctrl+C), then RESET; or replug USB |
| `Access is denied` on COM port | Close other apps using it, replug, restart Thonny |
| `Wifi Internal State Error` | Handled automatically (driver reset + retries) |
| Page times out | Same Wi-Fi as the board? Try `ping <ip>`. Disable VPN. Router "AP isolation" must be off. Only 2.4 GHz works |
| Out of memory | Notes are capped at 4000 characters |

Never commit `wifi_config.py`.
