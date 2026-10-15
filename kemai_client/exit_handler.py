r"""Percorso unico di uscita: ferma il timesheet, il vassoio, il processo.

Chiamato da tre voci di menu (File, Modifica, tray). Garantisce che
l'uscita non lasci il processo vivo nel vassoio o un timesheet aperto.

Ordine delle operazioni (non negoziabile):
    1. controller.stop() se in corso (cattura KimaiError, non propaga).
    2. tray.stop() (cattura qualsiasi eccezione, non propaga).
    3. root.quit()
    4. root.destroy()

La gestione di root e' separata dall'errore di stop:
un'uscita che si blocca a causa della rete e' peggio di un'uscita
senza chiusura del timesheet.

Nessun messaggio per l'utente: gli errori di stop finiscono nel log.
"""

from __future__ import annotations

import logging
from typing import Any

from kemai_client.api.errors import KimaiError
from kemai_client.logging_setup import log_exception

logger = logging.getLogger("kimai")


def exit_sequence(controller: Any, root: Any, tray: Any) -> None:
    """Esegue la sequenza di chiusura: stop timesheet, tray, destroy.

    Ordine: stop() -> tray.stop() -> quit() -> destroy().
    Non interrompe la sequenza per errori del server o del tray.

    Args:
        controller: oggetto con is_running() e stop().
        root: oggetto Tk root con quit() e destroy().
        tray: oggetto TrayIcon con stop().
    """
    # (1) Ferma il timesheet se in corso.
    if controller.is_running():
        try:
            controller.stop()
        except KimaiError as exc:
            # Errore (401, rete, ...): log e continua.
            log_exception(logger, exc, "stop_timesheet")

    # (2) Ferma il vassoio: non interrompere la sequenza.
    try:
        tray.stop()
    except Exception:
        pass  # Il vassoio potrebbe gi'a essere morto.
    root.quit()
    root.destroy()
