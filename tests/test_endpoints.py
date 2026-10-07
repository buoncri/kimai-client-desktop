"""Test degli endpoint.

Questi test hanno un motivo preciso: nessuno degli endpoint Kimai 1.15 e' mai
stato verificato, perche' il server e' in una rete interna non raggiungibile
dalla macchina di sviluppo. Gli endpoint sono quindi ipotesi centralizzate in
un solo file, e questi test garantiscono che quel file resti l'unico posto da
correggere quando il probing (tools/probe_api.py) rivelera un percorso diverso.
"""

from kemai_client.api import endpoints


class TestPaths:
    def test_base_path(self):
        assert endpoints.BASE_PATH == "/api"

    def test_every_path_is_built_from_base_path(self):
        # Se un path fosse scritto a mano "/api/customers", la correzione
        # post-probing su BASE_PATH non lo toccherebbe. Questo test fallisce
        # in quel caso, ed e' esattamente lo scenario che vogliamo impedire.
        for name in (
            "VERSIONS",
            "CUSTOMERS",
            "PROJECTS",
            "ACTIVITIES",
            "TIMESHEETS",
            "TIMESHEET_START",
            "TIMESHEET_STOP",
        ):
            path = getattr(endpoints, name)
            assert isinstance(path, str), f"{name} non e' una stringa"
            assert path.startswith(endpoints.BASE_PATH), (
                f"{name} = {path!r} non deriva da BASE_PATH"
            )

    def test_join_produces_expected_path(self):
        assert f"{endpoints.BASE_PATH}/customers" == "/api/customers"

    def test_no_path_has_a_trailing_slash(self):
        # Una barra finale produce 404 silenzioso su alcuni router.
        for name in ("VERSIONS", "CUSTOMERS", "PROJECTS", "ACTIVITIES", "TIMESHEETS"):
            assert not getattr(endpoints, name).endswith("/"), name


class TestFilterParamNames:
    def test_param_customer_is_non_empty(self):
        # Anche i nomi dei parametri di query sono ipotesi sul Kimai 1.15
        # reale, quindi vivono in endpoints.py con i path.
        assert isinstance(endpoints.PARAM_CUSTOMER, str)
        assert endpoints.PARAM_CUSTOMER.strip()

    def test_param_project_is_non_empty(self):
        assert isinstance(endpoints.PARAM_PROJECT, str)
        assert endpoints.PARAM_PROJECT.strip()

    def test_params_are_distinct(self):
        assert endpoints.PARAM_CUSTOMER != endpoints.PARAM_PROJECT


class TestPagingParams:
    def test_default_page_size_is_a_positive_int(self):
        # Un valore a zero o negativo produrrebbe una richiesta priva di
        # elementi e un elenco sempre vuoto, senza alcun errore visibile.
        assert isinstance(endpoints.DEFAULT_PAGE_SIZE, int)
        assert endpoints.DEFAULT_PAGE_SIZE > 0
