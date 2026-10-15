r"""Test strutturale della finestra principale.

Verifica solo la struttura: presenza della classe, dei metodi e dei
widget di base. La verifica visiva (layout, colori, posizione) è
**[UMANO]** — Task 12 Step 4.

Questo file non importa Tkinter: le finestre Tk non si testano via
assert su coordinate, ma si importa il modulo e si controlla che
l'API sia esposta.
"""

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

    def test_start_failure_leaves_button_clickable(self):
        """Dopo start() fallita, il controller e' pronto ma non in corso,
        quindi il bottone torna cliccabile (non resta spento)."""
        from unittest.mock import Mock
        ctrl = Mock()
        ctrl.can_start.return_value = True  # non c'e' timesheet
        ctrl.is_running.return_value = False
        win = self._make_window(ctrl)
        win._refresh_state()
        win._stop_button.set_enabled.assert_called_once_with(True)
