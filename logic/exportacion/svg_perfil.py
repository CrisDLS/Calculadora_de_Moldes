"""
Generación de SVG del perfil armado.
"""
from typing import Tuple
from logic.geometria.perfil import PerfilArmado
from logic.exportacion.estilos import EstiloSvg, IMPRESION

def svg_perfil(
    perfil: PerfilArmado,
    estilo: EstiloSvg = IMPRESION,
    escala: float = 10.0
) -> str:
    """Genera el SVG del perfil armado proyectado a escala 1:escala con cotas, anillos y pirámides."""
    factor = 10.0 / escala

    dim = perfil.dimensiones
    alto_real = dim.alto_total
    ancho_real = dim.ancho_con_picos

    dim_mayor_perfil = max(ancho_real * factor, alto_real * factor)

    if estilo.texto_proporcional:
        fs_titulo = max(4.5 * estilo.factor_texto, dim_mayor_perfil * 0.022)
        fs_sub = max(2.6 * estilo.factor_texto, dim_mayor_perfil * 0.015)
        fs_cota = max(2.8 * estilo.factor_texto, dim_mayor_perfil * 0.018)
        fs_nota = max(2.4 * estilo.factor_texto, dim_mayor_perfil * 0.014)
        margen_izq = max(60.0 * estilo.factor_texto, fs_cota * 6.0)
        margen_der = max(60.0 * estilo.factor_texto, fs_cota * 6.0)
        margen_sup = max(35.0 * estilo.factor_texto, fs_titulo * 3.0)
        margen_inf = max(40.0 * estilo.factor_texto, (fs_cota + fs_nota) * 3.5)
    else:
        fs_titulo = 4.5 * estilo.factor_texto
        fs_sub = 2.6 * estilo.factor_texto
        fs_cota = 2.8 * estilo.factor_texto
        fs_nota = 2.4 * estilo.factor_texto
        margen_izq = 60.0 * estilo.factor_texto
        margen_der = 60.0 * estilo.factor_texto
        margen_sup = 35.0 * estilo.factor_texto
        margen_inf = 40.0 * estilo.factor_texto

    dibujo_w = ancho_real * factor
    dibujo_h = alto_real * factor

    svg_w = dibujo_w + margen_izq + margen_der
    svg_h = dibujo_h + margen_sup + margen_inf

    # El eje central del globo en el dibujo
    cx = margen_izq + dibujo_w / 2.0
    # En el SVG y=0 está arriba. En el globo z=0 (boca) está abajo, z=alto (apex) está arriba.
    # Por tanto: svg_y = margen_sup + (alto_real - z) * factor
    def pt(x_cm: float, z_cm: float) -> Tuple[float, float]:
        sx = cx + x_cm * factor
        sy = margen_sup + (alto_real - z_cm) * factor
        return sx, sy

    # Construir contorno cerrado
    pts_perfil = []
    # Lado derecho: de z=0 a z=alto
    for x, z in perfil.contorno_derecho:
        pts_perfil.append(pt(x, z))
    # Lado izquierdo: de z=alto a z=0
    for x, z in reversed(perfil.contorno_izquierdo):
        pts_perfil.append(pt(x, z))

    path_silueta = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts_perfil) + " Z"

    # Líneas y grosores
    w_cont = 1.0 * estilo.factor_trazo
    w_eje = 0.3 * estilo.factor_trazo
    w_cuad = 0.25 * estilo.factor_trazo
    w_cota = 0.35 * estilo.factor_trazo
    w_pir = 0.45 * estilo.factor_trazo

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{svg_w:.2f}mm" height="{svg_h:.2f}mm" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}"',
        '     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">',
    ]

    # Marcadores de flechas para cotas
    lines.extend([
        '  <defs>',
        f'    <marker id="arrow-start" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">',
        f'      <path d="M 5 1 L 1 3 L 5 5 Z" fill="{estilo.texto}" />',
        '    </marker>',
        f'    <marker id="arrow-end" markerWidth="6" markerHeight="6" refX="1" refY="3" orient="auto">',
        f'      <path d="M 1 1 L 5 3 L 1 5 Z" fill="{estilo.texto}" />',
        '    </marker>',
        '  </defs>',
    ])

    if estilo.fondo:
        lines.append(f'  <rect width="100%" height="100%" fill="{estilo.fondo}" id="fondo"/>')

    # Relleno tenue de la silueta
    # Relleno tenue usando opacidad de contorno
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="relleno" id="layer-relleno">')
    lines.append(f'    <path d="{path_silueta}" fill="{estilo.contorno}" fill-opacity="0.08" id="path-relleno"/>')
    lines.append('  </g>')

    # Anillos horizontales (cuadrícula)
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="anillos" id="layer-anillos">')
    for i, a in enumerate(perfil.anillos):
        p_izq = pt(-a.semiancho_silueta, a.z)
        p_der = pt(a.semiancho_silueta, a.z)
        lines.append(
            f'    <line x1="{p_izq[0]:.2f}" y1="{p_izq[1]:.2f}" x2="{p_der[0]:.2f}" y2="{p_der[1]:.2f}" '
            f'stroke="{estilo.cuadricula}" stroke-width="{w_cuad:.2f}" stroke-dasharray="3,2" id="anillo-{i}"/>'
        )
    lines.append('  </g>')

    # Pirámides interiores proyectadas
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="piramides" id="layer-piramides">')
    for idx_pir, pir in enumerate(perfil.piramides):
        # Aristas de la pirámide proyectada: del ápice a las bases superior e inferior
        p_apex = pt(pir.apex_x, pir.apex_z)
        # Líneas a la base
        base_x = dim.diametro_cuerpo / 2.0 if pir.lado == "derecha" else -dim.diametro_cuerpo / 2.0
        p_base_inf = pt(base_x, pir.base_inferior_z)
        p_base_sup = pt(base_x, pir.base_superior_z)
        dash = 'stroke-dasharray="2,1"' if not pir.es_borde_extremo else ''
        lines.append(
            f'    <line x1="{p_base_inf[0]:.2f}" y1="{p_base_inf[1]:.2f}" x2="{p_apex[0]:.2f}" y2="{p_apex[1]:.2f}" '
            f'stroke="{estilo.costura}" stroke-width="{w_pir:.2f}" {dash} id="pir-inf-{idx_pir}"/>'
        )
        lines.append(
            f'    <line x1="{p_base_sup[0]:.2f}" y1="{p_base_sup[1]:.2f}" x2="{p_apex[0]:.2f}" y2="{p_apex[1]:.2f}" '
            f'stroke="{estilo.costura}" stroke-width="{w_pir:.2f}" {dash} id="pir-sup-{idx_pir}"/>'
        )
    lines.append('  </g>')

    # Eje central discontinuo
    p_boca_cen = pt(0.0, 0.0)
    p_apex_cen = pt(0.0, alto_real)
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="eje" id="layer-eje">')
    lines.append(
        f'    <line x1="{p_boca_cen[0]:.2f}" y1="{p_boca_cen[1]+8:.2f}" x2="{p_apex_cen[0]:.2f}" y2="{p_apex_cen[1]-8:.2f}" '
        f'stroke="{estilo.eje}" stroke-width="{w_eje:.2f}" stroke-dasharray="6,3,1,3" id="eje-central"/>'
    )
    lines.append('  </g>')

    # Contorno exterior de la silueta
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="contorno" id="layer-contorno">')
    lines.append(f'    <path d="{path_silueta}" fill="none" stroke="{estilo.contorno}" stroke-width="{w_cont:.2f}" id="path-silueta"/>')
    lines.append('  </g>')

    # Cotas
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="cotas" id="layer-cotas">')

    # 1. Cota de Alto Total (Izquierda)
    cota_x_alto = margen_izq * 0.25
    y_apex = pt(0.0, alto_real)[1]
    y_boca = pt(0.0, 0.0)[1]
    # Líneas auxiliares
    lines.append(f'    <line x1="{cota_x_alto:.2f}" y1="{y_apex:.2f}" x2="{cx - ancho_real*factor/2.0 - 2:.2f}" y2="{y_apex:.2f}" stroke="{estilo.texto}" stroke-width="0.15" stroke-dasharray="1,1"/>')
    lines.append(f'    <line x1="{cota_x_alto:.2f}" y1="{y_boca:.2f}" x2="{cx - dim.diametro_boca*factor/2.0 - 2:.2f}" y2="{y_boca:.2f}" stroke="{estilo.texto}" stroke-width="0.15" stroke-dasharray="1,1"/>')
    # Flecha vertical
    lines.append(f'    <line x1="{cota_x_alto:.2f}" y1="{y_apex:.2f}" x2="{cota_x_alto:.2f}" y2="{y_boca:.2f}" stroke="{estilo.texto}" stroke-width="{w_cota:.2f}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" id="cota-alto-total"/>')
    # Texto centrado rotado o al lado
    mid_y_alto = (y_apex + y_boca) / 2.0
    lines.append(f'    <text x="{cota_x_alto - 3:.2f}" y="{mid_y_alto:.2f}" font-size="{fs_cota:.2f}" fill="{estilo.texto}" text-anchor="middle" transform="rotate(-90 {cota_x_alto - 3:.2f} {mid_y_alto:.2f})">Alto total: {alto_real:.1f} cm</text>')

    # 2. Cota de Diámetro con Picos (Arriba o en el punto de mayor ancho)
    y_max_picos = pt(0.0, perfil.piramides[0].apex_z)[1] if perfil.piramides else (y_apex + y_boca)/2.0
    cota_x_izq = pt(-ancho_real/2.0, 0)[0]
    cota_x_der = pt(ancho_real/2.0, 0)[0]
    lines.append(f'    <line x1="{cota_x_izq:.2f}" y1="{y_max_picos:.2f}" x2="{cota_x_der:.2f}" y2="{y_max_picos:.2f}" stroke="{estilo.texto}" stroke-width="{w_cota:.2f}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" id="cota-ancho-picos"/>')
    lines.append(f'    <text x="{cx:.2f}" y="{y_max_picos - 3:.2f}" font-size="{fs_cota:.2f}" fill="{estilo.texto}" text-anchor="middle">Ø con picos: {ancho_real:.1f} cm</text>')

    # 3. Cota de Diámetro del Cuerpo (Derecha o bajo picos)
    r_cuerpo = dim.diametro_cuerpo / 2.0
    z_banda_inf = perfil.anillos[1].z
    y_cuerpo = pt(0.0, z_banda_inf)[1]
    cota_x_cuerpo_izq = pt(-r_cuerpo, 0)[0]
    cota_x_cuerpo_der = pt(r_cuerpo, 0)[0]
    lines.append(f'    <line x1="{cota_x_cuerpo_izq:.2f}" y1="{y_cuerpo:.2f}" x2="{cota_x_cuerpo_der:.2f}" y2="{y_cuerpo:.2f}" stroke="{estilo.texto}" stroke-width="{w_cota:.2f}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" id="cota-diam-cuerpo"/>')
    lines.append(f'    <text x="{cx:.2f}" y="{y_cuerpo + fs_cota + 1:.2f}" font-size="{fs_cota:.2f}" fill="{estilo.texto}" text-anchor="middle">Ø cuerpo: {dim.diametro_cuerpo:.1f} cm</text>')

    # 4. Cota de Boca (Abajo)
    y_cota_boca = y_boca + 8 * estilo.factor_texto
    r_boca = dim.diametro_boca / 2.0
    cota_boca_izq = pt(-r_boca, 0)[0]
    cota_boca_der = pt(r_boca, 0)[0]
    lines.append(f'    <line x1="{cota_boca_izq:.2f}" y1="{y_boca:.2f}" x2="{cota_boca_izq:.2f}" y2="{y_cota_boca + 2:.2f}" stroke="{estilo.texto}" stroke-width="0.15" stroke-dasharray="1,1"/>')
    lines.append(f'    <line x1="{cota_boca_der:.2f}" y1="{y_boca:.2f}" x2="{cota_boca_der:.2f}" y2="{y_cota_boca + 2:.2f}" stroke="{estilo.texto}" stroke-width="0.15" stroke-dasharray="1,1"/>')
    lines.append(f'    <line x1="{cota_boca_izq:.2f}" y1="{y_cota_boca:.2f}" x2="{cota_boca_der:.2f}" y2="{y_cota_boca:.2f}" stroke="{estilo.texto}" stroke-width="{w_cota:.2f}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" id="cota-diam-boca"/>')
    lines.append(f'    <text x="{cx:.2f}" y="{y_cota_boca + fs_cota + 1:.2f}" font-size="{fs_cota:.2f}" fill="{estilo.texto}" text-anchor="middle">Ø boca: {dim.diametro_boca:.1f} cm</text>')

    lines.append('  </g>')

    # Rótulos de Encabezado y Pie
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="etiquetas" id="layer-etiquetas">')
    # Título arriba
    lines.append(f'    <text x="{cx:.2f}" y="{margen_sup * 0.45:.2f}" font-size="{fs_titulo:.2f}" font-weight="bold" fill="{estilo.texto}" text-anchor="middle" id="titulo-perfil">Perfil armado</text>')
    lines.append(f'    <text x="{cx:.2f}" y="{margen_sup * 0.75:.2f}" font-size="{fs_sub:.2f}" fill="{estilo.texto}" text-anchor="middle" id="subtitulo-escala">Escala 1:{escala:.0f} · Vista lateral proyectada</text>')

    # Nota abajo
    y_nota = svg_h - margen_inf * 0.25
    lines.append(f'    <text x="{cx:.2f}" y="{y_nota:.2f}" font-size="{fs_nota:.2f}" fill="{estilo.texto}" text-anchor="middle" id="nota-poligono">Medidas del polígono exacto (el Resumen usa una estimación circular, diferencia &lt; 0.5 %)</text>')
    lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)
