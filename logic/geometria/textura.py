"""
Mapeo de texturas y coordenadas UV entre las caras 3D del globo y el lienzo de diseño 2D.

DEFINICIONES:
- Texturas por clave: "superior", "inferior", "pico_A", "pico_B". Cada una es el lienzo plano del GRUPO
  (el abanico del grupo; en el pico, el abanico de 1, 2 o 4 caras según el modo de caras del esquema).
  Coordenadas en cm con +y hacia arriba. El cuadro de la textura es la caja envolvente exacta del
  abanico, sin margen.
- Conos: el gajo global g usa la posición i = g % len(ciclo) del esquema de su sección. La coordenada
  de un vértice de cara sale del movimiento rígido inverso de transformacion_a_gajo(abanico, i),
  aplicado a su uv_cm (en uv_cm y crece del lado estrecho al ancho; en el abanico el lado estrecho
  está a la distancia s0 del ápice). El modo "mitad" y los reflejos NO cambian el mapeo: el reflejo ya
  está dentro de la composición del lienzo.
- Pico: la variante de la pirámide sale de variante_de_piramide(repeticion, h, g). El lienzo del pico
  tiene tantas caras (sub-gajos del abanico) como caras distintas admita el modo: 1 cara si "igual",
  2 caras si "alternado", 4 caras si "cuatro". La cara k (0..3) de la pirámide se mapea a la cara
  correspondiente del lienzo (k % n_caras).
- Coordenadas UV: u = (x - xmin) / ancho, v = (y - ymin) / alto, donde (xmin, ymin, ancho, alto) es la
  caja envolvente del abanico. Convención Three.js: v=1 en la parte superior (y_max) y v=0 en la
  inferior (y_min).
- Resolución en píxeles: calculada proporcionalmente para que el lado mayor tenga max_px (default 2048).
"""
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from logic.models import BalloonInput, BalloonCalculationResult
from logic.geometria.abanico import PiezaPlana, Abanico, pieza_a_geometria_plana, abanico, contorno_abanico
from logic.geometria.malla_trompo import Malla, Cara
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno, obtener_fragmento_capa
from logic.diseno.pintura import variante_de_piramide
from logic.diseno.transformaciones import transformacion_a_gajo, construir_grupo


@dataclass
class InfoTextura:
    """Información geométrica y raster de una textura para Three.js."""
    caja_cm: Tuple[float, float, float, float]  # (xmin, ymin, ancho, alto) en cm
    tam_px: Tuple[int, int]  # (ancho_px, alto_px)
    svg: Optional[str] = None  # Composición SVG lista para renderizar en textura


@dataclass
class MapaTextura:
    """Mapeo completo de texturas y coordenadas UV de la malla 3D."""
    caras_uv: List[Tuple[Optional[str], List[Tuple[float, float]]]]  # [(clave_textura, [(u, v), ...]), ...]
    texturas: Dict[str, InfoTextura] = field(default_factory=dict)


def _calcular_tam_px(ancho_cm: float, alto_cm: float, max_px: int = 2048) -> Tuple[int, int]:
    """Calcula las dimensiones en píxeles manteniendo el aspecto exacto."""
    if ancho_cm <= 1e-6 or alto_cm <= 1e-6:
        return (max_px, max_px)
    lado_mayor = max(ancho_cm, alto_cm)
    factor = max_px / lado_mayor
    px_w = max(1, int(round(ancho_cm * factor)))
    px_h = max(1, int(round(alto_cm * factor)))
    return (px_w, px_h)


def _obtener_n_abanico_cono(esquema: Optional[EsquemaDiseno], num_gajos: int) -> int:
    """Calcula el número de gajos del abanico del grupo para conos."""
    if not esquema:
        return 5
    if esquema.ciclo:
        return len(esquema.ciclo)
    return esquema.tam_grupo or 5


def _obtener_n_caras_pico(esquema_pico: Optional[EsquemaDisenoPico], variante: str = "A") -> int:
    """Determina cuántas caras (1, 2 o 4) tiene el abanico del pico según el modo de caras."""
    if not esquema_pico:
        return 4
    var_obj = esquema_pico.variante_b if (variante == "B" and esquema_pico.usar_variante_b) else esquema_pico.variante_a
    modo = getattr(var_obj, "modo_caras", "igual")
    if modo == "igual":
        return 1
    if modo == "alternado":
        return 2
    return 4


