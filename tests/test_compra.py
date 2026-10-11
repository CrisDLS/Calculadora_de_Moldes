import pytest
from logic.models import BalloonInput, Condiciones
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura
from logic.diseno.compra import lista_de_compra
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_lista_de_compra_todas_piezas_y_colores():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    res = calc.calcular(inp)
    
    # 30 sup + 30 inf + 240 picos = 300 piezas
    pintura = EsquemaPintura(color_superior="blanco", color_pico="amarillo", color_inferior="rojo")
    items = lista_de_compra(inp, res, pintura)
    
    tot_piezas = sum(it.piezas_totales for it in items)
    assert tot_piezas == 300
    
    items_dict = {it.color.id: it for it in items}
    assert items_dict["blanco"].piezas_superior == 30
    assert items_dict["blanco"].piezas_totales == 30
    assert items_dict["amarillo"].piezas_pico == 240
    assert items_dict["amarillo"].piezas_totales == 240
    assert items_dict["rojo"].piezas_inferior == 30
    assert items_dict["rojo"].piezas_totales == 30

    # Área total debe coincidir con res.area_total_m2
    area_tot = sum(it.area_m2 for it in items)
    assert area_tot == pytest.approx(res.area_total_m2, abs=0.01)

    # Pliegos calculados individualmente
    for it in items:
        assert it.pliegos > 0
        assert isinstance(it.pliegos, int)

def test_lista_de_compra_con_motivos():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(380, 20, 1, 1, usar_parametros_avanzados=False)
    res = calc.calcular(inp)
    
    # 20 gajos, repetición 2: motivo 0 (10 gajos), motivo 1 (10 gajos)
    esq_diseno = EsquemaDiseno("repeticion", 2)
    pintura = EsquemaPintura(
        color_superior="blanco",
        color_pico="amarillo",
        color_inferior="blanco",
        colores_motivos={
            0: {"superior": "azul_rey", "pico": "negro"},
            1: {"superior": "blanco", "pico": "blanco"},
        }
    )
    items = lista_de_compra(inp, res, pintura, esq_diseno)
    items_dict = {it.color.id: it for it in items}

    # Motivo 0: 10 sup azul_rey, 10*4=40 picos negros
    assert items_dict["azul_rey"].piezas_superior == 10
    assert items_dict["negro"].piezas_pico == 40

def test_serializacion_proyecto_con_pintura(tmp_path):
    inp = BalloonInput(950, 30, 2, 1)
    cond = Condiciones()
    esq = EsquemaDiseno("repeticion", 5)
    pintura = EsquemaPintura(
        color_superior="rosa_mexicano",
        color_pico="verde_limon",
        color_inferior="negro",
        colores_caras_especificas={"superior_0": "dorado"}
    )
    p = Proyecto(1, "Globo Pintado", inp, cond, esq, "Prueba", pintura=pintura)
    ruta = tmp_path / "pintado.json"
    guardar_proyecto(p, str(ruta))

    p_cargado = cargar_proyecto(str(ruta))
    assert p_cargado.pintura is not None
    assert p_cargado.pintura.color_superior == "rosa_mexicano"
    assert p_cargado.pintura.color_pico == "verde_limon"
    assert p_cargado.pintura.color_inferior == "negro"
    assert p_cargado.pintura.colores_caras_especificas.get("superior_0") == "dorado"
