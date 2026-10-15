r"""Test della composizione dell'applicazione.

`make_close_handler` è il gestore di WM_DELETE_WINDOW (la X della
finestra). È stato estratto da `main()` perché dentro `main()` non era
raggiungibile da nessun test, ed è proprio lì che si era nascosto un
NameError: `exit_sequence` veniva importata dentro una funzione diversa
e la X non usciva.

Tutti i test girano offline: `root`, `tray` e `controller` sono Mock,
nessuna finestra Tkinter viene creata.
"""

from unittest.mock import Mock, call

from kemai_client.app import make_close_handler


class TestMakeCloseHandlerWithdraw:
    """Ramo withdraw: l'utente ha "Chiudi nel vassoio" attivo.

    Nascondersi NON è uscire: nessuno stop, nessun destroy. Fermare
    l'attività qui farebbe perdere ore di lavoro all'utente.
    """

    def _handler(self):
        controller = Mock()
        controller.is_running.return_value = True
        root = Mock()
        tray = Mock()
        return controller, root, tray, make_close_handler(
            controller, root, tray, True
        )

    def test_withdraw_hides_the_window(self):
        _, root, _, handler = self._handler()

        handler()

        root.withdraw.assert_called_once_with()

    def test_withdraw_does_not_stop_the_timesheet(self):
        controller, _, _, handler = self._handler()

        handler()

        controller.stop.assert_not_called()

    def test_withdraw_does_not_destroy_the_window(self):
        _, root, _, handler = self._handler()

        handler()

        root.destroy.assert_not_called()
        root.quit.assert_not_called()

    def test_withdraw_does_not_stop_the_tray(self):
        _, _, tray, handler = self._handler()

        handler()

        tray.stop.assert_not_called()


class TestMakeCloseHandlerDestroy:
    """Ramo destroy: l'utente ha "Chiudi nel vassoio" disattivato."""

    def _handler(self, is_running=True):
        controller = Mock()
        controller.is_running.return_value = is_running
        root = Mock()
        tray = Mock()
        return controller, root, tray, make_close_handler(
            controller, root, tray, False
        )

    def test_destroy_stops_the_timesheet_when_running(self):
        controller, _, _, handler = self._handler(is_running=True)

        handler()

        controller.stop.assert_called_once_with()

    def test_destroy_destroys_the_window(self):
        _, root, _, handler = self._handler()

        handler()

        root.destroy.assert_called_once_with()

    def test_destroy_does_not_withdraw(self):
        _, root, _, handler = self._handler()

        handler()

        root.withdraw.assert_not_called()

    def test_destroy_runs_the_full_order(self):
        """Ordine non negoziabile: stop, tray, quit, destroy.

        Chiudere il vassoio dopo destroy lascia vivo il thread daemon
        di pystray, che è il difetto che questo intervento corregge.
        """
        order = []

        controller = Mock()
        controller.is_running.return_value = True
        controller.stop.side_effect = lambda: order.append("stop")
        root = Mock()
        root.quit.side_effect = lambda: order.append("quit")
        root.destroy.side_effect = lambda: order.append("destroy")
        tray = Mock()
        tray.stop.side_effect = lambda: order.append("tray")

        make_close_handler(controller, root, tray, False)()

        assert order == ["stop", "tray", "quit", "destroy"], (
            f"Ordine sbagliato: {order}"
        )