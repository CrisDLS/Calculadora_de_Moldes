"""Pruebas de la pestaña de Hoja de trazo (F3) en Flet."""

import os
import pytest
from app_flet.vistas.trompo import VistaTrompo


class MockFilePicker:
    def __init__(self, ruta_retorno="/tmp/prueba.svg", carpeta_retorno="/tmp/paquete"):
        self.ruta_retorno = ruta_retorno
        self.carpeta_retorno = carpeta_retorno
        self.save_llamado = False
        self.dir_llamado = False

    async def save_file(self, **kwargs):
        self.save_llamado = True
        return self.ruta_retorno

    async def get_directory_path(self, **kwargs):
        self.dir_llamado = True
        return self.carpeta_retorno


def test_vista_trompo_6_pestanas_e_inicializacion():
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    assert vista.tabs.length == 6
    assert len(vista.tabs.content.controls[0].tabs) == 6
    tab_names = [t.label for t in vista.tabs.content.controls[0].tabs]
    assert tab_names == ["Resumen", "Tablas de moldes", "Moldes 2D", "Hoja de trazo", "Diseño", "Vista 3D"]


def test_vista_trompo_hoja_tras_calcular():
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    # Estado inicial: vacio
    assert vista.lbl_vacio_hoja.visible is True
    assert vista.panel_contenido_hoja.visible is False

    # Calcular
    vista.on_calcular(None)
    assert vista.lbl_vacio_hoja.visible is False
    assert vista.panel_contenido_hoja.visible is True
    assert vista.img_svg_hoja.src != ""
    assert len(vista.col_resumen_esquema.controls) > 0


def test_vista_trompo_cambio_opciones_hoja():
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # Cambiar pieza a pico
    vista.selector_pieza_hoja.selected = ["pico"]
    vista.on_cambio_pieza_hoja(None)
    assert vista.controlador.hoja_pieza == "pico"
    assert vista.panel_contenido_hoja.visible is True

    # Cambiar opciones de hoja
    vista.dd_hoja.value = "a4"
    vista.dd_escala.value = "20"
    vista.on_cambio_hoja_opciones(None)
    assert vista.controlador.hoja_tipo == "a4"
    assert vista.controlador.hoja_escala == "20"
    assert vista.panel_contenido_hoja.visible is True


def test_vista_trompo_esquema_error_muestra_aviso():
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # Central con espejo pero grupo par (invalido)
    vista.dd_modo_esquema.value = "central_espejo"
    vista.txt_tam_grupo.value = "4"
    vista.on_cambio_esquema_opciones(None)

    assert vista.lbl_error_esquema.visible is True
    assert "impar" in vista.lbl_error_esquema.value
    assert vista.panel_contenido_hoja.visible is False
    assert vista.lbl_vacio_hoja.visible is True


@pytest.mark.anyio
async def test_vista_trompo_exportar_hoja_y_paquete(tmp_path):
    archivo_svg = str(tmp_path / "hoja_prueba.svg")
    carpeta_paquete = str(tmp_path / "paquete_prueba")
    picker = MockFilePicker(ruta_retorno=archivo_svg, carpeta_retorno=carpeta_paquete)
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # Exportar hoja
    await vista.on_exportar_hoja(None)
    assert picker.save_llamado is True
    assert os.path.exists(archivo_svg)
    assert os.path.getsize(archivo_svg) > 100
    assert "Hoja exportada" in vista.ultimo_mensaje_snackbar

    # Exportar paquete
    await vista.on_exportar_paquete(None)
    assert picker.dir_llamado is True
    assert os.path.exists(carpeta_paquete)
    archivos = os.listdir(carpeta_paquete)
    assert len(archivos) >= 3
    assert "Paquete exportado" in vista.ultimo_mensaje_snackbar


def test_hoja_trazo_pico_una_cara_y_sincronizacion_con_diseno():
    import re
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # 1. Cambiar a pico en Hoja de trazo
    vista.selector_pieza_hoja.selected = ["pico"]
    vista.on_cambio_pieza_hoja(None)
    assert vista.controlador.hoja_pieza == "pico"

    # La hoja de trazo del pico debe contener 1 sola cara (no 4)
    svg_pico = vista.controlador.svg_hoja
    caras_en_hoja = re.findall(r'Cara \d+', svg_pico)
    assert len(caras_en_hoja) == 1, f"La hoja de trazo del pico debe tener 1 cara, tiene {len(caras_en_hoja)}"

    # 2. Con 'Mitad (espejo)' activo en Diseño, la hoja muestra la mitad con eje recto
    vista.controlador.cambiar_diseno_seccion("pico")
    vista.controlador.cambiar_diseno_lienzo_modo("mitad")
    vista.pestana_hoja.actualizar(vista.controlador.get_view_model())

    assert vista.controlador.hoja_dibujar == "mitad"
    assert vista.pestana_hoja.selector_modo_dibujo.selected == ["mitad"]
    svg_mitad = vista.controlador.svg_hoja
    assert 'id="eje-espejo-recto"' in svg_mitad
    assert "Cara 1" in svg_mitad

    # 3. Y viceversa: cambiar en la hoja se refleja en Diseño
    # Cambiar a completo (cara completa) desde la hoja
    vista.pestana_hoja.selector_modo_dibujo.selected = ["completo"]
    vista.pestana_hoja.on_cambio_modo_dibujo(None)
    vista.pestana_diseno.actualizar(vista.controlador.get_view_model())

    assert vista.controlador.diseno_lienzo_modo == "una_cara"
    assert vista.pestana_diseno.selector_lienzo_diseno.selected == ["una_cara"]
    assert 'id="eje-espejo-recto"' not in vista.controlador.svg_hoja

    # Cambiar a mitad desde la hoja
    vista.pestana_hoja.selector_modo_dibujo.selected = ["mitad"]
    vista.pestana_hoja.on_cambio_modo_dibujo(None)
    vista.pestana_diseno.actualizar(vista.controlador.get_view_model())

    assert vista.controlador.diseno_lienzo_modo == "mitad"
    assert vista.pestana_diseno.selector_lienzo_diseno.selected == ["mitad"]
    assert 'id="eje-espejo-recto"' in vista.controlador.svg_hoja


