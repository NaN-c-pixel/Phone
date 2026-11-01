#!/usr/bin/env python3
"""Convert a video into HungsOS HVID v1 (320x240 RGB565, tile-delta + PackBits).
Requires FFmpeg in PATH. Audio is intentionally omitted.
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys

WIDTH, HEIGHT, TILE = 320, 240, 16
HEADER = struct.Struct("<4sBHHBBI")
FRAME = struct.Struct("<HH")
TILE_HEADER = struct.Struct("<BBBBBH")


def packbits(pixels):
    count = len(pixels) // 2
    out = bytearray()
    i = 0
    while i < count:
        pixel = pixels[i * 2:i * 2 + 2]
        run = 1
        while i + run < count and run < 128 and pixels[(i + run) * 2:(i + run) * 2 + 2] == pixel:
            run += 1
        if run >= 3:
            out.append(0x80 | (run - 1))
            out.extend(pixel)
            i += run
            continue
        start = i
        i += run
        while i < count and i - start < 128:
            pixel = pixels[i * 2:i * 2 + 2]
            run = 1
            while i + run < count and run < 3 and pixels[(i + run) * 2:(i + run) * 2 + 2] == pixel:
                run += 1
            if run >= 3:
                break
            i += run
        n = i - start
        out.append(n - 1)
        out.extend(pixels[start * 2:i * 2])
    return bytes(out)


def rgb24_to_565(raw):
    out = bytearray(WIDTH * HEIGHT * 2)
    p = 0
    for i in range(0, len(raw), 3):
        r, g, b = raw[i], raw[i + 1], raw[i + 2]
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out[p] = value & 255
        out[p + 1] = value >> 8
        p += 2
    return out


def get_tile(frame, tx, ty):
    tw, th = min(TILE, WIDTH - tx), min(TILE, HEIGHT - ty)
    out = bytearray(tw * th * 2)
    pos = 0
    for row in range(th):
        start = ((ty + row) * WIDTH + tx) * 2
        out[pos:pos + tw * 2] = frame[start:start + tw * 2]
        pos += tw * 2
    return bytes(out)


def encode(input_path, output_path, fps=15, key_interval=30):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH.")
    if not 1 <= fps <= 20:
        raise ValueError("FPS must be between 1 and 20.")
    if not 1 <= key_interval <= 255:
        raise ValueError("Keyframe interval must be between 1 and 255.")

    vf = ("fps=%d,scale=%d:%d:force_original_aspect_ratio=decrease:flags=bicubic,"
          "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black,format=rgb24"
          % (fps, WIDTH, HEIGHT, WIDTH, HEIGHT))
    command = ["ffmpeg", "-v", "error", "-i", input_path, "-an", "-sn",
               "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frame_bytes = WIDTH * HEIGHT * 3
    previous = None
    frame_count = 0
    raw_total = 0

    try:
        with open(output_path, "wb") as out:
            out.write(HEADER.pack(b"HVID", 1, WIDTH, HEIGHT, fps, key_interval, 0))
            while True:
                raw = proc.stdout.read(frame_bytes)
                if not raw:
                    break
                if len(raw) != frame_bytes:
                    raise RuntimeError("FFmpeg returned an incomplete frame.")
                current = rgb24_to_565(raw)
                keyframe = previous is None or (frame_count % key_interval == 0)
                changed = []
                for ty in range(0, HEIGHT, TILE):
                    for tx in range(0, WIDTH, TILE):
                        tile = get_tile(current, tx, ty)
                        if not keyframe and tile == get_tile(previous, tx, ty):
                            continue
                        packed = packbits(tile)
                        codec, payload = (1, packed) if len(packed) < len(tile) else (0, tile)
                        changed.append((tx, ty, min(TILE, WIDTH-tx),
                                        min(TILE, HEIGHT-ty), codec, payload))

                out.write(FRAME.pack(round(1000 / fps), len(changed)))
                for x, y, w, h, codec, payload in changed:
                    out.write(TILE_HEADER.pack(x, y, w, h, codec, len(payload)))
                    out.write(payload)
                previous = current
                frame_count += 1
                raw_total += frame_bytes
                if frame_count % fps == 0:
                    print("Encoded %d frames..." % frame_count)

            if proc.wait() != 0:
                raise RuntimeError("FFmpeg failed to decode the input video.")
            out.seek(0)
            out.write(HEADER.pack(b"HVID", 1, WIDTH, HEIGHT, fps, key_interval, frame_count))
    finally:
        if proc.poll() is None:
            proc.kill()
        if proc.stdout:
            proc.stdout.close()

    if frame_count == 0:
        os.remove(output_path)
        raise RuntimeError("No video frames were decoded.")
    size = os.path.getsize(output_path)
    print("")
    print("HungsOS video created:", output_path)
    print("Frames: %d | %d FPS | %dx%d RGB565" % (frame_count, fps, WIDTH, HEIGHT))
    print("Raw RGB565 size: %.2f MB" % (raw_total / 1048576))
    print("HVID file size: %.2f MB" % (size / 1048576))
    print("Compression ratio: %.1f%% of raw" % (100.0 * size / max(1, raw_total)))
    print("Copy the .hvid file to the SD card, e.g. /sd/movie.hvid")


def main():
    parser = argparse.ArgumentParser(description="HungsOS Mega Video Encoder")
    parser.add_argument("input", help="Input video file supported by FFmpeg")
    parser.add_argument("-o", "--output", help="Output .hvid file (default: input.hvid)")
    parser.add_argument("--fps", type=int, default=15, help="Target FPS, 1-20 (default: 15)")
    parser.add_argument("--key-interval", type=int, default=30, help="Full frame every N frames")
    args = parser.parse_args()
    output = args.output or os.path.splitext(args.input)[0] + ".hvid"
    try:
        encode(args.input, output, args.fps, args.key_interval)
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
