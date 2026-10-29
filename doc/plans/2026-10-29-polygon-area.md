# Piano: polygon_area (2026-10-29)

## Domande di chiarimento
**Nessuna.** La specifica è completa: shoelace formula, valore assoluto, ValueError < 3 punti, ~10 test.

## Riferimenti file:line

### 1. `kemai_client/geometry.py` — aggiungere `polygon_area` dopo `polyline_length`

- **Linea 60**: fine di `polyline_length` (il `return sum(...)` con la chiusura della funzione)
- **Linea 62**: `def octagon_points(...)` — il nuovo `polygon_area` va **prima** di questa riga
- Edit: **insert** dopo la riga 60 (dopo il `return sum(...)`) una nuova funzione

### 2. `tests/test_polygon_area.py` — nuovo file

- Stile: classe `TestPolygonArea` con metodi `def test_...`
- Import: `from kemai_client.geometry import polygon_area`
- Usare `pytest.approx` per i float (come `test_polyline_length.py`)
- Usare `pytest.raises(ValueError, match=...)` per i ValueError

## Lista test (~10)

| # | Test | Attesa |
|---|------|--------|
| 1 | `test_triangle_unit` | `polygon_area([(0,0),(1,0),(0,1)])` → 0.5 |
| 2 | `test_square_unit` | `polygon_area([(0,0),(1,0),(1,1),(0,1)])` → 1.0 |
| 3 | `test_concave` | L-shape: `[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]` → 3.0 |
| 4 | `test_clockwise_same_area` | Stesso triangolo ma orario → 0.5 |
| 5 | `test_empty_raises` | `[]` → ValueError |
| 6 | `test_one_point_raises` | `[(0,0)]` → ValueError |
| 7 | `test_float_coords` | `[(0,0),(1.5,0),(0,2.5)]` → 1.875 |
| 8 | `test_collinear_zero_area` | `[(0,0),(1,1),(2,2)]` → 0.0 |
| 9 | `test_minimal_3_points` | Triangolo generico 3 punti |
| 10 | `test_many_points` | `circle_points(0,0,1,12)` → π ≈ 3.14159 |

## Perimetro del drift
- **NON** modificare `polyline_length`, `octagon_points`, `circle_points`, `lerp`
- **NON** modificare `test_polyline_length.py` o `test_geometry.py`
- **NON** modificare il baseline `TestCheckActiveSession` (1 failed)

## Sequenza di esecuzione
1. Edit `geometry.py` → insert `polygon_area`
2. Write `tests/test_polygon_area.py`
3. `cd C:\Users\luca\test\local-llm && .venv\Scripts\python.exe -m pytest tests/test_polygon_area.py -v`
4. `cd C:\Users\luca\test\local-llm && .venv\Scripts\python.exe -m pytest -x` (verifica baseline)
