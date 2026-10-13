import math
import pytest
pytest.importorskip("flet")
import flet as ft

from app_flet.vistas.trompo import VistaTrompo
from app_flet.controlador import ControladorTrompo

def test_construccion_flet_estado_inicial():
    v = VistaTrompo()
    assert v is not None
    assert v.txt_gajos is not None
    assert v.tabs is not None
    assert v.tabs.length == 6

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


class MockSizeEvent:
    def __init__(self, w: float, h: float):
        self.width = w
        self.height = h


def test_visor_adaptacion_tamano_zona():
    v = VistaTrompo()
    v.on_calcular(None)

    # 1. Simular evento de cambio de tamaño a zona ancha (800x400)
    # Contenedor tiene padding=10 y border=1, descuento = 2*(10+1) = 22
    ev_ancho = MockSizeEvent(822.0, 422.0)
    v._on_container_size_change(ev_ancho)

    assert abs(v.zona_ancho - 800.0) < 0.1
    assert abs(v.zona_alto - 400.0) < 0.1
    assert abs(v.img_svg.width - 800.0) < 0.1
    assert abs(v.img_svg.height - 400.0) < 0.1

    # Comprobar que la vista base conserva la relación de aspecto medida (800/400 = 2.0)
    assert abs(v.vista_svg.aspecto - 2.0) < 0.05

    # 2. Conservación del centro al cambiar aspecto
    cx_antes = v.vista_svg.x + v.vista_svg.ancho / 2.0
    cy_antes = v.vista_svg.y + v.vista_svg.alto / 2.0

    # Cambiar a zona alta (422x822 -> útil 400x800, aspecto 0.5)
    ev_alto = MockSizeEvent(422.0, 822.0)
    v._on_container_size_change(ev_alto)

    cx_despues = v.vista_svg.x + v.vista_svg.ancho / 2.0
    cy_despues = v.vista_svg.y + v.vista_svg.alto / 2.0
    assert math.isclose(cx_antes, cx_despues, rel_tol=1e-3)
    assert math.isclose(cy_antes, cy_despues, rel_tol=1e-3)
    assert abs(v.vista_svg.aspecto - 0.5) < 0.05

    # 3. Conversión de cursor a fracciones usando el tamaño medido
    class MockLocalPos:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class MockScrollEvent:
        def __init__(self, x, y):
            self.local_position = MockLocalPos(x, y)
            self.scroll_delta = MockLocalPos(0, -10)

    # Con zona de 400x800, posición x=200, y=400 debe representar fx=0.5, fy=0.5
    ev_scroll = MockScrollEvent(200.0, 400.0)
    vista_pre_scroll = v.vista_svg
    v._on_gesture_scroll(ev_scroll)
    # Al hacer zoom en el centro (0.5, 0.5), el centro debe permanecer idéntico
    cx_scroll = v.vista_svg.x + v.vista_svg.ancho / 2.0
    cy_scroll = v.vista_svg.y + v.vista_svg.alto / 2.0
    assert math.isclose(cx_despues, cx_scroll, rel_tol=1e-3)
    assert math.isclose(cy_despues, cy_scroll, rel_tol=1e-3)


def test_seleccion_perfil_armado_en_vista_flet():
    v = VistaTrompo()
    # Sin calcular: texto "Calcula para ver el perfil" al seleccionar perfil
    v.selector_molde.selected = ["4"]
    v.on_cambio_pieza_molde(None)
    assert v.lbl_vacio_moldes.content.value == "Calcula para ver el perfil"

    # Al calcular
    v.on_calcular(None)
    assert v.panel_contenido_moldes.visible is True
    # Selector en '4' renderiza svg_perfil
    v.selector_molde.selected = ["4"]
    v.on_cambio_pieza_molde(None)
    assert "Perfil armado" in v._svg_actual_raw
    assert "Alto total:" in v._svg_actual_raw
    assert v.img_svg.src != b""



