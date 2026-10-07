r"""Finestra principale (282×312): selettori a cascata, cronometro, StopButton.

Le finestre non chiamano mai l'API Kimai: leggono solo gli attributi
pubblici dell'AppController e lo notificano quando l'utente compie un'azione.
Il controller, a sua volta, contatta il client.

Layout: grid, non pack. Nessun ttk combinato con pack nello stesso widget.
"""

from __future__ import annotations

from typing import Callable

import tkinter as tk
from tkinter import ttk

from kemai_client.i18n import t
from kemai_client.ui.widgets import StopButton, format_duration

# Dimensioni della finestra.
_WIDTH = 282
_HEIGHT = 312
_START_TICK_DELAY_MS = 1000


class MainWindow:
    """Finestra principale del client.

    Args:
        root: la finestra Tkinter di livello root.
        controller: istanza di AppController (unico detentore dello stato).
        on_open_settings: callable invocato quando l'utente apre Impostazioni.
        on_new_project: callable invocato per il dialogo "Nuovo progetto".
    """

    def __init__(
        self,
        root: tk.Tk,
        controller,  # AppController
        on_open_settings: Callable[[], None],
        on_new_project: Callable[[], None],
    ) -> None:
        self._root = root
        self._controller = controller
        self._on_open_settings = on_open_settings
        self._on_new_project = on_new_project

        # --- Finestra ---
        self._root.title(t("app_title"))
        self._root.geometry(f"{_WIDTH}x{_HEIGHT}")
        self._root.resizable(False, False)

        # --- Menu ---
        menu_bar = tk.Menu(self._root)
        self._root.config(menu=menu_bar)

        # File
        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_file.add_command(label=t("menu_new_project"), command=self._on_new_project)
        menu_file.add_command(label=t("menu_settings"), command=self._on_open_settings)
        menu_file.add_separator()
        menu_file.add_command(label=t("menu_quit"), command=self._root.quit)
        menu_bar.add_cascade(label=t("menu_file"), menu=menu_file)

        # Modifica
        menu_edit = tk.Menu(menu_bar, tearoff=0)
        menu_edit.add_command(label=t("menu_quit"), command=self._root.quit)
        menu_bar.add_cascade(label=t("menu_edit"), menu=menu_edit)

        # --- Container ---
        self._container = ttk.Frame(self._root, padding=8)
        self._container.pack(fill=tk.BOTH, expand=False)

        # --- Riga 1: Cliente ---
        self._frame_customer = ttk.Frame(self._container)
        self._frame_customer.grid(row=0, column=0, sticky="we", pady=2)
        ttk.Label(self._frame_customer, text=t("label_customer")).grid(
            row=0, column=0, sticky="e"
        )
        self._combo_customer = ttk.Combobox(self._frame_customer, state="readonly")
        self._combo_customer.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._combo_customer.bind("<<ComboboxSelected>>", self._on_customer_selected)

        # --- Riga 2: Progetto ---
        self._frame_project = ttk.Frame(self._container)
        self._frame_project.grid(row=1, column=0, sticky="we", pady=2)
        ttk.Label(self._frame_project, text=t("label_project")).grid(
            row=0, column=0, sticky="e"
        )
        self._combo_project = ttk.Combobox(self._frame_project, state="readonly")
        self._combo_project.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._combo_project.bind("<<ComboboxSelected>>", self._on_project_selected)

        # --- Riga 3: Attività ---
        self._frame_activity = ttk.Frame(self._container)
        self._frame_activity.grid(row=2, column=0, sticky="we", pady=2)
        ttk.Label(self._frame_activity, text=t("label_activity")).grid(
            row=0, column=0, sticky="e"
        )
        self._combo_activity = ttk.Combobox(self._frame_activity, state="readonly")
        self._combo_activity.grid(row=0, column=1, sticky="we", padx=(4, 0))
        self._combo_activity.bind("<<ComboboxSelected>>", self._on_activity_selected)

        # --- StopButton (centrato) ---
        self._stop_button = StopButton(
            self._container,
            on_click=self._on_toggle,
            width=72,
            height=72,
        )
        self._stop_button.grid(row=3, column=0, pady=8)

        # --- Avviato il ---
        self._frame_started = ttk.Frame(self._container)
        self._frame_started.grid(row=4, column=0, sticky="we", pady=2)
        ttk.Label(self._frame_started, text=t("label_started_at")).grid(
            row=0, column=0, sticky="e"
        )
        self._entry_started = ttk.Entry(self._frame_started, state="readonly")
        self._entry_started.grid(row=0, column=1, sticky="we", padx=(4, 0))

        # --- Cronometro ---
        self._lbl_elapsed = ttk.Label(
            self._container,
            text="00:00:00",
            font=("", 20, "bold"),
        )
        self._lbl_elapsed.grid(row=5, column=0, pady=4)

        # --- Avviso (troncatura) ---
        self._lbl_truncated = ttk.Label(
            self._container,
            text="",
            foreground="orange",
        )
        self._lbl_truncated.grid(row=6, column=0, pady=2)

        # --- Subscribe: ogni cambiamento dello stato richiama refresh() ---
        self._controller.subscribe(self.refresh)

        # --- Prima refresh e avvio cronometro ---
        self.refresh()
        self.start_ticking()

    # --- Callback cascata ---

    def _on_customer_selected(self, event: tk.Event) -> None:
        idx = self._combo_customer.current()
        if idx < 0:
            return
        customer_id = self._controller.customers[idx].id
        self._controller.select_customer(customer_id)

    def _on_project_selected(self, event: tk.Event) -> None:
        idx = self._combo_project.current()
        if idx < 0:
            return
        project_id = self._controller.projects[idx].id
        self._controller.select_project(project_id)

    def _on_activity_selected(self, event: tk.Event) -> None:
        idx = self._combo_activity.current()
        if idx < 0:
            return
        activity_id = self._controller.activities[idx].id
        self._controller.select_activity(activity_id)

    def _on_toggle(self) -> None:
        self._controller.toggle()

    # --- Aggiornamento UI ---

    def refresh(self) -> None:
        """Rilegge lo stato dal controller e aggiorna tutti i widget."""
        self._refresh_combos()
        self._refresh_state()

    def _refresh_combos(self) -> None:
        """Aggiorna i combobox con le liste del controller."""
        self._combo_customer["values"] = [
            c.display for c in self._controller.customers
        ]
        self._combo_project["values"] = [
            p.display for p in self._controller.projects
        ]
        self._combo_activity["values"] = [
            a.display for a in self._controller.activities
        ]

        # Mantieni la selezione attuale se ancora valida.
        if self._controller.customer_id is not None:
            for i, c in enumerate(self._controller.customers):
                if c.id == self._controller.customer_id:
                    self._combo_customer.current(i)
                    break

        if self._controller.project_id is not None:
            for i, p in enumerate(self._controller.projects):
                if p.id == self._controller.project_id:
                    self._combo_project.current(i)
                    break

        if self._controller.activity_id is not None:
            for i, a in enumerate(self._controller.activities):
                if a.id == self._controller.activity_id:
                    self._combo_activity.current(i)
                    break

        # Se un elenco era troncato, mostra l'avviso.
        if self._controller.truncated:
            self._lbl_truncated.configure(
                text="Elenco limitato: seleziona un altro elemento per vederne altri"
            )
        else:
            self._lbl_truncated.configure(text="")

    def _refresh_state(self) -> None:
        """Aggiorna i campi statici (cronometro, avvia il, stop button)."""
        self._stop_button.set_label(
            t("btn_start") if not self._controller.is_running() else t("btn_stop")
        )
        self._stop_button.set_enabled(self._controller.can_start())
        self._entry_started.delete(0, tk.END)
        self._entry_started.insert(0, self._controller.started_at_label())

    def _tick(self) -> None:
        """Update cronometro label e si ripianifica a 1 secondo."""
        self._lbl_elapsed.configure(text=format_duration(self._controller.elapsed_seconds()))
        self._root.after(_START_TICK_DELAY_MS, self._tick)

    def start_ticking(self) -> None:
        """Avvia l'aggiornamento periodico del cronometro."""
        self._root.after(
            _START_TICK_DELAY_MS, self._tick
        )
