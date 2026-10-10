""" 
1. Modelos de Datos 
Este archivo define qué datos entran y salen, sin importar cómo se calculan. 
Usaremos dataclasses de Python para un código limpio.

OJO: `altura_cuerpo` ahora significa LARGO TOTAL DE PAPEL (cono superior + picos + cono
inferior) medido sobre la superficie, no la altura vertical del globo armado (esa sale
en `altura_total_real`). El nombre se conserva por compatibilidad.

MODO SIMPLE (por defecto, `usar_parametros_avanzados=False`): 3 piezas con boca por
defecto (11 %), sin pestaña, sin mecha ni viabilidad (`boca`, `vuelo` y `viable` quedan
en None). MODO AVANZADO: activa boca personalizada, pestaña, mecha, empuje y viabilidad.
Todos los campos nuevos tienen valor por defecto para no romper el código existente.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class BalloonInput:
    altura_cuerpo: float            # cm de papel (largo total, ver nota arriba)
    num_gajos: int
    num_hileras_picos: int
    ancho_costura: float            # cm (la mitad se suma a cada borde)
    # --- Modo avanzado: SOLO se usan si usar_parametros_avanzados=True ---
    usar_parametros_avanzados: bool = False
    diametro_boca: Optional[float] = None    # cm; None -> 11 % de la altura
    pestana_boca: float = 4.0                # cm extra para doblar sobre el aro (calibrar)
    diametro_mecha: Optional[float] = None   # cm; None -> 50 % de la boca
    masa_mecha_g: Optional[float] = None     # peso real de mecha + combustible
    altura_llama: float = 40.0               # cm sobre el plano de la boca (calibrar)
    holgura_min: float = 10.0                # cm mínimos mecha -> papel (calibrar)
    alambre_mm: float = 2.0                  # grosor del alambre del aro/varillas
    varillas: int = 4                        # varillas de la parrilla

@dataclass(frozen=True)
class Condiciones:
    """Supuestos físicos para estimar empuje y papel (todos calibrables)."""
    papel_gm2: float = 20.0
    extra_pegamento: float = 0.20
    t_ambiente: float = 28.0
    t_interior: float = 70.0
    presion_pa: float = 101325.0
    desperdicio: float = 0.15
    pliego_cm: Tuple[float, float] = (50.0, 75.0)

@dataclass
class Point2D:
    paso_numero: int
    largo_segmento: float
    largo_acumulado: float
    ancho_medio: float

@dataclass
class SectionResult:
    nombre: str
    puntos: List[Point2D]
    altura_vertical: float
    generatriz_total: float
    radio_inicio: float
    radio_fin: float
    pestana: float = 0.0            # tira extra (solo cono inferior, modo avanzado)
    area_cm2: float = 0.0           # área de UNA pieza con costuras

@dataclass
class BocaResult:
    diametro: float
    circunferencia_aro: float
    ancho_por_gajo: float
    pestana: float = 0.0
    diametro_mecha: Optional[float] = None
    holgura: Optional[float] = None             # radio_boca - radio_mecha
    holgura_ok: Optional[bool] = None
    diametro_minimo: Optional[float] = None     # boca mínima para esa mecha
    radio_pared_a_llama: Optional[float] = None

@dataclass
class VueloResult:
    volumen_m3: float
    empuje_g: float
    masa_papel_g: float
    masa_estructura_g: float        # aro + varillas
    carga_libre_g: float            # empuje - papel
    carga_neta_g: float             # lo que queda para mecha + combustible
    pliegos: float

@dataclass
class BalloonCalculationResult:
    altura_cuerpo_base: float
    altura_picos: float
    altura_total_real: float
    diametro_globo: float
    ancho_max_gajo: float
    
    # Datos informativos
    diametro_boquilla_calculado: float 
    circumferencia_boquilla: float
    
    seccion_superior: SectionResult
    seccion_picos: SectionResult
    seccion_inferior: SectionResult

    # --- Nuevos (con valor por defecto) ---
    volumen_m3: float = 0.0                 # calculado en modo simple y avanzado
    boca: Optional[BocaResult] = None       # None en modo simple
    vuelo: Optional[VueloResult] = None     # None en modo simple
    gajos_min_70cm: int = 0
    gajos_min_50cm: int = 0
    area_total_m2: float = 0.0
    avisos: List[str] = field(default_factory=list)
    viable: Optional[bool] = None           # None = no evaluado (modo simple)