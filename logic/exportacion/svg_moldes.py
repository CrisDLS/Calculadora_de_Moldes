from typing import List, Optional
from logic.models import BalloonInput, BalloonCalculationResult, SectionResult, Point2D
from logic.exportacion.estilos import EstiloSvg, IMPRESION

def svg_pieza(resultado: BalloonCalculationResult, entrada: BalloonInput, seccion: str, escala: float = 10.0, estilo: EstiloSvg = IMPRESION) -> str:
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
        if seccion == "inferior":
            y = (L_real - l_acumulado) * factor
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

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    # Cuadricula
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="cuadricula" id="layer-cuadricula">')
    # linea vertical central
    w_eje = 0.2 * estilo.factor_trazo
    w_cuad = 0.2 * estilo.factor_trazo
    lines.append(f'    <line x1="{cx:.2f}" y1="0" x2="{cx:.2f}" y2="{L_real*factor:.2f}" stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" id="grid-center"/>')
    for i, p in enumerate(sec_res.puntos):
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        lines.append(f'    <line x1="{cx - w_cut:.2f}" y1="{y:.2f}" x2="{cx + w_cut:.2f}" y2="{y:.2f}" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="grid-step-{i}"/>')
    lines.append('  </g>')

    # Costura
    w_cost = 0.5 * estilo.factor_trazo
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="costura" id="layer-costura">')
    lines.append(f'    <path d="{path_seam}" fill="none" stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="2,2" id="path-seam"/>')
    lines.append('  </g>')

    # Contorno
    w_cont = 1.0 * estilo.factor_trazo
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    lines.append(f'    <path d="{path_cut}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_cont:.2f}" id="path-cut"/>')
    lines.append('  </g>')

    # Etiquetas
    fs_paso = 2 * estilo.factor_texto
    fs_info = 4 * estilo.factor_texto
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="etiquetas" id="layer-etiquetas">')
    for i, p in enumerate(sec_res.puntos):
        y = get_y(p.largo_acumulado)
        w_cut = p.ancho_medio * factor
        lines.append(f'    <text x="{cx - w_cut + 1:.2f}" y="{y - 1:.2f}" font-size="{fs_paso:.2f}" fill="{estilo.cuadricula}" id="label-step-{i+1}">{i+1}</text>')
    
    # Etiqueta general cerca de la punta
    if seccion == "inferior":
        text_y = get_y(0.0) - 10 # 1 cm arriba de la boca
    else:
        text_y = get_y(L_real) - 10 # 1 cm arriba del pico
    lines.append(f'    <text x="{cx:.2f}" y="{text_y:.2f}" font-size="{fs_info:.2f}" fill="{estilo.texto}" text-anchor="middle" id="label-info">{seccion.capitalize()} | {sec_res.cantidad} piezas | Escala 1:{escala} | Largo {L_real:.2f} cm</text>')
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
        w_pest = 0.5 * estilo.factor_trazo
        lines.append(f'    <rect x="{x1:.2f}" y="{y_boca:.2f}" width="{w_boca*2:.2f}" height="{p_pestana:.2f}" fill="none" stroke="{estilo.pestana}" stroke-width="{w_pest:.2f}" stroke-dasharray="2,2" id="rect-pestana"/>')
        lines.append('  </g>')

    # Diseño
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="diseno" id="layer-diseno">')
    lines.append('  </g>')

    lines.append('</svg>')
    
    return "\n".join(lines)

def guardar_svg(ruta: str, svg: str) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(svg)


