# Kimai Desktop Client (Tkinter) — Piano di Implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un client desktop Python/Tkinter che replica le tre finestre del client KEMAI e le collega a un'istanza Kimai 1.15 reale, permettendo di avviare e fermare attività di time tracking.

**Architecture:** Pacchetto modulare a strati. `AppController` è l'unico detentore dello stato; le finestre Tkinter non chiamano mai l'API, e `KimaiClient` non sa nulla di Tkinter. Questo confine è ciò che rende la logica testabile senza aprire una finestra. Tutti i path degli endpoint vivono in un solo modulo, perché il probing dell'istanza reale non è ancora stato fatto.

**Tech Stack:** Python 3.10+, Tkinter (stdlib), `requests`, `pystray` + `Pillow`, `pytest`.

**Spec:** `doc/plans/2026-09-30-kemai-client-design.md` — il piano argomenta dalla spec, quindi la spec viaggia con il piano; chi esegue legge entrambi.

## Preparazione ambiente (una tantum, prima del Task 1)

**`python` non funziona su questa macchina.** Il comando `python` nel PATH è uno stub
di 0 byte del Microsoft Store, non un interprete: si presenta come Python ma non
esegue nulla. **Non tentare di usarlo e non tentare di diagnosticarlo**: è noto.

Tutti i comandi di questo piano usano quindi l'interprete dell'ambiente virtuale,
`.venv\Scripts\python.exe`, che va creato una volta sola:

```bash
"C:\Users\luca\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
.venv\Scripts\python.exe -m pip install "requests>=2.31" "pystray>=0.19" "Pillow>=10.0" "pytest>=8.0"
```

Se `.venv\Scripts\python.exe` esiste già, salta questa sezione. La directory `.venv` è
in `.gitignore` e non va committata.

Il comando da usare in ogni task, senza eccezioni:

```
.venv\Scripts\python.exe -m pytest <percorso> -v
```

## Stato di esecuzione

| Task | Stato | Commit |
|---|---|---|
| 1. Modelli, endpoint ed errori | **fatto** | `1493882` |
| 2. KimaiClient | **fatto** (manca solo l'estensione del paging, vedi sotto) | `e7bd174` |
| 3. Configurazione persistente | da fare | — |
| 4. Stringhe italiane | da fare | — |
| 5. Script di probing | da fare | — |
| 6. Logging su file | da fare | — |
| 7. AppController | da fare | — |
| 8. Widget e utilità UI | da fare | — |
| 9. Finestra principale | da fare | — |
| 10. Finestra impostazioni e dialog | da fare | — |
| 11. System tray e composizione | da fare | — |
| 12. Dipendenze, documentazione, verifica | da fare | — |

**Il Task 1 è già completo: non lo rifare.** Se devi riprenderlo, verifica e basta:
`.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_endpoints.py tests/test_errors.py -v` deve dare 28 PASS, poi passa al Task 3.

**Il Task 2 è parzialmente completo.** Il client esiste e ha 32 test verdi, ma **non
ha ancora l'estensione del paging** (i quattro test `test_lists_request_explicit_page_size`,
`test_exact_page_size_flags_truncation`, `test_short_page_is_not_truncation`,
`test_truncation_flag_resets_between_calls`) né le costanti `PARAM_PAGE`, `PARAM_SIZE`,
`DEFAULT_PAGE_SIZE` in `endpoints.py`. Ecco il lavoro residuo esatto:

1. in `kemai_client/api/endpoints.py` aggiungi `PARAM_PAGE = "page"`, `PARAM_SIZE = "size"`, `DEFAULT_PAGE_SIZE = 200`
2. in `tests/test_endpoints.py` aggiungi `test_default_page_size_is_a_positive_int`
3. in `tests/test_client.py` aggiungi i quattro test di paging e `test_get_version_reads_the_version`
4. in `kemai_client/api/client.py` fai passare `PARAM_SIZE` nei `params` di ogni `list_*`, e imposta `self.last_list_truncated`
5. verifica con `.venv\Scripts\python.exe -m pytest -v` — devono dare 66 PASS

Nel repository esiste anche `app_gui.py`, un demo Tkinter generico **non collegato a
questo progetto**, presente prima del suo inizio. Non lo modificare, non lo usare come
riferimento, non lo cancellare: non è parte dell'architettura descritta qui.

## Passaggi riservati all'umano

Alcuni step di questo piano non sono eseguibili da un agente: richiedono di guardare una
finestra a schermo, o una macchina collegata alla rete interna. Sono marcati
`**[UMANO]**`.

**Un agente non deve eseguirli, non deve simularli, e soprattutto non deve dichiarare
fatto un passo che non ha potuto verificare.** Il comportamento corretto è eseguire tutto
il resto e riferire esplicitamente quale passo resta in carico all'umano. Un agente che
scrive "verificato a mano" senza aver visto nulla sta mentendo, ed è peggio di un agente
che si ferma e lo dichiara.

Elenco completo dei passaggi umani: Task 5 Step 6 e 7, Task 9 Step 4, Task 10 Step 4,
Task 11 Step 7, Task 12 Step 5.

Tutti gli altri step sono automatizzabili e **devono** essere eseguiti davvero.

## Global Constraints

- Python 3.10 o superiore.
- Dipendenze runtime **solo** `requests` e `pystray`; `Pillow` arriva come dipendenza di `pystray` per generare l'icona. Nient'altro: niente `customtkinter`, niente `PyQt`, niente ORM.
- Tutti i test devono girare **offline**: nessun test apre un socket, nessun test richiede l'istanza Kimai, nessun test richiede uno schermo X.
- **Tkinter gira sempre e solo nel main thread.** Nessuna operazione Tkinter da un thread diverso, senza eccezioni.
- I callback di `pystray` devono passare da `root.after(0, fn)` prima di toccare qualsiasi widget.
- L'interfaccia è **interamente in italiano**; nessuna stringa visibile all'utente è hardcoded in un modulo UI. Tutte passano da `i18n.t()`.
- Il file di configurazione sta in `%APPDATA%\KimaiClient\config.json`, **fuori dall'albero del repository**.
- **Il token API non compare mai in un file tracciato da git**, né qui, né nei test, né nei log. Nei test si usa sempre la costante fittizia `TEST_TOKEN = "test-token-not-real"`.
- Nessun segnaposto `TBD` o `TODO` nel codice finale.
- La documentazione e i commenti sono in italiano; i nomi di simboli pubblici sono in inglese.

## Review Focus

Sei classi di input o condizioni che la spec implica, che nessun test dei task esercita, ordinate per probabilità di mordere. Ogni riga ha il suo test assegnato al task che possiede il codice.

