# Piano di Refactor: Semplificazione del Codice Kimai Desktop Client

**Data**: 2026-10-19  
**Stato**: Design  
**Autore**: Luca  
**Verifica empirica**: grep su `kemai_client/` + `tests/` (commit `3c9c5d8`)

---

## 1. Duplicazioni e Incoerenze Confermate

Tutte le affermazioni sono verificate con grep. Se non è verificato, è marcato **DA VERIFICARE**.

### A. `connect` vs `_connect` in `controller.py`

**Verifica:**
```bash
$ grep -n 'def connect\|def _connect' kemai_client/controller.py
241:    def connect(
274:    def _connect(self, client: KimaiClient) -> None:
```

**Semantica DIVERSA (il piano originale le trattava come "stessa cosa"):**

| | `connect()` | `_connect()` |
|---|---|---|
| Linea controller | 241 | 274 |
| Parametri | `(host, username, token, verify_tls=None)` → crea un nuovo `KimaiClient` dal factory | `(client: KimaiClient)` → inietta un'istanza già costruita |
| Chiamata API | ✅ Chama `self._client.get_version()` per leggere la versione server | ❌ Nessuna chiamata API |
| Uso production | `ui/settings_window.py:156` — test connessione con credenziali dell'utente | Nessun uso in production (0 match in `kemai_client/` tranne definizione) |
| Uso test | `tests/test_controller.py:444-462` — test `connect_applies_*` | `tests/test_controller.py:98-738` — usato in 40+ test |
| Docstring | "Crea il client e restituisce la versione" | "Versione test: inietta un client finto direttamente" |

**Problema:** Non sono duplicate — sono **due operazioni diverse con nome simile**. La convenzione `_*` in Python indica private, ma `_connect` non è chiamata da nessun codice production. È un helper per i test esposto come metodo pubblico.

### B. `load_customers` vs `_load_customers` in `controller.py`

**Verifica:**
```bash
$ grep -n 'def load_customers\|def _load_customers' kemai_client/controller.py
280:    def load_customers(self) -> List[Customer]:
295:    def _load_customers(self) -> List[Customer]:
```

**Differenza (confronto corpo):**

`load_customers` (linea 280):
```python
try:
    self._customers = self._client.list_customers()
    self._truncated = self._client.last_list_truncated
    self.notify()
except KimaiError as exc:
    self._handle_kimai_error(exc, "load_customers")  # ← LOG + set _last_error_msg
    self._customers = []
    self._truncated = False
return self._customers
```

`_load_customers` (linea 295):
```python
try:
    self._customers = self._client.list_customers()
    self._truncated = self._client.last_list_truncated
    self.notify()
except KimaiError:
    self._customers = []
    self._truncated = False
return self._customers
```

**Differenza:** `_load_customers` è la stessa logica **ma senza logging** (evita `setup_logging()` richiesto dai test). È una copia con una riga `except KimaiError` vs `except KimaiError as exc; self._handle_kimai_error(...)`.

**Uso:**
```bash
$ grep -n '_load_customers\|\.load_customers(' kemai_client/ tests/ 2>/dev/null | grep -v __pycache__
kemai_client/ui/main_window.py:170:        self._controller.load_customers()
kemai_client/ui/settings_window.py:193:        self._controller.load_customers()
tests/test_controller.py:102:        ctrl._load_customers()
tests/test_controller.py:111:        ctrl._load_customers()
# ... 40+ test che usano _load_customers()
```

### C. `_get_id` in `api/client.py` — **NON duplicata**

```bash
$ grep -n '_get_id' kemai_client/api/client.py
67:def _get_id(item: dict) -> int | None:
# ... 5 usi (linee 271, 290, 309, 337, 363)
```

**Una sola definizione, 5 usi.** Il piano originale errato diceva "doppia def".

### D. `_select_by_id` — **NON duplicato in geometry.py o app.py**

```bash
$ grep -n '_select_by_id' kemai_client/ui/main_window.py kemai_client/geometry.py kemai_client/app.py
kemai_client/ui/main_window.py:26:def _select_by_id(combo, items, wanted_id) -> None:
kemai_client/ui/main_window.py:219:        _select_by_id(...)
kemai_client/ui/main_window.py:221:        _select_by_id(...)
kemai_client/ui/main_window.py:223:        _select_by_id(...)
# geometry.py: 0 match
# app.py: 0 match
```

**Una sola definizione in `ui/main_window.py`, usata 3 volte nella stessa classe.** Non esiste duplicazione da "estrarre".

