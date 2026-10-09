"""
2.Utilidades generales
Aquí van las matemáticas puras.
""" 

import math

def calcular_hipotenusa(cateto_a: float, cateto_b: float) -> float:
    """Calcula la hipotenusa (Generatriz)."""
    return math.sqrt(cateto_a**2 + cateto_b**2)

def calcular_ancho_gajo(radio: float, num_gajos: int) -> float:
    """Calcula el ancho máximo del gajo (Cuerda o Arco)."""
    # Usamos la fórmula de circunferencia dividida
    return (2 * math.pi * radio) / num_gajos

def interpolar_lineal(y_actual: float, y_max: float, x_max: float) -> float:
    """
    Regla de 3 simple para proyección de triángulos.
    Si en y_max tengo x_max, ¿cuánto tengo en y_actual?
    """
    if y_max == 0: return 0
    return (y_actual / y_max) * x_max