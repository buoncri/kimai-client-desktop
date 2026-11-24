r"""Persistenza della configurazione su disco.

Il file di configurazione vive in %APPDATA%\\KimaiClient\\config.json,
fuori dall'albero del repository. A runtime si usa `default_path()`;
nei test si passa sempre un percorso sotto `tmp_path`.

La scrittura e' atomica: si scrive su un file .tmp nella stessa directory
e si rinomina con `os.replace()`, che e' atomico su Windows e su POSIX.
Non e' possibile trovarsi con un file a meta'.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Configurazione dell'applicazione.

    I campi host, username e token sono le credenziali dell'istanza Kimai.
    Il token e' salvato in chiaro: e' una scelta deliberata (il file e'
    sotto %APPDATA%, non tracciato da git), perche' l'alternativa su
    Windows (DPAPI) aggiungerebbe una dipendenza esterna.

    `last_customer_id` e `last_project_id` ricordano l'ultima selezione
    dell'utente, cosi' al prossimo avvio la UI non ricomincia da zero.
    """

    host: str = ""
    username: str = ""
    token: str = ""
    close_to_tray: bool = False
    last_customer_id: int | None = None
    last_project_id: int | None = None
    # Verifica del certificato TLS del server. True di default: disattivarla
    # e' la scelta esplicita per un server interno con certificato non fidato.
    verify_tls: bool = True


def default_path() -> Path:
    """Percorso standard della configurazione.

    Restituisce %APPDATA%\\KimaiClient\\config.json.
    """
    return Path(os.environ.get("APPDATA") or Path.home()) / "KimaiClient" / "config.json"


def _coerce_field(name: str, value: Any, type_hint, default_value: Any) -> tuple[str, Any]:
    """Converte un singolo valore di campo nel tipo atteso.

    Restituisce (nome_campo, valore_convertito). Se la conversione fallisce
    (tipo non compatibile o None su un campo non nullabile), viene restituito
    *default_value*.

    I campi nullabili (es. int | None) accettano None come valore valido.

    Questo evita che una Config() sollevi TypeError quando il JSON salvato
    ha un tipo di valore non compatibile (es. una stringa dove si aspetta un
    intero).
    """
    # Per i campi nullabili (int | None), None e' valido → mantenilo.
    # Un campo e' nullabile quando il suo default e' None (es. last_customer_id: int | None = None).
    if value is None and default_value is None:
        return (name, None)

    if value is None:
        return (name, default_value)

    if type_hint == str:
        if isinstance(value, str):
            return (name, value)
        return (name, default_value)

    if type_hint == bool:
        if isinstance(value, bool):
            return (name, value)
        return (name, default_value)

    if type_hint == int:
        if isinstance(value, int) and not isinstance(value, bool):
            return (name, value)
        return (name, default_value)

    return (name, default_value)


def _load_from_dict(data: dict) -> Config:
    """Costruisce una Config da un dizionario, convertendo ogni campo nel
    tipo atteso.

    I campi di tipo non compatibile rientrano silenziosamente nel valore
    di default del dataclass, così l'app non si blocca su una config corrotta.
    """
    fields: dict[str, tuple[type, Any]] = {
        "host": (str, ""),
        "username": (str, ""),
        "token": (str, ""),
        "close_to_tray": (bool, False),
        "last_customer_id": (int, None),
        "last_project_id": (int, None),
        "verify_tls": (bool, True),
    }

    result: dict[str, Any] = {}
    for k, v in data.items():
        if k not in fields:
            continue
        type_hint, default = fields[k]
        name, coerced = _coerce_field(k, v, type_hint, default)
        result[name] = coerced

    return Config(**result)


def load(path: Path | str | None = None) -> Config:
    """Legge la configurazione da disco.

    Se il file non esiste o il suo contenuto non e' JSON valido,
    restituisce un Config() con tutti i default, senza sollevare
    eccezioni: l'app non deve mai crashare per un file corrotto.

    I campi sconosciuti presenti nel JSON vengono ignorati,
    perche' una configurazione scritta da una versione futura
    non deve rompere una versione precedente.

    Se un valore e' di tipo incompatibile (es. una stringa dove si
    aspetta un intero), il valore viene ignorato e usato il default
    della dataclass.

    Argomenti:
        path: Percorso del file. Se None, usa default_path().
    """
    if path is None:
        path = default_path()
    else:
        path = Path(path)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        # File mancante, permission denied o JSON malformato:
        # torniamo un Config di default.
        return Config()

    # JSON valido ma non un oggetto (lista, stringa, numero, booleano, null)
    # restituiamo un Config() con tutti i default.
    if not isinstance(data, dict):
        return Config()

    # Costruiamo il Config dai dati del file. I campi non presenti
    # nel dizionario usano i default della dataclass.
    return _load_from_dict(data)


def save(config: Config, path: Path | str | None = None) -> None:
    """Scrive la configurazione su disco in modo atomico.

    Scrive su <path>.tmp nella stessa directory, poi rinomina
    il file con os.replace(). In questo modo non e' mai visibile
    un file a meta' della scrittura.

    Se la directory di destinazione non esiste, la crea con makedirs.

    Argomenti:
        config: La configurazione da salvare.
        path: Percorso del file. Se None, usa default_path().
    """
    if path is None:
        path = default_path()
    else:
        path = Path(path)

    # Crea la directory padre se non esiste.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Scrive su un file temporaneo.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, ensure_ascii=False, indent=2)

    # Rinomina atomico: dopo questo punto il file definitivo e' visibile.
    os.replace(tmp_path, path)


def is_configured(config: Config) -> bool:
    """Verifica se la configurazione e' completa.

    E' True solo se host, username e token sono tutti non vuoti.
    Una configurazione con il token vuoto non e' considerata pronta,
    perche' significa che l'utente non ha ancora inserito le credenziali.
    """
    return bool(config.host and config.username and config.token)
