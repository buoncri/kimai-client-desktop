r"""Test dei widget dell'interfaccia.

format_duration: formattazione pura, nessun Tkinter necessario.
StopButton: geometria dell'ottagono, verificata con un Canvas iniettato.

Nessun test apre socket, nessun test richiede istanza Kimai reale.

La root Tkinter arriva dalla fixture `tk_root` (tests/conftest.py): e'
una sola per tutta la sessione, perche' crearne e distruggerne diverse in
sequenza fa fallire `tk.Tk()` in modo intermittente con "Can't find a
usable init.tcl". I test distruggono il Canvas che hanno creato, la root
la distrugge la fixture.
"""

import math
import tkinter as tk
from unittest.mock import Mock

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

    def test_octagon_has_eight_points(self, tk_root):
        canvas = tk.Canvas(tk_root, width=100, height=100)
        canvas.pack()
        try:
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
        finally:
            canvas.destroy()

    def test_octagon_starts_at_22dot5_degrees(self, tk_root):
        """Il primo vertice si trova a esattamente 22,5° dall'asse X."""
        canvas = tk.Canvas(tk_root, width=100, height=100)
        canvas.pack()
        try:
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
                a1 = math.degrees(
                    math.atan2(coords[2 * (i - 1) + 1] - 50, coords[2 * (i - 1)] - 50)
                )
                a2 = math.degrees(math.atan2(coords[2 * i + 1] - 50, coords[2 * i] - 50))
                step = abs(a2 - a1)
                # Potrebbe essere 315° → 22,5° (wrap) → differenza 45.
                assert abs(step - 45) < 0.01 or abs(step - 315) < 0.01, (
                    f"Step tra vertici {i - 1} e {i}: {step}° (atteso 45°)"
                )
        finally:
            canvas.destroy()

    def test_octagon_is_not_4_sides(self, tk_root):
        """Sicurezza: non confondere l'ottagono con un quadrato (4 vertici)."""
        canvas = tk.Canvas(tk_root, width=100, height=100)
        canvas.pack()
        try:
            item_id = draw_octagon(canvas, 50, 50, 40)
            coords = canvas.coords(item_id)
            # 4 vertici → 8 coordinate; 8 vertici → 16 coordinate.
            assert len(coords) == 16, f"Solo {len(coords) // 2} vertici, non 8"
        finally:
            canvas.destroy()


class TestStopButtonEnabled:
    """Verifica che set_enabled non disabiliti il Canvas intero.

    Un Canvas con `state="disabled"` smette di consegnare qualunque
    evento, anche quelli gia' legati con `tag_bind`: e' il modo in cui
    il pulsante Ferma diventava inutilizzabile mentre l'attivita' girava.
    """

    def _build(self, root):
        return StopButton(root, on_click=Mock())

    def test_set_enabled_false_keeps_canvas_normal(self, tk_root):
        btn = self._build(tk_root)
        try:
            btn.set_enabled(False)
            assert str(btn.cget("state")) == "normal", (
                f"stato={btn.cget('state')}: il Canvas disabilitato blocca gli eventi"
            )
        finally:
            btn.destroy()

    def test_set_enabled_false_repaints_grey(self, tk_root):
        btn = self._build(tk_root)
        try:
            btn.set_enabled(False)
            fill = btn.itemcget(btn._octagon_id, "fill")
            assert fill == "#b0b0b0", f"fill={fill} (atteso #b0b0b0)"
        finally:
            btn.destroy()

    def test_set_enabled_true_restores_fill(self, tk_root):
        btn = self._build(tk_root)
        try:
            btn.set_enabled(False)
            btn.set_enabled(True)
            fill = btn.itemcget(btn._octagon_id, "fill")
            assert fill == "#4a90d9", f"fill={fill} (atteso #4a90d9)"
        finally:
            btn.destroy()

    def test_disabled_button_still_delivers_clicks(self, tk_root):
        """Il colore grigio non deve spegnere i binding.

        E' il contratto che permette al controller di decidere cosa fare
        del click invece di affidarsi a Tkinter.

        Si verifica lo stato del widget e non la consegna dell'evento:
        `event_generate` su un Canvas dentro una finestra nascosta non
        arriva al `tag_bind` (manca la geometria mappata), quindi
        asserire sul callback darebbe un test che passa o fallisce per
        ragioni di backend e non per ragioni di codice. Lo stato
        `normal` e' la condizione necessaria perché l'evento arrivi.
        """
        btn = StopButton(tk_root, on_click=Mock())
        try:
            btn.set_enabled(False)
            state = str(btn.cget("state"))
        finally:
            btn.destroy()

        assert state == "normal", (
            "un Canvas disabled non consegna piu' nessun evento, nemmeno "
            "quelli gia' legati: il pulsante diventerebbe inutilizzabile"
        )