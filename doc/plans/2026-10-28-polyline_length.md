# Piano: implementazione `polyline_length(points)` in kemai_client/geometry.py

## Risposte alle domande di chiarimento

1. **Integration test con circle_points?** → **SÌ**, includere un test che verifica polyline_length su un cerchio n=8 ≈ 2πr (precisione ~1e-9).
2. **ValueError messaggio?** → `"La spezzata richiede almeno 2 punti"` (messaggio generico, coerente con lo stile italiano del progetto).
3. **~10 test:** (1) 2 punti, (2) 3 punti, (3) 1 punto→ValueError, (4) 0 punti→ValueError, (5) punti coincidenti→0, (6) spezzata negativa, (7) floating point precision, (8) 2 punti orizzontali, (9) 2 punti verticali, (10) integration test su cerchio n=8.

## Contesto

- **Repo:** `C:/Users/luca/test/local-llm/`
- **Modulo target:** `kemai_client/geometry.py` (linee 1-115)
- **Test target:** `tests/test_polyline_length.py` (nuovo)
- **Stile:** `test_lerp.py` — classe `TestPolylineLength`, docstring in italiano, `pytest.approx`
- **Venv:** `C:\Users\luca\test\local-llm\.venv\Scripts\python.exe -m pytest`
- **Baseline test:** "1 failed, 277 passed" (TestCheckActiveSession permanente)

## Perimetro drift

**MODIFICARE:**
- `kemai_client/geometry.py` — aggiungere funzione `polyline_length` (dopo lerp, prima di octagon_points)
- `tests/test_polyline_length.py` — nuovo file con ~10 test

**NON TOCCARE:**
- `lerp`, `octagon_points`, `circle_points` (stesso comportamento)
- `conftest.py`, `__init__.py`, `__pycache__`
- `tests/test_lerp.py`, `tests/test_geometry.py`, `tests/test_circle_points.py`
- `tests/test_errors.py`, `tests/test_probe.py`, `tests/test_exit_handler.py`, `tests/test_settings_dialog.py`
- `tests/test_app.py`, `tests/test_stop_button_click.py`, `tests/test_i18n.py`, `tests/test_tray.py`
- `tests/test_verify_fix_tool.py`, `tests/test_config.py`, `tests/test_logging.py`, `tests/test_widgets.py`
- `tests/test_controller.py`, `tests/test_main_window.py`, `tests/test_endpoints.py`, `tests/test_models.py`
- `tests/test_client.py`
- Qualsiasi file in `kemai_client/api/`, `kemai_client/controller.py`, `kemai_client/ui/`, `kemai_client/tray.py`

## Edit 1 — `kemai_client/geometry.py`

**Posizione:** dopo la funzione `lerp` (linea ~45, dopo `return a + (b - a) * t`), prima di `def octagon_points` (linea ~47).

**Codice da inserire:**

```python
def polyline_length(points: list[tuple[float, float]]) -> float:
    """Calcola la lunghezza della spezzata definita da `points`.

    Somma le distanze euclidee tra punti consecutivi.

    Args:
        points: lista di tuple (x, y).

    Returns:
        Lunghezza totale della spezzata.

    Raises:
        ValueError: se `points` contiene meno di 2 punti.

    Examples:
        >>> polyline_length([(0, 0), (3, 4)])
        5.0
        >>> polyline_length([(0, 0), (1, 0), (1, 1)])
        2.0
    """
    if len(points) < 2:
        raise ValueError("La spezzata richiede almeno 2 punti")
    return sum(
        math.hypot(points[i + 1][0] - points[i][0],
                   points[i + 1][1] - points[i][1])
        for i in range(len(points) - 1)
    )
```

## Edit 2 — `tests/test_polyline_length.py` (nuovo file)

**Contenuto completo:**

```python
"""Test della funzione polyline_length.

Nessuna dipendenza da Tkinter o Pillow: il modulo e' importabile
su una macchina headless.
"""

import math

import pytest

from kemai_client.geometry import polyline_length


class TestPolylineLength:
    def test_polyline_length_two_points(self):
        """2 punti -> distanza euclidea."""
        assert polyline_length([(0.0, 0.0), (3.0, 4.0)]) == pytest.approx(5.0)

    def test_polyline_length_three_points(self):
        """3 punti -> somma di 2 segmenti."""
        assert polyline_length([(0, 0), (1, 0), (1, 1)]) == pytest.approx(2.0)

    def test_polyline_length_one_point_raises(self):
        """1 punto -> ValueError."""
        with pytest.raises(ValueError, match="almeno 2 punti"):
            polyline_length([(0.0, 0.0)])

    def test_polyline_length_zero_points_raises(self):
        """0 punti -> ValueError."""
        with pytest.raises(ValueError, match="almeno 2 punti"):
            polyline_length([])

    def test_polyline_length_coincident_points(self):
        """Punti coincidenti -> lunghezza 0."""
        assert polyline_length([(1.0, 1.0), (1.0, 1.0)]) == pytest.approx(0.0)

    def test_polyline_length_negative_coords(self):
        """Coordinate negative."""
        assert polyline_length([(-1.0, -1.0), (1.0, 1.0)]) == pytest.approx(
            math.sqrt(8.0)
        )

    def test_polyline_length_precision(self):
        """Precisione floating point."""
        pts = [(0.0, 0.0), (0.1, 0.1)]
        result = polyline_length(pts)
        assert result == pytest.approx(math.sqrt(0.02), rel_tol=1e-12)

    def test_polyline_length_horizontal(self):
        """Segmento orizzontale."""
        assert polyline_length([(0.0, 5.0), (10.0, 5.0)]) == pytest.approx(10.0)

    def test_polyline_length_vertical(self):
        """Segmento verticale."""
        assert polyline_length([(3.0, 0.0), (3.0, 7.0)]) == pytest.approx(7.0)

    def test_polyline_length_circle_n8(self):
        """Spezzata su cerchio n=8: somma ≈ 2πr."""
        from kemai_client.geometry import circle_points
        pts = circle_points(0.0, 0.0, 1.0, 8)
        length = polyline_length(pts)
        # 8 segmenti di 45° su r=1: 8 * 2*sin(pi/8) = 8 * 0.76536...
        expected = 8.0 * math.sin(math.pi / 8.0) * 2.0
        assert length == pytest.approx(expected, rel_tol=1e-12)
        assert length < 2 * math.pi  # la spezzata e sempre piu corta della circonferenza
```

## Checklist di verifica (post-edit)

1. `C:\Users\luca\test\local-llm\.venv\Scripts\python.exe -m pytest tests/test_polyline_length.py -v` → 9 test verdi
2. `C:\Users\luca\test\local-llm\.venv\Scripts\python.exe -m pytest tests/ -v` → "1 failed, 286 passed" (baseline: TestCheckActiveSession permanente)
3. `C:\Users\luca\test\local-llm\.venv\Scripts\python.exe -c "from kemai_client.geometry import polyline_length; print(polyline_length([(0,0),(3,4)]))"` → `5.0`
4. Niente import di Tkinter/Pillow in `geometry.py` o `test_polyline_length.py`
5. `math.hypot` è usato (già importato via `import math` a riga 8)

## Rischio / nota

- `math.hypot` è già importato (riga 8 di geometry.py), nessun import extra necessario.
- Il modulo-level docstring di `geometry.py` (righe 1-6) menziona "ottagono" e "piano cartesiano". `polyline_length` è geometrica (spezzata) e rientra nel contesto dell'ottagono/circonferenza.
- `math.hypot` è O(1) per coppia di punti; complessità totale O(n) dove n = len(points).
