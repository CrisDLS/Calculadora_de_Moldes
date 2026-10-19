"""Reducción de colores mediante agrupación de tonos parecidos con Pillow y numpy."""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import List, Union

import numpy as np
from PIL import Image, ImageFilter

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


def _rgb_a_lab(rgb_arr: np.ndarray) -> np.ndarray:
    """Convierte un arreglo de colores sRGB (N, 3) a espacio perceptual CIE L*a*b*."""
    rgb = rgb_arr.astype(np.float64) / 255.0
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92

    # Matriz sRGB a XYZ (D65)
    X = rgb[:, 0] * 0.4124564 + rgb[:, 1] * 0.3575761 + rgb[:, 2] * 0.1804375
    Y = rgb[:, 0] * 0.2126729 + rgb[:, 1] * 0.7151522 + rgb[:, 2] * 0.0721750
    Z = rgb[:, 0] * 0.0193339 + rgb[:, 1] * 0.1191920 + rgb[:, 2] * 0.9503041

    X /= 0.95047
    Y /= 1.00000
    Z /= 1.08883

    for arr in [X, Y, Z]:
        m = arr > 0.008856
        arr[m] = arr[m] ** (1.0 / 3.0)
        arr[~m] = (7.787 * arr[~m]) + (16.0 / 116.0)

    L = (116.0 * Y) - 16.0
    a = 500.0 * (X - Y)
    b = 200.0 * (Y - Z)
    return np.stack([L, a, b], axis=-1)


def _lab_a_rgb(lab_arr: np.ndarray) -> np.ndarray:
    """Convierte un arreglo CIE L*a*b* (N, 3) de vuelta a sRGB (N, 3) uint8 [0, 255]."""
    L = lab_arr[:, 0]
    a = lab_arr[:, 1]
    b = lab_arr[:, 2]

    Y = (L + 16.0) / 116.0
    X = a / 500.0 + Y
    Z = Y - b / 200.0

    for arr in [X, Y, Z]:
        m = (arr ** 3) > 0.008856
        arr[m] = arr[m] ** 3
        arr[~m] = (arr[~m] - 16.0 / 116.0) / 7.787

    X *= 0.95047
    Y *= 1.00000
    Z *= 1.08883

    r = X * 3.2404542 + Y * -1.5371385 + Z * -0.4985314
    g = X * -0.9692660 + Y * 1.8760108 + Z * 0.0415560
    b = X * 0.0556434 + Y * -0.2040259 + Z * 1.0572252

    rgb = np.stack([r, g, b], axis=-1)
    mask = rgb > 0.0031308
    rgb[mask] = 1.055 * (rgb[mask] ** (1.0 / 2.4)) - 0.055
    rgb[~mask] = 12.92 * rgb[~mask]

    return np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)


def _kmeans_lab_ponderado(
    opacos_rgb: np.ndarray,
    max_colores: int,
    es_gris: bool = False,
    max_iter: int = 20,
    semilla: int = 42,
) -> np.ndarray:
    """Calcula una paleta de hasta max_colores usando k-means ponderado en espacio CIE Lab."""
    unicos, counts = np.unique(opacos_rgb, axis=0, return_counts=True)
    if len(unicos) <= max_colores:
        return unicos

    lab_unicos = _rgb_a_lab(unicos)
    weights = counts.astype(np.float64)

    rng = np.random.RandomState(semilla)
    n = len(unicos)
    first_idx = rng.choice(n, p=weights / weights.sum())
    centers = [lab_unicos[first_idx]]

    for _ in range(1, max_colores):
        dists = np.min([np.sum((lab_unicos - c) ** 2, axis=1) for c in centers], axis=0)
        probs = dists * weights
        total_p = probs.sum()
        if total_p == 0:
            break
        probs /= total_p
        next_idx = rng.choice(n, p=probs)
        centers.append(lab_unicos[next_idx])

    centers = np.array(centers)
    for _ in range(max_iter):
        dists = np.sum((lab_unicos[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(dists, axis=1)
        new_centers = []
        for k in range(len(centers)):
            mask = labels == k
            if np.any(mask):
                w_k = weights[mask]
                new_c = np.sum(lab_unicos[mask] * w_k[:, None], axis=0) / w_k.sum()
                new_centers.append(new_c)
            else:
                new_centers.append(centers[k])
        new_centers = np.array(new_centers)
        if np.allclose(centers, new_centers, atol=1e-2):
            break
        centers = new_centers

    pal_rgb = _lab_a_rgb(centers)
    if es_gris:
        gm = np.round(pal_rgb.mean(axis=1)).astype(np.uint8)
        pal_rgb = np.stack([gm, gm, gm], axis=-1)
    return pal_rgb


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
    suavizado: int = 3,
) -> Image.Image:
    """Reduce los colores de una imagen agrupando tonos parecidos sin dithering.

    - max_colores: tope máximo de colores (>= 1); tonos resultantes con distancia RGB
      menor a umbral_fusion_rgb se fusionan (puede devolver menos de max_colores).
    - modo: 'color' o 'grises' (donde todo píxel opaco cumple R=G=B).
    - umbral_fusion_rgb: distancia mínima euclidiana en RGB para no fusionar tonos parecidos.
    - suavizado: tamaño del filtro de mediana para eliminar grano y ruido antes de agrupar
      (por defecto 3; 0 para desactivar).
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
    opacos_rgb_orig = arr[mask_opaco][:, :3]
    if es_gris:
        gris_orig = np.round(
            0.299 * opacos_rgb_orig[:, 0] + 0.587 * opacos_rgb_orig[:, 1] + 0.114 * opacos_rgb_orig[:, 2]
        ).astype(np.uint8)
        opacos_trabajo_orig = np.stack([gris_orig, gris_orig, gris_orig], axis=-1)
    else:
        opacos_trabajo_orig = opacos_rgb_orig

    # Si la imagen ya tiene max_colores o menos, devolverla idéntica sin filtrar
    unicos_orig = np.unique(opacos_trabajo_orig, axis=0)
    if len(unicos_orig) <= max_colores:
        out_rgba = np.zeros_like(arr)
        out_rgba[mask_opaco, :3] = opacos_trabajo_orig
        out_rgba[mask_opaco, 3] = 255
        return Image.fromarray(out_rgba, mode="RGBA")

    # Suavizado de grano previo para estabilizar regiones y eliminar ruido de alta frecuencia
    if suavizado > 0 and suavizado % 2 == 0:
        suavizado += 1

    if suavizado >= 3 and min(img.size) >= 2:
        arr_rgb = arr[:, :, :3].copy()
        if not np.all(mask_opaco):
            color_medio = np.round(arr_rgb[mask_opaco].mean(axis=0)).astype(np.uint8)
            arr_rgb[~mask_opaco] = color_medio
        img_suave = Image.fromarray(arr_rgb, mode="RGB").filter(
            ImageFilter.MedianFilter(size=suavizado)
        )
        arr[:, :, :3] = np.array(img_suave, dtype=np.uint8)
        opacos_rgb = arr[mask_opaco][:, :3]
    else:
        opacos_rgb = opacos_rgb_orig

    if es_gris:
        gris = np.round(
            0.299 * opacos_rgb[:, 0] + 0.587 * opacos_rgb[:, 1] + 0.114 * opacos_rgb[:, 2]
        ).astype(np.uint8)
        opacos_trabajo = np.stack([gris, gris, gris], axis=-1)
    else:
        opacos_trabajo = opacos_rgb

    pal_cols = _kmeans_lab_ponderado(opacos_trabajo, max_colores, es_gris=es_gris)
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
