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
