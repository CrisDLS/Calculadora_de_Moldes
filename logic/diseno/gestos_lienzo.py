"""Módulo de conversiones de coordenadas y geometría de manipulación de capas.

Lógica matemática pura (sin dependencias de interfaz de usuario) para:
- Conversión bidireccional entre coordenadas de pantalla (px) y plano (cm).
- Regla preserveAspectRatio="xMidYMid meet" idéntica al visor vectorial SVG.
- Cálculo de esquinas y 8 tiradores de la capa en coordenadas del plano.
- Traslación, estiramiento con borde/esquina opuesta fija y rotación.
"""

from dataclasses import replace
import math
from typing import Dict, List, Optional, Tuple, Union

from logic.diseno.lienzo import CapaDiseno
from logic.exportacion.vista_svg import VistaSvg


class Conversion:
    """Conversión bidireccional entre coordenadas de pantalla (px) y del plano (cm).

    Implementa la regla de encaje preserveAspectRatio="xMidYMid meet":
    - Escala uniforme: s = min(ancho_px / ancho_vista, alto_px / alto_vista)
    - Centrado simétrico (bandas vacías):
        dx_offset = (ancho_px - ancho_vista * s) / 2.0
        dy_offset = (alto_px - alto_vista * s) / 2.0

    Convención del eje vertical:
    En el plano del abanico del globo (geometría de piezas), el ápice se ubica
    en el origen y +y apunta hacia arriba (alejándose del ápice hacia el arco s1).
    En la pantalla (Flutter/Flet) y en coordenadas SVG nativas, el origen (0,0)
    se ubica en la esquina superior izquierda y +y apunta hacia abajo.
    Por lo tanto, con y_arriba=True:
    - delta_plano_y = -dy_px / px_por_cm
    - Al mover el cursor hacia arriba (dy_px < 0), la coordenada y del plano
      aumenta (delta_plano_y > 0) y la capa sube en la pantalla.
    """

    def __init__(
        self,
        vista: VistaSvg,
        zona_px: Tuple[float, float],
        y_arriba: bool = True,
        factor_escala: float = 1.0,
        cx_vista: float = 0.0,
        cy_vista: float = 0.0,
        y_mid_plano: float = 0.0,
    ):
        """Inicializa la conversión.

        Args:
            vista: VistaSvg con la región visible en coordenadas de la vista.
            zona_px: Tupla (ancho, alto) de la zona del visor en píxeles.
            y_arriba: Si True, +y en el plano apunta hacia arriba.
            factor_escala: Unidades de la vista por cada cm del plano (ej. mm_svg / cm_plano).
                           1.0 si la vista ya está en cm o en escala 1:1.
            cx_vista: Centro X de la proyección del plano en la vista (mm).
            cy_vista: Centro Y de la proyección del plano en la vista (mm).
            y_mid_plano: Valor central Y del plano proyectado en cy_vista (cm).
        """
        self.vista = vista
        self.zona_w = max(1.0, float(zona_px[0]))
        self.zona_h = max(1.0, float(zona_px[1]))
        self.y_arriba = bool(y_arriba)

        self.factor_escala = max(1e-9, float(factor_escala))
        self.cx_vista = float(cx_vista)
        self.cy_vista = float(cy_vista)
        self.y_mid_plano = float(y_mid_plano)

        vw = max(1e-6, self.vista.ancho)
        vh = max(1e-6, self.vista.alto)

        # Regla preserveAspectRatio="xMidYMid meet"
        self._s = min(self.zona_w / vw, self.zona_h / vh)
        self._dx = (self.zona_w - vw * self._s) / 2.0
        self._dy = (self.zona_h - vh * self._s) / 2.0

        # Píxeles de pantalla por cada centímetro del plano
        self._px_por_cm = self._s * self.factor_escala

    @property
    def px_por_cm(self) -> float:
        """Píxeles de pantalla correspondientes a 1 centímetro en el plano."""
        return self._px_por_cm

    @property
    def escala_visor(self) -> float:
        """Escala uniforme en px por unidad de la vista (viewBox)."""
        return self._s

    @property
    def margen_x_px(self) -> float:
        """Desplazamiento horizontal de centrado (banda izquierda) en px."""
        return self._dx

    @property
    def margen_y_px(self) -> float:
        """Desplazamiento vertical de centrado (banda superior) en px."""
        return self._dy

    def plano_a_vista(self, x: float, y: float) -> Tuple[float, float]:
        """Convierte coordenadas del plano (cm) al sistema de coordenadas de la vista."""
        xs = self.cx_vista + x * self.factor_escala
        if self.y_arriba:
            ys = self.cy_vista - (y - self.y_mid_plano) * self.factor_escala
        else:
            ys = self.cy_vista + (y - self.y_mid_plano) * self.factor_escala
        return xs, ys

    def vista_a_plano(self, xs: float, ys: float) -> Tuple[float, float]:
        """Convierte coordenadas del sistema de la vista al plano (cm)."""
        x = (xs - self.cx_vista) / self.factor_escala
        if self.y_arriba:
            y = self.y_mid_plano - (ys - self.cy_vista) / self.factor_escala
        else:
            y = self.y_mid_plano + (ys - self.cy_vista) / self.factor_escala
        return x, y

    def plano_a_px(self, x: float, y: float) -> Tuple[float, float]:
        """Transforma un punto del plano (cm) a coordenadas de pantalla (px)."""
        xs, ys = self.plano_a_vista(x, y)
        px = self._dx + (xs - self.vista.x) * self._s
        py = self._dy + (ys - self.vista.y) * self._s
        return px, py

    def px_a_plano(self, px: float, py: float) -> Tuple[float, float]:
        """Transforma un punto de pantalla (px) a coordenadas del plano (cm)."""
        xs = self.vista.x + (px - self._dx) / self._s
        ys = self.vista.y + (py - self._dy) / self._s
        return self.vista_a_plano(xs, ys)

    def delta_px_a_plano(self, dx_px: float, dy_px: float) -> Tuple[float, float]:
        """Convierte un vector diferencial de pantalla (px) al plano (cm).

        Si y_arriba es True, dy_plano se invierte para que arrastrar hacia arriba
        en pantalla (dy_px < 0) resulte en un desplazamiento positivo en el plano.
        """
        dx_plano = dx_px / self._px_por_cm
        if self.y_arriba:
            dy_plano = -dy_px / self._px_por_cm
        else:
            dy_plano = dy_px / self._px_por_cm
        return dx_plano, dy_plano

    def delta_plano_a_px(self, dx_plano: float, dy_plano: float) -> Tuple[float, float]:
        """Convierte un vector diferencial del plano (cm) a pantalla (px)."""
        dx_px = dx_plano * self._px_por_cm
        if self.y_arriba:
            dy_px = -dy_plano * self._px_por_cm
        else:
            dy_px = dy_plano * self._px_por_cm
        return dx_px, dy_px


