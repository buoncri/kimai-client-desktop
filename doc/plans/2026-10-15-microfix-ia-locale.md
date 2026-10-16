Sei in C:\Users\luca\test\local-llm. Questa e' una run notturna NON
supervisionata: lavori da solo fino in fondo, senza che nessuno ti
risponda. Per questo le regole di arresto contano piu' della tua fretta.

Sei un agente di coding. Il piano di lavoro e' gia' scritto, verificato
e messo in ordine: il tuo compito e' eseguirlo alla lettera, non
ridiscuterlo e non migliorarlo. Ogni fix e' stato verificato a mano
sui file indicati: righe e stringhe sotto sono esatte.

=======================================================================
DOVE LAVORI
=======================================================================

Crea un branch dedicato PRIMA di toccare qualsiasi cosa:

    git checkout -b chore/microfix-ia-locale

Verifica di partenza, e se una di queste due fallisce FERMATI:

    git log -1 --oneline   deve essere ffece5b
    .venv\Scripts\python.exe -m pytest -q   deve dare 221 passed

Non usare MAI il comando `python`: su questa macchina e' uno stub di 0
byte del Microsoft Store che non esegue nulla. L'unico interprete e'
.venv\Scripts\python.exe. Tutti i comandi `pytest` sotto significano
`.venv\Scripts\python.exe -m pytest`.

Quando avrai finito, il branch si mergia solo dopo revisione umana.
Non aprire PR, non mergiare, non pushare.

=======================================================================
COSA STAI FACENDO (riassunto)
=======================================================================

Sette micro-task di igiene e micro-bug, tutti verificati, nessuno
cambia comportamento visibile dell'app. Ordine obbligatorio: Task 1,
poi 2, 3, 4, 5, 6, 7. Un commit per task, con il messaggio indicato.
Alla fine la suite deve dare 230 passed (221 + 9 nuovi, conteggi per
task sotto).

=======================================================================
VINCOLI ASSOLUTI
=======================================================================

1. MAI cancellare, rinominare, saltare (`skip`) o indebolire un test
   esistente. Il numero di test puo' solo SALIRE, e solo della quantita'
   che il task dichiara. Se un test esistente ti sta contro, il codice
   e' sbagliato, non il test.
