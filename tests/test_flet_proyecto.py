"""Pruebas de guardar y abrir proyecto (F3) en Flet."""

import os
import pytest
from app_flet.vistas.trompo import VistaTrompo


class MockFilePickerProyecto:
    def __init__(self, ruta_guardar=None, archivos_abrir=None):
        self.ruta_guardar = ruta_guardar
        self.archivos_abrir = archivos_abrir or []
        self.save_llamado = False
        self.pick_llamado = False

    async def save_file(self, **kwargs):
        self.save_llamado = True
        return self.ruta_guardar

    async def pick_files(self, **kwargs):
        self.pick_llamado = True
        return self.archivos_abrir


class MockFileResult:
    def __init__(self, path):
        self.path = path


@pytest.mark.anyio
async def test_vista_trompo_proyecto_flujo_completo(tmp_path):
    archivo_json = str(tmp_path / "globo_navidad.json")
    picker = MockFilePickerProyecto(
        ruta_guardar=archivo_json,
        archivos_abrir=[MockFileResult(archivo_json)]
    )
    vista = VistaTrompo(servicio_file_picker=picker)

    # Estado inicial
    assert vista.lbl_nombre_proyecto.value == "Sin título"
    assert vista.lbl_estado_proyecto.value == ""

    # Modificar una entrada
    vista.txt_altura.value = "920"
    vista.on_change_input(None)
    assert vista.lbl_estado_proyecto.value == "Sin guardar"

    # Guardar como...
    await vista.on_proyecto_guardar_como(None)
    assert picker.save_llamado is True
    assert os.path.exists(archivo_json)
    assert vista.lbl_nombre_proyecto.value == "globo_navidad"
    assert vista.lbl_estado_proyecto.value == ""
    assert "Proyecto guardado como" in vista.ultimo_mensaje_snackbar

    # Guardar cambios adicionales directamente
    vista.txt_gajos.value = "28"
    vista.on_change_input(None)
    assert vista.lbl_estado_proyecto.value == "Sin guardar"
    await vista.on_proyecto_guardar(None)
    assert vista.lbl_estado_proyecto.value == ""
    assert "Proyecto guardado" in vista.ultimo_mensaje_snackbar

    # Nuevo proyecto
    vista.on_proyecto_nuevo(None)
    assert vista.lbl_nombre_proyecto.value == "Sin título"
    assert vista.txt_altura.value == "950"
    assert vista.txt_gajos.value == "30"
    assert "Nuevo proyecto iniciado" in vista.ultimo_mensaje_snackbar

    # Abrir proyecto
    await vista.on_proyecto_abrir(None)
    assert picker.pick_llamado is True
    assert vista.lbl_nombre_proyecto.value == "globo_navidad"
    assert vista.txt_altura.value == "920.0" or vista.txt_altura.value == "920"
    assert vista.txt_gajos.value == "28"
    assert vista.lbl_estado_proyecto.value == ""
    assert "Proyecto abierto" in vista.ultimo_mensaje_snackbar
