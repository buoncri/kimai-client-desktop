r"""Test della finestra impostazioni e del dialog progetto.

Due livelli, per scelta:

- i test strutturali non creano finestre e non importano Tkinter;
- i test di comportamento costruiscono un `SettingsWindow` vero sulla root
  condivisa e verificano che la chiusura venga notificata a chi l'ha aperto.

La notifica conta perche' senza di essa il primo avvio non sa quando
l'utente ha finito con le impostazioni, e finisce in un ciclo che non
termina mai: chiudendo la finestra con X o "Annulla" restava un processo
vivo senza finestra.

La verifica visiva (layout, colori, posizione) resta **[UMANO]**.
"""

from unittest.mock import Mock

from kemai_client.ui.project_dialog import ProjectDialog
from kemai_client.ui.settings_window import SettingsWindow


def _controller():
    """Controller finto con una config gia' compilata."""
    from kemai_client.config import Config

    ctrl = Mock()
    ctrl.config = Config(
        host="https://esempio.local",
        username="prova",
        token="test-token-not-real",
    )
    ctrl.customers = []
    ctrl.apply_config = Mock()
    ctrl.load_customers = Mock()
    ctrl.can_start.return_value = False
    ctrl.is_running.return_value = False
    return ctrl


class TestSettingsWindowCloseNotification:
    """Chiudere le impostazioni deve dire a QUALCUNO l'ha chiuso."""

    def test_cancel_notifies_not_saved(self, tk_root):
        on_closed = Mock()
        win = SettingsWindow(tk_root, _controller(), on_closed=on_closed)

        win.cancel()

        on_closed.assert_called_once_with(False)

    def test_close_button_routes_through_cancel(self, tk_root):
        """La X deve passare da cancel, altrimenti non viene notificato.

        Tkinter registra la callback con il nome del metodo come
        suffisso, quindi il protocol restituito termina con "cancel".
        """
        win = SettingsWindow(tk_root, _controller())

        registered = win._window.protocol("WM_DELETE_WINDOW")

        assert registered.endswith("cancel"), (
            f"la X e' collegata a {registered!r}, non a cancel"
        )

    def test_save_notifies_saved(self, tk_root):
        on_saved = Mock()
        on_closed = Mock()
        win = SettingsWindow(
            tk_root, _controller(), on_saved=on_saved, on_closed=on_closed
        )

        win.save()

        on_saved.assert_called_once()
        on_closed.assert_called_once_with(True)

    def test_notifies_only_once_per_close(self, tk_root):
        """Chiudere due volte non deve far partire due cicli."""
        on_closed = Mock()
        win = SettingsWindow(tk_root, _controller(), on_closed=on_closed)

        win.cancel()
        try:
            win.cancel()
        except Exception:
            # La seconda chiude una finestra gia' distrutta: tollerato,
            # ma la notifica non deve essere raddoppiata.
            pass

        assert on_closed.call_count == 1, (
            f"notifiche emesse: {on_closed.call_count}"
        )

    def test_works_without_callbacks(self, tk_root):
        """Le callback sono facoltative: la finestra resta usabile."""
        win = SettingsWindow(tk_root, _controller())

        win.cancel()


class TestSettingsWindow:
    def test_settings_window_exists(self):
        assert SettingsWindow is not None

    def test_settings_window_has_test_connection(self):
        assert hasattr(SettingsWindow, "test_connection")

    def test_settings_window_has_save(self):
        assert hasattr(SettingsWindow, "save")

    def test_settings_window_has_cancel(self):
        assert hasattr(SettingsWindow, "cancel")


class TestProjectDialog:
    def test_project_dialog_exists(self):
        assert ProjectDialog is not None

    def test_project_dialog_has_result(self):
        assert hasattr(ProjectDialog, "result")

    def test_project_dialog_has_save(self):
        assert hasattr(ProjectDialog, "save")

    def test_project_dialog_has_cancel(self):
        assert hasattr(ProjectDialog, "cancel")