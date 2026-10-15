r"""Test della finestra principale.

Due livelli,per scelta:

- `TestMainWindowStructural` non crea nessun oggetto: verifica solo che
  l'API sia esposta.
- `TestRefreshState` costruisce la finestra senza Tkinter
  (`MainWindow.__new__`) per verificare il cablaggio.
- `TestQuitMenuEntries` crea una finestra Tkinter vera e nascolta e
  invoca i menu davvero: e' l'unico modo di provare che le voci "Esci"
  chiamano l'uscita unificata. Funziona senza schermo, perche' con la
  finestra nascosta Tk consegna comunque `invoke()` al comando.

La verifica visiva (layout, colori, posizione) resta **[UMANO]**.
"""

from unittest.mock import Mock

from kemai_client.i18n import t
from kemai_client.ui.main_window import MainWindow


class TestMainWindowStructural:
    """Struttura di MainWindow — senza creare un oggetto reale."""

    def test_main_window_exists(self):
        """La classe MainWindow è importabile."""
        assert MainWindow is not None

    def test_main_window_has_refresh(self):
        """MainWindow ha il metodo refresh."""
        assert hasattr(MainWindow, "refresh")

    def test_main_window_has_start_ticking(self):
        """MainWindow ha il metodo start_ticking."""
        assert hasattr(MainWindow, "start_ticking")


class TestRefreshState:
    """Verifica il contratto di cablaggio di _refresh_state: che argomento
    passa a set_enabled."""

    def _make_window(self, controller):
        from unittest.mock import Mock
        win = MainWindow.__new__(MainWindow)
        win._controller = controller
        win._stop_button = Mock()
        win._entry_started = Mock()
        return win

    def test_button_disabled_when_cascade_incomplete(self):
        """Nessuna selezione → bottone disabilitato."""
        from unittest.mock import Mock
        ctrl = Mock()
        ctrl.can_start.return_value = False
        ctrl.is_running.return_value = False
        win = self._make_window(ctrl)
        win._refresh_state()
        win._stop_button.set_enabled.assert_called_once_with(False)

    def test_button_enabled_when_ready_to_start(self):
        """Cascata completa, nessuna attivita' in corso → bottone abilitato."""
        from unittest.mock import Mock
        ctrl = Mock()
        ctrl.can_start.return_value = True
        ctrl.is_running.return_value = False
        win = self._make_window(ctrl)
        win._refresh_state()
        win._stop_button.set_enabled.assert_called_once_with(True)

    def test_button_enabled_while_running(self):
        """Attivita' in corso, cascata gia' completa (selected) → bottone abilitato.

        Questo e' il test che pinna la issue #1: can_start() restituisce
        False perche' c'e' gia' un timesheet, ma is_running() e' True,
        quindi il bottone deve restare cliccabile per poter fermare.
        """
        from unittest.mock import Mock
        ctrl = Mock()
        ctrl.can_start.return_value = False
        ctrl.is_running.return_value = True
        win = self._make_window(ctrl)
        win._refresh_state()
        win._stop_button.set_enabled.assert_called_once_with(True)

    def test_label_shows_stop_while_running(self):
        """Mentre e' in corso, l'etichetta dice 'Ferma' (btn_stop)."""
        from kemai_client.i18n import t
        from unittest.mock import Mock
        ctrl = Mock()
        ctrl.can_start.return_value = False
        ctrl.is_running.return_value = True
        win = self._make_window(ctrl)
        win._refresh_state()
        win._stop_button.set_label.assert_called_once_with(t("btn_stop"))


class TestQuitMenuEntries:
    """Le voci "Esci" dei menu devono chiamare l'uscita unificata.

    Prima della issue #1 i due "Esci" chiamavano root.quit() direttamente:
    il processo non terminava e il timesheet restava aperto. Qui si
    verifica che la callback passata dal compositore sia quella usata,
    con una finestra Tkinter vera e i menu invocati davvero.
    """

    def _window(self, root):
        ctrl = Mock()
        ctrl.customers = []
        ctrl.projects = []
        ctrl.activities = []
        ctrl.truncated = False
        ctrl.customer_id = None
        ctrl.project_id = None
        ctrl.activity_id = None
        ctrl.can_start.return_value = False
        ctrl.is_running.return_value = False
        ctrl.started_at_label.return_value = ""

        on_quit = Mock()
        win = MainWindow(root, ctrl, Mock(), Mock(), on_quit)
        return win, on_quit

    def _submenu(self, win, label):
        """Sottomenu con l'etichetta data, cercato per nome.

        Non si indicizza a mano: la barra dei menu ha una voce tear-off
        in posizione 0 quando viene creata senza `tearoff=0`, quindi
        gli indici dipendono da come e' stata costruita.
        """
        import tkinter as tk

        bar = win._menu_bar
        for i in range(bar.index("end") + 1):
            try:
                if bar.type(i) != "cascade":
                    continue
                if bar.entrycget(i, "label") == label:
                    return win._root.nametowidget(bar.entrycget(i, "menu"))
            except tk.TclError:
                continue
        raise AssertionError(f"nessuna voce a cascata con etichetta {label!r}")

    def test_file_quit_invokes_the_unified_exit(self, tk_root):
        win, on_quit = self._window(tk_root)
        # File: Nuovo progetto, Impostazioni, separatore, Esci.
        self._submenu(win, t("menu_file")).invoke(3)
        on_quit.assert_called_once()

    def test_edit_quit_invokes_the_unified_exit(self, tk_root):
        win, on_quit = self._window(tk_root)
        self._submenu(win, t("menu_edit")).invoke(0)
        on_quit.assert_called_once()

    def test_quit_entries_do_not_bypass_the_exit_handler(
        self, tk_root, monkeypatch
    ):
        """Nessuna delle due voci deve chiamare root.quit() direttamente."""
        win, on_quit = self._window(tk_root)
        spy = Mock()
        # monkeypatch ripristina da solo: la root e' condivisa.
        monkeypatch.setattr(tk_root, "quit", spy)

        self._submenu(win, t("menu_file")).invoke(3)
        self._submenu(win, t("menu_edit")).invoke(0)

        assert on_quit.call_count == 2, (
            "entrambe le voci devono passare da on_quit"
        )
        spy.assert_not_called()
