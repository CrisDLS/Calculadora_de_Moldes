import pytest
pytest.importorskip("flet")

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
    assert len(v.datatable.rows) == 17
    assert "Cono superior" in v.lbl_titulo_tabla.value
    assert "30 piezas" in v.lbl_resumen_tabla.value

    # Cambiar a pieza 1 (Pico) -> 12 filas
    v.selector_tabla.selected = ["1"]
    v.on_cambio_pieza_tabla(None)
    assert len(v.datatable.rows) == 12
    assert "Pico" in v.lbl_titulo_tabla.value
    assert "triángulos" in v.lbl_resumen_tabla.value

    # Cambiar a pieza 2 (Cono inferior) -> 25 filas
    v.selector_tabla.selected = ["2"]
    v.on_cambio_pieza_tabla(None)
    assert len(v.datatable.rows) == 25
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

    # Probar botón Copiar tabla sin excepciones
    v.on_copiar_tabla(None)


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
