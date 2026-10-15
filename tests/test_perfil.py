import pytest
import math
import xml.etree.ElementTree as ET
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.malla_trompo import construir_malla
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_perfil import svg_perfil
from logic.exportacion.estilos import IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO
from tests.test_estilos import _ratio_contraste

@pytest.fixture
def casos_perfil():
    return [
        (BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=False), "950_simple"),
        (BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, diametro_boca=104.5, pestana_boca=4), "950_avanzado"),
        (BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=False), "380_simple"),
        (BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=True, diametro_boca=53.2, pestana_boca=4), "380_avanzado"),
    ]

def test_perfil_armado_propiedades_geometricas(casos_perfil):
    calc = TrompoEstrellaCalculator()
    for inp, nombre in casos_perfil:
        res = calc.calcular(inp)
        malla = construir_malla(inp, res)
        perf = perfil_armado(inp, res, mostrar_picos_al_borde=True)

        # 1. z máxima coincide con la de la malla
        z_apex_malla = malla.vertices[malla.anillos["apex"]][2]
        assert math.isclose(perf.dimensiones.alto_total, z_apex_malla, rel_tol=1e-5), f"Falla z max en {nombre}"

        # 2. La boca está en z=0 con semiancho Rb
        anillo_boca = perf.anillos[0]
        assert anillo_boca.nombre == "Boca"
        assert math.isclose(anillo_boca.z, 0.0, abs_tol=1e-5)
        # semiancho de la silueta cuando rotado pi/N
        assert math.isclose(anillo_boca.radio, malla.anillos["rb_boca"], rel_tol=1e-5)

        # 3. El número de anillos es hileras + 2 (boca, borde inferior de la banda y uno por hilera)
        assert len(perf.anillos) == inp.num_hileras_picos + 2, f"Falla num anillos en {nombre}"

        # 4. El ancho máximo con picos corresponde a 2 * (apotema + altura de pirámide) cuando N es par y mostrar_picos_al_borde=True
        if inp.num_gajos % 2 == 0:
            N = inp.num_gajos
            a = res.ancho_max_gajo
            l_pico = res.seccion_picos.generatriz_total
            h_p = math.sqrt(l_pico**2 - (a/2)**2)
            R_apo = malla.anillos["r_cuerpo"] * math.cos(math.pi / N)
            ancho_teorico = 2.0 * (R_apo + h_p)
            assert math.isclose(perf.dimensiones.ancho_con_picos, ancho_teorico, rel_tol=1e-4), f"Falla ancho con picos en {nombre}"

        # 5. Contorno simétrico
        assert len(perf.contorno_derecho) == len(perf.contorno_izquierdo)
        for (xd, zd), (xi, zi) in zip(perf.contorno_derecho, perf.contorno_izquierdo):
            assert math.isclose(xd, -xi, abs_tol=1e-5)
            assert math.isclose(zd, zi, abs_tol=1e-5)

        # 6. Con mostrar_picos_al_borde=False el ancho es menor o igual
        perf_sin_borde = perfil_armado(inp, res, mostrar_picos_al_borde=False)
        assert perf_sin_borde.dimensiones.ancho_con_picos <= perf.dimensiones.ancho_con_picos + 1e-4

def test_svg_perfil_validez_y_cotas(casos_perfil):
    calc = TrompoEstrellaCalculator()
    for inp, nombre in casos_perfil:
        res = calc.calcular(inp)
        perf = perfil_armado(inp, res)
        
        # Validar XML en los 3 estilos
        for estilo in [IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO]:
            svg = svg_perfil(perf, estilo=estilo)
            root = ET.fromstring(svg)
            assert root.tag.endswith("svg")
            assert "width" in root.attrib and "height" in root.attrib and "viewBox" in root.attrib

            # Cotas contienen los valores correctos
            assert f"Alto total: {perf.dimensiones.alto_total:.1f} cm" in svg
            assert f"Ø con picos: {perf.dimensiones.ancho_con_picos:.1f} cm" in svg
            assert f"Ø cuerpo: {perf.dimensiones.diametro_cuerpo:.1f} cm" in svg
            assert f"Ø boca: {perf.dimensiones.diametro_boca:.1f} cm" in svg
            assert "Medidas del polígono exacto" in svg
            assert "Perfil armado" in svg

def test_svg_perfil_wcag_contraste():
    nombres_a_hex = {
        "black": "#000000",
        "white": "#ffffff",
        "red": "#ff0000",
        "blue": "#0000ff",
        "green": "#00ff00",
    }

    for estilo in [IMPRESION, PANTALLA_OSCURO, PANTALLA_CLARO]:
        fondo = estilo.fondo or estilo.fondo_referencia
        txt_hex = nombres_a_hex.get(estilo.texto.lower(), estilo.texto)
        bg_hex = nombres_a_hex.get(fondo.lower(), fondo)
        r_texto = _ratio_contraste(txt_hex, bg_hex)
        assert r_texto >= 4.5, f"Texto en estilo {estilo} falla WCAG: ratio {r_texto:.2f} < 4.5"
