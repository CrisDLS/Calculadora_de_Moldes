import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno

@dataclass
class Proyecto:
    version: int
    nombre: str
    entrada: BalloonInput
    condiciones: Condiciones
    esquema: Optional[EsquemaDiseno]
    notas: str

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
            
        return cls(
            version=data["version"],
            nombre=data["nombre"],
            entrada=ent,
            condiciones=cond,
            esquema=esq,
            notas=data.get("notas", "")
        )

def _migrar_proyecto(data: Dict[str, Any]) -> Dict[str, Any]:
    v = data.get("version")
    if v is None:
        raise ValueError("JSON corrupto o sin versión.")
    if v > 1:
        raise ValueError(f"Versión de proyecto desconocida: {v}")
    
    # Aquí irán las migraciones de v1 a v2, etc.
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
