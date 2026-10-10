"""
Construcción de la malla 3D exacta del globo.

CONVENCIÓN DE LARGOS Y CONSISTENCIA GEOMÉTRICA:
El "largo" de las piezas (l_sup, l_inf, l_pico) generado por la calculadora corresponde al
EJE CENTRAL de la pieza (la altura del triángulo o trapecio plano), NO a los bordes laterales.
Por lo tanto, la malla usa el apotema del polígono (la distancia del centro al punto medio 
del segmento, R_apo) en lugar del circunradio (R) para calcular las alturas 3D, garantizando 
que el eje de cada cara mida exactamente l_sup/l_inf, y que su área plana sin costura sea 
idéntica a su área 3D.
- h_sup = sqrt(l_sup² - R_apo²)
- h_inf = sqrt(l_inf² - (R_apo - Rb_apo)²)
- h_p = sqrt(l_pico² - (a/2)²) (desplazamiento del ápice de la pirámide hacia afuera)

DIFERENCIA CON LA CALCULADORA:
La calculadora estima las dimensiones globales asumiendo que el globo es un círculo perfecto 
(circunferencia = N * a). La malla modela el polígono exacto (N lados rectos).
Debido a esta aproximación, la calculadora subestima ligeramente el radio y, por lo tanto, 
sobreestima la pérdida de altura por curvatura. Como resultado, la altura armada estimada 
por la calculadora (~703.8 cm para 950/30/2/1) y la Z máxima de la malla (~706.3 cm) 
difieren en un ~0.35 %. Esto es esperado y no requiere alterar la calculadora.
"""
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from logic.models import BalloonInput, BalloonCalculationResult

@dataclass
class Cara:
    indices_vertices: List[int]
    seccion: str  # "inferior", "pico", "superior"
    gajo: int
    hilera: Optional[int]
    sub: Optional[int]
    normal: List[float]
    uv_cm: List[Tuple[float, float]]

@dataclass
class Malla:
    vertices: List[Tuple[float, float, float]]
    caras: List[Cara]
    anillos: Dict[str, Any]

def normal_triangulo(v0, v1, v2):
    # Vector unitario normal a 3 vértices
    u = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
    v = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    m = math.hypot(nx, ny, nz)
    if m == 0:
        return [0.0, 0.0, 0.0]
    return [nx/m, ny/m, nz/m]

