"""
Pruebas unitarias para el componente reutilizable VisorSvg.
"""

from unittest.mock import MagicMock
import pytest
from app_flet.vistas.componentes.visor_svg import VisorSvg
from logic.exportacion.vista_svg import VistaSvg


class MockSizeChangeEvent:
    def __init__(self, w: float, h: float):
        self.width = w
        self.height = h


class MockScrollEvent:
    def __init__(self, x: float, y: float, dy: float = -10.0):
        self.local_position = MagicMock(x=x, y=y)
        self.scroll_delta = MagicMock(y=dy)


class MockPanEvent:
    def __init__(self, dx: float, dy: float):
        self.local_delta = MagicMock(x=dx, y=dy)
        self.global_delta = None


def test_construccion_visor_svg():
    visor = VisorSvg(papel_blanco=False)
    assert visor.container_viewer_svg is not None
    assert visor.img_svg is not None
    assert visor.detector_gestos is not None
    assert visor.barra_zoom is not None
    assert visor.lbl_zoom_porcentaje.value == "100 %"
    assert visor.papel_blanco is False


def test_construccion_visor_svg_papel_blanco():
    visor = VisorSvg(papel_blanco=True, drag_interval=35)
    assert visor.papel_blanco is True
    assert visor.detector_gestos.drag_interval == 35


def test_cargar_svg_y_ajustar():
    visor = VisorSvg()
    svg_dummy = '<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    visor.cargar_svg(svg_dummy, reset_vista=True)

    assert visor.vista_svg is not None
    assert visor.vista_base_svg is not None
    assert visor.porcentaje_zoom() == pytest.approx(100.0, rel=1e-2)
    assert b"viewBox=" in visor.img_svg.src


def test_zoom_in_out_y_ajustar():
    visor = VisorSvg()
    svg_dummy = '<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    visor.cargar_svg(svg_dummy, reset_vista=True)

    ancho_base = visor.vista_svg.ancho
    visor.zoom_in()
    assert visor.vista_svg.ancho < ancho_base
    assert visor.porcentaje_zoom() > 100.0

    visor.zoom_out()
    assert visor.vista_svg.ancho == pytest.approx(ancho_base, rel=1e-2)

    # Zoom out adicional y reajuste
    visor.zoom_out()
    assert visor.vista_svg.ancho > ancho_base
    visor.ajustar_vista()
    assert visor.vista_svg.ancho == pytest.approx(ancho_base, rel=1e-2)


def test_size_change_adapta_aspecto():
    visor = VisorSvg()
    svg_dummy = '<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    visor.cargar_svg(svg_dummy, reset_vista=True)

    ev = MockSizeChangeEvent(w=800.0, h=400.0)
    visor.on_container_size_change(ev)

    assert abs(visor.zona_ancho - (800.0 - 22.0)) < 1.0
    assert abs(visor.zona_alto - (400.0 - 22.0)) < 1.0


def test_pan_update_desplaza_vista():
    visor = VisorSvg()
    svg_dummy = '<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    visor.cargar_svg(svg_dummy, reset_vista=True)

    x_inicial = visor.vista_svg.x
    ev = MockPanEvent(dx=10.0, dy=0.0)
    visor.on_gesture_pan_update(ev)

    # Al arrastrar hacia la derecha, la vista se desplaza
    assert visor.vista_svg.x != x_inicial


def test_pan_custom_callback():
    callback_mock = MagicMock(return_value=True)
    visor = VisorSvg(on_custom_pan_update=callback_mock)
    svg_dummy = '<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    visor.cargar_svg(svg_dummy, reset_vista=True)

    ev = MockPanEvent(dx=10.0, dy=5.0)
    visor.on_gesture_pan_update(ev)
    callback_mock.assert_called_once_with(ev)
