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
    assert v.detector_gestos is not None
    assert v.btn_zoom_in is not None
    assert v.btn_zoom_out is not None
    assert v.btn_ajustar is not None
    assert v.lbl_zoom_porcentaje is not None


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

    # 3. Pestaña Moldes 2D activa con viewBox
    assert v.lbl_vacio_moldes.visible is False
    assert v.panel_contenido_moldes.visible is True
    assert v.img_svg.src is not None
    assert b"<svg" in v.img_svg.src
    assert b'width="100%"' in v.img_svg.src
    assert b'viewBox=' in v.img_svg.src

    # Cambiar selector de moldes a Cono superior ("1")
    v.selector_molde.selected = ["1"]
    v.on_cambio_pieza_molde(None)
    assert v.img_svg.src is not None
    assert b"<svg" in v.img_svg.src


def test_zoom_gestos_y_botones():
    v = VistaTrompo()
    v.on_calcular(None)

    # Estado inicial: 100%
    assert v.lbl_zoom_porcentaje.value == "100 %"
    ancho_inicial = v.vista_svg.ancho

    # Botón Zoom In (+)
    v._on_btn_zoom_in(None)
    assert v.vista_svg.ancho < ancho_inicial
    pct_in = float(v.lbl_zoom_porcentaje.value.replace("%", "").strip())
    assert pct_in > 100.0

    # Botón Zoom Out (-)
    v._on_btn_zoom_out(None)
    pct_out = float(v.lbl_zoom_porcentaje.value.replace("%", "").strip())
    assert pct_out < pct_in

    # Botón Ajustar
    v._on_btn_ajustar(None)
    assert v.lbl_zoom_porcentaje.value == "100 %"
    assert v.vista_svg.ancho == pytest.approx(ancho_inicial)

    # Doble clic ajusta
    v._on_btn_zoom_in(None)
    assert v.lbl_zoom_porcentaje.value != "100 %"
    v._on_gesture_double_tap(None)
    assert v.lbl_zoom_porcentaje.value == "100 %"


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


class MockPage:
    def __init__(self):
        self.updates = 0
        self.theme_mode = ft.ThemeMode.DARK
        self.theme = None
        self.dark_theme = None
        self.theme_animation_style = None

    def update(self):
        self.updates += 1


def test_toggle_tema_atomico_y_una_sola_actualizacion():
    v = VistaTrompo()
    mock_p = MockPage()
    # Mockear property obtener_pagina
    type(v).obtener_pagina = property(lambda self: mock_p)

    v.on_calcular(None)
    mock_p.updates = 0

    # Alternar tema
    v.on_toggle_tema(None)

    # Demostrar que se llama a page.update() EXACTAMENTE 1 vez
    assert mock_p.updates == 1
    assert v.conteo_page_updates == 1
    assert v.ultimo_tiempo_toggle_tema_ms > 0
    # Verificamos que la animación fue desactivada
    assert mock_p.theme_animation_style is not None

    # Alternar de vuelta a oscuro
    v.on_toggle_tema(None)
    assert mock_p.updates == 2
    assert v.conteo_page_updates == 2


def test_wcag_contraste_textos_y_arbol_sin_colores_viejos():
    from tests.test_estilos import _ratio_contraste
    from app_flet.tema import PALETA_OSCURA, PALETA_CLARA

    # 1. Contraste WCAG >= 4.5 de textos principales y secundarios en ambos temas
    for pal, nombre in [(PALETA_OSCURA, "Oscuro"), (PALETA_CLARA, "Claro")]:
        # Texto principal contra fondo y contra panel
        r1 = _ratio_contraste(pal.texto, pal.fondo)
        r2 = _ratio_contraste(pal.texto, pal.panel)
        assert r1 >= 4.5, f"Texto en {nombre} contra fondo ratio {r1:.2f} < 4.5"
        assert r2 >= 4.5, f"Texto en {nombre} contra panel ratio {r2:.2f} < 4.5"

        # Texto secundario (etiquetas/ayudas) contra panel
        r3 = _ratio_contraste(pal.texto_secundario, pal.panel)
        assert r3 >= 4.5, f"Texto secundario en {nombre} contra panel ratio {r3:.2f} < 4.5"

    # 2. Recorrer árbol de controles tras alternar a claro:
    # Comprobar que ningún control conserva los colores hex viejos del modo oscuro
    v = VistaTrompo()
    v.on_calcular(None)
    v.on_toggle_tema(None) # Pasa a claro

    colores_prohibidos_en_claro = {
        PALETA_OSCURA.texto.lower(),
        PALETA_OSCURA.texto_secundario.lower(),
        PALETA_OSCURA.panel.lower(),
        PALETA_OSCURA.fondo.lower(),
    }

    def verificar_control(ctrl):
        if not ctrl:
            return
        for prop in ["color", "bgcolor"]:
            val = getattr(ctrl, prop, None)
            if isinstance(val, str) and val.startswith("#"):
                assert val.lower() not in colores_prohibidos_en_claro, (
                    f"Control {ctrl} retiene color {val} del tema oscuro en modo claro"
                )
        # Recursión sobre controls / content
        if hasattr(ctrl, "controls") and isinstance(ctrl.controls, list):
            for c in ctrl.controls:
                verificar_control(c)
        if hasattr(ctrl, "content") and ctrl.content:
            verificar_control(ctrl.content)

    verificar_control(v)


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


