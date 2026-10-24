# Phone

A pocket computer on an **ESP32-S3 (N16R8)** running MicroPython. It serves an iPhone-style
home screen over Wi-Fi; open it from any phone or PC browser on the same network.

**Apps:**
- **Notes**, **Tasks** (to-do list with done/delete)
- **Files** (view, create, edit, delete files on the board)
- **Timer** (stopwatch with laps + countdown)
- **Monitor** (live RAM, Wi-Fi signal graph, chip temperature)
- **GPIO** (set/read safe pins, e.g. to drive an LED)
- **Terminal** (Kali-style shell on the board: files, Wi-Fi, GPIO, `neofetch`; optional PIN-locked Python prompt)
- **Kali** (opens a *real* Kali Linux shell running on your PC/VM/Pi, see below)
- **Assistant** (tiny offline chatbot: time, RAM, temperature, maths, add tasks, open apps; no cloud or API key)
- **Weather** (live, set your city with `WEATHER_LAT/LON/NAME` in `wifi_config.py`), **Contacts**, **Calendar**
- **Convert** (units), **Snake**, **Passwords** (generator), **World** clock, **Net Tools** (DNS, port check, public IP)
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

## Real Kali on the phone
An ESP32 cannot run Kali itself (it needs a Linux kernel and gigabytes of storage), so the **Kali** app
shows a Kali shell that runs on a computer you own:
1. Install Kali (Windows: `wsl --install -d kali-linux`; or a VM; or a Raspberry Pi).
2. In Kali: `sudo apt install ttyd` then `ttyd -p 7681 -c kali:YOUR_PASSWORD bash`.
3. In `wifi_config.py` on the board add `KALI_URL = "http://<that-computer-ip>:7681"`.
Home Wi-Fi only; never expose the port to the internet.

## Test your board's flash (if saving files fails)
If saving files fails with `OSError: 28`, `OSError: 36` or "No space left on device" even though
the storage looks empty, the board's flash may be unreliable (common on cheap or relabeled chips).
`tools/flashtest.py` writes and re-reads random data at every 1 MB of the flash and reports which
areas are good.

```
python -m pip install esptool
python tools/flashtest.py COM6      # use your board's COM port
```

- Put the board in download mode if it can't connect (hold **BOOT**, tap **RST**, release **BOOT**).
- The test overwrites the filesystem area, so afterwards run `python -m esptool --port COM6 erase_flash`
  and flash MicroPython again.
- Run `python -m esptool --port COM6 flash_id` first to see the flash maker and size.
- Post the output in an issue so others can compare their boards.

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
