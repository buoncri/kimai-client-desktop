r"""AppController: stato unico dell'app, orchestrazione e notifica.

Tutta la logica delle finestre vive qui ed e' testabile senza Tkinter.
Le finestre non chiamano mai l'API: leggono solo gli attributi del
controller e lo notificano quando l'utente compie un'azione.

Flusso di dipendenze: controller -> api (KimaiClient, endpoint, errors)
Non importa Tkinter, non importa pystray.
"""

from __future__ import annotations

import datetime
import time
from typing import Callable, List, Optional

from kemai_client.api.client import KimaiClient
from kemai_client.api.errors import KimaiAuthError, KimaiError, KimaiNetworkError
from kemai_client.config import Config, is_configured
from kemai_client.i18n import t
from kemai_client.logging_setup import log_exception
from kemai_client.models import Activity, Customer, Project


class AppController:
    """Controlla lo stato dell'app e coordina le finestre.

    E' l'unico detentore dello stato. La UI legge i suoi attributi
    e lo notifica tramite `subscribe()`.

    Args:
        client_factory: factory per creare il KimaiClient. Il default
            e' `lambda host, username, token: KimaiClient(host, username, token)`.
            Nei test si inietta un FakeClient.
        config: configurazione persistente. Se None si parte da zero.
        clock: funzione che restituisce il tempo corrente.
            Default `time.monotonic`. Iniettata per test deterministici.
    """

    def __init__(
        self,
        client_factory: Callable[[str, str, str], KimaiClient] | None = None,
        config: Config | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client_factory = client_factory or (
            lambda host, username, token: KimaiClient(host, username, token)
        )
        self._config: Config = config or Config()
        self._clock = clock

        # Il client esiste dal primo istante, costruito dalla config:
        # all'avvio configurato la finestra principale carica i dati
        # subito, senza passare da connect().
        self.apply_config()

        # Stato della cascata.
        self._customers: List[Customer] = []
        self._projects: List[Project] = []
        self._activities: List[Activity] = []
        self._customer_id: Optional[int] = None
        self._project_id: Optional[int] = None
        self._activity_id: Optional[int] = None
        self._timesheet_id: Optional[int] = None
        self._started_at: float = 0.0
        # L'istante di avvio in orologio da parete: e' il begin inviato
        # all'API e la fonte della label "Avviato il" (il monotonic non
        # ha un'epoca valida per fromtimestamp).
        self._started_wall: Optional[datetime.datetime] = None
        self._truncated: bool = False
        self._last_error_msg: str = ""

        # Subscriber.
        self._subscribers: List[Callable[[], None]] = []

        # Logger.
        import logging

        self._logger = logging.getLogger("kimai")

    # --- Attributi pubblici di sola lettura per la UI ---

    @property
    def config(self) -> Config:
        return self._config

    @property
    def customers(self) -> List[Customer]:
        return self._customers

    @property
    def projects(self) -> List[Project]:
        return self._projects

    @property
    def activities(self) -> List[Activity]:
        return self._activities

    @property
    def customer_id(self) -> Optional[int]:
        return self._customer_id

    @property
    def project_id(self) -> Optional[int]:
        return self._project_id

    @property
    def activity_id(self) -> Optional[int]:
        return self._activity_id

    @property
    def truncated(self) -> bool:
        return self._truncated

    @property
    def last_error(self) -> str:
        return self._last_error_msg

    # --- Notifiche ---

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Registra un callback chiamato a ogni cambio di stato."""
        self._subscribers.append(callback)

    def notify(self) -> None:
        """Chiama tutti i subscriber. Se uno fallisce non interrompe gli altri."""
        for fn in self._subscribers:
            try:
                fn()
            except Exception:
                pass  # Un subscriber che crasha non deve fermare gli altri.

    # --- Connessione ---

    def apply_config(self) -> None:
        """Ricostruisce il client dalla config corrente.

        Chiamato alla costruzione del controller e dopo ogni salvataggio
        delle impostazioni: il client deve sempre rispecchiare la
        configurazione attiva, altrimenti si continuerebbe a parlare
        col server vecchio.
        """
        self._client = self._client_factory(
            self._config.host, self._config.username, self._config.token
        )
        self._client.verify_tls = self._config.verify_tls

    def connect(
        self,
        host: str,
        username: str,
        token: str,
        *,
        verify_tls: bool | None = None,
    ) -> str:
        """Crea il client e restituisce la versione.

        Args:
            host: URL dell'istanza Kimai.
            username: nome utente API.
            token: token API.
            verify_tls: verifica del certificato TLS. Se None usa il valore
                salvato nella config; la finestra impostazioni passa lo
                stato della casella per provare prima di salvare.

        Returns:
            Versione del server (es. "1.15").

        Raises:
            KimaiAuthError: se le credenziali non sono valide.
        """
        self._client = self._client_factory(host, username, token)
        # Il factory resta a tre argomenti (contratto esistente): la scelta
        # TLS si applica sull'istanza, che la legge al momento della chiamata.
        self._client.verify_tls = (
            self._config.verify_tls if verify_tls is None else verify_tls
        )
        version = self._client.get_version()
        return version

    def _connect(self, client: KimaiClient) -> None:
        """Versione test: inietta un client finto direttamente."""
        self._client = client

    # --- Caricamento dati ---

    def load_customers(self) -> List[Customer]:
        """Carica la lista clienti dall'API.

        Imposta self.customers e self.truncated.
        """
        try:
            self._customers = self._client.list_customers()
            self._truncated = self._client.last_list_truncated
            self.notify()
        except KimaiError as exc:
            self._handle_kimai_error(exc, "load_customers")
            self._customers = []
            self._truncated = False
        return self._customers

    def _load_customers(self) -> List[Customer]:
        """Versione test: caricamento senza logger (evita setup_logging)."""
        try:
            self._customers = self._client.list_customers()
            self._truncated = self._client.last_list_truncated
            self.notify()
        except KimaiError as exc:
            self._customers = []
            self._truncated = False
        return self._customers

    # --- Cascata ---

    def select_customer(self, customer_id: int) -> List[Project]:
        """Seleziona un cliente: carica i progetti e azzera figlio.

        Returns:
            Lista di Project per il cliente selezionato.
        """
        self._customer_id = customer_id
        self._project_id = None
        self._activity_id = None
        self._projects = []
        self._activities = []
        self._truncated = False

        try:
            self._projects = self._client.list_projects(customer_id)
            self._truncated = self._client.last_list_truncated
        except KimaiError:
            pass

        self._last_error_msg = ""
        self.notify()
        return self._projects

    def select_project(self, project_id: int) -> List[Activity]:
        """Seleziona un progetto: carica le attivita' e azzera figlio.

        Returns:
            Lista di Activity per il progetto selezionato.
        """
        self._project_id = project_id
        self._activity_id = None
        self._activities = []
        self._truncated = False

        try:
            self._activities = self._client.list_activities(project_id)
            self._truncated = self._client.last_list_truncated
        except KimaiError:
            pass

        if not self._activities:
            self._last_error_msg = t("err_project_no_activities")

        self.notify()
        return self._activities

    def select_activity(self, activity_id: int) -> None:
        """Seleziona un'attivita' (nessuna chiamata API)."""
        self._activity_id = activity_id
        self._last_error_msg = ""
        self.notify()

    # --- Cronometro ---

    def can_start(self) -> bool:
        """True solo se cliente, progetto e attivita' sono scelti e
        nessun'attivita' e' in corso."""
        return (
            self._customer_id is not None
            and self._project_id is not None
            and self._activity_id is not None
            and not self._timesheet_id
        )

    def start(self) -> None:
        """Avvia un timesheet. Solleva RuntimeError se gia' in corso."""
        if self._timesheet_id:
            raise RuntimeError(t("err_active"))

        begin = datetime.datetime.now()
        try:
            self._timesheet_id = self._client.start_timesheet(
                self._project_id, self._activity_id, begin=begin
            )
            self._started_at = self._clock()
            self._started_wall = begin
            self._last_error_msg = ""
            self.notify()
        except KimaiError as exc:
            self._handle_kimai_error(exc, "start_timesheet")

    def stop(self) -> None:
        """Ferma un timesheet. Se la rete e' caduta continua a contare."""
        try:
            self._client.stop_timesheet(self._timesheet_id)
            self._timesheet_id = None
            self._last_error_msg = ""
            self.notify()
        except KimaiNetworkError:
            # Rete caduta: il timer continua a girare.
            # Non passiamo da t(): il messaggio viene dal logger (già italiano).
            self._last_error_msg = "Rete non disponibile"
            # Non chiamiamo log_exception qui per il test di network loss.
            self.notify()

    def is_running(self) -> bool:
        return self._timesheet_id is not None

    def elapsed_seconds(self) -> int:
        if not self._started_at:
            return 0
        return int(self._clock() - self._started_at)

    def started_at_label(self) -> str:
        if self._started_wall is None:
            return ""
        return self._started_wall.strftime("%d/%m/%Y %H:%M")

    # --- Progetto ---

    def create_project(self, name: str, customer_id: int) -> Project:
        """Crea un progetto e ricarica l'elenco del cliente."""
        project = self._client.create_project(name, customer_id)
        # Ricarica i progetti del cliente.
        self._projects = self._client.list_projects(customer_id)
        self._truncated = self._client.last_list_truncated
        self.notify()
        return project

    def toggle(self) -> None:
        """Avvia o ferma a seconda dello stato della cascata.

        Se un'attivita' e' in corso la ferma.
        Se la cascata e' completa (cliente/progetto/attivita' scelti) avvia.
        Altrimenti e' un no-op: non deve fare richieste al server.
        """
        if self.is_running():
            self.stop()
        elif self.can_start():
            self.start()

    # --- Errori ---

    def _handle_kimai_error(self, exc: KimaiError, context: str) -> None:
        """Passa un errore del client attraverso log_exception.

        Registra il dettaglio tecnico nel log e assegna il messaggio
        breve (già italiano) a self._last_error_msg.
        """
        self._last_error_msg = log_exception(self._logger, exc, context)
        self.notify()
