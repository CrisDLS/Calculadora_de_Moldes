import math
from dataclasses import dataclass
from typing import List, Dict, Optional
from logic.models import BalloonInput, BalloonCalculationResult, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, color_de_cara
from logic.diseno.paleta import ColorPapel, color_por_id, cargar_catalogo
from logic.geometria.malla_trompo import Cara

@dataclass
class ItemCompra:
    color: ColorPapel
    piezas_superior: int
    piezas_pico: int
    piezas_inferior: int
    piezas_totales: int
    area_m2: float
    pliegos: int
    paquetes: int = 0

def lista_de_compra(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    esquema_pintura: EsquemaPintura,
    esquema_diseno: Optional[EsquemaDiseno] = None,
    condiciones: Optional[Condiciones] = None,
    catalogo: Optional[List[ColorPapel]] = None,
    pliegos_por_paquete: int = 100
) -> List[ItemCompra]:
    """Calcula la cantidad de piezas, área (m²), pliegos y paquetes de papel por cada color."""
    cond = condiciones or Condiciones()
    cat = catalogo if catalogo is not None else cargar_catalogo()
    
    N = entrada.num_gajos
    hileras = entrada.num_hileras_picos

    # Áreas por pieza individual (en cm²)
    area_sup_cm2 = resultado.seccion_superior.area_cm2
    area_pic_cm2 = resultado.seccion_picos.area_cm2
    area_inf_cm2 = resultado.seccion_inferior.area_cm2

    # Acumuladores por color_id: {"sup": int, "pic": int, "inf": int, "area_cm2": float}
    conteos: Dict[str, Dict[str, float]] = {}

    def get_slot(cid: str) -> Dict[str, float]:
        if cid not in conteos:
            conteos[cid] = {"sup": 0, "pic": 0, "inf": 0, "area_cm2": 0.0}
        return conteos[cid]

    # Iterar cada gajo k = 0..N-1 usando color_de_cara para máxima coherencia con el 3D
    for k in range(N):
        # Cono superior
        cara_sup = Cara([], "superior", k, None, None, [0, 0, 1], [])
        c_sup = color_de_cara(esquema_pintura, cara_sup, esquema_diseno, N)
        slot_s = get_slot(c_sup)
        slot_s["sup"] += 1
        slot_s["area_cm2"] += area_sup_cm2

        # Cono inferior
        cara_inf = Cara([], "inferior", k, None, None, [0, 0, -1], [])
        c_inf = color_de_cara(esquema_pintura, cara_inf, esquema_diseno, N)
        slot_i = get_slot(c_inf)
        slot_i["inf"] += 1
        slot_i["area_cm2"] += area_inf_cm2

        # Picos de este gajo: cada pirámide tiene 4 caras triangulares
        for j in range(hileras):
            for sub in range(4):
                cara_pic = Cara([], "pico", k, j, sub, [1, 0, 0], [])
                c_pic = color_de_cara(esquema_pintura, cara_pic, esquema_diseno, N)
                slot_p = get_slot(c_pic)
                slot_p["pic"] += 1
                slot_p["area_cm2"] += area_pic_cm2

    area_pliego_cm2 = cond.pliego_cm[0] * cond.pliego_cm[1]
    items: List[ItemCompra] = []
    t_paquete = max(1, pliegos_por_paquete)

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
        paquetes = math.ceil(pliegos / t_paquete) if pliegos > 0 else 0
        
        items.append(ItemCompra(
            color=col,
            piezas_superior=p_sup,
            piezas_pico=p_pic,
            piezas_inferior=p_inf,
            piezas_totales=tot_piezas,
            area_m2=area_m2,
            pliegos=pliegos,
            paquetes=paquetes
        ))

    # Ordenar por piezas totales descendente
    items.sort(key=lambda x: x.piezas_totales, reverse=True)
    return items
