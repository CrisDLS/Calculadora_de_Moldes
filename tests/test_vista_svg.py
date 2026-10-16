# tests/test_vista_svg.py
import pytest
import xml.etree.ElementTree as ET
from logic.exportacion.vista_svg import (
    VistaSvg,
    ajustar,
    zoom,
    desplazar,
    aplicar_viewbox,
    extraer_dimensiones_svg,
)

def test_ajustar_encaja_contenido_centrado():
    # Caso 1: Contenido ancho en zona horizontal
    v1 = ajustar(200.0, 100.0, aspecto_zona=2.0, margen=0.0)
    assert v1.ancho == pytest.approx(200.0)
    assert v1.alto == pytest.approx(100.0)
    assert v1.x == pytest.approx(0.0)
    assert v1.y == pytest.approx(0.0)

    # Caso 2: Contenido alto en zona horizontal
    # Contenido 100 x 200, aspecto 0.5. Zona aspecto 2.0. El alto manda.
    v2 = ajustar(100.0, 200.0, aspecto_zona=2.0, margen=0.0)
    assert v2.alto == pytest.approx(200.0)
    assert v2.ancho == pytest.approx(400.0) # 200 * 2.0
    # Centrado en X: (100 / 2) - (400 / 2) = 50 - 200 = -150
    assert v2.x == pytest.approx(-150.0)
    assert v2.y == pytest.approx(0.0)

    # Caso 3: Contenido con margen
    v3 = ajustar(100.0, 100.0, aspecto_zona=1.0, margen=0.1) # 10% margen a cada lado -> 1.2
    assert v3.ancho == pytest.approx(120.0)
    assert v3.alto == pytest.approx(120.0)
    assert v3.x == pytest.approx(-10.0)
    assert v3.y == pytest.approx(-10.0)


def test_zoom_invariancia_punto_cursor():
    v = VistaSvg(x=10.0, y=20.0, ancho=200.0, alto=100.0)
    # Cursor al 30% en X, 70% en Y
    fx = 0.3
    fy = 0.7
    px_esperado = v.x + fx * v.ancho # 10 + 60 = 70.0
    py_esperado = v.y + fy * v.alto  # 20 + 70 = 90.0

    # Zoom in 2.5x
    v_zoom = zoom(v, factor=2.5, fx=fx, fy=fy)
    px_resultante = v_zoom.x + fx * v_zoom.ancho
    py_resultante = v_zoom.y + fy * v_zoom.alto

    assert px_resultante == pytest.approx(px_esperado)
    assert py_resultante == pytest.approx(py_esperado)
    assert v_zoom.ancho == pytest.approx(200.0 / 2.5)
    assert v_zoom.alto == pytest.approx(100.0 / 2.5)


def test_zoom_ida_y_vuelta():
    v_inicial = VistaSvg(x=0.0, y=0.0, ancho=300.0, alto=150.0)
    fx, fy = 0.4, 0.6

    # Zoom in 3x
    v_in = zoom(v_inicial, factor=3.0, fx=fx, fy=fy)
    # Zoom out 3x
    v_out = zoom(v_in, factor=1.0 / 3.0, fx=fx, fy=fy)

    assert v_out.x == pytest.approx(v_inicial.x, abs=1e-4)
    assert v_out.y == pytest.approx(v_inicial.y, abs=1e-4)
    assert v_out.ancho == pytest.approx(v_inicial.ancho, abs=1e-4)
    assert v_out.alto == pytest.approx(v_inicial.alto, abs=1e-4)


def test_zoom_limites():
    v = VistaSvg(x=0.0, y=0.0, ancho=100.0, alto=100.0)
    # Limites: ancho mínimo 5.0 (zoom max 20x), ancho máximo 200.0 (zoom min 0.5x)
    limites = (5.0, 200.0)

    # Intentar zoom in excesivo (factor 50x)
    v_max = zoom(v, factor=50.0, fx=0.5, fy=0.5, limites=limites)
    assert v_max.ancho == pytest.approx(5.0)

    # Intentar zoom out excesivo (factor 0.1x)
    v_min = zoom(v, factor=0.1, fx=0.5, fy=0.5, limites=limites)
    assert v_min.ancho == pytest.approx(200.0)


def test_desplazar_y_limites():
    v = VistaSvg(x=0.0, y=0.0, ancho=100.0, alto=100.0)
    # Desplazamiento simple
    v_mov = desplazar(v, dx=30.0, dy=-20.0)
    assert v_mov.x == pytest.approx(-30.0)
    assert v_mov.y == pytest.approx(20.0)
    assert v_mov.ancho == 100.0
    assert v_mov.alto == 100.0

    # Desplazamiento con límites de contenido (contenido 200x200)
    # Intento de desplazar a la luna (dx = -5000)
    v_lim = desplazar(v, dx=-5000.0, dy=-5000.0, limites_contenido=(200.0, 200.0))
    # No puede perderse totalmente
    assert v_lim.x <= 200.0 - 100.0 * 0.1
    assert v_lim.y <= 200.0 - 100.0 * 0.1


def test_aplicar_viewbox_y_xml_valido():
    svg_original = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg width="250.00mm" height="400.00mm" viewBox="0 0 250.00 400.00" xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect x="0" y="0" width="100" height="100" fill="red"/>\n'
        '</svg>'
    )
    dim_w, dim_h = extraer_dimensiones_svg(svg_original)
    assert dim_w == pytest.approx(250.0)
    assert dim_h == pytest.approx(400.0)

    vista = VistaSvg(x=25.0, y=50.0, ancho=125.0, alto=200.0)
    svg_modificado = aplicar_viewbox(svg_original, vista)

    # Validar que es XML bien formado
    root = ET.fromstring(svg_modificado)
    assert root.tag.endswith("svg")
    assert root.attrib["width"] == "100%"
    assert root.attrib["height"] == "100%"
    assert root.attrib["preserveAspectRatio"] == "xMidYMid meet"
    assert root.attrib["viewBox"] == "25.00 50.00 125.00 200.00"
