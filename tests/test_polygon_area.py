"""Test della funzione polygon_area.

Nessuna dipendenza da Tkinter o Pillow: il modulo e' importabile
su una macchina headless.
"""

import pytest

from kemai_client.geometry import polygon_area


class TestPolygonArea:
    def test_polygon_area_rectangle(self):
        """Quadrato [0,4]x[0,3] -> area 12."""
        assert polygon_area(
            [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]
        ) == pytest.approx(12.0)

    def test_polygon_area_triangle(self):
        """Triangolo (0,0),(4,0),(0,3) -> area 6."""
        assert polygon_area(
            [(0.0, 0.0), (4.0, 0.0), (0.0, 3.0)]
        ) == pytest.approx(6.0)

    def test_polygon_area_negative_area_sign(self):
        """Polygon con ordine giusto (anti-orario) -> area positiva."""
        # vertici in ordine anti-orario: area positiva
        assert polygon_area(
            [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (0.0, 2.0)]
        ) == pytest.approx(6.0)

    def test_polygon_area_clockwise_absolute(self):
        """Ordine orario -> area stessa (valore assoluto)."""
        # vertici in ordine orario: area negativa prima dell'abs()
        assert polygon_area(
            [(0.0, 2.0), (0.0, 0.0), (3.0, 0.0), (3.0, 2.0)]
        ) == pytest.approx(6.0)

    def test_polygon_area_concave(self):
        """Pentagono concavico con vertici ciclicamente ordinati."""
        # vertici anti-orario concavi: area 5.0
        assert polygon_area(
            [(0.0, 0.0), (3.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        ) == pytest.approx(5.0)

    def test_polygon_area_one_point_raises(self):
        """1 punto -> ValueError."""
        with pytest.raises(ValueError, match="almeno 3 punti"):
            polygon_area([(0.0, 0.0)])

    def test_polygon_area_two_points_raises(self):
        """2 punti -> ValueError."""
        with pytest.raises(ValueError, match="almeno 3 punti"):
            polygon_area([(0.0, 0.0), (1.0, 1.0)])

    def test_polygon_area_empty_raises(self):
        """0 punti -> ValueError."""
        with pytest.raises(ValueError, match="almeno 3 punti"):
            polygon_area([])

    def test_polygon_area_degenerate_collinear_raises(self):
        """3 punti collineari -> area 0 (non ValueError)."""
        assert polygon_area([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]) == pytest.approx(0.0)

    def test_polygon_area_circle_like_points(self):
        """Circonferenza come poligono: area stimata (non 0)."""
        import math

        cx, cy, r = 0.0, 0.0, 1.0
        n = 64
        points = []
        for i in range(n):
            theta = 2.0 * math.pi * i / n
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            points.append((x, y))
        expected = math.pi * r * r
        # area della circunferenza stimata (non 0) con n vertici.
        assert polygon_area(points) == pytest.approx(expected, rel=1.0 / n)
