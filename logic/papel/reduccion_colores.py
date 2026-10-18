"""Reducción de colores mediante agrupación de tonos parecidos con Pillow y numpy."""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import List, Union

import numpy as np
from PIL import Image

# Umbral mínimo de distancia euclidiana RGB entre dos colores de la paleta reducida.
# Equivale a ~6.3 % de la diagonal RGB (441.7) o ~16.2 niveles de gris (28 / sqrt(3)),
# fusionando tonos redundantes que en papel china comercial corresponden al mismo pliego.
UMBRAL_FUSION_RGB: float = 28.0


def _cargar_imagen_rgba(imagen_rgba: Union[Image.Image, str, Path, bytes, bytearray]) -> Image.Image:
    """Convierte la entrada (ruta, bytes o PIL.Image) a una instancia PIL en modo RGBA."""
    if isinstance(imagen_rgba, (str, Path)):
        return Image.open(imagen_rgba).convert("RGBA")
    if isinstance(imagen_rgba, (bytes, bytearray)):
        return Image.open(io.BytesIO(imagen_rgba)).convert("RGBA")
    if hasattr(imagen_rgba, "convert"):
        return imagen_rgba if imagen_rgba.mode == "RGBA" else imagen_rgba.convert("RGBA")
    raise TypeError(f"Tipo de imagen no soportado: {type(imagen_rgba)}")


def _fusionar_colores_cercanos(
    colores_rgb: np.ndarray,
    pesos: np.ndarray,
    umbral_rgb: float,
    es_gris: bool = False,
) -> np.ndarray:
    """Fusiona iterativamente pares de colores con distancia RGB menor a umbral_rgb."""
    cols: List[List[float]] = colores_rgb.astype(np.float64).tolist()
    w: List[float] = pesos.astype(np.float64).tolist()

    while len(cols) > 1:
        min_d = float("inf")
        par = (-1, -1)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                d = math.dist(cols[i], cols[j])
                if d < min_d:
                    min_d = d
                    par = (i, j)
        if min_d >= umbral_rgb:
            break

        i, j = par
        wi, wj = w[i], w[j]
        wtot = wi + wj
        fusionado = [(cols[i][k] * wi + cols[j][k] * wj) / wtot for k in range(3)]
        if es_gris:
            gm = float(round(sum(fusionado) / 3.0))
            fusionado = [gm, gm, gm]
        cols[i] = fusionado
        w[i] = wtot
        cols.pop(j)
        w.pop(j)

    pal_final = np.clip(np.round(np.array(cols)), 0, 255).astype(np.uint8)
    if es_gris:
        gm_arr = np.round(pal_final.mean(axis=1)).astype(np.uint8)
        pal_final = np.stack([gm_arr, gm_arr, gm_arr], axis=-1)
    return pal_final


def _calcular_paleta_unicos(unicos: np.ndarray, max_colores: int, es_gris: bool) -> np.ndarray:
    """Obtiene hasta max_colores sobre el conjunto de colores únicos sin sesgo de área."""
    paleta_img = Image.new("RGB", (len(unicos), 1))
    paleta_img.putdata([tuple(map(int, c)) for c in unicos])
    pal = paleta_img.quantize(
        colors=max_colores,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    q_unicos = paleta_img.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    pal_cols = np.unique(np.array(q_unicos, dtype=np.uint8).reshape(-1, 3), axis=0)
    if es_gris:
        gv = np.round(pal_cols.mean(axis=1)).astype(np.uint8)
        pal_cols = np.stack([gv, gv, gv], axis=-1)
    return pal_cols


def _asignar_a_paleta(puntos_rgb: np.ndarray, paleta_rgb: np.ndarray) -> np.ndarray:
    """Devuelve el índice del color más cercano en paleta_rgb para cada píxel."""
    dists = np.sum(
        (puntos_rgb[:, None, :].astype(np.float64) - paleta_rgb[None, :, :].astype(np.float64)) ** 2,
        axis=2,
    )
    return np.argmin(dists, axis=1)


def reducir_colores(
    imagen_rgba: Union[Image.Image, str, Path, bytes, bytearray],
    max_colores: int,
    modo: str = "color",
    umbral_fusion_rgb: float = UMBRAL_FUSION_RGB,
) -> Image.Image:
    """Reduce los colores de una imagen agrupando tonos parecidos sin dithering.

    - max_colores: tope máximo de colores (>= 1); tonos resultantes con distancia RGB
      menor a umbral_fusion_rgb se fusionan (puede devolver menos de max_colores).
    - modo: 'color' o 'grises' (donde todo píxel opaco cumple R=G=B).
    - Transparencia: alpha < 128 -> 0, alpha >= 128 -> 255.
    """
    if max_colores < 1:
        raise ValueError("max_colores debe ser al menos 1")
    if modo not in ("color", "grises"):
        raise ValueError(f"Modo desconocido: '{modo}'. Debe ser 'color' o 'grises'.")

    img = _cargar_imagen_rgba(imagen_rgba)
    arr = np.array(img, dtype=np.uint8)
    mask_opaco = arr[:, :, 3] >= 128
    if not np.any(mask_opaco):
        return Image.new("RGBA", img.size, (0, 0, 0, 0))

    es_gris = modo == "grises"
    opacos_rgb = arr[mask_opaco][:, :3]
    if es_gris:
        gris = np.round(
            0.299 * opacos_rgb[:, 0] + 0.587 * opacos_rgb[:, 1] + 0.114 * opacos_rgb[:, 2]
        ).astype(np.uint8)
        opacos_trabajo = np.stack([gris, gris, gris], axis=-1)
    else:
        opacos_trabajo = opacos_rgb

    unicos = np.unique(opacos_trabajo, axis=0)
    if len(unicos) <= max_colores:
        out_rgba = np.zeros_like(arr)
        out_rgba[mask_opaco, :3] = opacos_trabajo
        out_rgba[mask_opaco, 3] = 255
        return Image.fromarray(out_rgba, mode="RGBA")

    pal_cols = _calcular_paleta_unicos(unicos, max_colores, es_gris)
    labels = _asignar_a_paleta(opacos_trabajo, pal_cols)
    used_idx, counts = np.unique(labels, return_counts=True)
    cols_usados = pal_cols[used_idx]

    if umbral_fusion_rgb > 0.0 and len(cols_usados) > 1:
        pal_final = _fusionar_colores_cercanos(cols_usados, counts, umbral_fusion_rgb, es_gris)
        colores_asignados = pal_final[_asignar_a_paleta(opacos_trabajo, pal_final)]
    else:
        colores_asignados = pal_cols[labels]

    out_rgba = np.zeros_like(arr)
    out_rgba[mask_opaco, :3] = colores_asignados
    out_rgba[mask_opaco, 3] = 255
    return Image.fromarray(out_rgba, mode="RGBA")
