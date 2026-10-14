import os
import pytest
import math
from pathlib import Path
from logic.diseno.lienzo import (
    CapaDiseno,
    Diseno,
    ajustar_capa,
    importar_recurso,
)
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.estilos import PANTALLA_OSCURO, IMPRESION
from logic.diseno.esquema import EsquemaDiseno
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput
from app_flet.controlador import ControladorTrompo
from app_flet.vistas.trompo import VistaTrompo


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def recurso_svg_sample(tmp_path):
    p = tmp_path / "estrella_decorativa.svg"
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="red"/></svg>', encoding="utf-8")
    return p


@pytest.fixture
def capa_prueba():
    return CapaDiseno(
        id="c1",
        nombre="test",
        tipo="svg",
        archivo="test.svg",
        ancho_natural=10.0,
        alto_natural=20.0,
        x=0.0,
        y=0.0,
        ancho=10.0,
        alto=20.0,
        rotacion=0.0,
        reflejo_h=False,
        reflejo_v=False,
        opacidad=1.0,
        visible=True,
        bloqueada=False,
    )


def test_ajustar_capa_modos(capa_prueba):
    ventana = (-50.0, 0.0, 50.0, 200.0)  # w_v = 100, h_v = 200 (aspecto 1:2)
    
    # 1. Centrar
    c_centrar = ajustar_capa(capa_prueba, ventana, "centrar")
    assert c_centrar.ancho == 10.0
    assert c_centrar.alto == 20.0
    # Centro en X=0, Y=100 => x_final = 0 - 5 = -5, y_final = 100 - 10 = 90
    assert c_centrar.x == pytest.approx(-5.0, abs=1e-3)
    assert c_centrar.y == pytest.approx(90.0, abs=1e-3)

    # 2. Contener
    # capa_prueba tiene w=10, h=20 (proporción 1:2). ventana es 100x200 (proporción 1:2).
    # Cabrá a s = min(100/10, 200/20) = 10 => w=100, h=200
    c_contener = ajustar_capa(capa_prueba, ventana, "contener")
    assert c_contener.ancho == pytest.approx(100.0, abs=1e-3)
    assert c_contener.alto == pytest.approx(200.0, abs=1e-3)
    assert c_contener.x == pytest.approx(-50.0, abs=1e-3)
    assert c_contener.y == pytest.approx(0.0, abs=1e-3)

    # Ventana asimétrica 100x100
    ventana_cuadrada = (-50.0, 0.0, 50.0, 100.0)
    # Contener en 100x100: limitado por alto (200 > 100 => s = 100/20 = 5 => w=50, h=100)
    c_cont_cuad = ajustar_capa(capa_prueba, ventana_cuadrada, "contener")
    assert c_cont_cuad.ancho == pytest.approx(50.0, abs=1e-3)
    assert c_cont_cuad.alto == pytest.approx(100.0, abs=1e-3)
    assert c_cont_cuad.x == pytest.approx(-25.0, abs=1e-3)
    assert c_cont_cuad.y == pytest.approx(0.0, abs=1e-3)

    # 3. Cubrir en 100x100: limitado por ancho (s = max(100/10, 100/20) = 10 => w=100, h=200)
    c_cubrir = ajustar_capa(capa_prueba, ventana_cuadrada, "cubrir")
    assert c_cubrir.ancho == pytest.approx(100.0, abs=1e-3)
    assert c_cubrir.alto == pytest.approx(200.0, abs=1e-3)
    assert c_cubrir.x == pytest.approx(-50.0, abs=1e-3)
    assert c_cubrir.y == pytest.approx(-50.0, abs=1e-3)

    # 4. Estirar
    c_estirar = ajustar_capa(capa_prueba, ventana_cuadrada, "estirar")
    assert c_estirar.ancho == pytest.approx(100.0, abs=1e-3)
    assert c_estirar.alto == pytest.approx(100.0, abs=1e-3)

    # 5. Ancho
    c_ancho = ajustar_capa(capa_prueba, ventana_cuadrada, "ancho")
    assert c_ancho.ancho == pytest.approx(100.0, abs=1e-3)
    assert c_ancho.alto == pytest.approx(200.0, abs=1e-3)
    assert c_ancho.x == pytest.approx(-50.0, abs=1e-3)

    # 6. Alto
    c_alto = ajustar_capa(capa_prueba, ventana_cuadrada, "alto")
    assert c_alto.alto == pytest.approx(100.0, abs=1e-3)
    assert c_alto.ancho == pytest.approx(50.0, abs=1e-3)


