# Issue #1 — Pulsante Ferma non funziona: piano di intervento

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Far sì che il pulsante Ferma sia cliccabile mentre un'attività è in corso, e che ogni percorso di uscita dell'app fermi il timesheet prima di terminare il processo.

**Architecture:** Il difetto non è nell'endpoint (`stop_timesheet` fa il PATCH corretto, verificato live): è nel cablaggio tra il controller e la UI. L'intervento isola tre difetti distinti e li tratta come tre task separati, perché ognuno è rivedibile da solo. Il principio è uno solo: **un controllo che sembra cliccabile deve fare qualcosa, e un controllo che non può fare niente non deve sembrare cliccabile.** Il controller resta l'unico detentore dello stato; la UI legge e non decide.

**Tech Stack:** Python 3.10+, Tkinter (std), `requests`, `pystray` + `Pillow`, `pytest`. Nessuna dipendenza nuova.

**Spec:** `doc/issues/2026-10-13-github-issues.md` — la sezione "Analisi (2026-10-13)" è la diagnosi che questo piano realizza, con i numeri di riga. Chi esegue legge entrambi i file.

## Stato di partenza

| | |
|---|---|
| Branch | `main`, allineato con `origin/main` a `e882545` (0 commit di divergenza) |
| Test verdi | **152** (`.venv\Scripts\python.exe -m pytest -q` → `152 passed in 0.76s`) |
| File non tracciato | `scheletro.json` — **non toccarlo, non committarlo**, non c'entra con questo intervento |
| Default branch GitHub | `qwen38-35b-distill`, **non** `main`. Non cambiare il default branch in questo intervento. |

| Task | Stato | Commit |
|---|---|---|
| 1. `StopButton.set_enabled` non spegne più il Canvas | da fare | — |
| 2. `AppController.toggle()` a tre vie | da fare | — |
| 3. `_refresh_state` abilita Ferma mentre l'attività è in corso | da fare | — |
| 4. Un unico percorso di uscita che ferma il timesheet | da fare | — |
| 5. Etichetta del vassoio coerente con lo stato | da fare | — |

Ogni task è TDD e finisce con la suite completa verde. I task sono in ordine di dipendenza: 2 prima di 3 (il 3 asserisce una condizione che il 2 rende possibile), 4 indipendente, 5 indipendente.

## Global Constraints

- Python 3.10 o superiore. Nessuna dipendenza runtime nuova: solo `requests`, `pystray`, `Pillow`.
- Tutti i test girano **offline**: nessun socket, nessuna istanza Kimai, nessun accesso al filesystem per l'icona.
- **Tkinter gira sempre e solo nel main thread.** Le callback di `pystray` passano da `root.after(0, fn)` prima di toccare un widget.
- L'interfaccia è **interamente in italiano**; ogni stringa visibile passa da `i18n.t()`.
- **Non aggiungere chiavi a `i18n.STRINGS`.** `tests/test_i18n.py::test_no_extra_keys` asserisce che le chiavi siano esattamente le 31 attuali: una chiave nuova senza usarla in una finestra fa fallire la suite, e una chiave nuova usata solo qui allargerebbe il contratto di i18n senza bisogno. Se durante il lavoro ti serve una stringa nuova, fermati e segnalalo invece di allargare il dizionario.
- `tests/test_main_window.py` oggi contiene **solo** tre smoke test `hasattr`. Questo piano lo trasforma in un file di test di comportamento: i tre test esistenti **restano**, non si cancellano.
- Nessun segnaposto `TBD` o `TODO` nel codice finale.
- Commenti e documentazione in italiano; i nomi di simboli pubblici in inglese.
- **Non modificare `kemai_client/api/client.py`.** Gli endpoint sono verificati dal vivo e sono corretti: il difetto è a monte. Se pensi che il client vada cambiato, fermati e segnalalo.

## Review Focus

Cinque classi di condizione che l'analisi implica, che nessun test esistente esercita, ordinate per probabilità di mordere. Ogni riga ha il suo test assegnato al task che possiede il codice.

