r"""Test della configurazione persistente.

Tutti i test scrivono in tmp_path, mai nella %APPDATA% reale.
La configurazione vive in %APPDATA%\\KimaiClient\\config.json a runtime,
ma i test la simulano su un percorso temporaneo.
"""

import json
import os
from pathlib import Path

import pytest

from kemai_client.config import (
    Config,
    default_path,
    is_configured,
    load,
    save,
)


class TestDefaultPath:
    def test_default_path_under_appdata(self):
        # Il file di configurazione sta fuori dall'albero del repository.
        # Verifica che il percorso finale sia esattamente quello previsto.
        path = default_path()
        parts = path.parts
        assert "KimaiClient" in parts
        assert parts[-1] == "config.json"
        # Assicuriamoci che termini con KimaiClient/config.json
        assert path.name == "config.json"
        # La directory padre deve essere KimaiClient
        assert path.parent.name == "KimaiClient"


class TestSaveLoadRoundtrip:
    def test_save_load_roundtrip(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(
            host="https://crono.bonificaumbra.local",
            username="luca",
            token="test-token-not-real",
            close_to_tray=True,
            last_customer_id=42,
            last_project_id=7,
        )
        save(cfg, path)
        loaded = load(path)
        assert loaded == cfg


class TestLoadMissingFile:
    def test_load_missing_file(self, tmp_path):
        # Su un percorso inesistente deve restituire un Config di default,
        # senza sollevare eccezioni.
        cfg = load(tmp_path / "non_esiste.json")
        assert cfg.host == ""
        assert cfg.username == ""
        assert cfg.token == ""
        assert cfg.close_to_tray is False
        assert cfg.last_customer_id is None
        assert cfg.last_project_id is None


class TestLoadCorruptFile:
    def test_load_corrupt_file(self, tmp_path):
        # Su JSON malformato deve restituire il default, senza sollevare eccezioni.
        path = tmp_path / "corrotto.json"
        path.write_text("{ questo non e' json valido }")
        cfg = load(path)
        assert cfg == Config()


class TestSaveIsAtomic:
    def test_save_is_atomic(self, tmp_path):
        """Durante il salvataggio non esiste mai config.json incompleto."""
        path = tmp_path / "config.json"
        cfg = Config(
            host="https://host",
            username="user",
            token="tok",
        )
        # Prima di salvare, il file non deve esistere.
        assert not path.exists()
        save(cfg, path)
        # Dopo il salvataggio, il file definitivo esiste.
        assert path.exists()
        # Non deve esserci alcun file temporaneo residuo.
        for child in tmp_path.iterdir():
            assert child.suffix != ".tmp"
        # Il contenuto e' il JSON valido.
        with open(path) as f:
            data = json.load(f)
        assert data["host"] == "https://host"


class TestSaveCreatesParents:
    def test_save_creates_parents(self, tmp_path):
        # Se la directory KimaiClient manca, save deve crearla.
        path = tmp_path / "KimaiClient" / "config.json"
        cfg = Config(host="https://host", username="u", token="t")
        save(cfg, path)
        # La directory deve esistere.
        assert path.parent.exists()
        # E deve esserci config.json.
        assert path.exists()


class TestIsConfigured:
    def test_not_configured_when_token_missing(self):
        cfg = Config(host="https://host", username="luca")
        assert not is_configured(cfg)

    def test_not_configured_when_host_missing(self):
        cfg = Config(username="luca", token="tok")
        assert not is_configured(cfg)

    def test_configured_only_with_all_three(self):
        cfg = Config(
            host="https://host",
            username="luca",
            token="tok",
        )
        assert is_configured(cfg)


class TestVerifyTls:
    def test_default_is_verify_enabled(self):
        # La verifica del certificato e' attiva di default: disattivarla
        # deve restare una scelta esplicita dell'utente, mai un silenzio.
        assert Config().verify_tls is True

    def test_roundtrip_persists_verify_tls(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(
            host="https://host",
            username="u",
            token="t",
            verify_tls=False,
        )
        save(cfg, path)
        assert load(path).verify_tls is False

    def test_old_config_without_key_verifies_tls(self, tmp_path):
        # Un config.json scritto prima dell'opzione non contiene la chiave:
        # la verifica resta attiva, mai disattivata per omissione.
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "https://host", "username": "u", "token": "t"}))
        assert load(path).verify_tls is True
  
