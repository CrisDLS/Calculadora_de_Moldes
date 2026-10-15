import os
import json
import re
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

@dataclass
class ColorPapel:
    id: str
    nombre: str
    hex: str
    aproximado: bool = True
    marca: str = ""
    codigo: str = ""
    notas: str = ""

    def __post_init__(self):
        self.hex = self.hex.strip().lower()
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
                    col = ColorPapel(
                        id=item["id"],
                        nombre=item["nombre"],
                        hex=item["hex"],
                        aproximado=item.get("aproximado", True),
                        marca=item.get("marca", ""),
                        codigo=item.get("codigo", ""),
                        notas=item.get("notas", "")
                    )
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
                    col = ColorPapel(
                        id=item["id"],
                        nombre=item["nombre"],
                        hex=item["hex"],
                        aproximado=item.get("aproximado", True),
                        marca=item.get("marca", ""),
                        codigo=item.get("codigo", ""),
                        notas=item.get("notas", "")
                    )
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

def exportar_csv(ruta: str, colores: Optional[List[ColorPapel]] = None) -> None:
    """Exporta colores a formato CSV en UTF-8 con encabezados estándar."""
    items = colores if colores is not None else cargar_catalogo()
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["nombre", "marca", "codigo", "hex", "calibrado", "notas"])
        for c in items:
            calibrado_str = "si" if not c.aproximado else "no"
            writer.writerow([c.nombre, c.marca, c.codigo, c.hex, calibrado_str, c.notas])

def _detectar_delimitador(lineas: List[str]) -> str:
    muestra = "".join(lineas[:5])
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(muestra, delimiters=",;\t")
        return dialect.delimiter
    except Exception:
        # Contar ocurrencias simples
        comas = muestra.count(",")
        puntos_coma = muestra.count(";")
        return ";" if puntos_coma > comas else ","

def _generar_id_color(nombre: str, marca: str = "", codigo: str = "") -> str:
    base = f"{marca}_{nombre}_{codigo}" if marca or codigo else nombre
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", base.strip().lower()).strip("_")
    return clean or "color_personalizado"

def importar_csv(ruta: str, ruta_usuario_destino: Optional[str] = None) -> Tuple[List[ColorPapel], List[str]]:
    """Importa colores desde un CSV con tolerancia a delimitadores (, o ;), BOM UTF-8 y filas erróneas.
    
    Devuelve: (lista_colores_importados, lista_mensajes_errores_por_fila).
    """
    errores: List[str] = []
    importados: List[ColorPapel] = []

    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    # Leer texto detectando posible BOM UTF-8
    with open(ruta, "r", encoding="utf-8-sig", errors="replace") as f:
        lineas = f.readlines()

    if not lineas:
        return importados, ["El archivo está vacío."]

    delimiter = _detectar_delimitador(lineas)
    reader = csv.reader(lineas, delimiter=delimiter)

    filas = list(reader)
    if not filas:
        return importados, ["No se encontraron filas de datos."]

    # Buscar cabecera si existe
    primera_fila = [col.strip().lower() for col in filas[0]]
    tiene_cabecera = any(k in primera_fila for k in ["nombre", "hex", "marca", "codigo"])
    
    idx_nombre = 0
    idx_marca = 1
    idx_codigo = 2
    idx_hex = 3
    idx_calibrado = 4
    idx_notas = 5

    fila_inicio = 0
    if tiene_cabecera:
        fila_inicio = 1
        if "nombre" in primera_fila: idx_nombre = primera_fila.index("nombre")
        if "marca" in primera_fila: idx_marca = primera_fila.index("marca")
        if "codigo" in primera_fila: idx_codigo = primera_fila.index("codigo")
        if "hex" in primera_fila: idx_hex = primera_fila.index("hex")
        if "calibrado" in primera_fila: idx_calibrado = primera_fila.index("calibrado")
        if "notas" in primera_fila: idx_notas = primera_fila.index("notas")

    ids_vistos = set()

    for num_fila, fila in enumerate(filas[fila_inicio:], start=fila_inicio + 1):
        if not fila or all(not celda.strip() for celda in fila):
            continue  # Fila vacía ignorada silenciosamente
        
        try:
            nombre = fila[idx_nombre].strip() if len(fila) > idx_nombre else ""
            marca = fila[idx_marca].strip() if len(fila) > idx_marca else ""
            codigo = fila[idx_codigo].strip() if len(fila) > idx_codigo else ""
            hex_val = fila[idx_hex].strip() if len(fila) > idx_hex else ""
            calibrado_val = fila[idx_calibrado].strip().lower() if len(fila) > idx_calibrado else "no"
            notas = fila[idx_notas].strip() if len(fila) > idx_notas else ""

            if not nombre:
                errores.append(f"Fila {num_fila}: Falta el nombre del color.")
                continue

            # Corregir hex si le falta '#'
            if hex_val and not hex_val.startswith("#"):
                hex_val = "#" + hex_val

            if not re.match(r"^#[0-9a-fA-F]{6}$", hex_val):
                errores.append(f"Fila {num_fila}: Código HEX inválido '{hex_val}'.")
                continue

            aproximado = True
            if calibrado_val in ["si", "sí", "true", "1", "calibrado"]:
                aproximado = False

            base_id = _generar_id_color(nombre, marca, codigo)
            cid = base_id
            contador = 2
            while cid in ids_vistos:
                cid = f"{base_id}_{contador}"
                contador += 1
            ids_vistos.add(cid)

            nuevo_color = ColorPapel(
                id=cid,
                nombre=nombre,
                hex=hex_val,
                aproximado=aproximado,
                marca=marca,
                codigo=codigo,
                notas=notas
            )
            importados.append(nuevo_color)
            guardar_color_usuario(nuevo_color, ruta_usuario_destino)

        except Exception as err:
            errores.append(f"Fila {num_fila}: Error inesperado: {err}")

    return importados, errores

def color_por_id(id_color: str, catalogo: Optional[List[ColorPapel]] = None) -> ColorPapel:
    cat = catalogo if catalogo is not None else cargar_catalogo()
    for c in cat:
        if c.id == id_color:
            return c
    # Respaldo por defecto: blanco
    return ColorPapel("blanco", "Blanco", "#ffffff", True)
