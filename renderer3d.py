# HungsOS Hungs3D — tiny wireframe renderer for ESP32-S3 / MicroPython.
# Uses the existing Renderer2D API (canvas.line) and requires no 3D GPU.

import math


CUBE_VERTICES = (
    (-1.0, -1.0, -1.0),
    ( 1.0, -1.0, -1.0),
    ( 1.0,  1.0, -1.0),
    (-1.0,  1.0, -1.0),
    (-1.0, -1.0,  1.0),
    ( 1.0, -1.0,  1.0),
    ( 1.0,  1.0,  1.0),
    (-1.0,  1.0,  1.0),
)

CUBE_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
)


class WireframeRenderer:
    """Perspective wireframe renderer that draws through a Renderer2D canvas.

    Coordinates use a camera looking along +Z. Objects closer than near
    are clipped before projection to avoid division by zero and huge lines.
    """

    def __init__(self, canvas, focal_length=None, near=0.15):
        if canvas is None:
            raise ValueError("A Renderer2D canvas is required")
        self.canvas = canvas
        self.width = canvas.width
        self.height = canvas.height
        self.center_x = self.width * 0.5
        self.center_y = self.height * 0.5
        self.focal_length = (min(self.width, self.height) * 0.85
                             if focal_length is None else float(focal_length))
        self.near = float(near)

    @staticmethod
    def _rotate(point, sin_x, cos_x, sin_y, cos_y, sin_z, cos_z):
        x, y, z = point

        # Rotate around X.
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
        # Rotate around Y.
        x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
        # Rotate around Z.
        x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z
        return x, y, z

    def _project(self, point):
        x, y, z = point
        factor = self.focal_length / z
        sx = int(self.center_x + x * factor)
        sy = int(self.center_y - y * factor)
        return sx, sy

    def _draw_edge(self, a, b, color):
        # Clip an edge against the near plane in camera space.
        ax, ay, az = a
        bx, by, bz = b
        near = self.near

        if az < near and bz < near:
            return
        if az < near:
            t = (near - az) / (bz - az)
            ax = ax + (bx - ax) * t
            ay = ay + (by - ay) * t
            az = near
        elif bz < near:
            t = (near - az) / (bz - az)
            bx = ax + (bx - ax) * t
            by = ay + (by - ay) * t
            bz = near

        x0, y0 = self._project((ax, ay, az))
        x1, y1 = self._project((bx, by, bz))
        self.canvas.line(x0, y0, x1, y1, color)

    def draw_mesh(self, vertices, edges, rotation=(0.0, 0.0, 0.0),
                  camera_distance=4.0, scale=1.0, color=None):
        """Rotate, project, and draw a mesh.

        vertices: iterable of (x, y, z)
        edges: iterable of (vertex_index_a, vertex_index_b)
        rotation: Euler angles (X, Y, Z), in radians
        camera_distance: distance from camera to object origin
        scale: uniform object scale
        color: RGB565 color; defaults to WHITE from render.py
        """
        if color is None:
            color = 0xFFFF

        rx, ry, rz = rotation
        sin_x, cos_x = math.sin(rx), math.cos(rx)
        sin_y, cos_y = math.sin(ry), math.cos(ry)
        sin_z, cos_z = math.sin(rz), math.cos(rz)

        transformed = []
        for vertex in vertices:
            x, y, z = self._rotate(
                (vertex[0] * scale, vertex[1] * scale, vertex[2] * scale),
                sin_x, cos_x, sin_y, cos_y, sin_z, cos_z
            )
            transformed.append((x, y, z + camera_distance))

        for edge in edges:
            self._draw_edge(transformed[edge[0]], transformed[edge[1]], color)

    def draw_cube(self, angle_x=0.0, angle_y=0.0, angle_z=0.0,
                  size=1.0, camera_distance=4.0, color=None):
        """Convenience method for drawing a rotating cube."""
        self.draw_mesh(
            CUBE_VERTICES,
            CUBE_EDGES,
            rotation=(angle_x, angle_y, angle_z),
            camera_distance=camera_distance,
            scale=size,
            color=color
        )


def demo(canvas, frames=180, delay_ms=30):
    """Run a rotating-cube demo. Pass an initialized Renderer2D canvas.

    Call from main.py after initializing the display. Press Ctrl+C in the
    REPL to stop. The display is not initialized or reconfigured here.
    """
    import time

    renderer = WireframeRenderer(canvas)
    angle = 0.0
    while frames is None or frames > 0:
        canvas.clear(0x0000)
        renderer.draw_cube(
            angle_x=angle * 0.73,
            angle_y=angle,
            angle_z=angle * 0.37,
            size=1.0,
            camera_distance=4.2,
            color=0x07FF
        )
        canvas.text("Hungs3D / wireframe", 5, 5, 0xFFFF, 1)
        angle += 0.045
        if frames is not None:
            frames -= 1
        time.sleep_ms(delay_ms)
