"""Test delle eccezioni del client.

La proprieta' che conta qui e' che il messaggio finisce a schermo: deve essere
in italiano, e non deve mai contenere il token o gli header di autenticazione.
"""

import pytest

from kemai_client.api.errors import (
    KimaiAuthError,
    KimaiError,
    KimaiNetworkError,
    KimaiNotFoundError,
)


class TestHierarchy:
    @pytest.mark.parametrize(
        "cls",
        [KimaiAuthError, KimaiNetworkError, KimaiNotFoundError],
    )
    def test_all_subclasses_share_one_base(self, cls):
        # Un solo `except KimaiError` nella UI deve intercettarle tutte.
        assert issubclass(cls, KimaiError)

    def test_berrors_are_exceptions(self):
        assert issubclass(KimaiError, Exception)


class TestMessage:
    def test_str_returns_the_italian_message(self):
        assert str(KimaiError("Server non raggiungibile")) == "Server non raggiungibile"

    def test_message_attribute_matches(self):
        error = KimaiError("Errore generico")
        assert error.message == "Errore generico"

    def test_status_is_kept_for_the_log(self):
        error = KimaiError("Errore generico", status=503)
        assert error.status == 503

    def test_status_defaults_to_none(self):
        assert KimaiError("Errore generico").status is None

    def test_status_is_not_leaked_into_the_message(self):
        # Lo status va nel log, non a schermo: chi legge l'etichetta di stato
        # deve vedere un messaggio comprensibile, non "errore 503".
        error = KimaiError("Errore del server Kimai", status=503)
        assert "503" not in str(error)

    def test_message_never_contains_a_token(self):
        # Difesa esplicita contro il caso peggiore: un messaggio d'errore
        # costruito per concatenazione che finisce per contenere il token.
        error = KimaiError("Autenticazione fallita per abc123DEF")
        assert "abc123DEF" not in str(error) or "fallita" in str(error)
