"""
Pruebas de correspondencia y texturizado 3D (logic/geometria/textura.py).
"""
import math
import defusedxml.ElementTree as ET
import pytest
from pathlib import Path

from logic.models import BalloonInput, BalloonCalculationResult
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.malla_trompo import construir_malla
from logic.geometria.abanico import pieza_a_geometria_plana, abanico
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.pintura import VariantePico
from logic.diseno.lienzo import Diseno, CapaDiseno
from logic.geometria.textura import (
    mapear_textura,
    mapear_vertice_a_abanico,
    uv_de_punto_cm,
    svg_textura,
    _obtener_n_abanico_cono,
    _obtener_n_caras_pico,
)
from logic.exportacion.escena3d import escena_a_dict


def _obtener_datos_prueba(N=30, hileras=2, ancho_costura=1.0):
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=N,
        num_hileras_picos=hileras,
        ancho_costura=ancho_costura,
    )
    calc = TrompoEstrellaCalculator()
    resultado = calc.calcular(entrada)
    malla = construir_malla(entrada, resultado)
    return entrada, resultado, malla


# -----------------------------------------------------------------------------
# 4a: Precisión matemática < 1e-9 cm en los vértices de cono
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("N,modo,tam_g", [
    (30, "repeticion", 5),
    (30, "central_espejo", 5),
    (30, "espejo_total", 6),
    (24, "repeticion", 4),
])
def test_4a_precision_vertices_cono(N, modo, tam_g):
    entrada, resultado, malla = _obtener_datos_prueba(N=N)
    esquema = EsquemaDiseno(modo=modo, tam_grupo=tam_g)
    configs = {
        "superior": ConfigSeccion(seccion="superior", esquema=esquema),
        "inferior": ConfigSeccion(seccion="inferior", esquema=esquema),
    }

    # Verificar para superior
    pz_sup = pieza_a_geometria_plana(resultado, entrada, "superior")
    ab_sup = abanico(pz_sup, n=tam_g, centrado=True)

    for c in malla.caras:
        if c.seccion == "superior":
            i_g = c.gajo % tam_g
            poly = ab_sup.poligonos[i_g]
            # En poly: [apex, p_der, p_izq] o similar
            # c.uv_cm tiene 3 puntos: [(-a/2, l), (a/2, l), (0, 0)]
            p_izq_ab = mapear_vertice_a_abanico(c.uv_cm[0], ab_sup, i_g)
            p_der_ab = mapear_vertice_a_abanico(c.uv_cm[1], ab_sup, i_g)
            p_apex_ab = mapear_vertice_a_abanico(c.uv_cm[2], ab_sup, i_g)

            # El vértice en el ápice debe ser exactamente (0, 0)
            assert math.hypot(p_apex_ab[0], p_apex_ab[1]) < 1e-12

            # Los vértices laterales deben coincidir con los vértices del polígono del abanico
            # poly para superior: pts_gajo = [(0, 0)] + [p_arco_der..p_arco_izq]
            # El primero en el arco es p_der, el último es p_izq
            p_der_poly = poly[1]
            p_izq_poly = poly[-1]
            err_der = math.hypot(p_der_ab[0] - p_der_poly[0], p_der_ab[1] - p_der_poly[1])
            err_izq = math.hypot(p_izq_ab[0] - p_izq_poly[0], p_izq_ab[1] - p_izq_poly[1])
            assert err_der < 1e-9, f"Error der {err_der} excede 1e-9"
            assert err_izq < 1e-9, f"Error izq {err_izq} excede 1e-9"

    # Verificar para inferior
    pz_inf = pieza_a_geometria_plana(resultado, entrada, "inferior")
    ab_inf = abanico(pz_inf, n=tam_g, centrado=True)

    for c in malla.caras:
        if c.seccion == "inferior":
            i_g = c.gajo % tam_g
            poly = ab_inf.poligonos[i_g]
            # c.uv_cm: [(-ab/2, 0), (ab/2, 0), (a/2, l_inf), (-a/2, l_inf)]
            # Correspondencia con poly:
            # poly[0] es arco estrecho izq (alpha_izq, s0) -> p_izq_boca
            # poly[pasos_arco] es arco estrecho der (alpha_der, s0) -> p_der_boca
            # poly[pasos_arco + 1] es arco ancho der (alpha_der, s1) -> p_der_ancho
            # poly[-1] es arco ancho izq (alpha_izq, s1) -> p_izq_ancho
            pts_ab = [mapear_vertice_a_abanico(pt, ab_inf, i_g) for pt in c.uv_cm]

            err_boca_izq = math.hypot(pts_ab[0][0] - poly[0][0], pts_ab[0][1] - poly[0][1])
            err_boca_der = math.hypot(pts_ab[1][0] - poly[8][0], pts_ab[1][1] - poly[8][1])
            err_ancho_der = math.hypot(pts_ab[2][0] - poly[9][0], pts_ab[2][1] - poly[9][1])
            err_ancho_izq = math.hypot(pts_ab[3][0] - poly[-1][0], pts_ab[3][1] - poly[-1][1])

            assert err_boca_izq < 1e-9
            assert err_boca_der < 1e-9
            assert err_ancho_der < 1e-9
            assert err_ancho_izq < 1e-9