1. **Avvia con il server che risponde con un errore** (500, 422) → `start()` non imposta `_timesheet_id`, quindi l'app deve tornare allo stato "pronto" con il bottone blu che dice "Avvia", **non** restare in uno stato mezzo avviato da cui non si può più uscire. *Test in Task 3.*
2. **Cambio di cliente, progetto o attività nei combobox mentre un'attività è in corso** → `select_customer`/`select_project` azzerano gli id figli ma non toccano `_timesheet_id`: Ferma deve chiudere il timesheet **vecchio**, non quello appena selezionato. *Test in Task 3.*
3. **Rete che cade mentre l'app sta uscendo** → `stop()` cattura `KimaiNetworkError`, mantiene lo stato "in corso" e non solleva: l'uscita deve **completarsi lo stesso**, perché un'uscita bloccata lascia l'utente con un processo che non si chiude. *Test in Task 4.*
4. **Token scaduto: il server risponde 401 quando l'app tenta di fermare** → `stop()` lascia propagare `KimaiAuthError`, quindi senza protezione l'uscita si blocca con una traccia tecnica. *Test in Task 4.*
5. **Chiusura con la X e "Chiudi nel vassoio" attivo, con un'attività in corso** → il comportamento è withdraw, non uscita: nessuno stop, nessun destroy, il timer continua. Una correzione che ferma l'attività qui farebbe perdere ore all'utente. **Nessun test automatico lo copre**, perché `on_close` vive dentro `app.main()` e non è estraibile senza rifattorizzare la composizione. Il vincolo che questo piano impone è che il ramo `withdraw` resti **solo** `root.withdraw()` e non chiami mai `exit_sequence`; la verifica del comportamento è **[UMANO]**, passo 3 sotto. *Test in Task 4 sul ramo già esistente di `close_behaviour` (deve continuare a restituire `"withdraw"` per `True`).*

---

### Task 1: `StopButton.set_enabled` non deve spegnere il Canvas

**Files:**
- Modify: `kemai_client/ui/widgets.py:117-130` (`StopButton.set_enabled`)
- Test: `tests/test_widgets.py`

**Interfaces:**
- Consumes: nessuno (primo task).
- Produces: `StopButton.set_enabled(self, enabled: bool) -> None`, con firma invariata e **semantica nuova**: `False` cambia solo i colori, non lo stato del widget. Dopo `set_enabled(False)` il Canvas resta `state="normal"` e continua a consegnare gli eventi già legati con `tag_bind`.

Il motivo di fondo: `config(state="disabled")` applicato al Canvas **intero** non disabilita "l'ottagono", disabilita l'intero widget, e Tkinter smette di consegnare qualunque evento — anche quelli già legati. Oggi la UI si affida a quel comportamento per bloccare il click su un pulsante non utilizzabile: è la trappola che ha spento Ferma.

- [ ] **Step 1: Scrivi i test che falliscono**

In `tests/test_widgets.py`, aggiungi una classe `TestStopButtonEnabled`, che costruisce un `StopButton` reale dentro una root Tkinter nascosta — lo stesso pattern già usato da `TestOctagon`, che crea `tk.Tk()`, chiama `root.withdraw()`, e alla fine fa `canvas.destroy()` e `root.destroy()`. Usa `on_click=Mock()` come callback.

`test_set_enabled_false_keeps_canvas_normal`: dopo `btn.set_enabled(False)`, asserisci `str(btn.cget("state")) == "normal"`. Il messaggio di fallimento deve dire che è l'evento a essere perso, non solo lo stato: `f"stato={btn.cget('state')}"`.

`test_set_enabled_false_repaints_grey`: dopo `btn.set_enabled(False)`, il fill dell'ottagono (`btn._octagon_id`) deve essere `"#b0b0b0"`, cioè il colore spento, per garantire che la disattivazione resti visibile all'utente anche senza spegnere il widget.

