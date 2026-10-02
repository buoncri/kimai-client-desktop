r"""Test del dizionario stringhe italiane.

Verifica che esistano esattamente le 31 chiavi richieste dalla spec
e che t() le formatti correttamente con kwargs.
"""

import pytest

from kemai_client import i18n


class TestKeys:
    def test_all_required_keys_exist(self):
        # Le chiavi sono un contratto: le finestre le usano tutte.
        required = (
            "app_title",
            "menu_file",
            "menu_edit",
            "menu_new_project",
            "menu_settings",
            "menu_quit",
            "label_customer",
            "label_project",
            "label_activity",
            "label_started_at",
            "btn_start",
            "btn_stop",
            "label_host",
            "label_username",
            "label_token",
            "chk_close_to_tray",
            "btn_test",
            "btn_cancel",
            "btn_save",
            "status_connected",
            "status_error",
            "dlg_project_title",
            "label_name",
            "err_no_selection",
            "err_project_no_activities",
            "err_auth",
            "err_response",
            "err_active",
            "err_name_empty",
            "tray_show",
            "tray_quit",
        )
        for key in required:
            assert key in i18n.STRINGS, f"Chiave mancante: {key!r}"

    def test_no_extra_keys(self):
        # Non aggiungere mai chiavi non usate nelle finestre:
        # un dizionario che cresce silenziosamente nasconde errori di typo.
        required = frozenset((
            "app_title",
            "menu_file",
            "menu_edit",
            "menu_new_project",
            "menu_settings",
            "menu_quit",
            "label_customer",
            "label_project",
            "label_activity",
            "label_started_at",
            "btn_start",
            "btn_stop",
            "label_host",
            "label_username",
            "label_token",
            "chk_close_to_tray",
            "btn_test",
            "btn_cancel",
            "btn_save",
            "status_connected",
            "status_error",
            "dlg_project_title",
            "label_name",
            "err_no_selection",
            "err_project_no_activities",
            "err_auth",
            "err_response",
            "err_active",
            "err_name_empty",
            "tray_show",
            "tray_quit",
        ))
        extra = set(i18n.STRINGS.keys()) - required
        assert not extra, f"Chiavi extra non usate: {extra}"


class TestFormat:
    def test_t_formats_kwargs(self):
        # status_connected = "Connesso a Kimai {version}"
        result = i18n.t("status_connected", version="1.15")
        assert result == "Connesso a Kimai 1.15"

    def test_t_missing_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            i18n.t("non_esistente")


class TestValuesAreStrings:
    def test_all_values_are_strings(self):
        # La UI legge .format() sulle chiavi: se un valore non e' str
        # (es. None o un int), si rompe a runtime.
        for key, value in i18n.STRINGS.items():
            assert isinstance(value, str), f"{key} non e' una stringa: {value!r}"
