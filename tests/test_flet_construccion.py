import pytest
pytest.importorskip("flet")

from app_flet.vistas.trompo import VistaTrompo
from app_flet.controlador import ControladorTrompo

def test_construccion_flet():
    # Solo construir la vista para asegurar que no hay errores de sintaxis o de API
    v = VistaTrompo()
    assert v is not None
    # Verificar controles clave
    assert v.txt_altura is not None
    assert v.txt_gajos is not None
    assert v.tabs is not None
    assert v.tabs.length == 4
    
    # Calcular y ver que se actualiza el layout (tarjetas en ResponsiveRow)
    v.on_calcular(None)
    assert len(v.grid_tarjetas.controls) == 8 # En modo simple