`test_set_enabled_true_restores_fill`: dopo `set_enabled(False)` e poi `set_enabled(True)`, il fill torna a `"#4a90d9"`.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_widgets.py -v`
Expected: FAIL — `test_set_enabled_false_keeps_canvas_normal` con `state=disabled`. Gli altri due PASS già.

- [ ] **Step 3: Implementa il cambio**

In `StopButton.set_enabled`, rimuovi le due righe `self.config(state="normal", ...)` e `self.config(state="disabled", ...)` dal ramo `else` e dall'`if`. Tieni `self.config(bg=...)` per lo sfondo del Canvas. Aggiorna la docstring: `enabled` comanda **solo l'aspetto**, e spiega in due righe perché il widget non viene mai disabilitato (disabilitare un Canvas in Tkinter azzera la consegna degli eventi su tutto il widget, non su un singolo elemento disegnato dentro).

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_widgets.py -v`
Expected: PASS. Poi la suite completa: `.venv\Scripts\python.exe -m pytest -q` → `155 passed` (152 + 3).

- [ ] **Step 5: Committa**

```bash
git add kemai_client/ui/widgets.py tests/test_widgets.py
git commit -m "fix(ui): set_enabled non spegne piu' il Canvas, cambia solo i colori"
```

---

### Task 2: `AppController.toggle()` a tre vie

**Files:**
- Modify: `kemai_client/controller.py:334-339` (`AppController.toggle`)
- Test: `tests/test_controller.py` (riusa il `FakeClient` già definito a `tests/test_controller.py:25` e il clock finto già in uso)

**Interfaces:**
- Consumes: `AppController.can_start() -> bool` e `AppController.is_running() -> bool`, entrambe già esistenti e senza modifiche.
- Produces: `AppController.toggle(self) -> None` con firma invariata e semantica nuova a tre vie: se `is_running()` ferma, se `can_start()` avvia, altrimenti **non fa niente**. Il nome e la firma restano, perché il tray e la UI li chiamano già.

Il difetto: dopo il Task 1 il Canvas non è più spento, quindi un click su un bottone grigio arriverebbe davvero a `toggle()`. Senza questa guardia, `start()` partirebbe con `project_id=None`. È per questo che i due task sono in quest'ordine e non indipendenti.

- [ ] **Step 1: Scrivi i test che falliscono**

Tre test nella classe di test del controller esistente, con un controller costruito come negli altri test del file e un `FakeClient`:

`test_toggle_with_incomplete_cascade_does_nothing`: non selezionare nulla, chiama `ctrl.toggle()`, poi asserisci che `fake.calls` non contiene nessuna entry con metodo `"start_timesheet"` né `"stop_timesheet"`, e che `ctrl.is_running() is False`. Il punto è che **non deve partire nessuna richiesta**, non solo che non deve partire nessun timer.

`test_toggle_starts_when_ready`: seleziona cliente, progetto e attività, `ctrl.toggle()`, asserisci che il fake ha registrato `start_timesheet` e che `ctrl.is_running() is True`.

`test_toggle_stops_when_running`: parti da `ctrl.start()`, poi `ctrl.toggle()`, asserisci che il fake ha registrato `stop_timesheet` e che `ctrl.is_running() is False`.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_controller.py -v -k toggle`
Expected: FAIL solo `test_toggle_with_incomplete_cascade_does_nothing`, con una chiamata `start_timesheet` registrata. Gli altri due PASS già.

- [ ] **Step 3: Implementa il cambio**

Sostituisci il corpo di `toggle()` con la sequenza: `if self.is_running(): self.stop(); elif self.can_start(): self.start()`. Niente `else`. Aggiorna la docstring per dire che la funzione è un no-op quando la cascata è incompleta, e perché.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_controller.py -v`
Expected: PASS. Poi la suite completa → `158 passed` (155 + 3).

- [ ] **Step 5: Committa**

```bash
git add kemai_client/controller.py tests/test_controller.py
git commit -m "fix(controller): toggle() a tre vie, nessuna richiesta a cascata incompleta"
```

---

### Task 3: `_refresh_state` abilita Ferma mentre l'attività è in corso

**Files:**
- Modify: `kemai_client/ui/main_window.py:224-231` (`MainWindow._refresh_state`)
- Test: `tests/test_main_window.py`

**Interfaces:**
- Consumes: `AppController.can_start() -> bool` e `AppController.is_running() -> bool` (Task 2), `StopButton.set_enabled(enabled: bool) -> None` (Task 1).
- Produces: `MainWindow` **senza variazioni di firma** in questo task. `_refresh_state()` chiama `set_enabled` con `can_start() or is_running()`.