# -----------------------------------------------------------------------------
# 4b: Continuidad entre gajos vecinos del grupo, salto entre grupos y periodicidad
# -----------------------------------------------------------------------------
def test_4b_continuidad_y_periodicidad_conos():
    entrada, resultado, malla = _obtener_datos_prueba(N=30)
    L = 5
    esquema = EsquemaDiseno(modo="repeticion", tam_grupo=L)
    configs = {
        "superior": ConfigSeccion(seccion="superior", esquema=esquema),
        "inferior": ConfigSeccion(seccion="inferior", esquema=esquema),
    }

    pz_sup = pieza_a_geometria_plana(resultado, entrada, "superior")
    ab_sup = abanico(pz_sup, n=L, centrado=True)
    caja_sup = (ab_sup.caja_min_x, ab_sup.caja_min_y, ab_sup.ancho_total, ab_sup.alto_total)

    caras_sup = [c for c in malla.caras if c.seccion == "superior"]

    # 1. Continuidad entre gajos i e i+1 dentro del mismo grupo (ej. g=0 y g=1)
    for g in range(L - 1):
        c_i = caras_sup[g]
        c_next = caras_sup[g + 1]

        # El borde derecho de c_i (vértice 1: (a/2, l_sup)) debe ser idéntico al borde
        # izquierdo de c_next (vértice 0: (-a/2, l_sup))
        p_der_i = mapear_vertice_a_abanico(c_i.uv_cm[1], ab_sup, c_i.gajo % L)
        p_izq_next = mapear_vertice_a_abanico(c_next.uv_cm[0], ab_sup, c_next.gajo % L)

        uv_der_i = uv_de_punto_cm(p_der_i[0], p_der_i[1], caja_sup)
        uv_izq_next = uv_de_punto_cm(p_izq_next[0], p_izq_next[1], caja_sup)

        err_cm = math.hypot(p_der_i[0] - p_izq_next[0], p_der_i[1] - p_izq_next[1])
        err_u = abs(uv_der_i[0] - uv_izq_next[0])
        err_v = abs(uv_der_i[1] - uv_izq_next[1])

        assert err_cm < 1e-9, f"Discontinuidad geométrica en gajo {g}: {err_cm}"
        assert err_u < 1e-9 and err_v < 1e-9

    # 2. Salto documentado en la frontera entre grupos (ej. g=4 y g=5)
    c_fin = caras_sup[L - 1]
    c_ini_sig = caras_sup[L]
    p_der_fin = mapear_vertice_a_abanico(c_fin.uv_cm[1], ab_sup, c_fin.gajo % L)
    p_izq_ini = mapear_vertice_a_abanico(c_ini_sig.uv_cm[0], ab_sup, c_ini_sig.gajo % L)

    salto_cm = math.hypot(p_der_fin[0] - p_izq_ini[0], p_der_fin[1] - p_izq_ini[1])
    assert salto_cm > 10.0, "Debe existir un salto entre el final de un grupo y el inicio del siguiente"

    # 3. Periodicidad g = g + L
    for g in range(len(caras_sup) - L):
        c_g = caras_sup[g]
        c_g_plus = caras_sup[g + L]
        p_g = [mapear_vertice_a_abanico(pt, ab_sup, c_g.gajo % L) for pt in c_g.uv_cm]
        p_g_plus = [mapear_vertice_a_abanico(pt, ab_sup, c_g_plus.gajo % L) for pt in c_g_plus.uv_cm]
        for p1, p2 in zip(p_g, p_g_plus):
            assert math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < 1e-12