def svg_hoja(resultado: BalloonCalculationResult, entrada: BalloonInput, seccion: str,
             esquema, escala="auto", hoja="carta", margen_mm=10.0, estilo: EstiloSvg = IMPRESION) -> str:
    import warnings
    
    if seccion == "superior":
        sec_res = resultado.seccion_superior
    elif seccion == "inferior":
        sec_res = resultado.seccion_inferior
    elif seccion == "pico":
        sec_res = resultado.seccion_picos
    else:
        raise ValueError(f"Sección desconocida: {seccion}")

    L_real = sec_res.generatriz_total
    max_ancho_medio = max(p.ancho_medio for p in sec_res.puntos)
    W_real = max_ancho_medio * 2
    
    H_real = L_real
    pestana_cm = 0.0
    if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
        pestana_cm = entrada.pestana_boca
        H_real += pestana_cm

    if hoja not in ["carta", "a4"]:
        raise ValueError("Hoja debe ser 'carta' o 'a4'")
    
    hoja_w, hoja_h = (215.9, 279.4) if hoja == "carta" else (210.0, 297.0)
    gap_mm = 5.0
    
    motivos = list(range(esquema.motivos_a_dibujar))
    n_copias = len(motivos)
    
    def compute_scale(escala_val, orientacion, cols):
        w_page, h_page = (hoja_w, hoja_h) if orientacion == "vertical" else (hoja_h, hoja_w)
        rows = (n_copias + cols - 1) // cols
        
        avail_w = w_page - 2 * margen_mm - (cols - 1) * gap_mm
        avail_h = h_page - 2 * margen_mm - (rows - 1) * gap_mm
        
        if avail_w <= 0 or avail_h <= 0:
            return None
            
        req_S_x = (cols * W_real * 10) / avail_w
        req_S_y = (rows * H_real * 10) / avail_h
        min_S = max(req_S_x, req_S_y)
        
        if escala_val != "auto" and escala_val < min_S:
            return None
            
        return min_S

    best_layout = None
    
    if escala == "auto":
        best_S = float('inf')
        for orientacion in ["vertical", "horizontal"]:
            for cols in range(1, n_copias + 1):
                S = compute_scale("auto", orientacion, cols)
                if S and S < best_S:
                    best_S = S
                    best_layout = (orientacion, cols, S)
    else:
        S = float(escala)
        for cols in range(1, n_copias + 1):
            if compute_scale(S, "vertical", cols):
                best_layout = ("vertical", cols, S)
                break
        if not best_layout:
            for cols in range(1, n_copias + 1):
                if compute_scale(S, "horizontal", cols):
                    best_layout = ("horizontal", cols, S)
                    warnings.warn("No cabía en vertical, se cambió a horizontal automáticamente.")
                    break
                    
    if not best_layout:
        raise ValueError(f"No caben a escala 1:{escala} con los márgenes especificados.")
        
    orientacion, cols, factor_S = best_layout
    factor = 10.0 / factor_S
    rows = (n_copias + cols - 1) // cols
    
    w_page, h_page = (hoja_w, hoja_h) if orientacion == "vertical" else (hoja_h, hoja_w)
    
    lines = [
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{w_page:.2f}mm" height="{h_page:.2f}mm" viewBox="0 0 {w_page:.2f} {h_page:.2f}"',
        f'     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
    ]

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    W_svg = W_real * factor
    H_svg = H_real * factor
    cx = W_svg / 2
    costura = entrada.ancho_costura
    
    def get_y(l_acumulado: float) -> float:
        if seccion == "inferior":
            y = (L_real - l_acumulado) * factor
        else:
            y = l_acumulado * factor
        return y

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

    path_cut = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_cut)
    path_cut += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_cut))
    path_cut += " Z"

    path_seam = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_seam)
    path_seam += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_seam))
    path_seam += " Z"

    total_w_content = cols * W_svg + (cols - 1) * gap_mm
    total_h_content = rows * H_svg + (rows - 1) * gap_mm
    off_x = (w_page - total_w_content) / 2
    off_y = (h_page - total_h_content) / 2

    resumen = esquema.resumen_moldes()

    fs_header = 4 * estilo.factor_texto
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="encabezado" id="layer-encabezado">')
    lines.append(f'    <text x="10" y="10" font-size="{fs_header:.2f}" fill="{estilo.texto}">Escala 1:{factor_S:.1f} | Hoja {hoja.capitalize()}</text>')
    lines.append('  </g>')

    w_eje = 0.2 * estilo.factor_trazo
    w_cuad = 0.2 * estilo.factor_trazo
    w_cost = 0.5 * estilo.factor_trazo
    w_cont = 1.0 * estilo.factor_trazo
    w_pest = 0.5 * estilo.factor_trazo
    fs_paso = 2 * estilo.factor_texto
    fs_molde = 3 * estilo.factor_texto

    for i, motivo in enumerate(motivos):
        c = i % cols
        r = i // cols
        tx = off_x + c * (W_svg + gap_mm)
        ty = off_y + r * (H_svg + gap_mm)
        
        lines.append(f'  <g transform="translate({tx:.2f}, {ty:.2f})" id="pieza-{i}">')
        
        lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="cuadricula-{i}" id="layer-cuadricula-{i}">')
        lines.append(f'      <line x1="{cx:.2f}" y1="0" x2="{cx:.2f}" y2="{L_real*factor:.2f}" stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" id="grid-center-{i}"/>')
        for j, p in enumerate(sec_res.puntos):
            y = get_y(p.largo_acumulado)
            w_cut = p.ancho_medio * factor
            lines.append(f'      <line x1="{cx - w_cut:.2f}" y1="{y:.2f}" x2="{cx + w_cut:.2f}" y2="{y:.2f}" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="grid-step-{i}-{j}"/>')
        lines.append('    </g>')
        
        lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="costura-{i}" id="layer-costura-{i}">')
        lines.append(f'      <path d="{path_seam}" fill="none" stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="2,2" id="path-seam-{i}"/>')
        lines.append('    </g>')
        
        lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="contorno-{i}" id="layer-contorno-{i}">')
        lines.append(f'      <path d="{path_cut}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_cont:.2f}" id="path-cut-{i}"/>')
        lines.append('    </g>')
        
        lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="etiquetas-{i}" id="layer-etiquetas-{i}">')
        for j, p in enumerate(sec_res.puntos):
            y = get_y(p.largo_acumulado)
            w_cut = p.ancho_medio * factor
            lines.append(f'      <text x="{cx - w_cut + 1:.2f}" y="{y - 1:.2f}" font-size="{fs_paso:.2f}" fill="{estilo.cuadricula}" id="label-step-{i}-{j+1}">{j+1}</text>')
        
        tot, en_esp, sin_esp = resumen[motivo]
        cant_por_gajo = sec_res.cantidad // entrada.num_gajos
        t_tot = tot * cant_por_gajo
        t_en_esp = en_esp * cant_por_gajo
        
        if seccion == "inferior":
            text_y = get_y(0.0) - 5
        else:
            text_y = get_y(L_real) - 5
            
        esp_txt = f" ({t_en_esp} en espejo)" if t_en_esp > 0 else ""
        lines.append(f'      <text x="{cx:.2f}" y="{text_y:.2f}" font-size="{fs_molde:.2f}" fill="{estilo.texto}" text-anchor="middle" id="label-info-{i}">Molde {motivo} — ×{t_tot}{esp_txt}</text>')
        lines.append('    </g>')
        
        if seccion == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
            lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="pestana-{i}" id="layer-pestana-{i}">')
            p_pestana = pestana_cm * factor
            y_boca = get_y(0.0)
            w_boca = sec_res.puntos[0].ancho_medio * factor
            x1 = cx - w_boca
            lines.append(f'      <rect x="{x1:.2f}" y="{y_boca:.2f}" width="{w_boca*2:.2f}" height="{p_pestana:.2f}" fill="none" stroke="{estilo.pestana}" stroke-width="{w_pest:.2f}" stroke-dasharray="2,2" id="rect-pestana-{i}"/>')
            lines.append('    </g>')
            
        lines.append(f'    <g inkscape:groupmode="layer" inkscape:label="diseno-motivo-{motivo}" id="layer-diseno-{i}">')
        lines.append('    </g>')

        lines.append('  </g>')

    lines.append('</svg>')
    
    return "\n".join(lines)


