import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from logic.models import BalloonInput, BalloonCalculationResult

@dataclass
class PiezaPlana:
    seccion: str  # "superior" | "pico" | "inferior"
    largo: float  # cm (largo del eje)
    ancho_mayor: float  # cm (ancho de gajo a)
    ancho_menor: float  # cm (0 en superior/pico, ab en inferior)
    distancia_vertice: float  # s_0 (cm)
    radio_arco: float         # s_1 = s_0 + largo (cm)
    angulo_abertura_rad: float # psi (radianes)
    puntos_perfil: List[Tuple[float, float]] = field(default_factory=list)  # [(y, semiancho), ...]

@dataclass
class Abanico:
    pieza: PiezaPlana
    n: int
    poligonos: List[List[Tuple[float, float]]]
    aristas_comunes: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    ejes: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    caja_min_x: float
    caja_min_y: float
    caja_max_x: float
    caja_max_y: float
    ancho_total: float
    alto_total: float
    pasos_radiales: List[float] = field(default_factory=list)

def pieza_a_geometria_plana(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    seccion: str
) -> PiezaPlana:
    """Calcula los parámetros geométricos planos para construir el abanico."""
    if seccion == "superior":
        sec_res = resultado.seccion_superior
        largo = sec_res.generatriz_total
        ancho_mayor = resultado.ancho_max_gajo
        ancho_menor = 0.0
        s0 = 0.0
    elif seccion == "inferior":
        sec_res = resultado.seccion_inferior
        largo = sec_res.generatriz_total
        ancho_mayor = resultado.ancho_max_gajo
        ancho_menor = resultado.circumferencia_boquilla / entrada.num_gajos
        dif = ancho_mayor - ancho_menor
        if dif > 1e-6:
            s0 = largo * ancho_menor / dif
        else:
            s0 = 0.0
    elif seccion == "pico":
        sec_res = resultado.seccion_picos
        largo = sec_res.generatriz_total
        ancho_mayor = resultado.ancho_max_gajo
        ancho_menor = 0.0
        s0 = 0.0
    else:
        raise ValueError(f"Sección no reconocida para geometría plana: {seccion}")

    s1 = s0 + largo
    psi = 2.0 * math.atan((ancho_mayor / 2.0) / s1)

    pts = [(p.largo_acumulado, p.ancho_medio) for p in sec_res.puntos]

    return PiezaPlana(
        seccion=seccion,
        largo=largo,
        ancho_mayor=ancho_mayor,
        ancho_menor=ancho_menor,
        distancia_vertice=s0,
        radio_arco=s1,
        angulo_abertura_rad=psi,
        puntos_perfil=pts,
    )

def abanico(
    pieza: PiezaPlana,
    n: int,
    centrado: bool = True,
    pasos_arco: int = 8
) -> Abanico:
    """Construye la geometría plana de n gajos en abanico unidos por aristas comunes.
    
    Ápice / vértice virtual en el origen (0, 0), con eje general hacia +y.
    El gajo i tiene un ángulo de rotación theta_i = (i - (n - 1) / 2) * psi si centrado=True.
    """
    if n <= 0:
        raise ValueError(f"El número de gajos n debe ser mayor a 0, recibido: {n}")

    psi = pieza.angulo_abertura_rad
    s0 = pieza.distancia_vertice
    s1 = pieza.radio_arco

    poligonos: List[List[Tuple[float, float]]] = []
    aristas_comunes: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    ejes: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

    # Lista de radios de los pasos intermedios para referencia de trazo
    pasos_radiales = [s0 + p[0] for p in pieza.puntos_perfil]

    for i in range(n):
        if centrado:
            theta_i = (i - (n - 1) / 2.0) * psi
        else:
            theta_i = (i + 0.5) * psi

        # Segmento de eje
        p_eje_0 = (s0 * math.sin(theta_i), s0 * math.cos(theta_i))
        p_eje_1 = (s1 * math.sin(theta_i), s1 * math.cos(theta_i))
        ejes.append((p_eje_0, p_eje_1))

        # Límites angulares del gajo i
        alpha_izq = theta_i - psi / 2.0
        alpha_der = theta_i + psi / 2.0

        pts_gajo: List[Tuple[float, float]] = []

        if s0 > 1e-6:
            # Cono inferior: extremo estrecho (s0), lateral derecho, extremo ancho (s1), lateral izquierdo
            # 1. Borde estrecho de izq a der a radio s0
            for step in range(pasos_arco + 1):
                ang = alpha_izq + (alpha_der - alpha_izq) * (step / pasos_arco)
                pts_gajo.append((s0 * math.sin(ang), s0 * math.cos(ang)))
            # 2. Borde exterior ancho de der a izq a radio s1
            for step in range(pasos_arco + 1):
                ang = alpha_der - (alpha_der - alpha_izq) * (step / pasos_arco)
                pts_gajo.append((s1 * math.sin(ang), s1 * math.cos(ang)))
        else:
            # Cono superior o pico: ápice en (0, 0)
            pts_gajo.append((0.0, 0.0))
            if pieza.seccion == "pico":
                # En pirámides (pico), la base de cada cara es un segmento recto
                p_ancho_der = (s1 * math.sin(alpha_der), s1 * math.cos(alpha_der))
                p_ancho_izq = (s1 * math.sin(alpha_izq), s1 * math.cos(alpha_izq))
                pts_gajo.append(p_ancho_der)
                pts_gajo.append(p_ancho_izq)
            else:
                # Cono superior: arco exterior discretizado
                for step in range(pasos_arco + 1):
                    ang = alpha_der - (alpha_der - alpha_izq) * (step / pasos_arco)
                    pts_gajo.append((s1 * math.sin(ang), s1 * math.cos(ang)))

        poligonos.append(pts_gajo)

        # Aristas comunes entre gajo i y gajo i+1
        if i < n - 1:
            ang_comun = alpha_der
            p_comun_0 = (s0 * math.sin(ang_comun), s0 * math.cos(ang_comun))
            p_comun_1 = (s1 * math.sin(ang_comun), s1 * math.cos(ang_comun))
            aristas_comunes.append((p_comun_0, p_comun_1))

    # Bounding box
    todos_pts: List[Tuple[float, float]] = []
    for poli in poligonos:
        todos_pts.extend(poli)
    for seg in aristas_comunes:
        todos_pts.extend([seg[0], seg[1]])
    for seg in ejes:
        todos_pts.extend([seg[0], seg[1]])

    min_x = min(p[0] for p in todos_pts)
    max_x = max(p[0] for p in todos_pts)
    min_y = min(p[1] for p in todos_pts)
    max_y = max(p[1] for p in todos_pts)

    return Abanico(
        pieza=pieza,
        n=n,
        poligonos=poligonos,
        aristas_comunes=aristas_comunes,
        ejes=ejes,
        caja_min_x=min_x,
        caja_min_y=min_y,
        caja_max_x=max_x,
        caja_max_y=max_y,
        ancho_total=max_x - min_x,
        alto_total=max_y - min_y,
        pasos_radiales=pasos_radiales,
    )