### E. `geometry.py` contiene solo `octagon_points`

```bash
$ grep 'def ' kemai_client/geometry.py
11:def octagon_points(cx: float, cy: float, r: float) -> list[float]:
```

**Uso:**
```bash
$ grep -rn 'from kemai_client.geometry\|import octagon_points' kemai_client/
kemai_client/tray.py:21:from kemai_client.geometry import octagon_points
kemai_client/ui/widgets.py:12:from kemai_client.geometry import octagon_points
```

Due consumer in file diversi. `geometry.py` è una pure function geometrica, non un "helper UI".

### F. Logging inconsistente in `controller.py`

```bash
$ grep -n 'log_exception\|_handle_kimai_error' kemai_client/controller.py
22:from kemai_client.logging_setup import log_exception
105:            log_exception(self._logger, exc, "check_active_session")     # ← pattern A diretto
290:            self._handle_kimai_error(exc, "load_customers")               # ← pattern B wrapper
325:            log_exception(self._logger, exc, "select_customer")           # ← pattern A diretto
346:            log_exception(self._logger, exc, "select_project")            # ← pattern A diretto
387:            self._handle_kimai_error(exc, "start_timesheet")              # ← pattern B wrapper
447:    def _handle_kimai_error(self, exc, context): ...                    # ← pattern B
```

Due pattern incoerenti nello stesso file: `log_exception(...)` diretto vs `self._handle_kimai_error(...)` wrapper.

### G. `exit_handler.py` usa `log_exception` diretto (senza wrapper)

```bash
$ grep -n 'log_exception' kemai_client/exit_handler.py
24:from kemai_client.logging_setup import log_exception
48:            log_exception(logger, exc, "stop_timesheet")
57:        log_exception(logger, exc, "tray_stop")
```

Non usa il wrapper `_handle_kimai_error` (che è un metodo di istanza) e non ha logging inconsistente nel suo modulo, ma non è coerente con `controller.py`.

### H. Import cycle potenziale

```bash
# main_window imports from widgets:
kemai_client/ui/main_window.py:18:from kemai_client.ui.widgets import StopButton, format_duration

# widgets.py imports geometry (no circular with main_window)
kemai_client/ui/widgets.py:12:from kemai_client.geometry import octagon_points

# Main window is imported by app.py:
kemai_client/app.py:20:from kemai_client.ui.main_window import MainWindow
```

**Rischio:** Se si sposta `_select_by_id` in `widgets.py`, `main_window.py` importerà da `widgets`. Se `widgets.py` non importa nulla da `main_window.py`, **non c'è ciclo**. Verificato: `widgets.py` importa solo `geometry`. OK.

---

## 2. Piano di Refactor

### Step 1: Unificare `load_customers` / `_load_customers`

**Obiettivo:** Eliminare la copia quasi-identica, usare un unico metodo con parametro opzionale `for_test`.

**File coinvolti:** `kemai_client/controller.py`

**Modifiche:**
```python
# RIMUOVERE: def _load_customers (linee 295-303)
# SOSTITUIRE: la riga 289-291 con un parametro opzionale:

def load_customers(self, *, for_test: bool = False) -> List[Customer]:
    try:
        self._customers = self._client.list_customers()
        self._truncated = self._client.last_list_truncated
        self.notify()
    except KimaiError as exc:
        if not for_test:
            self._handle_kimai_error(exc, "load_customers")
        self._customers = []
        self._truncated = False
    return self._customers
```

**File che chiamano:**
- `kemai_client/ui/main_window.py:170` → `self._controller.load_customers()` (NO CHANGE)
- `kemai_client/ui/settings_window.py:193` → `self._controller.load_customers()` (NO CHANGE)
- `tests/test_controller.py:102, 111, ...` → `ctrl._load_customers()` → `ctrl.load_customers(for_test=True)` (24+ chiamate)

**Rischio:** Alto per i test (40+ chiamate). Tutti i test devono essere aggiornati.

**Verifica:**
```bash
$ grep -c '_load_customers' tests/test_controller.py   # 24 occurrences
$ python -m pytest tests/test_controller.py          # dopo update, deve passare
```

**Beneficio:** Elimina 8 righe duplicate. Unico punto di manutenzione per `list_customers()`.

---

### Step 2: Normalizzare `connect` / `_connect` (conservativo)

**Obiettivo:** Rinominare `_connect` in `inject_client` (o mantenere come `set_client`) e documentare che è pubblico per test. **Non eliminarlo** perché è necessario per l'iniezione del fake in 40+ test.

