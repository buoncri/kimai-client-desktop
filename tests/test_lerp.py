"""Test della funzione lerp.

Nessuna dipendenza da Tkinter o Pillow: il modulo e' importabile
su una macchina headless.
"""

import math

import pytest

from kemai_client.geometry import lerp


class TestLerp:
    def test_lerp_midpoint(self):
        """t=0.5 -> media dei due estremi."""
        assert lerp(0.0, 10.0, 0.5) == pytest.approx(5.0)

    def test_lerp_at_zero(self):
        """t=0 -> restituisce a."""
        assert lerp(3.0, 7.0, 0.0) == pytest.approx(3.0)

    def test_lerp_at_one(self):
        """t=1 -> restituisce b."""
        assert lerp(3.0, 7.0, 1.0) == pytest.approx(7.0)

    def test_lerp_clamp_below_zero(self):
        """t < 0 -> clamp a 0 -> restituisce a."""
        assert lerp(0.0, 10.0, -1.0) == pytest.approx(0.0)

    def test_lerp_clamp_above_one(self):
        """t > 1 -> clamp a 1 -> restituisce b."""
        assert lerp(0.0, 10.0, 2.0) == pytest.approx(10.0)

    def test_lerp_negative_range(self):
        """Interpolazione su range negativo: [-5, -1]."""
        assert lerp(-5.0, -1.0, 0.5) == pytest.approx(-3.0)

    def test_lerp_same_values(self):
        """a == b -> risultato sempre a (o b)."""
        assert lerp(5.0, 5.0, 0.5) == pytest.approx(5.0)

    def test_lerp_float_return_type(self):
        """Il ritorno e' float anche con input int."""
        result = lerp(0, 10, 0.5)
        assert isinstance(result, float)

    def test_lerp_does_not_affect_octagon(self):
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

    def test_lerp_does_not_affect_circle_points(self):
        """La nuova funzione non modifica il comportamento di circle_points."""
        from kemai_client.geometry import circle_points
        pts = circle_points(0.0, 0.0, 1.0, 4)
        assert len(pts) == 4
        assert math.isclose(pts[0][0], 1.0, abs_tol=1e-9)
        assert math.isclose(pts[0][1], 0.0, abs_tol=1e-9)