def test_reactividad_inmediata_cambio_esquema_hoja():
    """Verifica que cambiar modo o grupo G en la Hoja de trazo valide y redibuje inmediatamente,
    despachando la actualización a la vista sin pulsar Calcular."""
    import unittest.mock as mock

    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # Simular página de Flet conectada
    mock_update = mock.MagicMock()
    vista.update = mock_update

    # 1. Cambiar a modo espejo_total con G=5 (inválido por impar)
    vista.dd_modo_esquema.value = "espejo_total"
    vista.txt_tam_grupo.value = "5"
    vista.on_cambio_esquema_opciones(None)

    # Debe despachar actualización a la vista y mostrar el error al instante
    assert mock_update.call_count >= 1, "vista.update() debió ser invocado para reflejar el error de inmediato"
    assert vista.lbl_error_esquema.visible is True
    assert "par" in vista.lbl_error_esquema.value
    assert vista.panel_contenido_hoja.visible is False
    assert vista.lbl_vacio_hoja.visible is True

    # 2. Cambiar G a 6 (válido: par y divisor de 30)
    mock_update.reset_mock()
    vista.txt_tam_grupo.value = "6"
    vista.on_cambio_esquema_opciones(None)

    # Debe despachar actualización a la vista y redibujar el abanico al instante
    assert mock_update.call_count >= 1, "vista.update() debió ser invocado para redibujar el abanico de inmediato"
    assert vista.lbl_error_esquema.visible is False
    assert vista.panel_contenido_hoja.visible is True
    assert vista.lbl_vacio_hoja.visible is False
    assert vista.img_svg_hoja.src != ""


def test_independencia_grupo_g_secciones_y_deshabilitado_en_pico():
    """Verifica que cambiar G en el cono superior no cambie el G de inferior ni de pico,
    que en pico el campo G muestre 4 y esté deshabilitado, y al volver a un cono
    se habilite con su valor propio."""
    picker = MockFilePicker()
    vista = VistaTrompo(servicio_file_picker=picker)
    vista.on_calcular(None)

    # 1. Por defecto, superior tiene G=5
    assert vista.controlador.hoja_pieza == "superior"
    assert vista.txt_tam_grupo.value == "5"
    assert vista.txt_tam_grupo.disabled is False

    # 2. Cambiar G a 8 en cono superior
    vista.txt_tam_grupo.value = "8"
    vista.on_cambio_esquema_opciones(None)

    # Debe ser 8 en superior, pero inferior debe conservar su valor propio (5)
    assert vista.controlador.config_secciones["superior"].esquema.tam_grupo == 8
    assert vista.controlador.config_secciones["inferior"].esquema.tam_grupo == 5

    # 3. Seleccionar pico
    vista.selector_pieza_hoja.selected = ["pico"]
    vista.on_cambio_pieza_hoja(None)

    # El campo G en el pico debe mostrar 4 y estar deshabilitado (no editable)
    assert vista.controlador.hoja_pieza == "pico"
    assert vista.txt_tam_grupo.value == "4"
    assert vista.txt_tam_grupo.disabled is True

    # Cambiar G en cono superior no debió alterar pico, ni cambiar G en pico debe afectar superior
    assert vista.controlador.config_secciones["superior"].esquema.tam_grupo == 8
    assert vista.controlador.config_secciones["inferior"].esquema.tam_grupo == 5

    # 4. Volver a cono superior
    vista.selector_pieza_hoja.selected = ["superior"]
    vista.on_cambio_pieza_hoja(None)

    # Debe habilitarse con su valor propio (8)
    assert vista.controlador.hoja_pieza == "superior"
    assert vista.txt_tam_grupo.value == "8"
    assert vista.txt_tam_grupo.disabled is False

    # 5. Ir a cono inferior
    vista.selector_pieza_hoja.selected = ["inferior"]
    vista.on_cambio_pieza_hoja(None)

    # Debe habilitarse con su valor propio (5)
    assert vista.controlador.hoja_pieza == "inferior"
    assert vista.txt_tam_grupo.value == "5"
    assert vista.txt_tam_grupo.disabled is False

    # 6. Proyecto viejo con G!=4 en pico: se ignora al mostrarlo y no se borra
    from logic.diseno.esquema import EsquemaDiseno
    vista.controlador.config_secciones["pico"].esquema = EsquemaDiseno("repeticion", 7)
    vista.selector_pieza_hoja.selected = ["pico"]
    vista.on_cambio_pieza_hoja(None)
    assert vista.txt_tam_grupo.value == "4"
    assert vista.txt_tam_grupo.disabled is True
    # No se borra del objeto
    assert vista.controlador.config_secciones["pico"].esquema.tam_grupo == 7



