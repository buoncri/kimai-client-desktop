r"""Finestra Impostazioni.

Campi: Host, Nome utente, Token (show="*").
Pulsanti: "Prova" (verifica senza salvare), "Annulla", "Salva".
L'etichetta di stato diventa verde (connesso) o rossa (errore).
Casella "Ignora la verifica del certificato TLS": per server interni
con certificato non fidato; disattivata di default.

Questo modulo non importa mai KimaiClient: interagisce solo con
l'AppController e le stringhe italiane tramite i18n.t().
"""

from __future__ import annotations

from typing import Callable

import tkinter as tk
from tkinter import ttk

from kemai_client.api.errors import KimaiAuthError, KimaiError
from kemai_client.i18n import t
from kemai_client.config import Config, save


class SettingsWindow:
    """Finestra delle impostazioni.

    Args:
        parent: il widget genitore (Tk o Toplevel).
        controller: istanza di AppController.
        on_saved: callable invocato dopo un salvataggio riuscito.
        on_closed: callable invocato alla chiusura, con True se la
            configurazione e' stata salvata e False se la finestra e'
            stata chiusa senza salvare. Senza questo chi apre la finestra
            non ha modo di sapere quando l'utente ha finito.
    """

    def __init__(
        self,
        parent: tk.Misc,
        controller,  # AppController
        on_saved: Callable[[], None] | None = None,
        on_closed: Callable[[bool], None] | None = None,
    ) -> None:
        self._parent = parent
        self._controller = controller
        self._on_saved = on_saved
        self._on_closed = on_closed
        self._closed = False

        # --- Finestra ---
        self._window = tk.Toplevel(parent)
        self._window.title(t("app_title"))
        self._window.transient(parent)
        self._window.grab_set()
        self._window.resizable(False, False)
        self._window.geometry("320x306")
        # La X passa da cancel: senza questo la finestra sparirebbe senza
        # notificare nessuno, e chi l'ha aperta resterebbe in attesa.
        self._window.protocol("WM_DELETE_WINDOW", self.cancel)

        # --- Host ---
        self._frame_host = ttk.Frame(self._window, padding=(10, 5))
        self._frame_host.grid(row=0, column=0, sticky="we")
        ttk.Label(self._frame_host, text=t("label_host")).grid(
            row=0, column=0, sticky="e"
        )
        self._entry_host = ttk.Entry(self._frame_host)
        self._entry_host.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._entry_host.insert(0, controller.config.host)

        # --- Nome utente ---
        self._frame_user = ttk.Frame(self._window, padding=(10, 5))
        self._frame_user.grid(row=1, column=0, sticky="we")
        ttk.Label(self._frame_user, text=t("label_username")).grid(
            row=0, column=0, sticky="e"
        )
        self._entry_user = ttk.Entry(self._frame_user)
        self._entry_user.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._entry_user.insert(0, controller.config.username)

        # --- Token ---
        self._frame_token = ttk.Frame(self._window, padding=(10, 5))
        self._frame_token.grid(row=2, column=0, sticky="we")
        ttk.Label(self._frame_token, text=t("label_token")).grid(
            row=0, column=0, sticky="e"
        )
        self._entry_token = ttk.Entry(self._frame_token, show="*")
        self._entry_token.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._entry_token.insert(0, controller.config.token)

        # --- Checkbox: chiudi nel vassoio ---
        self._chk_tray = tk.BooleanVar(
            value=controller.config.close_to_tray
        )
        chk_frame = ttk.Frame(self._window, padding=(10, 5))
        chk_frame.grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(
            chk_frame,
            text=t("chk_close_to_tray"),
            variable=self._chk_tray,
        ).pack()

        # --- Checkbox: ignora la verifica del certificato TLS ---
        # Spunta = non verificare il certificato (server interno con
        # certificato non fidato). La variabile e' "ignora": il valore
        # in config e' il negato (verify_tls).
        self._chk_tls_ignore = tk.BooleanVar(
            value=not controller.config.verify_tls
        )
        chk_tls_frame = ttk.Frame(self._window, padding=(10, 5))
        chk_tls_frame.grid(row=4, column=0, sticky="w")
        ttk.Checkbutton(
            chk_tls_frame,
            text=t("chk_verify_tls"),
            variable=self._chk_tls_ignore,
        ).pack()

        # --- Etichetta di stato ---
        self._lbl_status = ttk.Label(self._window, text="")
        self._lbl_status.grid(row=5, column=0, pady=5)

        # --- Pulsanti ---
        btn_frame = ttk.Frame(self._window, padding=(10, 5))
        btn_frame.grid(row=6, column=0, sticky="we")

        ttk.Button(btn_frame, text=t("btn_test"), command=self._on_test).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text=t("btn_cancel"), command=self.cancel).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text=t("btn_save"), command=self._on_save).pack(
            side=tk.LEFT, padx=2
        )

        # Focalizza sul primo campo
        self._entry_host.focus_set()

    def _on_test(self) -> None:
        """Verifica le credenziali senza modificare la config.

        Se l'autenticazione fallisce, l'etichetta diventa rossa con
        il messaggio italiano, senza chiudere la finestra.
        """
        host = self._entry_host.get().strip()
        username = self._entry_user.get().strip()
        token = self._entry_token.get().strip()

        try:
            version = self._controller.connect(
                host,
                username,
                token,
                verify_tls=not self._chk_tls_ignore.get(),
            )
            self._lbl_status.configure(
                text=t("status_connected", version=version),
                foreground="green",
            )
        except KimaiAuthError as exc:
            self._lbl_status.configure(text=str(exc), foreground="red")
        except KimaiError as exc:
            self._lbl_status.configure(text=str(exc), foreground="red")

    def _on_save(self) -> None:
        """Salva la configurazione e chiude la finestra."""
        host = self._entry_host.get().strip()
        username = self._entry_user.get().strip()
        token = self._entry_token.get().strip()
        close_to_tray = self._chk_tray.get()

        # Aggiorna il controller con i valori della finestra.
        self._controller._config = Config(  # type: ignore[attr-defined]
            host=host,
            username=username,
            token=token,
            close_to_tray=close_to_tray,
            verify_tls=not self._chk_tls_ignore.get(),
        )

        # Salva su disco (atomico, crea directory se serve).
        save(self._controller.config)

        # Il client deve rispecchiare la nuova configurazione, e i dati
        # vanno ricaricati dal server (eventualmente diverso).
        self._controller.apply_config()
        self._controller.load_customers()

        if self._on_saved is not None:
            self._on_saved()

        self.cancel(saved=True)

    def cancel(self, saved: bool = False) -> None:
        """Chiude la finestra e notifica la chiusura.

        Args:
            saved: True se la configurazione e' stata appena salvata.
                Chi non chiama `cancel` non viene notificato, quindi
                al primo avvio non si saprebbe mai quando riprovare.
        """
        if self._closed:
            return
        self._closed = True

        self._window.destroy()

        if self._on_closed is not None:
            self._on_closed(saved)

    # Esporta per il test strutturale.
    def test_connection(self) -> None:
        """Alias pubblico per il test strutturale."""
        self._on_test()

    def save(self) -> None:
        """Alias pubblico per il test strutturale."""
        self._on_save()

    def cancel_pub(self) -> None:
        """Alias pubblico per il test strutturale."""
        self.cancel()
