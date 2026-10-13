import math
import warnings
import base64
from pathlib import Path
from typing import List, Tuple, Optional, Union
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.estilos import EstiloSvg, IMPRESION
from logic.geometria.abanico import pieza_a_geometria_plana, abanico, PiezaPlana, Abanico
from logic.diseno.lienzo import Diseno, CapaDiseno
from logic.diseno.transformaciones import construir_grupo

def svg_abanico(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    seccion: str,
    esquema: Optional[EsquemaDiseno] = None,
    estilo: EstiloSvg = IMPRESION,
    escala: Union[str, float, int] = "auto",
    hoja: str = "carta",
    margen_mm: float = 10.0,
    dibujar: str = "completo",
    diseno: Optional[Diseno] = None,
    unir_grupos: bool = False,
    carpeta_recursos: Optional[Union[str, Path]] = None,
) -> str:
    """Genera un SVG con la hoja de trazo en abanico para impresión o Inkscape.
    
    Orientación: ápice / lado estrecho ABAJO.
    Escala auto: prueba orientaciones de hoja para maximizar aprovechamiento.
    Capas Inkscape: papel, cuadricula, ejes, aristas_comunes, contorno, costura, rotulos (y pestana).
    """
    if hoja not in ["carta", "a4"]:
        raise ValueError(f"Hoja no soportada: {hoja}. Use 'carta' o 'a4'.")

    hoja_w, hoja_h = (215.9, 279.4) if hoja == "carta" else (210.0, 297.0)

    # 1. Determinar número de gajos n
    if seccion == "pico":
        n = 4 if dibujar == "completo" else 2
    else:
        tam_g = esquema.tam_grupo if esquema else 5
        if unir_grupos and esquema and esquema.modo == "repeticion":
            reps = entrada.num_gajos // tam_g
            n = min(entrada.num_gajos, tam_g * 2) if reps >= 2 else tam_g
        elif dibujar == "mitad":
            n = (tam_g + 1) // 2
        else:
            n = tam_g

    # 2. Geometría pura
    pieza = pieza_a_geometria_plana(resultado, entrada, seccion)
    ab = abanico(pieza, n=n, centrado=True)

    psi = pieza.angulo_abertura_rad
    s0 = pieza.distancia_vertice
    s1 = pieza.radio_arco
    costura_cm = entrada.ancho_costura

    # Incluir pestaña en cono inferior para el cálculo de caja
    pestana_cm = 0.0
    if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
        pestana_cm = entrada.pestana_boca

    # Calcular bounding box total considerando si la pestaña expande hacia adentro
    min_x_cm = ab.caja_min_x
    max_x_cm = ab.caja_max_x
    min_y_cm = ab.caja_min_y
    max_y_cm = ab.caja_max_y

    if pestana_cm > 0:
        r_pestana = max(0.0, s0 - pestana_cm)
        # Puntos de pestaña
        ang_min = -n * psi / 2.0
        ang_max = n * psi / 2.0
        pts_pest = [
            (r_pestana * math.sin(ang_min), r_pestana * math.cos(ang_min)),
            (r_pestana * math.sin(ang_max), r_pestana * math.cos(ang_max)),
        ]
        min_x_cm = min(min_x_cm, *(p[0] for p in pts_pest))
        max_x_cm = max(max_x_cm, *(p[0] for p in pts_pest))
        min_y_cm = min(min_y_cm, *(p[1] for p in pts_pest))
        max_y_cm = max(max_y_cm, *(p[1] for p in pts_pest))

    w_cm = max_x_cm - min_x_cm
    h_cm = max_y_cm - min_y_cm

    # 3. Cálculo de escala y orientación óptima
    def compute_s(orient: str) -> Optional[float]:
        w_page, h_page = (hoja_w, hoja_h) if orient == "vertical" else (hoja_h, hoja_w)
        avail_w = w_page - 2 * margen_mm
        avail_h = h_page - 2 * margen_mm
        if avail_w <= 0 or avail_h <= 0:
            return None
        s_x = (w_cm * 10.0) / avail_w
        s_y = (h_cm * 10.0) / avail_h
        return max(s_x, s_y)

    mejor_orientacion = "vertical"
    if str(escala).lower() == "auto":
        s_vert = compute_s("vertical")
        s_horiz = compute_s("horizontal")
        if s_horiz and (s_vert is None or s_horiz < s_vert):
            mejor_orientacion = "horizontal"
            factor_s = s_horiz
        else:
            mejor_orientacion = "vertical"
            factor_s = s_vert
    else:
        factor_s = float(escala)
        s_vert = compute_s("vertical")
        s_horiz = compute_s("horizontal")
        if s_vert and factor_s >= s_vert:
            mejor_orientacion = "vertical"
        elif s_horiz and factor_s >= s_horiz:
            mejor_orientacion = "horizontal"
            warnings.warn("No cabía en vertical, se cambió a horizontal automáticamente.")
        else:
            raise ValueError(f"No cabe a escala 1:{escala} con los márgenes especificados.")

    if not factor_s or factor_s <= 0:
        factor_s = 10.0

    w_page, h_page = (hoja_w, hoja_h) if mejor_orientacion == "vertical" else (hoja_h, hoja_w)
    avail_w = w_page - 2 * margen_mm
    avail_h = h_page - 2 * margen_mm

    factor = 10.0 / factor_s  # mm por cm real

    # Centrado en el área útil de la página
    cx_page = margen_mm + avail_w / 2.0
    cy_page = margen_mm + avail_h / 2.0

    y_mid_cm = (min_y_cm + max_y_cm) / 2.0

    # Transformación cm -> mm SVG con ÁPICE ABAJO:
    # x_cm=0 queda en cx_page
    # y_cm creciendo hacia el extremo ancho va hacia ARRIBA (menor Y en SVG)
    def to_svg(x: float, y: float) -> Tuple[float, float]:
        xs = cx_page + x * factor
        ys = cy_page - (y - y_mid_cm) * factor
        return xs, ys

    # Parámetros angulares
    ang_min = -n * psi / 2.0
    ang_max = n * psi / 2.0

    # 4. Calcular contorno exterior del abanico primero (para clipPath y para la capa de contorno)
    pts_contorno_svg: List[Tuple[float, float]] = []
    pasos_arco = max(8, n * 6)
    if s0 > 1e-4:
        # Cono inferior:
        # 1. Lateral izquierdo (s0 a s1 en ang_min)
        pts_contorno_svg.append(to_svg(s0 * math.sin(ang_min), s0 * math.cos(ang_min)))
        pts_contorno_svg.append(to_svg(s1 * math.sin(ang_min), s1 * math.cos(ang_min)))
        # 2. Borde exterior ancho (s1 de ang_min a ang_max)
        for st in range(1, pasos_arco + 1):
            ang = ang_min + (ang_max - ang_min) * (st / pasos_arco)
            pts_contorno_svg.append(to_svg(s1 * math.sin(ang), s1 * math.cos(ang)))
        # 3. Lateral derecho (s1 a s0 en ang_max)
        pts_contorno_svg.append(to_svg(s0 * math.sin(ang_max), s0 * math.cos(ang_max)))
        # 4. Borde interior estrecho (s0 de ang_max a ang_min)
        for st in range(1, pasos_arco + 1):
            ang = ang_max - (ang_max - ang_min) * (st / pasos_arco)
            pts_contorno_svg.append(to_svg(s0 * math.sin(ang), s0 * math.cos(ang)))
    else:
        # Cono superior o pico:
        pts_contorno_svg.append(to_svg(0.0, 0.0))
        pts_contorno_svg.append(to_svg(s1 * math.sin(ang_min), s1 * math.cos(ang_min)))
        if seccion == "pico":
            # Bases rectas por cada cara de la pirámide
            for k in range(1, n + 1):
                ang_k = ang_min + k * psi
                pts_contorno_svg.append(to_svg(s1 * math.sin(ang_k), s1 * math.cos(ang_k)))
        else:
            for st in range(1, pasos_arco + 1):
                ang = ang_min + (ang_max - ang_min) * (st / pasos_arco)
                pts_contorno_svg.append(to_svg(s1 * math.sin(ang), s1 * math.cos(ang)))
        pts_contorno_svg.append(to_svg(0.0, 0.0))

    d_contorno = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_contorno_svg) + " Z"

    # 5. Construir elementos SVG
    lines = [
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{w_page:.2f}mm" height="{h_page:.2f}mm" viewBox="0 0 {w_page:.2f} {h_page:.2f}"',
        f'     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
        f'  <defs>',
        f'    <clipPath id="clip-abanico">',
        f'      <path d="{d_contorno}"/>',
        f'    </clipPath>',
        f'  </defs>',
    ]

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    # Capa: papel
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="papel" id="layer-papel">')
    # Margen útil punteado
    w_papel_trazo = 0.2 * estilo.factor_trazo
    lines.append(f'    <rect x="{margen_mm:.2f}" y="{margen_mm:.2f}" width="{avail_w:.2f}" height="{avail_h:.2f}" '
                 f'fill="none" stroke="{estilo.cuadricula}" stroke-width="{w_papel_trazo:.2f}" stroke-dasharray="3,3" id="margen-util"/>')
    lines.append('  </g>')

    # Capa: cuadricula (arcos o rectas de cada paso)
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="cuadricula" id="layer-cuadricula">')
    w_cuad = 0.2 * estilo.factor_trazo

    for idx_paso, y_paso in enumerate(ab.pasos_radiales):
        r_paso = y_paso
        if r_paso <= 1e-4:
            continue
        pts_paso_svg = []
        for st in range(pasos_arco + 1):
            ang = ang_min + (ang_max - ang_min) * (st / pasos_arco)
            pts_paso_svg.append(to_svg(r_paso * math.sin(ang), r_paso * math.cos(ang)))
        d_arco = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_paso_svg)
        lines.append(f'    <path d="{d_arco}" fill="none" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="cuad-paso-{idx_paso}"/>')

        # Número de paso sobre el eje central
        px_num, py_num = to_svg(0.0, r_paso)
        fs_paso = max(1.8 * estilo.factor_texto, w_page * 0.012)
        lines.append(f'    <text x="{px_num + 1.5:.2f}" y="{py_num:.2f}" font-size="{fs_paso:.2f}" fill="{estilo.texto}" '
                     f'font-family="sans-serif" dominant-baseline="middle">{idx_paso}</text>')
    lines.append('  </g>')

    # Capa: diseno (recortada por el contorno del abanico)
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="diseno" id="layer-diseno" clip-path="url(#clip-abanico)">')
    if diseno and diseno.capas:
        carp_rec = Path(carpeta_recursos) if carpeta_recursos else None
        capas_a_dibujar = construir_grupo(diseno, esquema, modo_lienzo=dibujar)
        for c in capas_a_dibujar:
            es_ref = c.id.endswith("_reflejo")
            opac_mult = 0.5 if (dibujar == "mitad" and es_ref) else 1.0
            elem_svg = _renderizar_capa_en_abanico(c, to_svg, factor, carp_rec, opacidad_mult=opac_mult)
            if elem_svg:
                lines.append(f'    {elem_svg}')
    lines.append('  </g>')

    # Capa: ejes
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="ejes" id="layer-ejes">')
    w_eje = 0.3 * estilo.factor_trazo
    for i, (p0, p1) in enumerate(ab.ejes):
        p0_svg = to_svg(p0[0], p0[1])
        p1_svg = to_svg(p1[0], p1[1])
        lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                     f'stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" stroke-dasharray="4,2" id="eje-gajo-{i}"/>')

    # Si estamos en modo mitad, resaltar el eje de simetría / espejo
    if dibujar == "mitad":
        p_esp_0 = to_svg(0.0, s0)
        p_esp_1 = to_svg(0.0, s1)
        w_esp = 0.6 * estilo.factor_trazo
        lines.append(f'    <line x1="{p_esp_0[0]:.2f}" y1="{p_esp_0[1]:.2f}" x2="{p_esp_1[0]:.2f}" y2="{p_esp_1[1]:.2f}" '
                     f'stroke="{estilo.eje}" stroke-width="{w_esp:.2f}" stroke-dasharray="6,3" id="eje-espejo-simetria"/>')
    lines.append('  </g>')

    # Capa: aristas_comunes
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="aristas_comunes" id="layer-aristas-comunes">')
    w_arista = 0.3 * estilo.factor_trazo
    for i, (p0, p1) in enumerate(ab.aristas_comunes):
        p0_svg = to_svg(p0[0], p0[1])
        p1_svg = to_svg(p1[0], p1[1])
        lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                     f'stroke="{estilo.contorno}" stroke-width="{w_arista:.2f}" stroke-dasharray="2,2" id="arista-comun-{i}"/>')
    lines.append('  </g>')

    # Capa: contorno exterior completo
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    w_contorno = 0.7 * estilo.factor_trazo
    lines.append(f'    <path d="{d_contorno}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_contorno:.2f}" id="path-contorno-abanico"/>')
    lines.append('  </g>')


    # Capa: costura (SOLO en bordes laterales extremos)
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="costura" id="layer-costura">')
    w_cost = 0.4 * estilo.factor_trazo
    # Desplazamiento angular correspondiente al semiancho de costura
    d_psi_costura = (costura_cm / 2.0) / s1 if s1 > 0 else 0.0
    ang_cost_izq = ang_min + d_psi_costura
    ang_cost_der = ang_max - d_psi_costura

    p0_c_izq = to_svg(s0 * math.sin(ang_cost_izq), s0 * math.cos(ang_cost_izq))
    p1_c_izq = to_svg(s1 * math.sin(ang_cost_izq), s1 * math.cos(ang_cost_izq))
    p0_c_der = to_svg(s0 * math.sin(ang_cost_der), s0 * math.cos(ang_cost_der))
    p1_c_der = to_svg(s1 * math.sin(ang_cost_der), s1 * math.cos(ang_cost_der))

    lines.append(f'    <line x1="{p0_c_izq[0]:.2f}" y1="{p0_c_izq[1]:.2f}" x2="{p1_c_izq[0]:.2f}" y2="{p1_c_izq[1]:.2f}" '
                 f'stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="3,3" id="costura-lateral-izq"/>')
    lines.append(f'    <line x1="{p0_c_der[0]:.2f}" y1="{p0_c_der[1]:.2f}" x2="{p1_c_der[0]:.2f}" y2="{p1_c_der[1]:.2f}" '
                 f'stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="3,3" id="costura-lateral-der"/>')
    lines.append('  </g>')

    # Capa: pestaña (si aplica al cono inferior)
    if pestana_cm > 0 and s0 > 0:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="pestana" id="layer-pestana">')
        w_pest = 0.3 * estilo.factor_trazo
        r_pest = max(0.0, s0 - pestana_cm)
        pts_pest_svg = []
        for st in range(pasos_arco + 1):
            ang = ang_min + (ang_max - ang_min) * (st / pasos_arco)
            pts_pest_svg.append(to_svg(r_pest * math.sin(ang), r_pest * math.cos(ang)))
        for st in range(pasos_arco + 1):
            ang = ang_max - (ang_max - ang_min) * (st / pasos_arco)
            pts_pest_svg.append(to_svg(s0 * math.sin(ang), s0 * math.cos(ang)))
        d_pest = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_pest_svg) + " Z"
        lines.append(f'    <path d="{d_pest}" fill="none" stroke="{estilo.pestana}" stroke-width="{w_pest:.2f}" stroke-dasharray="2,2" id="path-pestana-boca"/>')
        lines.append('  </g>')

    # Capa: rotulos
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="rotulos" id="layer-rotulos">')
    fs_tit = max(3.8 * estilo.factor_texto, w_page * 0.024)
    fs_sub = max(2.4 * estilo.factor_texto, w_page * 0.015)

    nombres_sec = {
        "superior": "Cono superior",
        "pico": "Pico piramidal",
        "inferior": "Cono inferior"
    }
    nombre_sec_str = nombres_sec.get(seccion, seccion.capitalize())
    modo_str = "Abanico completo" if dibujar == "completo" else "Medio abanico (espejo)"

    # Rótulo superior en el margen
    y_text = margen_mm + 5.0
    lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_tit:.2f}" font-weight="bold" fill="{estilo.texto}" font-family="sans-serif">{nombre_sec_str} — {modo_str}</text>')
    y_text += fs_tit * 1.2
    ang_tot_deg = math.degrees(n * psi)
    info_line1 = f"Escala 1:{factor_s:.1f} · {hoja.upper()} ({w_page:.0f}×{h_page:.0f} mm) · {n} gajos/caras · Ángulo total: {ang_tot_deg:.1f}°"
    lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" font-family="sans-serif">{info_line1}</text>')
    y_text += fs_sub * 1.2
    info_line2 = f"Radio base s₁: {s1:.1f} cm · Radio boca s₀: {s0:.1f} cm · Largo pieza: {pieza.largo:.1f} cm"
    lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" font-family="sans-serif">{info_line2}</text>')

    # Números de gajo
    for i in range(n):
        theta_i = ang_min + (i + 0.5) * psi
        r_lbl = s1 * 0.95
        px_gajo, py_gajo = to_svg(r_lbl * math.sin(theta_i), r_lbl * math.cos(theta_i))
        fs_gajo = max(2.6 * estilo.factor_texto, w_page * 0.016)
        lbl_gajo = f"Gajo {i+1}" if seccion != "pico" else f"Cara {i+1}"
        lines.append(f'    <text x="{px_gajo:.2f}" y="{py_gajo:.2f}" font-size="{fs_gajo:.2f}" font-weight="bold" fill="{estilo.texto}" '
                     f'text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">{lbl_gajo}</text>')

    lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)


def _renderizar_capa_en_abanico(
    capa: CapaDiseno,
    to_svg,
    factor: float,
    carpeta_recursos: Optional[Path],
    opacidad_mult: float = 1.0,
) -> str:
    """Renderiza un elemento SVG <image> o <rect> para una capa en el abanico."""
    if not capa.visible:
        return ""

    cx_cm = capa.x + capa.ancho / 2.0
    cy_cm = capa.y + capa.alto / 2.0

    cx_svg, cy_svg = to_svg(cx_cm, cy_cm)
    w_svg = capa.ancho * factor
    h_svg = capa.alto * factor
    x_svg = cx_svg - w_svg / 2.0
    y_svg = cy_svg - h_svg / 2.0

    transforms = []
    if abs(capa.rotacion) > 1e-4:
        transforms.append(f"rotate({-capa.rotacion:.2f} {cx_svg:.2f} {cy_svg:.2f})")
    if capa.reflejo_h:
        transforms.append(f"translate({cx_svg:.2f} {cy_svg:.2f}) scale(-1 1) translate({-cx_svg:.2f} {-cy_svg:.2f})")
    if capa.reflejo_v:
        transforms.append(f"translate({cx_svg:.2f} {cy_svg:.2f}) scale(1 -1) translate({-cx_svg:.2f} {-cy_svg:.2f})")

    trans_str = f' transform="{" ".join(transforms)}"' if transforms else ""
    opac = max(0.0, min(1.0, capa.opacidad * opacidad_mult))

    href = ""
    if carpeta_recursos:
        arch = carpeta_recursos / capa.archivo
        if arch.exists() and arch.is_file():
            b64_str = base64.b64encode(arch.read_bytes()).decode("ascii")
            if capa.tipo == "svg":
                href = f"data:image/svg+xml;base64,{b64_str}"
            else:
                mime = "image/png" if arch.suffix.lower() == ".png" else "image/jpeg"
                href = f"data:{mime};base64,{b64_str}"

    if href:
        return f'<image href="{href}" x="{x_svg:.2f}" y="{y_svg:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" opacity="{opac:.2f}"{trans_str} id="capa-{capa.id}"/>'
    else:
        return (f'<rect x="{x_svg:.2f}" y="{y_svg:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" '
                f'fill="none" stroke="#888888" stroke-width="0.3" stroke-dasharray="2,2"{trans_str} id="capa-{capa.id}"/>')

