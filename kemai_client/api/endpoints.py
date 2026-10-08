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
- POST /api/timesheets: crea il timesheet (200, risposta con "id").
  Campi accettati: begin, end, project, activity, description, billable,
  tags. Formato begin/end accettato: "Y-m-d H:i:s" (anche ISO con "T").
- PATCH /api/timesheets/{id}: aggiorna (200). Metodi ammessi sull'item:
  GET, PATCH, DELETE (PUT e POST rispondono 405).
- POST /api/timesheets/start e /stop: NON esistono (405). Ciclo completo
  creato e cancellato dal vivo: POST 200 -> PATCH 200 -> DELETE 204.

Ancora NON verificati (servono 200 reali con query string):
- i nomi dei parametri di paging (page, size)

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
