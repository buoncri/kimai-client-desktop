"""Helper geometrico per l'ottagono regolare.

L'ottagono ha 8 vertici equidistanti a 45° l'uno dall'altro,
partendo da 22,5° (il punto a destra dell'orologio è a 0°).
Il piano cartesiano di riferimento usa y verso l'alto;
"""

import math


def lerp(a: float, b: float, t: float) -> float:
    """Interpolazione lineare tra `a` e `b` al parametro `t`.

    Calcola `a + (b - a) * t`. Se `t` e fuori dall'intervallo `[0, 1]`
    viene **clamped** a `[0, 1]` prima del calcolo.

    Il piano cartesiano usa y verso l'alto (sentito matematico standard).

    Args:
        a: valore di partenza.
        b: valore di arrivo.
        t: parametro di interpolazione (clamp a [0, 1]).

    Returns:
        Il valore interpolato tra a e b.

    Examples:
        >>> lerp(0, 10, 0.5)
        5.0
        >>> lerp(0, 10, -1.0)
        0.0
        >>> lerp(0, 10, 2.0)
        10.0
        >>> lerp(5, 5, 0.5)
        5.0
    """
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def octagon_points(cx: float, cy: float, r: float) -> list[float]:
    """Restituisce i 16 float (x,y) × 8 vertici dell'ottagono."""
    points: list[float] = []
    for i in range(8):
        angle_deg = 22.5 + i * 45
        angle_rad = angle_deg * math.pi / 180.0
        x = cx + r * math.cos(angle_rad)
        y = cy - r * math.sin(angle_rad)
        points.extend((x, y))
    return points


def circle_points(cx: float, cy: float, r: float, n: int) -> list[tuple[float, float]]:
    """Restituisce i n vertici di una circonferenza centrata in (cx,cy) con raggio r.

    Il primo vertice è a angolo 0 rad: (cx+r, cy).
    I vertici sono in ordine anti-orario (angolo crescente).
    Niente chiusura duplicata: se n=3 si ottengono 3 punti, non 4.

    Il piano cartesiano usa y verso l'alto (sentito matematico standard).

    Args:
        cx: coordinata x del centro.
        cy: coordinata y del centro.
        r:  raggio (deve essere > 0).
        n:  numero di vertici (deve essere un intero positivo).

    Returns:
        Lista di tuple (x, y) con n punti.

    Raises:
        TypeError: se n non è un intero.
        ValueError: se n <= 0.

    Examples:
        >>> circle_points(0, 0, 1, 4)
        [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
        >>> circle_points(0, 0, 1, 3)
        [(1.0, 0.0), (-0.5, 0.8660254037844386), (-0.5, -0.8660254037844386)]
    """
    if not isinstance(n, int):
        raise TypeError(f"n deve essere un intero, non {type(n).__name__}")
    if n <= 0:
        raise ValueError(f"n deve essere positivo, non {n}")

    points: list[tuple[float, float]] = []
    for i in range(n):
        theta = 2.0 * math.pi * i / n
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        points.append((x, y))
    return points
