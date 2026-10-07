r"""Dialog di creazione progetto.

Finestra modale con campo Nome e combobox Cliente.
Un nome vuoto non chiude il dialog e mostra un avviso.
Se il cliente pre-selezionato è già attivo nella finestra principale,
la combobox parte da quel cliente.

Questo modulo non importa mai KimaiClient.
"""

from __future__ import annotations

from typing import Callable

import tkinter as tk
from tkinter import ttk

from kemai_client.i18n import t
from kemai_client.models import Project


class ProjectDialog:
    """Dialog modale per la creazione di un nuovo progetto.

    Args:
        parent: il widget genitore (Tk o Toplevel).
        controller: istanza di AppController.
        preselected_customer: ID del cliente pre-selezionato, se già attivo.
    """

    def __init__(
        self,
        parent: tk.Misc,
        controller,  # AppController
        preselected_customer: int | None = None,
    ) -> None:
        self._parent = parent
        self._controller = controller
        self._preselected_customer = preselected_customer
        self._result: Project | None = None
        self._name_empty = False

        # --- Finestra ---
        self._window = tk.Toplevel(parent)
        self._window.title(t("dlg_project_title"))
        self._window.transient(parent)
        self._window.grab_set()
        self._window.resizable(False, False)
        self._window.geometry("280x160")

        # --- Nome ---
        self._frame_name = ttk.Frame(self._window, padding=(10, 10))
        self._frame_name.grid(row=0, column=0, sticky="we")
        ttk.Label(self._frame_name, text=t("label_name")).grid(
            row=0, column=0, sticky="e"
        )
        self._entry_name = ttk.Entry(self._frame_name)
        self._entry_name.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._entry_name.focus_set()

        # --- Cliente ---
        self._frame_customer = ttk.Frame(self._window, padding=(10, 5))
        self._frame_customer.grid(row=1, column=0, sticky="we")
        ttk.Label(self._frame_customer, text=t("label_customer")).grid(
            row=0, column=0, sticky="e"
        )
        customer_names = [c.display for c in self._controller.customers]
        self._combo_customer = ttk.Combobox(
            self._frame_customer, values=customer_names, state="readonly"
        )
        self._combo_customer.grid(row=0, column=1, sticky="we", padx=(4, 0))

        # Seleziona il cliente pre-selezionato se disponibile.
        if preselected_customer is not None:
            for i, c in enumerate(self._controller.customers):
                if c.id == preselected_customer:
                    self._combo_customer.current(i)
                    break

        # --- Pulsanti ---
        btn_frame = ttk.Frame(self._window, padding=(10, 10))
        btn_frame.grid(row=2, column=0, sticky="we")

        ttk.Button(btn_frame, text=t("btn_save"), command=self._on_save).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text=t("btn_cancel"), command=self._on_cancel).pack(
            side=tk.LEFT, padx=2
        )

        # --- Avviso nome vuoto ---
        self._lbl_error = ttk.Label(self._window, text="", foreground="red")
        self._lbl_error.grid(row=3, column=0, sticky="we", padx=20)

    def _on_save(self) -> None:
        """Salva il progetto se il nome non è vuoto."""
        name = self._entry_name.get().strip()

        if not name:
            self._name_empty = True
            self._lbl_error.configure(text=t("err_name_empty"))
            return

        self._name_empty = False
        self._lbl_error.configure(text="")

        customer_idx = self._combo_customer.current()
        if customer_idx < 0:
            return

        customer_id = self._controller.customers[customer_idx].id
        self._result = self._controller.create_project(name, customer_id)
        self._window.destroy()

    def _on_cancel(self) -> None:
        self._result = None
        self._window.destroy()

    @property
    def result(self) -> Project | None:
        """Il progetto creato, o None se l'utente ha annullato."""
        return self._result

    # Alias pubblici per il test strutturale.
    def save(self) -> None:
        """Alias pubblico per il test strutturale."""
        self._on_save()

    def cancel(self) -> None:
        """Alias pubblico per il test strutturale."""
        self._on_cancel()
