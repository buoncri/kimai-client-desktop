r"""Fixture condivise della suite.

Un solo `tk.Tk()` per tutta la sessione.

Motivo, non una questione di stile: creare e distruggere root Tkinter in
sequenza rapida fa fallire intermittently `tk.Tk()` con

    _tkinter.TclError: Can't find a usable init.tcl ...

Su Windows il ricaricamento di init.tcl dopo la distruzione di una root
precedente non e' affidabile. Con una root per sessione quel percorso
viene percorso una volta sola invece che una per test.

Prima di questa fixture la suite era gia' instabile (test_widgets.py
creava sei root); i test che costruivano una MainWindow rea l'hanno resa
piu' frequente. Il sintomo e' intermittente per definizione: passa al
primo run e fallisce al terzo.
"""

import sys
import tkinter as tk
from pathlib import Path

import pytest

# `tools/` non e' un pacchetto installato: si aggiunge al path perche' i
# suoi script siano testabili senza trasformarli in libreria.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


@pytest.fixture(scope="session")
def tk_root():
    """Root Tkinter nascosta, condivisa da tutti i test che ne hanno bisogno.

    I test che devono ispezionare i widget devono distruggere quello che
    hanno creato, ma non la root: si occupa teardown della fixture.
    """
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - solo ambienti senza Tcl
        pytest.skip(f"Tkinter non utilizzabile su questa macchina: {exc}")

    root.withdraw()
    try:
        yield root
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass