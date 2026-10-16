import math
import warnings
from pathlib import Path
from typing import Tuple, Optional, Union, Dict, Any
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.estilos import EstiloSvg, IMPRESION
from logic.geometria.abanico import pieza_a_geometria_plana, abanico, contorno_abanico
from logic.diseno.lienzo import Diseno, CapaDiseno, obtener_fragmento_capa
from logic.diseno.transformaciones import construir_grupo


def _calcular_orientacion_y_escala_abanico(
    w_cm: float,
    h_cm: float,
    hoja_w: float,
    hoja_h: float,
    margen_mm: float,
    escala: Union[str, float, int],
) -> Tuple[str, float]:
    """Determina la mejor orientación ('vertical'|'horizontal') y el factor_s."""
    def compute_s(orient: str) -> Optional[float]:
        w_p, h_p = (hoja_w, hoja_h) if orient == "vertical" else (hoja_h, hoja_w)
        av_w = w_p - 2 * margen_mm
        av_h = h_p - 2 * margen_mm
        if av_w <= 0 or av_h <= 0:
            return None
        return max((w_cm * 10.0) / av_w, (h_cm * 10.0) / av_h)

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
    return mejor_orientacion, factor_s


def _calcular_caja_abanico(
    ab: Any,
    n: int,
    psi: float,
    s0: float,
    pestana_cm: float,
    dibujar: str,
    mostrar_reflejo: bool,
) -> Tuple[float, float, float, float]:
    """Calcula el bounding box [min_x, max_x, min_y, max_y] en cm del abanico."""
    if dibujar == "mitad" and not mostrar_reflejo:
        min_x_cm = 0.0
        max_x_cm = ab.caja_max_x
    else:
        min_x_cm = ab.caja_min_x
        max_x_cm = ab.caja_max_x

    min_y_cm = ab.caja_min_y
    max_y_cm = ab.caja_max_y

    if pestana_cm > 0:
        r_pestana = max(0.0, s0 - pestana_cm)
        ang_min_pest = 0.0 if (dibujar == "mitad" and not mostrar_reflejo) else -n * psi / 2.0
        ang_max_pest = n * psi / 2.0
        pts_pest = [
            (r_pestana * math.sin(ang_min_pest), r_pestana * math.cos(ang_min_pest)),
            (r_pestana * math.sin(ang_max_pest), r_pestana * math.cos(ang_max_pest)),
        ]
        min_x_cm = min(min_x_cm, *(p[0] for p in pts_pest))
        max_x_cm = max(max_x_cm, *(p[0] for p in pts_pest))
        min_y_cm = min(min_y_cm, *(p[1] for p in pts_pest))
        max_y_cm = max(max_y_cm, *(p[1] for p in pts_pest))

    return min_x_cm, max_x_cm, min_y_cm, max_y_cm


