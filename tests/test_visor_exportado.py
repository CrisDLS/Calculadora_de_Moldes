import pytest
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.pintura import EsquemaPintura
from logic.diseno.compra import lista_de_compra
from logic.exportacion.visor3d import exportar_visor_autocontenido
from logic.exportacion.escena3d import escena_a_dict

def test_visor_html_autocontenido_sin_referencias_externas(tmp_path):
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(ent)
    pintura = EsquemaPintura()
    
    escena = escena_a_dict(ent, res, esquema_pintura=pintura)
    salida_html = str(tmp_path / "visor_test.html")
    exportar_visor_autocontenido(escena, salida_html)

    with open(salida_html, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Verificar que no existen llamadas a scripts externos ni URLs externas en src o href
    assert '<script src=' not in contenido
    assert '<link rel="stylesheet"' not in contenido
    assert 'href="http' not in contenido
    assert 'src="http' not in contenido

    # Verificar que los datos y three.js están embebidos
    assert "window.__DATOS_ESCENA_3D__" in contenido
    assert "THREE.WebGLRenderer" in contenido
    assert "OrbitControls" in contenido
    assert "slider-azimut" in contenido
    assert "slider-elevacion" in contenido
    assert "btn-costuras" in contenido
    assert "btn-captura" in contenido
