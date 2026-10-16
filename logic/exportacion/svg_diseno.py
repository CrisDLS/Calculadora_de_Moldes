import math
from pathlib import Path
from typing import List, Tuple, Optional, Union
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, obtener_fragmento_capa
from logic.diseno.transformaciones import (
    transformacion_a_gajo,
    gajos_equivalentes,
    construir_grupo,
)
from logic.exportacion.estilos import EstiloSvg, IMPRESION
from logic.exportacion.comun import guardar_svg, formatear_path_simetrico
from logic.geometria.abanico import pieza_a_geometria_plana, abanico
from logic.exportacion.svg_abanico import svg_abanico

def svg_gajo(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    seccion: str,
    esquema: Optional[EsquemaDiseno],
    diseno: Optional[Diseno],
    indice: int,
    carpeta_recursos: Optional[Union[str, Path]] = None,
    estilo: EstiloSvg = IMPRESION,
    escala: Union[str, float, int] = 1,
    hoja: str = "carta",
    dibujar: str = "completo",
    vista_previa: bool = False,
) -> str:
    """Genera el SVG de un gajo individual decorado con su recorte de diseño."""
    if seccion == "superior":
        sec_res = resultado.seccion_superior
    elif seccion == "inferior":
        sec_res = resultado.seccion_inferior
    elif seccion == "pico":
        sec_res = resultado.seccion_picos
    else:
        raise ValueError(f"Sección desconocida: {seccion}")

    factor_escala = float(escala) if str(escala).lower() != "auto" else 1.0
    factor = 10.0 / factor_escala  # mm por cm real
    costura = entrada.ancho_costura

    # Motivo y condición de espejo para este gajo
    num_total_gajos = entrada.num_gajos if seccion != "pico" else 4
    equiv = gajos_equivalentes(esquema, num_total_gajos) if esquema else [(i, False, i) for i in range(num_total_gajos)]
    motivo, es_reflejo, idx_en_grupo = equiv[indice % len(equiv)]

    # Geometría de la pieza suelta canónica
    L_real = sec_res.generatriz_total
    max_ancho_medio = max(p.ancho_medio for p in sec_res.puntos)
    ancho_max = max_ancho_medio * 2.0

    margin_x = 15.0
    margin_y = 15.0
    cx = margin_x + (ancho_max / 2.0) * factor
    svg_w = ancho_max * factor + 2 * margin_x
    svg_h = L_real * factor + 2 * margin_y

    def get_y(l_acumulado: float) -> float:
        if seccion == "inferior":
            return margin_y + (L_real - l_acumulado) * factor
        return margin_y + l_acumulado * factor

    pts_left_cut: List[Tuple[float, float]] = []
    pts_right_cut: List[Tuple[float, float]] = []
    pts_center_cut: List[Tuple[float, float]] = []
    pts_left_seam: List[Tuple[float, float]] = []
    pts_right_seam: List[Tuple[float, float]] = []

    for p in sec_res.puntos:
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        w_seam = max(0.0, p.ancho_medio - costura / 2.0) * factor
        pts_left_cut.append((cx - w_cut, y))
        pts_right_cut.append((cx + w_cut, y))
        pts_center_cut.append((cx, y))
        pts_left_seam.append((cx - w_seam, y))
        pts_right_seam.append((cx + w_seam, y))

    path_cut = formatear_path_simetrico(pts_right_cut, pts_left_cut)
    path_seam = formatear_path_simetrico(pts_right_seam, pts_left_seam)

    tam_g = esquema.tam_grupo if esquema else 5
    k_grupo = idx_en_grupo % tam_g
    es_central_impar = (dibujar == "mitad") and (tam_g % 2 == 1) and (k_grupo == tam_g // 2)

    # SVG XML
    lines = [
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{svg_w:.2f}mm" height="{svg_h:.2f}mm" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}"',
        f'     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
        f'  <defs>',
        f'    <clipPath id="clip-gajo-{indice}">',
        f'      <path d="{path_cut}"/>',
        f'    </clipPath>',
    ]
    if es_central_impar:
        path_cut_der = formatear_path_simetrico(pts_right_cut, pts_center_cut)
        path_cut_izq = formatear_path_simetrico(pts_center_cut, pts_left_cut)
        lines.extend([
            f'    <clipPath id="clip-gajo-{indice}-der">',
            f'      <path d="{path_cut_der}"/>',
            f'    </clipPath>',
            f'    <clipPath id="clip-gajo-{indice}-izq">',
            f'      <path d="{path_cut_izq}"/>',
            f'    </clipPath>',
        ])
    lines.append('  </defs>')

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    # Capa: cuadricula
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="cuadricula" id="layer-cuadricula">')
    w_eje = 0.2 * estilo.factor_trazo
    w_cuad = 0.2 * estilo.factor_trazo
    y_min = margin_y
    y_max = margin_y + L_real * factor
    lines.append(f'    <line x1="{cx:.2f}" y1="{y_min:.2f}" x2="{cx:.2f}" y2="{y_max:.2f}" stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" id="grid-center"/>')
    for idx_p, p in enumerate(sec_res.puntos):
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        lines.append(f'    <line x1="{cx - w_cut:.2f}" y1="{y:.2f}" x2="{cx + w_cut:.2f}" y2="{y:.2f}" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="grid-step-{idx_p}"/>')
    lines.append('  </g>')

    # Capa: diseno (recortada por el contorno de la pieza suelta)
    lines.append(f'  <g inkscape:groupmode="layer" inkscape:label="diseno" id="layer-diseno" clip-path="url(#clip-gajo-{indice})">')
    if diseno and diseno.capas:
        carp_rec = Path(carpeta_recursos) if carpeta_recursos else None
        pieza_plana = pieza_a_geometria_plana(resultado, entrada, seccion)
        ab = abanico(pieza_plana, n=tam_g, centrado=True)
        t_gajo = transformacion_a_gajo(ab, k_grupo)
        psi = pieza_plana.angulo_abertura_rad
        theta_i = (k_grupo - (ab.n - 1) / 2.0) * psi
        theta_deg = math.degrees(theta_i)
        aplicar_espejo_esquema = es_reflejo and (dibujar != "mitad")

        def _render_capa_gajo(capa_item, indent: str = "    ") -> Optional[str]:
            if not capa_item.visible:
                return None
            cx_capa_cm = capa_item.x + capa_item.ancho / 2.0
            cy_capa_cm = capa_item.y + capa_item.alto / 2.0
            cx_canon_cm, cy_canon_cm = t_gajo.transformar_punto((cx_capa_cm, cy_capa_cm))
            if aplicar_espejo_esquema:
                cx_canon_cm = -cx_canon_cm

            x_svg_center = cx + cx_canon_cm * factor
            if seccion == "inferior":
                y_svg_center = margin_y + (L_real - cy_canon_cm) * factor
            else:
                y_svg_center = margin_y + cy_canon_cm * factor

            w_svg = capa_item.ancho * factor
            h_svg = capa_item.alto * factor
            x_svg_top_left = x_svg_center - w_svg / 2.0
            y_svg_top_left = y_svg_center - h_svg / 2.0

            rot_final = capa_item.rotacion - theta_deg
            if aplicar_espejo_esquema:
                rot_final = -rot_final
            ref_h = (not capa_item.reflejo_h) if aplicar_espejo_esquema else capa_item.reflejo_h

            transforms = []
            if abs(rot_final) > 1e-4:
                transforms.append(f"rotate({rot_final:.2f} {x_svg_center:.2f} {y_svg_center:.2f})")
            if ref_h:
                transforms.append(f"translate({x_svg_center:.2f} {y_svg_center:.2f}) scale(-1 1) translate({-x_svg_center:.2f} {-y_svg_center:.2f})")
            if capa_item.reflejo_v:
                transforms.append(f"translate({x_svg_center:.2f} {y_svg_center:.2f}) scale(1 -1) translate({-x_svg_center:.2f} {-y_svg_center:.2f})")

            trans_str = f' transform="{" ".join(transforms)}"' if transforms else ""
            contenido_frag, vb = obtener_fragmento_capa(capa_item, carp_rec, vista_previa=vista_previa)

            if capa_item.tipo == "svg" and contenido_frag:
                vx, vy, vw, vh = vb
                if vw > 0 and vh > 0:
                    s = min(w_svg / vw, h_svg / vh)
                    dx = (w_svg - vw * s) / 2.0 - vx * s
                    dy = (h_svg - vh * s) / 2.0 - vy * s
                    t_local = f"translate({x_svg_top_left:.2f} {y_svg_top_left:.2f}) translate({dx:.2f} {dy:.2f}) scale({s:.4f})"
                    return (
                        f'{indent}<g id="gajo-capa-{capa_item.id}" opacity="{capa_item.opacidad:.2f}"{trans_str}>\n'
                        f'{indent}  <g transform="{t_local}">\n'
                        f'{contenido_frag}\n'
                        f'{indent}  </g>\n'
                        f'{indent}</g>'
                    )
            elif capa_item.tipo != "svg" and contenido_frag:
                return f'{indent}<image href="{contenido_frag}" x="{x_svg_top_left:.2f}" y="{y_svg_top_left:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" opacity="{capa_item.opacidad:.2f}"{trans_str} id="gajo-capa-{capa_item.id}"/>'
            return f'{indent}<rect x="{x_svg_top_left:.2f}" y="{y_svg_top_left:.2f}" width="{w_svg:.2f}" height="{h_svg:.2f}" fill="none" stroke="#888888" stroke-width="0.3"{trans_str} id="gajo-capa-{capa_item.id}"/>'

        if dibujar == "mitad":
            todas = construir_grupo(diseno, esquema, modo_lienzo="mitad")
            capas_orig = [c for c in todas if not c.id.endswith("_reflejo")]
            capas_refl = [c for c in todas if c.id.endswith("_reflejo")]

            if es_central_impar:
                lines.append(f'    <g id="diseno-gajo-central-der" clip-path="url(#clip-gajo-{indice}-der)">')
                for c in capas_orig:
                    el = _render_capa_gajo(c, indent="      ")
                    if el:
                        lines.append(el)
                lines.append('    </g>')
                lines.append(f'    <g id="diseno-gajo-central-izq" clip-path="url(#clip-gajo-{indice}-izq)">')
                for c in capas_refl:
                    el = _render_capa_gajo(c, indent="      ")
                    if el:
                        lines.append(el)
                lines.append('    </g>')
            elif k_grupo < (tam_g - 1) / 2.0:
                for c in capas_refl:
                    el = _render_capa_gajo(c, indent="    ")
                    if el:
                        lines.append(el)
            else:
                for c in capas_orig:
                    el = _render_capa_gajo(c, indent="    ")
                    if el:
                        lines.append(el)
        else:
            for c in diseno.capas:
                el = _render_capa_gajo(c, indent="    ")
                if el:
                    lines.append(el)

    lines.append('  </g>')

    # Capa: costura
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="costura" id="layer-costura">')
    w_cost = 0.5 * estilo.factor_trazo
    lines.append(f'    <path d="{path_seam}" fill="none" stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="2,2" id="path-seam"/>')
    lines.append('  </g>')

    # Capa: contorno
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    w_cont = 1.0 * estilo.factor_trazo
    lines.append(f'    <path d="{path_cut}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_cont:.2f}" id="path-cut"/>')
    lines.append('  </g>')

    # Capa: etiquetas
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="etiquetas" id="layer-etiquetas">')
    fs_tit = max(3.5 * estilo.factor_texto, svg_w * 0.030)

    nombre_sec = seccion.capitalize()
    espejo_str = " (Espejo)" if es_reflejo else ""
    rotulo_principal = f"{nombre_sec} · Gajo {indice + 1} · Motivo {motivo + 1}{espejo_str}"
    lines.append(f'    <text x="{cx:.2f}" y="{margin_y / 2.0:.2f}" font-size="{fs_tit:.2f}" font-weight="bold" fill="{estilo.texto}" text-anchor="middle" font-family="sans-serif">{rotulo_principal}</text>')
    lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)


