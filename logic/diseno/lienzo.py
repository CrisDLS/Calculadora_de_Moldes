import io
import base64
import re
import uuid
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
from PIL import Image, ImageOps
import defusedxml.ElementTree as ET
import xml.etree.ElementTree as xml_ET

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
    viewbox: Optional[Tuple[float, float, float, float]] = None
    complejo: bool = False
    aviso: Optional[str] = None
    elementos_count: int = 0
    tam_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = {
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
        if self.viewbox is not None:
            d["viewbox"] = list(self.viewbox)
        if self.complejo:
            d["complejo"] = True
        if self.aviso:
            d["aviso"] = self.aviso
        if self.elementos_count > 0:
            d["elementos_count"] = self.elementos_count
        if self.tam_bytes > 0:
            d["tam_bytes"] = self.tam_bytes
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapaDiseno":
        vb = None
        if "viewbox" in data and isinstance(data["viewbox"], (list, tuple)) and len(data["viewbox"]) == 4:
            vb = tuple(float(v) for v in data["viewbox"])
        return cls(
            id=str(data["id"]),
            nombre=str(data.get("nombre", "Capa")),
            tipo=str(data.get("tipo", "raster")),
            archivo=str(data.get("archivo", "")),
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
            viewbox=vb,
            complejo=bool(data.get("complejo", False)),
            aviso=data.get("aviso"),
            elementos_count=int(data.get("elementos_count", 0)),
            tam_bytes=int(data.get("tam_bytes", 0)),
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


CACHE_FRAGMENTOS_CAPA: Dict[Tuple[str, str, str, bool], Tuple[str, Tuple[float, float, float, float]]] = {}


def limpiar_cache_fragmentos():
    """Limpia la caché de fragmentos de capas."""
    CACHE_FRAGMENTOS_CAPA.clear()


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


def _validar_y_procesar_svg(
    ruta: Path,
    id_capa: str = "",
) -> Tuple[float, float, str, Tuple[float, float, float, float], int, int, bool, Optional[str], str]:
    """Valida seguridad de un archivo SVG, sanea namespaces, extrae viewBox y genera hijos limpios."""
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
    elementos = list(root.iter())
    num_elem = len(elementos)

    for elem in elementos:
        tag_local = elem.tag.split("}")[-1].lower()
        if tag_local in ("script", "foreignobject"):
            raise ValueError(f"El SVG contiene etiqueta no permitida: <{tag_local}>")

        for attr, val in list(elem.attrib.items()):
            attr_local = attr.split("}")[-1].lower()
            if attr_local.startswith("on"):
                raise ValueError(f"El SVG contiene evento no permitido: {attr_local}")
            if attr_local in ("href", "xlink:href", "src"):
                val_limpio = val.strip().lower()
                if val_limpio.startswith(("http:", "https:", "file:", "ftp:", "//")):
                    raise ValueError(f"El SVG contiene enlace externo no permitido: {val}")
                if val_limpio.startswith("data:") and not val_limpio.startswith(("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp")):
                    raise ValueError("El SVG contiene URI de datos no permitida.")

    # Extraer dimensiones naturales y viewBox
    ancho_cm = None
    alto_cm = None
    vb_tuple = None

    if "viewBox" in root.attrib:
        partes = [p for p in re.split(r"[\s,]+", root.attrib["viewBox"].strip()) if p]
        if len(partes) == 4:
            try:
                vx = float(partes[0])
                vy = float(partes[1])
                vw = float(partes[2])
                vh = float(partes[3])
                if vw > 0 and vh > 0:
                    vb_tuple = (vx, vy, vw, vh)
                    ancho_cm = vw * (2.54 / 96.0)
                    alto_cm = vh * (2.54 / 96.0)
            except ValueError:
                pass

    ancho_attr = root.attrib.get("width")
    alto_attr = root.attrib.get("height")
    if ancho_attr and not ancho_attr.endswith("%"):
        c = _parsear_dimension_svg(ancho_attr)
        if c:
            ancho_cm = c
    if alto_attr and not alto_attr.endswith("%"):
        c = _parsear_dimension_svg(alto_attr)
        if c:
            alto_cm = c

    if ancho_cm is None or ancho_cm <= 0:
        ancho_cm = 10.0
    if alto_cm is None or alto_cm <= 0:
        alto_cm = 10.0

    if vb_tuple is None:
        vb_tuple = (0.0, 0.0, ancho_cm * (96.0 / 2.54), alto_cm * (96.0 / 2.54))

    complejo = (num_elem > 20000 or tam_bytes > 5 * 1024 * 1024)
    aviso = "SVG muy complejo: la vista previa puede ser lenta" if complejo else None

    # Registrar namespaces estándar para que ElementTree no agregue prefijos como ns0:
    xml_ET.register_namespace('', 'http://www.w3.org/2000/svg')
    xml_ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    xml_ET.register_namespace('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
    xml_ET.register_namespace('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')

    # Prefijar IDs para garantizar unicidad y actualizar referencias internas
    if id_capa:
        prefijo = f"c_{id_capa}_"
        id_map = {}
        for elem in root.iter():
            old_id = elem.attrib.get("id")
            if old_id:
                new_id = f"{prefijo}{old_id}"
                elem.attrib["id"] = new_id
                id_map[old_id] = new_id

        if id_map:
            for elem in root.iter():
                for k, v in list(elem.attrib.items()):
                    k_local = k.split("}")[-1].lower()
                    if k_local in ("fill", "stroke", "clip-path", "filter", "mask"):
                        for old_id, new_id in id_map.items():
                            if f"url(#{old_id})" in v:
                                elem.attrib[k] = v.replace(f"url(#{old_id})", f"url(#{new_id})")
                    elif k_local in ("href",):
                        for old_id, new_id in id_map.items():
                            if v == f"#{old_id}":
                                elem.attrib[k] = f"#{new_id}"

    # Extraer hijos útiles de <svg>
    hijos_xml = []
    for child in list(root):
        tag_local = child.tag.split("}")[-1].lower()
        if tag_local not in ("namedview", "metadata"):
            hijos_xml.append(xml_ET.tostring(child, encoding="utf-8").decode("utf-8"))
    contenido_hijos_str = "\n".join(hijos_xml)

    contenido_limpio = xml_ET.tostring(root, encoding="utf-8").decode("utf-8")

    return ancho_cm, alto_cm, contenido_limpio, vb_tuple, num_elem, tam_bytes, complejo, aviso, contenido_hijos_str


def _validar_y_procesar_raster(ruta: Path) -> Tuple[float, float, Image.Image, int, int]:
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

    return ancho_cm, alto_cm, img, img.width, img.height


def obtener_fragmento_capa(
    capa: CapaDiseno,
    carpeta_recursos: Optional[Path],
    vista_previa: bool = True,
) -> Tuple[str, Tuple[float, float, float, float]]:
    """Obtiene el contenido SVG nativo o data-URI y el viewBox de la capa, utilizando caché."""
    clave = (capa.id, capa.archivo, capa.tipo, vista_previa)
    if clave in CACHE_FRAGMENTOS_CAPA:
        return CACHE_FRAGMENTOS_CAPA[clave]

    if not carpeta_recursos:
        return ("", capa.viewbox or (0.0, 0.0, 100.0, 100.0))

    arch = carpeta_recursos / capa.archivo
    if not arch.exists() or not arch.is_file():
        return ("", capa.viewbox or (0.0, 0.0, 100.0, 100.0))

    if capa.tipo == "svg":
        _, _, _, vb, _, _, _, _, hijos_xml = _validar_y_procesar_svg(arch, id_capa=capa.id)
        res = (hijos_xml, vb)
        CACHE_FRAGMENTOS_CAPA[clave] = res
        return res
    else:
        # Raster (JPG / PNG)
        try:
            img = Image.open(arch)
            img.load()
            w_orig, h_orig = img.width, img.height
            fmt = "JPEG" if arch.suffix.lower() in (".jpg", ".jpeg") else "PNG"
            mime = "image/jpeg" if fmt == "JPEG" else "image/png"

            if vista_previa and max(w_orig, h_orig) > 1600:
                img_prev = img.copy()
                img_prev.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                if fmt == "JPEG" and img_prev.mode in ("RGBA", "P"):
                    img_prev = img_prev.convert("RGB")
                img_prev.save(buf, format=fmt, quality=85)
                b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
            else:
                b64_str = base64.b64encode(arch.read_bytes()).decode("ascii")

            data_uri = f"data:{mime};base64,{b64_str}"
            vb = (0.0, 0.0, float(w_orig), float(h_orig))
            res = (data_uri, vb)
            CACHE_FRAGMENTOS_CAPA[clave] = res
            return res
        except Exception as e:
            try:
                from logic.registro import logger
                logger.warning(f"Error al obtener fragmento de capa '{capa.nombre}': {e}")
            except Exception:
                pass
            vb = (0.0, 0.0, 100.0, 100.0)
            return ("", vb)


def ajustar_capa(
    capa: CapaDiseno,
    ventana: Tuple[float, float, float, float],
    modo: str,
) -> CapaDiseno:
    """Ajusta las coordenadas y dimensiones de una capa según la ventana especificada.
    
    ventana = (min_x, min_y, max_x, max_y) en cm.
    modos:
      - 'cubrir': escala conservando proporción para cubrir toda la ventana, centrada.
      - 'contener': escala conservando proporción para caber completa en la ventana, centrada.
      - 'estirar': llena exactamente la ventana modificando ancho y alto, centrada.
      - 'ancho': ajusta al ancho de ventana conservando proporción, centrada en X y apoyada en min_y.
      - 'alto': ajusta al alto de ventana conservando proporción, centrada en X y Y.
      - 'centrar': conserva ancho y alto actuales, sólo centra la capa en la ventana.
    """
    min_x, min_y, max_x, max_y = ventana
    w_v = max(1e-4, max_x - min_x)
    h_v = max(1e-4, max_y - min_y)
    cx_v = (min_x + max_x) / 2.0
    cy_v = (min_y + max_y) / 2.0

    w0 = capa.ancho_natural if capa.ancho_natural > 0 else capa.ancho
    h0 = capa.alto_natural if capa.alto_natural > 0 else capa.alto
    w0 = max(1e-4, w0)
    h0 = max(1e-4, h0)

    # Considerar rotación en la caja envolvente
    ang_rad = math.radians(capa.rotacion)
    cos_a = abs(math.cos(ang_rad))
    sin_a = abs(math.sin(ang_rad))

    w_rot0 = w0 * cos_a + h0 * sin_a
    h_rot0 = w0 * sin_a + h0 * cos_a

    modo_lower = modo.lower()

    if modo_lower == "centrar":
        w_final = capa.ancho
        h_final = capa.alto
        x_final = cx_v - w_final / 2.0
        y_final = cy_v - h_final / 2.0

    elif modo_lower == "contener":
        s = min(w_v / w_rot0, h_v / h_rot0)
        w_final = s * w0
        h_final = s * h0
        x_final = cx_v - w_final / 2.0
        y_final = cy_v - h_final / 2.0

    elif modo_lower == "cubrir":
        s = max(w_v / w_rot0, h_v / h_rot0)
        w_final = s * w0
        h_final = s * h0
        x_final = cx_v - w_final / 2.0
        y_final = cy_v - h_final / 2.0

    elif modo_lower == "estirar":
        if abs(capa.rotacion) < 1e-4:
            w_final = w_v
            h_final = h_v
        else:
            det = cos_a * cos_a - sin_a * sin_a
            if abs(det) > 1e-3:
                w_cand = (w_v * cos_a - h_v * sin_a) / det
                h_cand = (h_v * cos_a - w_v * sin_a) / det
                if w_cand > 0 and h_cand > 0:
                    w_final = w_cand
                    h_final = h_cand
                else:
                    s = min(w_v / w_rot0, h_v / h_rot0)
                    w_final = s * w0
                    h_final = s * h0
            else:
                s = min(w_v / w_rot0, h_v / h_rot0)
                w_final = s * w0
                h_final = s * h0
        x_final = cx_v - w_final / 2.0
        y_final = cy_v - h_final / 2.0

    elif modo_lower == "ancho":
        s = w_v / w_rot0
        w_final = s * w0
        h_final = s * h0
        x_final = cx_v - w_final / 2.0
        # Apoyada en el fondo (y = min_y):
        h_rot_final = w_final * sin_a + h_final * cos_a
        cy_final = min_y + h_rot_final / 2.0
        y_final = cy_final - h_final / 2.0

    elif modo_lower == "alto":
        s = h_v / h_rot0
        w_final = s * w0
        h_final = s * h0
        x_final = cx_v - w_final / 2.0
        y_final = cy_v - h_final / 2.0

    else:
        raise ValueError(f"Modo de ajuste no reconocido: {modo}. Use 'cubrir', 'contener', 'estirar', 'ancho', 'alto' o 'centrar'.")

    return CapaDiseno(
        id=capa.id,
        nombre=capa.nombre,
        tipo=capa.tipo,
        archivo=capa.archivo,
        ancho_natural=capa.ancho_natural,
        alto_natural=capa.alto_natural,
        x=round(x_final, 4),
        y=round(y_final, 4),
        ancho=round(w_final, 4),
        alto=round(h_final, 4),
        rotacion=capa.rotacion,
        reflejo_h=capa.reflejo_h,
        reflejo_v=capa.reflejo_v,
        opacidad=capa.opacidad,
        visible=capa.visible,
        bloqueada=capa.bloqueada,
    )


def importar_recurso(
    ruta_origen: Union[str, Path],
    carpeta_recursos: Union[str, Path],
    id_capa: Optional[str] = None,
    nombre: Optional[str] = None,
    ventana: Optional[Tuple[float, float, float, float]] = None,
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
        ancho_cm, alto_cm, contenido, vb, num_elem, tam_bytes, complejo, aviso, hijos_xml = _validar_y_procesar_svg(origen, id_capa=uid)
        with open(ruta_destino, "w", encoding="utf-8") as f:
            f.write(contenido)
        CACHE_FRAGMENTOS_CAPA[(uid, nombre_archivo, "svg", True)] = (hijos_xml, vb)
        CACHE_FRAGMENTOS_CAPA[(uid, nombre_archivo, "svg", False)] = (hijos_xml, vb)
    else:
        ancho_cm, alto_cm, img, w_px, h_px = _validar_y_procesar_raster(origen)
        tam_bytes = origen.stat().st_size
        num_elem = 1
        vb = (0.0, 0.0, float(w_px), float(h_px))
        complejo = (w_px > 4000 or h_px > 4000 or tam_bytes > 5 * 1024 * 1024)
        aviso = "Imagen muy grande: se usa vista previa optimizada en pantalla" if complejo else None

        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            img.save(ruta_destino)
        else:
            # Convertir otros formatos raster a PNG
            nombre_archivo = f"{stem_limpio}_{uid}.png"
            ruta_destino = destino_dir / nombre_archivo
            img.save(ruta_destino, format="PNG")

    capa = CapaDiseno(
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
        viewbox=vb,
        complejo=complejo,
        aviso=aviso,
        elementos_count=num_elem,
        tam_bytes=tam_bytes,
    )

    try:
        from logic.registro import logger
        logger.info(
            f"Capa importada: '{nombre}' ({tipo}), dims={ancho_cm:.1f}x{alto_cm:.1f} cm, "
            f"viewBox={vb}, elementos={num_elem}, bytes={tam_bytes}"
        )
    except Exception:
        pass

    if ventana is not None:
        capa = ajustar_capa(capa, ventana, modo="contener")

    return capa
