# Specifica di progetto — Kimai Desktop Client (Tkinter)

**Data:** 2026-09-30
**Stato:** revisione 2 — lacune di paging e logging integrate il 2026-09-30
**Riferimenti visivi:** `img-ref/kemai-running.png`, `img-ref/kemai-settings.png`, `img-ref/kemai-add-project.png`

---

## 1. Obiettivo

Realizzare un client desktop in Python con GUI Tkinter che riproduce le tre finestre del
client ufficiale KEMAI (Kimai desktop client di Alexandre Petitjean) e le collega a
un'istanza Kimai reale, permettendo di avviare e fermare attività di time tracking.

Successo significa: un utente installa le dipendenze, lancia `python -m kemai_client`,
inserisce host e token, vede lelenco clienti/progetti/attività, avvia il timer, ferma
l'attività e la vede registrata su Kimai.

## 2. Scopo

### In scope
- Finestra principale con selettori a cascata Cliente → Progetto → Attività
- Pulsante unico che alterna Avvia / Ferma
- Cronometro `HH:MM:SS` e campo "Avviato il" in sola lettura
- Finestra impostazioni: host, nome utente, token, "chiudi nel vassoio", verifica connessione
- Dialog di creazione progetto (Nome + Cliente)
- Icona nella system tray con pystray (menu: Mostra, Avvia/Ferma, Esci)
- Persistenza della configurazione su disco
- Interfaccia interamente in italiano
- Client HTTP per l'API Kimai 1.15

### Fuori scope (YAGNI esplicito)
- Modifica di record esistenti o eliminazione
- Report, statistiche, dashboard
- Più profili utente o multi-istanza
- Aggiornamento automatico dell'applicazione
- Internazionalizzazione oltre l'italiano
- Installer Windows o pacchettamento PyInstaller
- Sincronizzazione dello stato fra più istanze dell'app

## 3. Vincoli ambientali

| Vincolo | Valore |
|---|---|
| Server Kimai | `https://crono.bonificaumbra.local` — **rete interna** (per mesi il nome fu trascritto con il refuso "bonificaumbria" al posto di "bonificaumbra": era quello il motivo dei fallimenti DNS, non l'irraggiungibilita') |
| Versione Kimai | 1.15 (linea legacy, diversa dalla 2.x) |
| Utente API | `luca` (id 1) |
| Sistema operativo sviluppo | Windows |
| Python | 3.10+ |
| Consegna | script Python + `requirements.txt`, nessun installer |

**Conseguenze dirette:**

1. Lo sviluppo e i test automatici **non possono** dipendere dall'istanza reale.
2. Il probing degli endpoint deve essere eseguito dall'utente su una macchina nella
   rete interna, tramite lo script `tools/probe_api.py` (Task 5 del piano).
3. Tutti i path degli endpoint sono centralizzati in `kemai_client/api/endpoints.py`,
   in modo che le correzioni successive al probing tocchino un solo file.
4. Il client deve degradare con grazia: ogni risposta HTTP non attesa diventa un
   messaggio comprensibile, mai un'eccezione non gestita.

## 4. Requisiti funzionali

| ID | Requisito |
|---|---|
| RF-01 | Selezionare un Cliente carica i Progetti ad esso associati |
| RF-02 | Selezionare un Progetto carica le Attività e azzera l'Attività precedentemente scelta |
| RF-03 | Il pulsante è disabilitato finché Cliente, Progetto e Attività non sono tutti scelti |
| RF-04 | "Avvia" registra l'inizio attività su Kimai e avvia il cronometro |
| RF-05 | "Ferma" registra la fine attività su Kimai e azzera il cronometro |
| RF-06 | Il cronometro sopravvive alla minimizzazione e alla chiusura nel vassoio |
| RF-07 | Il campo "Avviato il" mostra il data/ora di inizio in sola lettura |
| RF-08 | La finestra impostazioni verifica le credenziali senza salvarle |
| RF-09 | La configurazione connessa viene ripresa all'avvio successivo |
| RF-10 | Il menu File permette di aprire il dialog di creazione progetto |
| RF-11 | Il progetto creato compare nell'elenco senza riavvio |
| RF-12 | La chiusura della finestra nasconde l'app nel vassoio quando l'opzione è attiva |
| RF-13 | Il menu del vassoio permette di riprendere la finestra e di uscire davvero |
| RF-14 | Gli errori di rete o di autenticazione sono mostrati in italiano e registrati nel log |
| RF-15 | Se un elenco risulta troncato dal server, la finestra principale lo dichiara con un avviso non bloccante |

