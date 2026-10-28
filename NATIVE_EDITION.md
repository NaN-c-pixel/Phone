# HungsOS Native Edition

This work is being developed on the `native-screen` branch. Keep `main` as the existing Wi-Fi/web edition until the native UI is tested on the actual hardware.

## Chosen startup experience

1. **Boot splash:** black background with a glowing HungsOS wordmark and a restrained loading animation.
2. **Lock screen:** large clock and date, with a clear swipe-up hint.
3. **Unlock:** a six-digit PIN keypad with six masked indicators.
4. **Home screen:** native app launcher with a compact status bar and rounded app tiles.

The six-digit PIN is a user-configurable setting; do not hard-code a real PIN into source control. A lightweight local lock is a convenience feature, not strong protection for data stored on a physically accessible microcontroller.

## Input

- Touchscreen: swipe upward to reveal the PIN keypad, tap digits, and swipe/tap to navigate.
- KY-023 joystick fallback: use VRx/VRy to move focus, SW to select, and a deliberate upward gesture to unlock.
- Use 3.3 V for the joystick module. ESP32 GPIOs are not 5 V tolerant.
- Debounce the joystick switch and analog directions; provide a visible focus indicator for non-touch use.

## Display hardware is not confirmed yet

The product listing mentions both ST7789V and ILI9341 and has separate touchscreen/non-touch options. These are not enough to identify the exact module ordered. Confirm the controller and touch option from the order variant, seller, or PCB markings before choosing a driver and GPIO mapping.

Keep display operations behind a small driver interface so the UI state machine is independent of the final controller. Do not assume that a touch controller is present just because the TFT is present.

## Native-mode goals

- Draw directly to the TFT; the browser-based web interface is not the native UI.
- Keep startup and rendering lightweight for MicroPython on the ESP32-S3 N16R8.
- Preserve existing web-edition code on `main`; native development stays on this branch.
- Reuse existing app logic only where it can be separated from HTTP/browser assumptions. Native UI navigation and screen rendering will need their own implementation.
- Avoid enabling the Wi-Fi web server in native-only startup mode.

## Suggested implementation stages

1. Confirm display controller, touch variant, screen orientation, and available pins.
2. Implement and test display initialization, color fill, text, and a simple HungsOS splash.
3. Add input abstraction for touchscreen and KY-023 joystick.
4. Build the boot → lock screen → PIN → home state machine.
5. Port native app screens incrementally and test memory/refresh performance on the real board.
6. Document installation and publish a release only after hardware testing.

## Current status

Design decisions recorded; display-specific driver and GPIO mapping are intentionally pending hardware confirmation.
