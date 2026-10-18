"""Medición de áreas por color mediante vectorización poligonal con VTracer."""

from __future__ import annotations

import io
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple, Union

import defusedxml.ElementTree as ET
from PIL import Image
import vtracer


class DictAreas(dict):
    """Diccionario de áreas por color con búsqueda insensible a mayúsculas/minúsculas."""

    def __getitem__(self, key: str) -> float:
        if isinstance(key, str):
            key = key.upper()
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: float) -> None:
        if isinstance(key, str):
            key = key.upper()
        super().__setitem__(key, value)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            key = key.upper()
        return super().__contains__(key)

    def get(self, key: str, default: float | None = None) -> float | None:
        if isinstance(key, str):
            key = key.upper()
        return super().get(key, default)


def calcular_area_shoelace(puntos: List[Tuple[float, float]]) -> float:
    """Calcula el área con signo de un polígono 2D usando la fórmula de Shoelace (Gauss).

    En coordenadas de pantalla (Y hacia abajo):
    - Sentido horario -> área signada positiva (+).
    - Sentido antihorario -> área signada negativa (-).
    """
    n = len(puntos)
    if n < 3:
        return 0.0
    area_doble = sum(
        puntos[i][0] * puntos[(i + 1) % n][1] - puntos[(i + 1) % n][0] * puntos[i][1]
        for i in range(n)
    )
    return area_doble / 2.0


def extraer_traslacion(transform_str: str | None) -> Tuple[float, float]:
    """Extrae traslación (tx, ty) de un atributo SVG transform translate(...)."""
    if not transform_str:
        return 0.0, 0.0
    patron = r"translate\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)(?:[\s,]+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?))?\s*\)"
    match = re.search(patron, transform_str)
    if not match:
        return 0.0, 0.0
    tx = float(match.group(1))
    ty = float(match.group(2)) if match.group(2) is not None else 0.0
    return tx, ty


def parsear_subpoligonos_d(d_str: str, tx: float = 0.0, ty: float = 0.0) -> List[List[Tuple[float, float]]]:
    """Parsea el atributo 'd' de un path SVG generado en modo polígono.

    Separa los distintos subpolígonos (iniciados con M/m y cerrados con Z/z)
    aplicando el desplazamiento (tx, ty) a cada vértice.
    """
    subpoligonos: List[List[Tuple[float, float]]] = []
    if not d_str:
        return subpoligonos

    # Divide por comandos M, L, Z
    partes = re.split(r"([MLZmlz])", d_str)
    poligono_actual: List[Tuple[float, float]] = []

    for parte in partes:
        texto = parte.strip()
        if not texto:
            continue
        if texto in "MLZmlz":
            cmd = texto.upper()
            if cmd in ("M", "Z"):
                if len(poligono_actual) >= 3:
                    subpoligonos.append(poligono_actual)
                poligono_actual = []
        else:
            numeros = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", texto)
            for i in range(0, len(numeros) - 1, 2):
                x = float(numeros[i]) + tx
                y = float(numeros[i + 1]) + ty
                poligono_actual.append((x, y))

    if len(poligono_actual) >= 3:
        subpoligonos.append(poligono_actual)

    return subpoligonos


def calcular_area_path(subpoligonos: List[List[Tuple[float, float]]]) -> float:
    """Calcula el área neta de un path con soporte para huecos (cutout).

    En VTracer con hierarchical='cutout', el polígono exterior tiene sentido horario (+)
    y los huecos interiores tienen sentido antihorario (-).
    La suma algebraica de las áreas signadas resta automáticamente los huecos.
    """
    if not subpoligonos:
        return 0.0
    if len(subpoligonos) == 1:
        return abs(calcular_area_shoelace(subpoligonos[0]))

    area_neta = sum(calcular_area_shoelace(sp) for sp in subpoligonos)
    return abs(area_neta)


def _normalizar_color(fill_str: str) -> str | None:
    """Normaliza un color SVG a formato hexadecimal '#RRGGBB'."""
    color = fill_str.strip()
    if not color or color.lower() == "none":
        return None
    if color.startswith("#"):
        # Si es formato corto #RGB -> #RRGGBB
        hex_digits = color[1:]
        if len(hex_digits) == 3:
            hex_digits = "".join(c * 2 for c in hex_digits)
        return f"#{hex_digits.upper()}"
    # Formato rgb(r, g, b)
    m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color, re.IGNORECASE)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02X}{g:02X}{b:02X}"
    return color.upper()


def medir_regiones(imagen_rgba: Union[Image.Image, str, Path, bytes]) -> Dict[str, float]:
    """Vectoriza una imagen con VTracer y calcula el área total en px² de cada color.

    Parámetros:
    - imagen_rgba: Imagen PIL en modo RGBA, o ruta a archivo de imagen, o bytes PNG.

    Retorna:
    - dict con mapeo {color_hex: area_px}, donde los huecos de cada pieza restan
      su superficie y las áreas de regiones del mismo color se suman.
    """
    # 1. Asegurar imagen PIL en RGBA
    if isinstance(imagen_rgba, (str, Path)):
        img = Image.open(imagen_rgba).convert("RGBA")
    elif isinstance(imagen_rgba, (bytes, bytearray)):
        img = Image.open(io.BytesIO(imagen_rgba)).convert("RGBA")
    elif hasattr(imagen_rgba, "convert"):
        img = imagen_rgba if imagen_rgba.mode == "RGBA" else imagen_rgba.convert("RGBA")
    else:
        raise TypeError(f"Tipo de imagen no soportado: {type(imagen_rgba)}")

    # 2. Convertir imagen a PNG en memoria para VTracer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    # 3. Vectorización con VTracer (modo polígono y jerarquía cutout)
    svg_str = vtracer.convert_raw_image_to_svg(
        png_bytes,
        img_format="png",
        colormode="color",
        hierarchical="cutout",
        mode="polygon",
        filter_speckle=0,
    )

    if isinstance(svg_str, bytes):
        svg_str = svg_str.decode("utf-8")

    # 4. Parsear SVG con defusedxml
    root = ET.fromstring(svg_str)
    areas_por_color = DictAreas()

    for elem in root.iter():
        if elem.tag.split("}")[-1] == "path":
            fill = elem.get("fill", "")
            color_hex = _normalizar_color(fill)
            if not color_hex:
                continue

            transform = elem.get("transform")
            tx, ty = extraer_traslacion(transform)
            d_str = elem.get("d", "")

            subpoligonos = parsear_subpoligonos_d(d_str, tx, ty)
            area_path = calcular_area_path(subpoligonos)

            if color_hex not in areas_por_color:
                areas_por_color[color_hex] = 0.0
            areas_por_color[color_hex] += area_path

    return areas_por_color