## 5. Architettura

### 5.1 Regola strutturale

**Le finestre non chiamano mai l'API.** Tutto passa da `AppController`, unico detentore
dello stato. Questo confine è il motivo per cui la logica è testabile senza Tkinter.

```
   ┌──────────────┐   root.after()   ┌────────────────┐   chiamate   ┌─────────────┐
   │  pystray     │ ───────────────► │ AppController  │ ───────────► │ KimaiClient │
   │ (thread      │ ◄─────────────── │  (stato unico) │ ◄─────────── │ (requests)  │
   │  daemon)     │  azioni utente  └───────┬────────┘   DTO/dict   └──────┬──────┘
   └──────────────┘                        │                                 │
                                   notifica│                                 ▼
   ┌──────────────┐  eventi / comandi  ┌───▼──────────┐              https://crono
   │ Finestre Tk  │ ◄────────────────► │  callback     │              .bonificaumbra
   │  (main       │                    │  di notifica  │               .local/api
   │   thread)    │                    └───────────────┘
   └──────────────┘
```

Dipendenze ammesse: `ui → controller → api → (requests, endpoints)`.
Il modulo `tray` dipende da `controller`, mai da `ui`, per non invertire il flusso.

### 5.2 Moduli

| File | Responsabilità unica |
|---|---|
| `kemai_client/models.py` | Dataclass `Customer`, `Project`, `Activity` |
| `kemai_client/api/endpoints.py` | **Unico** posto dove vivono i path degli endpoint |
| `kemai_client/api/client.py` | `KimaiClient`: sessione, auth, richieste, parsing, errori |
| `kemai_client/api/errors.py` | `KimaiError`, `KimaiAuthError`, `KimaiNetworkError`, `KimaiNotFoundError` |
| `kemai_client/config.py` | Dataclass `Config` + `load()` / `save()` |
| `kemai_client/i18n.py` | Tutte le stringhe italiane in un solo dizionario |
| `kemai_client/logging_setup.py` | Configurazione del log su file e `log_exception()` |
| `kemai_client/controller.py` | Stato, orchestrazione, notifica ai subscriber |
| `kemai_client/tray.py` | Icona pystray, menu, marshal sul thread Tk |
| `kemai_client/ui/widgets.py` | `StopButton` (Canvas con ottagono), `format_duration()` |
| `kemai_client/ui/main_window.py` | Finestra principale 282×312 |
| `kemai_client/ui/settings_window.py` | Finestra impostazioni |
| `kemai_client/ui/project_dialog.py` | Dialog creazione progetto |
| `kemai_client/app.py` | Composizione: costruisce controller, finestre, tray |
| `kemai_client/__main__.py` | Entry point |

Non esiste un modello `Timesheet`: `start_timesheet()` restituisce un semplice `int`,
l'identificativo restituito dal server. Un dataclass aggiungerebbe un livello senza
aggiungere informazione, e l'identificatore serve solo per la chiamata di stop.

## 6. Modello di threading

È il punto architetturalmente più delicato e la ragione principale per cui il progetto
non è un singolo file.

1. **Tkinter gira sempre nel main thread.** Tcl/Tk non è thread-safe.
2. `pystray.Icon.run()` è bloccante → parte su un **thread daemon** con
   `icon.setup()` seguito da `icon.run_detached()`.
3. I callback del menu del vassoio arrivano **sul thread pystray** e non devono toccare
   i widget. È obbligatorio il wrapper `root.after(0, fn)`, che rimanda l'esecuzione
   al main thread.
4. Il cronometro **non usa un thread dedicato**: `root.after(1000, tick)` sul main
   thread basta ed è sicuro.
5. Chiusura finestra: con `close_to_tray` attivo si chiama `withdraw()` invece di
   `destroy()`. `destroy()` senza `quit()` lascia il processo vivo per il thread tray:
   l'uscita reale avviene solo dal menu del vassoio, che chiama `root.quit()` e poi
   `icon.stop()`.
6. Il client HTTP non viene mai chiamato dal thread pystray, solo dal main thread.

La decisione fra `withdraw` e `destroy` è affidata a una **funzione pura**,
`close_behaviour(close_to_tray: bool) -> str` in `kemai_client/tray.py`, che restituisce
`"withdraw"` oppure `"destroy"`. Non è un dettaglio di stile: è la condizione che
distingue un'uscita pulita da un processo invisibile rimasto vivo. Isolandola in una
funzione pura la rende testabile senza avviare pystray né costruire una finestra, che è
l'unico modo per non scoprire il problema quando è ormai troppo tardi.

