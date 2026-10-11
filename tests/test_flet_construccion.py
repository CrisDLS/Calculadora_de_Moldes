import pytest
pytest.importorskip("flet")
import flet as ft

from app_flet.vistas.trompo import VistaTrompo
from app_flet.controlador import ControladorTrompo

def test_construccion_flet_estado_inicial():
    v = VistaTrompo()
    assert v is not None
    assert v.txt_altura is not None
    assert v.txt_gajos is not None
    assert v.tabs is not None
    assert v.tabs.length == 4

    # Estado inicial: tablas y moldes muestran mensajes amables de vacío
    assert v.lbl_vacio_tablas.visible is True
    assert v.panel_contenido_tablas.visible is False
    assert v.lbl_vacio_moldes.visible is True
    assert v.panel_contenido_moldes.visible is False
    assert v.selector_tabla is not None
    assert v.selector_molde is not None
    assert v.btn_copiar_tabla is not None
    assert v.viewer_svg is not None


def test_construccion_flet_con_datos_y_selector_tablas():
    v = VistaTrompo()
    # Calcular en modo simple (950 / 30 / 2 / 1)
    v.on_calcular(None)

    # 1. Pestaña Resumen con tarjetas
    assert len(v.grid_tarjetas.controls) == 8

    # 2. Pestaña Tablas activa
    assert v.lbl_vacio_tablas.visible is False
    assert v.panel_contenido_tablas.visible is True

    # Por defecto está seleccionada la pieza 0 (Cono superior) -> 17 filas
    assert v.selector_tabla.selected == ["0"]
    assert len(v.tabla_componente.list_filas.controls) == 17
    assert len(v.tabla_componente.row_encabezados.controls) == 4
    # Verificar pesos proporcionales de las columnas
    pesos_header = [c.expand for c in v.tabla_componente.row_encabezados.controls]
    assert pesos_header == [7, 10, 10, 10]
    # Verificar alineación a la derecha
    assert v.tabla_componente.row_encabezados.controls[0].alignment.x == 1

    primera_fila = v.tabla_componente.list_filas.controls[0].content
    pesos_fila = [c.expand for c in primera_fila.controls]
    assert pesos_fila == [7, 10, 10, 10]
    assert "Cono superior" in v.lbl_titulo_tabla.value
    assert "30 piezas" in v.lbl_resumen_tabla.value

    # Cambiar a pieza 1 (Pico) -> 12 filas
    v.selector_tabla.selected = ["1"]
    v.on_cambio_pieza_tabla(None)
    assert len(v.tabla_componente.list_filas.controls) == 12
    assert "Pico" in v.lbl_titulo_tabla.value
    assert "triángulos" in v.lbl_resumen_tabla.value

    # Cambiar a pieza 2 (Cono inferior) -> 25 filas
    v.selector_tabla.selected = ["2"]
    v.on_cambio_pieza_tabla(None)
    assert len(v.tabla_componente.list_filas.controls) == 25
    assert "Cono inferior" in v.lbl_titulo_tabla.value

    # 3. Pestaña Moldes 2D activa
    assert v.lbl_vacio_moldes.visible is False
    assert v.panel_contenido_moldes.visible is True
    assert v.img_svg.src is not None
    assert b"<svg" in v.img_svg.src

    # Cambiar selector de moldes a Cono superior ("1")
    v.selector_molde.selected = ["1"]
    v.on_cambio_pieza_molde(None)
    assert v.img_svg.src is not None
    assert b"<svg" in v.img_svg.src


def test_construccion_flet_desactualizado():
    v = VistaTrompo()
    v.on_calcular(None)
    assert v.panel_contenido_tablas.visible is True
    assert v.panel_contenido_moldes.visible is True

    # Al cambiar un campo, se desactualiza
    v.txt_altura.value = "960"
    v.on_change_input(None)

    assert v.lbl_desactualizado.visible is True
    assert v.lbl_vacio_tablas.visible is True
    assert v.panel_contenido_tablas.visible is False
    assert v.lbl_vacio_moldes.visible is True
    assert v.panel_contenido_moldes.visible is False


def test_toggle_tema_claro_oscuro():
    v = VistaTrompo()
    assert v.modo_tema == ft.ThemeMode.DARK
    assert v.btn_tema.icon == ft.Icons.LIGHT_MODE
    assert v.controlador.estilo_svg.fondo_referencia == "#1e1e24"

    # Calcular para tener SVGs listos
    v.on_calcular(None)
    svg_oscuro = v.img_svg.src

    # Alternar a tema claro
    v.on_toggle_tema(None)
    assert v.modo_tema == ft.ThemeMode.LIGHT
    assert v.btn_tema.icon == ft.Icons.DARK_MODE
    assert v.controlador.estilo_svg.fondo_referencia == "#f8f9fa"
    svg_claro = v.img_svg.src
    assert svg_claro != svg_oscuro

    # Alternar de regreso a oscuro
    v.on_toggle_tema(None)
    assert v.modo_tema == ft.ThemeMode.DARK
    assert v.btn_tema.icon == ft.Icons.LIGHT_MODE
    assert v.controlador.estilo_svg.fondo_referencia == "#1e1e24"


class MockClipboard:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.texto_copiado = None

    def set(self, text: str):
        if self.fail:
            raise RuntimeError("Error simulado de portapapeles")
        self.texto_copiado = text


def test_copiar_tabla_con_servicio_mock():
    mock_cb = MockClipboard()
    v = VistaTrompo(servicio_clipboard=mock_cb)
    v.on_calcular(None)

    # Copiar con éxito
    v.on_copiar_tabla(None)
    assert mock_cb.texto_copiado is not None
    assert "Paso\tLargo (cm)\tAcumulado (cm)\tAncho/2 (cm)" in mock_cb.texto_copiado
    assert v.ultimo_mensaje_snackbar == "Tabla copiada al portapapeles"

    # Caso de fallo simulado
    mock_cb_fail = MockClipboard(fail=True)
    v_fail = VistaTrompo(servicio_clipboard=mock_cb_fail)
    v_fail.on_calcular(None)
    v_fail.on_copiar_tabla(None)
    assert mock_cb_fail.texto_copiado is None
    assert v_fail.ultimo_mensaje_snackbar == "No se pudo copiar"

