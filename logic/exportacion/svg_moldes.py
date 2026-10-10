from typing import List, Optional
from logic.models import BalloonInput, BalloonCalculationResult, SectionResult, Point2D

def svg_pieza(resultado: BalloonCalculationResult, entrada: BalloonInput, seccion: str, escala: float = 10.0) -> str:
    if seccion == "superior":
        sec_res = resultado.seccion_superior
    elif seccion == "inferior":
        sec_res = resultado.seccion_inferior
    elif seccion == "pico":
        sec_res = resultado.seccion_picos
    else:
        raise ValueError(f"Sección desconocida: {seccion}")

    factor = 10.0 / escala
    costura = entrada.ancho_costura
    
    # Altura real
    L_real = sec_res.generatriz_total
    
    # Ancho máximo de la pieza
    # El ancho máximo será el ancho máximo registrado en los puntos (incluye costura) por 2
    max_ancho_medio = max(p.ancho_medio for p in sec_res.puntos)
    W_real = max_ancho_medio * 2

    # SVG dimensions in mm
    svg_h = L_real * factor
    svg_w = W_real * factor
    
    # Para el cono inferior, añadimos espacio extra en el SVG para la pestaña en la parte inferior
    pestana_svg = 0.0
    if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
        pestana_svg = entrada.pestana_boca * factor
        svg_h += pestana_svg

    # Center x
    cx = svg_w / 2

    def get_y(l_acumulado: float) -> float:
        # Queremos punta estrecha ABAJO. 
        # En inferior: largo_acumulado = 0 es la boca (estrecha). -> Y = L_real
        if seccion == "inferior":
            y = (L_real - l_acumulado) * factor
        # En superior y pico: largo_acumulado = 0 es la banda (ancha), l = L_real es apex (estrecha) -> Y = l_acumulado
        else:
            y = l_acumulado * factor
        return y

    # Construir path coords
    pts_left_cut = []
    pts_right_cut = []
    pts_left_seam = []
    pts_right_seam = []

    for p in sec_res.puntos:
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        w_seam = (p.ancho_medio - costura/2) * factor
        
        pts_left_cut.append((cx - w_cut, y))
        pts_right_cut.append((cx + w_cut, y))
        pts_left_seam.append((cx - w_seam, y))
        pts_right_seam.append((cx + w_seam, y))

    # Path data: right side down, left side up
    # Since pts_right_cut goes from first point to last
    path_cut = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_cut)
    path_cut += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_cut))
    path_cut += " Z"

    path_seam = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_seam)
    path_seam += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_seam))
    path_seam += " Z"

    # SVG XML
    lines = [
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{svg_w:.2f}mm" height="{svg_h:.2f}mm" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}"',
        f'     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
    ]

    # Cuadricula
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="cuadricula" id="layer-cuadricula">')
    # linea vertical central
    lines.append(f'    <line x1="{cx:.2f}" y1="0" x2="{cx:.2f}" y2="{L_real*factor:.2f}" stroke="blue" stroke-width="0.2" id="grid-center"/>')
    for i, p in enumerate(sec_res.puntos):
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        lines.append(f'    <line x1="{cx - w_cut:.2f}" y1="{y:.2f}" x2="{cx + w_cut:.2f}" y2="{y:.2f}" stroke="blue" stroke-width="0.2" id="grid-step-{i}"/>')
    lines.append('  </g>')

    # Costura
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="costura" id="layer-costura">')
    lines.append(f'    <path d="{path_seam}" fill="none" stroke="red" stroke-width="0.5" stroke-dasharray="2,2" id="path-seam"/>')
    lines.append('  </g>')

    # Contorno
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    lines.append(f'    <path d="{path_cut}" fill="none" stroke="black" stroke-width="1.0" id="path-cut"/>')
    lines.append('  </g>')

    # Etiquetas
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="etiquetas" id="layer-etiquetas">')
    for i, p in enumerate(sec_res.puntos):
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        lines.append(f'    <text x="{cx - w_cut + 1:.2f}" y="{y - 1:.2f}" font-size="2" fill="blue" id="label-step-{i+1}">{i+1}</text>')
    
    # Etiqueta general cerca de la punta
    if seccion == "inferior":
        text_y = get_y(0.0) - 10 # 1 cm arriba de la boca
    else:
        text_y = get_y(L_real) - 10 # 1 cm arriba del pico
    lines.append(f'    <text x="{cx:.2f}" y="{text_y:.2f}" font-size="4" fill="black" text-anchor="middle" id="label-info">{seccion.capitalize()} | {sec_res.cantidad} piezas | Escala 1:{escala} | Largo {L_real:.2f} cm</text>')
    lines.append('  </g>')

    # Pestaña (solo inferior avanzado)
    if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="pestana" id="layer-pestana">')
        pestana_cm = entrada.pestana_boca
        p_pestana = pestana_cm * factor
        y_boca = get_y(0.0)
        y_end = y_boca + p_pestana
        w_boca = sec_res.puntos[0].ancho_medio * factor
        x1 = cx - w_boca
        x2 = cx + w_boca
        lines.append(f'    <rect x="{x1:.2f}" y="{y_boca:.2f}" width="{w_boca*2:.2f}" height="{p_pestana:.2f}" fill="none" stroke="green" stroke-width="0.5" stroke-dasharray="2,2" id="rect-pestana"/>')
        lines.append('  </g>')

    # Diseño
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="diseno" id="layer-diseno">')
    lines.append('  </g>')

    lines.append('</svg>')
    
    return "\n".join(lines)

def guardar_svg(ruta: str, svg: str) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(svg)