## 7. Design delle finestre

### 7.1 Principale (282×312)

- Titolo `Kemai - Kimai client`, menu `File` / `Modifica`
- Tre righe `Etichetta + Combobox` in sola lettura per Cliente, Progetto, Attività
- Pulsante ottagonale grande che alterna `Avvia` e `Ferma`
  - etichetta `Avvia` quando nessuna attività è in corso, `Ferma` quando è in corso
  - disabilitato se Cliente, Progetto o Attività non sono tutti selezionati
  - disabilitato anche mentre un'attività è in corso, perché in quel momento l'unica
    azione possibile è `Ferma` e va espressa dalla stessa etichetta, non da uno stato
    disabilitato
- Riga `Avviato il` con Entry in sola lettura
- Cronometro `HH:MM:SS` in font monospaziato grande
- Riga di avviso, inizialmente vuota, che mostra un messaggio non bloccante quando
  un elenco risulta troncato (vedi §8.3)

L'ottagono è disegnato su un `tk.Canvas` con `create_polygon`, non è un semplice
pulsante ttk: la fedeltà visiva è il requisito, e un ttk non disegna poligoni.

### 7.2 Impostazioni

- Campi Host, Nome utente, Token
- Checkbox `Chiudi nel vassoio di sistema`
- Etichetta di stato, in verde se connessa e in rosso se fallita
- Pulsanti `Prova`, `Annulla`, `Salva`
- `Prova` esegue una chiamata di verifica **senza salvare**
- `Annulla` scarta le modifiche e ripristina i valori correnti
- `Salva` persiste e chiude

### 7.3 Dialog progetto

- Titolo `Progetto`, Entry `Nome`, Combobox `Cliente`
- Pulsanti `Salva` e `Annulla`
- Aperto dal menu `File → Nuovo progetto`
- Se il Cliente corrente è già selezionato nella finestra principale, il dialog
  parte da quel cliente

## 8. Integrazione API Kimai 1.15

### 8.1 Cosa è noto e cosa no

Kimai 1.15 è una versione legacy. La conoscenza generale della linea 1.x indica:

