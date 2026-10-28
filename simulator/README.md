# HungsOS ILI9341 Circuit Simulator

The existing `index.html` is a browser-only UI mockup. This folder documents the planned Wokwi circuit so the ESP32-S3, display and GPIO wiring can be simulated separately.

## Board identification

The physical board has two USB-C ports and an ESP32-S3-WROOM module. This narrows the board family, but does not uniquely identify the development-board layout or its exposed GPIO pins. Do not assume that all two-USB-C ESP32-S3 boards have the same pinout.

## Proposed SPI display connections

These are a *draft* mapping for the virtual circuit, not confirmed wiring for the physical board. Verify the chosen Wokwi board's exposed GPIOs before building the diagram.

| ILI9341 pin | Draft ESP32-S3 GPIO |
|---|---:|
| VCC | 3V3 |
| GND | GND |
| SCK / CLK | GPIO 12 |
| SDI / MOSI | GPIO 11 |
| SDO / MISO | GPIO 13 (optional if display reads are unused) |
| CS | GPIO 10 |
| DC / RS | GPIO 9 |
| RESET / RST | GPIO 14 |
| LED / BL | Follow the module's backlight specification |

## Touchscreen warning

ILI9341 is the display controller, not the touch controller. A resistive-touch variant commonly exposes separate touch SPI pins and uses a controller such as XPT2046. Do not assume touch is present or wire touch pins until the exact screen variant is confirmed.

## Next step

Select the closest Wokwi ESP32-S3 board model and add the ILI9341 part and jumper connections in Wokwi. The HTML UI preview does not itself emulate electrical pins. Firmware integration should wait until the simulator's supported display API and selected board model are verified.