def construir_malla(entrada: BalloonInput, resultado: BalloonCalculationResult) -> Malla:
    N = entrada.num_gajos
    a = resultado.ancho_max_gajo
    
    # Ancho de la boca (tomar del resultado calculado si es modo simple, o del objeto boca)
    if entrada.usar_parametros_avanzados and resultado.boca:
        ab = resultado.boca.ancho_por_gajo
    else:
        # En modo simple, calcular diametro o circunferencia de la boquilla
        d_boca = resultado.diametro_boquilla_calculado
        ab = math.pi * d_boca / N

    # Radios del polígono exacto
    sin_pi_N = math.sin(math.pi / N)
    R = a / (2 * sin_pi_N)
    Rb = ab / (2 * sin_pi_N)

    l_sup = resultado.seccion_superior.generatriz_total
    l_inf = resultado.seccion_inferior.generatriz_total
    l_pico = resultado.seccion_picos.generatriz_total

    # Alturas usando la apotema para que el largo de las piezas coincida
    # con la altura 3D de las caras (y así cuadre el área l_inf * (a+ab)/2).
    # La instrucción original decía R, pero R es el radio al vértice.
    R_apo = R * math.cos(math.pi / N)
    Rb_apo = Rb * math.cos(math.pi / N)
    
    h_sup = math.sqrt(l_sup**2 - R_apo**2) if l_sup > R_apo else 0.0
    h_inf = math.sqrt(l_inf**2 - (R_apo - Rb_apo)**2) if l_inf > abs(R_apo - Rb_apo) else 0.0
    
    hileras = entrada.num_hileras_picos

    vertices = []
    
    def add_v(r, z, k_angle):
        theta = 2 * math.pi * k_angle / N
        vertices.append((r * math.cos(theta), r * math.sin(theta), z))
        return len(vertices) - 1

    # 1. Anillos
    idx_boca = [add_v(Rb, 0.0, k) for k in range(N)]
    
    anillos_picos = []
    z_curr = h_inf
    for j in range(hileras + 1):
        anillos_picos.append([add_v(R, z_curr, k) for k in range(N)])
        z_curr += a
    
    z_apex = h_inf + hileras * a + h_sup
    idx_apex = add_v(0.0, z_apex, 0.0)
    
    # 2. Picos (ápices de pirámides)
    idx_apices_piramides = {}
    h_p = math.sqrt(l_pico**2 - (a/2)**2) if l_pico > a/2 else 0.0
    
    for j in range(hileras):
        for k in range(N):
            # Centro del cuadrado (desplazado hacia afuera normal a la cara)
            theta_c = 2 * math.pi * (k + 0.5) / N
            r_c = R * math.cos(math.pi / N) + h_p
            z_c = h_inf + j * a + a/2
            vertices.append((r_c * math.cos(theta_c), r_c * math.sin(theta_c), z_c))
            idx_apices_piramides[(j, k)] = len(vertices) - 1

    caras = []

    # Generar caras
    for k in range(N):
        k_next = (k + 1) % N
        
        # Cono inferior (Trapecio)
        v0 = idx_boca[k]
        v1 = idx_boca[k_next]
        v2 = anillos_picos[0][k_next]
        v3 = anillos_picos[0][k]
        n_inf = normal_triangulo(vertices[v0], vertices[v1], vertices[v2])
        uv_inf = [(-ab/2, 0.0), (ab/2, 0.0), (a/2, l_inf), (-a/2, l_inf)]
        caras.append(Cara([v0, v1, v2, v3], "inferior", k, None, None, n_inf, uv_inf))

        # Cono superior (Triángulo)
        v4 = anillos_picos[hileras][k]
        v5 = anillos_picos[hileras][k_next]
        v6 = idx_apex
        n_sup = normal_triangulo(vertices[v4], vertices[v5], vertices[v6])
        uv_sup = [(-a/2, l_sup), (a/2, l_sup), (0.0, 0.0)]
        caras.append(Cara([v4, v5, v6], "superior", k, None, None, n_sup, uv_sup))

        # Picos (Pirámides)
        for j in range(hileras):
            bl = anillos_picos[j][k]
            br = anillos_picos[j][k_next]
            tr = anillos_picos[j+1][k_next]
            tl = anillos_picos[j+1][k]
            apex = idx_apices_piramides[(j, k)]

            uv_base = [(-a/2, l_pico), (a/2, l_pico), (0.0, 0.0)]
            
            n0 = normal_triangulo(vertices[bl], vertices[br], vertices[apex])
            caras.append(Cara([bl, br, apex], "pico", k, j, 0, n0, uv_base))
            
            n1 = normal_triangulo(vertices[br], vertices[tr], vertices[apex])
            caras.append(Cara([br, tr, apex], "pico", k, j, 1, n1, uv_base))
            
            n2 = normal_triangulo(vertices[tr], vertices[tl], vertices[apex])
            caras.append(Cara([tr, tl, apex], "pico", k, j, 2, n2, uv_base))
            
            n3 = normal_triangulo(vertices[tl], vertices[bl], vertices[apex])
            caras.append(Cara([tl, bl, apex], "pico", k, j, 3, n3, uv_base))

    anillos_dict = {
        "boca": idx_boca,
        "picos": anillos_picos,
        "apex": idx_apex,
        "r_cuerpo": R,
        "rb_boca": Rb
    }

    return Malla(vertices, caras, anillos_dict)

def malla_a_dict(malla: Malla) -> Dict[str, Any]:
    return {
        "vertices": [[float(x), float(y), float(z)] for x, y, z in malla.vertices],
        "caras": [{
            "indices_vertices": c.indices_vertices,
            "seccion": c.seccion,
            "gajo": c.gajo,
            "hilera": c.hilera,
            "sub": c.sub,
            "normal": c.normal,
            "uv_cm": [[float(u), float(v)] for u, v in c.uv_cm]
        } for c in malla.caras],
        "anillos": malla.anillos
    }
