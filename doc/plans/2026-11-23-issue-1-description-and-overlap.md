# Piano di intervento: Issue #1 — Nuove richieste

**Repository:** `buoncri/kimai-client-desktop`
**Issue:** #1 — "Pulsante Ferma non funziona" (chiuso ma con nuove richieste)
**Autori:** edi1973 (richiedente), buoncri (owner)
**Data:** 2026-11-23

---

## Contesto

Il pulsante Ferma era già stato risolto nel commit `ffece5b` (2026-10-15).
Il commentatore `edi1973` (2026-11-04) chiede due nuove feature:

1. Campo "Descrizione" oltre a Cliente, Progetto, Attività
2. L'arrotondamento a 15 minuti non deve sovrapporsi all'orario precedente

---

## Richiesta 1: Campo "Descrizione"

### Obiettivo
Aggiungere un campo testuale libero "Descrizione" nella finestra principale,
tra la riga "Progetto" e "Attività". Il valore viene inviato al server
solo se non vuoto.

### File da modificare

#### 1. `kemai_client/i18n.py`
Aggiungere al dizionario `STRINGS`:
```python
"label_description": "Descrizione",
```

#### 2. `kemai_client/ui/main_window.py`
- Aggiungere una nuova riga nel grid (tra row=1 e row=2):
  ```python
  # --- Riga 3.5: Descrizione ---
  self._frame_description = ttk.Frame(self._container)
  self._frame_description.grid(row=3, column=0, sticky="we", pady=2)
  ttk.Label(self._frame_description, text=t("label_description")).grid(
      row=0, column=0, sticky="e"
  )
  self._entry_description = ttk.Entry(self._frame_description)
  self._entry_description.grid(row=0, column=1, sticky="we", padx=(4, 0))
  ```
- Modificare `refresh()` per resettare l'entry alla chiusura del timesheet
- Modificare `_on_toggle()` per leggere il valore dall'entry e passarlo

#### 3. `kemai_client/controller.py`
- Aggiungere attributo `_description: str = ""` a `__init__`
- Modificare `start()` per accettare parametro `description: str = ""`
- Modificare `stop()` per azzerare `_description`
- Modificare `toggle()` per leggere dal controller e passare al client
- Aggiungere metodo `set_description(self, description: str) -> None`

#### 4. `kemai_client/api/client.py`
- Modificare `start_timesheet()` per accettare `description: str = ""`
- Nel payload JSON, includere `"description": description` solo se non vuoto

#### 5. `kemai_client/api/endpoints.py`
- (Opzionale) Aggiungere commento che conferma "description" come campo accettato da POST /api/timesheets — già presente nel docstring esistente, nessun cambiamento necessario.

### Test da aggiungere

#### `tests/test_controller.py`
- `test_start_sends_description`: verifica che `start(description="test")` passi
  il parametro al client
- `test_start_omits_empty_description`: verifica che `start()` senza descrizione
  non includa il campo nel payload
- `test_stop_clears_description`: dopo `stop()`, `_description` è vuoto
- `test_toggle_passes_description`: `toggle()` legge l'entry e passa la descrizione

#### `tests/test_client.py`
- `test_start_sends_description_in_json`: verifica che il payload JSON contenga
  `"description": "test"` quando fornita
- `test_start_omits_empty_description`: verifica che il campo `description` non
  sia presente nel JSON se la stringa è vuota

### Dipendenze
- `i18n.py` → `main_window.py`, `controller.py`, `test_controller.py`
- `controller.py` → `client.py`, `test_client.py`
- Nessuna dipendenza circolare

---

## Richiesta 2: Nessuna sovrapposizione con l'arrotondamento a 15 minuti

### Obiettivo
Prima di avviare un timesheet, verificare che non esista un timesheet attivo
il cui `begin` (arrotondato per eccesso alle 15 min) sia ≤ ora corrente.
Se sì, sollevare `RuntimeError` invece di inviare la richiesta al server.

### File da modificare

#### 1. `kemai_client/i18n.py`
Aggiungere:
```python
"err_overlap": "L'attività precedente è ancora in corso. Ferma prima.",
```

