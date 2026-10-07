r"""Test dei widget dell'interfaccia.

format_duration: formattazione pura, nessun Tkinter necessario.
StopButton: geometria dell'ottagono, verificata con un Canvas iniettato.

Nessun test apre socket, nessun test richiede istanza Kimai reale.
"""

import math

from kemai_client.ui.widgets import (
    StopButton,
    draw_octagon,
    format_duration,
)


class TestFormatDuration:
    def test_format_zero(self):
        assert format_duration(0) == "00:00:00"

    def test_format_six_seconds(self):
        assert format_duration(6) == "00:00:06"

    def test_format_one_hour(self):
        assert format_duration(3661) == "01:01:01"

    def test_format_over_99_hours(self):
        # Oltre 99 ore non vanno a capo: 360000 secondi = 100h.
        assert format_duration(360000) == "100:00:00"

    def test_format_negative_is_clamped(self):
        # Valori negativi diventano zero.
        assert format_duration(-5) == "00:00:00"


class TestOctagon:
    """Verifica che draw_octagon generi esattamente 8 vertici con
    partenza a 22,5° e passo 45°."""

    def test_octagon_has_eight_points(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=100, height=100)
        canvas.pack()
        item_id = draw_octagon(canvas, 50, 50, 40)
        # getcoords restituisce una tupla: (x0, y0, x1, y1, ..., xN, yN).
        coords = canvas.coords(item_id)
        # 8 vertici → 16 coordinate.
        assert len(coords) == 8 * 2
        # La distanza radiale da (50, 50) a ogni vertice deve essere
        # esattamente il raggio passato.
        cx, cy = 50.0, 50.0
        r = 40.0
        for i in range(0, len(coords), 2):
            dx = coords[i] - cx
            dy = coords[i + 1] - cy
            dist = math.sqrt(dx * dx + dy * dy)
            assert abs(dist - r) < 1e-9, (
                f"Punto {i // 2} troppo lontano: {dist} != {r}"
            )
        canvas.destroy()
        root.destroy()

    def test_octagon_starts_at_22dot5_degrees(self):
        """Il primo vertice si trova a esattamente 22,5° dall'asse X."""
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=100, height=100)
        canvas.pack()
        draw_octagon(canvas, 50, 50, 40)
        coords = canvas.coords(canvas.find_all()[0])
        first_x = coords[0]
        first_y = coords[1]
        # Angolo = atan2(y - cy, x - cx)
        angle_rad = math.atan2(first_y - 50, first_x - 50)
        angle_deg = math.degrees(angle_rad)
        # Deve essere -22,5° (Tkinter inverte l'asse y).
        assert abs(angle_deg + 22.5) < 0.1, (
            f"Angolo primo vertice: {angle_deg}° (atteso 22,5°)"
        )
        # Step tra vertici consecutivi deve essere 45°.
        for i in range(1, 8):
            a1 = math.degrees(math.atan2(coords[2 * (i - 1) + 1] - 50, coords[2 * (i - 1)] - 50))
            a2 = math.degrees(math.atan2(coords[2 * i + 1] - 50, coords[2 * i] - 50))
            step = abs(a2 - a1)
            # Potrebbe essere 315° → 22,5° (wrap) → differenza 45.
            assert abs(step - 45) < 0.01 or abs(step - 315) < 0.01, (
                f"Step tra vertici {i-1} e {i}: {step}° (atteso 45°)"
            )
        canvas.destroy()
        root.destroy()

    def test_octagon_is_not_4_sides(self):
        """Sicurezza: non confondere l'ottagono con un quadrato (4 vertici)."""
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=100, height=100)
        canvas.pack()
        item_id = draw_octagon(canvas, 50, 50, 40)
        coords = canvas.coords(item_id)
        # 4 vertici → 8 coordinate; 8 vertici → 16 coordinate.
        assert len(coords) == 16, f"Solo {len(coords) // 2} vertici, non 8"
        canvas.destroy()
        root.destroy()
