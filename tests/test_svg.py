import pytest
import xml.etree.ElementTree as ET
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.exportacion.svg_moldes import svg_pieza

def test_svg_dimensiones_y_capas():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    r = calc.calcular(ent)
    
    svg_str = svg_pieza(r, ent, "inferior", escala=10.0)
    
    # Parsear XML
    # Añadir namespace de inkscape
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    root = ET.fromstring(svg_str)
    
    # Dimensiones
    w_mm = root.attrib['width']
    h_mm = root.attrib['height']
    assert w_mm.endswith("mm")
    assert h_mm.endswith("mm")
    
    w_val = float(w_mm[:-2])
    h_val = float(h_mm[:-2])
    
    # Verificación exacta de valores
    l_inf = r.seccion_inferior.generatriz_total # aprox 468.9166
    max_ancho = max(p.ancho_medio for p in r.seccion_inferior.puntos) * 2
    # Factor = 1.0
    assert h_val == pytest.approx(l_inf + 4.0, abs=0.1) # 4cm pestaña
    assert w_val == pytest.approx(max_ancho, abs=0.1)
    
    # Capas
    layers = [g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') for g in root.findall("{http://www.w3.org/2000/svg}g")]
    assert "contorno" in layers
    assert "costura" in layers
    assert "cuadricula" in layers
    assert "etiquetas" in layers
    assert "pestana" in layers
    assert "diseno" in layers
    
    # Elementos en cuadricula (1 vertical + 25 pasos horizontales = 26 líneas)
    grid_layer = next(g for g in root.findall("{http://www.w3.org/2000/svg}g") if g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') == 'cuadricula')
    lines = grid_layer.findall("{http://www.w3.org/2000/svg}line")
    assert len(lines) == 26
    
    # Etiquetas (25 puntos) + 1 general
    labels_layer = next(g for g in root.findall("{http://www.w3.org/2000/svg}g") if g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') == 'etiquetas')
    texts = labels_layer.findall("{http://www.w3.org/2000/svg}text")
    assert len(texts) == 26

def test_svg_cambio_escala():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    r = calc.calcular(ent)
    
    svg_str_10 = svg_pieza(r, ent, "superior", escala=10.0)
    svg_str_20 = svg_pieza(r, ent, "superior", escala=20.0)
    
    root_10 = ET.fromstring(svg_str_10)
    root_20 = ET.fromstring(svg_str_20)
    
    w_10 = float(root_10.attrib['width'][:-2])
    w_20 = float(root_20.attrib['width'][:-2])
    
    assert w_20 == pytest.approx(w_10 / 2, abs=0.01)

def test_svg_sin_pestana_en_simple():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=False)
    r = calc.calcular(ent)
    
    svg_str = svg_pieza(r, ent, "inferior", escala=10.0)
    root = ET.fromstring(svg_str)
    
    layers = [g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') for g in root.findall("{http://www.w3.org/2000/svg}g")]
    assert "pestana" not in layers


def test_svg_conjunto_valido_y_dimensiones():
    from logic.exportacion.svg_moldes import svg_conjunto
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=False)
    r = calc.calcular(ent)

    svg_str = svg_conjunto(r, ent, escala=10.0)

    # 1. XML válido
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")

    # 2. Tres grupos principales
    grupos = [g.attrib.get("id") for g in root.findall("{http://www.w3.org/2000/svg}g")]
    assert "grupo-superior" in grupos
    assert "grupo-pico" in grupos
    assert "grupo-inferior" in grupos

    # 3. Dimensiones esperadas para 950/30/2/1 a 1:10 (factor = 1.0 mm/cm)
    w_sup = max(p.ancho_medio for p in r.seccion_superior.puntos) * 2
    w_pic = max(p.ancho_medio for p in r.seccion_picos.puntos) * 2
    w_inf = max(p.ancho_medio for p in r.seccion_inferior.puntos) * 2
    w_total_esperado = 15.0 * 2 + (w_sup + w_pic + w_inf) * 1.0 + 20.0 * 2
    fs_tit = 4.0
    fs_sub = 2.6
    alto_rotulo_esperado = fs_tit + 3 * (fs_sub * 1.35) + 6.0
    h_max_esperado = 15.0 * 2 + alto_rotulo_esperado + r.seccion_inferior.generatriz_total * 1.0

    w_val = float(root.attrib['width'][:-2])
    h_val = float(root.attrib['height'][:-2])
    assert w_val == pytest.approx(w_total_esperado, abs=0.1)
    assert h_val == pytest.approx(h_max_esperado, abs=0.1)

    # 4. Rótulos presentes
    assert "Cono superior" in svg_str
    assert "Pico" in svg_str
    assert "Cono inferior" in svg_str
    assert f"Largo total: {r.seccion_superior.generatriz_total:.2f} cm" in svg_str
    assert f"Largo total: {r.seccion_picos.generatriz_total:.2f} cm" in svg_str
    assert f"Largo total: {r.seccion_inferior.generatriz_total:.2f} cm" in svg_str
    assert f"{r.seccion_superior.cantidad} piezas" in svg_str
    assert f"{r.seccion_picos.cantidad} triángulos" in svg_str


def test_svg_conjunto_rotulos_no_se_intersectan():
    from logic.exportacion.svg_moldes import svg_conjunto
    from logic.exportacion.estilos import IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO

    calc = TrompoEstrellaCalculator()
    casos = [
        BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=False),
        BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4),
        BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=False),
        BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=True, diametro_boca=53.2),
    ]
    estilos = [IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO]

    for entrada in casos:
        resultado = calc.calcular(entrada)
        for estilo in estilos:
            svg_str = svg_conjunto(resultado, entrada, escala=10.0, estilo=estilo)
            root = ET.fromstring(svg_str)

            # Capas y grupos por pieza
            grupos_piezas = ["grupo-superior", "grupo-pico", "grupo-inferior"]
            boxes_por_pieza = {}

            for g_id in grupos_piezas:
                grupo = root.find(f'.//{{http://www.w3.org/2000/svg}}g[@id="{g_id}"]')
                assert grupo is not None, f"Falta {g_id} en svg_conjunto"

                # Subcapas requeridas
                subcapas = [c.attrib.get("id") for c in grupo.findall("{http://www.w3.org/2000/svg}g")]
                clave = g_id.replace("grupo-", "")
                assert f"cuadricula-{clave}" in subcapas
                assert f"costura-{clave}" in subcapas
                assert f"contorno-{clave}" in subcapas

                # Extraer rótulos (textos hijos directos de grupo-{clave})
                textos = grupo.findall("{http://www.w3.org/2000/svg}text")
                assert len(textos) >= 3, f"Se esperaban al menos 3 líneas de rótulo para {g_id}"

                boxes = []
                for t in textos:
                    txt = t.text or ""
                    fs = float(t.attrib.get("font-size", 2.6))
                    w_est = len(txt) * fs * 0.6
                    cx = float(t.attrib["x"])
                    cy = float(t.attrib["y"])
                    # Bounding box: [x1, y1, x2, y2]
                    x1 = cx - w_est / 2.0
                    x2 = cx + w_est / 2.0
                    y1 = cy - fs
                    y2 = cy
                    boxes.append((x1, y1, x2, y2, txt))
                boxes_por_pieza[g_id] = boxes

            # Verificar que NINGÚN rótulo de una pieza se intersecta con el de otra pieza vecina
            # Superior está a la izquierda de Pico, y Pico a la izquierda de Inferior
            for p_izq, p_der in [("grupo-superior", "grupo-pico"), ("grupo-pico", "grupo-inferior")]:
                max_x2_izq = max(b[2] for b in boxes_por_pieza[p_izq])
                min_x1_der = min(b[0] for b in boxes_por_pieza[p_der])
                assert max_x2_izq < min_x1_der, (
                    f"Rótulos encimados entre {p_izq} (max_x={max_x2_izq:.2f}) y {p_der} (min_x={min_x1_der:.2f}) "
                    f"con entrada {entrada.altura_cuerpo}/{entrada.num_gajos} y estilo {estilo}"
                )



