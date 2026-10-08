"""Endpoint dell'API Kimai.

TUTTO quello che riguarda i percorsi del server vive in questo file, e solo
qui. I percorsi delle collezioni e della versione sono stati VERIFICATI live
contro il server reale il 2026-10-08 (richieste con credenziali finte e
verifica TLS disattivata: 401/403 = esistente, 404 = inesistente,
405 = esiste con metodo diverso).

Esito della verifica del 2026-10-08:
- GET /api/version: esiste (il plurale /api/versions NON esiste).
- GET /api/customers, /api/projects, /api/activities, /api/timesheets:
  esistono.
- POST /api/timesheets/start e /stop: NON esistono come endpoint dedicati
  (405: il server interpreta "start" come {id}). Per avviare e fermare si
  usa il ripiego previsto dal piano, POST /api/timesheets con i campi
  begin/end - da confermare con credenziali vere prima di fidarsi
  del formato dei campi.

Ancora NON verificati (servono credenziali vere, per ottenere 200):
- i nomi dei parametri di query (customer, project) e di paging (page, size)
- il formato dei campi begin/end del timesheet

Non aggiungere path hardcoded altrove nel progetto.
"""

# Prefisso comune a tutte le risorse API.
BASE_PATH = "/api"

# --- Percorsi -------------------------------------------------------------
# Tutti derivati da BASE_PATH, mai scritti a mano: se il prefisso cambia,
# cambiano anche loro.

VERSIONS = f"{BASE_PATH}/version"
CUSTOMERS = f"{BASE_PATH}/customers"
PROJECTS = f"{BASE_PATH}/projects"
ACTIVITIES = f"{BASE_PATH}/activities"
TIMESHEETS = f"{BASE_PATH}/timesheets"

# Operazioni sul timesheet corrente. VERIFICA 2026-10-08: endpoint dedicati
# NON esistono (405). Il client deve ripiegare su POST /api/timesheets con
# i campi begin ed end; la correzione del client resta da fare, con
# credenziali vere per confermare il formato dei campi.
TIMESHEET_START = f"{BASE_PATH}/timesheets/start"
TIMESHEET_STOP = f"{BASE_PATH}/timesheets/stop"

# --- Parametri di filtro --------------------------------------------------
# Anche i nomi dei parametri di query sono ipotesi non verificate, quindi
# stanno qui con i path e non nella logica del client.

PARAM_CUSTOMER = "customer"
PARAM_PROJECT = "project"

# --- Parametri di paging --------------------------------------------------
# Valori ipotetici per Kimai 1.x. Il probing del Task 5 li confermerà o correggerà.

PARAM_PAGE = "page"
PARAM_SIZE = "size"
DEFAULT_PAGE_SIZE = 200
