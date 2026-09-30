"""Errori del client Kimai.

Una sola regola che vale per tutti: i messaggi di queste eccezioni finiscono
a schermo, quindi devono essere in italiano e comprensibili da chi non sa cosa
e' un API. Nessuno puo' contenere il token o un header di autenticazione.
Lo status HTTP resta disponibile per il log, ma non viene stampato all'utente.
"""

from __future__ import annotations


class KimaiError(Exception):
    """Errore generico comunicabile all'utente."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status

    def __str__(self) -> str:
        return self.message


class KimaiAuthError(KimaiError):
    """Credenziali rifiutate: token assente, errato, revocato o scaduto."""


class KimaiNetworkError(KimaiError):
    """Il server non e' raggiungibile, o ha risposto troppo lentamente."""


class KimaiNotFoundError(KimaiError):
    """La risorsa richiesta non esiste (HTTP 404)."""
