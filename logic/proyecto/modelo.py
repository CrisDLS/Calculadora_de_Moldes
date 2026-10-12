import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, VariantePico
from logic.diseno.diseno_pico import EsquemaDisenoPico

@dataclass
class Proyecto:
    version: int
    nombre: str
    entrada: BalloonInput
    condiciones: Condiciones
    esquema: Optional[EsquemaDiseno]
    notas: str
    hoja: str = "carta"
    escala: Union[str, int, float] = "auto"
    pintura: Optional[EsquemaPintura] = None
    pliegos_por_paquete: int = 100
    esquema_pico: Optional[EsquemaDisenoPico] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proyecto":
        # Migración vacía para el futuro
        data = _migrar_proyecto(data)
        
        # Validar campos requeridos
        for req in ["version", "nombre", "entrada"]:
            if req not in data:
                raise ValueError(f"Falta el campo requerido: {req}")
        
        ent = BalloonInput(**data["entrada"])
        cond = Condiciones(**data.get("condiciones", {}))
        
        esq = None
        if data.get("esquema"):
            e_data = data["esquema"]
            ciclo = e_data.get("ciclo")
            if ciclo:
                ciclo = [(c[0], c[1]) for c in ciclo]
            esq = EsquemaDiseno(e_data["modo"], e_data.get("tam_grupo", e_data.get("k", 1)), ciclo)
            
        pintura = None
        if data.get("pintura"):
            p_data = data["pintura"]
            col_motivos = {}
            for k, v in p_data.get("colores_motivos", {}).items():
                col_motivos[int(k)] = v
            
            var_a_data = p_data.get("variante_a", {})
            var_a = VariantePico(**var_a_data) if var_a_data else VariantePico()

            var_b_data = p_data.get("variante_b", {})
            var_b = VariantePico(**var_b_data) if var_b_data else VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo")

            pintura = EsquemaPintura(
                modo_superior=p_data.get("modo_superior", "liso"),
                colores_superior=p_data.get("colores_superior", [p_data.get("color_superior", "blanco")]),
                tam_bloque_superior=p_data.get("tam_bloque_superior", 5),
                mismo_esquema_inferior=p_data.get("mismo_esquema_inferior", False),
                modo_inferior=p_data.get("modo_inferior", "liso"),
                colores_inferior=p_data.get("colores_inferior", [p_data.get("color_inferior", "blanco")]),
                tam_bloque_inferior=p_data.get("tam_bloque_inferior", 5),
                variante_a=var_a,
                usar_variante_b=p_data.get("usar_variante_b", False),
                variante_b=var_b,
                repeticion_picos=p_data.get("repeticion_picos", "todas_a"),
                color_superior=p_data.get("color_superior", "blanco"),
                color_pico=p_data.get("color_pico", "amarillo"),
                color_inferior=p_data.get("color_inferior", "blanco"),
                colores_motivos=col_motivos,
                colores_caras_especificas=p_data.get("colores_caras_especificas", {})
            )

        esq_pico = None
        if data.get("esquema_pico"):
            ep_data = data["esquema_pico"]
            var_a_data = ep_data.get("variante_a", {})
            var_a = VariantePico(**var_a_data) if var_a_data else VariantePico()
            var_b_data = ep_data.get("variante_b", {})
            var_b = VariantePico(**var_b_data) if var_b_data else VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo")
            esq_pico = EsquemaDisenoPico(
                modo_repeticion=ep_data.get("modo_repeticion", "todas_a"),
                variante_a=var_a,
                usar_variante_b=ep_data.get("usar_variante_b", False),
                variante_b=var_b,
                motivos_por_cara=ep_data.get("motivos_por_cara", [0, 1, 2, 3])
            )

        return cls(
            version=data["version"],
            nombre=data["nombre"],
            entrada=ent,
            condiciones=cond,
            esquema=esq,
            notas=data.get("notas", ""),
            hoja=data.get("hoja", "carta"),
            escala=data.get("escala", "auto"),
            pintura=pintura,
            pliegos_por_paquete=data.get("pliegos_por_paquete", 100),
            esquema_pico=esq_pico,
        )

def _migrar_proyecto(data: Dict[str, Any]) -> Dict[str, Any]:
    v = data.get("version")
    if v is None:
        raise ValueError("JSON corrupto o sin versión.")
    if v > 1:
        raise ValueError(f"Versión de proyecto desconocida: {v}")
    
    return data

def guardar_proyecto(proyecto: Proyecto, ruta: str) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(asdict(proyecto), f, indent=4, ensure_ascii=False)

def cargar_proyecto(ruta: str) -> Proyecto:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError("El archivo no es un JSON válido.") from e
    
    return Proyecto.from_dict(data)
