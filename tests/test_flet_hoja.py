"""Pruebas de la pestaña de Hoja de trazo (F3) en Flet."""

import os
import pytest
import flet as ft
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