def calcular_parametros_proyeccion_abanico(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    seccion: str = "superior",
    esquema: Optional[EsquemaDiseno] = None,
    hoja: str = "carta",
    escala: Union[str, float, int] = "auto",
    margen_mm: float = 10.0,
    dibujar: str = "completo",
    mostrar_reflejo: bool = True,
    unir_grupos: bool = False,
) -> Dict[str, Any]:
    """Calcula la geometría plana del abanico y los parámetros afines de proyección a SVG."""
    if hoja not in ["carta", "a4"]:
        raise ValueError(f"Hoja no soportada: {hoja}. Use 'carta' o 'a4'.")

    hoja_w, hoja_h = (215.9, 279.4) if hoja == "carta" else (210.0, 297.0)

    if seccion == "pico":
        n = 4
    else:
        tam_g = esquema.tam_grupo if esquema else 5
        unir = unir_grupos and bool(esquema and esquema.modo == "repeticion" and (entrada.num_gajos // tam_g >= 2))
        n = min(entrada.num_gajos, tam_g * 2) if unir else tam_g

    # 2. Geometría pura (abanico completo centrado)
    pieza = pieza_a_geometria_plana(resultado, entrada, seccion)
    ab = abanico(pieza, n=n, centrado=True)
    psi = pieza.angulo_abertura_rad
    s0 = pieza.distancia_vertice
    s1 = pieza.radio_arco
    costura_cm = entrada.ancho_costura

    pestana_cm = 0.0
    if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
        pestana_cm = entrada.pestana_boca

    min_x_cm, max_x_cm, min_y_cm, max_y_cm = _calcular_caja_abanico(
        ab, n, psi, s0, pestana_cm, dibujar, mostrar_reflejo
    )

    w_cm = max_x_cm - min_x_cm
    h_cm = max_y_cm - min_y_cm

    mejor_orientacion, factor_s = _calcular_orientacion_y_escala_abanico(
        w_cm, h_cm, hoja_w, hoja_h, margen_mm, escala
    )

    w_page, h_page = (hoja_w, hoja_h) if mejor_orientacion == "vertical" else (hoja_h, hoja_w)
    avail_w = w_page - 2 * margen_mm
    avail_h = h_page - 2 * margen_mm
    factor = 10.0 / factor_s

    if dibujar == "mitad" and not mostrar_reflejo:
        cx_page = margen_mm + (avail_w - w_cm * factor) / 2.0
    else:
        cx_page = margen_mm + avail_w / 2.0

    cy_page = margen_mm + avail_h / 2.0
    y_mid_cm = (min_y_cm + max_y_cm) / 2.0

    return {
        "factor": factor,
        "factor_s": factor_s,
        "cx_page": cx_page,
        "cy_page": cy_page,
        "y_mid_cm": y_mid_cm,
        "w_page": w_page,
        "h_page": h_page,
        "avail_w": avail_w,
        "avail_h": avail_h,
        "mejor_orientacion": mejor_orientacion,
        "min_x_cm": min_x_cm,
        "max_x_cm": max_x_cm,
        "min_y_cm": min_y_cm,
        "max_y_cm": max_y_cm,
        "w_cm": w_cm,
        "h_cm": h_cm,
        "pieza": pieza,
        "ab": ab,
        "n": n,
        "s0": s0,
        "s1": s1,
        "psi": psi,
        "costura_cm": costura_cm,
        "pestana_cm": pestana_cm,
    }


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
    mostrar_reflejo: bool = False,
    ver_cuadricula: bool = True,
    ver_rotulos: bool = True,
    ver_costuras: bool = True,
    overlay_capa_activa: Optional[CapaDiseno] = None,
    vista_previa: bool = True,
    modo_fantasma: bool = False,
) -> str:
    """Genera un SVG con la hoja de trazo en abanico para impresión o Inkscape."""
    geom = calcular_parametros_proyeccion_abanico(
        resultado=resultado,
        entrada=entrada,
        seccion=seccion,
        esquema=esquema,
        hoja=hoja,
        escala=escala,
        margen_mm=margen_mm,
        dibujar=dibujar,
        mostrar_reflejo=mostrar_reflejo,
        unir_grupos=unir_grupos,
    )

    factor = geom["factor"]
    factor_s = geom["factor_s"]
    cx_page = geom["cx_page"]
    cy_page = geom["cy_page"]
    y_mid_cm = geom["y_mid_cm"]
    w_page = geom["w_page"]
    h_page = geom["h_page"]
    avail_w = geom["avail_w"]
    avail_h = geom["avail_h"]
    pieza = geom["pieza"]
    ab = geom["ab"]
    n = geom["n"]
    s0 = geom["s0"]
    s1 = geom["s1"]
    psi = geom["psi"]
    costura_cm = geom["costura_cm"]
    pestana_cm = geom["pestana_cm"]

    # Transformación cm -> mm SVG con ÁPICE ABAJO:
    def to_svg(x: float, y: float) -> Tuple[float, float]:
        xs = cx_page + x * factor
        ys = cy_page - (y - y_mid_cm) * factor
        return xs, ys

    # Parámetros angulares
    ang_min = -n * psi / 2.0
    ang_max = n * psi / 2.0
    pasos_arco = max(8, n * 6)

    # 4. Calcular contorno exterior del abanico usando contorno_abanico
    pts_contorno_cm = contorno_abanico(pieza, n, dibujar=dibujar, pasos_arco=pasos_arco)
    pts_contorno_svg = [to_svg(x, y) for x, y in pts_contorno_cm]
    d_contorno = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_contorno_svg) + " Z"

    d_contorno_ref = ""
    if dibujar == "mitad" and mostrar_reflejo:
        pts_contorno_ref_cm = [(-x, y) for x, y in pts_contorno_cm]
        pts_contorno_ref_svg = [to_svg(x, y) for x, y in pts_contorno_ref_cm]
        d_contorno_ref = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_contorno_ref_svg) + " Z"

    # 5. Construir elementos SVG
    lines = [
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{w_page:.2f}mm" height="{h_page:.2f}mm" viewBox="0 0 {w_page:.2f} {h_page:.2f}"',
        f'     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
        f'  <defs>',
        f'    <clipPath id="clip-abanico">',
        f'      <path d="{d_contorno}"/>',
        f'    </clipPath>',
    ]
    if d_contorno_ref:
        lines.append(f'    <clipPath id="clip-abanico-reflejo">')
        lines.append(f'      <path d="{d_contorno_ref}"/>')
        lines.append(f'    </clipPath>')
    lines.append('  </defs>')

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    # Capa: papel
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="papel" id="layer-papel">')
    w_papel_trazo = 0.2 * estilo.factor_trazo
    lines.append(f'    <rect x="{margen_mm:.2f}" y="{margen_mm:.2f}" width="{avail_w:.2f}" height="{avail_h:.2f}" '
                 f'fill="none" stroke="{estilo.cuadricula}" stroke-width="{w_papel_trazo:.2f}" stroke-dasharray="3,3" id="margen-util"/>')
    lines.append('  </g>')

    # Capa: cuadricula (arcos o rectas de cada paso)
    if ver_cuadricula:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="cuadricula" id="layer-cuadricula">')
        w_cuad = 0.2 * estilo.factor_trazo

        for idx_paso, y_paso in enumerate(ab.pasos_radiales):
            r_paso = y_paso
            if r_paso <= 1e-4:
                continue

            if dibujar == "mitad":
                # Arco derecho (zona activa)
                pts_paso_svg = []
                for st in range(pasos_arco + 1):
                    ang = ang_max * (st / pasos_arco)
                    pts_paso_svg.append(to_svg(max(0.0, r_paso * math.sin(ang)), r_paso * math.cos(ang)))
                d_arco = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_paso_svg)
                lines.append(f'    <path d="{d_arco}" fill="none" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="cuad-paso-{idx_paso}"/>')

                # Arco izquierdo (reflejo atenuado)
                if mostrar_reflejo:
                    pts_paso_ref_svg = []
                    for st in range(pasos_arco + 1):
                        ang = -ang_max + ang_max * (st / pasos_arco)
                        pts_paso_ref_svg.append(to_svg(min(0.0, r_paso * math.sin(ang)), r_paso * math.cos(ang)))
                    d_arco_ref = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_paso_ref_svg)
                    lines.append(f'    <path d="{d_arco_ref}" fill="none" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" opacity="0.35" id="cuad-paso-ref-{idx_paso}"/>')
            else:
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

    # Capa: diseno
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="diseno" id="layer-diseno">')
    if diseno and diseno.capas:
        carp_rec = Path(carpeta_recursos) if carpeta_recursos else None
        if dibujar == "mitad":
            # Capas en mitad derecha activa (clipPath al contorno de mitad)
            lines.append('    <g id="diseno-mitad-activa" clip-path="url(#clip-abanico)">')
            for c in diseno.capas:
                elem_svg = _renderizar_capa_en_abanico(
                    c, to_svg, factor, carp_rec, opacidad_mult=1.0, vista_previa=vista_previa, modo_fantasma=modo_fantasma
                )
                if elem_svg:
                    lines.append(f'      {elem_svg}')
            lines.append('    </g>')

            # Reflejo simétrico atenuado en mitad izquierda (recortado a la mitad izquierda; oculto en modo editar/fantasma)
            if mostrar_reflejo and not modo_fantasma and d_contorno_ref:
                todas_capas = construir_grupo(diseno, esquema, modo_lienzo="mitad")
                lines.append('    <g id="diseno-mitad-reflejo" opacity="0.38" clip-path="url(#clip-abanico-reflejo)">')
                for c in todas_capas:
                    if c.id.endswith("_reflejo"):
                        elem_svg = _renderizar_capa_en_abanico(
                            c, to_svg, factor, carp_rec, opacidad_mult=1.0, vista_previa=vista_previa, modo_fantasma=modo_fantasma
                        )
                        if elem_svg:
                            lines.append(f'      {elem_svg}')
                lines.append('    </g>')
        else:
            lines.append('    <g id="diseno-completo" clip-path="url(#clip-abanico)">')
            for c in diseno.capas:
                elem_svg = _renderizar_capa_en_abanico(
                    c, to_svg, factor, carp_rec, opacidad_mult=1.0, vista_previa=vista_previa, modo_fantasma=modo_fantasma
                )
                if elem_svg:
                    lines.append(f'      {elem_svg}')
            lines.append('    </g>')
    lines.append('  </g>')

    # Capa: ejes
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="ejes" id="layer-ejes">')
    w_eje = 0.3 * estilo.factor_trazo
    for i, (p0, p1) in enumerate(ab.ejes):
        p0_svg = to_svg(p0[0], p0[1])
        p1_svg = to_svg(p1[0], p1[1])
        x_prom = (p0[0] + p1[0]) / 2.0
        if dibujar == "mitad":
            if x_prom > 1e-4:
                lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                             f'stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" stroke-dasharray="4,2" id="eje-gajo-{i}"/>')
            elif x_prom < -1e-4 and mostrar_reflejo:
                lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                             f'stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" stroke-dasharray="4,2" opacity="0.35" id="eje-gajo-ref-{i}"/>')
        else:
            lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                         f'stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" stroke-dasharray="4,2" id="eje-gajo-{i}"/>')

    # Si estamos en modo mitad, trazar el EJE DE ESPEJO RECTO DESTACADO
    if dibujar == "mitad":
        y_top_eje = s1 if seccion != "pico" or n % 2 == 0 else s1 * math.cos(psi / 2.0)
        y_bot_eje = (s0 - pestana_cm) if (s0 > 0 and pestana_cm > 0) else s0
        p_esp_0 = to_svg(0.0, y_bot_eje)
        p_esp_1 = to_svg(0.0, y_top_eje)
        w_esp = 0.6 * estilo.factor_trazo
        lines.append(f'    <line x1="{p_esp_0[0]:.2f}" y1="{p_esp_0[1]:.2f}" x2="{p_esp_1[0]:.2f}" y2="{p_esp_1[1]:.2f}" '
                     f'stroke="{estilo.eje}" stroke-width="{w_esp:.2f}" stroke-dasharray="6,3" id="eje-espejo-recto"/>')

        y_mid_eje = (p_esp_0[1] + p_esp_1[1]) / 2.0
        x_txt_eje = p_esp_0[0] - 2.5
        fs_txt_eje = max(2.0 * estilo.factor_texto, w_page * 0.013)
        lines.append(f'    <text x="{x_txt_eje:.2f}" y="{y_mid_eje:.2f}" font-size="{fs_txt_eje:.2f}" fill="{estilo.eje}" '
                     f'font-family="sans-serif" text-anchor="middle" transform="rotate(-90 {x_txt_eje:.2f} {y_mid_eje:.2f})">eje de espejo</text>')
    lines.append('  </g>')

    # Capa: aristas_comunes
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="aristas_comunes" id="layer-aristas-comunes">')
    w_arista = 0.3 * estilo.factor_trazo
    for i, (p0, p1) in enumerate(ab.aristas_comunes):
        p0_svg = to_svg(p0[0], p0[1])
        p1_svg = to_svg(p1[0], p1[1])
        x_prom = (p0[0] + p1[0]) / 2.0
        if dibujar == "mitad":
            if x_prom > 1e-4:
                lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                             f'stroke="{estilo.contorno}" stroke-width="{w_arista:.2f}" stroke-dasharray="2,2" id="arista-comun-{i}"/>')
            elif x_prom < -1e-4 and mostrar_reflejo:
                lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                             f'stroke="{estilo.contorno}" stroke-width="{w_arista:.2f}" stroke-dasharray="2,2" opacity="0.35" id="arista-comun-ref-{i}"/>')
        else:
            lines.append(f'    <line x1="{p0_svg[0]:.2f}" y1="{p0_svg[1]:.2f}" x2="{p1_svg[0]:.2f}" y2="{p1_svg[1]:.2f}" '
                         f'stroke="{estilo.contorno}" stroke-width="{w_arista:.2f}" stroke-dasharray="2,2" id="arista-comun-{i}"/>')
    lines.append('  </g>')

    # Capa: contorno exterior
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    w_contorno = 0.7 * estilo.factor_trazo
    lines.append(f'    <path d="{d_contorno}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_contorno:.2f}" id="path-contorno-abanico"/>')
    if dibujar == "mitad" and mostrar_reflejo and d_contorno_ref:
        lines.append(f'    <path d="{d_contorno_ref}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_contorno:.2f}" opacity="0.35" stroke-dasharray="4,2" id="path-contorno-reflejo"/>')
    lines.append('  </g>')

    # Capa: costura (SOLO en bordes laterales extremos)
    if ver_costuras:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="costura" id="layer-costura">')
        w_cost = 0.4 * estilo.factor_trazo
        d_psi_costura = (costura_cm / 2.0) / s1 if s1 > 0 else 0.0
        ang_cost_der = ang_max - d_psi_costura

        p0_c_der = to_svg(s0 * math.sin(ang_cost_der), s0 * math.cos(ang_cost_der))
        p1_c_der = to_svg(s1 * math.sin(ang_cost_der), s1 * math.cos(ang_cost_der))

        if dibujar == "completo":
            ang_cost_izq = ang_min + d_psi_costura
            p0_c_izq = to_svg(s0 * math.sin(ang_cost_izq), s0 * math.cos(ang_cost_izq))
            p1_c_izq = to_svg(s1 * math.sin(ang_cost_izq), s1 * math.cos(ang_cost_izq))
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
        if dibujar == "mitad":
            # De 0 a ang_max a radio r_pest
            for st in range(pasos_arco + 1):
                ang = ang_max * (st / pasos_arco)
                pts_pest_svg.append(to_svg(max(0.0, r_pest * math.sin(ang)), r_pest * math.cos(ang)))
            # De ang_max a 0 a radio s0
            for st in range(pasos_arco + 1):
                ang = ang_max * (1.0 - st / pasos_arco)
                pts_pest_svg.append(to_svg(max(0.0, s0 * math.sin(ang)), s0 * math.cos(ang)))
            # Cerrada en x=0 con una recta vertical continua con el eje de espejo
            pts_pest_svg.append(to_svg(0.0, r_pest))
        else:
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
    if ver_rotulos:
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
        ang_tot_deg = math.degrees(n * psi) if dibujar == "completo" else math.degrees(n * psi / 2.0)
        info_line1 = f"Escala 1:{factor_s:.1f} · {hoja.upper()} ({w_page:.0f}×{h_page:.0f} mm) · {n} gajos/caras · Ángulo total: {ang_tot_deg:.1f}°"
        lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" font-family="sans-serif">{info_line1}</text>')
        y_text += fs_sub * 1.2
        info_line2 = f"Radio base s₁: {s1:.1f} cm · Radio boca s₀: {s0:.1f} cm · Largo pieza: {pieza.largo:.1f} cm"
        lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" font-family="sans-serif">{info_line2}</text>')

        if dibujar == "mitad":
            y_text += fs_sub * 1.2
            leyenda_esp = "Eje de espejo sobre la costura central" if (n % 2 == 0) else "Eje de espejo corta por el centro del gajo central (se asume simétrico)"
            lines.append(f'    <text x="{margen_mm:.2f}" y="{y_text:.2f}" font-size="{fs_sub:.2f}" font-style="italic" fill="{estilo.texto}" font-family="sans-serif">{leyenda_esp}</text>')

        # Números de gajo
        for i in range(n):
            theta_i = ang_min + (i + 0.5) * psi
            r_lbl = s1 * 0.95
            x_lbl = r_lbl * math.sin(theta_i)
            y_lbl = r_lbl * math.cos(theta_i)
            px_gajo, py_gajo = to_svg(x_lbl, y_lbl)
            fs_gajo = max(2.6 * estilo.factor_texto, w_page * 0.016)
            lbl_gajo = f"Gajo {i+1}" if seccion != "pico" else f"Cara {i+1}"

            if dibujar == "mitad":
                if x_lbl >= -1e-4:
                    lines.append(f'    <text x="{px_gajo:.2f}" y="{py_gajo:.2f}" font-size="{fs_gajo:.2f}" font-weight="bold" fill="{estilo.texto}" '
                                 f'text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">{lbl_gajo}</text>')
                elif mostrar_reflejo:
                    lines.append(f'    <text x="{px_gajo:.2f}" y="{py_gajo:.2f}" font-size="{fs_gajo:.2f}" font-weight="bold" fill="{estilo.texto}" opacity="0.35" '
                                 f'text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">{lbl_gajo}\'</text>')
            else:
                lines.append(f'    <text x="{px_gajo:.2f}" y="{py_gajo:.2f}" font-size="{fs_gajo:.2f}" font-weight="bold" fill="{estilo.texto}" '
                             f'text-anchor="middle" dominant-baseline="middle" font-family="sans-serif">{lbl_gajo}</text>')

        lines.append('  </g>')

    # Capa: overlay de selección interactiva (tiradores y centro)
    if overlay_capa_activa:
        c = overlay_capa_activa
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="overlay_seleccion" id="layer-overlay-seleccion">')
        cx_cm = c.x + c.ancho / 2.0
        cy_cm = c.y + c.alto / 2.0
        cx_s, cy_s = to_svg(cx_cm, cy_cm)
        w_s = c.ancho * factor
        h_s = c.alto * factor
        x_s = cx_s - w_s / 2.0
        y_s = cy_s - h_s / 2.0

        rot_trans = f' transform="rotate({-c.rotacion:.2f} {cx_s:.2f} {cy_s:.2f})"' if abs(c.rotacion) > 1e-4 else ""
        lines.append(f'    <g{rot_trans} id="overlay-capa-{c.id}">')
        lines.append(f'      <rect x="{x_s:.2f}" y="{y_s:.2f}" width="{w_s:.2f}" height="{h_s:.2f}" '
                     f'fill="none" stroke="#2196F3" stroke-width="0.5" stroke-dasharray="3,2" id="overlay-box"/>')
        sz_h = 2.5
        h_sz = sz_h / 2.0
        for h_id, (hx, hy) in [
            ("tl", (x_s, y_s)),
            ("tr", (x_s + w_s, y_s)),
            ("br", (x_s + w_s, y_s + h_s)),
            ("bl", (x_s, y_s + h_s)),
        ]:
            lines.append(f'      <rect x="{hx - h_sz:.2f}" y="{hy - h_sz:.2f}" width="{sz_h:.2f}" height="{sz_h:.2f}" '
                         f'fill="#FFFFFF" stroke="#2196F3" stroke-width="0.6" id="tirador-{h_id}"/>')
        lines.append(f'      <circle cx="{cx_s:.2f}" cy="{cy_s:.2f}" r="2.0" fill="#2196F3" fill-opacity="0.8" stroke="#FFFFFF" stroke-width="0.5" id="tirador-centro"/>')
        lines.append('    </g>')
        lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)


