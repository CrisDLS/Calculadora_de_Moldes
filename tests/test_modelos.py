"""Pruebas de logic/models.py: valores por defecto y retrocompatibilidad."""
from logic.models import (
    BalloonInput, BalloonCalculationResult, SectionResult, Point2D,
    Condiciones, BocaResult, VueloResult,
)


def _seccion(nombre="x"):
    return SectionResult(nombre, [Point2D(1, 0.0, 0.0, 0.5)], 10.0, 11.0, 0.0, 5.0)


def test_input_valores_por_defecto():
    e = BalloonInput(altura_cuerpo=950, num_gajos=30, num_hileras_picos=2, ancho_costura=1)
    assert e.usar_parametros_avanzados is False
    assert e.diametro_boca is None
    assert e.pestana_boca == 4.0
    assert e.diametro_mecha is None
    assert e.masa_mecha_g is None
    assert e.altura_llama == 40.0
    assert e.holgura_min == 10.0
    assert e.alambre_mm == 2.0
    assert e.varillas == 4


def test_input_estilo_viejo_por_posicion():
    e = BalloonInput(950.0, 30, 2, 1.0)
    assert e.altura_cuerpo == 950.0 and e.num_gajos == 30


def test_condiciones_por_defecto():
    c = Condiciones()
    assert (c.papel_gm2, c.extra_pegamento) == (20.0, 0.20)
    assert (c.t_ambiente, c.t_interior, c.presion_pa) == (28.0, 70.0, 101325.0)
    assert c.desperdicio == 0.15
    assert c.pliego_cm == (50.0, 75.0)


def test_section_result_campos_nuevos_por_defecto():
    s = _seccion()
    assert s.pestana == 0.0
    assert s.area_cm2 == 0.0


def test_resultado_a_la_manera_vieja():
    r = BalloonCalculationResult(
        altura_cuerpo_base=1.0, altura_picos=2.0, altura_total_real=3.0,
        diametro_globo=4.0, ancho_max_gajo=5.0,
        diametro_boquilla_calculado=6.0, circumferencia_boquilla=7.0,
        seccion_superior=_seccion("a"), seccion_picos=_seccion("b"),
        seccion_inferior=_seccion("c"),
    )
    assert r.boca is None
    assert r.vuelo is None
    assert r.viable is None          # None = no evaluado
    assert r.avisos == []
    assert r.gajos_min_70cm == 0 and r.gajos_min_50cm == 0
    assert r.area_total_m2 == 0.0


def test_avisos_no_se_comparten_entre_instancias():
    kw = dict(altura_cuerpo_base=1, altura_picos=1, altura_total_real=1, diametro_globo=1,
              ancho_max_gajo=1, diametro_boquilla_calculado=1, circumferencia_boquilla=1,
              seccion_superior=_seccion(), seccion_picos=_seccion(), seccion_inferior=_seccion())
    a, b = BalloonCalculationResult(**kw), BalloonCalculationResult(**kw)
    a.avisos.append("x")
    assert b.avisos == []


def test_boca_result():
    b = BocaResult(diametro=104.5, circunferencia_aro=328.3, ancho_por_gajo=10.9)
    assert b.diametro_mecha is None and b.holgura is None and b.holgura_ok is None
    assert b.diametro_minimo is None and b.radio_pared_a_llama is None and b.pestana == 0.0
    b2 = BocaResult(104.5, 328.3, 10.9, pestana=4.0, diametro_mecha=52.2, holgura=26.1,
                    holgura_ok=True, diametro_minimo=72.2, radio_pared_a_llama=77.7)
    assert b2.holgura_ok is True


def test_vuelo_result():
    v = VueloResult(volumen_m3=100.5, empuje_g=14400, masa_papel_g=2500,
                    masa_estructura_g=133, carga_libre_g=11900, carga_neta_g=11800,
                    pliegos=319)
    assert v.pliegos == 319 and v.carga_neta_g == 11800


def test_resultado_con_boca_y_vuelo():
    b = BocaResult(104.5, 328.3, 10.9)
    v = VueloResult(1, 2, 3, 4, 5, 6, 7)
    r = BalloonCalculationResult(1, 2, 3, 4, 5, 6, 7, _seccion(), _seccion(), _seccion(),
                                 boca=b, vuelo=v, viable=True)
    assert r.boca is b and r.vuelo is v and r.viable is True