def mapear_vertice_a_abanico(
    uv_cm_pt: Tuple[float, float],
    ab: Abanico,
    i_gajo: int
) -> Tuple[float, float]:
    """Mapea un punto (u_cm, v_cm) canónico de la cara al abanico del grupo en cm."""
    u_pt, v_pt = uv_cm_pt
    s0 = ab.pieza.distancia_vertice
    s1 = ab.pieza.radio_arco
    psi = ab.pieza.angulo_abertura_rad

    r = s0 + v_pt
    w_half = (r / s1) * (ab.pieza.ancho_mayor / 2.0) if s1 > 0 else 0.0

    if w_half > 1e-9:
        frac = max(-1.0, min(1.0, u_pt / w_half))
    else:
        frac = 0.0

    phi = frac * (psi / 2.0)
    xc = r * math.sin(phi)
    yc = r * math.cos(phi) - s0

    t_inv = transformacion_a_gajo(ab, i_gajo).inversa()
    return t_inv.transformar_punto((xc, yc))


def uv_de_punto_cm(
    x_cm: float,
    y_cm: float,
    caja_cm: Tuple[float, float, float, float]
) -> Tuple[float, float]:
    """Calcula coordenadas (u, v) normalizadas [0, 1] respecto a la caja del abanico."""
    xmin, ymin, w, h = caja_cm
    if w <= 1e-9 or h <= 1e-9:
        return (0.0, 0.0)
    u = (x_cm - xmin) / w
    v = (y_cm - ymin) / h
    return (u, v)


def _mapear_cara_cono(
    cara: Cara,
    ab: Abanico,
    n_grupo: int,
    caja_cm: Tuple[float, float, float, float],
    clave: str
) -> Tuple[str, List[Tuple[float, float]]]:
    """Calcula UVs para una cara de cono superior o inferior."""
    i_gajo = cara.gajo % n_grupo
    uvs = []
    for pt in cara.uv_cm:
        x_ab, y_ab = mapear_vertice_a_abanico(pt, ab, i_gajo)
        u, v = uv_de_punto_cm(x_ab, y_ab, caja_cm)
        uvs.append((u, v))
    return (clave, uvs)


def _mapear_cara_pico(
    cara: Cara,
    esquema_pico: Optional[EsquemaDisenoPico],
    abanicos_pico: Dict[str, Abanico],
    cajas_pico: Dict[str, Tuple[float, float, float, float]]
) -> Tuple[str, List[Tuple[float, float]]]:
    """Calcula UVs para una cara de pirámide de pico."""
    modo_rep = esquema_pico.modo_repeticion if esquema_pico else "todas_a"
    usar_b = esquema_pico.usar_variante_b if esquema_pico else False
    h = cara.hilera if cara.hilera is not None else 0
    g = cara.gajo
    var_letra = variante_de_piramide(modo_rep, h, g) if usar_b else "A"
    clave = f"pico_{var_letra}"

    ab = abanicos_pico[clave]
    caja = cajas_pico[clave]
    sub = cara.sub if cara.sub is not None else 0
    i_cara = sub % ab.n

    uvs = []
    for pt in cara.uv_cm:
        x_ab, y_ab = mapear_vertice_a_abanico(pt, ab, i_cara)
        u, v = uv_de_punto_cm(x_ab, y_ab, caja)
        uvs.append((u, v))
    return (clave, uvs)


