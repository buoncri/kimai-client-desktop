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
from kemai_client.exit_handler import exit_sequence
from kemai_client.i18n import t
from kemai_client.logging_setup import setup_logging
from kemai_client.tray import TrayIcon, close_behaviour
from kemai_client.ui.main_window import MainWindow
from kemai_client.ui.settings_window import SettingsWindow


def make_close_handler(controller, root, tray, close_to_tray: bool):
    """Costruisce il gestore di WM_DELETE_WINDOW (la X della finestra).

    Vive a livello di modulo, e non dentro `main()`, perche' sia
    raggiungibile da un test: quando stava dentro `main()` chiamava
    `exit_sequence` senza importarla, e la X non usciva dal tutto.

    Args:
        controller: istanza di AppController.
        root: finestra Tkinter root.
        tray: istanza di TrayIcon.
        close_to_tray: True se l'utente ha scelto "Chiudi nel vassoio".

    Returns:
        Callable senza argomenti da passare a `root.protocol`.
    """
    behavior = close_behaviour(close_to_tray)

    def on_close() -> None:
        if behavior == "withdraw":
            # Nascondersi NON e' uscire: l'attivita' deve continuare a
            # girare e il processo deve restare vivo nel vassoio.
            root.withdraw()
        else:
            exit_sequence(controller, root, tray)

    return on_close


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
    # Il titolo va impostato SEMPRE, non solo nel ramo configurato:
    # al primo avvio la root nasce con il titolo di default 'tk'.
    root.title(t("app_title"))

    # Le callback condivise dai due percorsi di avvio, definite PRIMA
    # del ramo condizionale: nel flusso precedente on_open_settings
    # viveva solo nel ramo else, e _show_main_window del primo avvio
    # la chiamava generando un NameError inghiottito da Tkinter.
    def on_open_settings() -> None:
        SettingsWindow(root, controller)

    def on_new_project() -> None:
        from kemai_client.ui.project_dialog import ProjectDialog

        preselected = controller.customer_id
        ProjectDialog(root, controller, preselected_customer=preselected)

    def on_quit() -> None:
        exit_sequence(controller, root, tray)

    def _start_main_window() -> None:
        # Costruisce la finestra principale. Chiamata subito se configurati,
        # oppure dopo il salvataggio delle impostazioni al primo avvio.
        MainWindow(root, controller, on_open_settings, on_new_project, on_quit)

    # Se la configurazione non è completa, apre Impostazioni.
    if not is_configured(config):
        saved = {"ok": False}

        def on_saved() -> None:
            saved["ok"] = True

        settings = SettingsWindow(root, controller, on_saved=on_saved)
        root.after(200, settings._entry_host.focus_set)

        # Dopo il salvataggio, apre la finestra principale: ora la
        # configurazione esiste e il controller puo' parlare col server.
        def _open_main_when_saved() -> None:
            if saved["ok"]:
                _start_main_window()
            else:
                root.after(300, _open_main_when_saved)

        root.after(500, _open_main_when_saved)
    else:
        _start_main_window()

    # Tray vassoio.
    tray = TrayIcon(controller, root)
    tray.start()

    # WM_DELETE_WINDOW: decide tra nascondi (vassoio) o esci (destroy).
    root.protocol(
        "WM_DELETE_WINDOW", make_close_handler(controller, root, tray, config.close_to_tray)
    )

    # Main loop.
    root.mainloop()
