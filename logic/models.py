""" 
1. Modelos de Datos 
Este archivo define qué datos entran y salen, sin importar cómo se calculan. 
Usaremos dataclasses de Python para un código limpio.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class BalloonInput:
    altura_cuerpo: float
    num_gajos: int
    num_hileras_picos: int
    ancho_costura: float

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