r"""Configurazione del log su file e log_exception.

Il log e' su file in %APPDATA%\\KimaiClient\\kimai.log, con
RotatingFileHandler per evitare file infiniti (l'app resta
aperta potenzialmente per un'intera giornata).

setup_logging e' idempotente: una seconda chiamata non duplica
l'handler e quindi non raddoppia le righe di ogni messaggio.

log_exception scrive il dettaglio tecnico completo (con stack trace)
sul file di log e RESTITUISCE il messaggio breve italiano da
mostrare a schermo. La separazione dei due canali e' il motivo
per cui il modulo esiste: nessun gestore di errore puo'
dimenticare di usare log_exception.

Il token non compare MAI nel log: se l'exception chain contiene
un HTTPError con l'URL completo (che include il token), le
campi __cause__ e __context__ vengono azzerati prima del log.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union


def default_log_path() -> Path:
    """Percorso standard del file di log.

    Restituisce %APPDATA%\\KimaiClient\\kimai.log.
    """
    return Path(os.environ["APPDATA"]) / "KimaiClient" / "kimai.log"


def setup_logging(path: Union[Path, str, None] = None) -> logging.Logger:
    """Configura un RotatingFileHandler sul logger `kimai`.

    E' idempotente: se il logger ha gia' un RotatingFileHandler,
    non lo aggiunge di nuovo. Senza questo controllo ogni chiamata
    successiva (es. restart dell'app) duplicherebbe le righe.

    Args:
        path: Percorso del file. Se None, usa default_log_path().

    Returns:
        Il logger `kimai` con l'handler configurato.
    """
    if path is None:
        path = default_log_path()
    else:
        path = Path(path)

    logger = logging.getLogger("kimai")

    # Controllo idempotenza: evita di aggiungere handler duplicati
    # per lo STESSO path. Un logger "kimai" condiviso tra più
    # percorsi (es. test diversi) deve avere un handler per ognuno.
    if any(
        isinstance(h, RotatingFileHandler)
        and h.baseFilename == str(path)
        for h in logger.handlers
    ):
        return logger

    handler = RotatingFileHandler(
        str(path),
        maxBytes=512 * 1024,  # 512 KB
        backupCount=3,
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger


def log_exception(logger: logging.Logger, exc: Exception, context: str) -> str:
    """Registra un'eccezione con lo stack trace completo sul log.

    Prima di registrare, azzera la catena delle eccezioni (cause,
    context) per impedire che il token finisca nel file di log.
    Restituisce la stringa dell'eccezione (messaggio breve italiano)
    pronta per essere mostrata all'utente.

    Args:
        logger: Il logger kimai configurato da setup_logging().
        exc: L'eccezione da registrare.
        context: Contesto breve (es. "start_timesheet").

    Returns:
        str(exc): messaggio breve, senza stack trace.
    """
    # Rimuove la catena delle eccezioni perche' un HTTPError
    # sottostante potrebbe contenere l'URL completo con il token.
    # logger.exception() con exc_info=True stampa la catena
    # intera; azzerandola restiamo solo con str(exc).
    exc.__cause__ = None
    exc.__context__ = None

    # logger.exception() usa sys.exc_info() (vuoto se non siamo
    # dentro un except). Passiamo l'eccezione esplicitamente per
    # funzionare anche nei test e in qualsiasi contesto.
    logger.exception(context, exc_info=(type(exc), exc, exc.__traceback__))

    # Flush immediato: assicura che il file sia scritto su disco
    # prima che il chiamante lo legga (necessario per i test che
    # leggono il file subito dopo log_exception, e in produzione
    # per un'app che viene chiusa senza chiudere esplicitamente il logger).
    for h in logger.handlers:
        h.flush()
        # Su Windows flush() non sempre forza lo sync: forziamo esplicitamente.
        try:
            os.fsync(h.stream.fileno())
        except (OSError, AttributeError, ValueError):
            pass

    return str(exc)
