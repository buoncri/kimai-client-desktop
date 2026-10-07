# Kimai Desktop Client

Client desktop in Python/Tkinter per l'API del server **Kimai** (time tracking).

## Installazione

### Prerequisiti

- **Python 3.10+** (3.12 consigliato)
- Windows (sviluppato e testato su Windows 10/11)

### Procedura

```bash
# Crea un ambiente virtuale
"C:\Users\luca\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv

# Attiva e installa le dipendenze
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Le dipendenze runtime sono **tre**: `requests`, `pystray` (Pillow come dipendenza transitiva), `pystray` (per l'icona nel vassoio).

### Esecuzione

```bash
.venv\Scripts\python.exe -m kemai_client
```

Al primo avvio appare la finestra **Impostazioni**: inserisci host, nome utente e token API.
Il pulsante "Salva" persiste la configurazione in `%APPDATA%\KimaiClient\config.json` (atomico).

## Configurazione

Il file di configurazione si trova in:

```
%APPDATA%\KimaiClient\config.json
```

Contiene:
| Campo | Descrizione |
|---|---|
| `host` | URL del server Kimai (es. `https://crono.bonificaumbria.local`) |
| `username` | Nome utente API |
| `token` | Token API (in chiaro, come deciso da Kimai) |
| `close_to_tray` | Chiudi nel vassoio di sistema |
| `last_customer_id` | Ultimo cliente selezionato |
| `last_project_id` | Ultimo progetto selezionato |

Il file **non è tracciato da git** (`.gitignore` lo esclude).

## Token API

Il token è un dato sensibile: **non è mai stato inserito manualmente** nei file del
repository e non compare in nessuna documentazione. Per generarlo:

1. Accedi al pannello Web di Kimai con le tue credenziali.
2. Vai su **Impostazioni utente** → **Token API** (o "Access tokens").
3. Clicca **Genera nuovo token** (dai un nome identificativo, es. "Desktop").
4. **Copia subito il token** (non sarà più visibile dopo la chiusura del dialog).
5. Incollalo nella finestra *Impostazioni* del client desktop.

> ⚠️ Il token è memorizzato in chiaro su disco (scelta deliberata: su Windows
> DPAPI richiederebbe un pacchetto aggiuntivo). Il file è sotto `%APPDATA%`, che
> è già per utente, e non viene tracciato da git.

## Interfaccia

La finestra principale (282×312 px) contiene:

- **Selettori a cascata**: Cliente → Progetto → Attività
- **Pulsante centrale a forma di ottagono**: alterna *Avvia* / *Ferma*
- **Cronometro** HH:MM:SS con aggiornamento ogni secondo
- **Campo "Avviato il"** con data/ora in sola lettura
- **Avviso di troncatura** (se l'elenco clienti/progetti/attività supera 200 elementi)

Il pulsante nel **vassoio di sistema** (pystray) mostra: *Mostra*, *Avvia/Ferma*, *Esci*.

## Note tecniche

- Tutte le finestre passano da `AppController`: **non chiamano mai l'API Kimai direttamente**.
- Il client HTTP usa `requests` con sessione iniettata per i test (trasporto finto).
- Le stringhe visibili sono tutte in italiano e centralizzate in `kemai_client/i18n.py`.
- Il file di log locale (`%APPDATA%\KimaiClient\kimai.log`) ruota a 512 KB, massimo 3 backup.
- Il token **non compare mai nel log**: gli errori usano un canale separato
  (messaggio breve a schermo, dettaglio tecnico solo nel file).
- Tutte le operazioni Tkinter girano nel **main thread**; pystray usa un **thread daemon**
  (`run_detached()`).

## Licenza

Nessuna: progetto personale per l'organizzazione.
