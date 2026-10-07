"""Test del KimaiClient.

Regola assoluta di questo file: nessun test apre un socket. Il `FakeTransport`
sostituisce la sessione `requests` e registra le chiamate, cosi' possiamo
verificare URL, header e payload senza toccare la rete.

Il token qui e' una costante fittizia dichiarata nel piano come unico valore
ammesso: nessun token reale deve mai entrare in questo file.
"""

import pytest

from kemai_client.api import endpoints
from kemai_client.api.client import KimaiClient
from kemai_client.api.errors import (
    KimaiAuthError,
    KimaiError,
    KimaiNetworkError,
    KimaiNotFoundError,
)
from kemai_client.models import Activity, Customer, Project

TEST_TOKEN = "test-token-not-real"
TEST_USER = "test-user"
TEST_HOST = "https://host.example"


class FakeResponse:
    """Risposta minima con la stessa interfaccia di quella di requests."""

    def __init__(self, status_code=200, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}
        self.text = text

    def json(self):
        if self._json is None:
            # Mima requests: solleva quando il corpo non e' JSON decodificabile.
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._json


class FakeTransport:
    """Trasporto finto: restituisce risposte preparate e registra le chiamate."""

    def __init__(self, response):
        # Un valore singolo viene riutilizzato; una lista e' consumata in ordine.
        self._single = response if not isinstance(response, list) else None
        self._queue = list(response) if isinstance(response, list) else None
        self.calls = []

    def request(self, method, url, *, headers, params=None, json=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        response = self._single if self._single is not None else self._queue.pop(0)
        # Se riceviamo un'eccezione la solleviamo, come fa requests. Restituirla
        # sarebbe un falso: il client non ha nulla in un try/except che la copra.
        if isinstance(response, BaseException):
            raise response
        return response

    @property
    def last(self):
        return self.calls[-1]


def make_client(response):
    transport = FakeTransport(response)
    client = KimaiClient(TEST_HOST, TEST_USER, TEST_TOKEN, transport=transport)
    return client, transport


# --- Autenticazione --------------------------------------------------------


class TestAuth:
    def test_headers_auth(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        headers = transport.last["headers"]
        assert headers["X-AUTH-USER"] == TEST_USER
        assert headers["X-AUTH-TOKEN"] == TEST_TOKEN

    def test_accepts_json(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        assert "json" in transport.last["headers"]["Accept"]

    def test_authorization_header_never_carries_the_token_in_a_url(self):
        # Il token viaggia solo in header: finirebbe nella cronologia del
        # server e in ogni log di accesso se finisse nell'URL.
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        assert TEST_TOKEN not in transport.last["url"]


# --- URL e parametri -------------------------------------------------------


class TestUrls:
    def test_customers_url(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        assert transport.last["url"] == f"{TEST_HOST}/api/customers"

    def test_projects_filtered(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_projects(7)
        assert transport.last["url"] == f"{TEST_HOST}/api/projects"
        params = transport.last["params"]
        assert params[endpoints.PARAM_CUSTOMER] == 7
        assert params[endpoints.PARAM_SIZE] == endpoints.DEFAULT_PAGE_SIZE

    def test_activities_filtered(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_activities(9)
        assert transport.last["url"] == f"{TEST_HOST}/api/activities"
        params = transport.last["params"]
        assert params[endpoints.PARAM_PROJECT] == 9
        assert params[endpoints.PARAM_SIZE] == endpoints.DEFAULT_PAGE_SIZE

    def test_start_hits_the_start_path(self):
        client, transport = make_client(FakeResponse(json_data={"id": 1}))
        client.start_timesheet(9, 3)
        assert transport.last["url"] == f"{TEST_HOST}{endpoints.TIMESHEET_START}"

    def test_stop_hits_the_stop_path(self):
        client, transport = make_client(FakeResponse(json_data={}))
        client.stop_timesheet(42)
        assert transport.last["url"] == f"{TEST_HOST}{endpoints.TIMESHEET_STOP}"


# --- Parsing ---------------------------------------------------------------


class TestParsing:
    def test_parses_lowercase_ids(self):
        client, _ = make_client(FakeResponse(json_data=[{"id": 1, "name": "Acme"}]))
        assert client.list_customers() == [Customer(1, "Acme")]

    def test_parses_uppercase_ids(self):
        # Kimai 1.x e' Symfony-based e in alcuni casi serializza con "ID".
        client, _ = make_client(FakeResponse(json_data=[{"ID": 1, "name": "Acme"}]))
        assert client.list_customers() == [Customer(1, "Acme")]

    def test_parses_list_payload(self):
        client, _ = make_client(FakeResponse(json_data={"customers": [{"id": 1, "name": "Acme"}]}))
        assert client.list_customers() == [Customer(1, "Acme")]

    def test_parses_empty_list(self):
        client, _ = make_client(FakeResponse(json_data=[]))
        assert client.list_customers() == []

    def test_ignores_unknown_fields(self):
        # Un campo in piu' dal server non deve mai far fallire il parsing.
        client, _ = make_client(
            FakeResponse(json_data=[{"id": 1, "name": "Acme", "nuovoCampo": {"a": 1}}])
        )
        assert client.list_customers() == [Customer(1, "Acme")]

    def test_projects_carry_customer_id_from_filter(self):
        client, _ = make_client(FakeResponse(json_data=[{"id": 9, "name": "Sito web"}]))
        assert client.list_projects(7) == [Project(9, "Sito web", 7)]

    def test_activities_carry_project_id_from_filter(self):
        client, _ = make_client(FakeResponse(json_data=[{"id": 3, "name": "Analisi"}]))
        assert client.list_activities(9) == [Activity(3, "Analisi", 9)]

    def test_start_returns_id(self):
        client, _ = make_client(FakeResponse(json_data={"id": 42}))
        assert client.start_timesheet(9, 3) == 42

    def test_start_sends_project_and_activity(self):
        client, transport = make_client(FakeResponse(json_data={"id": 42}))
        client.start_timesheet(9, 3)
        payload = transport.last["json"]
        assert payload["project"] == 9
        assert payload["activity"] == 3

    def test_create_project_sends_name_and_customer(self):
        client, transport = make_client(FakeResponse(json_data={"id": 5, "name": "Nuovo"}))
        project = client.create_project("Nuovo", 1)
        assert project == Project(5, "Nuovo", 1)
        assert transport.last["json"] == {"name": "Nuovo", "customer": 1}

    def test_get_version_reads_the_version(self):
        client, _ = make_client(FakeResponse(json_data={"version": "1.15"}))
        assert client.get_version() == "1.15"


# --- Errori: Review Focus 1 e 4 -------------------------------------------


class TestErrors:
    def test_auth_error_on_401(self):
        client, _ = make_client(FakeResponse(status_code=401, json_data={}))
        with pytest.raises(KimaiAuthError) as exc:
            client.list_customers()
        assert exc.value.status == 401

    def test_auth_error_on_403(self):
        client, _ = make_client(FakeResponse(status_code=403, json_data={}))
        with pytest.raises(KimaiAuthError):
            client.list_customers()

    def test_not_found_on_404(self):
        client, _ = make_client(FakeResponse(status_code=404, json_data={}))
        with pytest.raises(KimaiNotFoundError):
            client.list_customers()

    def test_generic_error_on_500(self):
        client, _ = make_client(FakeResponse(status_code=500, json_data={}))
        with pytest.raises(KimaiError) as exc:
            client.list_customers()
        assert not isinstance(exc.value, (KimaiAuthError, KimaiNotFoundError))
        assert exc.value.status == 500

    def test_server_message_is_preferred_when_present(self):
        client, _ = make_client(
            FakeResponse(status_code=400, json_data={"message": "Customer not found"})
        )
        with pytest.raises(KimaiError) as exc:
            client.list_customers()
        assert "Customer not found" in str(exc.value)

    def test_network_error_wraps(self):
        client, _ = make_client(OSError("connessione rifiutata"))
        with pytest.raises(KimaiNetworkError):
            client.list_customers()

    def test_network_error_is_not_an_oserror(self):
        # Se trapenasse OSError, la UI non potrebbe distinguerlo da un bug.
        client, _ = make_client(OSError("timeout"))
        with pytest.raises(KimaiError):
            client.list_customers()

    def test_html_response_becomes_kimai_error(self):
        # Review Focus 1: proxy aziendale o pagina di login che rispondono HTML
        # con status 200. Deve diventare un KimaiError, mai un ValueError
        # grezzo dalla chiamata a .json().
        client, _ = make_client(
            FakeResponse(
                status_code=200,
                headers={"Content-Type": "text/html"},
                text="<html><body>Login</body></html>",
            )
        )
        with pytest.raises(KimaiError) as exc:
            client.list_customers()
        assert not isinstance(exc.value, KimaiNetworkError)
        assert "html" in str(exc.value).lower() or "non valida" in str(exc.value).lower()

    def test_undecodable_json_with_json_content_type(self):
        # Content-Type promette JSON ma il corpo non lo e': stessa protezione.
        client, _ = make_client(
            FakeResponse(status_code=200, headers={"Content-Type": "application/json"}, text="nope")
        )
        with pytest.raises(KimaiError):
            client.list_customers()

    def test_invalid_token_message(self):
        # Review Focus 4: il messaggio mostrato all'utente deve essere italiano,
        # non contenere il token e non essere un numero di status grezzo.
        client, _ = make_client(FakeResponse(status_code=401, json_data={}))
        with pytest.raises(KimaiAuthError) as exc:
            client.list_customers()
        message = str(exc.value)
        assert TEST_TOKEN not in message
        assert "401" not in message
        assert any("a" <= c.lower() <= "z" for c in message)

    def test_error_never_exposes_authorization_header(self):
        client, _ = make_client(FakeResponse(status_code=401, json_data={}))
        with pytest.raises(KimaiAuthError) as exc:
            client.list_customers()
        assert "X-AUTH-TOKEN" not in str(exc.value)


# --- Timeout ---------------------------------------------------------------


class TestTimeout:
    def test_timeout_is_passed_to_the_transport(self):
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        assert transport.last["timeout"] == client.timeout

    def test_timeout_is_configurable(self):
        transport = FakeTransport(FakeResponse(json_data=[]))
        client = KimaiClient(TEST_HOST, TEST_USER, TEST_TOKEN, transport=transport, timeout=3.5)
        client.list_customers()
        assert transport.last["timeout"] == 3.5


class TestPaging:
    """Tolleranza alle pagine: PARAM_SIZE esplicito e flag di troncatura."""

    def test_lists_request_explicit_page_size(self):
        # Ogni list_* passa esplicitamente size=DEFAULT_PAGE_SIZE,
        # non si affida al default del server.
        client, transport = make_client(FakeResponse(json_data=[]))
        client.list_customers()
        assert transport.last["params"][endpoints.PARAM_SIZE] == endpoints.DEFAULT_PAGE_SIZE

    def test_exact_page_size_flags_truncation(self):
        # Una risposta con esattamente DEFAULT_PAGE_SIZE elementi
        # deve lasciare last_list_truncated a True.
        payload = [
            {"id": i, "name": f"Cliente_{i}"}
            for i in range(endpoints.DEFAULT_PAGE_SIZE)
        ]
        client, _ = make_client(FakeResponse(json_data=payload))
        client.list_customers()
        assert client.last_list_truncated is True

    def test_short_page_is_not_truncation(self):
        # Meno di DEFAULT_PAGE_SIZE elementi significa "tutto presente": False.
        payload = [
            {"id": i, "name": f"Cliente_{i}"}
            for i in range(endpoints.DEFAULT_PAGE_SIZE - 5)
        ]
        client, _ = make_client(FakeResponse(json_data=payload))
        client.list_customers()
        assert client.last_list_truncated is False

    def test_truncation_flag_resets_between_calls(self):
        # Un elenco troncato seguito da uno completo azzera il flag.
        client, _ = make_client(
            [
                FakeResponse(json_data=[{"id": i, "name": f"C{i}"} for i in range(endpoints.DEFAULT_PAGE_SIZE)]),
                FakeResponse(json_data=[{"id": 1, "name": "Solo"}]),
            ]
        )
        client.list_customers()
        assert client.last_list_truncated is True
        client.list_customers()
        assert client.last_list_truncated is False