#### 2. `kemai_client/api/client.py`
- Aggiungere metodo `_calculate_next_15min_block(dt: datetime) -> datetime`:
  arrotonda per eccesso ai 15 minuti (es. 10:07 → 10:15, 10:15 → 10:15)
- Modificare `start_timesheet()` per accettare un parametro opzionale
  `allow_overlap: bool = False` (per test)
- In `start_timesheet()`: se `allow_overlap` è False e il timesheet attivo
  esiste con begin arrotondato ≤ ora corrente, sollevare `KimaiError`

#### 3. `kemai_client/controller.py`
- Modificare `start()` per:
  1. Chiamare `_client.get_active_timesheet()`
  2. Se esiste un timesheet attivo:
     - Arrotondare il suo `begin` alle 15 min
     - Se arrotondato ≤ ora corrente → sollevare `RuntimeError(t("err_overlap"))`
  3. Altrimenti procedere con la chiamata al server

#### 4. `kemai_client/ui/main_window.py`
- (Opzionale) Mostrare il messaggio di errore in una label sotto il cronometro
  quando `start()` solleva `RuntimeError` — già gestito dal `try/except`
  esistente in `_on_toggle()`? No, `toggle()` non ha try/except.
  Aggiungere try/except in `_on_toggle()` per catturare `RuntimeError`.

### Test da aggiungere

#### `tests/test_controller.py`
- `test_start_fails_when_active_session_overlaps`: simulare un timesheet attivo
  con begin arrotondato a 15 min ≤ ora corrente; `start()` deve sollevare
- `test_start_succeeds_when_no_overlap`: timesheet attivo con begin nel futuro
  (es. 10:00, ora 10:05 → arrotondato a 10:15 > 10:05) → start OK
- `test_start_exactly_on_15min_boundary`: begin = 10:15, ora = 10:15 → overlap
- `test_start_with_no_active_session`: nessun timesheet attivo → start OK

#### `tests/test_client.py`
- `test_get_active_timesheet_returns_begin_for_overlap_check`: verificare che
  `get_active_timesheet()` restituisca il campo `begin` del timesheet attivo
- `test_start_timesheet_checks_overlap`: test del controllo di sovrapposizione
  a livello client

### Logica di sovrapposizione (pseudocodice)
```python
def _timesheet_overlaps_15min(active_ts):
    begin = datetime.strptime(active_ts["begin"], "%Y-%m-%d %H:%M:%S")
    # Arrotonda per eccesso alle 15 min
    minutes = begin.minute
    if minutes % 15 != 0:
        begin = begin.replace(minute=minutes - minutes % 15 + 15, second=0)
    return begin <= datetime.now()
```

### Dipendenze
- `i18n.py` → `controller.py`, `main_window.py`, `test_controller.py`
- `client.py` → `controller.py`
- Nessuna dipendenza circolare

---

## Ordine di implementazione

1. **Richiesta 1 (Descrizione)** — più semplice, modifica lineare
   - i18n → controller → client → main_window → test
2. **Richiesta 2 (Sovrapposizione)** — richiede logica temporale
   - i18n → client → controller → main_window → test

---

## Verifica post-implementation

- `pytest -q` deve passare (221 test esistenti + nuovi)
- Verifica manuale: avviare attività con descrizione, verificare che appaia
  sul server Kimai
- Verifica manuale: provare ad avviare un timesheet quando uno precedente
  è in corso e non ancora passato il blocco di 15 min

---

## Note

- Il progetto usa `pytest` con `unittest.mock` per il testing
- Il `FakeClient` in `test_controller.py` deve essere esteso per supportare
  i nuovi parametri (`description`, `get_active_timesheet` con `begin`)
- Il `FakeTransport` in `test_client.py` deve essere esteso per verificare
  i nuovi campi nel payload JSON
- L'arrotondamento a 15 minuti è un comportamento del server Kimai, non del client.
  Il client deve solo rilevarlo e prevenire la sovrapposizione.