def exportar_diseno(
    carpeta: Union[str, Path],
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    esquema: Optional[EsquemaDiseno],
    diseno: Optional[Diseno],
    carpeta_recursos: Optional[Union[str, Path]] = None,
    seccion: str = "superior",
    formato_hoja: str = "carta",
    dibujar: str = "completo",
) -> List[Path]:
    """Genera en la carpeta destino los SVGs de los gajos decorados y la hoja de trazo."""
    out_dir = Path(carpeta)
    out_dir.mkdir(parents=True, exist_ok=True)

    archivos_creados: List[Path] = []

    # 1. Hoja de trazo del abanico decorado
    ruta_abanico = out_dir / f"hoja_abanico_{seccion}.svg"
    svg_ab = svg_abanico(
        resultado=resultado,
        entrada=entrada,
        seccion=seccion,
        esquema=esquema,
        diseno=diseno,
        hoja=formato_hoja,
        carpeta_recursos=carpeta_recursos,
        dibujar=dibujar,
        vista_previa=False,
    )
    guardar_svg(str(ruta_abanico), svg_ab)
    archivos_creados.append(ruta_abanico)

    # 2. SVGs de cada gajo decorado
    num_gajos_export = entrada.num_gajos if seccion != "pico" else 4
    # Si hay esquema, exportar los gajos del grupo (o todos)
    tam_g = esquema.tam_grupo if esquema else num_gajos_export
    gajos_a_exportar = min(num_gajos_export, tam_g)

    for i in range(gajos_a_exportar):
        ruta_gajo = out_dir / f"gajo_{i+1:02d}.svg"
        svg_g = svg_gajo(
            resultado=resultado,
            entrada=entrada,
            seccion=seccion,
            esquema=esquema,
            diseno=diseno,
            indice=i,
            carpeta_recursos=carpeta_recursos,
            hoja=formato_hoja,
            dibujar=dibujar,
            vista_previa=False,
        )
        guardar_svg(str(ruta_gajo), svg_g)
        archivos_creados.append(ruta_gajo)

    return archivos_creados