**File coinvolti:** `kemai_client/controller.py`, `tests/test_controller.py`

**Modifiche:**
```python
# RINOMINARE (linea 274):
# def _connect(self, client: KimaiClient) -> None:
def set_client(self, client: KimaiClient) -> None:
    """Inietta un client finto (per test) o reale (non usato in production).

    A differenza di connect(), non chiama get_version().
    """
    self._client = client
```

**File che chiamano:**
- `tests/test_controller.py:40-738` → 40+ occorrenze `ctrl._connect(client)` → `ctrl.set_client(client)`
- **Nessun uso in production** (zero match in `kemai_client/` oltre la definizione)

**Rischio:** Medio. Richiede update di tutti i test. `connect()` production resta intatto.

**Verifica:**
```bash
$ grep -c 'ctrl._connect' tests/test_controller.py  # ~50 occorrenze
$ grep '_connect' kemai_client/                     # solo la definizione in controller.py
$ python -m pytest tests/test_controller.py
```

**Beneficio:** Naming chiaro che `_connect` era private è rimossa. La differenza semantica con `connect()` è esplicita (nome diverso).

---

### Step 3: Unificare i due pattern di logging in `controller.py`

**Obiettivo:** Eliminare l'alternanza tra `log_exception(...)` diretto e `_handle_kimai_error(...)`.

**File coinvolti:** `kemai_client/controller.py`

**Modifiche:**
```python
# RIMUOVERE: _handle_kimai_error wrapper (linee 447-453)
# OPPURE: mantenerlo ma usarlo SEMPRE (più sicuro, meno rischio)

# Opzione (conservativa): usare _handle_kimai_error SEMPRE
# Sostituisce le 3 occorrenze di log_exception(...) diretto:

# Linea 105:
log_exception(self._logger, exc, "check_active_session")
# → diventa:
self._handle_kimai_error(exc, "check_active_session")

# Linea 325:
log_exception(self._logger, exc, "select_customer")
# → diventa:
self._handle_kimai_error(exc, "select_customer")

# Linea 346:
log_exception(self._logger, exc, "select_project")
# → diventa:
self._handle_kimai_error(exc, "select_project")

# Linea 387:
self._handle_kimai_error(exc, "start_timesheet")  # ← già pattern B, no change
# Linea 290:
self._handle_kimai_error(exc, "load_customers")  # ← già pattern B, no change
```

**Nota sulla linea 406:** `stop()` usa `self._last_error_msg = t("err_network")` e **non** `log_exception` intenzionalmente (commento: "non chiamiamo log_exception qui per il test di network loss"). Lasciare così.

**File che importano `log_exception` da `controller.py`:**
```bash
$ grep -n 'from kemai_client.logging_setup import log_exception' kemai_client/
kemai_client/controller.py:22
kemai_client/exit_handler.py:24
kemai_client/logging_setup.py:1  (la definizione)
```

Se `_handle_kimai_error` rimane come wrapper che chiama `log_exception`, il `import log_exception` in controller.py diventa superfluo. **DA VERIFICARE** se dopo l'unificazione serve ancora l'import diretto.

**Rischio:** Basso. Le chiamate `log_exception` sono in try/except, sostituirle con il wrapper che fa la stessa cosa.

**Verifica:**
```bash
$ grep 'log_exception.*self._logger.*' kemai_client/controller.py  # 3 occorrenze
$ grep '_handle_kimai_error.*' kemai_client/controller.py         # 2 occorrenze (già B)
$ python -m pytest tests/test_controller.py
```

**Beneficio:** Un unico pattern di gestione errori in tutto il controller.

---

### Step 4 (opzionale): Costanti in `kemai_client/constants.py`

**Obiettivo:** Centralizzare magic numbers.

**File coinvolti:** `kemai_client/constants.py` (nuovo), `kemai_client/ui/main_window.py`, `kemai_client/api/client.py`, `kemai_client/tray.py`

**File da aggiornare (verifica grep):**

```bash
# main_window.py: _WIDTH, _HEIGHT, _START_TICK_DELAY_MS
$ grep -n '_WIDTH\|_HEIGHT\|_START_TICK' kemai_client/ui/main_window.py
# 60: self._root.geometry(f"{_WIDTH}x{_HEIGHT}")
# 23: _WIDTH = 282
# 24: _HEIGHT = 312
# 25: _START_TICK_DELAY_MS = 1000

# client.py: DEFAULT_TIMEOUT, DEFAULT_PAGE_SIZE
$ grep -n 'DEFAULT_TIMEOUT\|DEFAULT_PAGE_SIZE\|10\.0\|100' kemai_client/api/client.py
# 20: DEFAULT_TIMEOUT = 10.0
# endpoints.py: DEFAULT_PAGE_SIZE = 100

# tray.py: ICON_SIZE = 64
$ grep -n 'ICON_SIZE' kemai_client/tray.py
# 23: ICON_SIZE = 64
```

