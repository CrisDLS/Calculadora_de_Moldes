"""Regresión contra referencia/trompo_estrella.py con los valores canónicos de AGENTS.md
(950 cm / 30 gajos / 2 hileras / 1 cm de costura)."""
import pytest

from referencia import trompo_estrella as ref


@pytest.fixture(scope="module")
def res():
    return ref.calcular(ref.Entrada(altura=950, gajos=30, hileras_picos=2, costura=1))


def test_ancho_gajo(res):
    assert res.ancho_gajo == pytest.approx(63.6696, abs=1e-4)


def test_cono_superior(res):
    s = res.superior
    assert s.largo == pytest.approx(353.7441, abs=1e-4)
    assert s.puntos[1].largo == pytest.approx(22.1090, abs=1e-4)
    assert s.ancho_mitad_fin == pytest.approx(32.3348, abs=1e-4)
    assert len(s.puntos) == 17


def test_pico(res):
    assert res.pico.largo == pytest.approx(76.4035, abs=1e-4)
    assert len(res.pico.puntos) == 12


def test_cono_inferior(res):
    i = res.inferior
    assert i.largo == pytest.approx(468.9166, abs=1e-4)
    assert len(i.puntos) == 25
    assert i.ancho_mitad_inicio == pytest.approx(5.9716, abs=1e-4)


def test_boca_y_gajos_minimos(res):
    assert res.boca.diametro == pytest.approx(104.5, abs=1e-6)
    assert res.gajos_min_70cm == 28
    assert res.gajos_min_50cm == 40


def test_altura_armada_y_empuje(res):
    assert res.altura_armada_estimada == pytest.approx(704, abs=1)
    assert res.vuelo.empuje_g / 1000 == pytest.approx(15.2, abs=0.05)
