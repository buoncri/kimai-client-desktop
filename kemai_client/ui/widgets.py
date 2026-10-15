r"""Widget dell'interfaccia grafica.

Formattazione della durata, pulsante Stop a forma di ottagono
disegnato su un `tk.Canvas` (ttk non supporta i poligoni).

Tutte le etichette usate a schermo passano da `i18n.t()`, mai
test hardcoded qui.
"""

import math
from typing import Callable

import tkinter as tk


def format_duration(seconds: int) -> str:
    """Formatta secondi nella stringa `HH:MM:SS`.

    Valori negativi vengono clamped a zero; oltre 99 ore il campo
    ore non va a capo (es. `"100:00:00"`).

    Args:
        seconds: secondi totali da formattare.

    Returns:
        Stringa della forma ``HH:MM:SS``.
    """
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def draw_octagon(canvas: tk.Canvas, cx: float, cy: float, r: float) -> str:
    """Disegna un ottagono regolare su un Canvas.

    I vertici partono da 22,5° e procedono di 45° per giro, in senso
    orario (angolo negativo di *y* perché il sistema di coordinate di
    Tkinter ha l'asse y invertito).

    Args:
        canvas: il Canvas su cui disegnare.
        cx, cy: coordinate del centro.
        r: raggio dell'ottagono.

    Returns:
        L'ID dell'oggetto creato sul Canvas.
    """
    points: list[float] = []
    for i in range(8):
        angle_deg = 22.5 + i * 45  # gradi orari
        angle_rad = angle_deg * math.pi / 180.0
        # Tkinter ha y verso il basso; il segno - rende il senso
        # orario coerente con un orologio analogico.
        x = cx + r * math.cos(angle_rad)
        y = cy - r * math.sin(angle_rad)
        points.extend((x, y))

    return canvas.create_polygon(
        points, fill="#4a90d9", outline="#2c5f9e", width=2
    )


class StopButton(tk.Canvas):
    """Pulsante a forma di ottagono su `tk.Canvas`.

    Usa un Canvas perché `ttk.Button` non disegna poligoni, e la
    fedeltà visiva rispetto al client KEMAI è un requisito.

    Args:
        master: il master Tkinter.
        on_click: callback invocato alla pressione del pulsante.
        width: larghezza (default 72).
        height: altezza (default 72).
    """

    def __init__(
        self,
        master: tk.Misc,
        on_click: Callable[[], None],
        width: int = 72,
        height: int = 72,
    ) -> None:
        super().__init__(master, width=width, height=height, bg="#f0f0f0")
        self._on_click = on_click
        self._label: str = ""

        # Ottagono centrato: raggio leggermente inferiore alla metà
        # per lasciare spazio alla label centrale.
        cx = width / 2
        cy = height / 2
        r = min(cx, cy) * 0.85
        self._octagon_id = draw_octagon(self, cx, cy, r)

        # Etichetta al centro.
        self._text_id = self.create_text(
            cx,
            cy,
            text="",
            font=("", 10),
            fill="#ffffff",
        )

        # Gestione click: bind solo sull'ottagono.
        self.tag_bind(self._octagon_id, "<Button-1>", self._on_press)

    def _on_press(self, event: tk.Event) -> None:
        self._on_click()

    def set_label(self, text: str) -> None:
        """Aggiorna la etichetta al centro dell'ottagono."""
        self._label = text
        self.itemconfig(self._text_id, text=text)

    def set_enabled(self, enabled: bool) -> None:
        """Abilita o disabilita l'aspetto del pulsante.

        Cambia solo i colori: non tocca lo stato del Canvas, perché
        disabilitare un Canvas in Tkinter blocca la consegna di **tutti**
        gli eventi (inclusi quelli legati con tag_bind). Il pulsante
        resta sempre cliccabile anche quando è disabilitato.

        Args:
            enabled: True per l'aspetto normale, False per quello spento.
        """
        if enabled:
            self.itemconfig(self._octagon_id, fill="#4a90d9", outline="#2c5f9e")
            self.itemconfig(self._text_id, fill="#ffffff")
            self.config(bg="#f0f0f0")
        else:
            self.itemconfig(self._octagon_id, fill="#b0b0b0", outline="#888888")
            self.itemconfig(self._text_id, fill="#cccccc")
            self.config(bg="#e0e0e0")
