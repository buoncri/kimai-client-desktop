"""Endpoint dell'API Kimai.

TUTTO quello che riguarda i percorsi del server vive in questo file, e solo
qui. Il motivo e' concreto: il server di sviluppo (`crono.bonificaumbria.local`)
e' in una rete interna non raggiungibile dalla macchina di sviluppo, quindi
nessun endpoint e' mai stato verificato. I valori qui sotto sono IPOTESI basate
sulla linea Kimai 1.x.

Quando il probing (`tools/probe_api.py`) girera' sulla rete interna e
riportera' percorsi diversi, la correzione avverra' tutta qui dentro e in
`KimaiClient._request` per l'autenticazione. Nessun altro file andra' toccato.

Non aggiungere path hardcoded altrove nel progetto.
"""

# Prefisso comune a tutte le risorse API.
BASE_PATH = "/api"

# --- Percorsi -------------------------------------------------------------
# Tutti derivati da BASE_PATH, mai scritti a mano: se il prefisso cambia,
# cambiano anche loro.

VERSIONS = f"{BASE_PATH}/versions"
CUSTOMERS = f"{BASE_PATH}/customers"
PROJECTS = f"{BASE_PATH}/projects"
ACTIVITIES = f"{BASE_PATH}/activities"
TIMESHEETS = f"{BASE_PATH}/timesheets"

# Operazioni sul timesheet corrente. In Kimai 1.x non e' garantito che esistano
# come endpoint dedicati: il probing deve confermare questi due path, e in caso
# contrario si ripiega su POST /api/timesheets con i campi begin ed end.
TIMESHEET_START = f"{BASE_PATH}/timesheets/start"
TIMESHEET_STOP = f"{BASE_PATH}/timesheets/stop"

# --- Parametri di filtro --------------------------------------------------
# Anche i nomi dei parametri di query sono ipotesi non verificate, quindi
# stanno qui con i path e non nella logica del client.

PARAM_CUSTOMER = "customer"
PARAM_PROJECT = "project"
