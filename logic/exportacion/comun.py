"""Ayudantes y utilidades comunes para generación de SVG e integración con Inkscape."""

from typing import Iterable, List, Tuple

XML_DECLARACION: str = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
NAMESPACES_INKSCAPE: str = 'xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"'


def formatear_path(puntos: Iterable[Tuple[float, float]], cerrado: bool = False) -> str:
    """Formatea una secuencia de puntos 2D en una cadena de comando path SVG 'M x,y L x,y ... [Z]'."""
    pts = list(puntos)
    if not pts:
        return ""
    d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    if cerrado:
        d += " Z"
    return d


def formatear_path_simetrico(pts_derecha: Iterable[Tuple[float, float]], pts_izquierda: Iterable[Tuple[float, float]]) -> str:
    """Combina el perfil derecho con el izquierdo invertido formando un path cerrado."""
    puntos = list(pts_derecha) + list(reversed(list(pts_izquierda)))
    return formatear_path(puntos, cerrado=True)


def defs_marcadores_flechas(color: str) -> List[str]:
    """Genera bloque <defs> con marcadores de flechas para cotas en el color indicado."""
    return [
        '  <defs>',
        '    <marker id="arrow-start" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">',
        f'      <path d="M 5 1 L 1 3 L 5 5 Z" fill="{color}" />',
        '    </marker>',
        '    <marker id="arrow-end" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto">',
        f'      <path d="M 1 1 L 5 3 L 1 5 Z" fill="{color}" />',
        '    </marker>',
        '  </defs>',
    ]


def guardar_svg(ruta: str, svg: str) -> None:
    """Guarda una cadena SVG en disco codificada en UTF-8."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(svg)


def capa_inkscape(label: str, id_capa: str, lineas_hijas: Iterable[str]) -> List[str]:
    """Envuelve una lista de elementos en un grupo <g> etiquetado como capa de Inkscape."""
    salida = [f'  <g inkscape:groupmode="layer" inkscape:label="{label}" id="{id_capa}">']
    salida.extend(lineas_hijas)
    salida.append('  </g>')
    return salida
