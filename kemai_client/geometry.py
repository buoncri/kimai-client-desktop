"""Helper geometrico per l'ottagono regolare.

L'ottagono ha 8 vertici equidistanti a 45° l'uno dall'altro,
partendo da 22,5° (il punto a destra dell'orologio è a 0°).
Il piano cartesiano di riferimento usa y verso l'alto;
chiama questa funzione con cy negativo per il sistema Tkinter.
"""

import math


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
