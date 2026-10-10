"""Presentador del trompo estrella: funciones PURAS (sin customtkinter ni tkinter).

Convierte el texto de los campos de la vista en un `BalloonInput`, da formato al resultado
y clasifica los avisos. Se mantiene fuera de la vista para poder probarlo sin ventana y
reutilizarlo si se migra la UI a otra librería. Aquí no hay fórmulas de cálculo.
"""
import math
from typing import Dict, List, Optional, Tuple

from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonCalculationResult, BalloonInput

# Claves de los campos de la vista -> BalloonInput
CAMPOS_BASICOS = ("altura", "gajos", "hileras", "costura")
CAMPOS_AVANZADOS = ("diametro_boca", "pestana_boca", "diametro_mecha", "masa_mecha_g",
                    "alambre_mm", "varillas", "altura_llama", "holgura_min")

# Mensajes de error por campo (artículo + nombre ya incluidos)
_NOMBRES = {
    "altura": "La altura",
    "gajos": "Los gajos",
    "hileras": "Las hileras",
    "costura": "La costura",
    "diametro_boca": "El diámetro de la boca",
    "pestana_boca": "La pestaña",
    "diametro_mecha": "El diámetro de la mecha",
    "masa_mecha_g": "El peso de la mecha",
    "alambre_mm": "El grosor del alambre",
    "varillas": "Las varillas",
    "altura_llama": "La altura de llama",
    "holgura_min": "La holgura mínima",
}
_MENSAJES_ENTERO = {
    "gajos": "Los gajos deben ser un entero ≥ 3",
    "hileras": "Las hileras deben ser un entero ≥ 0",
    "varillas": "Las varillas deben ser un entero ≥ 0",
}

_L70 = TrompoEstrellaCalculator.GAJO_IDEAL_MAX_CM
_L50 = TrompoEstrellaCalculator.GAJO_REF_MIN_CM

# Etiquetas del resumen (la vista las usa también para el estado vacío)
ETIQUETAS_RESUMEN_SIMPLE = (
    "Diámetro del globo",
    "Ancho máx. de gajo",
    "Diámetro de la boca",
    "Circunferencia de la boca",
    f"Gajos mín. (ancho ≤ {_L70:.0f} cm)",
    f"Gajos máx. (ancho ≤ {_L50:.0f} cm)",
    "Altura armada estimada",
    "Área de papel",
)
ETIQUETAS_RESUMEN_AVANZADO = (
    "Pestaña",
    "Diámetro de mecha",
    "Holgura mecha-papel",
    "Empuje",
    "Carga neta para la mecha",
    "Pliegos",
    "Viable",
)


def _texto_a_numero(texto: Optional[str]) -> Optional[float]:
    """Texto -> float aceptando coma o punto decimal y espacios. Vacío -> None.
    Lanza ValueError (sin mensaje útil) si no es un número finito."""
    limpio = (texto or "").strip().replace(" ", "").replace(",", ".")
    if limpio == "":
        return None
    valor = float(limpio)
    if not math.isfinite(valor):
        raise ValueError(limpio)
    return valor


def _leer_float(valores: Dict[str, str], clave: str) -> Optional[float]:
    try:
        return _texto_a_numero(valores.get(clave))
    except ValueError:
        raise ValueError(f"{_NOMBRES[clave]} debe ser un número") from None


def _leer_entero(valores: Dict[str, str], clave: str) -> Optional[int]:
    try:
        numero = _texto_a_numero(valores.get(clave))
    except ValueError:
        raise ValueError(_MENSAJES_ENTERO[clave]) from None
    if numero is None:
        return None
    if not float(numero).is_integer():
        raise ValueError(_MENSAJES_ENTERO[clave])
    return int(numero)


def leer_entrada(valores: Dict[str, str], avanzado: bool) -> BalloonInput:
    """Convierte el texto de los campos en un BalloonInput.

    `valores` usa las claves de CAMPOS_BASICOS / CAMPOS_AVANZADOS. En modo simple NO se
    leen ni se validan los campos avanzados. Un campo avanzado vacío conserva el valor
    por defecto de BalloonInput. Lanza ValueError con un mensaje claro en español.
    """
    altura = _leer_float(valores, "altura")
    if altura is None:
        raise ValueError("La altura debe ser un número")
    gajos = _leer_entero(valores, "gajos")
    if gajos is None:
        raise ValueError(_MENSAJES_ENTERO["gajos"])
    hileras = _leer_entero(valores, "hileras")
    if hileras is None:
        raise ValueError(_MENSAJES_ENTERO["hileras"])
    costura = _leer_float(valores, "costura")
    if costura is None:
        raise ValueError("La costura debe ser un número")

    extra: Dict[str, object] = {}
    if avanzado:
        for clave in ("diametro_boca", "pestana_boca", "diametro_mecha", "masa_mecha_g",
                      "alambre_mm", "altura_llama", "holgura_min"):
            numero = _leer_float(valores, clave)
            if numero is not None:
                extra[clave] = numero
        varillas = _leer_entero(valores, "varillas")
        if varillas is not None:
            extra["varillas"] = varillas
    return BalloonInput(altura, gajos, hileras, costura,
                        usar_parametros_avanzados=avanzado, **extra)


def _cm(x: float, decimales: int = 1) -> str:
    return f"{x:.{decimales}f} cm"


def formatear_resumen(r: BalloonCalculationResult) -> List[Tuple[str, str]]:
    """Resultado -> lista de (etiqueta, valor formateado). Avanzado si r.boca no es None."""
    valores = [
        _cm(r.diametro_globo),
        _cm(r.ancho_max_gajo, 2),
        _cm(r.diametro_boquilla_calculado),
        _cm(r.circumferencia_boquilla),
        str(r.gajos_min_70cm),
        str(r.gajos_min_50cm),
        _cm(r.altura_total_real, 0),
        f"{r.area_total_m2:.1f} m²",
    ]
    filas = list(zip(ETIQUETAS_RESUMEN_SIMPLE, valores))
    if r.boca is not None and r.vuelo is not None:
        b, v = r.boca, r.vuelo
        holgura = _cm(b.holgura) + ("" if b.holgura_ok else " (insuficiente)")
        extra = [
            _cm(b.pestana),
            _cm(b.diametro_mecha),
            holgura,
            f"{v.empuje_g / TrompoEstrellaCalculator.G_POR_KG:.1f} kg",
            f"{v.carga_neta_g / TrompoEstrellaCalculator.G_POR_KG:.1f} kg",
            f"{v.pliegos:.0f}",
            "Sí" if r.viable else "No",
        ]
        filas += list(zip(ETIQUETAS_RESUMEN_AVANZADO, extra))
    return filas


def clasificar_aviso(texto: str) -> str:
    """'error' | 'aviso' | 'ok' | 'info' según el prefijo del texto."""
    t = texto.lstrip().upper()
    if t.startswith("ERROR"):
        return "error"
    if t.startswith("AVISO"):
        return "aviso"
    if t.startswith("OK"):
        return "ok"
    return "info"
