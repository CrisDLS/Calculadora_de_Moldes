import math
import pytest
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.abanico import pieza_a_geometria_plana, abanico

def test_abanico_cono_superior():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    geom = pieza_a_geometria_plana(res, inp, "superior")
    assert geom.distancia_vertice == 0.0
    assert geom.radio_arco == pytest.approx(353.74, abs=0.1)
    assert geom.ancho_mayor == pytest.approx(63.67, abs=0.1)
    # psi ~ 0.1795 - 0.1797 rad (~ 10.3 deg)
    assert geom.angulo_abertura_rad == pytest.approx(math.radians(10.3), abs=0.005)

    ab = abanico(geom, n=5, centrado=True)
    assert len(ab.poligonos) == 5
    assert len(ab.aristas_comunes) == 4
    assert len(ab.ejes) == 5

    # Ángulo total cubierto = 5 * psi ~ 51.5 deg
    angulo_total_deg = math.degrees(5 * geom.angulo_abertura_rad)
    assert angulo_total_deg == pytest.approx(51.5, abs=0.5)

    assert ab.ancho_total > 0
    assert ab.alto_total > 0
    # Bounding box centrado en X
    assert (ab.caja_min_x + ab.caja_max_x) == pytest.approx(0.0, abs=1e-5)

def test_abanico_cono_inferior():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    geom = pieza_a_geometria_plana(res, inp, "inferior")
    assert geom.largo == pytest.approx(468.92, abs=0.1)
    assert geom.ancho_mayor == pytest.approx(63.67, abs=0.1)
    assert geom.ancho_menor == pytest.approx(10.94, abs=0.1)

    # s0 ~ 97.3 cm, s1 ~ 566.2 cm
    assert geom.distancia_vertice == pytest.approx(97.3, abs=0.2)
    assert geom.radio_arco == pytest.approx(566.2, abs=0.3)
    # psi ~ 0.1124 rad (~ 6.44 deg)
    assert geom.angulo_abertura_rad == pytest.approx(0.1124, abs=0.002)
    assert math.degrees(geom.angulo_abertura_rad) == pytest.approx(6.44, abs=0.1)

    ab = abanico(geom, n=4, centrado=True)
    assert len(ab.poligonos) == 4
    assert len(ab.aristas_comunes) == 3
    assert len(ab.ejes) == 4
    assert ab.ancho_total > 0
    assert ab.alto_total > 0

def test_abanico_pico_4_caras():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    geom = pieza_a_geometria_plana(res, inp, "pico")
    assert geom.distancia_vertice == 0.0
    assert geom.radio_arco == pytest.approx(76.40, abs=0.1)
    assert geom.ancho_mayor == pytest.approx(63.67, abs=0.1)
    # psi ~ 0.7897 rad (~ 45.24 deg)
    assert geom.angulo_abertura_rad == pytest.approx(0.7897, abs=0.005)
    psi_deg = math.degrees(geom.angulo_abertura_rad)
    assert psi_deg == pytest.approx(45.24, abs=0.1)

    # 4 caras unidas cubren ~ 180.96 deg
    assert (4 * psi_deg) == pytest.approx(180.96, abs=0.5)

    ab = abanico(geom, n=4, centrado=True)
    assert len(ab.poligonos) == 4
    assert len(ab.aristas_comunes) == 3
    assert len(ab.ejes) == 4
    assert ab.ancho_total > 0
    assert ab.alto_total > 0

def test_conservacion_de_longitudes_sin_distorsion():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(380.0, 20, 1, 1.0)
    res = calc.calcular(inp)

    geom = pieza_a_geometria_plana(res, inp, "inferior")
    ab = abanico(geom, n=3, centrado=True)

    largo_esperado = geom.largo

    # Longitud de los ejes
    for (p0, p1) in ab.ejes:
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        assert dist == pytest.approx(largo_esperado, abs=1e-5)

    # Longitud de las aristas comunes
    for (p0, p1) in ab.aristas_comunes:
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        assert dist == pytest.approx(largo_esperado, abs=1e-5)
