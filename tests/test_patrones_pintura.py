import pytest
import os
from logic.models import BalloonInput, Condiciones
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.pintura import EsquemaPintura, VariantePico, color_de_cara
from logic.diseno.compra import lista_de_compra
from logic.geometria.malla_trompo import Cara
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_patrones_cono_superior_e_inferior():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(ent)

    # Modo liso
    p_liso = EsquemaPintura(modo_superior="liso", colores_superior=["blanco"])
    colores_sup = [color_de_cara(p_liso, Cara([], "superior", k, None, None, [0, 0, 1], []), None, 30) for k in range(30)]
    assert all(c == "blanco" for c in colores_sup)

    # Modo alternado con 2 colores
    p_alt = EsquemaPintura(modo_superior="alternado", colores_superior=["rojo", "azul_rey"])
    colores_alt = [color_de_cara(p_alt, Cara([], "superior", k, None, None, [0, 0, 1], []), None, 30) for k in range(30)]
    assert colores_alt[0] == "rojo"
    assert colores_alt[1] == "azul_rey"
    assert colores_alt[2] == "rojo"

    # Modo bloques de 5 gajos
    p_bloques = EsquemaPintura(modo_superior="bloques", colores_superior=["verde_bandera", "amarillo"], tam_bloque_superior=5)
    colores_bloq = [color_de_cara(p_bloques, Cara([], "superior", k, None, None, [0, 0, 1], []), None, 30) for k in range(30)]
    assert all(c == "verde_bandera" for c in colores_bloq[0:5])
    assert all(c == "amarillo" for c in colores_bloq[5:10])
    assert all(c == "verde_bandera" for c in colores_bloq[10:15])

    # Inferior vinculado a superior
    p_vinc = EsquemaPintura(
        modo_superior="alternado",
        colores_superior=["rojo", "blanco"],
        mismo_esquema_inferior=True
    )
    colores_inf = [color_de_cara(p_vinc, Cara([], "inferior", k, None, None, [0, 0, -1], []), None, 30) for k in range(30)]
    assert colores_inf[0] == "rojo"
    assert colores_inf[1] == "blanco"

def test_patrones_picos_variantes_y_repeticiones():
    # Variante A: igual en las 4
    var_a = VariantePico(modo_caras="igual", color_0="amarillo")
    # Variante B: alternando 2
    var_b = VariantePico(modo_caras="alternado", color_0="rojo", color_1="negro")

    # Repetición ajedrez
    p = EsquemaPintura(
        variante_a=var_a,
        usar_variante_b=True,
        variante_b=var_b,
        repeticion_picos="ajedrez"
    )

    # k=0, j=0 -> (0+0)%2 == 0 -> Var A (igual) -> cara 0: amarillo, cara 1: amarillo
    c_00_0 = color_de_cara(p, Cara([], "pico", 0, 0, 0, [1, 0, 0], []), None, 20)
    c_00_1 = color_de_cara(p, Cara([], "pico", 0, 0, 1, [1, 0, 0], []), None, 20)
    assert c_00_0 == "amarillo"
    assert c_00_1 == "amarillo"

    # k=1, j=0 -> (1+0)%2 == 1 -> Var B (alternado) -> cara 0: rojo, cara 1: negro
    c_10_0 = color_de_cara(p, Cara([], "pico", 1, 0, 0, [1, 0, 0], []), None, 20)
    c_10_1 = color_de_cara(p, Cara([], "pico", 1, 0, 1, [1, 0, 0], []), None, 20)
    assert c_10_0 == "rojo"
    assert c_10_1 == "negro"

    # k=1, j=1 -> (1+1)%2 == 0 -> Var A
    c_11_0 = color_de_cara(p, Cara([], "pico", 1, 1, 0, [1, 0, 0], []), None, 20)
    assert c_11_0 == "amarillo"

def test_lista_compra_suma_areas_exactas():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(ent)

    p = EsquemaPintura(
        modo_superior="alternado",
        colores_superior=["rojo", "blanco"],
        variante_a=VariantePico(modo_caras="cuatro", color_0="amarillo", color_1="azul_rey", color_2="verde_limon", color_3="naranja"),
        usar_variante_b=True,
        variante_b=VariantePico(modo_caras="igual", color_0="negro"),
        repeticion_picos="alternar_gajo"
    )

    items = lista_de_compra(ent, res, p)
    # Área total en m² sumando los items de compra
    area_compra_m2 = sum(it.area_m2 for it in items)

    # Área teórica calculada por la calculadora geométrica
    area_teorica_m2 = (
        30 * res.seccion_superior.area_cm2 +
        30 * 2 * 4 * res.seccion_picos.area_cm2 +
        30 * res.seccion_inferior.area_cm2
    ) / 10000.0

    assert pytest.approx(area_compra_m2, rel=1e-4) == area_teorica_m2

def test_guardar_y_restaurar_proyecto_con_patrones(tmp_path):
    ent = BalloonInput(950.0, 30, 2, 1.0)
    p = EsquemaPintura(
        modo_superior="bloques",
        colores_superior=["rojo", "azul_rey", "blanco"],
        tam_bloque_superior=3,
        mismo_esquema_inferior=True,
        variante_a=VariantePico(modo_caras="alternado", color_0="dorado", color_1="plata"),
        usar_variante_b=True,
        variante_b=VariantePico(modo_caras="igual", color_0="negro"),
        repeticion_picos="ajedrez"
    )

    proy = Proyecto(
        version=1,
        nombre="Test Patrones",
        entrada=ent,
        condiciones=Condiciones(),
        esquema=None,
        notas="Notas de prueba",
        pintura=p,
        pliegos_por_paquete=50
    )

    ruta = str(tmp_path / "proyecto_patron.json")
    guardar_proyecto(proy, ruta)

    cargado = cargar_proyecto(ruta)
    assert cargado.pliegos_por_paquete == 50
    assert cargado.pintura is not None
    assert cargado.pintura.modo_superior == "bloques"
    assert cargado.pintura.colores_superior == ["rojo", "azul_rey", "blanco"]
    assert cargado.pintura.tam_bloque_superior == 3
    assert cargado.pintura.mismo_esquema_inferior is True
    assert cargado.pintura.variante_a.modo_caras == "alternado"
    assert cargado.pintura.variante_a.color_0 == "dorado"
    assert cargado.pintura.usar_variante_b is True
    assert cargado.pintura.repeticion_picos == "ajedrez"
