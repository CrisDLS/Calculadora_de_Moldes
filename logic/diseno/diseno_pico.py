from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.pintura import VariantePico, variante_de_piramide

if TYPE_CHECKING:
    from logic.diseno.config_seccion import ConfigSeccion

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
    resultado: Optional[BalloonCalculationResult] = None,
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


def repeticiones_por_cara(
    seccion: str,
    entrada: BalloonInput,
    config_seccion: "ConfigSeccion",
) -> Dict[Tuple[Optional[str], int], int]:
    """Calcula cuántas veces aparece en el globo completo cada cara o motivo del lienzo 2D.

    Retorna:
    - dict[(variante, indice), int]
      - Para conos ("superior", "inferior"):
        variante es None, indice es el número de motivo (0..M-1).
        El valor es la cantidad de caras completas de ese motivo en el globo.
      - Para picos ("pico", "pico_A", "pico_B"):
        variante es "A" o "B", indice es la cara del lienzo (0 para 'una_cara'/'mitad', o 0..3 para 'completo').
        El valor es la cantidad de caras completas en el globo.
        En modo 'mitad', la mitad activa + su reflejo en espejo = 1 cara completa.
    """
    from logic.geometria.textura import num_caras_lienzo

    if seccion in ("superior", "inferior"):
        esquema = config_seccion.esquema
        if esquema is None:
            from logic.diseno.esquema import EsquemaDiseno
            esquema = EsquemaDiseno(modo="repeticion", tam_grupo=5)

        asignaciones = esquema.asignar(entrada.num_gajos)
        res_motivos = esquema.resumen_motivos(asignaciones)

        resultado_dict: Dict[Tuple[Optional[str], int], int] = {}
        for motivo, (total_gajos, _en_espejo, _sin_espejo) in res_motivos.items():
            resultado_dict[(None, motivo)] = total_gajos
        return resultado_dict

    # Sección de pico ("pico", "pico_A", "pico_B")
    esquema_pico = config_seccion.esquema_pico or EsquemaDisenoPico()
    res = resumen_pico(esquema_pico, entrada)
    p_a = res.piramides_a
    p_b = res.piramides_b

    # Modo de dibujo y número de caras del lienzo para pico
    modo_dibujar = getattr(config_seccion, "diseno_modo", getattr(config_seccion, "dibujar", "una_cara"))
    n_caras = num_caras_lienzo("pico", dibujar=modo_dibujar)

    # Si n_caras == 1 ('una_cara' o 'mitad'), cada pirámide de 4 caras usa esa cara 4 veces.
    # Si n_caras == 4 ('completo'), cada cara k aparece 1 vez por pirámide (cara sub k).
    factor_caras = 4 if n_caras == 1 else 1

    resultado_dict = {}
    incluir_a = seccion != "pico_B"
    incluir_b = seccion != "pico_A"

    for k in range(n_caras):
        if incluir_a:
            resultado_dict[("A", k)] = p_a * factor_caras
        if incluir_b:
            resultado_dict[("B", k)] = p_b * factor_caras

    return resultado_dict
