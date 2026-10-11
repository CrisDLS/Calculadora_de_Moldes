# logic/exportacion/estilos.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class EstiloSvg:
    contorno: str
    costura: str
    cuadricula: str
    eje: str
    texto: str
    pestana: str
    fondo: Optional[str]
    fondo_referencia: str
    factor_trazo: float = 1.0
    factor_texto: float = 1.0

# Preset IMPRESION: exactamente los colores y proporciones de impresión original
IMPRESION = EstiloSvg(
    contorno="black",
    costura="red",
    cuadricula="blue",
    eje="blue",
    texto="black",
    pestana="green",
    fondo=None,
    fondo_referencia="#ffffff",
    factor_trazo=1.0,
    factor_texto=1.0,
)

# Preset PANTALLA_OSCURO: líneas claras con alto contraste sobre fondo oscuro #1e1e24
PANTALLA_OSCURO = EstiloSvg(
    contorno="#ffffff",
    costura="#ff7675",
    cuadricula="#74b9ff",
    eje="#a4b0be",
    texto="#f1f2f6",
    pestana="#55efc4",
    fondo=None,
    fondo_referencia="#1e1e24",
    factor_trazo=1.5,
    factor_texto=2.0,
)

# Preset PANTALLA_CLARO: líneas oscuras legibles sobre fondo claro #f8f9fa
PANTALLA_CLARO = EstiloSvg(
    contorno="#1e272e",
    costura="#d63031",
    cuadricula="#0984e3",
    eje="#57606f",
    texto="#2d3436",
    pestana="#00b894",
    fondo=None,
    fondo_referencia="#f8f9fa",
    factor_trazo=1.5,
    factor_texto=2.0,
)
