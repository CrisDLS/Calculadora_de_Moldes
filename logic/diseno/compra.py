import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from logic.models import BalloonInput, BalloonCalculationResult, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura
from logic.diseno.paleta import ColorPapel, color_por_id, cargar_catalogo

@dataclass
class ItemCompra:
    color: ColorPapel
    piezas_superior: int
    piezas_pico: int
    piezas_inferior: int
    piezas_totales: int
    area_m2: float
    pliegos: int

def lista_de_compra(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    esquema_pintura: EsquemaPintura,
    esquema_diseno: Optional[EsquemaDiseno] = None,
    condiciones: Optional[Condiciones] = None,
    catalogo: Optional[List[ColorPapel]] = None
) -> List[ItemCompra]:
    """Calcula la cantidad de piezas, área (m²) y pliegos de papel por cada color."""
    cond = condiciones or Condiciones()
    cat = catalogo if catalogo is not None else cargar_catalogo()
    
    # 1. Determinar el motivo de cada gajo si hay esquema de diseño
    N = entrada.num_gajos
    hileras = entrada.num_hileras_picos
    asignaciones = None
    if esquema_diseno is not None:
        try:
            asignaciones = esquema_diseno.asignar(N)
        except Exception:
            asignaciones = None

    # Áreas por pieza individual (en cm²)
    area_sup_cm2 = resultado.seccion_superior.area_cm2
    area_pic_cm2 = resultado.seccion_picos.area_cm2
    area_inf_cm2 = resultado.seccion_inferior.area_cm2

    # Acumuladores por color_id: {"piezas_sup": int, "piezas_pic": int, "piezas_inf": int, "area_cm2": float}
    conteos: Dict[str, Dict[str, float]] = {}

    def get_slot(cid: str) -> Dict[str, float]:
        if cid not in conteos:
            conteos[cid] = {"sup": 0, "pic": 0, "inf": 0, "area_cm2": 0.0}
        return conteos[cid]

    # Iterar cada gajo k = 0..N-1
    for k in range(N):
        motivo = asignaciones[k].motivo if asignaciones and k < len(asignaciones) else None
        
        # Cono superior
        c_sup = "blanco"
        clave_s = f"superior_{k}"
        if clave_s in esquema_pintura.colores_caras_especificas:
            c_sup = esquema_pintura.colores_caras_especificas[clave_s]
        elif motivo is not None and motivo in esquema_pintura.colores_motivos and "superior" in esquema_pintura.colores_motivos[motivo]:
            c_sup = esquema_pintura.colores_motivos[motivo]["superior"]
        else:
            c_sup = esquema_pintura.color_superior
        
        slot_s = get_slot(c_sup)
        slot_s["sup"] += 1
        slot_s["area_cm2"] += area_sup_cm2

        # Cono inferior
        c_inf = "blanco"
        clave_i = f"inferior_{k}"
        if clave_i in esquema_pintura.colores_caras_especificas:
            c_inf = esquema_pintura.colores_caras_especificas[clave_i]
        elif motivo is not None and motivo in esquema_pintura.colores_motivos and "inferior" in esquema_pintura.colores_motivos[motivo]:
            c_inf = esquema_pintura.colores_motivos[motivo]["inferior"]
        else:
            c_inf = esquema_pintura.color_inferior

        slot_i = get_slot(c_inf)
        slot_i["inf"] += 1
        slot_i["area_cm2"] += area_inf_cm2

        # Picos de este gajo: cada pirámide tiene 4 caras triangulares
        # En total hay `hileras` pirámides por gajo, cada una con 4 triángulos del molde
        for j in range(hileras):
            for sub in range(4):
                clave_p = f"pico_{k}_{j}_{sub}"
                c_pic = "amarillo"
                if clave_p in esquema_pintura.colores_caras_especificas:
                    c_pic = esquema_pintura.colores_caras_especificas[clave_p]
                elif motivo is not None and motivo in esquema_pintura.colores_motivos and "pico" in esquema_pintura.colores_motivos[motivo]:
                    c_pic = esquema_pintura.colores_motivos[motivo]["pico"]
                else:
                    c_pic = esquema_pintura.color_pico
                
                slot_p = get_slot(c_pic)
                slot_p["pic"] += 1
                slot_p["area_cm2"] += area_pic_cm2

    area_pliego_cm2 = cond.pliego_cm[0] * cond.pliego_cm[1]
    items: List[ItemCompra] = []

    for cid, val in conteos.items():
        col = color_por_id(cid, cat)
        p_sup = int(val["sup"])
        p_pic = int(val["pic"])
        p_inf = int(val["inf"])
        tot_piezas = p_sup + p_pic + p_inf
        area_cm2 = val["area_cm2"]
        area_m2 = area_cm2 / 10000.0
        
        # Pliegos con desperdicio redondeados al entero superior
        pliegos = math.ceil(area_cm2 * (1.0 + cond.desperdicio) / area_pliego_cm2) if area_cm2 > 0 else 0
        
        items.append(ItemCompra(
            color=col,
            piezas_superior=p_sup,
            piezas_pico=p_pic,
            piezas_inferior=p_inf,
            piezas_totales=tot_piezas,
            area_m2=area_m2,
            pliegos=pliegos
        ))

    # Ordenar por piezas totales descendente
    items.sort(key=lambda x: x.piezas_totales, reverse=True)
    return items
