import os
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class ColorPapel:
    id: str
    nombre: str
    hex: str
    aproximado: bool = False

    def __post_init__(self):
        if not re.match(r"^#[0-9a-fA-F]{6}$", self.hex):
            raise ValueError(f"Código HEX inválido: '{self.hex}'. Debe tener formato #RRGGBB.")

def _ruta_catalogo_base() -> str:
    # Ubicación en <raíz>/datos/colores_papel.json
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "datos", "colores_papel.json")

def _ruta_catalogo_usuario() -> str:
    app_dir = ""
    try:
        import platformdirs
        app_dir = platformdirs.user_data_dir("MiProyectoGlobos", appauthor=False)
    except Exception:
        app_data = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~")
        app_dir = os.path.join(app_data, "MiProyectoGlobos")
    return os.path.join(app_dir, "colores_usuario.json")

def cargar_catalogo(ruta_usuario: Optional[str] = None) -> List[ColorPapel]:
    colores_dict: Dict[str, ColorPapel] = {}
    
    # 1. Cargar catálogo base
    ruta_base = _ruta_catalogo_base()
    if os.path.exists(ruta_base):
        try:
            with open(ruta_base, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    col = ColorPapel(**item)
                    colores_dict[col.id] = col
        except Exception:
            pass

    # 2. Cargar catálogo de usuario (sobrescribe o agrega)
    r_user = ruta_usuario or _ruta_catalogo_usuario()
    if os.path.exists(r_user):
        try:
            with open(r_user, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    col = ColorPapel(**item)
                    colores_dict[col.id] = col
        except Exception:
            pass

    return list(colores_dict.values())

def guardar_color_usuario(color: ColorPapel, ruta_usuario: Optional[str] = None) -> None:
    r_user = ruta_usuario or _ruta_catalogo_usuario()
    os.makedirs(os.path.dirname(r_user), exist_ok=True)
    
    actuales = {}
    if os.path.exists(r_user):
        try:
            with open(r_user, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    actuales[item["id"]] = item
        except Exception:
            actuales = {}
            
    actuales[color.id] = asdict(color)
    
    with open(r_user, "w", encoding="utf-8") as f:
        json.dump(list(actuales.values()), f, indent=2, ensure_ascii=False)

def color_por_id(id_color: str, catalogo: Optional[List[ColorPapel]] = None) -> ColorPapel:
    cat = catalogo if catalogo is not None else cargar_catalogo()
    for c in cat:
        if c.id == id_color:
            return c
    # Respaldo por defecto: blanco
    return ColorPapel("blanco", "Blanco", "#ffffff", False)