def _renderizar_capa_en_abanico(
    capa: CapaDiseno,
    to_svg,
    factor: float,
    carpeta_recursos: Optional[Path],
    opacidad_mult: float = 1.0,
    vista_previa: bool = True,
    modo_fantasma: bool = False,
) -> str:
    """Renderiza un elemento SVG nativo o imagen raster para una capa en el abanico."""
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

    if modo_fantasma:
        return (
            f'<rect x="{x_svg:.2f}" y="{y_svg:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" '
            f'fill="none" stroke="#2196F3" stroke-width="0.5" stroke-dasharray="3,2" '
            f'opacity="{opac * 0.4:.2f}"{trans_str} id="capa-fantasma-{capa.id}"/>'
        )

    contenido_frag, vb = obtener_fragmento_capa(capa, carpeta_recursos, vista_previa=vista_previa)

    if capa.tipo == "svg" and contenido_frag:
        vx, vy, vw, vh = vb
        if vw > 0 and vh > 0:
            s = min(w_svg / vw, h_svg / vh)
            dx = (w_svg - vw * s) / 2.0 - vx * s
            dy = (h_svg - vh * s) / 2.0 - vy * s
            t_local = f"translate({x_svg:.2f} {y_svg:.2f}) translate({dx:.2f} {dy:.2f}) scale({s:.4f})"
            return (
                f'<g id="capa-{capa.id}" opacity="{opac:.2f}"{trans_str}>\n'
                f'  <g transform="{t_local}">\n'
                f'{contenido_frag}\n'
                f'  </g>\n'
                f'</g>'
            )
    elif capa.tipo != "svg" and contenido_frag:
        return f'<image href="{contenido_frag}" x="{x_svg:.2f}" y="{y_svg:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" opacity="{opac:.2f}"{trans_str} id="capa-{capa.id}"/>'

    return (f'<rect x="{x_svg:.2f}" y="{y_svg:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" '
            f'fill="none" stroke="#888888" stroke-width="0.3" stroke-dasharray="2,2"{trans_str} id="capa-{capa.id}"/>')