`can_start()` risponde alla domanda "posso avviare?", non a "il pulsante è cliccabile?". Le due condizioni vanno tenute separate: con la sola `can_start()` il bottone si spegne proprio mentre serve per fermare.

**Come testare senza Tkinter.** Non costruire una `MainWindow` reale: il suo `__init__` crea venti widget e registra un `after`. Costruisci l'oggetto con `MainWindow.__new__(MainWindow)`, poi inietta tre `Mock`: `win._controller`, `win._stop_button`, `win._entry_started`, e chiama `win._refresh_state()`. `Mock` assorbe `delete`/`insert` su `_entry_started`. Il test asserisce il **contratto di cablaggio** — con quale argomento viene chiamato `set_enabled` — che è esattamente il punto in cui il bug vive, e gira senza schermo né event loop.

- [ ] **Step 1: Scrivi i test che falliscono**

Cinque test in `tests/test_main_window.py`, in una classe nuova `TestRefreshState`. Helper locale per costruire la finestra senza Tkinter:

```python
def _make_window(controller):
    win = MainWindow.__new__(MainWindow)
    win._controller = controller
    win._stop_button = Mock()
    win._entry_started = Mock()
    return win
```

`test_button_disabled_when_cascade_incomplete`: controller finto con `can_start` che restituisce False e `is_running` che restituisce False. Dopo `_refresh_state()`, asserisci che `set_enabled` è stato chiamato una volta con `False`.

`test_button_enabled_when_ready_to_start`: `can_start` True, `is_running` False. Asserisci `set_enabled` chiamato con `True`.

`test_button_enabled_while_running` — **è il test che pinning la issue #1**: `can_start` False (perché è la condizione creata dal timesheet attivo), `is_running` True. Asserisci `set_enabled` chiamato con `True`. Aggiungi nel messaggio di fallimento un riferimento all'argomento ricevuto, così il fallimento dice quale delle due condizioni è stata persa.

`test_label_shows_stop_while_running`: stesso controller del precedente, asserisci che `set_label` è stato chiamato con `i18n.t("btn_stop")`, cioè la stringa `"Ferma"`. Il label e l'abilitazione devono essere coerenti: non basta che il bottone sia cliccabile, deve anche dire cosa farà.

`test_start_failure_leaves_button_clickable`: controller finto il cui `can_start` restituisce True e `is_running` restituisce False — lo stato in cui si trova l'app dopo che `start()` ha sollevato un `KimaiError` e lasciato `_timesheet_id` a None. Asserisci `set_enabled(True)`: il pulsante deve tornare cliccabile e dire "Avvia", non restare in uno stato da cui non si esce.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main_window.py -v -k TestRefreshState`
Expected: FAIL `test_button_enabled_while_running` e `test_start_failure_leaves_button_clickable` con `set_enabled` chiamato con `False`. Gli altri tre PASS già.

- [ ] **Step 3: Implementa il cambio**