1. **Server Kimai che risponde HTML invece di JSON** (proxy d'azienda, pagina di errore, redirect di autenticazione) → deve diventare un `KimaiError` con messaggio italiano, non un `JSONDecodeError` grezzo. *Test in Task 2.*
2. **Rete che cade mentre l'attività è in corso** → il cronometro locale **non** si ferma e lo stato "in corso" resta intatto; la sincronizzazione avviene al tentativo successivo. *Test in Task 7.*
3. **Progetto selezionato senza attività assegnate** → la cascata si ferma, il pulsante Avvia resta disabilitato e l'utente riceve un motivo, non un silenzio. *Test in Task 7.*
4. **Token ruotato o revocato dopo la configurazione** → messaggio "credenziali non valide" e proposta di riaprire le impostazioni, senza traccia tecnica a schermo. *Test in Task 2 e Task 7.*
5. **Chiusura della finestra col vassoio attivo e timer in corso** → l'app si nasconde, il timer continua, e l'uscita dal menu del vassoio termina **davvero** il processo (nessun thread daemon che tiene vivo Python). *Test in Task 11 sulla funzione di decisione, verifica manuale per il resto.*
6. **Elenco troncato dal server** → se l'utente ha più di `DEFAULT_PAGE_SIZE` clienti, l'app deve **dichiarare** che la lista è limitata, non mostrarla come se fosse completa. *Test in Task 2 (euristica lato client) e Task 7 (esposizione alla UI).*

---

### Task 1: Modelli, endpoint ed errori — ✅ FATTO (commit `1493882`)

**Non rifarlo.** Se devi solo riprenderlo, verifica con
`.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_endpoints.py tests/test_errors.py -v`
che dia 28 PASS, e vai al Task 3.

Fondazione su cui tutto il resto poggia. Nessuna I/O, quindi test banali e veloci.

**Files:**
- Create: `kemai_client/__init__.py`
- Create: `kemai_client/models.py`
- Create: `kemai_client/api/__init__.py`
- Create: `kemai_client/api/endpoints.py`
- Create: `kemai_client/api/errors.py`
- Test: `tests/test_models.py`, `tests/test_endpoints.py`

**Interfaces:**
- Consumes: nulla (primo task).
- Produces:
  - `kemai_client.models`: `Customer(id: int, name: str)`, `Project(id: int, name: str, customer_id: int)`, `Activity(id: int, name: str, project_id: int | None = None)`, tutti `frozen=True` e con proprietà `display -> str` che restituisce `name`.
  - `kemai_client.api.endpoints`: costanti `BASE_PATH = "/api"`, `VERSIONS`, `CUSTOMERS`, `PROJECTS`, `ACTIVITIES`, `TIMESHEETS`, `TIMESHEET_START`, `TIMESHEET_STOP`, ciascuna come `str` costruita da `BASE_PATH`; più i **nomi dei parametri di filtro** `PARAM_CUSTOMER = "customer"` e `PARAM_PROJECT = "project"`, e i parametri di paging `PARAM_PAGE = "page"`, `PARAM_SIZE = "size"`, con `DEFAULT_PAGE_SIZE = 200`. Anche i nomi dei parametri sono ipotesi non verificate sul Kimai 1.15 reale, quindi vivono qui con i path: correggerli dopo il probing tocca un file solo.
  - `kemai_client.api.errors`: `KimaiError(Exception)`, `KimaiAuthError(KimaiError)`, `KimaiNetworkError(KimaiError)`, `KimaiNotFoundError(KimaiError)`. Ogni `KimaiError` accetta `(message: str, status: int | None = None)` e espone `.status`.

- [ ] **Step 1: Scrivi i test che falliscono**

`tests/test_endpoints.py` — asserisce che ogni costante richiesta dalla spec esista e inizi con `BASE_PATH`, e che `join(BASE_PATH, "customers")` produca `"/api/customers"`. Il test deve dimostrare che i path sono derivati da `BASE_PATH` e non scritti a mano, così il probing li può correggere da un posto solo. Verifica anche che `PARAM_CUSTOMER`, `PARAM_PROJECT`, `PARAM_PAGE`, `PARAM_SIZE` siano stringhe non vuote, per lo stesso motivo: i nomi dei parametri sono ipotesi come i path e devono stare nello stesso file. Aggiungi `test_default_page_size_is_a_positive_int` che asserisce `endpoints.DEFAULT_PAGE_SIZE > 0`, perché un valore a zero o negativo produrrebbe una richiesta priva di elementi e un elenco sempre vuoto, senza alcun errore visibile.

`tests/test_models.py` — asserisce che `Customer(1, "Acme").display == "Acme"`, che due `Customer` con lo stesso `id` e `name` siano uguali (`frozen=True` dà `__eq__`), e che un `Customer` non sia hashable-dopo-mutazione, cioè che l'assegnazione di un campo sollevi `dataclasses.FrozenInstanceError`.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_endpoints.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client'`

- [ ] **Step 3: Implementa i tre moduli**

`models.py` con tre `@dataclass(frozen=True)`, ciascuna con `display` come `@property`.

`endpoints.py` con `BASE_PATH = "/api"` e le altre costanti definite per composizione, ad esempio `CUSTOMERS = f"{BASE_PATH}/customers"`.

`errors.py` con le quattro classi. `KimaiError.__init__(self, message: str, status: int | None = None)` memorizza entrambi e passa `message` a `super().__init__`.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_endpoints.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/__init__.py kemai_client/models.py kemai_client/api/ tests/test_models.py tests/test_endpoints.py
git commit -m "feat: modelli, endpoint ed errori del client Kimai"
```

---

### Task 2: KimaiClient — ⚠️ PARZIALE (commit `e7bd174`)

**Non riscrivere il client: esiste già e ha 32 test verdi.** Manca solo l'estensione del
paging, descritta in fondo a questo task. Parti da lì, non dall'inizio.

Il cuore dell'integrazione. L'iniezione di `transport` è il seam che rende tutto testabile offline.

**Files:**
- Create: `kemai_client/api/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `Customer`, `Project`, `Activity` da `kemai_client.models`; costanti da `kemai_client.api.endpoints`; le quattro eccezioni da `kemai_client.api.errors`.
- Produces:
  - `class KimaiClient` con `__init__(self, base_url: str, username: str, token: str, transport: Transport | None = None, timeout: float = 10.0)`.
  - Attributo pubblico `last_list_truncated: bool`, impostato a `True` dall'ultima
    chiamata a `list_customers`, `list_projects` o `list_activities` quando la risposta
    contiene **esattamente** `DEFAULT_PAGE_SIZE` elementi. È l'euristica di §8.3 della
    spec: non richiede di credere a `X-Total-Count`, che è un'ipotesi non verificata, e
    nel caso peggiore avvisa inutilmente invece di mentire in silenzio.
  - Protocollo `Transport` in `kemai_client/api/client.py`: metodo `request(self, method: str, url: str, *, headers: dict, params: dict | None = None, json: dict | None = None, timeout: float) -> Response`. `Response` ha `.status_code: int`, `.headers: dict`, `.json() -> Any`, `.text: str`.
  - `get_version(self) -> str`
  - `test_connection(self) -> str` (alias che chiama `get_version` e solleva `KimaiAuthError` su 401/403)
  - `list_customers(self) -> list[Customer]`
  - `list_projects(self, customer_id: int) -> list[Project]`
  - `list_activities(self, project_id: int) -> list[Activity]`
  - `start_timesheet(self, project_id: int, activity_id: int) -> int` (restituisce l'id del timesheet)
  - `stop_timesheet(self, timesheet_id: int) -> None`
  - `create_project(self, name: str, customer_id: int) -> Project`

- [ ] **Step 1: Scrivi i test che falliscono**

Costruisci in `tests/test_client.py` un `FakeTransport` che registra le chiamate e restituisce risposte preparate, con `TEST_TOKEN = "test-token-not-real"` come credenziale fittizia.

Casi da coprire, con i valori esatti:

| Test | Asserzione |
|---|---|
| `test_headers_auth` | ogni richiesta porta `X-AUTH-USER` e `X-AUTH-TOKEN` |
| `test_customers_url` | `list_customers()` chiama `https://host/api/customers` |
| `test_projects_filtered` | `list_projects(7)` passa `params={"customer": 7}`, usando `PARAM_CUSTOMER` da `endpoints` e non la stringa letterale |
| `test_activities_filtered` | `list_activities(9)` passa `params={"project": 9}`, usando `PARAM_PROJECT` da `endpoints` |
| `test_parses_uppercase_ids` | da `[{"ID": 1, "name": "Acme"}]` ottiene `Customer(1, "Acme")` |
| `test_parses_list_payload` | da `{"customers": [...]}` ottiene comunque la lista, senza `KeyError` |
| `test_start_returns_id` | `start_timesheet(9, 3)` con risposta `{"id": 42}` restituisce `42` |
| `test_auth_error_on_401` | stato 401 solleva `KimaiAuthError` con `.status == 401` |
| `test_network_error_wraps` | `Transport` che solleva `OSError` produce `KimaiNetworkError`, mai `OSError` grezza |
| **`test_html_response_becomes_kimai_error`** | **Review Focus 1:** risposta 200 con `<html>` e `Content-Type: text/html` solleva `KimaiError`, non `JSONDecodeError` |
| **`test_invalid_token_message`** | **Review Focus 4:** `KimaiAuthError` espone un messaggio in italiano che non contiene il token né lo status grezzo |
| `test_get_version_reads_the_version` | da `{"version": "1.15"}` ottiene `"1.15"` |
| `test_lists_request_explicit_page_size` | ogni `list_*` passa `params` con `endpoints.PARAM_SIZE: endpoints.DEFAULT_PAGE_SIZE`, senza affidarsi al default del server |
| `test_exact_page_size_flags_truncation` | una risposta con **esattamente** `DEFAULT_PAGE_SIZE` elementi lascia `client.last_list_truncated is True` |
| `test_short_page_is_not_truncation` | una risposta con meno elementi di `DEFAULT_PAGE_SIZE` lascia `client.last_list_truncated is False` |
| `test_truncation_flag_resets_between_calls` | un elenco troncato seguito da uno completo lascia il flag a `False`: il flag descrive l'ultima chiamata, non la sessione |

Le ultime quattro righe coprono la troncatura di §8.3 della spec. Costruisci le risposte
troncate con una lista comprehension di lunghezza `endpoints.DEFAULT_PAGE_SIZE`, non
scrivendo 200 elementi a mano.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_client.py -v`
Expected: FAIL con `ImportError: cannot import name 'KimaiClient'`

- [ ] **Step 3: Implementa `KimaiClient` in `kemai_client/api/client.py`**

`_request(self, method: str, path: str, *, params=None, json=None) -> Any` è l'unico punto che parla con il transport: costruisce l'URL con `urljoin`, aggiunge gli header, chiama il transport dentro `try/except OSError` e converte in `KimaiNetworkError`.

Ordine di gestione in `_request`, che è il comportamento centrale del modulo:
1. `except OSError` → `KimaiNetworkError` con messaggio italiano
2. `status in (401, 403)` → `KimaiAuthError`
3. `status == 404` → `KimaiNotFoundError`
4. `status >= 400` → `KimaiError` con `message` letta da `.json().get("message")` se presente, altrimenti `f"Errore del server Kimai ({status})"`
5. `Content-Type` senza `json` → `KimaiError("Risposta non valida dal server Kimai")` — questo è il ramo che copre il Review Focus 1
6. altrimenti `.json()`

`_as_list(payload)` gestisce sia la lista diretta sia il dizionario con una chiave, ed è il motivo per cui il parsing non si rompe su variazioni di formato.

Ogni messaggio di errore va in italiano e **mai** contiene il token o gli header.

Ogni `list_*` passa `endpoints.PARAM_SIZE` con `endpoints.DEFAULT_PAGE_SIZE` nei `params`, unendo il proprio filtro se c'è. Dopo aver estratto la lista, imposta `self.last_list_truncated = len(items) >= endpoints.DEFAULT_PAGE_SIZE`. Non richiedere il totale: `X-Total-Count` è un'ipotesi non verificata, e aggiungere un test che finge di averlo letto produrrebbe un test che passa senza mai essere eseguito contro il server vero.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_client.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/api/client.py tests/test_client.py
git commit -m "feat: KimaiClient con transport iniettabile e gestione errori"
```

#### Lavoro residuo: estensione del paging

I passi da 1 a 5 sono **già eseguiti** (commit `e7bd174`): `client.py` esiste, ha
`FakeTransport` in `tests/test_client.py` e 32 test verdi. Esegui solo questi cinque passi.

- [ ] **Step R1: Aggiungi le costanti di paging a `kemai_client/api/endpoints.py`**

```python
PARAM_PAGE = "page"
PARAM_SIZE = "size"
DEFAULT_PAGE_SIZE = 200
```

- [ ] **Step R2: Aggiungi `test_default_page_size_is_a_positive_int` a `tests/test_endpoints.py`**

Asserisce `endpoints.DEFAULT_PAGE_SIZE > 0` e che sia un `int`. Un valore zero o negativo
produrrebbe una richiesta priva di elementi e un elenco sempre vuoto, senza alcun errore
visibile.

- [ ] **Step R3: Aggiungi i cinque test di paging a `tests/test_client.py`**

Riutilizza il `FakeTransport` e `make_client` già presenti in quel file: non crearne uno
nuovo. Costruisci la risposta troncata con
`[{"id": i, "name": f"C{i}"} for i in range(endpoints.DEFAULT_PAGE_SIZE)]`, senza
scrivere 200 elementi a mano. I test sono `test_get_version_reads_the_version`,
`test_lists_request_explicit_page_size`, `test_exact_page_size_flags_truncation`,
`test_short_page_is_not_truncation`, `test_truncation_flag_resets_between_calls`.

- [ ] **Step R4: Fai fallire i test**

Run: `.venv\Scripts\python.exe -m pytest tests/test_client.py -v`
Expected: FAIL. I test nuovi falliscono perché `last_list_truncated` non esiste e
`DEFAULT_PAGE_SIZE` non è importabile da `endpoints`.

- [ ] **Step R5: Implementa in `kemai_client/api/client.py`**

In `__init__` aggiungi `self.last_list_truncated: bool = False`. In ogni `list_*` aggiungi
`endpoints.PARAM_SIZE` ai `params` con il valore di `endpoints.DEFAULT_PAGE_SIZE`, e dopo
aver estratto la lista da `_as_list` imposta `self.last_list_truncated = len(items) >= endpoints.DEFAULT_PAGE_SIZE`.
Non leggere `X-Total-Count`: è un'ipotesi non verificata, e costruirci sopra produrrebbe
un test che passa senza essere mai stato eseguito contro il server vero.

- [ ] **Step R6: Verifica e committa**

Run: `.venv\Scripts\python.exe -m pytest -v`
Expected: 66 PASS, nessuno fallito.

```bash
git add kemai_client/api/client.py kemai_client/api/endpoints.py tests/test_client.py tests/test_endpoints.py
git commit -m "feat: dichiara la troncatura degli elenchi invece di tacere"
```

---

### Task 3: Configurazione persistente

**Files:**
- Create: `kemai_client/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nessuno.
- Produces:
  - `@dataclass Config` con campi `host: str = ""`, `username: str = ""`, `token: str = ""`, `close_to_tray: bool = False`, `last_customer_id: int | None = None`, `last_project_id: int | None = None`.
  - `default_path() -> Path` che restituisce `Path(os.environ["APPDATA"]) / "KimaiClient" / "config.json"`.
  - `load(path: Path | None = None) -> Config`
  - `save(config: Config, path: Path | None = None) -> None`
  - `is_configured(config: Config) -> bool` che è `True` solo se host, username e token sono tutti non vuoti.

- [ ] **Step 1: Scrivi i test che falliscono**

| Test | Asserzione |
|---|---|
| `test_default_path_under_appdata` | il percorso termina con `KimaiClient/config.json` |
| `test_save_load_roundtrip` | `save` poi `load` restituisce un `Config` identico, con `close_to_tray=True` e un `last_customer_id` valorizzato |
| `test_load_missing_file` | su percorso inesistente restituisce un `Config` di default, senza sollevare eccezioni |
| `test_load_corrupt_file` | su JSON malformato restituisce il default, senza sollevare eccezioni |
| `test_save_is_atomic` | durante il salvataggio non esiste mai `config.json` incompleto: il test controlla che nella directory finale compaia solo il file definitivo, mai `*.tmp` |
| `test_save_creates_parents` | crea la directory `%APPDATA%/KimaiClient` se manca |
| `test_is_configured` | `False` se manca il token, `True` solo con host+username+token |

Tutti i test devono scrivere in `tmp_path`, **mai** nella `%APPDATA%` reale.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.config'`

- [ ] **Step 3: Implementa `kemai_client/config.py`**

`save` scrive su `<path>.tmp` nella stessa directory e poi `os.replace` sul definitivo: `os.replace` è atomico su Windows e su POSIX, quindi la config non può restare a metà.

`load` avvolge `open` e `json.load` in `try/except (OSError, json.JSONDecodeError)` e, in caso di errore, costruisce e restituisce `Config()` con tutti i default. I campi sconosciuti presenti nel JSON vengono ignorati, così una config scritta da una versione futura non rompe questa.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/config.py tests/test_config.py
git commit -m "feat: configurazione persistente con scrittura atomica"
```

---

### Task 4: Stringhe italiane

**Files:**
- Create: `kemai_client/i18n.py`
- Test: `tests/test_i18n.py`

**Interfaces:**
- Consumes: nessuno.
- Produces: `STRINGS: dict[str, str]` e `t(key: str, **kwargs: object) -> str` che formatta con `str.format(**kwargs)` e solleva `KeyError` su chiave assente.

- [ ] **Step 1: Scrivi il test che fallisce**

`tests/test_i18n.py` asserisce che esistano **esattamente** queste chiavi, e non altre:

`app_title`, `menu_file`, `menu_edit`, `menu_new_project`, `menu_settings`, `menu_quit`, `label_customer`, `label_project`, `label_activity`, `label_started_at`, `btn_start`, `btn_stop`, `label_host`, `label_username`, `label_token`, `chk_close_to_tray`, `btn_test`, `btn_cancel`, `btn_save`, `status_connected`, `status_error`, `dlg_project_title`, `label_name`, `err_no_selection`, `err_project_no_activities`, `err_auth`, `err_network`, `err_response`, `err_active`, `err_name_empty`, `tray_show`, `tray_quit`

Aggiungi `test_t_formats_kwargs` con chiave `status_connected = "Connesso a Kimai {version}"` e `t("status_connected", version="1.15") == "Connesso a Kimai 1.15"`.

- [ ] **Step 2: Esegui il test e verifica che fallisca**

Run: `.venv\Scripts\python.exe -m pytest tests/test_i18n.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.i18n'`

- [ ] **Step 3: Implementa `kemai_client/i18n.py`**

Dizionario con le 31 chiavi elencate, valori in italiano. `btn_start = "Avvia"`, `btn_stop = "Ferma"`, `chk_close_to_tray = "Chiudi nel vassoio di sistema"`, `btn_test = "Prova"`, `menu_new_project = "Nuovo progetto"`.

- [ ] **Step 4: Esegui il test e verifica che passi**

Run: `.venv\Scripts\python.exe -m pytest tests/test_i18n.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/i18n.py tests/test_i18n.py
git commit -m "feat: dizionario stringhe italiane"
```

---

### Task 5: Script di probing degli endpoint

**Perché esiste:** l'istanza `https://crono.bonificaumbria.local` non risolve dalla macchina di sviluppo, quindi gli endpoint reali di Kimai 1.15 **non sono mai stati verificati**. Questo script gira sulla rete interna e produce il rapporto che conferma o smentisce le ipotesi in `endpoints.py`.

**Files:**
- Create: `tools/probe_api.py`
- Test: `tests/test_probe.py`

**Interfaces:**
- Consumes: `kemai_client.api.endpoints`, `TEST_TOKEN` finto.
- Produces:
  - `build_variants() -> list[RequestVariant]`, dove `RequestVariant` è un `NamedTuple(method: str, url: str, headers: dict[str, str])`. Elenca le varianti di autenticazione e formato da provare, in ordine di preferenza: prima header `X-AUTH-USER`/`X-AUTH-TOKEN`, poi HTTP Basic; per l'output, `Accept: application/json` e suffisso `.json` sull'URL.
  - `probe(host: str, username: str, token: str, variants: list[RequestVariant], opener=urlopen) -> list[ProbeResult]`, dove `ProbeResult` è un `NamedTuple(variant: RequestVariant, status: int, body_snippet: str, verdict: str)`.
  - `main() -> int` che stampa un rapporto leggibile e restituisce `0` se almeno una variante ha funzionato su `/api/versions`, `1` altrimenti.

- [ ] **Step 1: Scrivi il test che fallisce**

`tests/test_probe.py` verifica `build_variants()` senza rete:
- restituisce almeno 4 varianti
- la prima variante usa `X-AUTH-USER` e `X-AUTH-TOKEN`
- esiste una variante Basic con header `Authorization` che inizia per `Basic `
- esiste una variante con URL che termina in `.json`
- **`test_no_real_token_in_source`**: il sorgente di `tools/probe_api.py` non contiene il token reale e non accetta il token come argomento della riga di comando; arriva solo da `getpass`

`probe()` si testa iniettando un `opener` finto che restituisce risposte con status precisi; `test_probe_marks_auth_failure` con status 401 deve dare `verdict` contenente `"AUTENTICAZIONE FALLITA"`.

- [ ] **Step 2: Esegui il test e verifica che fallisca**

Run: `.venv\Scripts\python.exe -m pytest tests/test_probe.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementa `tools/probe_api.py`**

Il token si legge da `getpass.getpass("Token API: ")`, **mai** da un argomento della riga di comando, perché gli argomenti finiscono nella cronologia della shell. L'host si accetta come argomento, il nome utente pure.

`probe()` cattura `urllib.error.HTTPError` per estrarre lo status, `URLError` per l'irraggiungibilità, e in ogni caso cattura l'eccezione senza interrompersi: un probing che si ferma al primo errore non serve a niente. Il corpo della risposta viene troncato a 200 caratteri nel rapporto, e il token viene sostituito con `***` ovunque prima di stampare.

- [ ] **Step 4: Esegui il test e verifica che passi**

Run: `.venv\Scripts\python.exe -m pytest tests/test_probe.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add tools/probe_api.py tests/test_probe.py
git commit -m "feat: script di probing degli endpoint Kimai"
```

- [ ] **Step 6: [UMANO] Esegui il probing sulla rete interna**

Run, **da una macchina collegata alla rete interna**, con `luca` come utente e il token API personale:

```bash
.venv\Scripts\python.exe tools/probe_api.py https://crono.bonificaumbria.local luca
```

Il prompt chiede il token. **Incolla il nuovo token ruotato, non quello già finito in questa chat.**

Expected: un rapporto che dice quali varianti funzionano, e in particolare conferma o smentisce `X-AUTH-USER`/`X-AUTH-TOKEN` e il percorso `/api/versions`.

- [ ] **Step 7: [UMANO] Applica le correzioni al probing, se servono**

Se il rapporto smentisce le ipotesi, correggi **solo** `kemai_client/api/endpoints.py` — che contiene sia i path sia i nomi dei parametri di filtro e di paging — e, se cambia il metodo di autenticazione, **solo** il blocco header in `KimaiClient._request`. Non toccare `models.py`, `config.py` o i test già verdi: il confine esiste proprio per questo.

```bash
git add kemai_client/api/endpoints.py
git commit -m "fix: allinea gli endpoint ai risultati del probing"
```

---

### Task 6: Logging su file

Non è uno slancio di ambizione: la spec promette il log in quattro punti (RF-14, §10 e due
volte in §11) e fino a qui non esisteva. Senza questo task quelle promesse sono vacue, e
soprattutto la regola di sicurezza "il token non finisce mai nel log" non è verificabile
perché non c'è un log in cui il token possa finire.

**Files:**
- Create: `kemai_client/logging_setup.py`
- Test: `tests/test_logging.py`

**Interfaces:**
- Consumes: `kemai_client.api.errors` (Task 1), per i tipi di eccezione da loggare.
- Produces:
  - `default_log_path() -> Path` che restituisce `Path(os.environ["APPDATA"]) / "KimaiClient" / "kimai.log"`, con lo stesso criterio di `config.default_path()`: l'app non scrive mai nelle directory dell'installazione.
  - `setup_logging(path: Path | None = None) -> logging.Logger` che configura un `RotatingFileHandler` su `path`, con `maxBytes=512*1024` e `backupCount=3`, e restituisce il logger `kimai`. Va chiamata una sola volta da `app.main()`.
  - `log_exception(logger: logging.Logger, exc: Exception, context: str) -> str` che registra `exc` con `logger.exception(context)`, **senza** includere il token, e restituisce la stringa del messaggio da mostrare a schermo.

- [ ] **Step 1: Scrivi i test che falliscono**

| Test | Asserzione |
|---|---|
| `test_log_exception_returns_short_message` | il valore restituito è il messaggio breve italiano, non la stringa con lo stack trace |
| `test_log_exception_writes_detail_to_log` | il file di log contiene il testo dell'eccezione e il `context` |
| **`test_token_never_reaches_the_log`** | passando un `KimaiAuthError` costruito con il token nella chain, il contenuto del file di log **non** contiene il token. Questo è il test che rende vera la regola di sicurezza della spec |
| `test_logging_does_not_duplicate_handlers` | chiamare `setup_logging` due volte non raddoppia le righe nel file: senza `force=True` o un controllo esplicito, ogni avvio aggiungerebbe handler e il file crescerebbe a runtime |
| `test_log_file_rotates` | con `maxBytes` piccolo, superata la soglia il file viene ruotato e non cresce indefinitamente |
| `test_log_path_is_under_appdata` | `default_log_path()` termina con `KimaiClient/kimai.log` |

Ogni test passa `tmp_path` a `setup_logging`, così non scrive mai nella `%APPDATA%` reale.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_logging.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.logging_setup'`

- [ ] **Step 3: Implementa `kemai_client/logging_setup.py`**

`setup_logging` deve essere **idempotente**: prima di aggiungere l'handler, controlla se il
logger `kemai` ne ha già uno, e in quel caso non aggiunge niente. Senza questo, ogni
chiamata successiva raddoppia le righe di ogni messaggio.

La rotazione serve perché l'app resta aperta potenzialmente per un'intera giornata di
lavoro, e su un'app lanciata da collegamento non esiste console dove guardare.

- [ ] **Step 4: Implementa `log_exception` senza perdere il segreto**

Registra il contesto e l'eccezione con `logger.exception(context)`. Non aggiungere mai il
token al testo: il modulo non lo conosce, e deve restare così. Se l'eccezione contiene
nei suoi attributi un segreto, non serializzarla a mano: `logger.exception` registra
l'eccezione con la sua `str()`, che per `KimaiError` è già il messaggio italiano pulito.

Restituisci `str(exc)` per la UI: è l'unico punto del progetto in cui i due canali si
separano, ed è il posto giusto perché ogni gestore di errore in seguito ci passa.

- [ ] **Step 5: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_logging.py -v`
Expected: PASS

- [ ] **Step 6: Committa**

```bash
git add kemai_client/logging_setup.py tests/test_logging.py
git commit -m "feat: log su file con rotazione e separazione dei canali di errore"
```

---

### Task 7: AppController

Il cuore logico: stato, orchestrazione, notifica. Tutta la logica delle finestre vive qui ed è testabile senza Tkinter.

**Files:**
- Create: `kemai_client/controller.py`
- Test: `tests/test_controller.py`

**Interfaces:**
- Consumes: `KimaiClient` (Task 2), `Config`, `load`, `save`, `is_configured` (Task 4), `t` (Task 5), `log_exception` (Task 6), i modelli (Task 1).
- Produces:
  - `class AppController` con `__init__(self, client_factory: Callable[[str, str, str], KimaiClient] | None = None, config: Config | None = None, clock: Callable[[], float] = time.monotonic)`.
  - `subscribe(self, callback: Callable[[], None]) -> None` — registra un subscriber chiamato a ogni cambio di stato.
  - `notify(self) -> None` — chiama tutti i subscriber.
  - `connect(self, host: str, username: str, token: str) -> str` — crea il client via `client_factory` e restituisce la versione.
  - `load_customers(self) -> list[Customer]`
  - `select_customer(self, customer_id: int) -> list[Project]` — ricalcola progetti e **azzera** progetto e attività.
  - `select_project(self, project_id: int) -> list[Activity]`
  - `select_activity(self, activity_id: int) -> None`
  - `can_start(self) -> bool` — `True` solo con cliente, progetto e attività selezionati e nessuna attività in corso.
  - `start(self) -> None` — chiama `start_timesheet`, memorizza `started_at` e azzera il cronometro.
  - `stop(self) -> None` — chiama `stop_timesheet` e libera lo stato.
  - `is_running(self) -> bool`
  - `elapsed_seconds(self) -> int` — `int(clock() - self._started_monotonic)`, con `clock` iniettabile per test deterministici.
  - `started_at_label(self) -> str` — data/ora formattata in italiano, `""` se non in corso.
  - `create_project(self, name: str, customer_id: int) -> Project` — rilancia e poi ricarica i progetti del cliente.
  - `toggle(self) -> None` — `start()` o `stop()` secondo lo stato.
  - `last_error(self) -> str` — messaggio breve dell'ultimo errore, già pronto per la UI, vuoto se non ce n'è stato nessuno.
  - Attributi pubblici di sola lettura per l'UI: `customers`, `projects`, `activities`, `customer_id`, `project_id`, `activity_id`, `config`, `truncated`.
  - `truncated: bool` — `True` se l'ultimo elenco caricato era troncato, copiato da `client.last_list_truncated` dopo ogni `list_*`. È ciò che alimenta l'avviso non bloccante di RF-15.

- [ ] **Step 1: Scrivi i test che falliscono**

Test con un `FakeClient` che registra le chiamate e restituisce dati fissi, e un `clock` finto che avanza a piacere.

| Test | Asserzione |
|---|---|
| `test_select_customer_returns_projects` | `select_customer(1)` restituisce la lista progetti e imposta `customer_id` |
| `test_select_customer_clears_children` | dopo `select_project` e `select_activity`, un nuovo `select_customer` azzera `project_id` e `activity_id` a `None` |
| `test_select_project_returns_activities` | `select_project(9)` restituisce le attività |
| `test_can_start_requires_all_three` | `False` se manca uno dei tre, `True` con tutti |
| `test_start_records_and_notifies` | `start()` chiama `start_timesheet(9, 3)`, imposta `is_running()` e i subscriber sono stati chiamati |
| `test_start_twice_raises` | secondo `start()` solleva `RuntimeError` con il messaggio di `t("err_active")` |
| `test_stop_clears_state` | `stop()` chiama `stop_timesheet` e `is_running()` torna `False` |
| `test_elapsed_uses_injected_clock` | con clock fissa a 100 e poi a 106.5, `elapsed_seconds() == 6` |
| `test_toggle_dispatches` | `toggle()` su inattivo chiama `start`, su attivo chiama `stop` |
| **`test_network_loss_keeps_timer_running`** | **Review Focus 2:** se `stop_timesheet` solleva `KimaiNetworkError`, `elapsed_seconds()` continua ad avanzare e `is_running()` resta `True`; il controller registra l'errore per la sincronizzazione successiva |
| **`test_project_without_activities_disables_start`** | **Review Focus 3:** `select_project` su un progetto senza attività lascia `can_start()` `False` e produce il messaggio di `t("err_project_no_activities")` |
| **`test_auth_error_is_italian_and_tokenless`** | **Review Focus 4:** `KimaiAuthError` dal client fa fallire `start()` con messaggio `t("err_auth")`, senza contenere il token |
| `test_create_project_reloads` | `create_project("Nuovo", 1)` chiama il client e la lista progetti contiene quello nuovo |
| `test_truncated_flag_is_exposed` | dopo un `list_customers()` su un client con `last_list_truncated=True`, `controller.truncated` è `True` e i subscriber sono stati avvisati |
| `test_errors_go_through_log_exception` | un errore del client finisce in `controller.last_error()` **e** viene passato a `log_exception`, così il dettaglio tecnico va nel log mentre a schermo resta il messaggio breve |

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_controller.py -v`
Expected: FAIL con `ImportError: cannot import name 'AppController'`

- [ ] **Step 3: Implementa `AppController` in `kemai_client/controller.py`**

`client_factory` esiste perché i test non devono mai costruire un `KimaiClient` vero. Il default è `lambda host, username, token: KimaiClient(host, username, token)`.

I subscriber sono una `list[Callable[[], None]]` e `notify()` li chiama in un `try/except Exception` per ciascuno: un subscriber che solleva non deve impedire agli altri di aggiornarsi, né far cadere il controller.

`start()` chiama `notify()` **prima** dell'avanzamento del tempo, così l'UI si aggiorna una sola volta per transizione.

Ogni `except KimaiError` passa da `log_exception(self.logger, exc, context)` e assegna il valore restituito a `self.last_error`. Non stampare mai l'eccezione a schermo con una `messagebox` che contenga la sua `str()` grezza: è il canale che porta i dettagli tecnici, e la `str()` di un errore del client è già un messaggio italiano pulito, ma la regola vale per tutte le eccezioni, comprese quelle future.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_controller.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/controller.py tests/test_controller.py
git commit -m "feat: AppController con stato, cascata e cronometro"
```

---

### Task 8: Widget e utilità UI

**Files:**
- Create: `kemai_client/ui/__init__.py`
- Create: `kemai_client/ui/widgets.py`
- Test: `tests/test_widgets.py`

**Interfaces:**
- Consumes: `t` (Task 5).
- Produces:
  - `format_duration(seconds: int) -> str` → `"HH:MM:SS"`, con ore che non vanno a capo a 99 e senza segno per valori negativi (restituono `"00:00:00"`).
  - `class StopButton(tk.Canvas)` con `__init__(self, master, on_click: Callable[[], None], width: int = 72, height: int = 72)`, metodo `set_label(self, text: str) -> None` e `set_enabled(self, enabled: bool) -> None`.
  - `draw_octagon(self, cx: float, cy: float, r: float) -> None` che disegna il poligono a 8 vertici sul canvas.

- [ ] **Step 1: Scrivi i test che falliscono**

`tests/test_widgets.py` — i test di `format_duration` sono puri e non richiedono schermo:

| Test | Asserzione |
|---|---|
| `test_format_zero` | `format_duration(0) == "00:00:00"` |
| `test_format_six_seconds` | `format_duration(6) == "00:00:06"` |
| `test_format_one_hour` | `format_duration(3661) == "01:01:01"` |
| `test_format_over_99_hours` | `format_duration(360000) == "100:00:00"`, non `"1:0:0"` |
| `test_format_negative_is_clamped` | `format_duration(-5) == "00:00:00"` |
| `test_octagon_has_eight_points` | `draw_octagon` crea esattamente 8 vertici sul canvas di prova |

Questi test girano su `tk.Tk()` headless su Windows senza bisogno di schermo; se l'ambiente non può creare un `Tk`, il test dell'ottagono si marca `skip` con `pytest.importorskip`-style guard, **ma i test di `format_duration` devono comunque passare** e non si marcano mai `skip`.

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_widgets.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.ui'`

- [ ] **Step 3: Implementa `kemai_client/ui/widgets.py`**

`format_duration` calcola `h = seconds // 3600`, `m = (seconds % 3600) // 60`, `s = seconds % 60` e formatta con `f"{h:02d}:{m:02d}:{s:02d}"`; il clamp a zero avviene prima del calcolo.

`StopButton` estende `tk.Canvas` perché **ttk non disegna poligoni**: l'ottagono è un requisito di fedeltà visiva rispetto agli screenshot, non una decorazione. `draw_octagon` calcola 8 vertici a partire da `angle = 22.5°` con passo di `45°`, usando `math.cos` e `math.sin`, e chiama `self.create_polygon(points, fill=..., outline=...)`.

`set_enabled(False)` imposta `state="disabled"` e cambia il riempimento in grigio, così il feedback visivo è immediato come nello screenshot.

- [ ] **Step 4: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_widgets.py -v`
Expected: PASS

- [ ] **Step 5: Committa**

```bash
git add kemai_client/ui/ tests/test_widgets.py
git commit -m "feat: StopButton a ottagono e formatazione durata"
```

---

### Task 9: Finestra principale

**Files:**
- Create: `kemai_client/ui/main_window.py`
- Test: nessun test automatico; verifica manuale nel Task 12

**Interfaces:**
- Consumes: `AppController` (Task 7), `StopButton`, `format_duration` (Task 8), `t` (Task 5).
- Produces: `class MainWindow` con `__init__(self, root: tk.Tk, controller: AppController, on_open_settings: Callable[[], None], on_new_project: Callable[[], None])`, metodo `refresh(self) -> None` che rilegge lo stato dal controller e aggiorna tutti i widget, e `start_ticking(self) -> None` che avvia `root.after(1000, ...)`.

- [ ] **Step 1: Scrivi la finestra**

Costruisci con `ttk.Frame` e `grid`, non con `pack`: i selettori hanno larghezze diverse e `grid` con `sticky="ew"` e `uniform` è l'unico modo per allinearli come nello screenshot.

Elementi nell'ordine dello screenshot `img-ref/kemai-running.png`:
- menu `File` / `Modifica`; sotto `File`: `Nuovo progetto`, `Impostazioni`, `Esci`
- tre righe `Etichetta + ttk.Combobox` in sola lettura per Cliente, Progetto, Attività
- `StopButton` centrato
- riga `Avviato il` con `ttk.Entry` in sola lettura
- etichetta cronometro in font monospaziato grande

`root.geometry("282x312")`, `root.resizable(False, False)`, titolo `t("app_title")`.

- [ ] **Step 2: Collega il controller senza chiamare l'API**

`refresh()` deve **solo leggere** `controller.customers`, `controller.projects`, `controller.activities` e chiamare `controller.select_*`. Nessuna istanza di `KimaiClient` è visibile da questo file: è la regola architetturale centrale della spec, e va rispettata anche se sembra ridondante.

Registra il controller con `controller.subscribe(self.refresh)` in `__init__`.

- [ ] **Step 3: Implementa il cronometro senza thread**

`start_ticking` chiama `root.after(1000, self._tick)`; `_tick` aggiorna l'etichetta con `format_duration(controller.elapsed_seconds())` e **si ripianifica da sola** finché l'attività è in corso. Nessun `threading.Thread`: Tkinter sta nel main thread e `after` è sufficiente.

- [ ] **Step 4: [UMANO] Avvia l'app e verifica a mano**

Run: `.venv\Scripts\python.exe -m kemai_client`
Expected: la finestra si apre a 282×312 con l'ottagono visibile, i selettori disabilitati, il cronometro a `00:00:00`.

- [ ] **Step 5: Committa**

```bash
git add kemai_client/ui/main_window.py
git commit -m "feat: finestra principale con selettori a cascata e cronometro"
```

---

### Task 10: Finestra impostazioni e dialog progetto

**Files:**
- Create: `kemai_client/ui/settings_window.py`
- Create: `kemai_client/ui/project_dialog.py`
- Test: nessun test automatico; verifica manuale nel Task 12

**Interfaces:**
- Consumes: `AppController` (Task 7), `Config` (Task 4), `t` (Task 5).
- Produces:
  - `class SettingsWindow(tk.Toplevel)` con `__init__(self, parent, controller: AppController, on_saved: Callable[[], None] | None = None)`.
  - `class ProjectDialog(tk.Toplevel)` con `__init__(self, parent, controller: AppController, preselected_customer: int | None = None)` e attributo `result: Project | None`, che resta `None` se l'utente annulla.

- [ ] **Step 1: Scrivi la finestra impostazioni**

Tre `ttk.Entry` per Host, Nome utente, Token; il campo Token con `show="*"`; un `ttk.Checkbutton` per `t("chk_close_to_tray")`; un'etichetta di stato che diventa verde con `t("status_connected", version=...)` o rossa con il messaggio d'errore; tre pulsanti `Prova`, `Annulla`, `Salva` in riga.

`Prova` chiama `controller.connect(host, username, token)` **senza** salvare, e aggiorna l'etichetta di stato. `Annulla` fa `destroy()` senza scrivere. `Salva` scrive in `controller.config`, chiama `config.save` e poi `on_saved` se presente.

- [ ] **Step 2: Gestisci il risultato di `Prova` senza perdere i dati**

`Prova` non deve mai chiudere la finestra né svuotare i campi, anche in caso di errore: l'utente ha appena digitato le credenziali e deve poter correggerle. Cattura `KimaiAuthError` e `KimaiError`, e in entrambi i casi aggiorna solo l'etichetta di stato.

- [ ] **Step 3: Scrivi il dialog progetto**

`ttk.Entry` per `t("label_name")`, `ttk.Combobox` in sola lettura per `t("label_customer")` popolata da `controller.customers`, e i pulsanti `Salva` e `Annulla`. Se `preselected_customer` è valoriato, il combobox parte da quel cliente.

`Salva` chiama `controller.create_project(name, customer_id)`, mette il risultato in `self.result` e chiude. `Annulla` lascia `self.result = None` e chiude. Un nome vuoto non chiude e mostra `t("err_name_empty")`.

- [ ] **Step 4: [UMANO] Verifica a mano**

Run: `.venv\Scripts\python.exe -m kemai_client`, poi `File → Impostazioni`.
Expected: si apre una finestra con i tre campi, `Prova` con credenziali finte mostra errore in rosso **senza chiudere la finestra**, `Annulla` non salva nulla.

- [ ] **Step 5: Committa**

```bash
git add kemai_client/ui/settings_window.py kemai_client/ui/project_dialog.py
git commit -m "feat: finestra impostazioni e dialog di creazione progetto"
```

---

### Task 11: System tray e composizione

Il task con la logica di threading più delicata e l'unico con una condizione di uscita che può lasciare processi zombie.

**Files:**
- Create: `kemai_client/tray.py`
- Create: `kemai_client/app.py`
- Create: `kemai_client/__main__.py`
- Test: `tests/test_tray.py`

**Interfaces:**
- Consumes: `AppController` (Task 7), `Config` (Task 4), `t` (Task 5), `StopButton` per l'icona (Task 8), `setup_logging` (Task 6).
- Produces:
  - `close_behaviour(close_to_tray: bool) -> str` in `kemai_client/tray.py` che restituisce `"withdraw"` oppure `"destroy"`. È una funzione **pura**, deliberatamente, perché la sua correttezza è ciò che distingue un'uscita pulita da un processo zombie.
  - `build_menu(controller: AppController, root: tk.Tk) -> pystray.Menu` con voci Mostra, Avvia/Ferma, Esci.
  - `build_icon() -> PIL.Image.Image` che genera l'icona a runtime, senza file binari nel repository.
  - `class TrayIcon` con `start(self) -> None` (chiama `setup()` poi avvia `run_detached()` su un `threading.Thread(daemon=True)`) e `stop(self) -> None`.
  - `main() -> None` in `kemai_client/app.py`, chiamata da `kemai_client/__main__.py`.

- [ ] **Step 1: Scrivi i test che falliscono**

`tests/test_tray.py` — **senza avviare pystray**, perché il modulo va importato ma `TrayIcon.start()` non viene mai chiamato:

| Test | Asserzione |
|---|---|
| **`test_close_behaviour_withdraw`** | **Review Focus 5:** `close_behaviour(True) == "withdraw"` |
| **`test_close_behaviour_destroy`** | `close_behaviour(False) == "destroy"` |
| `test_menu_callbacks_are_deferred` | ogni callback del menu pystray passa da `root.after`, mai chiama direttamente il controller: il test registra un `root` finto e verifica che il controller non venga toccato al momento della costruzione del menu, ma solo dopo l'invocazione del callback differito |
| `test_icon_is_generated` | `build_icon()` restituisce un'immagine 64×64 senza toccare il filesystem |

- [ ] **Step 2: Esegui i test e verifica che falliscano**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tray.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'kemai_client.tray'`

- [ ] **Step 3: Implementa `kemai_client/tray.py`**

`TrayIcon.start()` **non** deve mai chiamare `icon.run()`, che è bloccante: chiama `icon.setup()` e poi `icon.run_detached()` dentro `threading.Thread(target=..., daemon=True)`. Il `daemon=True` è essenziale — è la garanzia che un bug nel tray non tenga vivo il processo.

Ogni callback del menu fa `root.after(0, fn)`. I callback arrivano sul thread pystray e toccano il controller, **mai** un widget; solo le azioni che devono aggiornare la GUI passano per `root.after`.

`build_icon()` disegna l'icona con `PIL.ImageDraw` a runtime. Nessun file `.ico` o `.png` viene committato: gli asset binari nel repository sono un costo di merge e qui non servono.

- [ ] **Step 4: Implementa `close_behaviour` e la finestra di chiusura**

In `app.py`, il protocollo `WM_DELETE_WINDOW` chiama `close_behaviour(config.close_to_tray)`: se il risultato è `"withdraw"` chiama `root.withdraw()`, se è `"destroy"` chiama `root.quit()` **e poi** `tray.stop()`.

`root.quit()` da solo **non** termina il processo se il thread del tray è vivo: senza `tray.stop()` e senza `daemon=True` l'app resta in background invisibile. Questa è la ragione per cui `close_behaviour` è testata e non lasciata a una `if` inline.

- [ ] **Step 5: Implementa `app.py` e `__main__.py`**

`main()` carica la config, costruisce il controller, la `MainWindow` e il `TrayIcon`, collega `WM_DELETE_WINDOW`, e chiama `root.mainloop()`. Se `is_configured(config)` è `False`, apre `SettingsWindow` dopo 200 ms senza bloccare, così l'utente inserisce le credenziali al primo avvio.

- [ ] **Step 6: Esegui i test e verifica che passino**

Run: `.venv\Scripts\python.exe -m pytest tests/test_tray.py -v`
Expected: PASS

- [ ] **Step 7: [UMANO] Verifica a mano l'uscita pulita**

Run: `.venv\Scripts\python.exe -m kemai_client`
Poi: avvia un'attività, chiudi la finestra con la X, apri il menu del vassoio, scegli **Esci**, e controlla in Task Manager che il processo `python` sia sparito.
Expected: il processo termina. Se resta, `daemon=True` o `tray.stop()` non sono stati applicati.

- [ ] **Step 8: Committa**

```bash
git add kemai_client/tray.py kemai_client/app.py kemai_client/__main__.py tests/test_tray.py
git commit -m "feat: system tray con pystray e composizione dell'app"
```

---

### Task 12: Dipendenze, documentazione e verifica finale

**Files:**
- Modify: `requirements.txt`
- Create: `README.md`
- Create: `.gitignore`
- Test: suite completa

**Interfaces:**
- Consumes: tutto il resto.
- Produces: repository pronto alla consegna.

- [ ] **Step 1: Scrivi `requirements.txt`**

Sostituisci il file placeholder attuale con le sole dipendenze reali:

```
requests>=2.31
pystray>=0.19
Pillow>=10.0
pytest>=8.0
```

- [ ] **Step 2: Scrivi `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
config.json
*.local.json
.env
```

Le ultime quattro righe sono la rete di sicurezza della spec §11: la config reale sta in `%APPDATA%` e non dovrebbe mai arrivare qui, ma se qualcuno la copia nella cartella del progetto non deve finire in un commit.

- [ ] **Step 3: Scrivi `README.md`**

In italiano: requisiti, `pip install -r requirements.txt`, `.venv\Scripts\python.exe -m kemai_client`, come generare il token API nel profilo Kimai, il comando del probing del Task 6, e la nota che il server è in rete interna.

**Il README non contiene alcun token reale.** Solo la procedura per ottenerne uno.

- [ ] **Step 4: Esegui la suite completa**

Run: `.venv\Scripts\python.exe -m pytest -v`
Expected: PASS su tutti i test, nessuno saltato tranne l'eventuale test dell'ottagono su ambiente senza schermo.

- [ ] **Step 5: [UMANO] Confronta ogni finestra con il suo screenshot**

Con l'app in esecuzione, confronta a occhio contro `img-ref/`:

| Finestra | Riferimento | Criteri di accettazione |
|---|---|---|
| Principale, ferma | `kemai-running.png` | 282×312, tre selettori allineati, ottagono centrato, cronometro in basso |
| Principale, in corso | `kemai-running.png` | etichetta passa ad `Avviato il` con data/ora, ottagono passa a `Ferma` |
| Impostazioni | `kemai-settings.png` | tre campi in colonna, checkbox, tre pulsanti in riga a destra |
| Dialog progetto | `kemai-add-project.png` | nome e cliente in colonna, due pulsanti in riga |

Ogni differenza di layout che emerge qui è un bug del task che ha costruito quella finestra: torna al task e correggi, invece di annotare.

- [ ] **Step 6: Committa**

```bash
git add requirements.txt README.md .gitignore
git commit -m "docs: dipendenze, README e regole di ignoranza"
```

---

## Ordine di esecuzione e note

I task 1→2→4→5→6→7 formano la catena critica e vanno eseguiti in ordine: ogni task usa le firme esatte prodotte dal precedente, così che un errore di nome si veda subito e non alla fine. Il Task 3 non ha dipendenze e si può infilare in qualsiasi momento.

Il Task 6 è l'unico che richiede un'azione fuori dal repository: gira sulla rete interna e restituisce informazioni. Può essere eseguito in parallelo con i task 1-5, e conviene farlo presto, perché il suo Step 7 può modificare `endpoints.py` e preferibilmente non deve accadere a metà del Task 7.

I Task 8-11 dipendono dal Task 7 e non possono essere parallelizzati fra loro, perché condividono la firma di `AppController`.

I Task 9 e 10 non hanno test automatici: sono finestre, e un test che verifica "la finestra si apre" vale meno di un confronto con lo screenshot. Il Task 12 Step 5 è il loro vero banco di prova, ed è il motivo per cui gli screenshot in `img-ref/` sono parte del materiale di lavoro e non solo documentazione.

Il Task 6 (logging) sta prima del 7 per una ragione precisa, non per ordine estetico: `AppController` instrada ogni errore attraverso `log_exception`, quindi il modulo deve esistere prima. Se il logging fosse stato messo in fondo, i task 7-11 avrebbero referenziato una funzione inesistente.
