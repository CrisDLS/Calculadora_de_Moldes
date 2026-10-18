"""Reducción de colores mediante agrupación de tonos parecidos con Pillow."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Tuple, Union

from PIL import Image


def reducir_colores(
    imagen_rgba: Union[Image.Image, str, Path, bytes, bytearray],
    max_colores: int,
    modo: str = "color",
) -> Image.Image:
    """Reduce los colores de una imagen agrupando tonos parecidos sin dithering.

    Parámetros:
    - imagen_rgba: Imagen PIL RGBA, ruta de archivo o bytes de imagen.
    - max_colores: Número máximo de colores permitidos (>= 1).
    - modo: 'color' para cuantización en color, o 'grises' para niveles de gris.

    Comportamiento:
    - Transparencia: píxeles con alpha < 128 quedan transparentes (alpha=0),
      el resto quedan opacos (alpha=255).
    - Sin dithering: transiciones directas entre zonas de color.
    - Si la imagen ya tiene max_colores o menos, no la altera.
    - En modo 'grises': todo píxel opaco cumple R=G=B con máximo max_colores niveles.
    """
    if max_colores < 1:
        raise ValueError("max_colores debe ser al menos 1")
    if modo not in ("color", "grises"):
        raise ValueError(f"Modo desconocido: '{modo}'. Debe ser 'color' o 'grises'.")

    # 1. Asegurar formato PIL en RGBA
    if isinstance(imagen_rgba, (str, Path)):
        img = Image.open(imagen_rgba).convert("RGBA")
    elif isinstance(imagen_rgba, (bytes, bytearray)):
        img = Image.open(io.BytesIO(imagen_rgba)).convert("RGBA")
    elif hasattr(imagen_rgba, "convert"):
        img = imagen_rgba if imagen_rgba.mode == "RGBA" else imagen_rgba.convert("RGBA")
    else:
        raise TypeError(f"Tipo de imagen no soportado: {type(imagen_rgba)}")

    # 2. Máscara binaria de transparencia (alpha < 128 -> 0, alpha >= 128 -> 255)
    alpha = img.getchannel("A")
    mascara_binaria = alpha.point(lambda a: 255 if a >= 128 else 0, mode="L")

    # 3. Extraer colores opacos para no sesgar la paleta con píxeles transparentes
    pixels = img.getdata()
    opacos_rgb = [p[:3] for p in pixels if p[3] >= 128]

    # Si no hay píxeles opacos, devolver imagen completamente transparente
    if not opacos_rgb:
        res_vacia = Image.new("RGBA", img.size, (0, 0, 0, 0))
        return res_vacia

    # 4. Procesamiento según modo
    if modo == "color":
        opacos_unicos = set(opacos_rgb)
        if len(opacos_unicos) <= max_colores:
            res = img.copy()
            res.putalpha(mascara_binaria)
            return res

        base_rgb = img.convert("RGB")
        paleta_img = Image.new("RGB", (len(opacos_rgb), 1))
        paleta_img.putdata(opacos_rgb)
        pal = paleta_img.quantize(colors=max_colores, dither=Image.Dither.NONE)

        cuantizada = base_rgb.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
        cuantizada.putalpha(mascara_binaria)
        return cuantizada

    else:  # modo == "grises"
        opacos_gris_rgb = [
            (int(round(0.299 * r + 0.587 * g + 0.114 * b)),) * 3
            for r, g, b in opacos_rgb
        ]
        base_gris_rgb = img.convert("L").convert("RGB")
        opacos_gris_unicos = set(opacos_gris_rgb)

        if len(opacos_gris_unicos) <= max_colores:
            res = base_gris_rgb
            res.putalpha(mascara_binaria)
            return res

        paleta_img = Image.new("RGB", (len(opacos_gris_rgb), 1))
        paleta_img.putdata(opacos_gris_rgb)
        pal = paleta_img.quantize(colors=max_colores, dither=Image.Dither.NONE)

        cuantizada = base_gris_rgb.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
        cuantizada.putalpha(mascara_binaria)
        return cuantizada
