import os
import shutil
import re
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
from PIL import Image, ImageOps
import defusedxml.ElementTree as ET

MAX_RASTER_DIM = 10000
MAX_RASTER_BYTES = 30 * 1024 * 1024  # 30 MB
MAX_SVG_BYTES = 10 * 1024 * 1024     # 10 MB

@dataclass
class CapaDiseno:
    id: str
    nombre: str
    tipo: str  # "svg" | "raster"
    archivo: str  # Relativo a <nombre>_recursos/
    ancho_natural: float  # cm
    alto_natural: float   # cm
    x: float = 0.0        # cm (posición en lienzo del abanico)
    y: float = 0.0        # cm
    ancho: float = 10.0   # cm
    alto: float = 10.0    # cm
    rotacion: float = 0.0 # grados (-180..180)
    reflejo_h: bool = False
    reflejo_v: bool = False
    opacidad: float = 1.0 # 0.0 a 1.0
    visible: bool = True
    bloqueada: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "archivo": self.archivo,
            "ancho_natural": round(float(self.ancho_natural), 4),
            "alto_natural": round(float(self.alto_natural), 4),
            "x": round(float(self.x), 4),
            "y": round(float(self.y), 4),
            "ancho": round(float(self.ancho), 4),
            "alto": round(float(self.alto), 4),
            "rotacion": round(float(self.rotacion), 2),
            "reflejo_h": bool(self.reflejo_h),
            "reflejo_v": bool(self.reflejo_v),
            "opacidad": round(float(self.opacidad), 3),
            "visible": bool(self.visible),
            "bloqueada": bool(self.bloqueada),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapaDiseno":
        return cls(
            id=str(data["id"]),
            nombre=str(data.get("nombre", "Capa")),
            tipo=str(data.get("tipo", "raster")),
            archivo=str(data["archivo"]),
            ancho_natural=float(data.get("ancho_natural", 10.0)),
            alto_natural=float(data.get("alto_natural", 10.0)),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            ancho=float(data.get("ancho", 10.0)),
            alto=float(data.get("alto", 10.0)),
            rotacion=float(data.get("rotacion", 0.0)),
            reflejo_h=bool(data.get("reflejo_h", False)),
            reflejo_v=bool(data.get("reflejo_v", False)),
            opacidad=float(data.get("opacidad", 1.0)),
            visible=bool(data.get("visible", True)),
            bloqueada=bool(data.get("bloqueada", False)),
        )

@dataclass
class Diseno:
    seccion: str  # "superior" | "inferior" | "pico"
    variante: str = "A"  # "A" | "B" (solo para pico)
    capas: List[CapaDiseno] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seccion": self.seccion,
            "variante": self.variante,
            "capas": [c.to_dict() for c in self.capas],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diseno":
        capas_data = data.get("capas", [])
        return cls(
            seccion=str(data.get("seccion", "superior")),
            variante=str(data.get("variante", "A")),
            capas=[CapaDiseno.from_dict(c) for c in capas_data],
        )


def _parsear_dimension_svg(val: str) -> Optional[float]:
    """Convierte valor de dimensión SVG (px, mm, cm, in, pt) a centímetros."""
    if not val:
        return None
    val = val.strip()
    match = re.match(r"^([\d.]+)\s*(px|mm|cm|in|pt)?$", val, re.IGNORECASE)
    if not match:
        return None
    num = float(match.group(1))
    unidad = (match.group(2) or "px").lower()
    if unidad == "cm":
        return num
    elif unidad == "mm":
        return num / 10.0
    elif unidad == "in":
        return num * 2.54
    elif unidad == "pt":
        return num * (2.54 / 72.0)
    elif unidad == "px":
        return num * (2.54 / 96.0)
    return num * (2.54 / 96.0)


def _validar_y_procesar_svg(ruta: Path) -> Tuple[float, float, str]:
    """Valida seguridad de un archivo SVG y extrae sus dimensiones naturales en cm."""
    tam_bytes = ruta.stat().st_size
    if tam_bytes > MAX_SVG_BYTES:
        raise ValueError(f"El archivo SVG excede el límite de 10 MB ({tam_bytes / (1024*1024):.1f} MB).")

    with open(ruta, "rb") as f:
        contenido_bytes = f.read()

    try:
        contenido_str = contenido_bytes.decode("utf-8")
    except UnicodeDecodeError:
        contenido_str = contenido_bytes.decode("latin-1")

    # Rechazar DOCTYPE y ENTITY
    if re.search(r"<!DOCTYPE|<!ENTITY", contenido_str, re.IGNORECASE):
        raise ValueError("El SVG contiene declaraciones DOCTYPE o ENTITY no permitidas.")

    # Rechazar scripts o foreignObject
    if re.search(r"<\s*script[\s>]", contenido_str, re.IGNORECASE):
        raise ValueError("El SVG contiene etiquetas <script> no permitidas.")
    if re.search(r"<\s*foreignObject[\s>]", contenido_str, re.IGNORECASE):
        raise ValueError("El SVG contiene etiquetas <foreignObject> no permitidas.")

    # Parsear con defusedxml
    try:
        root = ET.fromstring(contenido_bytes)
    except Exception as e:
        raise ValueError(f"SVG inválido o corrupto: {e}")

    # Validar elementos y atributos en el árbol XML
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1].lower()
        if tag_local in ("script", "foreignobject"):
            raise ValueError(f"El SVG contiene etiqueta no permitida: <{tag_local}>")

        for attr, val in elem.attrib.items():
            attr_local = attr.split("}")[-1].lower()
            if attr_local.startswith("on"):
                raise ValueError(f"El SVG contiene evento no permitido: {attr_local}")
            if attr_local in ("href", "xlink:href", "src"):
                val_limpio = val.strip().lower()
                if val_limpio.startswith(("http:", "https:", "file:", "ftp:", "//")):
                    raise ValueError(f"El SVG contiene enlace externo no permitido: {val}")
                if val_limpio.startswith("data:") and not val_limpio.startswith(("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp")):
                    raise ValueError("El SVG contiene URI de datos no permitida.")

    # Extraer dimensiones naturales
    ancho_cm = None
    alto_cm = None

    ancho_attr = root.attrib.get("width")
    alto_attr = root.attrib.get("height")
    if ancho_attr and not ancho_attr.endswith("%"):
        ancho_cm = _parsear_dimension_svg(ancho_attr)
    if alto_attr and not alto_attr.endswith("%"):
        alto_cm = _parsear_dimension_svg(alto_attr)

    if (ancho_cm is None or alto_cm is None) and "viewBox" in root.attrib:
        partes = [p for p in re.split(r"[\s,]+", root.attrib["viewBox"].strip()) if p]
        if len(partes) == 4:
            try:
                vb_w = float(partes[2])
                vb_h = float(partes[3])
                if vb_w > 0 and vb_h > 0:
                    ancho_cm = vb_w * (2.54 / 96.0)
                    alto_cm = vb_h * (2.54 / 96.0)
            except ValueError:
                pass

    if ancho_cm is None or ancho_cm <= 0:
        ancho_cm = 10.0
    if alto_cm is None or alto_cm <= 0:
        alto_cm = 10.0

    return ancho_cm, alto_cm, contenido_str


