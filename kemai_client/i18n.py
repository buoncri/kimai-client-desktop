r"""Dizionario stringhe italiane per l'intera interfaccia.

Tutte le stringhe visibili all'utente passano da qui, non sono mai
hardcoded nelle finestre. Il modulo non importa Tkinter, quindi
puede essere usato anche nei test del controller.

Le chiavi sono un contratto: non aggiungerne nuove senza
modificare contemporaneamente tests/test_i18n.py.
"""

STRINGS: dict[str, str] = {
    # --- Finestra principale ---
    "app_title": "Kemai - Kimai client",
    "menu_file": "File",
    "menu_edit": "Modifica",
    "menu_new_project": "Nuovo progetto",
    "menu_settings": "Impostazioni",
    "menu_quit": "Esci",
    "label_customer": "Cliente",
    "label_project": "Progetto",
    "label_activity": "Attività",
    "label_started_at": "Avviato il",
    "btn_start": "Avvia",
    "btn_stop": "Ferma",
    "status_connected": "Connesso a Kimai {version}",
    "status_error": "Errore: {message}",

    # --- Finestra impostazioni ---
    "label_host": "Host",
    "label_username": "Nome utente",
    "label_token": "Token",
    "chk_close_to_tray": "Chiudi nel vassoio di sistema",
    "btn_test": "Prova",
    "btn_cancel": "Annulla",
    "btn_save": "Salva",

    # --- Dialog progetto ---
    "dlg_project_title": "Progetto",
    "label_name": "Nome",

    # --- Errori ---
    "err_no_selection": "Nessuna selezione attiva",
    "err_project_no_activities": "Il progetto selezionato non ha attività",
    "err_auth": "Autenticazione non valida. Verifica host e token.",
    "err_response": "Risposta non valida dal server",
    "err_active": "Un'attività è già in corso",
    "err_name_empty": "Il nome non può essere vuoto",

    # --- System tray ---
    "tray_show": "Mostra finestra",
    "tray_quit": "Esci",
}


def t(key: str, **kwargs: object) -> str:
    """Formatta una stringa con le keyword arguments.

    Args:
        key: Chiave nel dizionario STRINGS.
        **kwargs: Parametri da interpolare, es. ``version="1.15"``.

    Raises:
        KeyError: se la chiave non esiste nel dizionario.
    """
    template = STRINGS[key]
    return template.format(**kwargs)
