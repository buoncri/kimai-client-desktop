r"""Verifica del ciclo avvia/ferma contro l'istanza Kimai reale.

Serve a separare i due possibili colpevoli quando "il pulsante Ferma non
funziona": o e' la GUI (bottone grigio, uscita che non chiude), o e' il
server (PATCH che non mette `end`). Questo script isola il contratto
del server e lo dice in modo secco, senza dover toccare la finestra.

Cosa fa, in ordine:

1. legge la configurazione da %APPDATA%\KimaiClient\config.json
2. verifica la connessione e la versione
3. carica la cascata (clienti -> progetti -> attivita')
4. avvia un timesheet reale
5. lo ferma
6. rilegge il timesheet dal server e controlla che `end` sia valorizzato

La finestra non c'entra: se questo script passa, il pulsante Ferma
dovrebbe funzionare e il problema e' nella UI; se fallisce allo step 6,
il problema e' lato server o di autenticazione.

Uso:
    .venv\Scripts\python.exe tools/verify_fix.py
    .venv\Scripts\python.exe tools/verify_fix.py --customer 7

Il token non viene mai stampato. Questo script crea un record reale di
qualche secondo: non e' una simulazione. Se il fermamento fallisce, il
timesheet resta aperto e va chiuso a mano dalla web di Kimai.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Eseguito come script, Python mette `tools/` nel sys.path e non la root
# del repository: senza questa riga `import kemai_client` fallisce con
# ModuleNotFoundError.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kemai_client.api import endpoints  # noqa: E402
from kemai_client.api.client import KimaiClient  # noqa: E402
from kemai_client.api.errors import KimaiError  # noqa: E402
from kemai_client.config import default_path, is_configured, load  # noqa: E402

PASS = "  [ OK ]"
FAIL = "  [KO  ]"
INFO = "  [ -- ]"


class Report:
    """Accumulatore di esiti, con un codice di uscita coerente."""

    def __init__(self) -> None:
        self.failures = 0

    def step(self, ok: bool, label: str, detail: str = "") -> bool:
        mark = PASS if ok else FAIL
        if not ok:
            self.failures += 1
        suffix = f"  ({detail})" if detail else ""
        print(f"{mark} {label}{suffix}")
        return ok

    def info(self, label: str, detail: str = "") -> None:
        print(f"{INFO} {label}{('  (' + detail + ')') if detail else ''}")

    def section(self, title: str) -> None:
        print()
        print(title)
        print("-" * len(title))


def _pick_client(config) -> KimaiClient:
    client = KimaiClient(config.host, config.username, config.token)
    client.verify_tls = config.verify_tls
    return client


def verify(
    config,
    customer_id: int | None = None,
    client: KimaiClient | None = None,
) -> Report:
    """Esegue il giro completo e restituisce il rapporto.

    Args:
        config: configurazione letta da disco.
        customer_id: cliente da usare, o None per scegliere automaticamente.
        client: client gia' costruito. Serve ai test per non parlare con
            un server vero; a runtime viene costruito dalla config.
    """
    report = Report()

    report.section("1. Configurazione")
    path = default_path()
    if not is_configured(config):
        report.step(False, "configurazione completa", f"manca o incompleta: {path}")
        return report
    report.step(True, "configurazione letta", str(path))
    report.info("host", config.host)
    report.info("utente", config.username)
    # Il token non viene stampato, nemmeno per errore.

    if client is None:
        client = _pick_client(config)

    report.section("2. Connessione")
    try:
        version = client.get_version()
        report.step(True, f"server raggiunto, versione {version}")
    except KimaiError as exc:
        report.step(False, "connessione al server", str(exc))
        return report

    report.section("3. Cascata")
    try:
        customers = client.list_customers()
    except KimaiError as exc:
        report.step(False, "caricamento clienti", str(exc))
        return report
    if not report.step(bool(customers), "clienti presenti", f"{len(customers)} trovati"):
        return report

    if customer_id is None:
        chosen = next(
            (c for c in customers if c.id == config.last_customer_id), customers[0]
        )
    else:
        chosen = next((c for c in customers if c.id == customer_id), None)
        if chosen is None:
            report.step(False, f"cliente {customer_id} trovato", "non in elenco")
            return report
    report.step(True, f"cliente: {chosen.display} (id {chosen.id})")

    try:
        projects = client.list_projects(chosen.id)
    except KimaiError as exc:
        report.step(False, "caricamento progetti", str(exc))
        return report
    if not report.step(bool(projects), "progetti presenti", f"{len(projects)} trovati"):
        return report
    project = projects[0]

    try:
        activities = client.list_activities(project.id)
    except KimaiError as exc:
        report.step(False, "caricamento attivita'", str(exc))
        return report
    if not report.step(
        bool(activities), "attivita' presenti", f"{len(activities)} trovate"
    ):
        report.step(
            False,
            "potremo avviare",
            f"il progetto {project.display!r} non ha attivita': in Kimai "
            "assegnane una prima",
        )
        return report
    activity = activities[0]
    report.info("progetto", f"{project.display} (id {project.id})")
    report.info("attivita'", f"{activity.display} (id {activity.id})")

    report.section("4. Avvio e arresto")
    timesheet_id: int | None = None
    try:
        timesheet_id = client.start_timesheet(project.id, activity.id)
        report.step(
            isinstance(timesheet_id, int),
            "timesheet avviato",
            f"id {timesheet_id}",
        )
    except KimaiError as exc:
        report.step(False, "avvio timesheet", str(exc))
        return report

    try:
        client.stop_timesheet(timesheet_id)
        report.step(True, "timesheet fermato", f"PATCH su id {timesheet_id}")
    except KimaiError as exc:
        report.step(
            False,
            "arresto timesheet",
            f"{exc} -- il record {timesheet_id} resta APERTO, chiudilo a mano",
        )
        return report

    report.section("5. Verifica sul server")
    try:
        payload = client._request(  # noqa: SLF001 - strumento diagnostico
            "GET", f"{endpoints.TIMESHEETS}/{timesheet_id}"
        )
    except KimaiError as exc:
        report.step(False, "rilettura del timesheet", str(exc))
        return report

    end = payload.get("end") if isinstance(payload, dict) else None
    report.step(
        bool(end),
        "il server ha registrato l'ora di fine",
        f"end={end!r}" if end else "end vuoto: il record risulta ancora aperto",
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica il ciclo avvia/ferma contro l'istanza Kimai."
    )
    parser.add_argument(
        "--customer",
        type=int,
        default=None,
        help="id del cliente da usare (default: ultimo usato, o il primo)",
    )
    args = parser.parse_args()

    config = load()
    report = verify(config, args.customer)

    print()
    print("=" * 70)
    if report.failures == 0:
        print("TUTTO OK: il server accetta e chiude i timesheet.")
        print("Se il pulsante Ferma non funziona, il problema e' nella UI.")
    else:
        print(f"{report.failures} VERIFICHE FALLITE.")
        print("Se fallisce la lettura di `end`, il problema non e' nella UI.")
    print("=" * 70)

    return 0 if report.failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())