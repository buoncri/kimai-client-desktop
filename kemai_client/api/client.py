"""Client HTTP per l'API Kimai.

Unico modulo che parla con il server. Non sa nulla di Tkinter, e le finestre
non lo usano mai direttamente: ci arriva attraverso `AppController`.

La dipendenza da `requests` e' iniettata. Il parametro `transport` accetta un
qualsiasi oggetto con lo stesso metodo `request` di una `requests.Session`, il
che rende l'intero modulo testabile senza aprire un socket. `requests.Session`
e' solo il caso di default.
"""

from __future__ import annotations

from typing import Any, Protocol
from urllib.parse import urljoin

from kemai_client.api import endpoints
from kemai_client.api.errors import (
    KimaiAuthError,
    KimaiError,
    KimaiNetworkError,
    KimaiNotFoundError,
)
from kemai_client.models import Activity, Customer, Project

DEFAULT_TIMEOUT = 10.0


class Response(Protocol):
    """La parte di una risposta che questo modulo usa."""

    status_code: int
    headers: dict
    text: str

    def json(self) -> Any: ...


class Transport(Protocol):
    """La parte di `requests.Session` che questo modulo usa."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict,
        params: dict | None = None,
        json: dict | None = None,
        timeout: float | None = None,
    ) -> Response: ...


def _default_transport() -> Transport:
    """Costruisce la sessione requests per davvero.

    Importata qui dentro e non a livello di modulo, cosi' i test che non
    toccano la rete non dipendono nemmeno dall'installazione di requests.
    """
    import requests

    return requests.Session()


def _get_id(item: dict) -> int | None:
    """Legge l'id accettando sia `id` che `ID`.

    Il server e' basato su Symfony e la capitalizzazione non e' uniforme fra
    le risorse, quindi tentiamo entrambe le forme.
    """
    value = item.get("id", item.get("ID"))
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_list(payload: Any) -> list[dict]:
    """Normalizza il payload in una lista di dizionari.

    Le API paginate possono rispondere o con una lista diretta o con
    un dizionario che contiene la lista sotto una chiave. Accettiamo entrambi
    perche' non sappiamo quale forma usi il Kimai 1.15 che girera' davvero.
    """
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


class KimaiClient:
    """Accesso alle risorse dell'API Kimai."""

    def __init__(
        self,
        base_url: str,
        username: str,
        token: str,
        transport: Transport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self._token = token
        self.timeout = timeout
        # Il trasporto di default viene creato in pigizia: costruire un client
        # per i test non deve aprire connessioni.
        self._transport = transport

    # --- Richiesta --------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        # Il token viaggia solo qui. Non finisce mai nell'URL, perche' gli URL
        # finiscono nei log di accesso del server.
        return {
            "X-AUTH-USER": self.username,
            "X-AUTH-TOKEN": self._token,
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> Any:
        """Esegue una richiesta e restituisce il corpo JSON gia' validato.

        Tutta la traduzione degli errori in eccezioni del dominio avviene qui,
        in un solo punto, cosi' il resto del modulo riceve sempre o un
        risultato utile o un'eccezione comprensibile.
        """
        transport = self._transport if self._transport is not None else _default_transport()
        url = f"{self.base_url}{path}"

        try:
            response = transport.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except OSError as exc:
            # Timeout, connessione rifiutata, DNS fallito: per l'utente e'
            # un unico fatto, "non riesco a parlare con il server".
            raise KimaiNetworkError(
                "Impossibile contattare il server Kimai. Verifica la connessione."
            ) from exc

        status = response.status_code
        if status in (401, 403):
            raise KimaiAuthError(
                "Credenziali non valide. Controlla nome utente e token API.",
                status=status,
            )
        if status == 404:
            raise KimaiNotFoundError("Risorsa non trovata sul server Kimai.", status=status)
        if status >= 400:
            raise KimaiError(self._server_message(response), status=status)

        return self._decode(response)

    def _server_message(self, response: Response) -> str:
        """Estrae il messaggio d'errore del server, se lo invia.

        Kimai e' Symfony-based e di solito manda `{"code": ..., "message": ...}`.
        Se il corpo non e' JSON leggibile, o se non c'e' un messaggio utile,
        si cade su un testo generico: meglio poco informazione che una
        stringa grezza a schermo.
        """
        try:
            payload = response.json()
        except ValueError:
            return "Errore del server Kimai."
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message
        return "Errore del server Kimai."

    def _decode(self, response: Response) -> Any:
        """Valida che il corpo sia JSON prima di restituirlo.

        Senza questo controllo, un proxy aziendale o una pagina di login che
        rispondono HTML con status 200 produrrebbero un ValueError grezzo
        dal chiamante, che a schermo diventerebbe incomprensibile.
        """
        content_type = ""
        headers = getattr(response, "headers", None) or {}
        for name, value in headers.items():
            if str(name).lower() == "content-type":
                content_type = str(value).lower()
                break

        try:
            return response.json()
        except ValueError as exc:
            if "html" in content_type:
                raise KimaiError(
                    "Il server ha risposto con una pagina HTML invece dei dati "
                    "attesi. Verifica l'indirizzo inserito."
                ) from exc
            raise KimaiError(
                "Risposta non valida dal server Kimai: il contenuto non e' JSON."
            ) from exc

    # --- Risorse ---------------------------------------------------------

    def get_version(self) -> str:
        """Versione del server Kimai, mostrata nella finestra impostazioni."""
        payload = self._request("GET", endpoints.VERSIONS)
        if isinstance(payload, dict):
            version = payload.get("version") or payload.get("Version")
            if isinstance(version, str) and version.strip():
                return version
        return "sconosciuta"

    def test_connection(self) -> str:
        """Verifica le credenziali. Solleva KimaiAuthError se non sono valide."""
        return self.get_version()

    def list_customers(self) -> list[Customer]:
        payload = self._request("GET", endpoints.CUSTOMERS)
        customers = []
        for item in _as_list(payload):
            identifier = _get_id(item)
            if identifier is None:
                continue
            customers.append(Customer(identifier, str(item.get("name", ""))))
        return customers

    def list_projects(self, customer_id: int) -> list[Project]:
        payload = self._request(
            "GET", endpoints.PROJECTS, params={endpoints.PARAM_CUSTOMER: customer_id}
        )
        projects = []
        for item in _as_list(payload):
            identifier = _get_id(item)
            if identifier is None:
                continue
            projects.append(Project(identifier, str(item.get("name", "")), customer_id))
        return projects

    def list_activities(self, project_id: int) -> list[Activity]:
        payload = self._request(
            "GET", endpoints.ACTIVITIES, params={endpoints.PARAM_PROJECT: project_id}
        )
        activities = []
        for item in _as_list(payload):
            identifier = _get_id(item)
            if identifier is None:
                continue
            activities.append(Activity(identifier, str(item.get("name", "")), project_id))
        return activities

    def start_timesheet(self, project_id: int, activity_id: int) -> int:
        payload = self._request(
            "POST",
            endpoints.TIMESHEET_START,
            json={"project": project_id, "activity": activity_id},
        )
        if isinstance(payload, dict):
            identifier = _get_id(payload)
            if identifier is not None:
                return identifier
        raise KimaiError("Il server non ha restituito l'identificativo dell'attivita'.")

    def stop_timesheet(self, timesheet_id: int) -> None:
        self._request("POST", endpoints.TIMESHEET_STOP, json={"id": timesheet_id})

    def create_project(self, name: str, customer_id: int) -> Project:
        payload = self._request(
            "POST", endpoints.PROJECTS, json={"name": name, "customer": customer_id}
        )
        if isinstance(payload, dict):
            identifier = _get_id(payload)
            if identifier is not None:
                return Project(identifier, str(payload.get("name", name)), customer_id)
        raise KimaiError("Il server non ha restituito il nuovo progetto.")
