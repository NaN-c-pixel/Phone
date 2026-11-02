# HungsOS Render — lightweight 2D drawing helpers for ESP32-S3 / MicroPython.
# Works with the ILI9341 driver in tft_screen.py. No GPU API required.

BLACK = 0x0000
WHITE = 0xFFFF
BLUE = 0x087F
GREEN = 0x07E0
RED = 0xF800
GRAY = 0x8410
DARK = 0x2104
LIGHT = 0xEF7D


def rgb565(red, green, blue):
    """Convert 8-bit RGB values to an ILI9341 RGB565 colour."""
    red = max(0, min(255, int(red)))
    green = max(0, min(255, int(green)))
    blue = max(0, min(255, int(blue)))
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


class Renderer2D:
    """Small immediate-mode 2D renderer around a tft_screen.ILI9341 object."""

    def __init__(self, display):
        if display is None:
            raise ValueError("A display instance is required")
        self.display = display
        self.width = display.width
        self.height = display.height

    def clear(self, color=BLACK):
        self.display.fill(color)

    def pixel(self, x, y, color=WHITE):
        x, y = int(x), int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.display.rect(x, y, 1, 1, color)

    def rect(self, x, y, width, height, color=WHITE, filled=True):
        x, y = int(x), int(y)
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            return
        if filled:
            self.display.rect(x, y, width, height, color)
        else:
            self.line(x, y, x + width - 1, y, color)
            self.line(x, y, x, y + height - 1, color)
            self.line(x + width - 1, y, x + width - 1, y + height - 1, color)
            self.line(x, y + height - 1, x + width - 1, y + height - 1, color)

    def line(self, x0, y0, x1, y1, color=WHITE):
        """Bresenham line; uses the driver's 1x1 rectangle as a pixel."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def circle(self, cx, cy, radius, color=WHITE, filled=False):
        """Midpoint circle. Filled mode draws horizontal spans."""
        cx, cy, radius = int(cx), int(cy), int(radius)
        if radius < 0:
            return
        x, y, decision = radius, 0, 1 - radius
        while x >= y:
            if filled:
                self.line(cx - x, cy + y, cx + x, cy + y, color)
                self.line(cx - x, cy - y, cx + x, cy - y, color)
                self.line(cx - y, cy + x, cx + y, cy + x, color)
                self.line(cx - y, cy - x, cx + y, cy - x, color)
            else:
                points = ((cx+x,cy+y),(cx+y,cy+x),(cx-y,cy+x),(cx-x,cy+y),
                          (cx-x,cy-y),(cx-y,cy-x),(cx+y,cy-x),(cx+x,cy-y))
                for px, py in points:
                    self.pixel(px, py, color)
            y += 1
            if decision <= 0:
                decision += 2 * y + 1
            else:
                x -= 1
                decision += 2 * (y - x) + 1

    def text(self, value, x, y, color=WHITE, scale=1):
        self.display.text(str(value), int(x), int(y), color, max(1, int(scale)))

    def centered_text(self, value, y, color=WHITE, scale=1):
        value = str(value)
        scale = max(1, int(scale))
        # The bundled font is 5 pixels wide plus one pixel of spacing.
        x = (self.width - len(value) * 6 * scale) // 2
        self.text(value, x, y, color, scale)

    def button(self, x, y, width, height, label, color=BLUE,
               text_color=WHITE):
        self.rect(x, y, width, height, color, True)
        label = str(label)
        scale = 1
        tx = int(x) + max(2, (int(width) - len(label) * 6) // 2)
        ty = int(y) + max(2, (int(height) - 7) // 2)
        self.text(label, tx, ty, text_color, scale)

    def progress(self, x, y, width, height, value, maximum=100,
                 color=GREEN, background=GRAY):
        width, height = int(width), int(height)
        self.rect(x, y, width, height, background, True)
        if maximum <= 0:
            return
        value = max(0, min(maximum, value))
        filled_width = (width * value) // maximum
        if filled_width:
            self.rect(x, y, filled_width, height, color, True)


def demo(display):
    """Draw a simple 2D test screen. Pass an initialized ILI9341 display."""
    canvas = Renderer2D(display)
    canvas.clear(LIGHT)
    canvas.rect(0, 0, canvas.width, 42, BLUE)
    canvas.text("HungsOS Render", 10, 15, WHITE, 2)
    canvas.centered_text("2D graphics test", 58, DARK, 1)
    canvas.rect(12, 82, canvas.width - 24, 74, WHITE, True)
    canvas.circle(canvas.width // 2, 119, 24, BLUE, False)
    canvas.line(20, 175, canvas.width - 20, 205, RED)
    canvas.button(24, 225, canvas.width - 48, 34, "RENDER OK", GREEN)
    canvas.text("ESP32-S3 / MicroPython", 10, canvas.height - 18, DARK, 1)
    return canvas