class TestDefaultPathWithoutAppdata:  
  
    def test_default_path_without_appdata(self, monkeypatch):  
        monkeypatch.delenv("APPDATA", raising=False)  
        from kemai_client.config import default_path  
        p = default_path()  
        assert p.name == "config.json"  
        assert p.parent.name == "KimaiClient"


class TestLoadNonObject:
    """JSON valido ma non-dizionario deve restituire Config() di default."""

    def test_load_json_list(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text(json.dumps([1, 2, 3]))
        cfg = load(path)
        assert cfg == Config()

    def test_load_json_string(self, tmp_path):
        path = tmp_path / "string.json"
        path.write_text(json.dumps("hello"))
        cfg = load(path)
        assert cfg == Config()

    def test_load_json_number(self, tmp_path):
        path = tmp_path / "number.json"
        path.write_text(json.dumps(42))
        cfg = load(path)
        assert cfg == Config()

    def test_load_json_bool(self, tmp_path):
        path = tmp_path / "bool.json"
        path.write_text(json.dumps(True))
        cfg = load(path)
        assert cfg == Config()

    def test_load_json_null(self, tmp_path):
        path = tmp_path / "null.json"
        path.write_text(json.dumps(None))
        cfg = load(path)
        assert cfg == Config()


class TestLoadTypeMismatch:
    """Campi con tipo incompatibile usano il default, senza crash."""

    def test_host_string_instead_of_int(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": 123, "username": "u", "token": "t"}))
        cfg = load(path)
        assert cfg.host == ""  # default
        assert cfg.username == "u"
        assert cfg.token == "t"

    def test_last_customer_id_string_instead_of_int(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "last_customer_id": "42"}))
        cfg = load(path)
        assert cfg.last_customer_id is None  # default

    def test_verify_tls_number_instead_of_bool(self, tmp_path):
        # 1 è int, non bool: il default per verify_tls è True.
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "verify_tls": 1}))
        cfg = load(path)
        assert cfg.verify_tls is True

    def test_close_to_tray_string_instead_of_bool(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "close_to_tray": "yes"}))
        cfg = load(path)
        assert cfg.close_to_tray is False

    def test_host_none_uses_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": None, "username": "u", "token": "t"}))
        cfg = load(path)
        assert cfg.host == ""  # default

    def test_username_none_uses_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": None, "token": "t"}))
        cfg = load(path)
        assert cfg.username == ""  # default

    def test_token_none_uses_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": None}))
        cfg = load(path)
        assert cfg.token == ""  # default

    def test_verify_tls_none_uses_default(self, tmp_path):
        # None su un campo bool: per verify_tls il default è True.
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "verify_tls": None}))
        cfg = load(path)
        assert cfg.verify_tls is True

    def test_close_to_tray_none_uses_default(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "close_to_tray": None}))
        cfg = load(path)
        assert cfg.close_to_tray is False

    def test_last_customer_id_none_is_valid(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "last_customer_id": None}))
        cfg = load(path)
        assert cfg.last_customer_id is None

    def test_unknown_fields_ignored(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "h", "username": "u", "token": "t", "future_field": 999}))
        cfg = load(path)
        assert cfg.host == "h"
        assert cfg.username == "u"
        assert cfg.token == "t"
        assert cfg.last_customer_id is None

    def test_valid_roundtrip_still_works(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(
            host="https://host",
            username="u",
            token="t",
            close_to_tray=True,
            last_customer_id=42,
            last_project_id=7,
            verify_tls=False,
        )
        save(cfg, path)
        assert load(path) == cfg

    def test_roundtrip_persists_verify_tls(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(
            host="https://host",
            username="u",
            token="t",
            verify_tls=False,
        )
        save(cfg, path)
        assert load(path).verify_tls is False

    def test_old_config_without_key_verifies_tls(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"host": "https://host", "username": "u", "token": "t"}))
        assert load(path).verify_tls is True
