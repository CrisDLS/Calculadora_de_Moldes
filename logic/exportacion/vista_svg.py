# logic/exportacion/vista_svg.py
import re
from dataclasses import dataclass
from typing import Optional, Tuple
import xml.etree.ElementTree as ET

@dataclass
class VistaSvg:
    x: float
    y: float
    ancho: float
    alto: float

    @property
    def aspecto(self) -> float:
        return self.ancho / self.alto if self.alto > 0 else 1.0


def ajustar(contenido_ancho: float, contenido_alto: float, aspecto_zona: float = 1.0, margen: float = 0.05) -> VistaSvg:
    """Encaja todo el contenido centrado en la zona, conservando la relación de aspecto de la zona de pantalla."""
    if contenido_ancho <= 0 or contenido_alto <= 0:
        return VistaSvg(0.0, 0.0, 100.0, 100.0 / max(aspecto_zona, 0.01))

    w_con_margen = contenido_ancho * (1.0 + 2.0 * margen)
    h_con_margen = contenido_alto * (1.0 + 2.0 * margen)

    aspecto_contenido = w_con_margen / h_con_margen

    if aspecto_contenido > aspecto_zona:
        # El ancho manda
        ancho_vista = w_con_margen
        alto_vista = ancho_vista / aspecto_zona
    else:
        # El alto manda
        alto_vista = h_con_margen
        ancho_vista = alto_vista * aspecto_zona

    cx = contenido_ancho / 2.0
    cy = contenido_alto / 2.0

    x = cx - ancho_vista / 2.0
    y = cy - alto_vista / 2.0

    return VistaSvg(x, y, ancho_vista, alto_vista)


def zoom(
    vista: VistaSvg,
    factor: float,
    fx: float = 0.5,
    fy: float = 0.5,
    limites: Optional[Tuple[float, float]] = None,
    vista_base: Optional[VistaSvg] = None,
) -> VistaSvg:
    """Aplica zoom hacia el cursor manteniendo invariable el punto bajo (fx, fy).
    
    fx, fy son fracciones de la zona (0..1).
    factor > 1.0 acerca (zoom in), factor < 1.0 aleja (zoom out).
    limites es (ancho_min, ancho_max) en unidades del dibujo.
    """
    if factor <= 0:
        return vista

    # Punto en coordenadas del dibujo bajo el cursor
    px = vista.x + fx * vista.ancho
    py = vista.y + fy * vista.alto

    nuevo_ancho = vista.ancho / factor

    if limites is not None:
        ancho_min, ancho_max = limites
        if nuevo_ancho < ancho_min:
            nuevo_ancho = ancho_min
        elif nuevo_ancho > ancho_max:
            nuevo_ancho = ancho_max

    nuevo_alto = nuevo_ancho / vista.aspecto

    nuevo_x = px - fx * nuevo_ancho
    nuevo_y = py - fy * nuevo_alto

    return VistaSvg(nuevo_x, nuevo_y, nuevo_ancho, nuevo_alto)


def desplazar(
    vista: VistaSvg,
    dx: float,
    dy: float,
    limites_contenido: Optional[Tuple[float, float]] = None,
) -> VistaSvg:
    """Desplaza la vista por un delta (dx, dy) en coordenadas del dibujo."""
    nuevo_x = vista.x - dx
    nuevo_y = vista.y - dy

    if limites_contenido is not None:
        cont_w, cont_h = limites_contenido
        # Evitar que el dibujo se salga por completo de la zona (mantener al menos un 10% visible)
        min_x = -vista.ancho * 0.9
        max_x = cont_w - vista.ancho * 0.1
        min_y = -vista.alto * 0.9
        max_y = cont_h - vista.alto * 0.1

        nuevo_x = max(min_x, min(max_x, nuevo_x))
        nuevo_y = max(min_y, min(max_y, nuevo_y))

    return VistaSvg(nuevo_x, nuevo_y, vista.ancho, vista.alto)


def extraer_dimensiones_svg(svg: str) -> Tuple[float, float]:
    """Extrae ancho y alto nativos en mm del SVG, o del viewBox."""
    match_viewbox = re.search(r'viewBox="([^"]+)"', svg)
    if match_viewbox:
        parts = [float(p) for p in match_viewbox.group(1).split()]
        if len(parts) == 4:
            return parts[2], parts[3]

    match_w = re.search(r'width="([0-9.]+)mm"', svg)
    match_h = re.search(r'height="([0-9.]+)mm"', svg)
    if match_w and match_h:
        return float(match_w.group(1)), float(match_h.group(1))

    return 200.0, 200.0


def aplicar_viewbox(svg: str, vista: VistaSvg) -> str:
    """Reescribe el viewBox del SVG y fija width/height a 100% para que se ajuste al control."""
    viewbox_str = f'viewBox="{vista.x:.2f} {vista.y:.2f} {vista.ancho:.2f} {vista.alto:.2f}"'
    
    # Reemplazar viewBox
    if 'viewBox="' in svg:
        svg_nuevo = re.sub(r'viewBox="[^"]+"', viewbox_str, svg, count=1)
    else:
        svg_nuevo = re.sub(r'<svg', f'<svg {viewbox_str}', svg, count=1)

    # Reemplazar width y height por 100%
    svg_nuevo = re.sub(r'width="[^"]+"', 'width="100%"', svg_nuevo, count=1)
    svg_nuevo = re.sub(r'height="[^"]+"', 'height="100%"', svg_nuevo, count=1)

    # Asegurar preserveAspectRatio="xMidYMid meet"
    if 'preserveAspectRatio="' in svg_nuevo:
        svg_nuevo = re.sub(r'preserveAspectRatio="[^"]+"', 'preserveAspectRatio="xMidYMid meet"', svg_nuevo, count=1)
    else:
        svg_nuevo = re.sub(r'<svg', '<svg preserveAspectRatio="xMidYMid meet"', svg_nuevo, count=1)

    return svg_nuevo
