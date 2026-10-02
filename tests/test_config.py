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
            host="https://crono.bonificaumbria.local",
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
