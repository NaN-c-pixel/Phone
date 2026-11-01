# HungsOS offline video (.hvid)

The video-playing branch adds offline playback alongside the browser-cast experiment.

## Files

- tools/hvid_encode.py: PC-side encoder. Uses FFmpeg to decode common video formats.
- hungsos_video.py: MicroPython player for the ESP32-S3.
- .hvid: custom, silent, 320x240 RGB565 video container.

## Encode on Windows

1. Install FFmpeg and make sure `ffmpeg` works in PowerShell.
2. From the repository folder run:

   `py tools\\hvid_encode.py "C:\\Videos\\clip.mp4" --fps 15`

3. Copy the resulting .hvid file to the SD card, for example as /sd/movie.hvid.

The encoder letterboxes the image (keeps its aspect ratio), removes audio, converts to 320x240 RGB565, and stores only changed 16x16 tiles. Repeated-colour runs and literal pixel blocks use a small PackBits-style codec. A full keyframe is written every 30 frames by default.

## Play on the ESP32

The SD card must first be mounted at /sd by a driver/configuration matching the actual module wiring. This project deliberately does not guess SD GPIO pins.

With the HungsOS PC framebuffer and show() function already initialized:

    import hungsos_video
    hungsos_video.play("/sd/movie.hvid", buf, show, show_tile=show_tile)

The player reads one tile at a time and updates the existing framebuffer. Sparse frames are sent as partial ILI9341 tile updates using show_tile; dense frames use one full-screen refresh. It does not load the whole movie into RAM or use the 16 MB flash for video storage.

## Format and limits

- 320x240, RGB565 (65,536 colours), silent.
- Target 15 FPS; actual playback speed depends on SD read speed, SPI display speed and MicroPython overhead.
- Compression ratio depends heavily on the video. Static scenes and repeated areas compress well; fast, noisy footage may not.
- 8 MB PSRAM is not required for a whole-video buffer; the player uses the existing 153,600-byte display framebuffer plus small tile buffers.
- HVID is a simple custom frame/tile format, not H.264. The PC does the expensive video decoding.

Do not claim 15 FPS until measured on the physical board. The existing live /cast feature remains separate and unchanged.
