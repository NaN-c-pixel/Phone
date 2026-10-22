# Phone

A pocket computer on an **ESP32-S3 (N16R8)** running MicroPython. It serves an iPhone-style
home screen over Wi-Fi; open it from any phone or PC browser on the same network.

**Apps:** Notes, Files, Settings, Wi-Fi, Bluetooth scanner, Calculator, Reboot.

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
3. **Wi-Fi login:** copy `wifi_config_example.py` to `wifi_config.py`, fill in your 2.4 GHz
   network name and password, and save **both** it and `main.py` to the board
   (File → Save as → *MicroPython device*).
4. Press RESET. The shell prints `Open http://192.168.x.x` — visit that address.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Device is busy` / `backend isn't ready` | Press Stop (Ctrl+C), then RESET; or replug USB |
| `Access is denied` on COM port | Close other apps using it, replug, restart Thonny |
| `Wifi Internal State Error` | Handled automatically (driver reset + retries) |
| Page times out | Same Wi-Fi as the board? Try `ping <ip>`. Disable VPN. Router "AP isolation" must be off. Only 2.4 GHz works |
| Out of memory | Notes are capped at 4000 characters |

Never commit `wifi_config.py`.
