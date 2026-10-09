"""Pruebas de regresión: valores de referencia del Excel (950 / 30 gajos / 2 hileras / 1 cm)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator


def casi(a, b, tol=1e-3):
    assert abs(a - b) <= tol, f"{a} != {b}"


def calcular_ref(avanzado=True):
    return TrompoEstrellaCalculator().calcular(BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=avanzado))


def test_cono_superior():
    s = calcular_ref().seccion_superior
    assert len(s.puntos) == 17
    casi(s.generatriz_total, 353.7441)
    casi(s.puntos[1].largo_segmento, 22.1090)
    casi(s.puntos[0].ancho_medio, 0.5)
    casi(s.puntos[-1].ancho_medio, 32.3348)


def test_pico():
    p = calcular_ref().seccion_picos
    assert len(p.puntos) == 12
    casi(p.generatriz_total, 76.4035)
    casi(p.puntos[1].ancho_medio, 3.3941)


def test_cono_inferior():
    i = calcular_ref().seccion_inferior
    assert len(i.puntos) == 25
    casi(i.generatriz_total, 468.9166)
    casi(i.puntos[0].ancho_medio, 5.9716)      # el Excel da 5.99 (constantes fijas)
    casi(i.puntos[-1].ancho_medio, 32.3348)
    casi(i.pestana, 4.0)


def test_generales():
    r = calcular_ref()
    casi(r.ancho_max_gajo, 63.6696)
    casi(r.diametro_boquilla_calculado, 104.5)
    assert (r.gajos_min_70cm, r.gajos_min_50cm) == (28, 40)
    casi(r.altura_total_real, 703.8, 0.1)
    casi(r.vuelo.empuje_g / 1000, 14.4, 0.05)
    assert r.viable


def test_viabilidad_chica_no_viable():
    assert not TrompoEstrellaCalculator().calcular(BalloonInput(190, 30, 2, 1, usar_parametros_avanzados=True)).viable


def test_boca_ancha_arregla_380():
    r = TrompoEstrellaCalculator().calcular(BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=True, diametro_boca=380 * 0.14))
    assert r.viable


def test_modo_simple_no_usa_parametros_avanzados():
    """Simple = como el Excel: sin pestaña, sin mecha/empuje; los 3 moldes no cambian."""
    s, a = calcular_ref(False), calcular_ref(True)
    assert s.seccion_inferior.pestana == 0.0 and s.vuelo is None
    assert s.boca.holgura is None and s.viable
    casi(s.seccion_superior.generatriz_total, a.seccion_superior.generatriz_total)
    casi(s.seccion_inferior.puntos[0].ancho_medio, a.seccion_inferior.puntos[0].ancho_medio)
    assert any(x.startswith("INFO") for x in s.avisos)


def test_modo_simple_ignora_boca_personalizada():
    e = BalloonInput(950, 30, 2, 1, diametro_boca=200)      # usar_parametros_avanzados=False
    casi(TrompoEstrellaCalculator().calcular(e).boca.diametro, 104.5)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn(); print("OK", nombre)
