from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from logic.geometria.malla_trompo import Cara
from logic.diseno.esquema import EsquemaDiseno

@dataclass
class VariantePico:
    """Configuración de caras para una pirámide de pico.
    
    modo_caras:
    - 'igual': las 4 caras usan el mismo color (color_0)
    - 'alternado': caras 0 y 2 usan color_0; caras 1 y 3 usan color_1
    - 'cuatro': cada cara 0, 1, 2, 3 tiene su propio color
    """
    modo_caras: str = "igual"  # "igual", "alternado", "cuatro"
    color_0: str = "amarillo"
    color_1: str = "amarillo"
    color_2: str = "amarillo"
    color_3: str = "amarillo"

    def color_para_sub(self, sub: int) -> str:
        s = sub % 4
        if self.modo_caras == "igual":
            return self.color_0
        elif self.modo_caras == "alternado":
            return self.color_0 if s in (0, 2) else self.color_1
        elif self.modo_caras == "cuatro":
            if s == 0: return self.color_0
            if s == 1: return self.color_1
            if s == 2: return self.color_2
            return self.color_3
        return self.color_0

@dataclass
class EsquemaPintura:
    """Esquema de pintura para el globo.
    
    Soporta:
    - Modos por cono: 'liso', 'alternado', 'bloques'
    - Ciclos de colores para superior e inferior (1 a 6 colores)
    - Cono inferior vinculado opcionalmente al superior
    - Picos con Variante A y B, y repetición entre pirámides ('todas_a', 'alternar_gajo', 'alternar_hilera', 'ajedrez')
    - Compatibilidad hacia atrás completa con color_superior, color_pico, color_inferior, colores_motivos y colores_caras_especificas.
    """
    # Cono Superior
    modo_superior: str = "liso"  # "liso", "alternado", "bloques"
    colores_superior: List[str] = field(default_factory=lambda: ["blanco"])
    tam_bloque_superior: int = 5

    # Cono Inferior
    mismo_esquema_inferior: bool = False
    modo_inferior: str = "liso"  # "liso", "alternado", "bloques"
    colores_inferior: List[str] = field(default_factory=lambda: ["blanco"])
    tam_bloque_inferior: int = 5

    # Picos (Variantes A y B)
    variante_a: VariantePico = field(default_factory=VariantePico)
    usar_variante_b: bool = False
    variante_b: VariantePico = field(default_factory=lambda: VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo"))
    repeticion_picos: str = "todas_a"  # "todas_a", "alternar_gajo", "alternar_hilera", "ajedrez"

    # Campos heredados / retrocompatibles
    color_superior: str = "blanco"
    color_pico: str = "amarillo"
    color_inferior: str = "blanco"
    colores_motivos: Dict[int, Dict[str, str]] = field(default_factory=dict)
    colores_caras_especificas: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # Si se pasaron valores en color_superior/color_inferior pero colores_superior/inferior quedaron con el default de ["blanco"],
        # priorizar el valor explícito de color_superior/inferior.
        if self.color_superior != "blanco" and self.colores_superior == ["blanco"]:
            self.colores_superior = [self.color_superior]
        elif self.colores_superior:
            self.color_superior = self.colores_superior[0]

        if self.color_inferior != "blanco" and self.colores_inferior == ["blanco"]:
            self.colores_inferior = [self.color_inferior]
        elif self.colores_inferior:
            self.color_inferior = self.colores_inferior[0]

        if self.color_pico != "amarillo" and self.variante_a.color_0 == "amarillo":
            self.variante_a.color_0 = self.color_pico
        elif self.variante_a.color_0 != "amarillo":
            self.color_pico = self.variante_a.color_0

def clave_cara(cara: Cara) -> str:
    """Genera un identificador único para una cara de la malla."""
    if cara.seccion == "pico":
        return f"pico_{cara.gajo}_{cara.hilera}_{cara.sub}"
    return f"{cara.seccion}_{cara.gajo}"

def _color_en_patron(modo: str, colores: List[str], gajo: int, tam_bloque: int = 5) -> str:
    if not colores:
        return "blanco"
    if modo == "liso" or len(colores) == 1:
        return colores[0]
    elif modo == "alternado":
        return colores[gajo % len(colores)]
    elif modo == "bloques":
        t = max(1, tam_bloque)
        indice_bloque = (gajo // t) % len(colores)
        return colores[indice_bloque]
    return colores[0]

def color_de_cara(
    esquema_pintura: EsquemaPintura,
    cara: Cara,
    esquema_diseno: Optional[EsquemaDiseno] = None,
    num_gajos: int = 30
) -> str:
    """Determina el id de color de papel asignado a una cara dada.
    
    Prioridad:
    1. Cara específica (`colores_caras_especificas[clave]`)
    2. Color asignado al motivo del gajo (`colores_motivos[motivo][seccion]`)
    3. Patrones de sección (Modos de conos o Variantes A/B de picos)
    """
    c_key = clave_cara(cara)
    if c_key in esquema_pintura.colores_caras_especificas:
        return esquema_pintura.colores_caras_especificas[c_key]
        
    if esquema_diseno is not None and esquema_pintura.colores_motivos:
        try:
            asignaciones = esquema_diseno.asignar(num_gajos)
            if cara.gajo < len(asignaciones):
                motivo = asignaciones[cara.gajo].motivo
                if motivo in esquema_pintura.colores_motivos:
                    dict_sec = esquema_pintura.colores_motivos[motivo]
                    if cara.seccion in dict_sec:
                        return dict_sec[cara.seccion]
        except Exception:
            pass

    # Evaluación de patrones por sección
    if cara.seccion == "superior":
        return _color_en_patron(
            esquema_pintura.modo_superior,
            esquema_pintura.colores_superior,
            cara.gajo,
            esquema_pintura.tam_bloque_superior
        )
    elif cara.seccion == "inferior":
        if esquema_pintura.mismo_esquema_inferior:
            return _color_en_patron(
                esquema_pintura.modo_superior,
                esquema_pintura.colores_superior,
                cara.gajo,
                esquema_pintura.tam_bloque_superior
            )
        else:
            return _color_en_patron(
                esquema_pintura.modo_inferior,
                esquema_pintura.colores_inferior,
                cara.gajo,
                esquema_pintura.tam_bloque_inferior
            )
    elif cara.seccion == "pico":
        j = cara.hilera if cara.hilera is not None else 0
        k = cara.gajo
        sub = cara.sub if cara.sub is not None else 0

        # Selección de variante A o B
        usa_var_b = False
        if esquema_pintura.usar_variante_b:
            rep = esquema_pintura.repeticion_picos
            if rep == "alternar_gajo":
                usa_var_b = (k % 2 == 1)
            elif rep == "alternar_hilera":
                usa_var_b = (j % 2 == 1)
            elif rep == "ajedrez":
                usa_var_b = ((k + j) % 2 == 1)

        variante = esquema_pintura.variante_b if usa_var_b else esquema_pintura.variante_a
        return variante.color_para_sub(sub)

    return "blanco"
