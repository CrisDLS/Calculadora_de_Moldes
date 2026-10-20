"""Cálculo de consumo y superficie de papel en cm² por color para una imagen y silueta."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Union

import numpy as np
from PIL import Image

from logic.papel.reduccion_colores import reducir_colores, _cargar_imagen_rgba
from logic.papel.vectorizacion import medir_regiones, _normalizar_color, DictAreas


def medir_cm2_por_color(
    imagen_rgba: Union[Image.Image, str, Path, bytes, bytearray],
    mascara_silueta: np.ndarray,
    cm_por_px: float,
    color_base_hex: str,
    max_colores: int = 8,
    modo: str = "color",
) -> Dict[str, float]:
    """Mide la superficie en cm² consumida por cada color de una imagen dentro de una silueta.

    Parámetros:
    - imagen_rgba: Imagen PIL en modo RGBA (o ruta/bytes convertible).
    - mascara_silueta: Arreglo booleano 2D (H, W) que delimita la pieza.
    - cm_por_px: Escala en centímetros por píxel (factor lineal > 0).
    - color_base_hex: Color de fondo asignado a las zonas vacías (ej. "#FFFFFF").
    - max_colores: Número máximo de colores a agrupar en el diseño (por defecto 8).
    - modo: 'color' o 'grises'.

    Retorna:
    - Dict[str, float]: Mapeo {color_hex: superficie_cm2}.
    """
    if cm_por_px <= 0.0:
        raise ValueError(f"cm_por_px debe ser mayor a 0, recibido: {cm_por_px}")

    img = _cargar_imagen_rgba(imagen_rgba)
    arr = np.array(img, dtype=np.uint8)

    mask = np.asarray(mascara_silueta, dtype=bool)
    if mask.shape != (arr.shape[0], arr.shape[1]):
        raise ValueError(
            f"Las dimensiones de la máscara {mask.shape} no coinciden con la imagen {(arr.shape[0], arr.shape[1])}"
        )

    factor_cm2 = float(cm_por_px) ** 2
    base_norm = _normalizar_color(color_base_hex)
    if not base_norm:
        base_norm = color_base_hex.upper() if color_base_hex.startswith("#") else f"#{color_base_hex.upper()}"

    # Identificar zonas dentro de la máscara: opacas (diseño) y vacías (papel base)
    mask_opaco = mask & (arr[:, :, 3] >= 128)
    mask_vacio = mask & (arr[:, :, 3] < 128)

    num_px_vacios = int(np.sum(mask_vacio))
    area_vacia_cm2 = num_px_vacios * factor_cm2

    areas_cm2 = DictAreas()

    # Si no hay píxeles opacos dentro de la máscara, todo es color base
    num_px_opacos = int(np.sum(mask_opaco))
    if num_px_opacos == 0:
        if area_vacia_cm2 > 0.0:
            areas_cm2[base_norm] = area_vacia_cm2
        return areas_cm2

    # Construir imagen aislada solo con los píxeles opacos dentro de la máscara
    arr_enmascarado = np.zeros_like(arr)
    arr_enmascarado[mask_opaco] = arr[mask_opaco]
    img_enmascarada = Image.fromarray(arr_enmascarado, mode="RGBA")

    # Reducir colores del diseño y medir regiones vectorizadas
    img_reducida = reducir_colores(
        img_enmascarada,
        max_colores=max_colores,
        modo=modo,
    )
    regiones_px = medir_regiones(img_reducida)

    # Convertir áreas medidas en px² a cm²
    for color_hex, area_px in regiones_px.items():
        c_norm = _normalizar_color(color_hex) or color_hex.upper()
        areas_cm2[c_norm] = area_px * factor_cm2

    # Sumar el área de zonas vacías al color base
    if area_vacia_cm2 > 0.0:
        areas_cm2[base_norm] = areas_cm2.get(base_norm, 0.0) + area_vacia_cm2

    return areas_cm2
