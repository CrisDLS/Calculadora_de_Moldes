import math
from dataclasses import dataclass, field
from typing import List, Tuple
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


def area_poligono(puntos: List[Tuple[float, float]]) -> float:
    """Calcula el área de un polígono cerrado 2D usando la fórmula del área de Gauss (Shoelace)."""
    n = len(puntos)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = puntos[i]
        x2, y2 = puntos[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def contorno_abanico(
    pieza: PiezaPlana,
    n: int,
    dibujar: str = "completo",
    pasos_arco: int = 32,
) -> List[Tuple[float, float]]:
    """Devuelve los puntos del contorno exterior cerrado del abanico en cm.
    
    En 'completo', abarca simétricamente de -n*psi/2 a +n*psi/2 con ápice en (0, 0).
    En 'mitad', abarca estrictamente la mitad derecha (x >= 0, de 0 a +n*psi/2)
    con un borde izquierdo recto sobre el eje de simetría vertical x=0.
    """
    if n <= 0:
        raise ValueError(f"El número de gajos n debe ser mayor a 0, recibido: {n}")
    if dibujar not in ["completo", "mitad"]:
        raise ValueError(f"Modo no reconocido: {dibujar}. Use 'completo' o 'mitad'.")

    psi = pieza.angulo_abertura_rad
    s0 = pieza.distancia_vertice
    s1 = pieza.radio_arco
    ang_max = n * psi / 2.0
    es_pico = (pieza.seccion == "pico")

    pts: List[Tuple[float, float]] = []

    if dibujar == "completo":
        ang_min = -ang_max
        if s0 > 1e-6:
            # 1. Lateral izquierdo (s0 a s1 en ang_min)
            pts.append((s0 * math.sin(ang_min), s0 * math.cos(ang_min)))
            pts.append((s1 * math.sin(ang_min), s1 * math.cos(ang_min)))
            # 2. Arco exterior ancho (s1 de ang_min a ang_max)
            for st in range(1, 2 * pasos_arco + 1):
                ang = ang_min + (2 * ang_max) * (st / (2 * pasos_arco))
                pts.append((s1 * math.sin(ang), s1 * math.cos(ang)))
            # 3. Lateral derecho (s1 a s0 en ang_max)
            pts.append((s0 * math.sin(ang_max), s0 * math.cos(ang_max)))
            # 4. Borde interior estrecho (s0 de ang_max a ang_min)
            for st in range(1, 2 * pasos_arco + 1):
                ang = ang_max - (2 * ang_max) * (st / (2 * pasos_arco))
                pts.append((s0 * math.sin(ang), s0 * math.cos(ang)))
        else:
            # Cono superior o pico: ápice en (0, 0)
            pts.append((0.0, 0.0))
            pts.append((s1 * math.sin(ang_min), s1 * math.cos(ang_min)))
            if es_pico:
                # Bases rectas por cara
                for k in range(1, n + 1):
                    ang_k = ang_min + k * psi
                    pts.append((s1 * math.sin(ang_k), s1 * math.cos(ang_k)))
            else:
                for st in range(1, 2 * pasos_arco + 1):
                    ang = ang_min + (2 * ang_max) * (st / (2 * pasos_arco))
                    pts.append((s1 * math.sin(ang), s1 * math.cos(ang)))
            pts.append((0.0, 0.0))

    else:  # dibujar == "mitad"
        # Borde izquierdo recto sobre x=0 continuo
        if s0 > 1e-6:
            # De (0, s0) a (0, s1)
            pts.append((0.0, s0))
            pts.append((0.0, s1))
            # Arco exterior de 0 a +ang_max
            for st in range(1, pasos_arco + 1):
                ang = ang_max * (st / pasos_arco)
                pts.append((max(0.0, s1 * math.sin(ang)), s1 * math.cos(ang)))
            # Lateral derecho a s0
            pts.append((max(0.0, s0 * math.sin(ang_max)), s0 * math.cos(ang_max)))
            # Arco interior de +ang_max a 0
            for st in range(1, pasos_arco + 1):
                ang = ang_max * (1.0 - st / pasos_arco)
                pts.append((max(0.0, s0 * math.sin(ang)), s0 * math.cos(ang)))
        else:
            # Cono superior o pico:
            if es_pico:
                if n % 2 == 0:
                    y_top = s1
                    pts.append((0.0, 0.0))
                    pts.append((0.0, y_top))
                    # Caras derechas
                    for k in range(n // 2 + 1, n + 1):
                        ang_k = -ang_max + k * psi
                        pts.append((max(0.0, s1 * math.sin(ang_k)), s1 * math.cos(ang_k)))
                else:
                    y_top = s1 * math.cos(psi / 2.0)
                    pts.append((0.0, 0.0))
                    pts.append((0.0, y_top))
                    for k in range((n + 1) // 2, n + 1):
                        ang_k = -ang_max + k * psi
                        pts.append((max(0.0, s1 * math.sin(ang_k)), s1 * math.cos(ang_k)))
            else:
                pts.append((0.0, 0.0))
                pts.append((0.0, s1))
                for st in range(1, pasos_arco + 1):
                    ang = ang_max * (st / pasos_arco)
                    pts.append((max(0.0, s1 * math.sin(ang)), s1 * math.cos(ang)))
            pts.append((0.0, 0.0))

    return pts



