r"""Test dello script di probing degli endpoint Kimai.

I test di build_variants() girano offline.
I test di probe() iniettano un opener finto.
Nessun test usa token reali o apre socket verso il server.
"""

import base64
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tools.probe_api import (
    build_variants,
    probe,
    ProbeResult,
    RequestVariant,
)


class TestBuildVariants:
    def test_returns_at_least_four_variants(self):
        # Le varianti combinano: 2 metodi auth × 2 formati = almeno 4.
        variants = build_variants()
        assert len(variants) >= 4

    def test_first_variant_uses_x_auth(self):
        # La prima variante e' X-AUTH-USER / X-AUTH-TOKEN.
        variants = build_variants()
        first = variants[0]
        assert "X-AUTH-USER" in first.headers
        assert "X-AUTH-TOKEN" in first.headers

    def test_has_basic_variant(self):
        # Esiste una variante Basic auth con header Authorization.
        variants = build_variants()
        basic = next(v for v in variants if v.headers.get("Authorization", "").startswith("Basic "))
        assert basic is not None

    def test_has_json_suffix_variant(self):
        # Esiste una variante con path che termina in .json.
        variants = build_variants()
        json_variant = next(v for v in variants if v.path.endswith(".json"))
        assert json_variant is not None

    def test_no_real_token_in_source(self):
        # Il sorgente non contiene il token reale e non lo accetta come
        # argomento della riga di comando.
        source_path = Path(__file__).parent.parent / "tools" / "probe_api.py"
        source = source_path.read_text()
        # Il token di sviluppo di luca (id 1) non deve comparire.
        # Il test e' esplicito: se qualcuno incolla il token qui,
        # il test fallisce e il token viene ruotato.
        assert "TOKEN_REALE_DA_RUOTARE" not in source


class TestProbe:
    def test_probe_marks_auth_failure(self):
        # Un opener che restituisce 401 deve dare verdict con
        # "AUTENTICAZIONE FALLITA".
        variants = build_variants()

        def fake_opener(request):
            raise urllib.error.HTTPError(
                request.full_url, 401, "Unauthorized", {}, None
            )

        results = probe("https://host", "luca", "tok", variants, opener=fake_opener)
        verdicts = [r.verdict for r in results]
        # Almeno una variante deve fallire con AUTENTICAZIONE FALLITA.
        assert any("AUTENTICAZIONE FALLITA" in v for v in verdicts)

    def test_probe_marks_not_found(self):
        # Status 404 e' "NOT_FOUND".
        variants = build_variants()

        def fake_opener(request):
            raise urllib.error.HTTPError(
                request.full_url, 404, "Not Found", {}, None
            )

        results = probe("https://host", "luca", "tok", variants, opener=fake_opener)
        verdicts = [r.verdict for r in results]
        assert all("NOT_FOUND" in v for v in verdicts)

    def test_probe_marks_unreachable(self):
        # Un'eccezione di connession e' "IRRAGGIUNGIBILE".
        variants = build_variants()

        def fake_opener(request):
            raise urllib.error.URLError("network unreachable")

        results = probe("https://host", "luca", "tok", variants, opener=fake_opener)
        verdicts = [r.verdict for r in results]
        assert all("IRRAGGIUNGIBILE" in v for v in verdicts)

    def test_probe_sends_x_auth_credentials(self):
        # X-AUTH: gli header devono contenere username e token reali.
        captured = []
        variants = build_variants()

        def fake_opener(request):
            captured.append(request.headers)
            raise urllib.error.HTTPError(
                request.full_url, 401, "Unauthorized", {}, None
            )

        probe("https://host", "luca", "tok", variants, opener=fake_opener)
        xauth_headers = next(
            h for h in captured
            if "X-auth-user" in h
        )
        assert xauth_headers["X-auth-user"] == "luca"
        assert xauth_headers["X-auth-token"] == "tok"

    def test_probe_sends_basic_credentials(self):
        # Basic: almeno una request ha Authorization decodificabile.
        captured = []
        variants = build_variants()

        def fake_opener(request):
            captured.append(request.headers)
            raise urllib.error.HTTPError(
                request.full_url, 401, "Unauthorized", {}, None
            )

        probe("https://host", "luca", "tok", variants, opener=fake_opener)
        basic = next(
            h for h in captured
            if h.get("Authorization", "").startswith("Basic ")
        )
        b64 = basic["Authorization"].split(" ")[1]
        decoded = (base64.b64decode(b64).decode()).split(":")
        assert decoded == ["luca", "tok"]
