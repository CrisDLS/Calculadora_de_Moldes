from dataclasses import dataclass, field
from typing import Dict, List
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.pintura import VariantePico, variante_de_piramide

@dataclass
class EsquemaDisenoPico:
    """Modela los patrones de diseño y variantes de las pirámides de picos."""
    modo_repeticion: str = "todas_a"  # "todas_a", "alternar_gajo", "alternar_hilera", "ajedrez"
    variante_a: VariantePico = field(default_factory=VariantePico)
    usar_variante_b: bool = False
    variante_b: VariantePico = field(default_factory=lambda: VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo"))
    motivos_por_cara: List[int] = field(default_factory=lambda: [0, 1, 2, 3])

@dataclass
class ResumenPico:
    """Resumen cuantitativo del despiece de picos."""
    total_piramides: int
    piramides_a: int
    piramides_b: int
    total_triangulos: int
    triangulos_a: int
    triangulos_b: int
    cuatro_caras_iguales_a: bool
    cuatro_caras_iguales_b: bool
    conteo_colores: Dict[str, int] = field(default_factory=dict)

def resumen_pico(
    esquema: EsquemaDisenoPico,
    entrada: BalloonInput,
    resultado: BalloonCalculationResult
) -> ResumenPico:
    """Calcula el conteo exacto de pirámides, triángulos y variantes del pico."""
    H = entrada.num_hileras_picos
    N = entrada.num_gajos
    total_pir = H * N
    total_tri = total_pir * 4

    p_a = 0
    p_b = 0
    conteo_col: Dict[str, int] = {}

    for h in range(H):
        for g in range(N):
            if esquema.usar_variante_b:
                var_letra = variante_de_piramide(esquema.modo_repeticion, h, g)
            else:
                var_letra = "A"

            if var_letra == "B":
                p_b += 1
                var_obj = esquema.variante_b
            else:
                p_a += 1
                var_obj = esquema.variante_a

            for sub in range(4):
                c = var_obj.color_para_sub(sub)
                conteo_col[c] = conteo_col.get(c, 0) + 1

    iguales_a = (esquema.variante_a.modo_caras == "igual")
    iguales_b = (esquema.variante_b.modo_caras == "igual")

    return ResumenPico(
        total_piramides=total_pir,
        piramides_a=p_a,
        piramides_b=p_b,
        total_triangulos=total_tri,
        triangulos_a=p_a * 4,
        triangulos_b=p_b * 4,
        cuatro_caras_iguales_a=iguales_a,
        cuatro_caras_iguales_b=iguales_b,
        conteo_colores=conteo_col,
    )
