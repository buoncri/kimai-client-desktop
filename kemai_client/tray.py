r"""Sistema tray / vassoio di sistema.

Funzione pura `close_behaviour`: distingue l'uscita pulita ("withdraw")
dal processo zombie ("destroy non terminato"). Testabile senza Tkinter.

`TrayIcon.start()` avvia pystray su un **thread daemon** con
`setup()` + `run_detached()`. Il `daemon=True` è la rete di sicurezza:
se il tray crasha, il processo Python termina comunque.

`root.after(0, fn)`: ogni callback del menu pystray passa dal
thread principale (Tkinter è monothread). Mai toccare widget
dal thread pystray.

L'icona viene generata a runtime con Pillow, senza file binari
nel repository.
"""

from __future__ import annotations

import math
import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw

from kemai_client.i18n import t

# Dimensione icona del vassoio (quadrato).
ICON_SIZE = 64


def close_behaviour(close_to_tray: bool) -> str:
    """Determina il comportamento di chiusura.

    Funzione pura: la correttezza della sua uscita distingue un'uscita
    pulita da un processo zombie invisibile.

    Args:
        close_to_tray: True se l'utente ha selezionato "Chiudi nel vassoio".

    Returns:
        "withdraw" se l'app si nasconde nel vassoio,
        "destroy" se la finestra viene distrutta e il processo termina.
    """
    if close_to_tray:
        return "withdraw"
    return "destroy"


def build_icon() -> Image.Image:
    """Genera un'icona 64×64 a runtime.

    Non crea file sul filesystem: l'icona è un `PIL.Image.Image`
    in memoria, costruita con `ImageDraw`.

    Returns:
        Un'immagine quadrata 64×64 con un piccolo ottagono stilizzato
        al centro.
    """
    img = Image.new("RGB", (ICON_SIZE, ICON_SIZE), color="#4a90d9")
    draw = ImageDraw.Draw(img)

    # Ottagono stilizzato (più piccolo, per l'icona).
    cx, cy = ICON_SIZE / 2, ICON_SIZE / 2
    r = ICON_SIZE * 0.35

    points: list[float] = []
    for i in range(8):
        angle_deg = 22.5 + i * 45
        angle_rad = angle_deg * math.pi / 180.0
        x = cx + r * math.cos(angle_rad)
        y = cy - r * math.sin(angle_rad)
        points.extend((x, y))

    draw.polygon(points, fill="#ffffff")

    return img


class TrayIcon:
    """Gestisce l'icona del vassoio di sistema.

    Avviato su un thread **daemon** (termina con il processo principale).
    I callback del menu passano da `root.after(0, fn)` prima di
    toccare qualsiasi widget.

    Args:
        controller: istanza di AppController.
        root: finestra Tkinter root.
    """

    def __init__(
        self,
        controller,  # AppController
        root: tk.Tk,
    ) -> None:
        self._controller = controller
        self._root = root
        self._menu = build_menu(controller, root)
        self._icon = pystray.Icon(
            "kemai",
            build_icon(),
            menu=self._menu,
            title=t("app_title"),
        )
        self._daemon_thread: threading.Thread | None = None

    def start(self) -> None:
        """Avvia l'icona nel vassoio di sistema.

        Usa `icon.setup()` + `icon.run_detached()` su un thread
        **daemon**. Il `daemon=True` garantisce che un crash del
        tray non tenga vivo il processo.
        """
        self._daemon_thread = threading.Thread(
            target=self._run_detached, daemon=True, name="pystray"
        )
        self._daemon_thread.start()

    def _run_detached(self) -> None:
        """Esegue setup + run_detached, mai run() (bloccante)."""
        self._icon.setup()
        self._icon.run_detached()

    def stop(self) -> None:
        """Ferma l'icona del vassoio."""
        if self._daemon_thread and self._daemon_thread.is_alive():
            self._icon.stop()

    def is_running(self) -> bool:
        return self._daemon_thread is not None and self._daemon_thread.is_alive()


def build_menu(controller, root: tk.Tk) -> pystray.Menu:
    """Costruisce il menu del vassoio.

    Ogni callback passa da `root.after(0, fn)`: arriva sul thread
    pystray, non deve mai toccare widget Tkinter direttamente.

    Args:
        controller: istanza di AppController.
        root: finestra Tkinter root.

    Returns:
        Un `pystray.Menu` con voci "Mostra", "Avvia/Ferma", "Esci".
    """
    import tkinter as tk

    def show_window():
        """Mostra la finestra principale."""
        root.after(0, root.deiconify)

    def toggle_activity():
        """Avvia o ferma l'attività corrente."""
        root.after(0, controller.toggle)

    def quit_app():
        """Esci dal vassoio e termina il processo."""
        root.after(0, root.quit)

    return pystray.Menu(
        pystray.MenuItem(t("tray_show"), show_window, default=True),
        pystray.MenuItem(t("btn_start"), toggle_activity),
        pystray.MenuItem(t("tray_quit"), quit_app),
    )
