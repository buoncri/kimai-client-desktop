r"""Test del modulo exit_sequence: il percorso unico di uscita.

Nessun Tkinter: usiamo Mock per controller, root e tray.
L'ordine delle chiamate e' il cuore del test.
"""

from kemai_client.api.errors import KimaiAuthError, KimaiNetworkError
from kemai_client.exit_handler import exit_sequence


class TestExitSequenceStopsRunning:
    """Comportamento normale di exit_sequence."""

    def test_exit_sequence_stops_running_timesheet(self):
        """Se is_running e' True, chiama controller.stop()."""
        from unittest.mock import Mock

        controller = Mock()
        controller.is_running.return_value = True
        controller.stop = Mock()

        root = Mock()
        root.quit = Mock()
        root.destroy = Mock()

        tray = Mock()
        tray.stop = Mock()

        exit_sequence(controller, root, tray)
        controller.stop.assert_called_once()

    def test_exit_sequence_does_not_stop_when_idle(self):
        """Se is_running e' False, non tocca il controller."""
        from unittest.mock import Mock

        controller = Mock()
        controller.is_running.return_value = False
        controller.stop = Mock()

        root = Mock()
        root.quit = Mock()
        root.destroy = Mock()

        tray = Mock()
        tray.stop = Mock()

        exit_sequence(controller, root, tray)
        controller.stop.assert_not_called()

    def test_exit_sequence_stops_tray_before_destroying(self):
        """L'ordine e': stop, tray_stop, quit, destroy.

        Chiudere il vassoio dopo destroy lascia il thread daemon vivo.
        """
        from unittest.mock import Mock

        called = []

        controller = Mock()
        controller.is_running.return_value = True
        controller.stop = Mock(side_effect=lambda: called.append("stop") or None)

        root = Mock(quit=Mock(side_effect=lambda: called.append("quit") or None),
                    destroy=Mock(side_effect=lambda: called.append("destroy") or None))

        tray = Mock(stop=Mock(side_effect=lambda: called.append("tray_stop") or None))

        exit_sequence(controller, root, tray)

        assert called == ["stop", "tray_stop", "quit", "destroy"], (
            f"ordine errato: {called}"
        )


class TestExitSequenceSurvivesErrors:
    """Errori non propagano: root.destroy e' comunque chiamato."""

    def test_exit_sequence_survives_auth_error_on_stop(self):
        """Token scaduto (401): non propaga, root.destroy e' comunque chiamato."""
        from unittest.mock import Mock

        called = []

        controller = Mock()
        controller.is_running.return_value = True

        def fail_auth():
            raise KimaiAuthError("token scaduto", status=401)

        controller.stop = Mock(side_effect=fail_auth)

        root = Mock(
            quit=Mock(side_effect=lambda: called.append("quit")),
            destroy=Mock(side_effect=lambda: called.append("destroy")),
        )
        tray = Mock(stop=Mock(side_effect=lambda: called.append("tray_stop")))

        # Non deve propagare
        exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called

    def test_exit_sequence_survives_network_error_on_stop(self):
        """Rete caduta (KimaiNetworkError): non propaga, root.destroy e' chiamato."""
        from unittest.mock import Mock

        called = []

        controller = Mock()
        controller.is_running.return_value = True

        def fail_network():
            raise KimaiNetworkError("rete caduta")

        controller.stop = Mock(side_effect=fail_network)

        root = Mock(
            quit=Mock(side_effect=lambda: called.append("quit")),
            destroy=Mock(side_effect=lambda: called.append("destroy")),
        )
        tray = Mock(stop=Mock(side_effect=lambda: called.append("tray_stop")))

        exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called

    def test_exit_sequence_survives_tray_failure(self):
        """Tray.stop solleva: root.quit e destroy sono comunque raggiunti."""
        from unittest.mock import Mock

        called = []

        controller = Mock()
        controller.is_running.return_value = False
        controller.stop = Mock()

        root = Mock(
            quit=Mock(side_effect=lambda: called.append("quit")),
            destroy=Mock(side_effect=lambda: called.append("destroy")),
        )
        tray = Mock(
            stop=Mock(side_effect=RuntimeError("tray crash"))
        )

        exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called
