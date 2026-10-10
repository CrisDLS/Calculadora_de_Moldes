"""Pruebas del presentador (funciones puras, sin ventana)."""
import pytest

from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput
from ui.modulos_moldes.presentador_trompo_estrella import (
    clasificar_aviso, formatear_resumen, leer_entrada,
    ETIQUETAS_RESUMEN_SIMPLE, ETIQUETAS_RESUMEN_AVANZADO,
)

BASE = {"altura": "950", "gajos": "30", "hileras": "2", "costura": "1"}


def _calc(avanzado):
    e = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=avanzado)
    return TrompoEstrellaCalculator().calcular(e)


# ------------------------------------------------------------ leer_entrada
def test_leer_entrada_basica():
    e = leer_entrada(BASE, avanzado=False)
    assert (e.altura_cuerpo, e.num_gajos, e.num_hileras_picos, e.ancho_costura) == (950, 30, 2, 1)
    assert e.usar_parametros_avanzados is False
    assert isinstance(e.num_gajos, int)


def test_coma_decimal_y_espacios():
    e = leer_entrada({**BASE, "altura": " 950,5 ", "costura": "1 ,5"}, avanzado=False)
    assert e.altura_cuerpo == 950.5 and e.ancho_costura == 1.5


def test_gajos_como_decimal_entero_se_acepta():
    assert leer_entrada({**BASE, "gajos": "30,0"}, False).num_gajos == 30


@pytest.mark.parametrize("campo,valor,mensaje", [
    ("altura", "abc", "La altura debe ser un número"),
    ("altura", "", "La altura debe ser un número"),
    ("altura", "nan", "La altura debe ser un número"),
    ("altura", "inf", "La altura debe ser un número"),
    ("costura", "x", "La costura debe ser un número"),
    ("gajos", "30.5", "Los gajos deben ser un entero ≥ 3"),
    ("gajos", "abc", "Los gajos deben ser un entero ≥ 3"),
    ("gajos", "", "Los gajos deben ser un entero ≥ 3"),
    ("hileras", "1.5", "Las hileras deben ser un entero ≥ 0"),
    ("hileras", "", "Las hileras deben ser un entero ≥ 0"),
])
def test_entradas_invalidas(campo, valor, mensaje):
    with pytest.raises(ValueError) as exc:
        leer_entrada({**BASE, campo: valor}, avanzado=False)
    assert str(exc.value) == mensaje


def test_simple_ignora_y_no_valida_avanzados():
    basura = {"diametro_boca": "texto", "pestana_boca": "???", "varillas": "1.5",
              "masa_mecha_g": "abc", "alambre_mm": "x", "altura_llama": "y", "holgura_min": "z",
              "diametro_mecha": "q"}
    e = leer_entrada({**BASE, **basura}, avanzado=False)
    ref = BalloonInput(950, 30, 2, 1)
    assert e == ref


def test_avanzado_lee_campos():
    valores = {**BASE, "diametro_boca": "120,5", "pestana_boca": "5", "diametro_mecha": "60",
               "masa_mecha_g": "500", "alambre_mm": "3", "varillas": "6",
               "altura_llama": "35", "holgura_min": "12"}
    e = leer_entrada(valores, avanzado=True)
    assert e.usar_parametros_avanzados is True
    assert e.diametro_boca == 120.5 and e.pestana_boca == 5 and e.diametro_mecha == 60
    assert e.masa_mecha_g == 500 and e.alambre_mm == 3 and e.varillas == 6
    assert e.altura_llama == 35 and e.holgura_min == 12


def test_avanzado_vacios_usan_valores_por_defecto():
    e = leer_entrada({**BASE, "diametro_boca": "", "pestana_boca": "  ", "varillas": ""}, avanzado=True)
    ref = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True)
    assert e == ref
    assert e.diametro_boca is None and e.pestana_boca == 4.0 and e.varillas == 4


