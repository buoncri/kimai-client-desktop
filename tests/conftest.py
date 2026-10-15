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

import os
import sys
import tempfile
import tkinter as tk
from pathlib import Path

import pytest

# `tools/` non e' un pacchetto installato: si aggiunge al path perche' i
# suoi script siano testabili senza trasformarli in libreria.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


@pytest.fixture(scope="session", autouse=True)
def isolated_appdata():
    """Sposta %APPDATA% in una cartella temporanea per tutta la sessione.

    `kemai_client.config.default_path()` costruisce il percorso della
    configurazione da %APPDATA%. Senza questo, un test che chiama
    `SettingsWindow.save()` finisce per scrivere la configurazione
    REALE dell'utente: e' successo, e ha sostituito un token valido con
    `test-token-not-real`.

    Il file di log segue lo stesso percorso, quindi anche quello viene
    isolato. Con questa fixture, qualsiasi test puo' scrivere la config
    senza reale: scrive in una cartella che sparisce a fine sessione.
    """
    with tempfile.TemporaryDirectory(prefix="kimai_test_appdata_") as tmp:
        original = os.environ.get("APPDATA")
        os.environ["APPDATA"] = tmp
        try:
            yield Path(tmp)
        finally:
            if original is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = original


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