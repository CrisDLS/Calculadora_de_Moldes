import pytest
import xml.etree.ElementTree as ET
from logic.exportacion.estilos import IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator

def _srgb_to_linear(c_srgb: float) -> float:
    if c_srgb <= 0.03928:
        return c_srgb / 12.92
    return ((c_srgb + 0.055) / 1.055) ** 2.4

def _luminancia_relativa(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)

def _ratio_contraste(hex1: str, hex2: str) -> float:
    l1 = _luminancia_relativa(hex1)
    l2 = _luminancia_relativa(hex2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def test_contraste_wcag_presets_pantalla():
    for preset, nombre in [(PANTALLA_OSCURO, "PANTALLA_OSCURO"), (PANTALLA_CLARO, "PANTALLA_CLARO")]:
        fondo = preset.fondo_referencia
        # Texto
        ratio_texto = _ratio_contraste(preset.texto, fondo)
        assert ratio_texto >= 4.5, f"Texto en {nombre} ({preset.texto}) contra fondo ({fondo}) tiene ratio {ratio_texto:.2f} < 4.5"
        # Contorno
        ratio_contorno = _ratio_contraste(preset.contorno, fondo)
        assert ratio_contorno >= 4.5, f"Contorno en {nombre} ({preset.contorno}) contra fondo ({fondo}) tiene ratio {ratio_contorno:.2f} < 4.5"


def test_los_tres_estilos_producen_xml_valido_y_capas():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    r = calc.calcular(ent)

    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")

    for est in [IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO]:
        svg_p = svg_pieza(r, ent, "inferior", escala=10.0, estilo=est)
        root_p = ET.fromstring(svg_p)
        assert root_p.tag.endswith("svg")
        layers = [g.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') for g in root_p.findall("{http://www.w3.org/2000/svg}g")]
        assert "contorno" in layers
        assert "costura" in layers
        assert "cuadricula" in layers
        assert "etiquetas" in layers
        assert "pestana" in layers

        svg_c = svg_conjunto(r, ent, escala=10.0, estilo=est)
        root_c = ET.fromstring(svg_c)
        assert root_c.tag.endswith("svg")
        grupos = [g.attrib.get("id") for g in root_c.findall("{http://www.w3.org/2000/svg}g")]
        assert "grupo-superior" in grupos
        assert "grupo-pico" in grupos
        assert "grupo-inferior" in grupos


def test_factor_texto_y_trazo_escala():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950, 30, 2, 1)
    r = calc.calcular(ent)

    svg_imp = svg_pieza(r, ent, "superior", escala=10.0, estilo=IMPRESION)
    svg_osc = svg_pieza(r, ent, "superior", escala=10.0, estilo=PANTALLA_OSCURO)

    root_imp = ET.fromstring(svg_imp)
    root_osc = ET.fromstring(svg_osc)

    # Texto de paso 1
    t_imp = root_imp.find('.//{http://www.w3.org/2000/svg}text[@id="label-step-1"]')
    t_osc = root_osc.find('.//{http://www.w3.org/2000/svg}text[@id="label-step-1"]')

    fs_imp = float(t_imp.attrib['font-size'])
    fs_osc = float(t_osc.attrib['font-size'])
    assert fs_osc == pytest.approx(fs_imp * PANTALLA_OSCURO.factor_texto, abs=0.01)


def test_tamano_letra_proporcional_en_pantalla_e_impresion_invariable():
    calc = TrompoEstrellaCalculator()
    for (h, g, hil, c) in [(950, 30, 2, 1), (380, 30, 2, 1)]:
        ent = BalloonInput(h, g, hil, c)
        r = calc.calcular(ent)

        # 1. IMPRESION no usa texto proporcional y mantiene factor 1.0 exacto
        svg_imp = svg_conjunto(r, ent, escala=10.0, estilo=IMPRESION)
        root_imp = ET.fromstring(svg_imp)
        t_tit_imp = root_imp.find('.//{http://www.w3.org/2000/svg}text[@id="titulo-superior"]')
        assert float(t_tit_imp.attrib['font-size']) == pytest.approx(4.0, abs=1e-3)

        # 2. En pantalla (PANTALLA_OSCURO y PANTALLA_CLARO), el texto es proporcional al tamaño del SVG
        for est_pantalla in [PANTALLA_OSCURO, PANTALLA_CLARO]:
            svg_pant = svg_conjunto(r, ent, escala=10.0, estilo=est_pantalla)
            root_pant = ET.fromstring(svg_pant)
            w_svg = float(root_pant.attrib['width'].replace('mm', ''))
            h_svg = float(root_pant.attrib['height'].replace('mm', ''))
            dim_mayor = max(w_svg, h_svg)

            t_tit_pant = root_pant.find('.//{http://www.w3.org/2000/svg}text[@id="titulo-superior"]')
            fs_tit_pant = float(t_tit_pant.attrib['font-size'])
            # Altura de letra entre 1.8 % y 3.5 % de la dimensión mayor
            pct = fs_tit_pant / dim_mayor
            assert 0.018 <= pct <= 0.035, f"Texto en {h} tiene {pct*100:.2f}% de la dimensión mayor ({dim_mayor}mm)"
