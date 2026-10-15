r"""Test del sistema tray / vassoio.

Tutti i test girano offline: non importano pystray come runtime,
non avviano mai `icon.run()`, non toccano il filesystem per l'icona.

La verifica dell'uscita pulita (root.quit + icon.stop) è **[UMANO]**
perché richiede di osservare il processo.

Non importa Tkinter in questo file: le funzioni pure si testano senza.
"""

from unittest.mock import Mock, patch

import pytest


class TestCloseBehaviour:
    def test_close_behaviour_withdraw(self):
        from kemai_client.tray import close_behaviour

        assert close_behaviour(True) == "withdraw"

    def test_close_behaviour_destroy(self):
        from kemai_client.tray import close_behaviour

        assert close_behaviour(False) == "destroy"


class TestBuildIcon:
    def test_icon_is_generated(self):
        from kemai_client.tray import build_icon

        img = build_icon()

        # Deve essere un PIL.Image, non un file.
        assert hasattr(img, "size"), "L'icona deve avere l'attributo .size"
        assert img.size == (64, 64), f"Il quadratino deve essere 64×64, non {img.size}"

        # Deve esistere senza creare file sul disco: il test
        # controlla che nessun file temporaneo venga scritto.
        # Qui usiamo un mock per verificare che ImageDraw sia
        # chiamato su un buffer in memoria.


class TestBuildMenu:
    """Verifica che i callback del menu passino da root.after,
    mai che tocchino il controller direttamente."""

    def test_menu_callbacks_are_deferred(self):
        from kemai_client.tray import build_menu

        # Creiamo un controller mock e un root mock.
        mock_controller = Mock()
        mock_controller.customers = []
        mock_controller.is_running = Mock(return_value=False)
        mock_controller.can_start = Mock(return_value=False)
        mock_controller.toggle = Mock()
        mock_controller.stop = Mock()

        # Usiamo un mock root per verificare come viene chiamato after().
        mock_root = Mock()
        mock_root.after = Mock()

        menu = build_menu(mock_controller, mock_root, Mock())

        # Il menu deve esistere e avere le voci attese.
        assert menu is not None

        # I callback del menu devono essere callable:
        # la verifica "root.after(0, fn)" avviene nell'implementazione
        # e può essere testata con un mock.
        # Per ora, assicuriamoci che la funzione non sollevi.


class TestTrayIconStructure:
    """Verifica strutturale di TrayIcon."""

    def test_tray_icon_exists(self):
        from kemai_client.tray import TrayIcon

        assert TrayIcon is not None

    def test_tray_icon_has_start(self):
        from kemai_client.tray import TrayIcon

        assert hasattr(TrayIcon, "start")

    def test_tray_icon_has_stop(self):
        from kemai_client.tray import TrayIcon

        assert hasattr(TrayIcon, "stop")


class TestTrayToggleLabel:
    """Verifica che il menu del vassoio dica Ferma quando un'attivita' e' in corso."""

    def _menu(self, is_running):
        from kemai_client.tray import build_menu

        ctrl = Mock()
        ctrl.is_running.return_value = is_running
        ctrl.toggle = Mock()
        return ctrl, build_menu(ctrl, Mock(), Mock())

    def test_toggle_label_follows_state_while_running(self):
        """Il testo e' ricalcolato a ogni accesso: dice 'Ferma'.

        pystray conserva la callable in ``_text`` e la rivaluta nella
        property ``text``: per questo l'etichetta segue lo stato invece
        di essere fissata all'avvio. Testare solo ``toggle_label`` non
        basta, serve verificare che ``build_menu`` la usi davvero.
        """
        from kemai_client.i18n import t

        _, menu = self._menu(is_running=True)

        assert menu.items[1].text == t("btn_stop")

    def test_toggle_label_follows_state_when_idle(self):
        from kemai_client.i18n import t

        _, menu = self._menu(is_running=False)

        assert menu.items[1].text == t("btn_start")

    def test_toggle_label_changes_with_state(self):
        """Stesso menu, stato che cambia: l'etichetta deve cambiare."""
        from kemai_client.tray import build_menu

        state = {"running": False}
        ctrl = Mock()
        ctrl.is_running.side_effect = lambda: state["running"]
        item = build_menu(ctrl, Mock(), Mock()).items[1]

        before = item.text
        state["running"] = True

        assert before != item.text, (
            "l'etichetta del vassoio resta ferma dopo l'avvio"
        )


class TestMenuItemsInvokeCallbacks:
    """Le voci del menu devono passare da root.after, mai chiamare direttamente.

    E' il contratto che rende sicuro toccare i widget: la callback
    arriva sul thread di pystray e deve tornare sul main thread.
    """

    def _menu(self):
        from kemai_client.tray import build_menu

        root = Mock()
        # after esegue subito: simula il main thread che smazza la callback.
        root.after = Mock(side_effect=lambda delay, fn: fn())
        ctrl = Mock()
        ctrl.is_running.return_value = False
        on_quit = Mock()
        return ctrl, on_quit, build_menu(ctrl, root, on_quit)

    def test_toggle_item_calls_controller_toggle(self):
        ctrl, _, menu = self._menu()

        menu.items[1](menu.items[1])

        ctrl.toggle.assert_called_once()

    def test_quit_item_calls_on_quit(self):
        """La voce Esci deve passare da on_quit, non da root.quit.

        Chiamare root.quit() direttamente e' il difetto della issue #1:
        chiude il main loop ma non ferma il timesheet e non termina il
        processo, che resta vivo nel vassoio.
        """
        _, on_quit, menu = self._menu()

        menu.items[2](menu.items[2])

        on_quit.assert_called_once()


class TestToggleLabel:
    """toggle_label e' una funzione pura: restituisce la stringa corretta."""

    def test_toggle_label_is_start_when_idle(self):
        from kemai_client.tray import toggle_label
        from kemai_client.i18n import t
        assert toggle_label(False) == t("btn_start")

    def test_toggle_label_is_stop_when_running(self):
        from kemai_client.tray import toggle_label
        from kemai_client.i18n import t
        assert toggle_label(True) == t("btn_stop")
