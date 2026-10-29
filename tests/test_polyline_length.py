"""Test della funzione polyline_length.

Nessuna dipendenza da Tkinter o Pillow: il modulo e' importabile
su una macchina headless.
"""

import math

import pytest

from kemai_client.geometry import polyline_length


class TestPolylineLength:
    def test_polyline_length_two_points(self):
        """2 punti -> distanza euclidea."""
        assert polyline_length([(0.0, 0.0), (3.0, 4.0)]) == pytest.approx(5.0)

    def test_polyline_length_three_points(self):
        """3 punti -> somma di 2 segmenti."""
        assert polyline_length([(0, 0), (1, 0), (1, 1)]) == pytest.approx(2.0)

    def test_polyline_length_one_point_raises(self):
        """1 punto -> ValueError."""
        with pytest.raises(ValueError, match="almeno 2 punti"):
            polyline_length([(0.0, 0.0)])

    def test_polyline_length_zero_points_raises(self):
        """0 punti -> ValueError."""
        with pytest.raises(ValueError, match="almeno 2 punti"):
            polyline_length([])

    def test_polyline_length_coincident_points(self):
        """Punti coincidenti -> lunghezza 0."""
        assert polyline_length([(1.0, 1.0), (1.0, 1.0)]) == pytest.approx(0.0)

    def test_polyline_length_negative_coords(self):
        """Coordinate negative."""
        assert polyline_length([(-1.0, -1.0), (1.0, 1.0)]) == pytest.approx(
            math.sqrt(8.0)
        )

    def test_polyline_length_precision(self):
        """Precisione floating point."""
        pts = [(0.0, 0.0), (0.1, 0.1)]
        result = polyline_length(pts)
        assert result == pytest.approx(math.sqrt(0.02), rel=1e-12)

    def test_polyline_length_horizontal(self):
        """Segmento orizzontale."""
        assert polyline_length([(0.0, 5.0), (10.0, 5.0)]) == pytest.approx(10.0)

    def test_polyline_length_vertical(self):
        """Segmento verticale."""
        assert polyline_length([(3.0, 0.0), (3.0, 7.0)]) == pytest.approx(7.0)

    def test_polyline_length_circle_n8(self):
        """Spezzata su cerchio n=8: somma ~ 2*pi*r."""
        from kemai_client.geometry import circle_points
        pts = circle_points(0.0, 0.0, 1.0, 8)
        length = polyline_length(pts)
        # 8 punti -> 7 segmenti, ognuno di angolo 45° (chord 2*sin(pi/8)): somma = 7 * 2*sin(pi/8)
        expected = 7.0 * 2.0 * math.sin(math.pi / 8.0)
        assert length == pytest.approx(expected, rel=1e-12)
        assert length < 2 * math.pi  # la spezzata e sempre piu corta della circonferenza