def test_importar_recurso_nombre_stem_y_posicion_contener(recurso_svg_sample, tmp_path):
    carp_rec = tmp_path / "recursos"
    ventana = (-40.0, 10.0, 40.0, 150.0)
    capa = importar_recurso(recurso_svg_sample, carp_rec, ventana=ventana)
    
    # Nombre por defecto debe ser el stem (sin extensión .svg)
    assert capa.nombre == "estrella_decorativa"
    assert capa.tipo == "svg"
    # Debe haber sido ajustada con contener dentro de la ventana
    assert capa.ancho > 0
    assert capa.alto > 0
    cx = capa.x + capa.ancho / 2.0
    cy = capa.y + capa.alto / 2.0
    assert cx == pytest.approx(0.0, abs=1e-2)
    assert cy == pytest.approx(80.0, abs=1e-2)


def test_svg_abanico_opciones_visuales_y_overlay():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(altura_cuerpo=950.0, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno(modo="repeticion", tam_grupo=5)

    capa_activa = CapaDiseno(
        id="c_activa",
        nombre="motivo",
        tipo="svg",
        archivo="test.svg",
        ancho_natural=20.0,
        alto_natural=30.0,
        x=-10.0,
        y=50.0,
        ancho=20.0,
        alto=30.0,
        rotacion=15.0,
        reflejo_h=False,
        reflejo_v=False,
        opacidad=1.0,
        visible=True,
        bloqueada=False,
    )

    # Con todo visible y overlay activo
    svg_txt = svg_abanico(
        resultado=res,
        entrada=inp,
        seccion="superior",
        esquema=esq,
        ver_cuadricula=True,
        ver_rotulos=True,
        ver_costuras=True,
        overlay_capa_activa=capa_activa,
    )
    assert 'id="layer-cuadricula"' in svg_txt
    assert 'id="layer-rotulos"' in svg_txt
    assert 'id="layer-costura"' in svg_txt
    assert 'id="layer-overlay-seleccion"' in svg_txt
    assert 'id="overlay-box"' in svg_txt
    assert 'id="tirador-tl"' in svg_txt
    assert 'id="tirador-centro"' in svg_txt

    # Ocultando capas
    svg_oculto = svg_abanico(
        resultado=res,
        entrada=inp,
        seccion="superior",
        esquema=esq,
        ver_cuadricula=False,
        ver_rotulos=False,
        ver_costuras=False,
        overlay_capa_activa=None,
    )
    assert 'id="layer-cuadricula"' not in svg_oculto
    assert 'id="layer-rotulos"' not in svg_oculto
    assert 'id="layer-costura"' not in svg_oculto
    assert 'id="layer-overlay-seleccion"' not in svg_oculto


def test_controlador_empujar_y_ajustes_rapidos(tmp_path, recurso_svg_sample):
    ctrl = ControladorTrompo()
    ctrl.calcular()
    ctrl.ruta_proyecto = str(tmp_path / "proyecto.json")
    capa = ctrl.anadir_capa(str(recurso_svg_sample))
    
    # Empujar X y Y
    x0 = capa.x
    y0 = capa.y
    ctrl.empujar_capa_seleccionada(dx=5.0, dy=-3.0, drot=10.0)
    assert capa.x == pytest.approx(x0 + 5.0, abs=1e-2)
    assert capa.y == pytest.approx(y0 - 3.0, abs=1e-2)
    assert capa.rotacion == 10.0

    # Ajustes rápidos
    ctrl.ajustar_capa_cubrir()
    assert capa.ancho > 0
    ctrl.ajustar_capa_contener()
    assert capa.ancho > 0
    ctrl.ajustar_capa_estirar()
    assert capa.ancho > 0
    ctrl.ajustar_capa_ancho()
    assert capa.ancho > 0
    ctrl.ajustar_capa_alto()
    assert capa.alto > 0
    ctrl.centrar_capa_seleccionada()
    vent = ctrl.ventana_lienzo()
    cx_vent = (vent[0] + vent[2]) / 2.0
    assert (capa.x + capa.ancho / 2.0) == pytest.approx(cx_vent, abs=1e-2)

    # Conmutadores de vista
    ctrl.cambiar_diseno_ver_cuadricula(False)
    assert ctrl.diseno_ver_cuadricula is False
    ctrl.cambiar_diseno_ver_rotulos(True)
    assert ctrl.diseno_ver_rotulos is True
    ctrl.cambiar_diseno_ver_costuras(False)
    assert ctrl.diseno_ver_costuras is False
    ctrl.cambiar_diseno_mostrar_reflejo(False)
    assert ctrl.diseno_mostrar_reflejo is False


def test_controlador_exportar_abanico_y_hoja(tmp_path, recurso_svg_sample):
    ctrl = ControladorTrompo()
    ctrl.calcular()
    ctrl.ruta_proyecto = str(tmp_path / "proy.json")
    ctrl.anadir_capa(str(recurso_svg_sample))

    ruta_abanico = tmp_path / "abanico_diseno.svg"
    ctrl.exportar_abanico_diseno(str(ruta_abanico))
    assert ruta_abanico.exists()
    contenido_ab = ruta_abanico.read_text(encoding="utf-8")
    assert "<svg" in contenido_ab
    assert "</svg>" in contenido_ab

    ruta_hoja = tmp_path / "hoja_diseno.svg"
    ctrl.exportar_hoja_diseno(str(ruta_hoja))
    assert ruta_hoja.exists()
    contenido_hj = ruta_hoja.read_text(encoding="utf-8")
    assert "<svg" in contenido_hj


def test_vista_controles_diseno_montaje():
    vista = VistaTrompo()
    ctrl = vista.controlador
    ctrl.calcular()
    vm = ctrl.get_view_model()
    vista._sync_controlador_a_vista(vm)

    # Verificar que los 6 botones de ajuste rápido y controles de empuje existen y están configurados
    assert hasattr(vista, "btn_ajustar_cubrir")
    assert hasattr(vista, "btn_ajustar_contener")
    assert hasattr(vista, "btn_ajustar_estirar")
    assert hasattr(vista, "btn_ajustar_ancho")
    assert hasattr(vista, "btn_ajustar_alto")
    assert hasattr(vista, "btn_centrar_capa")

    assert hasattr(vista, "btn_nudge_left")
    assert hasattr(vista, "btn_nudge_right")
    assert hasattr(vista, "btn_nudge_up")
    assert hasattr(vista, "btn_nudge_down")
    assert hasattr(vista, "btn_rot_m5")
    assert hasattr(vista, "btn_rot_p5")
    assert hasattr(vista, "btn_rot_0")

    # Botones de exportación
    assert hasattr(vista, "btn_exportar_abanico")
    assert hasattr(vista, "btn_exportar_gajos")
    assert hasattr(vista, "btn_exportar_hoja_diseno")

    # Barra superior de visualización
    assert hasattr(vista, "chk_ver_cuadricula")
    assert hasattr(vista, "chk_ver_rotulos")
    assert hasattr(vista, "chk_ver_costuras")
    assert hasattr(vista, "chk_mostrar_reflejo")
    assert hasattr(vista, "selector_interaccion_diseno")
