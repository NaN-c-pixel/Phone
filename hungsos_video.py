# HungsOS HVID video player for ESP32-S3 / MicroPython
# Reads a .hvid file from an already-mounted SD card and draws into the
# existing 320x240 RGB565 framebuffer used by hungsos_desktop.py.
#
# Usage:
#   import hungsos_video
#   hungsos_video.play("/sd/movie.hvid", buf, show)
#
# SD-card mounting is intentionally separate because SPI pin assignments
# depend on the user's actual SD module wiring. Do not guess those pins.

import time
import gc

WIDTH = 320
HEIGHT = 240
MAGIC = b"HVID"
VERSION = 1


def _read_exact(f, size):
    data = f.read(size)
    if data is None or len(data) != size:
        raise ValueError("Unexpected end of HVID file")
    return data


def _u16(data, offset=0):
    return data[offset] | (data[offset + 1] << 8)


def _decode_packbits(src, dst, pixel_count):
    si = 0
    di = 0
    total = pixel_count * 2
    while di < total:
        if si >= len(src):
            raise ValueError("Broken PackBits tile")
        token = src[si]
        si += 1
        count = (token & 0x7F) + 1
        if token & 0x80:
            if si + 2 > len(src):
                raise ValueError("Broken PackBits run")
            a, b = src[si], src[si + 1]
            si += 2
            end = di + count * 2
            if end > total:
                raise ValueError("PackBits run exceeds tile")
            while di < end:
                dst[di] = a
                dst[di + 1] = b
                di += 2
        else:
            amount = count * 2
            if si + amount > len(src) or di + amount > total:
                raise ValueError("PackBits literal exceeds tile")
            dst[di:di + amount] = src[si:si + amount]
            si += amount
            di += amount
    if si != len(src):
        raise ValueError("Extra PackBits data")
    return dst


def _write_tile(framebuffer, x, y, w, h, tile):
    row_bytes = w * 2
    src = 0
    for row in range(h):
        dst = ((y + row) * WIDTH + x) * 2
        framebuffer[dst:dst + row_bytes] = tile[src:src + row_bytes]
        src += row_bytes


def play(path, framebuffer, show, loop=False, max_frames=None):
    """Play HVID from path. Returns number of frames displayed.

    framebuffer must be a 320x240 RGB565 bytearray. show() sends it to ILI9341.
    Set loop=True to repeat; max_frames is useful for a short test.
    """
    if len(framebuffer) != WIDTH * HEIGHT * 2:
        raise ValueError("Expected a 320x240 RGB565 framebuffer")

    displayed = 0
    while True:
        with open(path, "rb") as f:
            header = _read_exact(f, 15)
            if header[0:4] != MAGIC or header[4] != VERSION:
                raise ValueError("Not a supported HVID v1 file")
            width, height = _u16(header, 5), _u16(header, 7)
            fps = header[9]
            frame_count = int.from_bytes(header[11:15], "little")
            if width != WIDTH or height != HEIGHT:
                raise ValueError("Video must be 320x240")
            if fps < 1 or fps > 20:
                raise ValueError("Invalid HVID FPS")

            frame_index = 0
            while frame_index < frame_count:
                frame_start = time.ticks_ms()
                record = _read_exact(f, 4)
                delay_ms, tile_count = _u16(record, 0), _u16(record, 2)
                for _ in range(tile_count):
                    thdr = _read_exact(f, 7)
                    x, y, w, h, codec = thdr[0], thdr[1], thdr[2], thdr[3], thdr[4]
                    data_len = _u16(thdr, 5)
                    if w < 1 or h < 1 or x + w > WIDTH or y + h > HEIGHT:
                        raise ValueError("Invalid tile position")
                    if w > 16 or h > 16 or data_len > 1024:
                        raise ValueError("Invalid tile size")
                    payload = _read_exact(f, data_len)
                    tile = bytearray(w * h * 2)
                    if codec == 0:
                        if data_len != len(tile):
                            raise ValueError("Raw tile length mismatch")
                        tile[:] = payload
                    elif codec == 1:
                        _decode_packbits(payload, tile, w * h)
                    else:
                        raise ValueError("Unknown tile codec")
                    _write_tile(framebuffer, x, y, w, h, tile)

                show()
                displayed += 1
                frame_index += 1
                if max_frames is not None and displayed >= max_frames:
                    return displayed
                elapsed = time.ticks_diff(time.ticks_ms(), frame_start)
                wait = delay_ms - elapsed
                if wait > 0:
                    time.sleep_ms(wait)

        if not loop:
            break
        gc.collect()
    return displayed
