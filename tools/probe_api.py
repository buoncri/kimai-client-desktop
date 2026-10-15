r"""Script di probing degli endpoint Kimai.

Gira su una macchina collegata alla rete interna e tenta diverse
combinazioni di autenticazione e formato di output per un endpoint
Kimai. Produce un rapporto stampato a console.

Il token viene letto da getpass, mai da un argomento della riga
di comando (evita di finire nella cronologia bash).

Uso:
    .venv\Scripts\python.exe tools/probe_api.py https://host luca
    # poi incolla il token quando richiesto.

Questo modulo non contiene token reali: il token e' richiesto
all'utente in fase di esecuzione.
"""

from __future__ import annotations

import base64
import getpass
import sys
from collections import namedtuple
from pathlib import Path
from typing import List

import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin

# Eseguito come script, Python mette `tools/` nel sys.path e non la root
# del repository: senza questa riga `import kemai_client` fallisce con
# ModuleNotFoundError, e il comando del README non funziona.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kemai_client.api import endpoints  # noqa: E402


# --- Tipi dati ----------------------------------------------------------

RequestVariant = namedtuple(
    "RequestVariant",
    ["path", "method", "headers"],
)

ProbeResult = namedtuple(
    "ProbeResult",
    ["variant", "status", "body_snippet", "verdict"],
)


def _redact(token: str, text: str) -> str:
    """Sostituisce il token in un testo con ***."""
    return text.replace(token, "***")


def build_variants() -> List[RequestVariant]:
    """Crea le varianti di richiesta da provare per un endpoint.

    Combina: 2 metodi di autenticazione × 2 formati di output = almeno 4
    varianti. L'ordine e' l'ordine di preferenza per il probing.

    Returns:
        Lista di RequestVariant con path relativo (es. "/api/versions").
    """
    variants: List[RequestVariant] = []

    # Autenticazione X-AUTH-USER (preferita per Kimai 1.x)
    for use_json_suffix in (False, True):
        path = endpoints.VERSIONS if not use_json_suffix else f"{endpoints.VERSIONS}.json"
        variants.append(
            RequestVariant(
                path=path,
                method="GET",
                headers={
                    "Accept": "application/json",
                    "X-AUTH-USER": "",
                    "X-AUTH-TOKEN": "",
                },
            )
        )

    # Autenticazione Basic
    for use_json_suffix in (False, True):
        path = endpoints.VERSIONS if not use_json_suffix else f"{endpoints.VERSIONS}.json"
        variants.append(
            RequestVariant(
                path=path,
                method="GET",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Basic ",
                },
            )
        )

    return variants


def probe(
    host: str,
    username: str,
    token: str,
    variants: List[RequestVariant],
    opener=None,
) -> List[ProbeResult]:
    """Prova una lista di varianti contro un endpoint Kimai.

    Args:
        host: URL base dell'istanza Kimai (es. "https://host").
        username: nome utente Kimai.
        token: token API.
        variants: varianti da provare (create da build_variants).
        opener: funzione che riceve urllib.request.Request e restituisce
            una risposta o solleva HTTPError/URLError. Default: urlopen.

    Returns:
        Lista di ProbeResult con status, snippet del corpo e verdict.
    """
    if opener is None:
        opener = urllib.request.urlopen

    results: List[ProbeResult] = []

    for variant in variants:
        url = urljoin(host, variant.path)
        headers = dict(variant.headers)
        if "X-AUTH-USER" in headers:
            headers["X-AUTH-USER"] = username
            headers["X-AUTH-TOKEN"] = token
        elif headers.get("Authorization", "").startswith("Basic "):
            headers["Authorization"] = "Basic " + base64.b64encode(
                f"{username}:{token}".encode()
            ).decode()
        request = urllib.request.Request(url, method=variant.method, headers=headers)

        try:
            response = opener(request)
            status = response.status_code if hasattr(response, "status_code") else response.getcode()
            body = response.read().decode("utf-8", errors="replace")[:200]
            verdict = "OK"
        except HTTPError as exc:
            status = exc.code
            body = exc.read().decode("utf-8", errors="replace")[:200]
            if status in (401, 403):
                verdict = "AUTENTICAZIONE FALLITA"
            elif status == 404:
                verdict = "NOT_FOUND"
            else:
                verdict = f"ERRORE {status}"
        except URLError as exc:
            status = 0
            body = str(exc.reason)[:200]
            verdict = "IRRAGGIUNGIBILE"

        results.append(
            ProbeResult(
                variant=variant,
                status=status,
                body_snippet=_redact(token, body),
                verdict=verdict,
            )
        )

    return results


def main() -> int:
    """Entry point: legge credenziali, prova le varianti, stampa un rapporto."""
    host = sys.argv[1] if len(sys.argv) > 1 else input("Host: ")
    username = sys.argv[2] if len(sys.argv) > 2 else input("Username: ")
    token = getpass.getpass("Token API: ")

    variants = build_variants()
    results = probe(host, username, token, variants)

    print(f"\n{'='*70}")
    print(f"Probing {host}{endpoints.VERSIONS}")
    print(f"{'='*70}")

    success = False
    for r in results:
        redacted = _redact(token, r.variant.path)
        print(
            f"  [{r.variant.method:4s}] {redacted:40s} "
            f"-> {r.status:4d}  {r.verdict}"
        )
        if r.status == 200 and r.verdict == "OK":
            success = True

    print(f"\n{'='*70}")
    if success:
        print("ALMENO UNA VARIANTE FUNZIONA su /api/versions")
    else:
        print("NESSUNA variante funzionante su /api/versions")
    print(f"{'='*70}\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
