r"""Test del modulo exit_sequence: il percorso unico di uscita.

Nessun Tkinter: usiamo Mock per controller, root e tray.
L'ordine delle chiamate e' il cuore del test.

Gli errori non devono solo "non propagare": devono finire nel log.
Swallowarli in silenzio e' esattamente il difetto che questo modulo
corregge (un vassoio che muore in silenzio tiene vivo il processo senza
lasciare traccia), quindi anche quello e' testato.
"""

import logging
from unittest.mock import Mock

from kemai_client.api.errors import KimaiAuthError, KimaiNetworkError
from kemai_client.exit_handler import exit_sequence

LOGGER = "kimai"


def _record_order() -> tuple[Mock, Mock, Mock, list]:
    """Controller/root/tray che appendono il proprio nome a `called`."""
    called: list = []
    controller = Mock()
    controller.is_running.return_value = True
    controller.stop = Mock(side_effect=lambda: called.append("stop"))
    root = Mock(
        quit=Mock(side_effect=lambda: called.append("quit")),
        destroy=Mock(side_effect=lambda: called.append("destroy")),
    )
    tray = Mock(stop=Mock(side_effect=lambda: called.append("tray_stop")))
    return controller, root, tray, called


class TestExitSequenceStopsRunning:
    """Comportamento normale di exit_sequence."""

    def test_exit_sequence_stops_running_timesheet(self):
        """Se is_running e' True, chiama controller.stop()."""
        controller, root, tray, _ = _record_order()
        controller.stop = Mock()

        exit_sequence(controller, root, tray)

        controller.stop.assert_called_once()

    def test_exit_sequence_does_not_stop_when_idle(self):
        """Se is_running e' False, non tocca il controller."""
        controller, root, tray, _ = _record_order()
        controller.is_running.return_value = False
        controller.stop = Mock()

        exit_sequence(controller, root, tray)

        controller.stop.assert_not_called()

    def test_exit_sequence_stops_tray_before_destroying(self):
        """L'ordine e': stop, tray_stop, quit, destroy.

        Chiudere il vassoio dopo destroy lascia il thread daemon vivo.
        """
        controller, root, tray, called = _record_order()

        exit_sequence(controller, root, tray)

        assert called == ["stop", "tray_stop", "quit", "destroy"], (
            f"ordine errato: {called}"
        )


class TestExitSequenceSurvivesErrors:
    """Errori non propagano: root.destroy e' comunque chiamato."""

    def test_exit_sequence_survives_auth_error_on_stop(self, caplog):
        """Token scaduto (401): non propaga, esce e registra nel log."""
        controller, root, tray, called = _record_order()
        controller.stop = Mock(
            side_effect=KimaiAuthError("token scaduto", status=401)
        )

        with caplog.at_level(logging.WARNING, logger=LOGGER):
            exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called
        assert any("stop_timesheet" in r.message for r in caplog.records), (
            "l'errore di stop deve finire nel log, non essere scartato"
        )

    def test_exit_sequence_survives_network_error_on_stop(self, caplog):
        """Rete caduta: non propaga, esce e registra nel log."""
        controller, root, tray, called = _record_order()
        controller.stop = Mock(side_effect=KimaiNetworkError("rete caduta"))

        with caplog.at_level(logging.WARNING, logger=LOGGER):
            exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called
        assert any("stop_timesheet" in r.message for r in caplog.records), (
            "l'errore di stop deve finire nel log, non essere scartato"
        )

    def test_exit_sequence_survives_unexpected_error_on_stop(self, caplog):
        """Errore non-Kimai da stop(): non propaga, esce e registra nel log."""
        controller, root, tray, called = _record_order()
        controller.stop = Mock(side_effect=RuntimeError("stop imprevisto"))

        with caplog.at_level(logging.WARNING, logger=LOGGER):
            exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called
        assert any("stop_timesheet" in r.message for r in caplog.records), (
            "l'errore di stop deve finire nel log, non essere scartato"
        )

    def test_exit_sequence_survives_tray_failure(self, caplog):
        """Tray.stop solleva: si esce lo stesso, ma il log registra."""
        controller, root, tray, called = _record_order()
        tray.stop = Mock(side_effect=RuntimeError("tray crash"))

        with caplog.at_level(logging.WARNING, logger=LOGGER):
            exit_sequence(controller, root, tray)

        assert "quit" in called
        assert "destroy" in called
        assert any("tray_stop" in r.message for r in caplog.records), (
            "un vassoio che muore in silenzio tiene vivo il processo: "
            "l'errore deve finire nel log"
        )


class TestExitSequenceNeverSkipsDestroy:
    """destroy e' l'ultimo passo e nessun errore puo' impedirlo."""

    def test_destroy_is_called_even_when_tray_raises_base_exception(self):
        """Anche un'eccezione non Kimai dal vassoio non blocca l'uscita."""
        controller, root, tray, called = _record_order()
        tray.stop = Mock(side_effect=OSError("handle gia' chiuso"))

        exit_sequence(controller, root, tray)

        assert called[-1] == "destroy", f"ordine errato: {called}"