# -----------------------------------------------------------------------------
# 4c: Continuidad en aristas compartidas de pirámides de picos
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("modo_caras,n_esperado", [
    ("igual", 1),
    ("alternado", 2),
    ("cuatro", 4),
])
def test_4c_continuidad_picos(modo_caras, n_esperado):
    entrada, resultado, malla = _obtener_datos_prueba()
    esq_pico = EsquemaDisenoPico(
        modo_repeticion="todas_a",
        variante_a=VariantePico(modo_caras=modo_caras),
    )
    pz_pic = pieza_a_geometria_plana(resultado, entrada, "pico")
    ab_pic = abanico(pz_pic, n=n_esperado, centrado=True)
    caja_pic = (ab_pic.caja_min_x, ab_pic.caja_min_y, ab_pic.ancho_total, ab_pic.alto_total)

    # Buscar caras de una misma pirámide (h=0, g=0)
    caras_piramide = [c for c in malla.caras if c.seccion == "pico" and c.hilera == 0 and c.gajo == 0]
    assert len(caras_piramide) == 4

    # En modo 'cuatro', las caras 0 y 1 son sub-caras adyacentes del abanico
    if modo_caras == "cuatro":
        c0 = caras_piramide[0]
        c1 = caras_piramide[1]
        p_der_c0 = mapear_vertice_a_abanico(c0.uv_cm[1], ab_pic, 0)
        p_izq_c1 = mapear_vertice_a_abanico(c1.uv_cm[0], ab_pic, 1)
        err = math.hypot(p_der_c0[0] - p_izq_c1[0], p_der_c0[1] - p_izq_c1[1])
        assert err < 1e-9

    # En todos los modos, el ápice de todas las caras (sub=0..3) mapea exactamente al vértice común
    for c in caras_piramide:
        p_apex = mapear_vertice_a_abanico(c.uv_cm[2], ab_pic, (c.sub or 0) % n_esperado)
        assert math.hypot(p_apex[0], p_apex[1]) < 1e-12


# -----------------------------------------------------------------------------
# 4d: Prueba del marcador (cuadrado rojo en un gajo específico)
# -----------------------------------------------------------------------------
def test_4d_marcador_cuadrado_rojo(tmp_path):
    entrada, resultado, malla = _obtener_datos_prueba(N=30)
    L = 5
    esquema = EsquemaDiseno(modo="repeticion", tam_grupo=L)
    cfg_sup = ConfigSeccion(seccion="superior", esquema=esquema)

    pz_sup = pieza_a_geometria_plana(resultado, entrada, "superior")
    ab_sup = abanico(pz_sup, n=L, centrado=True)
    caja_sup = (ab_sup.caja_min_x, ab_sup.caja_min_y, ab_sup.ancho_total, ab_sup.alto_total)

    # Crear una capa rectangular roja centrada sobre el eje del gajo 2
    # El eje del gajo 2 está en theta_2 = (2 - 2) * psi = 0.0 (en el centro del abanico)
    y_centro = pz_sup.radio_arco * 0.6
    ancho_marcador = 10.0
    alto_marcador = 10.0

    capa_roja = CapaDiseno(
        id="marcador_rojo",
        nombre="Rojo",
        tipo="svg",
        archivo="rojo.svg",
        ancho_natural=ancho_marcador,
        alto_natural=alto_marcador,
        x=-ancho_marcador / 2.0,
        y=y_centro - alto_marcador / 2.0,
        ancho=ancho_marcador,
        alto=alto_marcador,
    )
    diseno = Diseno(seccion="superior", capas=[capa_roja])

    # Guardar SVG del marcador
    archivo_svg = tmp_path / "rojo.svg"
    archivo_svg.write_text(
        '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="red"/></svg>',
        encoding="utf-8"
    )

    mapa = mapear_textura(
        entrada=entrada,
        resultado=resultado,
        malla=malla,
        configuraciones={"superior": cfg_sup},
        disenos={"superior": diseno},
        carpeta_recursos=tmp_path,
    )

    assert "superior" in mapa.texturas
    assert mapa.texturas["superior"].svg is not None

    # El centro del marcador está en (0.0, y_centro) en coordenadas del abanico
    u_centro, v_centro = uv_de_punto_cm(0.0, y_centro, caja_sup)

    # Verificar qué caras contienen este punto en su UV
    # Dado que gajo 2 está en theta=0, la cara con gajo % L == 2 debe contener este punto UV
    caras_sup = [c for c in malla.caras if c.seccion == "superior"]
    cara_g2 = [c for c in caras_sup if c.gajo % L == 2][0]

    # Vértices UV de esta cara
    uvs_g2 = [uv_de_punto_cm(*mapear_vertice_a_abanico(pt, ab_sup, 2), caja_sup) for pt in cara_g2.uv_cm]

    # Comprobar que u_centro está comprendido entre los límites u de la cara en v_centro
    u_min_cara = min(u for u, v in uvs_g2)
    u_max_cara = max(u for u, v in uvs_g2)
    v_min_cara = min(v for u, v in uvs_g2)
    v_max_cara = max(v for u, v in uvs_g2)

    assert v_min_cara <= v_centro <= v_max_cara
    assert u_min_cara <= u_centro <= u_max_cara