# ==============================================================================
# Geometría de la Capa (Lógica Pura)
# ==============================================================================


def centro_capa(capa: CapaDiseno) -> Tuple[float, float]:
    """Retorna el centro (cx, cy) de la capa en coordenadas del plano (cm)."""
    return capa.x + capa.ancho / 2.0, capa.y + capa.alto / 2.0


def ejes_locales(rotacion_grados: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Calcula los vectores unitarios u (+X local, ancho) y v (+Y local, alto)."""
    rad = math.radians(rotacion_grados)
    u = (math.cos(rad), math.sin(rad))
    v = (-math.sin(rad), math.cos(rad))
    return u, v


def esquinas_capa(capa: CapaDiseno) -> Dict[str, Tuple[float, float]]:
    """Calcula las 4 esquinas de la caja de la capa en el plano con rotación.

    Retorna un diccionario con claves:
      'tl': superior-izquierda (top-left)
      'tr': superior-derecha (top-right)
      'br': inferior-derecha (bottom-right)
      'bl': inferior-izquierda (bottom-left)
    """
    cx, cy = centro_capa(capa)
    u, v = ejes_locales(capa.rotacion)
    w2 = capa.ancho / 2.0
    h2 = capa.alto / 2.0

    return {
        "tl": (cx - w2 * u[0] + h2 * v[0], cy - w2 * u[1] + h2 * v[1]),
        "tr": (cx + w2 * u[0] + h2 * v[0], cy + w2 * u[1] + h2 * v[1]),
        "br": (cx + w2 * u[0] - h2 * v[0], cy + w2 * u[1] - h2 * v[1]),
        "bl": (cx - w2 * u[0] - h2 * v[0], cy - w2 * u[1] - h2 * v[1]),
    }


def tiradores(
    capa: CapaDiseno,
    incluir_rotacion: bool = True,
    dist_rot_cm: float = 2.0,
) -> Dict[str, Tuple[float, float]]:
    """Calcula las posiciones de los tiradores de manipulación en el plano (cm).

    Tiradores devueltos:
      - 4 esquinas: 'tl', 'tr', 'br', 'bl'
      - 4 lados: 't' (arriba), 'r' (derecha), 'b' (abajo), 'l' (izquierda)
      - Opcional 'rot': tirador de rotación ubicado por encima de 't'.
    """
    cx, cy = centro_capa(capa)
    u, v = ejes_locales(capa.rotacion)
    w2 = capa.ancho / 2.0
    h2 = capa.alto / 2.0

    res = {
        "tl": (cx - w2 * u[0] + h2 * v[0], cy - w2 * u[1] + h2 * v[1]),
        "t": (cx + h2 * v[0], cy + h2 * v[1]),
        "tr": (cx + w2 * u[0] + h2 * v[0], cy + w2 * u[1] + h2 * v[1]),
        "r": (cx + w2 * u[0], cy + w2 * u[1]),
        "br": (cx + w2 * u[0] - h2 * v[0], cy + w2 * u[1] - h2 * v[1]),
        "b": (cx - h2 * v[0], cy - h2 * v[1]),
        "bl": (cx - w2 * u[0] - h2 * v[0], cy - w2 * u[1] - h2 * v[1]),
        "l": (cx - w2 * u[0], cy - w2 * u[1]),
    }

    if incluir_rotacion:
        res["rot"] = (cx + (h2 + dist_rot_cm) * v[0], cy + (h2 + dist_rot_cm) * v[1])

    return res


def mover(capa: CapaDiseno, delta_plano: Tuple[float, float]) -> CapaDiseno:
    """Desplaza la capa por un delta (dx, dy) en centímetros del plano."""
    dx, dy = delta_plano
    return replace(capa, x=capa.x + dx, y=capa.y + dy)


def _ajustar_dimensiones_esquina(
    w_cand: float,
    h_cand: float,
    w0: float,
    h0: float,
    mantener_proporcion: bool,
    minimo_cm: float,
) -> Tuple[float, float]:
    """Ajusta las dimensiones de una esquina considerando proporción y tamaño mínimo."""
    if not mantener_proporcion:
        w = max(minimo_cm, w_cand)
        h = max(minimo_cm, h_cand)
        return w, h

    aspecto = w0 / h0 if h0 > 0 else 1.0

    # Proyección ortogonal por mínimos cuadrados sobre la recta w = aspecto * h
    denom = aspecto * aspecto + 1.0
    h = (w_cand * aspecto + h_cand) / denom
    w = h * aspecto

    # Limitar en el tamaño mínimo sin romper la relación de aspecto
    if w < minimo_cm or h < minimo_cm:
        h_min = max(minimo_cm, minimo_cm / aspecto)
        h = h_min
        w = h * aspecto

    return w, h


def estirar(
    capa: CapaDiseno,
    tirador: str,
    delta_plano: Tuple[float, float],
    mantener_proporcion: bool = False,
    minimo_cm: float = 1.0,
) -> CapaDiseno:
    """Redimensiona la capa manteniendo fija la esquina o borde opuesto en el plano.

    Args:
        capa: Capa a estirar.
        tirador: Identificador del tirador:
                 Esquinas: 'tl', 'tr', 'br', 'bl'
                 Lados: 't', 'b', 'r', 'l'
        delta_plano: Desplazamiento (dx, dy) en cm en coordenadas globales del plano.
        mantener_proporcion: Si True (en esquinas), conserva el aspecto original w/h.
        minimo_cm: Dimensión mínima en cm para ancho y alto (evita inversión).
    """
    t_id = tirador.lower().strip()
    sinonimos = {
        "top": "t",
        "bottom": "b",
        "left": "l",
        "right": "r",
        "tc": "t",
        "bc": "b",
        "ml": "l",
        "mr": "r",
        "top_left": "tl",
        "top_right": "tr",
        "bottom_left": "bl",
        "bottom_right": "br",
    }
    t_id = sinonimos.get(t_id, t_id)

    w0 = capa.ancho
    h0 = capa.alto
    w2 = w0 / 2.0
    h2 = h0 / 2.0
    cx, cy = centro_capa(capa)
    u, v = ejes_locales(capa.rotacion)

    # Proyección del delta global en los ejes locales u (+X) y v (+Y)
    dx_g, dy_g = delta_plano
    du = dx_g * u[0] + dy_g * u[1]
    dv = dx_g * v[0] + dy_g * v[1]

def _estirar_lado(
    t_id: str,
    w0: float,
    h0: float,
    cx: float,
    cy: float,
    u: Tuple[float, float],
    v: Tuple[float, float],
    du: float,
    dv: float,
    minimo_cm: float,
) -> Tuple[float, float, float, float]:
    """Calcula (w_final, h_final, cx_nuevo, cy_nuevo) para un tirador de lado."""
    w2 = w0 / 2.0
    h2 = h0 / 2.0
    if t_id == "r":
        p_fijo_x = cx - w2 * u[0]
        p_fijo_y = cy - w2 * u[1]
        w_final = max(minimo_cm, w0 + du)
        h_final = h0
        cx_nuevo = p_fijo_x + (w_final / 2.0) * u[0]
        cy_nuevo = p_fijo_y + (w_final / 2.0) * u[1]
    elif t_id == "l":
        p_fijo_x = cx + w2 * u[0]
        p_fijo_y = cy + w2 * u[1]
        w_final = max(minimo_cm, w0 - du)
        h_final = h0
        cx_nuevo = p_fijo_x - (w_final / 2.0) * u[0]
        cy_nuevo = p_fijo_y - (w_final / 2.0) * u[1]
    elif t_id == "t":
        p_fijo_x = cx - h2 * v[0]
        p_fijo_y = cy - h2 * v[1]
        w_final = w0
        h_final = max(minimo_cm, h0 + dv)
        cx_nuevo = p_fijo_x + (h_final / 2.0) * v[0]
        cy_nuevo = p_fijo_y + (h_final / 2.0) * v[1]
    else:  # "b"
        p_fijo_x = cx + h2 * v[0]
        p_fijo_y = cy + h2 * v[1]
        w_final = w0
        h_final = max(minimo_cm, h0 - dv)
        cx_nuevo = p_fijo_x - (h_final / 2.0) * v[0]
        cy_nuevo = p_fijo_y - (h_final / 2.0) * v[1]
    return w_final, h_final, cx_nuevo, cy_nuevo


def _estirar_esquina(
    t_id: str,
    w0: float,
    h0: float,
    cx: float,
    cy: float,
    u: Tuple[float, float],
    v: Tuple[float, float],
    du: float,
    dv: float,
    mantener_proporcion: bool,
    minimo_cm: float,
) -> Tuple[float, float, float, float]:
    """Calcula (w_final, h_final, cx_nuevo, cy_nuevo) para un tirador de esquina."""
    w2 = w0 / 2.0
    h2 = h0 / 2.0
    if t_id == "tr":
        p_fijo_x = cx - w2 * u[0] - h2 * v[0]
        p_fijo_y = cy - w2 * u[1] - h2 * v[1]
        w_f, h_f = _ajustar_dimensiones_esquina(
            w0 + du, h0 + dv, w0, h0, mantener_proporcion, minimo_cm
        )
        cx_n = p_fijo_x + (w_f / 2.0) * u[0] + (h_f / 2.0) * v[0]
        cy_n = p_fijo_y + (w_f / 2.0) * u[1] + (h_f / 2.0) * v[1]
    elif t_id == "bl":
        p_fijo_x = cx + w2 * u[0] + h2 * v[0]
        p_fijo_y = cy + w2 * u[1] + h2 * v[1]
        w_f, h_f = _ajustar_dimensiones_esquina(
            w0 - du, h0 - dv, w0, h0, mantener_proporcion, minimo_cm
        )
        cx_n = p_fijo_x - (w_f / 2.0) * u[0] - (h_f / 2.0) * v[0]
        cy_n = p_fijo_y - (w_f / 2.0) * u[1] - (h_f / 2.0) * v[1]
    elif t_id == "tl":
        p_fijo_x = cx + w2 * u[0] - h2 * v[0]
        p_fijo_y = cy + w2 * u[1] - h2 * v[1]
        w_f, h_f = _ajustar_dimensiones_esquina(
            w0 - du, h0 + dv, w0, h0, mantener_proporcion, minimo_cm
        )
        cx_n = p_fijo_x - (w_f / 2.0) * u[0] + (h_f / 2.0) * v[0]
        cy_n = p_fijo_y - (w_f / 2.0) * u[1] + (h_f / 2.0) * v[1]
    else:  # "br"
        p_fijo_x = cx - w2 * u[0] + h2 * v[0]
        p_fijo_y = cy - w2 * u[1] + h2 * v[1]
        w_f, h_f = _ajustar_dimensiones_esquina(
            w0 + du, h0 - dv, w0, h0, mantener_proporcion, minimo_cm
        )
        cx_n = p_fijo_x + (w_f / 2.0) * u[0] - (h_f / 2.0) * v[0]
        cy_n = p_fijo_y + (w_f / 2.0) * u[1] - (h_f / 2.0) * v[1]
    return w_f, h_f, cx_n, cy_n


def estirar(
    capa: CapaDiseno,
    tirador: str,
    delta_plano: Tuple[float, float],
    mantener_proporcion: bool = False,
    minimo_cm: float = 1.0,
) -> CapaDiseno:
    """Redimensiona la capa manteniendo fija la esquina o borde opuesto en el plano.

    Args:
        capa: Capa a estirar.
        tirador: Identificador del tirador:
                 Esquinas: 'tl', 'tr', 'br', 'bl'
                 Lados: 't', 'b', 'r', 'l'
        delta_plano: Desplazamiento (dx, dy) en cm en coordenadas globales del plano.
        mantener_proporcion: Si True (en esquinas), conserva el aspecto original w/h.
        minimo_cm: Dimensión mínima en cm para ancho y alto (evita inversión).
    """
    t_id = tirador.lower().strip()
    sinonimos = {
        "top": "t",
        "bottom": "b",
        "left": "l",
        "right": "r",
        "tc": "t",
        "bc": "b",
        "ml": "l",
        "mr": "r",
        "top_left": "tl",
        "top_right": "tr",
        "bottom_left": "bl",
        "bottom_right": "br",
    }
    t_id = sinonimos.get(t_id, t_id)

    w0 = capa.ancho
    h0 = capa.alto
    cx, cy = centro_capa(capa)
    u, v = ejes_locales(capa.rotacion)

    # Proyección del delta global en los ejes locales u (+X) y v (+Y)
    dx_g, dy_g = delta_plano
    du = dx_g * u[0] + dy_g * u[1]
    dv = dx_g * v[0] + dy_g * v[1]

    if t_id in ("r", "l", "t", "b"):
        w_final, h_final, cx_nuevo, cy_nuevo = _estirar_lado(
            t_id, w0, h0, cx, cy, u, v, du, dv, minimo_cm
        )
    elif t_id in ("tr", "bl", "tl", "br"):
        w_final, h_final, cx_nuevo, cy_nuevo = _estirar_esquina(
            t_id, w0, h0, cx, cy, u, v, du, dv, mantener_proporcion, minimo_cm
        )
    else:
        raise ValueError(
            f"Tirador no reconocido: '{tirador}'. Use 'tl', 'tr', 'br', 'bl', 't', 'b', 'r' o 'l'."
        )

    return replace(
        capa,
        ancho=round(w_final, 4),
        alto=round(h_final, 4),
        x=round(cx_nuevo - w_final / 2.0, 4),
        y=round(cy_nuevo - h_final / 2.0, 4),
    )


def rotar(
    capa: CapaDiseno,
    punto_plano: Tuple[float, float],
    paso_grados: Optional[float] = None,
) -> CapaDiseno:
    """Calcula el nuevo ángulo de rotación de la capa orientando su eje superior hacia el cursor.

    Args:
        capa: Capa a rotar.
        punto_plano: Posición (px, py) en el plano hacia la que apunta el cursor.
        paso_grados: Si se especifica (ej. 15.0), ajusta el ángulo a múltiplos de este valor.
    """
    cx, cy = centro_capa(capa)
    px, py = punto_plano
    dx = px - cx
    dy = py - cy
    if math.hypot(dx, dy) < 1e-6:
        return capa

    # Ángulo matemático en el plano desde el centro hacia el cursor
    alfa_deg = math.degrees(math.atan2(dy, dx))
    # El tirador de rotación está en +Y local (+90° respecto a +X local)
    nueva_rot = alfa_deg - 90.0

    # Normalizar a (-180, 180]
    while nueva_rot <= -180.0:
        nueva_rot += 360.0
    while nueva_rot > 180.0:
        nueva_rot -= 360.0

    if paso_grados is not None and paso_grados > 0:
        nueva_rot = round(nueva_rot / paso_grados) * paso_grados
        while nueva_rot <= -180.0:
            nueva_rot += 360.0
        while nueva_rot > 180.0:
            nueva_rot -= 360.0

    return replace(capa, rotacion=round(nueva_rot, 2))
