import os
import re
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.svg_abanico import svg_abanico

def test_capas_inkscape_y_estructura():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0, usar_parametros_avanzados=True, pestana_boca=4.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("repeticion", 5)

    svg = svg_abanico(res, inp, "superior", esq, escala="auto", hoja="carta")

    # Verificar capas Inkscape
    assert 'inkscape:groupmode="layer"' in svg
    assert 'inkscape:label="papel"' in svg
    assert 'inkscape:label="cuadricula"' in svg
    assert 'inkscape:label="ejes"' in svg
    assert 'inkscape:label="aristas_comunes"' in svg
    assert 'inkscape:label="contorno"' in svg
    assert 'inkscape:label="costura"' in svg
    assert 'inkscape:label="rotulos"' in svg

    # Verificar que solo hay 2 costuras laterales
    lineas_costura = re.findall(r'id="costura-lateral-[^"]+"', svg)
    assert len(lineas_costura) == 2
    assert 'id="costura-lateral-izq"' in lineas_costura
    assert 'id="costura-lateral-der"' in lineas_costura

def test_modo_mitad_vs_completo_conos():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("central_espejo", 5)

    svg_comp = svg_abanico(res, inp, "superior", esq, dibujar="completo")
    svg_mitad = svg_abanico(res, inp, "superior", esq, dibujar="mitad")

    # Completo debe tener 5 gajos rotulados
    gajos_comp = re.findall(r'Gajo \d+', svg_comp)
    assert len(gajos_comp) == 5

    # Mitad (5+1)//2 = 3 gajos rotulados
    gajos_mitad = re.findall(r'Gajo \d+', svg_mitad)
    assert len(gajos_mitad) == 3

def test_pico_hoja_una_cara_completo_y_mitad():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    svg_pico_comp = svg_abanico(res, inp, "pico", dibujar="completo")
    caras_comp = re.findall(r'Cara \d+', svg_pico_comp)
    assert len(caras_comp) == 1
    assert "Cara 1" in caras_comp
    assert 'id="eje-espejo-recto"' not in svg_pico_comp

    svg_pico_mitad = svg_abanico(res, inp, "pico", dibujar="mitad")
    caras_mitad = re.findall(r'Cara \d+', svg_pico_mitad)
    assert len(caras_mitad) == 1
    assert "Cara 1" in caras_mitad
    assert 'id="eje-espejo-recto"' in svg_pico_mitad

def test_escala_auto_cabe_en_carta_y_a4():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("repeticion", 5)

    for sec in ["superior", "inferior", "pico"]:
        svg_carta = svg_abanico(res, inp, sec, esq, escala="auto", hoja="carta", margen_mm=10.0)
        assert 'width="215.90mm"' in svg_carta or 'width="279.40mm"' in svg_carta

        svg_a4 = svg_abanico(res, inp, sec, esq, escala="auto", hoja="a4", margen_mm=10.0)
        assert 'width="210.00mm"' in svg_a4 or 'width="297.00mm"' in svg_a4

def test_generacion_ejemplos_docs():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0, usar_parametros_avanzados=True, pestana_boca=4.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("repeticion", 5)

    os.makedirs("docs/ejemplos", exist_ok=True)
    
    svg_sup = svg_abanico(res, inp, "superior", esq, escala="auto", hoja="carta")
    with open("docs/ejemplos/abanico_sup_carta.svg", "w", encoding="utf-8") as f:
        f.write(svg_sup)

    svg_pico = svg_abanico(res, inp, "pico", esq, escala="auto", hoja="carta")
    with open("docs/ejemplos/abanico_pico_carta.svg", "w", encoding="utf-8") as f:
        f.write(svg_pico)

    svg_inf = svg_abanico(res, inp, "inferior", esq, escala="auto", hoja="carta")
    with open("docs/ejemplos/abanico_inf_carta.svg", "w", encoding="utf-8") as f:
        f.write(svg_inf)

    assert os.path.exists("docs/ejemplos/abanico_sup_carta.svg")
    assert os.path.exists("docs/ejemplos/abanico_pico_carta.svg")
    assert os.path.exists("docs/ejemplos/abanico_inf_carta.svg")