2. MAI modificare la firma di una funzione esistente (i test la usano
   cosi' com'e'). Solo il Task 6 aggiunge una funzione NUOVA.
3. MAI cambiare comportamento visibile: stessi testi a schermo (le
   stringhe si spostano in i18n, non si riscrivono), stessi ordini di
   chiamata, stessi valori restituiti.
4. Se un passo fallisce o una riga non corrisponde a quanto scritto
   qui, FERMATI su quel task e passa al successivo senza toccarlo.
   Non improvvisare alternative.
5. Dopo OGNI task: suite intera verde prima del commit. Se e' rossa,
   ripara subito: non andare avanti con la suite rossa.

=======================================================================
TASK 1 — config.py: tre micro-correzioni (+1 test -> 222)
=======================================================================

File: kemai_client/config.py, kemai_client/config.py:16,
kemai_client/config.py:50, kemai_client/config.py:73.

1a. Riga 16: `from dataclasses import dataclass, field, asdict`.
Prima verifica con grep che `field(` non sia usato in nessun altro
punto del file. Se grep trova un uso reale, SALTA 1a e vai a 1b.
Altrimenti riduci a `from dataclasses import dataclass, asdict`.

1b. Riga 73: `with open(path) as f:` diventa
`with open(path, encoding="utf-8") as f:` (save() a riga 108 scrive
gia' UTF-8: la lettura deve essere simmetrica).

1c. Riga 50: `return Path(os.environ["APPDATA"]) / "KimaiClient" / "config.json"`
diventa
`return Path(os.environ.get("APPDATA") or Path.home()) / "KimaiClient" / "config.json"`
(`Path` e' gia' importato nel file; `os` pure). Motivo: su Linux/macOS
APPDATA non esiste e l'app crasha con KeyError all'avvio.

Test (1 nuovo, in tests/test_config.py):

    def test_default_path_without_appdata(monkeypatch):
        monkeypatch.delenv("APPDATA", raising=False)
        from kemai_client.config import default_path
        p = default_path()
        assert p.name == "config.json"
        assert p.parent.name == "KimaiClient"

Verifica: `.venv\Scripts\python.exe -m pytest -q` deve dare 222 passed.
Commit: `git add kemai_client/config.py tests/test_config.py`
`git commit -m "chore: config robusta (encoding, APPDATA, import inutilizzato)"`

=======================================================================
TASK 2 — i18n: due stringhe hardcoded entrano nel dizionario (+1 test -> 223)
=======================================================================

File: kemai_client/i18n.py, kemai_client/i18n.py:5,
kemai_client/controller.py:312, kemai_client/ui/main_window.py:225,
tests/test_i18n.py (le tuple a riga 15-48 e 55-88).

Aggiungi ESATTAMENTE queste due chiavi (testi invariati, si spostano e
basta):

    "warn_truncated": "Elenco limitato: seleziona un altro elemento per vederne altri",
    "err_network": "Rete non disponibile",

`warn_truncated` va nella sezione "Finestra principale",
`err_network` nella sezione "Errori".

Poi usa le chiavi:

- kemai_client/controller.py:312:
  `self._last_error_msg = "Rete non disponibile"` diventa
  `self._last_error_msg = t("err_network")`
  (`t` e' gia' importato nel file, riga 20).
- kemai_client/ui/main_window.py:225:
  `text="Elenco limitato: seleziona un altro elemento per vederne altri"`
  diventa `text=t("warn_truncated")`
  (`t` e' gia' importato nel file).

Poi correggi il refuso a kemai_client/i18n.py:5: `puede` diventa `puo'`.

ATTENZIONE — test_i18n.py ha `test_no_extra_keys`: fallisce se
aggiungi chiavi senza aggiornarlo. Aggiungi `"warn_truncated"` e
`"err_network"` a ENTRAMBE le tuple (quella di
`test_all_required_keys_exist` e il frozenset di `test_no_extra_keys`),
in coda dopo `"tray_quit"`.

Test (1 nuovo, in tests/test_i18n.py, classe TestValuesAreStrings o
nuova classe):

    def test_new_keys_have_expected_values(self):
        from kemai_client import i18n
        assert i18n.t("err_network") == "Rete non disponibile"
        assert i18n.t("warn_truncated").startswith("Elenco limitato")

Verifica: suite deve dare 223 passed.
Commit: `git commit -m "chore: stringhe in i18n (err_network, warn_truncated)"`
(con `git add` dei 4 file toccati).

=======================================================================
TASK 3 — probe_api: probe() deve inviare davvero le credenziali (+2 test -> 225)
=======================================================================

File: tools/probe_api.py (righe 124-126), tests/test_probe.py.
NON toccare build_variants(): 7 test esistenti la chiamano senza
argomenti e le sue firme non si cambiano (vincolo 2).

Difetto verificato: `probe(host, username, token, ...)` riceve le
credenziali ma a riga 126 costruisce la Request con
`headers=variant.headers` cosi' com'e', e gli header sono vuoti
(`"X-AUTH-USER": ""`, `"X-AUTH-TOKEN": ""`, `"Authorization": "Basic "`).
Il probing va sempre in 401 e `token` serve solo a `_redact`.

Fix, dentro il ciclo `for variant in variants:` di probe(), prima di
costruire la Request: copia gli header e riempili.

    headers = dict(variant.headers)
    if "X-AUTH-USER" in headers:
        headers["X-AUTH-USER"] = username
        headers["X-AUTH-TOKEN"] = token
    elif headers.get("Authorization", "").startswith("Basic "):
        import base64
        headers["Authorization"] = "Basic " + base64.b64encode(
            f"{username}:{token}".encode()
        ).decode()

e usa `headers=headers` nella Request di riga 126. (`import base64`
puo' stare in testa al file invece che inline: scegli la testa del
file, e' piu' pulito; il comportamento e' identico.)

Test (2 nuovi, in tests/test_probe.py, con opener finto che cattura
la Request ricevuta — mai rete vera):

    def test_probe_sends_x_auth_credentials(self):
        (opener finto che registra request.headers e restituisce
        status 200; chiama probe("https://x", "luca", "tok",
        build_variants(), opener=finto))
        assert gli header inviati alla variante X-AUTH contengono
        "luca" e "tok"

    def test_probe_sends_basic_credentials(self):
        (stesso finto opener)
        assert almeno una Request abbia header Authorization diverso
        da "Basic " vuoto e decodificabile in "luca:tok"

Verifica: suite deve dare 225 passed.
Commit: `git commit -m "fix: probe_api invia le credenziali negli header"`

=======================================================================
TASK 4 — select_customer/select_project: errori loggati, non inghiottiti (+2 test -> 227)
=======================================================================

File: kemai_client/controller.py (righe 228-236 e 249-259),
tests/test_controller.py.

Difetto verificato: entrambi i metodi fanno `except KimaiError: pass`
— un errore del server sparisce senza lasciare traccia. NON cambiare
il comportamento verso la UI (liste azzerate, `last_error` invariato):
aggiungi solo il log.

- Riga 231: `except KimaiError:` diventa `except KimaiError as exc:`
  e prima riga del blocco: `log_exception(self._logger, exc, "select_customer")`
- Riga 252: stessa cosa con `"select_project"`.
(`log_exception` e' gia' importato a riga 21; `self._logger` esiste.)

Test (2 nuovi, in tests/test_controller.py, con caplog sul logger
"kimai"): client finto la cui `list_projects` solleva
`KimaiError("boom")`, poi `select_customer(1)`; assert che almeno un
record contenga "select_customer". Stessa cosa per `select_project`
con `list_activities` che solleva. Per costruire il controller usa
`AppController(client_factory=lambda h, u, t: FintoCheFallisce(), config=Config())`
(guarda in testa a test_controller.py come sono fatti gli altri stub).

Verifica: suite deve dare 227 passed.
Commit: `git commit -m "chore: log degli errori in select_customer/select_project"`

=======================================================================
TASK 5 — geometria ottagono in un helper puro (+2 test -> 229)
=======================================================================

File NUOVO: kemai_client/geometry.py. File da modificare:
kemai_client/ui/widgets.py (righe 51-59),
kemai_client/tray.py (righe 82-93). Test NUOVO: tests/test_geometry.py.

Difetto verificato: la matematica dei vertici (`22.5 + i * 45`,
cos/sin) e' copiata in due posti. Estrai:

    def octagon_points(cx: float, cy: float, r: float) -> list[float]:
        """Restituisce gli 8 vertici (16 float x, y) dell'ottagono."""
        (stesso ciclo dei due posti esistenti)

Il modulo NON deve importare tkinter (resta importabile senza display).

Poi sostituisci il ciclo in `draw_octagon()` e in `build_icon()` con
una chiamata all'helper. Output identico: nessun test esistente deve
cambiare.

Test (2 nuovi, in tests/test_geometry.py):

    def test_octagon_has_eight_vertices(self):
        pts = octagon_points(36.0, 36.0, 10.0)
        assert len(pts) == 16

    def test_octagon_first_vertex_angle(self):
        (verifica con math.isclose che pts[0], pts[1] valgano
        cx + r*cos(22.5 gradi in radianti), cy - r*sin(...))

Verifica: suite deve dare 229 passed.
Commit: `git commit -m "chore: helper octagon_points condiviso"`

=======================================================================
TASK 6 — main_window: helper per il ripristino selezione combo (+1 test -> 230)
=======================================================================

File: kemai_client/ui/main_window.py (righe 203-220),
tests/test_main_window.py.

Difetto verificato: tre cicli di ricerca lineare copiati per cliente,
progetto, attivita'. Aggiungi funzione a livello di modulo (NON
metodo, cosi' si testa senza Tk):

    def _select_by_id(combo, items, wanted_id) -> None:
        """Seleziona in combo l'indice dell'item con id == wanted_id."""
        for i, item in enumerate(items):
            if item.id == wanted_id:
                combo.current(i)
                break

e sostituisci i tre cicli con tre chiamate. Comportamento identico.

Test (1 nuovo, in tests/test_main_window.py, con Mock: nessun Tk):

    def test_select_by_id_selects_matching_index(self):
        from kemai_client.ui.main_window import _select_by_id
        combo = Mock()  # ha .current()
        items = [Mock(id=1), Mock(id=2)]
        _select_by_id(combo, items, 2)
        combo.current.assert_called_once_with(1)

Verifica: suite deve dare 230 passed.
Commit: `git commit -m "chore: helper _select_by_id per le combo"`

=======================================================================
TASK 7 — micro-igiene senza cambi di comportamento (+0 test -> resta 230)
=======================================================================

Tre modifiche testuali, nessuna cambia comportamento. La suite deve
restare a 230 passed (nessun test nuovo in questo task).

7a. kemai_client/controller.py righe 77-79: `import logging` sepolto
dentro `__init__`. Spostalo in testa al file con gli altri import e
cancella le tre righe dentro `__init__` (compreso il commento
"# Logger." se resta orfano — no: il commento resta, sposta solo
l'import; rileggi il punto prima di toccarlo).

7b. kemai_client/controller.py riga 208: `except KimaiError as exc:`
(`exc` mai usato in `_load_customers`) diventa `except KimaiError:`.

7c. tools/probe_api.py riga 179:
`if r.status in (200,) and "OK" == r.verdict:` diventa
`if r.status == 200 and r.verdict == "OK":`.

Verifica: suite deve dare 230 passed.
Commit: `git commit -m "chore: micro-igiene (import, except, yoda)"`

=======================================================================
VERIFICA FINALE
=======================================================================

    .venv\Scripts\python.exe -m pytest -q   deve dare 230 passed
    git log --oneline -n 8                  deve mostrare 7 commit chore/fix sopra ffece5b
    git status --short                      deve essere vuoto (tutto committato)

Fatto questo, FERMATI. Riepilogo breve: per ogni task una riga
"Task N: ok (N test)". Non mergiare, non pushare.

=======================================================================
ESCLUSO DA QUESTO PIANO (decisione umana, non tua)
=======================================================================

Non toccare, nemmeno "di passaggio":

- `kemai_client/api/client.py` e `kemai_client/api/endpoints.py`:
  gli endpoint sono verificati dal vivo; `PARAM_PAGE` inutilizzato e'
  noto ma la strategia di paging va decisa con il server vero.
- `_tick()` di main_window.py (ri-pianificazione senza cancel):
  serve una decisione di design sul ciclo vita della finestra.
- `create_project()` / `project_dialog.py` / `_on_save()` delle
  impostazioni senza try: la UX degli errori va disegnata, non
  improvvisata di notte.
- `toggle()`/`stop()` sul percorso non-exit: la mitigazione
  nell'exit path esiste gia' (commit ffece5b); cambiare la semantica
  di toggle e' decisione di prodotto.
- Fusione `load_customers()`/`_load_customers()`: toccherebbe 21 call
  site nei test, troppo per questa run.