def mapear_textura(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    malla: Malla,
    configuraciones: Optional[Dict[str, ConfigSeccion]] = None,
    disenos: Optional[Dict[str, Diseno]] = None,
    carpeta_recursos: Optional[Union[str, Path]] = None,
    max_px: int = 2048,
) -> MapaTextura:
    """Mapea cada cara de la malla 3D a su clave de textura y coordenadas UV."""
    configs = configuraciones or {}
    dis_dict = disenos or {}

    # Construir piezas planas
    pz_sup = pieza_a_geometria_plana(resultado, entrada, "superior")
    pz_inf = pieza_a_geometria_plana(resultado, entrada, "inferior")
    pz_pic = pieza_a_geometria_plana(resultado, entrada, "pico")

    # Esquemas y abanicos de conos
    cfg_sup = configs.get("superior")
    n_sup = _obtener_n_abanico_cono(cfg_sup.esquema if cfg_sup else None, entrada.num_gajos)
    ab_sup = abanico(pz_sup, n=n_sup, centrado=True)
    caja_sup = (ab_sup.caja_min_x, ab_sup.caja_min_y, ab_sup.ancho_total, ab_sup.alto_total)

    cfg_inf = configs.get("inferior")
    n_inf = _obtener_n_abanico_cono(cfg_inf.esquema if cfg_inf else None, entrada.num_gajos)
    ab_inf = abanico(pz_inf, n=n_inf, centrado=True)
    caja_inf = (ab_inf.caja_min_x, ab_inf.caja_min_y, ab_inf.ancho_total, ab_inf.alto_total)

    # Esquemas y abanicos de picos
    cfg_pic = configs.get("pico")
    esq_pic = cfg_pic.esquema_pico if cfg_pic else None
    n_pic_a = _obtener_n_caras_pico(esq_pic, "A")
    ab_pic_a = abanico(pz_pic, n=n_pic_a, centrado=True)
    caja_pic_a = (ab_pic_a.caja_min_x, ab_pic_a.caja_min_y, ab_pic_a.ancho_total, ab_pic_a.alto_total)

    n_pic_b = _obtener_n_caras_pico(esq_pic, "B")
    ab_pic_b = abanico(pz_pic, n=n_pic_b, centrado=True)
    caja_pic_b = (ab_pic_b.caja_min_x, ab_pic_b.caja_min_y, ab_pic_b.ancho_total, ab_pic_b.alto_total)

    abanicos_pico = {"pico_A": ab_pic_a, "pico_B": ab_pic_b}
    cajas_pico = {"pico_A": caja_pic_a, "pico_B": caja_pic_b}

    # Estructura de información de texturas
    texturas_info: Dict[str, InfoTextura] = {
        "superior": InfoTextura(caja_sup, _calcular_tam_px(caja_sup[2], caja_sup[3], max_px)),
        "inferior": InfoTextura(caja_inf, _calcular_tam_px(caja_inf[2], caja_inf[3], max_px)),
        "pico_A": InfoTextura(caja_pic_a, _calcular_tam_px(caja_pic_a[2], caja_pic_a[3], max_px)),
        "pico_B": InfoTextura(caja_pic_b, _calcular_tam_px(caja_pic_b[2], caja_pic_b[3], max_px)),
    }

    # Generar SVGs de textura si hay capas visibles
    for clave, caja in [
        ("superior", caja_sup),
        ("inferior", caja_inf),
        ("pico_A", caja_pic_a),
        ("pico_B", caja_pic_b),
    ]:
        dis = dis_dict.get(clave)
        tiene_capas = bool(dis and any(c.visible for c in dis.capas))
        if tiene_capas:
            sec_nombre = "pico" if clave.startswith("pico") else clave
            cfg = configs.get(sec_nombre)
            svg_str = svg_textura(
                clave=clave,
                entrada=entrada,
                resultado=resultado,
                diseno=dis,
                config_seccion=cfg,
                carpeta_recursos=carpeta_recursos,
                max_px=max_px,
            )
            texturas_info[clave].svg = svg_str

    # Mapeo por cara
    caras_uv: List[Tuple[Optional[str], List[Tuple[float, float]]]] = []
    for c in malla.caras:
        if c.seccion == "superior":
            caras_uv.append(_mapear_cono_con_filtro("superior", c, ab_sup, n_sup, caja_sup, texturas_info))
        elif c.seccion == "inferior":
            caras_uv.append(_mapear_cono_con_filtro("inferior", c, ab_inf, n_inf, caja_inf, texturas_info))
        elif c.seccion == "pico":
            caras_uv.append(_mapear_pico_con_filtro(c, esq_pic, abanicos_pico, cajas_pico, texturas_info))
        else:
            caras_uv.append((None, [(0.0, 0.0) for _ in c.indices_vertices]))

    return MapaTextura(caras_uv=caras_uv, texturas=texturas_info)


