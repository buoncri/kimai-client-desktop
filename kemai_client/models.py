"""Modelli di dominio.

Sono deliberatamente minimi: un identificativo, un nome, e il legame con il
padre quando serve. Tutto il resto che Kimai potrebbe aggiungere nelle sue
risposte viene ignorato in fase di parsing, perche' un campo in piu' sul server
non deve mai rompere il client.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    """Un cliente di Kimai, il nodo piu' in alto della cascata."""

    id: int
    name: str

    @property
    def display(self) -> str:
        """Testo da mostrare nei Combobox.

        La UI non legge mai `name` direttamente: passa da `display`, cosi'
        un eventuale cambio di formato dell'etichetta resta confinato qui.
        """
        return self.name


@dataclass(frozen=True)
class Project:
    """Un progetto, che appartiene a un cliente."""

    id: int
    name: str
    customer_id: int

    @property
    def display(self) -> str:
        return self.name


@dataclass(frozen=True)
class Activity:
    """Un'attivita', che puo' appartenere a un progetto.

    `project_id` e' opzionale perche' non tutte le versioni di Kimai
    espongono il legame con il progetto direttamente sull'attivita': quando
    manca, il filtro per progetto avviene lato server.
    """

    id: int
    name: str
    project_id: int | None = None

    @property
    def display(self) -> str:
        return self.name