def test_avanzado_valida_campos_avanzados():
    with pytest.raises(ValueError, match="El diámetro de la boca debe ser un número"):
        leer_entrada({**BASE, "diametro_boca": "ancha"}, avanzado=True)
    with pytest.raises(ValueError, match="Las varillas deben ser un entero ≥ 0"):
        leer_entrada({**BASE, "varillas": "2.5"}, avanzado=True)
    with pytest.raises(ValueError, match="El peso de la mecha debe ser un número"):
        leer_entrada({**BASE, "masa_mecha_g": "pesada"}, avanzado=True)


def test_claves_faltantes_se_tratan_como_vacias():
    e = leer_entrada(BASE, avanzado=True)          # sin claves avanzadas en el dict
    assert e == BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True)


# -------------------------------------------------------- formatear_resumen
def test_resumen_simple_950():
    filas = dict(formatear_resumen(_calc(False)))
    assert tuple(filas) == ETIQUETAS_RESUMEN_SIMPLE
    assert filas["Diámetro del globo"] == "608.0 cm"
    assert filas["Ancho máx. de gajo"] == "63.67 cm"
    assert filas["Diámetro de la boca"] == "104.5 cm"
    assert filas["Circunferencia de la boca"] == "328.3 cm"
    assert filas["Gajos mín. (ancho ≤ 70 cm)"] == "28"
    assert filas["Gajos máx. (ancho ≤ 50 cm)"] == "40"
    assert filas["Altura armada estimada"] == "704 cm"
    assert filas["Área de papel"] == "103.8 m²"


def test_resumen_avanzado_950():
    filas = dict(formatear_resumen(_calc(True)))
    assert tuple(filas) == ETIQUETAS_RESUMEN_SIMPLE + ETIQUETAS_RESUMEN_AVANZADO
    assert filas["Diámetro de la boca"] == "104.5 cm"
    assert filas["Gajos mín. (ancho ≤ 70 cm)"] == "28"
    assert filas["Gajos máx. (ancho ≤ 50 cm)"] == "40"
    assert filas["Área de papel"] == "103.9 m²"            # con pestaña
    assert filas["Pestaña"] == "4.0 cm"
    assert filas["Diámetro de mecha"] == "52.2 cm"
    assert filas["Holgura mecha-papel"] == "26.1 cm"
    assert filas["Empuje"] == "14.4 kg"
    assert filas["Carga neta para la mecha"] == "11.8 kg"
    assert filas["Pliegos"] == "319"
    assert filas["Viable"] == "Sí"


def test_resumen_avanzado_no_viable():
    r = TrompoEstrellaCalculator().calcular(
        BalloonInput(190, 30, 2, 1, usar_parametros_avanzados=True))
    filas = dict(formatear_resumen(r))
    assert filas["Viable"] == "No"
    assert "insuficiente" in filas["Holgura mecha-papel"]


def test_resumen_simple_no_incluye_filas_avanzadas():
    etiquetas = [e for e, _ in formatear_resumen(_calc(False))]
    for avanzada in ETIQUETAS_RESUMEN_AVANZADO:
        assert avanzada not in etiquetas


# --------------------------------------------------------- clasificar_aviso
@pytest.mark.parametrize("texto,clase", [
    ("ERROR: holgura mecha→papel 5.0 cm < 10 cm.", "error"),
    ("AVISO: gajo de 95 cm (>70).", "aviso"),
    ("OK: medidas viables con los supuestos actuales.", "ok"),
    ("Modo simple: solo geometría. Activa parámetros avanzados para verificar viabilidad "
     "(holgura de mecha y empuje).", "info"),
    ("INFO: otra cosa", "info"),
    ("", "info"),
    ("  ERROR: con espacios", "error"),
])
def test_clasificar_aviso(texto, clase):
    assert clasificar_aviso(texto) == clase


def test_clasifica_avisos_reales_del_calculo():
    assert [clasificar_aviso(a) for a in _calc(False).avisos] == ["info"]
    assert [clasificar_aviso(a) for a in _calc(True).avisos] == ["ok"]
