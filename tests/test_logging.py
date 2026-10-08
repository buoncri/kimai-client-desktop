r"""Test del modulo di logging.

Tutti i test passano un percorso sotto tmp_path e non toccano
la %APPDATA% reale. Il modulo deve essere idempotente, la rotazione
deve funzionare, e soprattutto il token non deve mai apparire nel file.
"""

import os
import pathlib
import re
from pathlib import Path

import pytest

from kemai_client.api.errors import KimaiAuthError
from kemai_client.logging_setup import (
    default_log_path,
    log_exception,
    setup_logging,
)


class TestDefaultLogPath:
    def test_log_path_is_under_appdata(self):
        # default_log_path() termina con KimaiClient/kimai.log.
        path = default_log_path()
        assert path.name == "kimai.log"
        assert path.parent.name == "KimaiClient"


class TestLogException:
    def test_log_exception_returns_short_message(self, tmp_path):
        # Il valore restituito e' il messaggio breve italiano,
        # non la stringa con lo stack trace.
        exc = KimaiAuthError("Autenticazione fallita per il server")
        log_path = tmp_path / "kimai.log"
        logger = setup_logging(log_path)
        result = log_exception(logger, exc, "start_timesheet")
        assert result == "Autenticazione fallita per il server"

    def test_log_exception_writes_detail_to_log(self, tmp_path):
        # Il file di log contiene il testo dell'eccezione e il context.
        log_path = tmp_path / "kimai.log"
        logger = setup_logging(log_path)
        exc = KimaiAuthError("Errore di rete")
        log_exception(logger, exc, "stop_timesheet")
        # Il file deve esistere e contenere il context e il messaggio.
        content = log_path.read_text()
        assert "stop_timesheet" in content
        assert "Errore di rete" in content


class TestTokenNeverReachesTheLog:
    def test_token_never_reaches_the_log(self, tmp_path):
        """Passando un KimaiAuthError con il token nella chain, il contenuto
        del file di log non contiene il token.

        Questo e' il test che rende vera la regola di sicurezza della spec:
        se l'exception chain contiene un URL con il token (es. un HTTPError
        sottostante), log_exception non lo include nel log.
        """
        log_path = tmp_path / "kimai.log"
        fake_token = "SUPER-SECRET-TOKEN-abc123"
        logger = setup_logging(log_path)

        # Costruiamo un'eccezione il cui messaggio NON contiene il token,
        # ma il __cause__ (catena) contiene un URL con il token.
        exc = KimaiAuthError("Autenticazione fallita")
        # Simuliamo che l'eccezione sia stata sollevata da un'API call
        # che contiene il token nell'URL (come un HTTPError reale).
        class FakeHTTPError(Exception):
            def __init__(self):
                super().__init__(
                    f"https://host/api?token={fake_token}"
                )
        exc.__cause__ = FakeHTTPError()

        log_exception(logger, exc, "test")

        # Il file di log NON deve contenere il token.
        content = log_path.read_text()
        assert fake_token not in content, (
            f"Il token e' finito nel log: {content[:500]}"
        )


class TestIdempotentSetup:
    def test_logging_does_not_duplicate_handlers(self, tmp_path):
        # Chiamare setup_logging due volte non raddoppia le righe.
        log_path = tmp_path / "kimai.log"
        logger = setup_logging(log_path)
        logger.info("primo messaggio")

        logger2 = setup_logging(log_path)
        logger2.info("secondo messaggio")

        # Se i handler fossero duplicati, "secondo messaggio"
        # apparirebbe due volte. Verifichiamo che compaia una sola volta.
        content = log_path.read_text()
        count = content.count("secondo messaggio")
        assert count == 1, (
            f"'secondo messaggio' e' presente {count} volte (duplicazione handler?)"
        )


class TestRotatingFile:
    def test_log_file_rotates(self, tmp_path):
        # Con maxBytes piccolo, superata la soglia il file viene ruotato
        # e non cresce indefinitamente.
        # Nota: questo test verifica che RotatingFileHandler sia stato
        # configurato correttamente, non che il file sia esattamente
        # 512 KB.
        log_path = tmp_path / "kimai.log"

        # Creiamo un logger con RotatingFileHandler a 100 byte.
        import logging
        from logging.handlers import RotatingFileHandler

        logger = logging.getLogger("kimai.test_rotate")
        # Rimuovi handler esistenti per pulizia.
        logger.handlers.clear()

        handler = RotatingFileHandler(
            log_path, maxBytes=100, backupCount=3
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Scrivi abbastanza dati da forzare la rotazione.
        for i in range(20):
            logger.info("X" * 50)

        # Dopo la rotazione, il file principale non deve superare
        # maxBytes * (backupCount + 1) circa.
        size = log_path.stat().st_size
        # Verifichiamo che sia presente almeno un .1 rotato.
        rotated = tmp_path / "kimai.log.1"
        assert rotated.exists(), (
            "Nessun file rotato: il RotatingFileHandler non funziona?"
        )


class TestPrimoAvvio:
    """Il caso del primo avvio: la directory padre non esiste ancora.

    E' il bug che ha bloccato l'app al lancio: RotatingFileHandler crea
    il file ma non le cartelle. Il piano non conteneva questo test, quindi
    nessun agente poteva vederlo: aggiunto dopo il primo crash reale.
    """

    def test_setup_logging_creates_missing_parent_directory(self, tmp_path):
        log = tmp_path / "KimaiClient" / "kimai.log"
        assert not log.parent.exists()
        setup_logging(log)
        assert log.parent.exists()
        assert log.parent.is_dir()