In `_refresh_state`, cambia una sola riga: l'argomento di `set_enabled` diventa `self._controller.can_start() or self._controller.is_running()`. Aggiungi un commento di due righe che spiega perché i due predicati sono in or: uno dice se si può avviare, l'altro se si può fermare, e il bottone serve a entrambi.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main_window.py -v`
Expected: PASS (gli 3 smoke test strutturali più i 5 nuovi = 8). Suite completa → `163 passed` (158 + 5).

- [ ] **Step 5: Committa**

```bash
git add kemai_client/ui/main_window.py tests/test_main_window.py
git commit -m "fix(ui): Ferma resta cliccabile mentre l'attivita' e' in corso"
```

---

### Task 4: Un unico percorso di uscita che ferma il timesheet

Il secondo difetto della issue #1. Oggi i tre "Esci" — `main_window.py:62` (File), `main_window.py:69` (Modifica), `tray.py:167` (vassoio) — chiamano tutti `root.quit()` e basta: niente `controller.stop()`, niente `tray.stop()`, niente `root.destroy()`. `root.quit()` chiude il main loop ma **non chiude il record sul server** e **non termina il processo**: il thread daemon di pystray lo tiene vivo, l'app sparisce dalla taskbar e gira ancora nel vassoio. Da lì l'incoerenza descritta nella issue.

**Files:**
- Create: `kemai_client/exit_handler.py`
- Modify: `kemai_client/app.py:88-105` (`on_close`, costruzione del tray)
- Modify: `kemai_client/ui/main_window.py:36-63` (firma di `__init__`, voci di menu File e Modifica)
- Modify: `kemai_client/tray.py:142-173` (`build_menu`, `TrayIcon.__init__`)
- Test: `tests/test_exit_handler.py` (nuovo), `tests/test_tray.py:49-72` (`TestBuildMenu`)

**Interfaces:**
- Consumes: `AppController.is_running() -> bool`, `AppController.stop() -> None`, `AppController.last_error -> str` (tutte esistenti), `TrayIcon.stop() -> None` (esistente, `tray.py:133-136`), `close_behaviour(close_to_tray: bool) -> str` (esistente, `tray.py:33-48`), `KimaiError` da `kemai_client.api.errors`.
- Produce:
  - `kemai_client.exit_handler.exit_sequence(controller, root, tray) -> None`. I tre parametri non sono tipizzati con classi concrete: accetta qualsiasi oggetto che esponga quei metodi, così il test passa `Mock`. Ordine interno fisso e non negoziabile: **(1)** se `controller.is_running()` allora `controller.stop()` dentro un `try/except KimaiError` che registra l'errore e **prosegue**; **(2)** `tray.stop()`; **(3)** `root.quit()`; **(4)** `root.destroy()`. Nessun `except` che coinvolga `root`: se `tray.stop()` solleva, l'uscita deve continuare.
  - `kemai_client.tray.build_menu(controller, root, on_quit) -> pystray.Menu` — **firma cambiata**, terzo parametro obbligatorio: il callback che il menu del vassoio deve invocare per uscire. `TrayIcon.__init__` passa `self._quit_app`, che chiama `exit_sequence(controller, root, self)`.
  - `MainWindow.__init__(self, root, controller, on_open_settings, on_new_project, on_quit)` — **firma cambiata**, quinto parametro obbligatorio `on_quit: Callable[[], None]`, usato da entrambe le voci "Esci".

Attenzione all'ordine di costruzione in `app.py`: `MainWindow` viene costruito **prima** di `tray`, e non può essere diversamente. È un closure, quindi `tray` viene risolto alla chiamata e non all'istruzione: `on_quit` può essere definito prima che `tray` esista, purché non venga mai invocato durante `MainWindow.__init__`. Non lo è. Lo stesso schema è già usato per `on_open_settings` e `on_new_project` in `app.py:51-58`.

- [ ] **Step 1: Scrivi i test che falliscono**

Crea `tests/test_exit_handler.py`. Tutti con `Mock`, nessun Tkinter, nessuna rete.

`test_exit_sequence_stops_running_timesheet`: `controller.is_running` True. Asserisci che `controller.stop` è stato chiamato una volta.

`test_exit_sequence_does_not_stop_when_idle`: `controller.is_running` False. Asserisci che `controller.stop` **non** è stato chiamato: uscire non deve toccare il server se non c'è niente in corso.

`test_exit_sequence_stops_tray_before_destroying`: registra l'ordine delle chiamate con un `Mock` che ha come `side_effect` una funzione che appende il nome su una lista, per `controller.stop`, `tray.stop`, `root.quit`, `root.destroy`. Asserisci che la lista è esattamente `["stop", "tray_stop", "quit", "destroy"]`. L'ordine è metà del fix: chiudere il vassoio dopo `destroy` lascia il thread daemon vivo.

`test_exit_sequence_survives_auth_error_on_stop`: `controller.stop` solleva `KimaiAuthError("token scaduto", status=401)`. Asserisci che `root.destroy` è comunque stato chiamato, e che la funzione **non** propaga l'eccezione. Questo è il caso Review Focus #4.

`test_exit_sequence_survives_network_error_on_stop`: `controller.stop` solleva `KimaiNetworkError("rete caduta")`. Stesse due asserzioni. Questo è il caso Review Focus #3.

`test_exit_sequence_survives_tray_failure`: `tray.stop` solleva `RuntimeError`. Asserisci che `root.quit` e `root.destroy` sono comunque stati chiamati.

In `tests/test_tray.py`, **aggiorna** `TestBuildMenu::test_menu_callbacks_are_deferred` (riga 49) per la firma nuova: passa un terzo argomento `Mock()` come `on_quit`. Non cancellare il test. Aggiungi `test_tray_toggle_item_is_clickable_while_running`: con `controller.is_running` che restituisce True, costruisci il menu con `build_menu(controller, Mock(), Mock())` e asserisci che il secondo elemento del menu ha `enabled` che risolve a `True`. È l'equivalente nel vassoio del contratto che il Task 3 verifica sulla finestra: la voce Avvia/Ferma deve restare utilizzabile mentre l'attività è in corso.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_exit_handler.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.exit_handler'`.

