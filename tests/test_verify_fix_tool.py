r"""Test dello strumento di verifica tools/verify_fix.py.

Lo strumento dice al collega "il server funziona" oppure "il problema
e' altrove". Se sbaglia, guida la diagnosi sulla strada sbagliata, quindi
va testato come qualsiasi altro codice: con un finto client, senza rete.

Non richiede configurazione reale: `Config` viene costruito in memoria con
il token fittizio convenzionale del progetto.
"""

import pytest

from verify_fix import verify

from kemai_client.api.errors import KimaiAuthError, KimaiNetworkError  # noqa: E402
from kemai_client.config import Config  # noqa: E402
from kemai_client.models import Activity, Customer, Project  # noqa: E402

TEST_TOKEN = "test-token-not-real"


class FakeServer:
    """Client finto che simula un Kimai, con controlli sui difetti."""

    def __init__(self, *, end_after_stop: str | None = "2026-10-15 10:00:00"):
        self.end_after_stop = end_after_stop
        self.calls: list[tuple[str, dict]] = []

    def _record(self, name, **kw):
        self.calls.append((name, kw))

    def get_version(self):
        self._record("get_version")
        return "1.15"

    def list_customers(self):
        self._record("list_customers")
        return [Customer(1, "Acme"), Customer(2, "Globex")]

    def list_projects(self, customer_id):
        self._record("list_projects", customer_id=customer_id)
        return [Project(10, "Sito web", customer_id)]

    def list_activities(self, project_id):
        self._record("list_activities", project_id=project_id)
        return [Activity(100, "Bug", project_id)]

    def start_timesheet(self, project_id, activity_id, begin=None):
        self._record(
            "start_timesheet", project_id=project_id, activity_id=activity_id
        )
        return 4242

    def stop_timesheet(self, timesheet_id, end=None):
        self._record("stop_timesheet", timesheet_id=timesheet_id)
        if isinstance(timesheet_id, str) and timesheet_id == "network":
            raise KimaiNetworkError("rete caduta")

    def _request(self, method, url, **kwargs):
        self._record("read_back", url=url)
        return {"id": 4242, "end": self.end_after_stop}


@pytest.fixture
def config():
    return Config(
        host="https://kimai.example",
        username="prova",
        token=TEST_TOKEN,
        verify_tls=True,
    )


def _server(**kw):
    return FakeServer(**kw)


class TestHappyPath:
    def test_full_cycle_passes(self, config, capsys):
        report = verify(config, client=_server())

        assert report.failures == 0, capsys.readouterr().out

    def test_server_is_actually_asked_to_close_the_record(self, config):
        server = _server()
        verify(config, client=server)

        names = [c[0] for c in server.calls]
        assert "start_timesheet" in names
        assert "stop_timesheet" in names
        assert "read_back" in names

    def test_token_is_never_printed(self, config, capsys):
        verify(config, client=_server())

        assert TEST_TOKEN not in capsys.readouterr().out


class TestServerSideFailure:
    def test_missing_end_is_reported_as_a_failure(self, config, capsys):
        """`end` vuoto e' il caso pericoloso: il record resta aperto.

        E' l'unico esito che cambia la diagnosi, quindi deve essere
        rosso, non un avviso.
        """
        report = verify(config, client=_server(end_after_stop=None))
        out = capsys.readouterr().out

        assert report.failures == 1, out
        assert "ancora aperto" in out

    def test_network_error_stopping_is_a_failure(self, config, capsys):
        class FlakyNetwork(FakeServer):
            def stop_timesheet(self, timesheet_id, end=None):
                self._record("stop_timesheet", timesheet_id=timesheet_id)
                raise KimaiNetworkError("rete caduta")

        report = verify(config, client=FlakyNetwork())

        assert report.failures == 1, capsys.readouterr().out

    def test_auth_error_on_connect_stops_early(self, config):
        class Unreachable:
            def get_version(self):
                raise KimaiAuthError("credenziali non valide", status=401)

            def list_customers(self):
                raise AssertionError("non deve arrivare qui")

            def list_projects(self, customer_id):
                raise AssertionError("non deve arrivare qui")

            def list_activities(self, project_id):
                raise AssertionError("non deve arrivare qui")

            def start_timesheet(self, *a, **k):
                raise AssertionError("non deve arrivare qui")

            def stop_timesheet(self, *a, **k):
                raise AssertionError("non deve arrivare qui")

        report = verify(config, client=Unreachable())

        assert report.failures == 1


class TestIncompleteData:
    def test_project_without_activities_is_explained(self, config, capsys):
        class NoActivities(FakeServer):
            def list_activities(self, project_id):
                return []

        report = verify(config, client=NoActivities())
        out = capsys.readouterr().out

        assert report.failures == 2, out
        assert "non ha attivita" in out

    def test_empty_customer_list_is_a_failure(self, config):
        class NoCustomers(FakeServer):
            def list_customers(self):
                return []

        report = verify(config, client=NoCustomers())

        assert report.failures == 1

    def test_missing_config_is_a_failure(self):
        report = verify(Config(), client=None)

        assert report.failures == 1


class TestCustomerSelection:
    def test_uses_requested_customer(self, config):
        server = _server()
        verify(config, customer_id=2, client=server)

        started = [c for c in server.calls if c[0] == "start_timesheet"]
        assert started, "nessun avvio effettuato"

    def test_unknown_customer_is_reported(self, config, capsys):
        report = verify(config, customer_id=999, client=_server())
        out = capsys.readouterr().out

        assert report.failures == 1
        assert "non in elenco" in out