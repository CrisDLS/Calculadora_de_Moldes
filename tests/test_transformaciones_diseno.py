import math
import pytest
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.abanico import (
    pieza_a_geometria_plana,
    abanico,
    Transformacion2D,
    reflejo_del_abanico,
    transformacion_a_gajo,
    recorte_gajo,
    gajos_equivalentes,
    construir_grupo,
)
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno

@pytest.fixture
def abanico_superior():
    calc = TrompoEstrellaCalculator()
    entrada = BalloonInput(950, 30, 2, 1)
    res = calc.calcular(entrada)
    pieza = pieza_a_geometria_plana(res, entrada, "superior")
    return abanico(pieza, n=5)

@pytest.fixture
def abanico_inferior():
    calc = TrompoEstrellaCalculator()
    entrada = BalloonInput(950, 30, 2, 1)
    res = calc.calcular(entrada)
    pieza = pieza_a_geometria_plana(res, entrada, "inferior")
    return abanico(pieza, n=4)

def test_transformacion_inversa_exactitud(abanico_superior):
    # Probar para cada gajo i en el abanico
    for i in range(abanico_superior.n):
        t = transformacion_a_gajo(abanico_superior, i)
        t_inv = t.inversa()

        # Tomar los puntos del polígono original del gajo i
        pts_originales = abanico_superior.poligonos[i]
        for p in pts_originales:
            # Llevar a coordenadas canónicas y luego de vuelta al abanico
            p_canon = t.transformar_punto(p)
            p_recuperado = t_inv.transformar_punto(p_canon)

            assert abs(p[0] - p_recuperado[0]) < 1e-9
            assert abs(p[1] - p_recuperado[1]) < 1e-9

def test_transformacion_inversa_inferior(abanico_inferior):
    for i in range(abanico_inferior.n):
        t = transformacion_a_gajo(abanico_inferior, i)
        t_inv = t.inversa()
        pts_originales = abanico_inferior.poligonos[i]
        for p in pts_originales:
            p_canon = t.transformar_punto(p)
            p_recuperado = t_inv.transformar_punto(p_canon)
            assert abs(p[0] - p_recuperado[0]) < 1e-9
            assert abs(p[1] - p_recuperado[1]) < 1e-9

def test_recorte_gajo_sin_sangrado_cobertura(abanico_superior):
    # Sin sangrado, los recortes deben coincidir exactamente con los polígonos del abanico
    for i in range(abanico_superior.n):
        poli_recorte = recorte_gajo(abanico_superior, i, margen_costura=1.0, sangrado=False)
        poli_original = abanico_superior.poligonos[i]
        assert len(poli_recorte) == len(poli_original)
        for (x1, y1), (x2, y2) in zip(poli_recorte, poli_original):
            assert abs(x1 - x2) < 1e-9
            assert abs(y1 - y2) < 1e-9

def test_recorte_gajo_con_sangrado_ensanchamiento(abanico_superior):
    # Con sangrado, el polígono debe ser más ancho que el original
    poli_sin = recorte_gajo(abanico_superior, 0, margen_costura=1.0, sangrado=False)
    poli_con = recorte_gajo(abanico_superior, 0, margen_costura=2.0, sangrado=True)

    ancho_sin = max(p[0] for p in poli_sin) - min(p[0] for p in poli_sin)
    ancho_con = max(p[0] for p in poli_con) - min(p[0] for p in poli_con)
    assert ancho_con > ancho_sin

def test_reflejo_del_abanico(abanico_superior):
    # Abanico centrado: reflejo en x=0 invierte x y conserva y
    t_ref = reflejo_del_abanico(abanico_superior)
    p = (15.5, 42.0)
    p_ref = t_ref.transformar_punto(p)
    assert pytest.approx(p_ref[0]) == -15.5
    assert pytest.approx(p_ref[1]) == 42.0

def test_gajos_equivalentes_modos():
    # Modo repetición N=20, G=5
    esq_rep = EsquemaDiseno("repeticion", 5)
    equiv_rep = gajos_equivalentes(esq_rep, 20)
    assert len(equiv_rep) == 20
    # Los motivos se repiten 0..4 cuatro veces
    assert [m for m, esp, k in equiv_rep[:5]] == [0, 1, 2, 3, 4]
    assert all(not esp for _, esp, _ in equiv_rep)

    # Modo central con espejo N=20, G=5 (impar) -> 1-2-3-2'-1' o ciclo con espejo
    esq_cen = EsquemaDiseno("central_espejo", 5)
    equiv_cen = gajos_equivalentes(esq_cen, 20)
    assert len(equiv_cen) == 20
    # Verifica que tiene espejos en los extremos
    motivos_grupo = [m for m, _, _ in equiv_cen[:5]]
    espejos_grupo = [esp for _, esp, _ in equiv_cen[:5]]
    assert True in espejos_grupo  # Hay al menos un espejo

    # Modo espejo total N=20, G=4 (par) -> 1-2-2'-1'
    esq_esp = EsquemaDiseno("espejo_total", 4)
    equiv_esp = gajos_equivalentes(esq_esp, 20)
    assert len(equiv_esp) == 20
    espejos_esp = [esp for _, esp, _ in equiv_esp[:4]]
    assert espejos_esp == [False, False, True, True]

    # Modo personalizado N=6, ciclo [(0, False), (1, True)]
    esq_pers = EsquemaDiseno("personalizado", 2, ciclo=[(0, False), (1, True)])
    equiv_pers = gajos_equivalentes(esq_pers, 6)
    assert len(equiv_pers) == 6
    assert [m for m, _, _ in equiv_pers] == [0, 1, 0, 1, 0, 1]
    assert [esp for _, esp, _ in equiv_pers] == [False, True, False, True, False, True]

def test_construir_grupo_mitad():
    capa = CapaDiseno(
        id="c1",
        nombre="Estrella",
        tipo="svg",
        archivo="est.svg",
        ancho_natural=10.0,
        alto_natural=10.0,
        x=5.0,
        y=20.0,
        ancho=10.0,
        alto=10.0,
        rotacion=15.0,
        reflejo_h=False,
    )
    diseno = Diseno(seccion="superior", capas=[capa])

    # En modo completo, no duplica
    grupo_comp = construir_grupo(diseno, modo_lienzo="completo")
    assert len(grupo_comp) == 1

    # En modo mitad, duplica con reflejo
    grupo_mitad = construir_grupo(diseno, modo_lienzo="mitad")
    assert len(grupo_mitad) == 2
    assert grupo_mitad[0].id == "c1"
    c_ref = grupo_mitad[1]
    assert c_ref.id == "c1_reflejo"
    assert c_ref.rotacion == -15.0
    assert c_ref.reflejo_h is True
    assert c_ref.y == 20.0
