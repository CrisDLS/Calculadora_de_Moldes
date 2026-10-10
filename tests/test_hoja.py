import pytest
import xml.etree.ElementTree as ET
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.svg_moldes import svg_hoja

@pytest.fixture(scope="module")
def calculos():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    r = calc.calcular(ent)
    return ent, r

def test_svg_hoja_carta_auto(calculos):
    ent, r = calculos
    eq = EsquemaDiseno("central_espejo", 5) # 3 motivos
    
    # SVG hoja carta
    svg_str = svg_hoja(r, ent, "inferior", eq, escala="auto", hoja="carta", margen_mm=10.0)
    
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    root = ET.fromstring(svg_str)
    
    w_mm = root.attrib['width']
    h_mm = root.attrib['height']
    
    assert float(w_mm[:-2]) == pytest.approx(215.9)
    assert float(h_mm[:-2]) == pytest.approx(279.4)
    
    # Contiene 3 g's principales por pieza
    piezas = [g for g in root.findall("{http://www.w3.org/2000/svg}g") if g.attrib.get('id', '').startswith("pieza-")]
    assert len(piezas) == 3
    
    # Capa etiquetas: "Molde X — ×Y (Z en espejo)"
    # N=30, G=5 central_espejo -> 6 repeticiones.
    # eq.resumen_motivos: m0 -> (6,0), m1 -> (12, 6), m2 -> (12, 6)
    texts_found = []
    for p in piezas:
        for g in p.findall("{http://www.w3.org/2000/svg}g"):
            if "etiquetas" in g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label', ''):
                for t in g.findall("{http://www.w3.org/2000/svg}text"):
                    if t.text and t.text.startswith("Molde"):
                        texts_found.append(t.text)
                        
    assert "Molde 0 — ×6" in texts_found
    assert "Molde 1 — ×12 (6 en espejo)" in texts_found
    assert "Molde 2 — ×12 (6 en espejo)" in texts_found

def test_svg_hoja_escala_forzada(calculos):
    ent, r = calculos
    eq = EsquemaDiseno("repeticion", 5) # 5 motivos
    
    # 1:19 forced should fit
    svg_str = svg_hoja(r, ent, "inferior", eq, escala=19.0, hoja="carta")
    assert svg_str is not None
    
    # 1:5 should not fit
    with pytest.raises(ValueError, match="No caben a escala"):
        svg_hoja(r, ent, "inferior", eq, escala=5.0, hoja="carta")

def test_svg_hoja_a4(calculos):
    ent, r = calculos
    eq = EsquemaDiseno("repeticion", 1)
    svg_str = svg_hoja(r, ent, "inferior", eq, escala="auto", hoja="a4")
    root = ET.fromstring(svg_str)
    assert float(root.attrib['width'][:-2]) == pytest.approx(210.0)
    assert float(root.attrib['height'][:-2]) == pytest.approx(297.0)

def test_svg_hoja_cantidades_ejemplos_usuario():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(100, 20, 2, 1, usar_parametros_avanzados=False) # N=20
    r = calc.calcular(ent)
    
    # 1) repeticion G=5
    eq1 = EsquemaDiseno("repeticion", 5)
    svg1 = svg_hoja(r, ent, "superior", eq1, escala="auto", hoja="carta")
    assert "Molde 4 — ×4" in svg1
    
    # 2) central_espejo G=5
    eq2 = EsquemaDiseno("central_espejo", 5)
    svg2 = svg_hoja(r, ent, "superior", eq2, escala="auto", hoja="carta")
    assert "Molde 0 — ×4</text>" in svg2
    assert "Molde 1 — ×8 (4 en espejo)" in svg2
    assert "Molde 2 — ×8 (4 en espejo)" in svg2
    
    # 3) espejo_total G=4
    eq3 = EsquemaDiseno("espejo_total", 4)
    svg3 = svg_hoja(r, ent, "superior", eq3, escala="auto", hoja="carta")
    assert "Molde 0 — ×10 (5 en espejo)" in svg3
    assert "Molde 1 — ×10 (5 en espejo)" in svg3
