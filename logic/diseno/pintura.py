from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from logic.geometria.malla_trompo import Cara
from logic.diseno.esquema import EsquemaDiseno

@dataclass
class EsquemaPintura:
    """Esquema de pintura para el globo.
    
    Permite asignar colores por defecto a cada sección ('superior', 'pico', 'inferior'),
    o asignar colores por motivo (definidos en EsquemaDiseno) o colores específicos por cara.
    """
    color_superior: str = "blanco"
    color_pico: str = "amarillo"
    color_inferior: str = "blanco"
    
    # Colores por motivo: {motivo_idx: {"superior": "rojo", "pico": "azul", "inferior": "blanco"}}
    colores_motivos: Dict[int, Dict[str, str]] = field(default_factory=dict)
    
    # Sobrescribir cara específica por clave única
    colores_caras_especificas: Dict[str, str] = field(default_factory=dict)

def clave_cara(cara: Cara) -> str:
    """Genera un identificador único para una cara de la malla."""
    if cara.seccion == "pico":
        return f"pico_{cara.gajo}_{cara.hilera}_{cara.sub}"
    return f"{cara.seccion}_{cara.gajo}"

def color_de_cara(esquema_pintura: EsquemaPintura, cara: Cara, esquema_diseno: Optional[EsquemaDiseno] = None, num_gajos: int = 30) -> str:
    """Determina el id de color de papel asignado a una cara dada.
    
    Prioridad:
    1. Cara específica (`colores_caras_especificas[clave]`)
    2. Color asignado al motivo del gajo (`colores_motivos[motivo][seccion]`)
    3. Color por sección (`color_superior`, `color_pico`, `color_inferior`)
    """
    c_key = clave_cara(cara)
    if c_key in esquema_pintura.colores_caras_especificas:
        return esquema_pintura.colores_caras_especificas[c_key]
        
    if esquema_diseno is not None:
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

    if cara.seccion == "superior":
        return esquema_pintura.color_superior
    elif cara.seccion == "pico":
        return esquema_pintura.color_pico
    elif cara.seccion == "inferior":
        return esquema_pintura.color_inferior
    return "blanco"