def _mapear_cono_con_filtro(
    clave: str,
    cara: Cara,
    ab: Abanico,
    n_grupo: int,
    caja: Tuple[float, float, float, float],
    texturas_info: Dict[str, InfoTextura]
) -> Tuple[Optional[str], List[Tuple[float, float]]]:
    k, uvs = _mapear_cara_cono(cara, ab, n_grupo, caja, clave)
    if texturas_info[clave].svg is None:
        return (None, uvs)
    return (k, uvs)


def _mapear_pico_con_filtro(
    cara: Cara,
    esq_pic: Optional[EsquemaDisenoPico],
    abanicos_pico: Dict[str, Abanico],
    cajas_pico: Dict[str, Tuple[float, float, float, float]],
    texturas_info: Dict[str, InfoTextura]
) -> Tuple[Optional[str], List[Tuple[float, float]]]:
    k, uvs = _mapear_cara_pico(cara, esq_pic, abanicos_pico, cajas_pico)
    if texturas_info[k].svg is None:
        return (None, uvs)
    return (k, uvs)


def _renderizar_elemento_svg_textura(
    capa: CapaDiseno,
    carpeta_recursos: Optional[Path],
    opacidad_mult: float = 1.0,
) -> str:
    """Renderiza una capa individual en el espacio SVG del abanico (x_svg = x_cm, y_svg = -y_cm)."""
    if not capa.visible:
        return ""

    cx_cm = capa.x + capa.ancho / 2.0
    cy_cm = capa.y + capa.alto / 2.0
    w_cm = capa.ancho
    h_cm = capa.alto

    # Convención de textura: el lienzo tiene +y_cm hacia arriba (v=1 en ymax con flipY=true en Three.js),
    # por lo que en SVG (+y hacia abajo, viewBox desde -ymax) el centro queda en (cx_cm, -cy_cm)
    # y el borde superior de la capa (cy_cm + h/2) queda en y_svg = -cy_cm - h/2 = -(capa.y + capa.alto).
    cx_svg = cx_cm
    cy_svg = -cy_cm
    x_svg = cx_svg - w_cm / 2.0
    y_svg = cy_svg - h_cm / 2.0

    transforms = []
    if abs(capa.rotacion) > 1e-4:
        transforms.append(f"rotate({-capa.rotacion:.2f} {cx_svg:.4f} {cy_svg:.4f})")
    if capa.reflejo_h:
        transforms.append(f"translate({cx_svg:.4f} {cy_svg:.4f}) scale(-1 1) translate({-cx_svg:.4f} {-cy_svg:.4f})")
    if capa.reflejo_v:
        transforms.append(f"translate({cx_svg:.4f} {cy_svg:.4f}) scale(1 -1) translate({-cx_svg:.4f} {-cy_svg:.4f})")

    trans_str = f' transform="{" ".join(transforms)}"' if transforms else ""
    opac = max(0.0, min(1.0, capa.opacidad * opacidad_mult))

    contenido_frag, vb = obtener_fragmento_capa(capa, carpeta_recursos, vista_previa=False)

    if capa.tipo == "svg" and contenido_frag:
        vx, vy, vw, vh = vb
        if vw > 0 and vh > 0:
            s = min(w_cm / vw, h_cm / vh)
            dx = (w_cm - vw * s) / 2.0 - vx * s
            dy = (h_cm - vh * s) / 2.0 - vy * s
            t_local = f"translate({x_svg:.4f} {y_svg:.4f}) translate({dx:.4f} {dy:.4f}) scale({s:.6f})"
            return (
                f'<g id="capa-{capa.id}" opacity="{opac:.2f}"{trans_str}>\n'
                f'  <g transform="{t_local}">\n'
                f'{contenido_frag}\n'
                f'  </g>\n'
                f'</g>'
            )
    elif capa.tipo != "svg" and contenido_frag:
        return (
            f'<image href="{contenido_frag}" x="{x_svg:.4f}" y="{y_svg:.4f}" '
            f'width="{w_cm:.4f}" height="{h_cm:.4f}" opacity="{opac:.2f}"{trans_str} id="capa-{capa.id}"/>'
        )

    return ""


