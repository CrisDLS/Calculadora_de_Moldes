import pytest
import xml.etree.ElementTree as ET
import re
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto, svg_hoja
from logic.exportacion.svg_perfil import svg_perfil
from logic.geometria.perfil import perfil_armado
from logic.exportacion.estilos import IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO
from logic.diseno.esquema import EsquemaDiseno

def get_texts_bounding_boxes(elem, tx=0.0, ty=0.0):
    """Extrae las cajas delimitadoras estimadas de todos los textos no rotados."""
    res = []
    tr = elem.attrib.get('transform', '')
    cur_tx, cur_ty = tx, ty
    m = re.search(r'translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', tr)
    if m:
        cur_tx += float(m.group(1))
        cur_ty += float(m.group(2))
    
    if elem.tag.endswith('text'):
        txt = ''.join(elem.itertext()).strip()
        if txt:
            x = float(elem.attrib.get('x', 0.0)) + cur_tx
            y = float(elem.attrib.get('y', 0.0)) + cur_ty
            fs = float(elem.attrib.get('font-size', 10.0))
            anchor = elem.attrib.get('text-anchor', 'start')
            rot = elem.attrib.get('transform', '')
            w = len(txt) * fs * 0.6
            if anchor == 'middle':
                x0 = x - w / 2.0
            elif anchor == 'end':
                x0 = x - w
            else:
                x0 = x
            x1 = x0 + w
            y0 = y - fs * 0.85
            y1 = y + fs * 0.15
            is_rot = 'rotate' in rot
            res.append({
                'id': elem.attrib.get('id', ''),
                'text': txt,
                'box': (x0, y0, x1, y1),
                'rot': is_rot,
                'fs': fs
            })
    for child in elem:
        res.extend(get_texts_bounding_boxes(child, cur_tx, cur_ty))
    return res

def check_overlaps(texts):
    overlaps = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            t1, t2 = texts[i], texts[j]
            if t1['rot'] or t2['rot']:
                continue
            b1, b2 = t1['box'], t2['box']
            if (b1[0] < b2[2] and b1[2] > b2[0] and b1[1] < b2[3] and b1[3] > b2[1]):
                overlaps.append((t1, t2))
    return overlaps

@pytest.mark.parametrize("h", [950, 380])
@pytest.mark.parametrize("estilo, nom_estilo", [
    (IMPRESION, "impresion"),
    (PANTALLA_OSCURO, "oscuro"),
    (PANTALLA_CLARO, "claro"),
])
def test_ausencia_traslapes_todos_los_textos(h, estilo, nom_estilo):
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(h, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    res = calc.calcular(inp)
    perf = perfil_armado(inp, res, mostrar_picos_al_borde=True)
    esq = EsquemaDiseno('repeticion', 5)

    svgs = {
        'conjunto': svg_conjunto(res, inp, estilo=estilo),
        'perfil': svg_perfil(perf, estilo=estilo),
        'hoja_sup': svg_hoja(res, inp, 'superior', esq, hoja='carta', estilo=estilo),
        'hoja_pic': svg_hoja(res, inp, 'pico', esq, hoja='carta', estilo=estilo),
        'hoja_inf': svg_hoja(res, inp, 'inferior', esq, hoja='carta', estilo=estilo),
        'pieza_sup': svg_pieza(res, inp, 'superior', estilo=estilo),
        'pieza_pic': svg_pieza(res, inp, 'pico', estilo=estilo),
        'pieza_inf': svg_pieza(res, inp, 'inferior', estilo=estilo),
    }

    for nom_svg, svg_content in svgs.items():
        root = ET.fromstring(svg_content)
        texts = get_texts_bounding_boxes(root)
        overlaps = check_overlaps(texts)
        assert len(overlaps) == 0, (
            f"Traslape detectado en {nom_svg} con h={h} y estilo {nom_estilo}: {overlaps}"
        )
