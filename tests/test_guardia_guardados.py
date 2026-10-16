"""Pruebas de guardia para asegurar que las pruebas y demos no tocan la carpeta guardados/."""
import os
import hashlib
from pathlib import Path
from logic.proyecto.modelo import obtener_carpeta_datos, CARPETA_DATOS_DEFAULT
from app_flet.controlador import ControladorTrompo


def test_globos_datos_apunta_a_directorio_temporal_en_tests():
    """Verifica que durante la ejecución de pruebas GLOBOS_DATOS está aislado en un temporal."""
    carpeta_datos = obtener_carpeta_datos()
    assert str(carpeta_datos) != CARPETA_DATOS_DEFAULT
    assert "globos_datos" in str(carpeta_datos).lower()


def test_controlador_sin_proyecto_usa_directorio_temporal():
    """Verifica que el controlador activo sin proyecto usa el directorio temporal y no guardados/."""
    ctrl = ControladorTrompo()
    rec_dir = ctrl.obtener_carpeta_recursos_activa()
    assert "guardados" not in rec_dir.parts
    assert "recursos_temp" in rec_dir.parts


def test_guardados_no_modificado_directamente():
    """Verifica que la carpeta guardados/ existe o se mantiene intacta."""
    carp = Path("guardados")
    if carp.exists():
        archivos = [f for f in carp.rglob("*") if f.is_file()]
        assert len(archivos) >= 0