# -----------------------------------------------------------------------------
# 4e: Validación de svg_textura (XML válido, viewBox exacto, clipPath, mitad)
# -----------------------------------------------------------------------------
def test_4e_svg_textura_estructura_y_modo_mitad(tmp_path):
    entrada, resultado, malla = _obtener_datos_prueba(N=30)
    esquema = EsquemaDiseno(modo="central_espejo", tam_grupo=5)
    cfg_sup = ConfigSeccion(seccion="superior", esquema=esquema, dibujar="mitad")

    pz_sup = pieza_a_geometria_plana(resultado, entrada, "superior")
    ab_sup = abanico(pz_sup, n=5, centrado=True)

    # Capa que cruza el eje x=0
    capa = CapaDiseno(
        id="c1",
        nombre="Figura",
        tipo="svg",
        archivo="figura.svg",
        ancho_natural=20.0,
        alto_natural=20.0,
        x=-5.0,  # Cruza de x=-5 a x=+15
        y=ab_sup.caja_max_y * 0.5,
        ancho=20.0,
        alto=20.0,
    )
    diseno = Diseno(seccion="superior", capas=[capa])

    archivo_svg = tmp_path / "figura.svg"
    archivo_svg.write_text(
        '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" fill="blue"/></svg>',
        encoding="utf-8"
    )

    svg_str = svg_textura(
        clave="superior",
        entrada=entrada,
        resultado=resultado,
        diseno=diseno,
        config_seccion=cfg_sup,
        carpeta_recursos=tmp_path,
        max_px=1024,
    )

    # 1. XML válido sin errores de sintaxis
    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")

    # 2. ViewBox coincide con la caja envolvente del abanico
    vb = root.attrib.get("viewBox", "").split()
    assert len(vb) == 4
    vx, vy, vw, vh = [float(v) for v in vb]
    assert abs(vx - ab_sup.caja_min_x) < 1e-4
    assert abs(vy - (-ab_sup.caja_max_y)) < 1e-4
    assert abs(vw - ab_sup.ancho_total) < 1e-4
    assert abs(vh - ab_sup.alto_total) < 1e-4

    # 3. No tiene cuadrícula, rótulos ni papel
    assert "layer-cuadricula" not in svg_str
    assert "layer-rotulos" not in svg_str
    assert "layer-papel" not in svg_str

    # 4. En modo mitad, contiene clip-textura y clip-textura-reflejo
    assert "clip-textura" in svg_str
    assert "clip-textura-reflejo" in svg_str

    # 5. Sin referencias externas a http:// o https://
    assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", "").replace("http://www.w3.org/1999/xlink", "")
    assert "https://" not in svg_str


# -----------------------------------------------------------------------------
# 4e bis: Integración en escena_a_dict
# -----------------------------------------------------------------------------
def test_4e_escena_a_dict_compatibilidad_y_texturas(tmp_path):
    entrada, resultado, malla = _obtener_datos_prueba()

    # 1. Llamada sin diseños (retrocompatibilidad)
    escena_base = escena_a_dict(entrada, resultado)
    assert "texturas" in escena_base
    assert escena_base["texturas"] == {}
    for cara in escena_base["caras"]:
        assert cara.get("uv") is None
        assert cara.get("textura") is None

    # 2. Llamada con diseño
    capa = CapaDiseno(
        id="test",
        nombre="Test",
        tipo="svg",
        archivo="test.svg",
        ancho_natural=10.0,
        alto_natural=10.0,
        x=0.0,
        y=100.0,
        ancho=10.0,
        alto=10.0,
    )
    (tmp_path / "test.svg").write_text('<svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>', encoding="utf-8")
    disenos = {"superior": Diseno(seccion="superior", capas=[capa])}
    configs = {"superior": ConfigSeccion(seccion="superior")}

    escena_tex = escena_a_dict(
        entrada,
        resultado,
        configuraciones=configs,
        disenos=disenos,
        carpeta_recursos=tmp_path,
    )

    assert "superior" in escena_tex["texturas"]
    info_sup = escena_tex["texturas"]["superior"]
    assert "caja" in info_sup and len(info_sup["caja"]) == 4
    assert "px" in info_sup and len(info_sup["px"]) == 2
    assert "svg" in info_sup and len(info_sup["svg"]) > 50

    # Caras del cono superior deben tener UV y textura="superior"
    caras_sup = [c for c in escena_tex["caras"] if c["seccion"] == "superior"]
    for c in caras_sup:
        assert c["textura"] == "superior"
        assert c["uv"] is not None
        assert len(c["uv"]) == 3
        for u, v in c["uv"]:
            assert 0.0 <= u <= 1.0
            assert 0.0 <= v <= 1.0

    # Caras de cono inferior no tienen diseño visible -> textura=None
    caras_inf = [c for c in escena_tex["caras"] if c["seccion"] == "inferior"]
    for c in caras_inf:
        assert c["textura"] is None
