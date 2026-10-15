r"""Test dell'helper geometrico octagon_points.

Nessuna dipendenza da Tkinter o Pillow: il modulo è importabile
su una macchina headless.
"""

import math

from kemai_client.geometry import octagon_points


class TestOctagonPoints:
    def test_octagon_has_eight_vertices(self):
        pts = octagon_points(36.0, 36.0, 10.0)
        assert len(pts) == 16

    def test_octagon_first_vertex_angle(self):
        # Primo vertice: 22,5°. In un sistema dove y è verso il basso
        # (come Tkinter), il punto a 22,5° è:
        #   x = cx + r*cos(22,5°), y = cy - r*sin(22,5°)
        pts = octagon_points(0.0, 0.0, 10.0)
        angle = math.radians(22.5)
        expected_x = 10.0 * math.cos(angle)
        expected_y = -10.0 * math.sin(angle)
        assert math.isclose(pts[0], expected_x, abs_tol=1e-9)
        assert math.isclose(pts[1], expected_y, abs_tol=1e-9)