def test_svg_conjunto_escala_comun():
    from logic.exportacion.svg_moldes import svg_conjunto
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    r = calc.calcular(ent)

    svg_10 = svg_conjunto(r, ent, escala=10.0)
    svg_20 = svg_conjunto(r, ent, escala=20.0)

    root_10 = ET.fromstring(svg_10)
    root_20 = ET.fromstring(svg_20)

    # Revisar las líneas de centro de cada pieza: la relación de largo debe ser exactamente la misma (factor 1.0 vs 0.5)
    line_sup_10 = root_10.find('.//{http://www.w3.org/2000/svg}line[@id="grid-center-superior"]')
    line_sup_20 = root_20.find('.//{http://www.w3.org/2000/svg}line[@id="grid-center-superior"]')
    largo_10 = float(line_sup_10.attrib['y2']) - float(line_sup_10.attrib['y1'])
    largo_20 = float(line_sup_20.attrib['y2']) - float(line_sup_20.attrib['y1'])
    assert largo_20 == pytest.approx(largo_10 / 2.0, abs=0.01)

    line_inf_10 = root_10.find('.//{http://www.w3.org/2000/svg}line[@id="grid-center-inferior"]')
    line_inf_20 = root_20.find('.//{http://www.w3.org/2000/svg}line[@id="grid-center-inferior"]')
    largo_inf_10 = float(line_inf_10.attrib['y2']) - float(line_inf_10.attrib['y1'])
    largo_inf_20 = float(line_inf_20.attrib['y2']) - float(line_inf_20.attrib['y1'])
    assert largo_inf_20 == pytest.approx(largo_inf_10 / 2.0, abs=0.01)

    # Pestaña presente en inferior avanzado
    rect_pestana = root_10.find('.//{http://www.w3.org/2000/svg}rect[@id="rect-pestana-inferior"]')
    assert rect_pestana is not None
