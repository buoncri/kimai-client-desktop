"""Composizione dell'applicazione.

Configurazione, controller, finestre e tray.
Entry point: `python -m kemai_client`.

Regola architetture: Tkinter gira solo nel main thread.
pystray parte su un thread daemon (non tiene vivo il processo).
"""

from __future__ import annotations

from pathlib import Path

from kemai_client.config import Config, load, is_configured
from kemai_client.controller import AppController
from kemai_client.logging_setup import setup_logging
from kemai_client.tray import TrayIcon
from kemai_client.ui.main_window import MainWindow
from kemai_client.ui.settings_window import SettingsWindow


def main() -> None:
    """Entry point principale.

    Carica la configurazione, costruisce il controller, le finestre
    e il tray. Se non c'è configurazione, apre la finestra
    Impostazioni dopo 200 ms.
    """
    # Setup logging (idempotente).
    log_path = setup_logging()

    # Carica config (file opzionale, restituisce Config default se manca).
    config = load()

    # Costruisce il controller.
    controller = AppController(config=config)

    # Tkinter root.
    import tkinter as tk

    root = tk.Tk()

    # Se la configurazione non è completa, apre Impostazioni.
    if not is_configured(config):
        opened_settings = False

        def on_saved() -> None:
            nonlocal opened_settings
            opened_settings = True

        settings = SettingsWindow(root, controller, on_saved=on_saved)
        root.after(200, settings._entry_host.focus_set)

        # Dopo che l'utente salva, mostra la finestra principale.
        def _show_main_window() -> None:
            if opened_settings:
                on_open_settings()

        root.after(500, _show_main_window)
    else:
        # Finestra principale.
        def on_open_settings() -> None:
            SettingsWindow(root, controller)

        def on_new_project() -> None:
            from kemai_client.ui.project_dialog import ProjectDialog

            preselected = controller.customer_id
            dialog = ProjectDialog(
                root, controller, preselected_customer=preselected
            )

        MainWindow(root, controller, on_open_settings, on_new_project)

    # Tray vassoio.
    tray = TrayIcon(controller, root)
    tray.start()

    # WM_DELETE_WINDOW: decide tra nascondi (vassoio) o esci (destroy).
    def on_close() -> None:
        import traceback
        from kemai_client.tray import close_behaviour

        behavior = close_behaviour(config.close_to_tray)
        if behavior == "withdraw":
            root.withdraw()
        else:
            # Destroy richiede root.quit() + tray.stop(),
            # altrimenti il thread pystray mantiene vivo il processo.
            tray.stop()
            root.quit()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Main loop.
    root.mainloop()
