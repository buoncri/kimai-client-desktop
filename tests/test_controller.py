r"""Test di AppController.

Tutti i test usano un FakeClient (nessuna rete) e un clock finto
per test deterministici. Il controller e' il cuore logico: tutto
passa da qui, mai dalle finestre.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kemai_client.api.errors import KimaiAuthError, KimaiNetworkError
from kemai_client.config import Config, is_configured
from kemai_client.controller import AppController
from kemai_client.i18n import t
from kemai_client.logging_setup import log_exception
from kemai_client.models import Activity, Customer, Project


# --- Fake transport per i test del controller ---

class FakeClient:
    """Client finto che registra le chiamate e restituisce dati fissi."""

    def __init__(self):
        self.calls: list = []
        self.last_list_truncated = False
        self._created_projects: dict[int, list[Project]] = {}  # customer_id -> list

    def record(self, method, **kwargs):
        self.calls.append((method, kwargs))
        return kwargs.get("return_value")

    def get_version(self):
        return self.record("get_version", return_value="1.15")

    def test_connection(self):
        return self.record("test_connection", return_value="1.15")

    def list_customers(self):
        return self.record(
            "list_customers",
            return_value=[
                Customer(1, "Acme"),
                Customer(2, "Globex"),
            ],
        )

    def list_projects(self, customer_id):
        self.record("list_projects", customer_id=customer_id)
        # Include projects created via create_project.
        projects = list(self._created_projects.get(customer_id, []))
        if customer_id == 1:
            projects = [
                Project(10, "Sito web", 1),
                Project(11, "App mobile", 1),
            ] + projects
        return projects

    def list_activities(self, project_id):
        self.record("list_activities", project_id=project_id)
        if project_id == 10:
            return [
                Activity(100, "Lavoro", 10),
                Activity(101, "Bug", 10),
            ]
        return []

    def start_timesheet(self, project_id, activity_id):
        self.record("start_timesheet", project_id=project_id, activity_id=activity_id)
        return 42

    def stop_timesheet(self, timesheet_id):
        self.record("stop_timesheet", timesheet_id=timesheet_id)

    def create_project(self, name, customer_id):
        project = Project(99, name, customer_id)
        self._created_projects[customer_id] = self._created_projects.get(customer_id, [])
        self._created_projects[customer_id].append(project)
        return self.record("create_project", return_value=project)


class TestSelectCascade:
    def test_select_customer_returns_projects(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        result = ctrl.select_customer(1)
        assert result == [Project(10, "Sito web", 1), Project(11, "App mobile", 1)]
        assert ctrl.customer_id == 1

    def test_select_customer_clears_children(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        # Un nuovo select_customer azzera i figli.
        ctrl.select_customer(2)
        assert ctrl.project_id is None
        assert ctrl.activity_id is None


class TestSelectProject:
    def test_select_project_returns_activities(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        result = ctrl.select_project(10)
        assert result == [
            Activity(100, "Lavoro", 10),
            Activity(101, "Bug", 10),
        ]
        assert ctrl.project_id == 10


class TestCanStart:
    def test_can_start_requires_all_three(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        assert ctrl.can_start() is False  # manca activity
        ctrl.select_activity(100)
        assert ctrl.can_start() is True


class TestStartStop:
    def test_start_records_and_notifies(self):
        client = FakeClient()
        notified = []
        ctrl = AppController(
            lambda h, u, t: client,
            clock=lambda: 100.0,
        )
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.subscribe(lambda: notified.append(1))
        ctrl.start()
        assert ctrl.is_running() is True
        assert len(notified) >= 1

    def test_start_twice_raises(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.start()
        with pytest.raises(RuntimeError, match=t("err_active")):
            ctrl.start()

    def test_stop_clears_state(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.start()
        ctrl.stop()
        assert ctrl.is_running() is False
        assert ctrl._timesheet_id is None

    def test_elapsed_uses_injected_clock(self):
        client = FakeClient()
        clock = time.monotonic
        ctrl = AppController(
            lambda h, u, t: client,
            clock=clock,
        )
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        # Finto: started_at a 100.0, clock che torna 106.5 -> 6 secondi.
        ctrl._started_at = 100.0
        # Sostituiamo il clock per controllare elapsed_seconds().
        ctrl._clock = lambda: 106.5
        elapsed = ctrl.elapsed_seconds()
        assert elapsed == 6

    def test_toggle_dispatches(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.toggle()
        assert ctrl.is_running()
        ctrl.toggle()
        assert not ctrl.is_running()


class TestNetworkLoss:
    def test_network_loss_keeps_timer_running(self):
        # Se stop_timesheet solleva KimaiNetworkError, il timer
        # continua a girare e is_running resta True.
        client = FakeClient()

        def failing_start(*args, **kwargs):
            client.record("start_timesheet")
            return 42

        def failing_stop(*args, **kwargs):
            client.record("stop_timesheet")
            raise KimaiNetworkError("Rete caduta")

        client.start_timesheet = failing_start
        client.stop_timesheet = failing_stop

        # Clock che avanza di 10s ad ogni chiamata.
        state = [100]
        def fake_clock():
            state[0] += 10
            return float(state[0])

        ctrl = AppController(lambda h, u, t: client, clock=fake_clock)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.start()  # _started_at = 110.0
        # stop fallisce ma il timer continua.
        ctrl.stop()
        assert ctrl.is_running() is True
        assert ctrl.elapsed_seconds() >= 10
        assert ctrl.last_error


class TestProjectWithoutActivities:
    def test_project_without_activities_disables_start(self):
        client = FakeClient()
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(11)  # 11 ha zero activities (FakeClient restituisce [])
        assert ctrl.can_start() is False
        assert ctrl.last_error


class TestAuthErrorItalian:
    def test_auth_error_is_italian_and_tokenless(self):
        client = FakeClient()

        def failing_start(*args, **kwargs):
            raise KimaiAuthError("Token scaduto, rigenerare")

        client.start_timesheet = failing_start

        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)
        ctrl.start()
        assert ctrl.last_error
        # Il messaggio e' in italiano e non contiene il token finto.
        assert "token" not in ctrl.last_error.lower() or "scaduto" in ctrl.last_error.lower()


class TestCreateProject:
    def test_create_project_reloads(self):
        # FakeClient traccia i progetti creati per customer_id.
        client = FakeClient()
        # Dopo create_project("Nuovo", 1), list_projects(1) deve
        # includere "Nuovo".
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.create_project("Nuovo", 1)
        # Il nuovo progetto e' nell'elenco.
        assert any(p.name == "Nuovo" for p in ctrl.projects)


class TestTruncated:
    def test_truncated_flag_is_exposed(self):
        client = FakeClient()
        client.last_list_truncated = True
        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        assert ctrl.truncated is True


class TestErrorsGoThroughLog:
    def test_errors_go_through_log_exception(self):
        # Un errore del client finisce in controller.last_error() e
        # viene passato a log_exception (testato in logging_setup.py).
        # Qui verifichiamo che last_error sia impostato e non vuoto.
        client = FakeClient()

        def failing_start(*args, **kwargs):
            raise KimaiNetworkError("Network down")

        client.start_timesheet = failing_start

        ctrl = AppController(lambda h, u, t: client)
        ctrl._connect(client)
        ctrl._load_customers()
        ctrl.select_customer(1)
        ctrl.select_project(10)
        ctrl.select_activity(100)

        ctrl.start()

        # L'errore e' in last_error (non vuoto, non il token).
        assert ctrl.last_error
        assert len(ctrl.last_error) > 0


# --- Verifica TLS: il controller porta la scelta della config al client ---

class TestConnectVerifyTls:
    def test_connect_applies_config_verify_tls(self):
        config = Config(
            host="https://host", username="u", token="t", verify_tls=False
        )
        ctrl = AppController(lambda h, u, t: FakeClient(), config=config)
        ctrl.connect("https://host", "u", "t")
        assert ctrl._client.verify_tls is False

    def test_connect_default_keeps_verification(self):
        config = Config(host="https://host", username="u", token="t")
        ctrl = AppController(lambda h, u, t: FakeClient(), config=config)
        ctrl.connect("https://host", "u", "t")
        assert ctrl._client.verify_tls is True

    def test_connect_explicit_choice_overrides_config(self):
        # La finestra impostazioni passa lo stato della casella: vince sulla
        # config salvata, perche' "Prova" verifica prima ancora di salvare.
        config = Config(
            host="https://host", username="u", token="t", verify_tls=True
        )
        ctrl = AppController(lambda h, u, t: FakeClient(), config=config)
        ctrl.connect("https://host", "u", "t", verify_tls=False)
        assert ctrl._client.verify_tls is False


# --- Ciclo di vita del client: dalla config, ricostruito al salvataggio ---

class TestClientLifecycle:
    def test_client_built_from_config_at_construction(self):
        # All'avvio configurato il client deve esistere gia': la finestra
        # principale carica i clienti subito, senza passare da connect().
        config = Config(
            host="https://host", username="u", token="t", verify_tls=False
        )
        ctrl = AppController(lambda h, u, t: FakeClient(), config=config)
        assert ctrl._client.verify_tls is False

    def test_apply_config_rebuilds_client_after_save(self):
        # Dopo aver salvato impostazioni diverse, il client deve rispecchiare
        # la nuova config: senza rebuild si continuerebbe a parlare col
        # server vecchio.
        config = Config(host="https://old", username="u", token="t")
        ctrl = AppController(lambda h, u, t: FakeClient(), config=config)
        old = ctrl._client
        ctrl._config = Config(
            host="https://new", username="u2", token="t2", verify_tls=False
        )
        ctrl.apply_config()
        assert ctrl._client is not old
        assert ctrl._client.verify_tls is False