Run: `.venv\Scripts\python.exe -m pytest tests/test_tray.py -v -k BuildMenu`
Expected: FAIL con `TypeError: build_menu() missing 1 required positional argument: 'on_quit'`.

- [ ] **Step 3: Implementa il modulo e i tre cablaggi**

`exit_handler.py`: `exit_sequence(controller, root, tray) -> None` nell'ordine indicato nelle Interfaces. Nel `except KimaiError` usa il logger `logging.getLogger("kimai")` e `log_exception` da `kemai_client.logging_setup`, già usato dal controller: l'errore va nel log, non a schermo. Non chiamare `t()` per il messaggio, per lo stesso motivo documentato in `controller.py:305`.

`app.py`: definisci `on_quit` subito dopo `on_new_project`, come closure su `exit_sequence(controller, root, tray)`. Passalo a `_start_main_window()`. Riscrivi `on_close` perché chiami `exit_sequence` nel ramo `destroy` e lasci `root.withdraw()` intatto nel ramo `withdraw` — quel ramo non deve mai fermare l'attività, è il caso Review Focus #5. Rimuovi il commento in `app.py:100` che promette un destroy che il codice non fa.

`main_window.py`: aggiungi il parametro `on_quit` dopo `on_new_project`, memorizzalo in `self._on_quit`, e sostituisci `command=self._root.quit` con `command=self._on_quit` in entrambe le voci di menu.

`tray.py`: aggiungi il parametro `on_quit` a `build_menu` e usalo al posto di `root.after(0, root.quit)` dentro `quit_app`. In `TrayIcon.__init__` passa `self._quit_app` e aggiungi il metodo `_quit_app(self) -> None` che chiama `exit_sequence(self._controller, self._root, self)`.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_exit_handler.py tests/test_tray.py tests/test_main_window.py -v`
Expected: PASS. Suite completa → `170 passed` (163 + 7: 6 in `tests/test_exit_handler.py` più `test_tray_toggle_item_is_clickable_while_running`; `test_menu_callbacks_are_deferred` è aggiornato, non aggiunto, e quindi non conta).

- [ ] **Step 5: Committa**

```bash
git add kemai_client/exit_handler.py kemai_client/app.py kemai_client/ui/main_window.py kemai_client/tray.py tests/test_exit_handler.py tests/test_tray.py
git commit -m "fix: un unico percorso di uscita che ferma il timesheet prima di terminare"
```

---

### Task 5: Etichetta del vassoio coerente con lo stato

La voce "Avvia" del menu del vassoio dice sempre `t("btn_start")`, anche mentre l'attività è in corso: stesso difetto di classe della issue #1, lo stato non raggiunge il controllo che lo muta. È l'unico task che allarga il perimetro di quanto chiesto, e si stacca da solo se preferisci.

**Files:**
- Modify: `kemai_client/tray.py:51-78` e `kemai_client/tray.py:142-173`
- Test: `tests/test_tray.py`

**Interfaces:**
- Consumes: `AppController.is_running() -> bool`.
- Produce: `toggle_label(is_running: bool) -> str` in `kemai_client.tray`, funzione **pura** che restituisce `t("btn_stop")` se `is_running` è vero, `t("btn_start")` altrimenti. `build_menu` la usa dentro una lambda passata come `text` alla `MenuItem` di pystray.

Estrarla in una funzione pura è la stessa scelta che il progetto ha già fatto con `close_behaviour`, ed è l'unico modo di testarla senza dipendere dagli interni di pystray.

- [ ] **Step 1: Scrivi i test che falliscono**

`test_toggle_label_is_start_when_idle`: `toggle_label(False) == i18n.t("btn_start")`, cioè `"Avvia"`.
`test_toggle_label_is_stop_when_running`: `toggle_label(True) == i18n.t("btn_stop")`, cioè `"Ferma"`.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tray.py -v -k toggle_label`
Expected: FAIL con `ImportError: cannot import name 'toggle_label'`.