def _validar_y_procesar_raster(ruta: Path) -> Tuple[float, float, Image.Image]:
    """Valida un archivo de imagen raster, corrige orientación EXIF y extrae dimensiones."""
    tam_bytes = ruta.stat().st_size
    if tam_bytes > MAX_RASTER_BYTES:
        raise ValueError(f"La imagen excede el límite de 30 MB ({tam_bytes / (1024*1024):.1f} MB).")

    try:
        img = Image.open(ruta)
        img.load()
    except Exception as e:
        raise ValueError(f"No se pudo abrir la imagen raster: {e}")

    if img.width > MAX_RASTER_DIM or img.height > MAX_RASTER_DIM:
        raise ValueError(f"La imagen excede las dimensiones máximas permitidas ({MAX_RASTER_DIM}x{MAX_RASTER_DIM} px). Dimensiones actuales: {img.width}x{img.height}.")

    # Transposición EXIF para corregir rotación de cámaras/móviles
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    dpi = img.info.get("dpi")
    if dpi and isinstance(dpi, (tuple, list)) and len(dpi) >= 2 and dpi[0] > 0 and dpi[1] > 0:
        dpi_x, dpi_y = float(dpi[0]), float(dpi[1])
    elif dpi and isinstance(dpi, (int, float)) and dpi > 0:
        dpi_x, dpi_y = float(dpi), float(dpi)
    else:
        dpi_x, dpi_y = 96.0, 96.0

    ancho_cm = (img.width / dpi_x) * 2.54
    alto_cm = (img.height / dpi_y) * 2.54

    return ancho_cm, alto_cm, img


def importar_recurso(
    ruta_origen: Union[str, Path],
    carpeta_recursos: Union[str, Path],
    id_capa: Optional[str] = None,
    nombre: Optional[str] = None,
) -> CapaDiseno:
    """Importa un archivo SVG o raster a la carpeta de recursos con validación rigurosa."""
    origen = Path(ruta_origen)
    if not origen.exists() or not origen.is_file():
        raise FileNotFoundError(f"El archivo origen no existe: {ruta_origen}")

    destino_dir = Path(carpeta_recursos)
    destino_dir.mkdir(parents=True, exist_ok=True)

    ext = origen.suffix.lower()
    es_svg = ext == ".svg"
    tipo = "svg" if es_svg else "raster"

    if nombre is None:
        nombre = origen.stem

    uid = id_capa or uuid.uuid4().hex[:8]
    stem_limpio = re.sub(r"[^a-zA-Z0-9_\-]", "_", origen.stem)[:30] or "capa"
    nombre_archivo = f"{stem_limpio}_{uid}{ext}"
    ruta_destino = destino_dir / nombre_archivo

    if es_svg:
        ancho_cm, alto_cm, contenido = _validar_y_procesar_svg(origen)
        with open(ruta_destino, "w", encoding="utf-8") as f:
            f.write(contenido)
    else:
        ancho_cm, alto_cm, img = _validar_y_procesar_raster(origen)
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            img.save(ruta_destino)
        else:
            # Convertir otros formatos raster a PNG
            nombre_archivo = f"{stem_limpio}_{uid}.png"
            ruta_destino = destino_dir / nombre_archivo
            img.save(ruta_destino, format="PNG")

    return CapaDiseno(
        id=uid,
        nombre=nombre,
        tipo=tipo,
        archivo=nombre_archivo,
        ancho_natural=round(ancho_cm, 4),
        alto_natural=round(alto_cm, 4),
        x=0.0,
        y=0.0,
        ancho=round(ancho_cm, 4),
        alto=round(alto_cm, 4),
        rotacion=0.0,
        reflejo_h=False,
        reflejo_v=False,
        opacidad=1.0,
        visible=True,
        bloqueada=False,
    )