def svg_textura(
    clave: str,
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    diseno: Optional[Diseno],
    config_seccion: Optional[ConfigSeccion] = None,
    carpeta_recursos: Optional[Union[str, Path]] = None,
    max_px: int = 2048,
) -> str:
    """Genera la composición SVG pura del diseño para usarse como textura de Three.js."""
    if clave.startswith("pico"):
        seccion = "pico"
        var_letra = "B" if clave.endswith("B") else "A"
    else:
        seccion = clave
        var_letra = "A"

    cfg = config_seccion
    esquema = cfg.esquema if (cfg and seccion != "pico") else None
    esquema_pico = cfg.esquema_pico if (cfg and seccion == "pico") else None
    dibujar = cfg.dibujar if (cfg and seccion != "pico") else "completo"

    pz = pieza_a_geometria_plana(resultado, entrada, seccion)
    if seccion == "pico":
        n = _obtener_n_caras_pico(esquema_pico, var_letra)
    else:
        n = _obtener_n_abanico_cono(esquema, entrada.num_gajos)

    ab = abanico(pz, n=n, centrado=True)
    xmin = ab.caja_min_x
    ymin = ab.caja_min_y
    w = ab.ancho_total
    h = ab.alto_total
    ymax = ab.caja_max_y

    px_w, px_h = _calcular_tam_px(w, h, max_px)
    carp_rec = Path(carpeta_recursos) if carpeta_recursos else None

    # Contornos de recorte en coordenadas SVG (x_svg = x, y_svg = -y)
    pasos_arco = max(8, n * 6)
    pts_contorno = contorno_abanico(pz, n, dibujar=dibujar, pasos_arco=pasos_arco)
    d_contorno = "M " + " L ".join(f"{x:.4f},{-y:.4f}" for x, y in pts_contorno) + " Z"

    d_contorno_ref = ""
    if dibujar == "mitad":
        pts_contorno_ref = [(-x, y) for x, y in pts_contorno]
        d_contorno_ref = "M " + " L ".join(f"{x:.4f},{-y:.4f}" for x, y in pts_contorno_ref) + " Z"

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{px_w}" height="{px_h}" viewBox="{xmin:.4f} {-ymax:.4f} {w:.4f} {h:.4f}"',
        '     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',
        '  <defs>',
        '    <clipPath id="clip-textura">',
        f'      <path d="{d_contorno}"/>',
        '    </clipPath>',
    ]
    if d_contorno_ref:
        lines.extend([
            '    <clipPath id="clip-textura-reflejo">',
            f'      <path d="{d_contorno_ref}"/>',
            '    </clipPath>',
        ])
    lines.append('  </defs>')

    if diseno and diseno.capas:
        lines.extend(_generar_capas_svg_textura(diseno, esquema, dibujar, d_contorno_ref, carp_rec))

    lines.append('</svg>')
    return "\n".join(lines)


def _generar_capas_svg_textura(
    diseno: Diseno,
    esquema: Optional[EsquemaDiseno],
    dibujar: str,
    d_contorno_ref: str,
    carp_rec: Optional[Path]
) -> List[str]:
    """Genera los grupos de elementos SVG para las capas activas y reflejadas."""
    res: List[str] = []
    if dibujar == "mitad":
        res.append('    <g id="diseno-mitad-activa" clip-path="url(#clip-textura)">')
        for c in diseno.capas:
            elem = _renderizar_elemento_svg_textura(c, carp_rec, opacidad_mult=1.0)
            if elem:
                res.append(f'      {elem}')
        res.append('    </g>')

        if d_contorno_ref:
            todas_capas = construir_grupo(diseno, esquema, modo_lienzo="mitad")
            res.append('    <g id="diseno-mitad-reflejo" clip-path="url(#clip-textura-reflejo)">')
            for c in todas_capas:
                if c.id.endswith("_reflejo"):
                    elem = _renderizar_elemento_svg_textura(c, carp_rec, opacidad_mult=1.0)
                    if elem:
                        res.append(f'      {elem}')
            res.append('    </g>')
    else:
        res.append('    <g id="diseno-completo" clip-path="url(#clip-textura)">')
        for c in diseno.capas:
            elem = _renderizar_elemento_svg_textura(c, carp_rec, opacidad_mult=1.0)
            if elem:
                res.append(f'      {elem}')
        res.append('    </g>')
    return res

