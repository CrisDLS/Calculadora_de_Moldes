import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from logic.geometria.abanico import Abanico
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno

@dataclass
class Transformacion2D:
    a: float
    b: float
    c: float
    d: float
    tx: float
    ty: float

    def transformar_punto(self, p: Tuple[float, float]) -> Tuple[float, float]:
        """Aplica la transformación afín a un punto (x, y)."""
        x, y = p
        return (
            self.a * x + self.c * y + self.tx,
            self.b * x + self.d * y + self.ty,
        )

    def inversa(self) -> "Transformacion2D":
        """Calcula la transformación inversa exacta."""
        det = self.a * self.d - self.b * self.c
        if abs(det) < 1e-12:
            raise ValueError("Transformación afín singular; no tiene inversa.")
        inv_det = 1.0 / det
        ia = self.d * inv_det
        ib = -self.b * inv_det
        ic = -self.c * inv_det
        id_ = self.a * inv_det
        itx = -(ia * self.tx + ic * self.ty)
        ity = -(ib * self.tx + id_ * self.ty)
        return Transformacion2D(ia, ib, ic, id_, itx, ity)

    def to_svg_matrix(self) -> str:
        return f"matrix({self.a:.6f} {self.b:.6f} {self.c:.6f} {self.d:.6f} {self.tx:.4f} {self.ty:.4f})"


def reflejo_del_abanico(abanico: Abanico, modo: str = "mitad") -> Transformacion2D:
    """Devuelve la transformación de reflejo respecto al eje central del abanico."""
    psi = abanico.pieza.angulo_abertura_rad
    n = abanico.n
    theta_0 = -(n - 1) / 2.0 * psi
    theta_fin = (n - 1) / 2.0 * psi
    theta_eje = (theta_0 + theta_fin) / 2.0  # 0.0 si está centrado

    if abs(theta_eje) < 1e-9:
        # Reflexión simple respecto a x=0
        return Transformacion2D(a=-1.0, b=0.0, c=0.0, d=1.0, tx=0.0, ty=0.0)
    else:
        # Reflexión respecto a una recta que pasa por el origen con ángulo theta_eje
        cos2 = math.cos(2.0 * theta_eje)
        sin2 = math.sin(2.0 * theta_eje)
        return Transformacion2D(a=-cos2, b=sin2, c=sin2, d=cos2, tx=0.0, ty=0.0)


def transformacion_a_gajo(abanico: Abanico, i: int) -> Transformacion2D:
    """Devuelve la transformación afín rígida que lleva coordenadas del abanico a la pieza canónica."""
    if i < 0 or i >= abanico.n:
        raise IndexError(f"Índice de gajo fuera de rango: {i} (n={abanico.n})")

    psi = abanico.pieza.angulo_abertura_rad
    theta_i = (i - (abanico.n - 1) / 2.0) * psi
    s0 = abanico.pieza.distancia_vertice

    cos_t = math.cos(theta_i)
    sin_t = math.sin(theta_i)

    # x_c = x * cos(t) - y * sin(t)
    # y_c = x * sin(t) + y * cos(t) - s0
    return Transformacion2D(
        a=cos_t,
        b=sin_t,
        c=-sin_t,
        d=cos_t,
        tx=0.0,
        ty=-s0,
    )


def recorte_gajo(
    abanico: Abanico,
    i: int,
    margen_costura: float = 0.0,
    sangrado: bool = True,
    pasos_arco: int = 8,
) -> List[Tuple[float, float]]:
    """Devuelve el polígono 2D del gajo i en coordenadas del abanico.
    
    Si sangrado=False, devuelve el contorno nominal idéntico al polígono del abanico.
    Si sangrado=True, ensancha margen_costura/2 por los laterales.
    """
    if not sangrado or margen_costura <= 1e-6:
        return list(abanico.poligonos[i])

    # Construir contorno canónico ensanchado y proyectarlo al abanico
    s0 = abanico.pieza.distancia_vertice
    largo = abanico.pieza.largo
    costura_mitad = margen_costura / 2.0

    t_inv = transformacion_a_gajo(abanico, i).inversa()

    pts_canon: List[Tuple[float, float]] = []

    if abanico.pieza.puntos_perfil:
        # Usar perfil exacto de la pieza
        pts_der = []
        pts_izq = []
        for l_acum, ancho_med in abanico.pieza.puntos_perfil:
            w = ancho_med + costura_mitad
            pts_der.append((w, l_acum))
            pts_izq.append((-w, l_acum))
        pts_canon = pts_der + list(reversed(pts_izq))
    else:
        # Modelo geométrico estándar
        w_max = abanico.pieza.ancho_mayor / 2.0 + costura_mitad
        w_min = abanico.pieza.ancho_menor / 2.0 + (costura_mitad if s0 > 1e-6 else 0.0)
        pts_canon = [
            (-w_min, 0.0),
            (w_min, 0.0),
            (w_max, largo),
            (-w_max, largo),
        ]

    # Transformar puntos canónicos a coordenadas del abanico
    return [t_inv.transformar_punto(p) for p in pts_canon]


def gajos_equivalentes(
    esquema: Optional[EsquemaDiseno],
    n: int,
) -> List[Tuple[int, bool, int]]:
    """Para cada gajo i en [0, n-1], devuelve (motivo, es_reflejo, indice_en_grupo)."""
    if esquema is None:
        return [(i, False, i) for i in range(n)]

    asignaciones = esquema.asignar(n)
    ciclo = esquema._generar_ciclo()
    tam_grupo = len(ciclo)

    resultado = []
    for i, asig in enumerate(asignaciones):
        resultado.append((asig.motivo, asig.espejo, i % tam_grupo))
    return resultado


def construir_grupo(
    diseno: Diseno,
    esquema: Optional[EsquemaDiseno] = None,
    modo_lienzo: str = "completo",
) -> List[CapaDiseno]:
    """Si modo_lienzo es 'mitad', duplica el diseño reflejado en la otra mitad."""
    if modo_lienzo != "mitad":
        return list(diseno.capas)

    capas_resultado: List[CapaDiseno] = []
    for capa in diseno.capas:
        capas_resultado.append(capa)
        # Capa reflejada respecto al eje de simetría vertical x=0
        capa_ref = CapaDiseno(
            id=f"{capa.id}_reflejo",
            nombre=f"{capa.nombre} (reflejo)",
            tipo=capa.tipo,
            archivo=capa.archivo,
            ancho_natural=capa.ancho_natural,
            alto_natural=capa.alto_natural,
            x=-capa.x - capa.ancho,
            y=capa.y,
            ancho=capa.ancho,
            alto=capa.alto,
            rotacion=-capa.rotacion,
            reflejo_h=not capa.reflejo_h,
            reflejo_v=capa.reflejo_v,
            opacidad=capa.opacidad,
            visible=capa.visible,
            bloqueada=capa.bloqueada,
        )
        capas_resultado.append(capa_ref)

    return capas_resultado
