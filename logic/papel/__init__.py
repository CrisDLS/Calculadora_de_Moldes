"""Módulo de procesamiento y vectorización de papel."""

from logic.papel.vectorizacion import medir_regiones
from logic.papel.reduccion_colores import reducir_colores
from logic.papel.consumo import medir_cm2_por_color
from logic.papel.silueta import mascara_silueta

__all__ = ["medir_regiones", "reducir_colores", "medir_cm2_por_color", "mascara_silueta"]
