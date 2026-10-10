import pytest
import os
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_proyecto_ida_y_vuelta(tmp_path):
    ent = BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    cond = Condiciones(t_ambiente=25.0, t_interior=75.0)
    esq = EsquemaDiseno("repeticion", 5)
    p1 = Proyecto(1, "Test 1", ent, cond, esq, "Nota test")
    
    ruta = tmp_path / "test.json"
    guardar_proyecto(p1, str(ruta))
    
    p2 = cargar_proyecto(str(ruta))
    assert p2.version == 1
    assert p2.nombre == "Test 1"
    assert p2.entrada.altura_cuerpo == 380
    assert p2.condiciones.t_interior == 75.0
    assert p2.esquema.modo == "repeticion"
    assert p2.esquema.tam_grupo == 5
    assert p2.notas == "Nota test"

def test_proyecto_version_desconocida(tmp_path):
    ruta = tmp_path / "bad_v.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 99, "nombre": "bad"}')
    with pytest.raises(ValueError, match="Versión de proyecto desconocida"):
        cargar_proyecto(str(ruta))

def test_proyecto_json_corrupto(tmp_path):
    ruta = tmp_path / "corrupto.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{version: 1')
    with pytest.raises(ValueError, match="El archivo no es un JSON válido"):
        cargar_proyecto(str(ruta))

def test_proyecto_campos_faltantes_valores_defecto(tmp_path):
    ruta = tmp_path / "faltantes.json"
    # Falta esquema, condiciones y notas
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min", "entrada": {"altura_cuerpo": 100, "num_gajos": 10, "num_hileras_picos": 1, "ancho_costura": 1}}')
    
    p = cargar_proyecto(str(ruta))
    assert p.esquema is None
    assert p.notas == ""
    assert p.condiciones.t_ambiente == 28.0 # valor por defecto de Condiciones

def test_proyecto_falta_entrada(tmp_path):
    ruta = tmp_path / "sin_ent.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min"}')
    
    with pytest.raises(ValueError, match="Falta el campo requerido: entrada"):
        cargar_proyecto(str(ruta))
