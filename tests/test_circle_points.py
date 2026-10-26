r"""Test della funzione circle_points.

Nessuna dipendenza da Tkinter o Pillow: il modulo è importabile
su una macchina headless.
"""

import math

import pytest

from kemai_client.geometry import circle_points


class TestCirclePoints:
    def test_circle_has_n_vertices(self):
        pts = circle_points(0.0, 0.0, 1.0, 6)
        assert len(pts) == 6

    def test_circle_first_point_at_angle_zero(self):
        pts = circle_points(5.0, 3.0, 2.0, 4)
        # Primo punto: (cx+r, cy) = (7.0, 3.0)
        assert math.isclose(pts[0][0], 7.0, abs_tol=1e-9)
        assert math.isclose(pts[0][1], 3.0, abs_tol=1e-9)

    def test_circle_anti_clockwise_order(self):
        pts = circle_points(0.0, 0.0, 1.0, 4)
        # Angoli: 0, π/2, π, 3π/2
        assert math.isclose(pts[0][0], 1.0, abs_tol=1e-9)   # (1, 0)
        assert math.isclose(pts[1][1], 1.0, abs_tol=1e-9)   # (0, 1)
        assert math.isclose(pts[2][0], -1.0, abs_tol=1e-9)  # (-1, 0)
        assert math.isclose(pts[3][1], -1.0, abs_tol=1e-9)  # (0, -1)

    def test_circle_no_duplicate_closure(self):
        """Se n=5 si ottengono 5 punti, non 6 (l'ultimo non ripete il primo)."""
        pts = circle_points(0.0, 0.0, 1.0, 5)
        assert len(pts) == 5
        assert pts[0] != pts[-1]

    def test_circle_symmetry(self):
        """I punti sono equidistanti dall'origine."""
        pts = circle_points(0.0, 0.0, 3.0, 8)
        for x, y in pts:
            assert math.isclose(math.hypot(x, y), 3.0, abs_tol=1e-9)

    def test_circle_type_error_non_int(self):
        with pytest.raises(TypeError):
            circle_points(0.0, 0.0, 1.0, 3.5)

    def test_circle_type_error_string(self):
        with pytest.raises(TypeError):
            circle_points(0.0, 0.0, 1.0, "3")

    def test_circle_value_error_zero(self):
        with pytest.raises(ValueError):
            circle_points(0.0, 0.0, 1.0, 0)

    def test_circle_value_error_negative(self):
        with pytest.raises(ValueError):
            circle_points(0.0, 0.0, 1.0, -1)

    def test_circle_n_equals_one(self):
        pts = circle_points(1.0, 2.0, 3.0, 1)
        assert len(pts) == 1
        assert math.isclose(pts[0][0], 4.0, abs_tol=1e-9)
        assert math.isclose(pts[0][1], 2.0, abs_tol=1e-9)

    def test_circle_n_equals_two(self):
        pts = circle_points(0.0, 0.0, 1.0, 2)
        assert math.isclose(pts[0][0], 1.0, abs_tol=1e-9)
        assert math.isclose(pts[0][1], 0.0, abs_tol=1e-9)
        assert math.isclose(pts[1][0], -1.0, abs_tol=1e-9)
        assert math.isclose(pts[1][1], 0.0, abs_tol=1e-9)

    def test_circle_does_not_affect_octagon(self):
        """La nuova funzione non modifica il comportamento di octagon_points."""
        from kemai_client.geometry import octagon_points
        pts = octagon_points(36.0, 36.0, 10.0)
        assert len(pts) == 16
        cx, cy, r = 36.0, 36.0, 10.0
        angle = math.radians(22.5)
        expected_x = cx + r * math.cos(angle)
        expected_y = cy - r * math.sin(angle)
        assert math.isclose(pts[0], expected_x, abs_tol=1e-9)
        assert math.isclose(pts[1], expected_y, abs_tol=1e-9)
