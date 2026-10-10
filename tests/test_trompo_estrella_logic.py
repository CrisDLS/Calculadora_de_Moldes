"""Pruebas de la calculadora real (logic/calculators/trompo_estrella.py):
valores canónicos, modo simple vs avanzado, paridad con la referencia, casos no viables
y entradas inválidas."""
import pytest

from logic.models import BalloonInput, Condiciones
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from referencia import trompo_estrella as ref

TOL = 1e-6


def calcular(altura=950, gajos=30, hileras=2, costura=1, avanzado=False, **kw):
    e = BalloonInput(altura, gajos, hileras, costura, usar_parametros_avanzados=avanzado, **kw)
    return TrompoEstrellaCalculator().calcular(e)


# ---------------------------------------------------------------- canónicos
def test_valores_canonicos_modo_avanzado():
    r = calcular(avanzado=True)
    s, p, i = r.seccion_superior, r.seccion_picos, r.seccion_inferior
    assert r.ancho_max_gajo == pytest.approx(63.6696, abs=1e-4)
    assert s.generatriz_total == pytest.approx(353.7441, abs=1e-4)
    assert s.puntos[1].largo_segmento == pytest.approx(22.1090, abs=1e-4)
    assert s.puntos[0].ancho_medio == pytest.approx(0.5)
    assert s.puntos[-1].ancho_medio == pytest.approx(32.3348, abs=1e-4)
    assert len(s.puntos) == 17
    assert p.generatriz_total == pytest.approx(76.4035, abs=1e-4)
    assert len(p.puntos) == 12
    assert i.generatriz_total == pytest.approx(468.9166, abs=1e-4)
    assert len(i.puntos) == 25
    assert i.puntos[0].ancho_medio == pytest.approx(5.9716, abs=1e-4)
    assert i.puntos[-1].ancho_medio == pytest.approx(32.3348, abs=1e-4)
    assert i.pestana == 4.0
    assert r.diametro_boquilla_calculado == pytest.approx(104.5)
    assert r.boca.diametro == pytest.approx(104.5)
    assert (r.gajos_min_70cm, r.gajos_min_50cm) == (28, 40)
    assert r.altura_total_real == pytest.approx(703.8, abs=0.1)
    assert r.vuelo.empuje_g / 1000 == pytest.approx(15.2, abs=0.05)
    assert r.viable is True


# ------------------------------------------------------------ simple/avanzado
def test_modo_simple_reglas():
    r = calcular()
    assert r.boca is None and r.vuelo is None and r.viable is None
    assert r.seccion_inferior.pestana == 0.0
    assert r.diametro_boquilla_calculado == pytest.approx(104.5)
    assert r.circumferencia_boquilla == pytest.approx(3.141592653589793 * 104.5)
    assert r.area_total_m2 > 0
    assert (r.gajos_min_70cm, r.gajos_min_50cm) == (28, 40)
    assert r.avisos == [TrompoEstrellaCalculator.AVISO_MODO_SIMPLE]
    assert r.avisos[0].startswith("Modo simple: solo geometría. Activa parámetros avanzados")


def test_modo_simple_aviso_geometrico_gajo_ancho():
    r = calcular(altura=950, gajos=20)       # gajo ~95 cm > 70
    assert len(r.avisos) == 2
    assert r.avisos[0].startswith("AVISO: gajo de")
    assert r.avisos[1] == TrompoEstrellaCalculator.AVISO_MODO_SIMPLE
    assert r.viable is None


def test_modo_simple_ignora_parametros_avanzados():
    base = calcular()
    r = calcular(diametro_boca=200, pestana_boca=9, diametro_mecha=80, masa_mecha_g=5000,
                 holgura_min=50, alambre_mm=9, varillas=9, altura_llama=1)
    assert r.diametro_boquilla_calculado == pytest.approx(104.5)
    assert r.seccion_inferior.pestana == 0.0 and r.boca is None and r.vuelo is None
    assert r.area_total_m2 == pytest.approx(base.area_total_m2)
    assert r.avisos == base.avisos


def test_modo_simple_no_valida_parametros_avanzados():
    calcular(pestana_boca=-5, diametro_boca=-1)      # ignorados en modo simple


