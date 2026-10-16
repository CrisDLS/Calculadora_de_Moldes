"""Pruebas unitarias para logic/diseno/gestos_lienzo.py."""

import math
import pytest
from logic.diseno.lienzo import CapaDiseno
from logic.diseno.gestos_lienzo import (
    Conversion,
    centro_capa,
    esquinas_capa,
    tiradores,
    mover,
    estirar,
    rotar,
)
from logic.exportacion.vista_svg import VistaSvg, zoom, desplazar
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.exportacion.svg_abanico import svg_abanico


def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _dot(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


# ------------------------------------------------------------------------------
# 1. Conversión de ida y vuelta plano <-> px con error < 1e-9
# ------------------------------------------------------------------------------


def test_conversion_ida_vuelta_precision_directa():
    """Verifica que plano_a_px y px_a_plano son biyecciones con error < 1e-9."""
    vista = VistaSvg(x=-50.0, y=-20.0, ancho=200.0, alto=150.0)
    zona_px = (1024.0, 768.0)

    for y_arriba in (True, False):
        conv = Conversion(vista=vista, zona_px=zona_px, y_arriba=y_arriba)

        puntos_prueba = [
            (0.0, 0.0),
            (-50.0, -20.0),
            (150.0, 130.0),
            (12.345678, 98.765432),
            (-33.333333, 45.678901),
            (0.0001, -0.0002),
        ]

        for x, y in puntos_prueba:
            px, py = conv.plano_a_px(x, y)
            x_rec, y_rec = conv.px_a_plano(px, py)
            assert abs(x_rec - x) < 1e-9, f"Error en X con y_arriba={y_arriba}: {abs(x_rec - x)}"
            assert abs(y_rec - y) < 1e-9, f"Error en Y con y_arriba={y_arriba}: {abs(y_rec - y)}"

        # Puntos en píxeles hacia plano y de vuelta
        pixeles_prueba = [
            (0.0, 0.0),
            (512.0, 384.0),
            (1024.0, 768.0),
            (123.45, 678.90),
        ]
        for px, py in pixeles_prueba:
            x_plano, y_plano = conv.px_a_plano(px, py)
            px_rec, py_rec = conv.plano_a_px(x_plano, y_plano)
            assert abs(px_rec - px) < 1e-9
            assert abs(py_rec - py) < 1e-9


def test_conversion_ida_vuelta_con_transformacion_hoja():
    """Verifica la precisión con escala mm/cm y traslación de hoja de trazo."""
    vista = VistaSvg(x=0.0, y=0.0, ancho=215.9, alto=279.4)
    zona_px = (800.0, 600.0)
    conv = Conversion(
        vista=vista,
        zona_px=zona_px,
        y_arriba=True,
        factor_escala=0.5,  # mm por cm (escala 1:20 -> 0.5 mm/cm)
        cx_vista=107.95,
        cy_vista=139.7,
        y_mid_plano=50.0,
    )

    for x in (-30.0, 0.0, 30.0):
        for y in (10.0, 50.0, 90.0):
            px, py = conv.plano_a_px(x, y)
            x_rec, y_rec = conv.px_a_plano(px, py)
            assert abs(x_rec - x) < 1e-9
            assert abs(y_rec - y) < 1e-9


# ------------------------------------------------------------------------------
# 2. Preservación del punto bajo el cursor al hacer zoom/desplazar
# ------------------------------------------------------------------------------


def test_preservacion_punto_cursor_zoom():
    """Al aplicar zoom con centro en el cursor, el punto del plano bajo él no cambia."""
    vista_orig = VistaSvg(x=10.0, y=20.0, ancho=200.0, alto=200.0)
    zona_px = (800.0, 800.0)
    conv1 = Conversion(vista=vista_orig, zona_px=zona_px, y_arriba=True)

    # Cursor del usuario en pantalla
    cursor_px = (450.0, 350.0)
    pt_plano = conv1.px_a_plano(cursor_px[0], cursor_px[1])

    # Fracción respecto a la vista
    xs, ys = conv1.plano_a_vista(pt_plano[0], pt_plano[1])
    fx = (xs - vista_orig.x) / vista_orig.ancho
    fy = (ys - vista_orig.y) / vista_orig.alto

    # Aplicar zoom
    vista_zoom = zoom(vista_orig, factor=2.0, fx=fx, fy=fy)
    conv2 = Conversion(vista=vista_zoom, zona_px=zona_px, y_arriba=True)

    # El punto del plano debe mapearse exactamente a la misma posición en pantalla
    px2, py2 = conv2.plano_a_px(pt_plano[0], pt_plano[1])
    assert abs(px2 - cursor_px[0]) < 1e-6
    assert abs(py2 - cursor_px[1]) < 1e-6


def test_preservacion_relativa_desplazar():
    """Al desplazar la vista en coordenadas de dibujo, la distancia en px refleja el delta."""
    vista_orig = VistaSvg(x=0.0, y=0.0, ancho=100.0, alto=100.0)
    zona_px = (500.0, 500.0)
    conv1 = Conversion(vista=vista_orig, zona_px=zona_px, y_arriba=True)

    pt = (25.0, 25.0)
    px1, py1 = conv1.plano_a_px(pt[0], pt[1])

    # Desplazar vista por (10, 5) unidades de vista
    vista_mov = desplazar(vista_orig, dx=10.0, dy=5.0)
    conv2 = Conversion(vista=vista_mov, zona_px=zona_px, y_arriba=True)
    px2, py2 = conv2.plano_a_px(pt[0], pt[1])

    # En pantalla el contenido se desplazó +dx y +dy píxeles
    dx_px_esperado = 10.0 * conv1.escala_visor
    dy_px_esperado = 5.0 * conv1.escala_visor
    assert abs((px2 - px1) - dx_px_esperado) < 1e-6
    assert abs((py2 - py1) - dy_px_esperado) < 1e-6


# ------------------------------------------------------------------------------
# 3. Las 4 esquinas y los 8 tiradores con rotación de 0°, 45°, 90°, 180° y reflejos
# ------------------------------------------------------------------------------


@pytest.mark.parametrize("angulo", [0.0, 45.0, 90.0, 180.0, -60.0])
@pytest.mark.parametrize("reflejo_h", [False, True])
@pytest.mark.parametrize("reflejo_v", [False, True])
def test_esquinas_y_tiradores_geometria(angulo, reflejo_h, reflejo_v):
    """Verifica dimensiones, ortogonalidad y coherencia de tiradores en cualquier rotación."""
    capa = CapaDiseno(
        id="c1",
        nombre="prueba",
        tipo="raster",
        archivo="img.png",
        ancho_natural=20.0,
        alto_natural=10.0,
        x=5.0,
        y=15.0,
        ancho=20.0,
        alto=10.0,
        rotacion=angulo,
        reflejo_h=reflejo_h,
        reflejo_v=reflejo_v,
    )

    cx, cy = centro_capa(capa)
    esq = esquinas_capa(capa)
    tl, tr, br, bl = esq["tl"], esq["tr"], esq["br"], esq["bl"]

    # 1. Distancias entre esquinas
    assert abs(_dist(tl, tr) - 20.0) < 1e-6
    assert abs(_dist(bl, br) - 20.0) < 1e-6
    assert abs(_dist(tl, bl) - 10.0) < 1e-6
    assert abs(_dist(tr, br) - 10.0) < 1e-6

    # 2. Ortogonalidad
    v_ancho = (tr[0] - tl[0], tr[1] - tl[1])
    v_alto = (tl[0] - bl[0], tl[1] - bl[1])
    assert abs(_dot(v_ancho, v_alto)) < 1e-6

    # 3. Centro medio
    cx_medio = (tl[0] + tr[0] + br[0] + bl[0]) / 4.0
    cy_medio = (tl[1] + tr[1] + br[1] + bl[1]) / 4.0
    assert abs(cx_medio - cx) < 1e-6
    assert abs(cy_medio - cy) < 1e-6

    # 4. Tiradores
    tirs = tiradores(capa, incluir_rotacion=True, dist_rot_cm=3.0)
    assert set(tirs.keys()) == {"tl", "tr", "br", "bl", "t", "b", "r", "l", "rot"}

    # Los tiradores de lado deben ser puntos medios exactos
    t, b, r, l = tirs["t"], tirs["b"], tirs["r"], tirs["l"]
    assert abs(t[0] - (tl[0] + tr[0]) / 2.0) < 1e-6
    assert abs(t[1] - (tl[1] + tr[1]) / 2.0) < 1e-6
    assert abs(b[0] - (bl[0] + br[0]) / 2.0) < 1e-6
    assert abs(b[1] - (bl[1] + br[1]) / 2.0) < 1e-6
    assert abs(r[0] - (tr[0] + br[0]) / 2.0) < 1e-6
    assert abs(r[1] - (tr[1] + br[1]) / 2.0) < 1e-6
    assert abs(l[0] - (tl[0] + bl[0]) / 2.0) < 1e-6
    assert abs(l[1] - (tl[1] + bl[1]) / 2.0) < 1e-6

    # Tirador de rotación está a 3 cm de 't' en dirección hacia afuera
    assert abs(_dist(tirs["rot"], t) - 3.0) < 1e-6


# ------------------------------------------------------------------------------
# 4. Estirar desde cada uno de los 8 tiradores: invarianza del borde/esquina opuesta
# ------------------------------------------------------------------------------


@pytest.mark.parametrize("rotacion", [0.0, 30.0, 90.0])
@pytest.mark.parametrize("mantener_proporcion", [False, True])
def test_estirar_esquinas_invarianza_opuesta(rotacion, mantener_proporcion):
    """Verifica que al estirar cualquier esquina, la esquina opuesta permanece inmóvil."""
    capa_orig = CapaDiseno(
        id="c1",
        nombre="capa",
        tipo="raster",
        archivo="img.png",
        ancho_natural=20.0,
        alto_natural=10.0,
        x=10.0,
        y=10.0,
        ancho=20.0,
        alto=10.0,
        rotacion=rotacion,
    )

    esquinas_orig = esquinas_capa(capa_orig)
    opuestos = {
        "tr": "bl",
        "bl": "tr",
        "tl": "br",
        "br": "tl",
    }

    deltas = [(4.0, 2.0), (-3.0, 5.0), (2.0, -1.0)]

    for t_id, op_id in opuestos.items():
        for delta in deltas:
            capa_estirada = estirar(
                capa_orig,
                t_id,
                delta_plano=delta,
                mantener_proporcion=mantener_proporcion,
                minimo_cm=1.0,
            )
            esquinas_nuevas = esquinas_capa(capa_estirada)

            # Invarianza: la esquina opuesta NO debe moverse
            p_fijo_orig = esquinas_orig[op_id]
            p_fijo_nuevo = esquinas_nuevas[op_id]
            assert abs(p_fijo_nuevo[0] - p_fijo_orig[0]) < 1e-3, (
                f"Fallo en {t_id} (opuesto {op_id}): X cambió de {p_fijo_orig[0]} a {p_fijo_nuevo[0]}"
            )
            assert abs(p_fijo_nuevo[1] - p_fijo_orig[1]) < 1e-3, (
                f"Fallo en {t_id} (opuesto {op_id}): Y cambió de {p_fijo_orig[1]} a {p_fijo_nuevo[1]}"
            )

            # Si mantiene proporción, verificar w/h
            if mantener_proporcion:
                prop_orig = capa_orig.ancho / capa_orig.alto
                prop_nueva = capa_estirada.ancho / capa_estirada.alto
                assert abs(prop_nueva - prop_orig) < 1e-3


@pytest.mark.parametrize("rotacion", [0.0, 45.0, 90.0])
def test_estirar_lados_invarianza_opuesta(rotacion):
    """Verifica que al estirar un lado, los dos vértices del lado opuesto permanecen inmóviles."""
    capa_orig = CapaDiseno(
        id="c1",
        nombre="capa",
        tipo="raster",
        archivo="img.png",
        ancho_natural=16.0,
        alto_natural=12.0,
        x=0.0,
        y=0.0,
        ancho=16.0,
        alto=12.0,
        rotacion=rotacion,
    )

    esquinas_orig = esquinas_capa(capa_orig)
    lados_opuestos = {
        "r": ("tl", "bl"),  # Lado derecho estirado -> lado izquierdo fijo
        "l": ("tr", "br"),  # Lado izquierdo estirado -> lado derecho fijo
        "t": ("bl", "br"),  # Lado superior estirado -> lado inferior fijo
        "b": ("tl", "tr"),  # Lado inferior estirado -> lado superior fijo
    }

    deltas = [(3.0, 2.0), (-2.0, 4.0)]

    for t_id, (p1_id, p2_id) in lados_opuestos.items():
        for delta in deltas:
            capa_estirada = estirar(
                capa_orig,
                t_id,
                delta_plano=delta,
                mantener_proporcion=False,
                minimo_cm=1.0,
            )
            esquinas_nuevas = esquinas_capa(capa_estirada)

            # Ambos vértices del lado opuesto deben ser idénticos
            for p_id in (p1_id, p2_id):
                orig_pt = esquinas_orig[p_id]
                new_pt = esquinas_nuevas[p_id]
                assert abs(new_pt[0] - orig_pt[0]) < 1e-3
                assert abs(new_pt[1] - orig_pt[1]) < 1e-3


# ------------------------------------------------------------------------------
# 5. Mínimo cm y verificación de signos con SVG real de svg_abanico
# ------------------------------------------------------------------------------


def test_minimo_cm_limite():
    """Verifica que estirar hacia adentro nunca reduzca las dimensiones por debajo de minimo_cm."""
    capa = CapaDiseno(
        id="c1",
        nombre="c",
        tipo="raster",
        archivo="f.png",
        ancho_natural=10.0,
        alto_natural=10.0,
        x=0.0,
        y=0.0,
        ancho=10.0,
        alto=10.0,
    )

    # Intento de colapso extremo
    capa_chica = estirar(capa, "tr", delta_plano=(-100.0, -100.0), minimo_cm=2.5)
    assert capa_chica.ancho >= 2.5
    assert capa_chica.alto >= 2.5

    capa_chica_lado = estirar(capa, "r", delta_plano=(-100.0, 0.0), minimo_cm=1.5)
    assert capa_chica_lado.ancho >= 1.5


def test_verificacion_signos_con_svg_abanico_real():
    """Verifica que mover el ratón hacia arriba sube la capa tanto en plano como en pantalla."""
    # 1. Generar abanico real con calculadora
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )
    calc = TrompoEstrellaCalculator()
    res = calc.calcular(entrada)

    # Abanico de cono superior en modo mitad
    svg_str = svg_abanico(
        resultado=res,
        entrada=entrada,
        seccion="superior",
        hoja="carta",
        dibujar="mitad",
    )

    # La hoja carta es 215.9 x 279.4 mm
    vista_svg = VistaSvg(0.0, 0.0, 215.9, 279.4)
    zona_px = (600.0, 800.0)

    conv = Conversion(
        vista=vista_svg,
        zona_px=zona_px,
        y_arriba=True,
        factor_escala=10.0 / 20.0,  # factor_s=20 -> 0.5 mm/cm
        cx_vista=107.95,
        cy_vista=139.7,
        y_mid_plano=60.0,
    )

    capa = CapaDiseno(
        id="c1",
        nombre="prueba",
        tipo="raster",
        archivo="recurso.png",
        ancho_natural=15.0,
        alto_natural=15.0,
        x=0.0,
        y=50.0,
        ancho=15.0,
        alto=15.0,
    )

    pos_px_inicial = conv.plano_a_px(*centro_capa(capa))

    # El usuario arrastra el ratón hacia arriba: dy_px < 0 (ej. -40 px)
    dy_px = -40.0
    dx_px = 0.0
    dx_plano, dy_plano = conv.delta_px_a_plano(dx_px, dy_px)

    # En el plano +y apunta hacia arriba, así que dy_plano DEBE ser positivo
    assert dy_plano > 0.0, "Al mover el ratón hacia arriba, dy_plano debe ser positivo"

    # Mover la capa con este delta
    capa_movida = mover(capa, (dx_plano, dy_plano))
    assert capa_movida.y > capa.y

    # Posición en pantalla resultante
    pos_px_final = conv.plano_a_px(*centro_capa(capa_movida))

    # En pantalla, el centro debe haber subido (pos_px_final[1] < pos_px_inicial[1])
    assert pos_px_final[1] < pos_px_inicial[1]
    assert abs((pos_px_final[1] - pos_px_inicial[1]) - dy_px) < 1e-4


def test_rotacion_hacia_cursor():
    """Verifica que la función rotar calcula el ángulo correcto hacia el cursor."""
    capa = CapaDiseno(
        id="c1",
        nombre="c",
        tipo="raster",
        archivo="f.png",
        ancho_natural=10.0,
        alto_natural=10.0,
        x=0.0,
        y=0.0,
        ancho=10.0,
        alto=10.0,
        rotacion=0.0,
    )
    cx, cy = centro_capa(capa)  # (5.0, 5.0)

    # Cursor directamente arriba del centro (+Y en el plano): rotación debe ser 0°
    capa_rot0 = rotar(capa, (cx, cy + 10.0))
    assert abs(capa_rot0.rotacion) < 1e-2

    # Cursor a la derecha del centro (+X en el plano): debe rotar -90° (horario)
    capa_rot90 = rotar(capa, (cx + 10.0, cy))
    assert abs(capa_rot90.rotacion - (-90.0)) < 1e-2

    # Cursor con ajuste a paso de 15°
    capa_paso = rotar(capa, (cx + 10.0, cy + 10.0), paso_grados=15.0)
    # Vector a 45° matemático -> rotación = 45° - 90° = -45°
    assert abs(capa_paso.rotacion - (-45.0)) < 1e-2