def svg_conjunto(resultado: BalloonCalculationResult, entrada: BalloonInput, escala: float = 10.0, estilo: EstiloSvg = IMPRESION) -> str:
    """Genera UN SVG con las 3 piezas (cono superior, pico, cono inferior) juntas.
    
    Colocadas una al lado de la otra a la misma escala (por defecto 1:10),
    con la punta estrecha hacia abajo, cuadrícula numerada y rótulo
    (nombre, cantidad y largo total) en mm reales.
    """
    factor = 10.0 / escala
    costura = entrada.ancho_costura
    margen_mm = 15.0
    sep_mm = 20.0
    alto_rotulo_mm = 14.0 * estilo.factor_texto

    piezas = [
        ("superior", "Cono superior", resultado.seccion_superior),
        ("pico", "Pico", resultado.seccion_picos),
        ("inferior", "Cono inferior", resultado.seccion_inferior),
    ]

    dims = []
    for clave, nombre, sec in piezas:
        w_real = max(p.ancho_medio for p in sec.puntos) * 2
        l_real = sec.generatriz_total
        w_mm = w_real * factor
        h_mm = l_real * factor
        pestana_mm = 0.0
        if clave == "inferior" and entrada.usar_parametros_avanzados and entrada.pestana_boca > 0:
            pestana_mm = entrada.pestana_boca * factor
            h_mm += pestana_mm
        dims.append({
            "clave": clave,
            "nombre": nombre,
            "sec": sec,
            "w_mm": w_mm,
            "h_mm": h_mm,
            "l_real": l_real,
            "pestana_mm": pestana_mm,
        })

    ancho_total_mm = margen_mm * 2 + sum(d["w_mm"] for d in dims) + sep_mm * (len(dims) - 1)
    max_h_piezas_mm = max(d["h_mm"] for d in dims)
    alto_total_mm = margen_mm * 2 + alto_rotulo_mm + max_h_piezas_mm

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{ancho_total_mm:.2f}mm" height="{alto_total_mm:.2f}mm" viewBox="0 0 {ancho_total_mm:.2f} {alto_total_mm:.2f}"',
        '     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
    ]

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    x_cur = margen_mm
    y_piezas_top = margen_mm + alto_rotulo_mm

    w_eje = 0.2 * estilo.factor_trazo
    w_cuad = 0.2 * estilo.factor_trazo
    w_cost = 0.4 * estilo.factor_trazo
    w_cont = 0.8 * estilo.factor_trazo
    w_pest = 0.4 * estilo.factor_trazo

    fs_tit = 4.0 * estilo.factor_texto
    fs_sub = 2.6 * estilo.factor_texto
    fs_paso = 1.8 * estilo.factor_texto

    for d in dims:
        clave = d["clave"]
        nombre = d["nombre"]
        sec = d["sec"]
        w_mm = d["w_mm"]
        l_real = d["l_real"]
        pestana_mm = d["pestana_mm"]
        cx = x_cur + w_mm / 2.0

        def get_y(l_acumulado: float, cl=clave, lr=l_real) -> float:
            if cl == "inferior":
                return y_piezas_top + (lr - l_acumulado) * factor
            else:
                return y_piezas_top + l_acumulado * factor

        pts_left_cut = []
        pts_right_cut = []
        pts_left_seam = []
        pts_right_seam = []

        for p in sec.puntos:
            y = get_y(p.largo_acumulado)
            w_cut = p.ancho_medio * factor
            w_seam = (p.ancho_medio - costura / 2.0) * factor
            pts_left_cut.append((cx - w_cut, y))
            pts_right_cut.append((cx + w_cut, y))
            pts_left_seam.append((cx - w_seam, y))
            pts_right_seam.append((cx + w_seam, y))

        path_cut = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_cut)
        path_cut += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_cut))
        path_cut += " Z"

        path_seam = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_right_seam)
        path_seam += " L " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(pts_left_seam))
        path_seam += " Z"

        if clave == "pico":
            cant_str = f"Cantidad: {sec.cantidad} triángulos ({resultado.num_piramides} pirámides × 4)"
        else:
            cant_str = f"Cantidad: {sec.cantidad} piezas"
        info_str = f"{cant_str} · Largo total {l_real:.2f} cm"

        lines.append(f'  <g id="grupo-{clave}" inkscape:label="{nombre}">')
        
        # Rótulo superior
        lines.append(f'    <text x="{cx:.2f}" y="{margen_mm + 4.0 * estilo.factor_texto:.2f}" font-size="{fs_tit:.2f}" font-weight="bold" fill="{estilo.texto}" text-anchor="middle" id="titulo-{clave}">{nombre}</text>')
        lines.append(f'    <text x="{cx:.2f}" y="{margen_mm + 9.0 * estilo.factor_texto:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" text-anchor="middle" id="info-{clave}">{info_str}</text>')

        # Cuadrícula
        lines.append(f'    <g id="cuadricula-{clave}" inkscape:groupmode="layer" inkscape:label="cuadricula-{clave}">')
        lines.append(f'      <line x1="{cx:.2f}" y1="{y_piezas_top:.2f}" x2="{cx:.2f}" y2="{y_piezas_top + l_real*factor:.2f}" stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" id="grid-center-{clave}"/>')
        for idx, p in enumerate(sec.puntos):
            y = get_y(p.largo_acumulado)
            w_cut = p.ancho_medio * factor
            lines.append(f'      <line x1="{cx - w_cut:.2f}" y1="{y:.2f}" x2="{cx + w_cut:.2f}" y2="{y:.2f}" stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" id="grid-step-{clave}-{idx}"/>')
            lines.append(f'      <text x="{cx - w_cut + 1.0:.2f}" y="{y - 0.8:.2f}" font-size="{fs_paso:.2f}" fill="{estilo.cuadricula}" id="label-step-{clave}-{idx+1}">{idx+1}</text>')
        lines.append('    </g>')

        # Costura
        lines.append(f'    <g id="costura-{clave}" inkscape:groupmode="layer" inkscape:label="costura-{clave}">')
        lines.append(f'      <path d="{path_seam}" fill="none" stroke="{estilo.costura}" stroke-width="{w_cost:.2f}" stroke-dasharray="2,2" id="path-seam-{clave}"/>')
        lines.append('    </g>')

        # Contorno
        lines.append(f'    <g id="contorno-{clave}" inkscape:groupmode="layer" inkscape:label="contorno-{clave}">')
        lines.append(f'      <path d="{path_cut}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_cont:.2f}" id="path-cut-{clave}"/>')
        lines.append('    </g>')

        # Pestaña en cono inferior
        if clave == "inferior" and pestana_mm > 0:
            lines.append(f'    <g id="pestana-{clave}" inkscape:groupmode="layer" inkscape:label="pestana-{clave}">')
            y_boca = get_y(0.0)
            w_boca = sec.puntos[0].ancho_medio * factor
            x_rec = cx - w_boca
            lines.append(f'      <rect x="{x_rec:.2f}" y="{y_boca:.2f}" width="{w_boca*2:.2f}" height="{pestana_mm:.2f}" fill="none" stroke="{estilo.pestana}" stroke-width="{w_pest:.2f}" stroke-dasharray="2,2" id="rect-pestana-{clave}"/>')
            lines.append('    </g>')

        lines.append('  </g>')

        x_cur += w_mm + sep_mm

    lines.append('</svg>')
    return "\n".join(lines)