def test_piezas_identicas_en_ambos_modos_salvo_pestana():
    s, a = calcular(avanzado=False), calcular(avanzado=True)
    for ps, pa in ((s.seccion_superior, a.seccion_superior), (s.seccion_picos, a.seccion_picos),
                   (s.seccion_inferior, a.seccion_inferior)):
        assert ps.generatriz_total == pytest.approx(pa.generatriz_total)
        assert [(q.largo_segmento, q.largo_acumulado, q.ancho_medio) for q in ps.puntos] == \
               pytest.approx([(q.largo_segmento, q.largo_acumulado, q.ancho_medio) for q in pa.puntos])
    assert s.seccion_inferior.pestana == 0.0 and a.seccion_inferior.pestana == 4.0
    assert a.area_total_m2 > s.area_total_m2           # la pestaña suma papel


def test_modo_avanzado_completo():
    r = calcular(avanzado=True, diametro_boca=120, diametro_mecha=60, masa_mecha_g=500)
    assert r.boca.diametro == 120 and r.boca.diametro_mecha == 60
    assert r.boca.holgura == pytest.approx(30.0) and r.boca.holgura_ok is True
    assert r.boca.diametro_minimo == pytest.approx(80.0)
    assert r.boca.pestana == 4.0
    assert r.vuelo.pliegos > 0 and r.vuelo.carga_neta_g < r.vuelo.carga_libre_g
    assert r.viable is True and r.avisos[-1].startswith(("OK", "AVISO"))


def test_condiciones_personalizadas_cambian_empuje():
    e = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True)
    base = TrompoEstrellaCalculator().calcular(e)
    caliente = TrompoEstrellaCalculator(Condiciones(t_interior=90.0)).calcular(e)
    assert caliente.vuelo.empuje_g > base.vuelo.empuje_g


# ------------------------------------------------------ paridad con referencia
CASOS = [
    (950, 30, 2, 1.0, None),
    (380, 30, 2, 1.0, 380 * 0.14),
    (500, 36, 3, 1.5, None),
    (1200, 44, 2, 1.0, None),
    (190, 30, 2, 1.0, None),            # no viable
]


def _piezas_ref(rr):
    return (rr.superior, rr.pico, rr.inferior)


def _piezas_nueva(r):
    return (r.seccion_superior, r.seccion_picos, r.seccion_inferior)


def _comparar_tablas(r, rr):
    for pn, pr in zip(_piezas_nueva(r), _piezas_ref(rr)):
        assert pn.generatriz_total == pytest.approx(pr.largo, abs=TOL)
        assert len(pn.puntos) == len(pr.puntos)
        for qn, qr in zip(pn.puntos, pr.puntos):
            assert qn.paso_numero == qr.paso
            assert qn.largo_segmento == pytest.approx(qr.largo, abs=TOL)
            assert qn.largo_acumulado == pytest.approx(qr.acumulado, abs=TOL)
            assert qn.ancho_medio == pytest.approx(qr.ancho_mitad, abs=TOL)
        assert pn.area_cm2 == pytest.approx(pr.area(), abs=1e-4)
    assert r.seccion_inferior.pestana == pytest.approx(rr.inferior.pestana)


