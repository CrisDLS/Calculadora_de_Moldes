"""Rasterización de siluetas de piezas en máscaras booleanas."""

from __future__ import annotations

from typing import Sequence, Tuple
import numpy as np
from PIL import Image, ImageDraw


def mascara_silueta(
    puntos_cm: Sequence[Tuple[float, float]],
    caja_cm: Tuple[float, float, float, float],
    px_por_cm: float,
    supersampling: int = 4,
) -> Tuple[np.ndarray, float]:
    """Genera una máscara booleana 2D que delimita la silueta de una pieza con escala conocida.

    Parámetros:
    - puntos_cm: Vértices del contorno en cm, con coordenadas cartesianas (+y hacia arriba).
    - caja_cm: Bounding box (xmin, ymin, ancho, alto) en cm.
    - px_por_cm: Resolución en píxeles por centímetro (factor lineal > 0).
    - supersampling: Factor de sobremuestreo para precisión subpíxel (por defecto 4).

    Retorna:
    - Tuple[np.ndarray, float]:
        - mascara: Arreglo booleano 2D (H, W) donde True indica dentro de la pieza.
        - cm_por_px: Escala lineal en cm por píxel (1.0 / px_por_cm).
    """
    if px_por_cm <= 0.0:
        raise ValueError(f"px_por_cm debe ser mayor a 0, recibido: {px_por_cm}")

    xmin, ymin, w_cm, h_cm = caja_cm
    ymax = ymin + h_cm

    w_px = max(1, int(round(w_cm * px_por_cm)))
    h_px = max(1, int(round(h_cm * px_por_cm)))
    cm_por_px = 1.0 / px_por_cm

    if not puntos_cm:
        return np.zeros((h_px, w_px), dtype=bool), cm_por_px

    ss = max(1, int(supersampling))
    w_hi = w_px * ss
    h_hi = h_px * ss

    scale_x = px_por_cm * ss
    scale_y = px_por_cm * ss

    puntos_px = [
        ((x - xmin) * scale_x, (ymax - y) * scale_y)
        for x, y in puntos_cm
    ]

    img_hi = Image.new("L", (w_hi, h_hi), 0)
    draw_hi = ImageDraw.Draw(img_hi)
    draw_hi.polygon(puntos_px, fill=255)

    if ss > 1:
        img_down = img_hi.resize((w_px, h_px), Image.Resampling.BILINEAR)
        mascara = np.array(img_down, dtype=np.uint8) >= 128
    else:
        mascara = np.array(img_hi, dtype=np.uint8) >= 128

    return mascara, cm_por_px
