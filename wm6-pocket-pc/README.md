# WM6 Pocket PC for ESP32-S3 N16R8

This is a separate Arduino/PlatformIO firmware project. It does not replace the existing MicroPython HungsOS files in the repository root.

## Target and compatibility

- Target: ESP32-S3 N16R8 (16 MB flash + 8 MB octal PSRAM)
- Framework: Arduino via PlatformIO
- Display driver: LovyanGFX for a 2.8-inch ILI9341 SPI display (240x320)
- Web interface: LittleFS files in `data/`
- The physical ILI9341 screen in this project is **not touch-enabled**; use the five GPIO buttons listed in the source comments. The web UI is controlled from a phone or computer connected to the ESP32 access point.

The supplied `platformio.ini` selects `esp32-s3-devkitc-1` with QIO flash + OPI PSRAM settings, which is the PlatformIO board definition used for ESP32-S3 N16R8 modules.

## Build and flash

Open this folder in VS Code with the PlatformIO extension, or install PlatformIO Core:

```powershell
py -m pip install --upgrade platformio
```

From this folder:

```powershell
pio run
pio run -t upload
pio run -t uploadfs
pio device monitor -b 115200
```

If more than one serial port is connected, specify the ESP32-S3 port:

```powershell
pio run -t upload --upload-port COM7
pio run -t uploadfs --upload-port COM7
pio device monitor --port COM7 -b 115200
```

## Connect

1. Join Wi-Fi network `WM6-Pocket` (default password: `pocketpc1`).
2. Open `http://192.168.4.1` from a phone or computer.
3. Change the access-point name/password near the top of `src/main.cpp` before sharing the device with others.

## ILI9341 wiring

See the wiring table in the project README/source. Default pins: SCLK 12, MOSI 11, MISO 13, DC 9, CS 10, RESET 8, backlight 14. Navigation buttons use GPIO4, GPIO5, GPIO15, GPIO6 and GPIO7.

**Hardware check before flashing:** this firmware assumes an SPI ILI9341 240x320 display. If your ESP32-S3 board has a different built-in display/controller or touch controller, its display driver and pin mapping must be changed first. Do not assume a different screen is ILI9341-compatible.

## Notes

- This firmware is independent from the MicroPython HungsOS firmware in the repository root.
- Uploading the firmware and uploading the LittleFS web files are separate steps; run both `upload` and `uploadfs`.
- The browser proxy does not verify HTTPS certificates. Do not use it to sign in to accounts or enter passwords.
- First build downloads the PlatformIO platform and libraries, so it needs an internet connection.