**Contenuto `constants.py`:**
```python
"""Costanti globali dell'applicazione."""

# API
DEFAULT_TIMEOUT: float = 10.0

# UI
WINDOW_WIDTH: int = 282
WINDOW_HEIGHT: int = 312
START_TICK_DELAY_MS: int = 1000

# Tray
ICON_SIZE: int = 64
```

**Rischio:** Basso. È un refactoring puramente di import.

**Verifica:**
```bash
$ python -m pytest tests/   # nessun test dovrebbe dipendere da _WIDTH direttamente
$ grep '_WIDTH\|_HEIGHT' tests/   # DA VERIFICARE
```

**Beneficio:** Tutte le costanti in un unico file. Aggiungere una nuova costante richiede un edit in un solo posto.

---

### Step 5: Documentare e unificare `geometry.py` come modulo pubblico

**Obiettivo:** `geometry.py` è una pure function utile. Documentarla come modulo pubblico, non "helper geometrico" nascosto.

**File coinvolti:** `kemai_client/geometry.py`

**Modifiche:**
- Aggiungere docstring modulo
- Aggiungere type hint a `octagon_points` se manca (verificare)
- Nessuna modifica funzionale

**Rischio:** Minimo.

**Verifica:**
```bash
$ grep 'def ' kemai_client/geometry.py
$ python -c "from kemai_client.geometry import octagon_points; print(octagon_points(0,0,1))"
```

**Beneficio:** Codice documentato.

---

## 3. Rischi Specifici e Mitigazione

| Rischio | Passo | Probabilità | Mitigazione |
|---------|-------|-------------|-------------|
| 40+ test `ctrl._connect` devono essere aggiornati | 2 | Alta | Script grep+sed: `sed -i 's/ctrl._connect/ctrl.set_client/g' tests/test_controller.py` |
| `load_customers(for_test=True)` rompe test | 1 | Media | `sed -i 's/_load_customers/load_customers(for_test=True)/g' tests/test_controller.py` |
| Import cycle se `widgets.py` importa `main_window` | 1/2 | Bassa (verificato: non succede) | Controllare con `python -c "import kemai_client.ui.widgets"` |
| `constants.py` import in `client.py` crea circular con `endpoints.py`? | 4 | Bassa | `client.py` importa `endpoints` → `constants.py` non importa nulla di `api/`. OK. |
| `exit_handler.py` logging pattern non unificato | 3 | Bassa | Lasciare così: `exit_handler.py` non ha _handle_kimai_error (non è in controller). In unificare, aggiungere un wrapper standalone se serve. |

---

## 4. Tabella Riassuntiva

| Step | Rischio | Beneficio | Test |
|------|---------|-----------|------|
| 1. Unificare `load_customers`/`_load_customers` | **Alto** (40+ test) | ⭐ Unica sorgente di `list_customers()` | `grep _load_customers → sed → pytest` |
| 2. Rinominare `_connect` → `set_client` | **Medio** (~50 test) | Naming chiaro, separa semantica da `connect()` | `sed → pytest` |
| 3. Unificare logging pattern | Basso | Unico pattern errori in controller | 3 replace + pytest |
| 4. `constants.py` | Basso | Centralizzazione costanti | 5 replace import + pytest |
| 5. `geometry.py` doc | Minimo | Documentazione | `python -c import` |

**Ordine consigliato:** 3 → 4 → 5 → 2 → 1 (basso rischio → alto rischio, verificare ogni step prima di procedere).

---

## 5. Cosa è stato RIMOSSO dal piano originale (errori)

| Affermazione originale | Stato |
|------------------------|-------|
| `_select_by_id` duplicato in `geometry.py` | ❌ **Non esiste** |
| `_select_by_id` duplicato in `app.py` | ❌ **Non esiste** |
| `_select_by_id` duplicato in `ui/main_window.py` | ✅ Esiste, 1 definizione, 3 usi (non duplicato) |
| `_get_id` duplicata in `api/client.py` | ❌ **Non esiste** (1 definizione, 5 usi) |
| `connect` / `_connect` = "stessa cosa" | ❌ Semantica diversa (factory + API call vs pure iniezione) |