@pytest.mark.parametrize("altura,gajos,hileras,costura,boca", CASOS)
def test_paridad_modo_avanzado(altura, gajos, hileras, costura, boca):
    rr = ref.calcular(ref.Entrada(altura, gajos, hileras, costura, diametro_boca=boca))
    r = calcular(altura, gajos, hileras, costura, avanzado=True, diametro_boca=boca)
    _comparar_tablas(r, rr)
    assert r.ancho_max_gajo == pytest.approx(rr.ancho_gajo, abs=TOL)
    assert r.diametro_globo == pytest.approx(rr.diametro_max, abs=TOL)
    assert r.area_total_m2 == pytest.approx(rr.area_total_m2, abs=1e-6)
    assert (r.gajos_min_70cm, r.gajos_min_50cm) == (rr.gajos_min_70cm, rr.gajos_min_50cm)
    assert r.altura_total_real == pytest.approx(rr.altura_armada_estimada, abs=1e-6)
    assert r.boca.diametro == pytest.approx(rr.boca.diametro, abs=TOL)
    assert r.boca.holgura == pytest.approx(rr.boca.holgura_plano_boca, abs=TOL)
    assert r.boca.holgura_ok == rr.boca.holgura_ok
    assert r.boca.diametro_minimo == pytest.approx(rr.boca.diametro_minimo, abs=TOL)
    assert r.boca.radio_pared_a_llama == pytest.approx(rr.boca.radio_pared_a_llama, abs=TOL)
    v, vr = r.vuelo, rr.vuelo
    assert v.volumen_m3 == pytest.approx(vr.volumen_m3, rel=1e-9)
    assert v.empuje_g == pytest.approx(vr.empuje_g, rel=1e-9)
    assert v.masa_papel_g == pytest.approx(vr.masa_papel_g, rel=1e-9)
    assert v.masa_estructura_g == pytest.approx(vr.masa_estructura_g, rel=1e-9)
    assert v.carga_neta_g == pytest.approx(vr.carga_neta_g, rel=1e-9)
    assert v.pliegos == pytest.approx(vr.pliegos, rel=1e-9)
    assert r.viable == rr.viable
    # mismas etiquetas (OK/AVISO/ERROR) en los avisos
    assert [a.split(":")[0] for a in r.avisos] == [a.split(":")[0] for a in rr.avisos]


@pytest.mark.parametrize("altura,gajos,hileras,costura,boca", CASOS)
def test_paridad_modo_simple(altura, gajos, hileras, costura, boca):
    """Simple = referencia con boca por defecto y pestaña 0 (la boca pedida se ignora)."""
    rr = ref.calcular(ref.Entrada(altura, gajos, hileras, costura, pestana_boca=0.0))
    r = calcular(altura, gajos, hileras, costura, avanzado=False, diametro_boca=boca)
    _comparar_tablas(r, rr)
    assert r.area_total_m2 == pytest.approx(rr.area_total_m2, abs=1e-6)
    assert r.diametro_boquilla_calculado == pytest.approx(rr.boca.diametro, abs=TOL)
    assert r.boca is None and r.vuelo is None and r.viable is None


# --------------------------------------------------------------- no viables
def test_no_viable_190cm():
    r = calcular(altura=190, avanzado=True)
    assert r.viable is False
    assert any(a.startswith("ERROR") for a in r.avisos)


def test_no_viable_boca_pequena():
    r = calcular(avanzado=True, diametro_boca=60, diametro_mecha=50)   # holgura 30-25 = 5 < 10
    assert r.viable is False
    assert r.boca.holgura_ok is False
    assert any("holgura" in a for a in r.avisos)


def test_no_viable_mecha_muy_pesada():
    r = calcular(avanzado=True, masa_mecha_g=50_000)
    assert r.viable is False
    assert any("mecha pesa" in a for a in r.avisos)


def test_380_viable_con_boca_ancha():
    assert calcular(380, avanzado=True, diametro_boca=380 * 0.14).viable is True


# ---------------------------------------------------------------- inválidas
@pytest.mark.parametrize("kw", [
    dict(altura=0), dict(altura=-10), dict(gajos=2), dict(hileras=-1), dict(costura=-1),
    dict(hileras=30),                                   # picos se comen todo el largo
])
def test_entradas_invalidas_ambos_modos(kw):
    for avanzado in (False, True):
        with pytest.raises(ValueError):
            calcular(avanzado=avanzado, **kw)


@pytest.mark.parametrize("kw", [
    dict(diametro_boca=700),        # boca > diámetro máximo (608)
    dict(diametro_boca=0), dict(diametro_boca=-5),
    dict(pestana_boca=-1), dict(diametro_mecha=0), dict(masa_mecha_g=-1),
    dict(holgura_min=-1), dict(alambre_mm=0), dict(varillas=-1),
])
def test_entradas_invalidas_modo_avanzado(kw):
    with pytest.raises(ValueError):
        calcular(avanzado=True, **kw)


def test_mensajes_claros():
    with pytest.raises(ValueError, match="altura"):
        calcular(altura=0)
    with pytest.raises(ValueError, match="boca"):
        calcular(avanzado=True, diametro_boca=700)