- Base path `/api/`
- Autenticazione tramite header `X-AUTH-USER` e `X-AUTH-TOKEN`
- Output JSON via header `Accept: application/json` (le versioni più vecchie richiedevano
  il suffisso `.json` sull'URL)
- Risorse attese: `/api/customers`, `/api/projects`, `/api/activities`, `/api/timesheets`
- Paging tramite `page` e `size`, con totali nell'header `X-Total-Count`
- Errori in JSON con `code` e `message`

**Nessuno di questi punti è stato verificato**, perché l'istanza non è raggiungibile dalla
macchina di sviluppo. Sono **ipotesi**, e il Task 5 del piano esiste per convertirle in
fatti.

### 8.2 Strategia di mitigazione

- `tools/probe_api.py` tenta, in ordine, le varianti di autenticazione e di formato
  (`Accept` header contro suffisso `.json`) e stampa un rapporto chiaro
- Tutti i path stanno in `api/endpoints.py`: correggere dopo il probing tocca un file
- Il parsing accetta sia dizionari che liste, e sia chiavi `id` che `ID`
- Ogni risposta non attesa diventa una `KimaiError` con messaggio in italiano, non un
  crash

### 8.3 Elenchi troncati: dichiarabili subito, paginabili dopo il probing

Kimai 1.x pagina i risultati. Senza gestirlo, un utente con piu' clienti della pagina di
default vedrebbe una lista troncata **senza alcun avviso**, e non potrebbe sapere che
l'elemento cercato esiste. Su uno strumento di time tracking la conseguenza e' concreta:
si sceglie il cliente sbagliato, o non lo si trova.

Non si puo' pero' implementare subito la paginazione vera, perche' che cosa significhi
`size` e se `X-Total-Count` esista sono anch'essi **ipotesi non verificate** (§8.1).
Costruire un loop su un'ipotesi non verificata ripeterebbe l'errore che la centralizzazione
di `endpoints.py` esiste per evitare.

La strategia e' quindi in due tempi, con lo stesso criterio che gia' governa gli endpoint.

**Prima del probing, e subito:** ogni elenco chiede esplicitamente `size=200` invece di
affidarsi al default del server, e il client deduce la troncazione dal numero di elementi
ricevuti. Se una risposta contiene **esattamente** `size` elementi, il client registra
`truncated=True`; il controller lo espone e la finestra principale mostra un messaggio
non bloccante del tipo *"Elenco clienti limitato a 200 elementi"*.

E' un'euristica dichiarata, non una certezza: se ho riempito la pagina, potrebbero
esserne altre. Nel caso peggiore l'app dice una cosa che potrebbe essere falsa
("potrebbero essercene altre"), invece di mentire in silenzio ("non ce ne sono").

**Dopo il probing:** se `page`, `size` e `X-Total-Count` risultano confermati, il client
sostituisce l'euristica con un ciclo di paginazione reale, con un tetto di pagine come
protezione contro un server che risponde sempre la stessa pagina. La modifica resta
confinata a `list_customers`, `list_projects` e `list_activities`.

Il parametro `size` e la sua entita' sono essi stessi ipotesi: vivono in
`api/endpoints.py` con gli altri, e il probing li conferma o li corregge.

## 9. Persistenza della configurazione

- Percorso: `%APPDATA%\KimaiClient\config.json`
- Contiene: `host`, `username`, `token`, `close_to_tray`, ultimi valori selezionati
- Scrittura atomica: si scrive su file temporaneo e si rinomina, per non corrompere la
  config a metà scrittura
- Se il file non esiste o è illeggibile, si riparte da un `Config` di default senza
  sollevare errori
- Il token è salvato **in chiaro**: è una scelta deliberata, dichiarata qui, perché
  l'alternativa su Windows è DPAPI e aggiunge complessità. Sono mitigate le exposure
  peggiori: il token non compare mai nei log e il file resta sotto `%APPDATA%`, che e'
  gia' per utente

Non si dichiara alcun contenimento degli accessi tramite permessi: su Windows `os.chmod`
mappa solo il flag di sola lettura e non limita altri utenti, quindi una simile promessa
sarebbe falsa. Chi volesse contenere davvero il token deve passare da DPAPI o da
Credential Manager, ed e' una decisione separata.

## 10. Gestione degli errori

| Situazione | Comportamento |
|---|---|
| Token non valido | Etichetta in rosso nella finestra impostazioni, si resta li, si suggerisce di riverificare |
| Server irraggiungibile o timeout | `messagebox` con messaggio in italiano, dettaglio tecnico solo nel log |
| Chiusura rete a metà attività | **Il cronometro locale non si ferma**: la sincronizzazione avviene al prossimo Avvia/Ferma o all'uscita |
| Risposta inattesa | `KimaiError` con messaggio comprensibile, nessuna traccia mostrata all'utente |
| Attività già in corso | Il controller rifiuta un secondo avvio e segnala l'errore all'utente |

## 11. Sicurezza

### Credenziali

- Le credenziali sono **dati di runtime**, inseriti dall'utente nella finestra
  impostazioni. Non compaiono in nessun file del repository.
- **Il token non viene mai scritto in un file tracciato da git**, né nella spec, né
  nel piano, né nei test, né nei log.
- Il file di configurazione vive in `%APPDATA%`, **fuori dall'albero del repository**,
  quindi non può finire in un commit neppure per sbaglio.
- `.gitignore` include comunque `config.json`, `*.local.json` e `.env`, come rete di
  sicurezza contro un `git add` esagerato.
- Al primo avvio l'app non ha credenziali: apre la finestra impostazioni e attende.
- Se un token compare per errore in un file tracciato, il rimedio è revocarlo: la
  cronologia git non si riscrive con `rm`.

### Altre regole

- Il token non viene mai scritto nei log
- Gli header di autenticazione non vengono stampati in nessun dump
- La configurazione non contiene segreti oltre al token API
- Nessuna scrittura di file nelle directory dell'installazione: tutto in `%APPDATA%`
- Le richieste verso l'host configurato sono HTTPS; la validazione del certificato
  resta attiva e non è disabilitabile
- I messaggi di errore mostrati all'utente non contengono stack trace: il dettaglio
  tecnico va solo nel file di log locale

### Logging

Il log e' su file, in `%APPDATA%\KimaiClient\kimai.log`, con `RotatingFileHandler` e
tetto di dimensione: l'app viene lanciata da collegamento, dove la console non esiste,
e senza rotazione il file crescerebbe senza limite per un'app pensata per restare aperta
tutta la giornata.

`kemai_client/logging_setup.py` espone due cose:

- `setup_logging(path: Path | None = None) -> None`, chiamata una volta da `app.main()`
- `log_exception(logger, exc: Exception, context: str) -> str`, che scrive il dettaglio
  tecnico completo, con stack trace, e **restituisce** il messaggio breve italiano da
  mostrare a schermo

Il ritorno e' la parte importante: e' l'unico punto in cui i due canali si separano, e
quindi l'unico posto dove vale la promessa "a schermo il messaggio comprensibile, nel log
il dettaglio". Tutti i gestori di errore passano di li', cosi' la regola non puo' essere
dimenticata in un nuovo ramo di codice.

Un test dedicato verifica che provocando un errore di autenticazione il token non
compaia in nessun record. E' la forma piu' utile del progetto: trasforma una regola di
sicurezza da frase documentale a proprieta' verificata.

## 12. Strategia di test

`pytest`, senza bisogno di Tkinter a schermo né dell'istanza reale.

| File | Cosa copre |
|---|---|
| `tests/test_endpoints.py` | Coerenza dei path e presenza di tutti gli endpoint usati |
| `tests/test_models.py` | Immutabilita', uguaglianza, hashabilita', attributo `display` |
| `tests/test_errors.py` | Gerarchia delle eccezioni, messaggi italiani, nessuna esposizione del token |
| `tests/test_client.py` | URL, header, payload, parsing e troncatura, tramite transport finto |
| `tests/test_controller.py` | Cascata, start/stop, rifiuto del doppio avvio, sopravvivenza a rete caduta |
| `tests/test_config.py` | Round-trip JSON, file mancante, file corrotto, scrittura atomica |
| `tests/test_i18n.py` | Presenza di ogni chiave usata nelle finestre |
| `tests/test_logging.py` | Il token non raggiunge mai nessun record di log |
| `tests/test_widgets.py` | `format_duration` e geometria dell'ottagono |
| `tests/test_tray.py` | `close_behaviour` e il marshal dei callback sul main thread, senza avviare pystray |
| `tests/test_probe.py` | Le varianti del probing e l'assenza del token nel sorgente |

I test di `format_duration` sono in `test_widgets.py` e non in `test_controller.py`: la
formattazione della durata e' responsibility di `ui/widgets.py`, e tenere i test accanto
alla proprieta' e' il motivo per cui la divisione fra moduli regge.

Il transport finto è un oggetto con la stessa firma di `requests.Session.request` che
restituisce risposte preparate: i test non aprono mai un socket.

Il test che protegge la sicurezza piu' di tutti e' `test_logging.py`: verifica che
provocando un errore di autenticazione il token non compaia in nessun record di log.
Senza quel test la regola "il token non finisce mai nel log" sarebbe solo una frase in un
documento, non una proprieta' che un cambiamento futuro non puo' rompere in silenzio.

## 13. Strategia di rilascio

- `python -m kemai_client` come unico comando di avvio
- `requirements.txt` con versioni minime fissate
- Le dipendenze reali sono solo `requests` e `pystray`; `Pillow` serve a pystray per
  generare l'icona
- `README.md` con le tre righe di setup e la procedura per generare il token API
- Nessun installer: esplicitamente fuori scope

## 14. Rischi aperti

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Endpoint Kimai 1.15 diversi dalle ipotesi | Alto | Task 5 di probing; path centralizzati in `endpoints.py` |
| Autenticazione non via header ma via Basic auth | Alto | Il probing tenta entrambe; `client.py` ha un solo punto di auth |
| Comportamento del vassoio atipico su Windows | Medio | Il piano prevede una verifica manuale dedicata con passi espliciti |
| `pystray` richiede un loop di eventi proprio | Medio | `setup()` + `run_detached()` su thread daemon, come da documentazione |
| Differenze di resa dei font rispetto agli screenshot | Basso | Il piano prevede un confronto visivo screenshot per screenshot |
| Il server non risolve dalla macchina di sviluppo | Medio già gestito | Tutti i test sono offline; il probing è un task manuale |
| `size` non supportato dal Kimai 1.15, quindi elenchi sempre troncati a 200 | Medio | Il parametro resta in `endpoints.py`; il probing lo conferma. Nel caso peggiore l'avviso di §8.3 e' rumoroso ma mai falso silenziosamente |
| Il log contiene dati personali in chiaro su una macchina condivisa | Basso | Il file sta in `%APPDATA%` ed e' escluso da git; un domani utente per utente e' la mitigazione reale |
