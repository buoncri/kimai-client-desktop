"""Test dei modelli di dominio.

Verificano che i modelli siano immutabili e che l'attributo `display`
sia il modo unico con cui la UI legge un'etichetta da mostrare.
"""

import dataclasses

import pytest

from kemai_client.models import Activity, Customer, Project


class TestCustomer:
    def test_display_is_the_name(self):
        assert Customer(1, "Acme").display == "Acme"

    def test_equality_on_same_id_and_name(self):
        # frozen=True genera __eq__: due istanze equivalenti sono uguali,
        # cosa che serve al controller per non duplicare voci nei Combobox.
        assert Customer(1, "Acme") == Customer(1, "Acme")

    def test_inequality_on_different_id(self):
        assert Customer(1, "Acme") != Customer(2, "Acme")

    def test_is_hashable(self):
        # I modelli finiscono in set e dizionari di deduplicazione: devono
        # essere hashabili, il che richiede frozen=True e hash generato.
        assert len({Customer(1, "Acme"), Customer(1, "Acme")}) == 1

    def test_cannot_be_mutated(self):
        customer = Customer(1, "Acme")
        with pytest.raises(dataclasses.FrozenInstanceError):
            customer.name = "Altro"


class TestProject:
    def test_display_is_the_name(self):
        assert Project(9, "Sito web", 1).display == "Sito web"

    def test_keeps_parent_customer_id(self):
        assert Project(9, "Sito web", 1).customer_id == 1

    def test_cannot_be_mutated(self):
        project = Project(9, "Sito web", 1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            project.customer_id = 2


class TestActivity:
    def test_display_is_the_name(self):
        assert Activity(3, "Analisi", 9).display == "Analisi"

    def test_project_id_is_optional(self):
        # Non tutte le istanze Kimai espongono il progetto padre sull'attivita,
        # quindi il campo deve poter mancare senza rompere il parsing.
        assert Activity(3, "Analisi").project_id is None

    def test_cannot_be_mutated(self):
        activity = Activity(3, "Analisi", 9)
        with pytest.raises(dataclasses.FrozenInstanceError):
            activity.name = "Altro"