- [ ] **Step 3: Implementa il cambio**

Aggiungi `toggle_label` in `tray.py`. Nella `MenuItem` del toggle, passa come primo argomento `lambda item: toggle_label(controller.is_running())` invece di `t("btn_start")`. Nessuna chiave i18n nuova: `btn_start` e `btn_stop` esistono già.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tray.py -v`
Expected: PASS. Suite completa → `172 passed` (170 + 2).

- [ ] **Step 5: Committa**

```bash
git add kemai_client/tray.py tests/test_tray.py
git commit -m "fix(tray): la voce del vassoio dice Ferma mentre l'attivita' e' in corso"
```

---

## Chiusura dell'intervento

Dopo il Task 5, in **un solo commit**:

```bash
git add doc/issues/2026-10-13-github-issues.md doc/plans/
git commit -m "docs: piano e issue #1 (pulsante Ferma)"
```

Non chiudere l'issue #1 su GitHub: è il collega che l'ha aperta e la chiude lui quando ha verificato che il pulsante gli funziona. Aggiungi però un commento alla issue che dice cosa è stato corretto e come verificarlo, così chi l'ha aperta sa dove guardare.

## Passaggi riservati all'umano

**Un agente non deve eseguirli, non deve simularli, e soprattutto non deve dichiarare fatto un passo che non ha potuto verificare.** Se un passo umano non è stato fatto, il comportamento corretto è eseguire tutto il resto e dire esplicitamente quale resta in carico. Un agente che scrive "verificato a mano" senza aver visto nulla sta mentendo.

1. **[UMANO] Avvio e uso reale.** `run_kimai.bat`, Impostazioni → Prova, scegliere cliente/progetto/attività, premere Avvia, verificare che il bottone **diventa grigio ma resta cliccabile e dice "Ferma"**, premere Ferma, verificare su Kimai che il record è chiuso. Questo è il solo test che conta per la issue.
2. **[UMANO] Uscita con attività in corso.** Avvia, poi File → Esci. Verificare che il processo termina davvero (nessuna icona residua nel vassoio) e che il record risulta chiuso su Kimai. Ripetere con Modifica → Esci e con il menu del vassoio.
3. **[UMANO] Chiusura con la X e "Chiudi nel vassoio" attivo.** Con un'attività in corso, premere la X: l'app deve nascondersi, il cronometro deve continuare a girare, e l'attività deve restare aperta. **Non deve fermarsi**: questo è il caso Review Focus #5 ed è il più facile da rompere per sbaglio.
4. **[UMANO] Ricerca dell'errore in Windows.** Dopo una di queste prove, aprire `%APPDATA%\KimaiClient\logs\` e verificare che non ci siano `KimaiError` non gestiti. Se l'errore non è nel log, il difetto è a monte del `log_exception` e va riferito.

## Cosa NON fare

- **Non modificare `kemai_client/api/client.py`**: gli endpoint sono verificati dal vivo e funzionano.
- **Non aggiungere chiavi a `i18n.STRINGS`**: `test_no_extra_keys` asserisce esattamente 32 chiavi.
- **Non cancellare i 3 test strutturali di `tests/test_main_window.py`**: si aggiungono ai 5 di comportamento.
- **Non committare `scheletro.json`**: file non tracciato, non correlato a questo intervento.
- **Non cambiare il default branch del repository** (`qwen38-35b-distill`): è una decisione separata.
- **Non aggiungere dipendenze**: niente `pytest-mock`, le `Mock` di `unittest.mock` bastano e sono già usate in `tests/test_tray.py` e `tests/test_controller.py`.