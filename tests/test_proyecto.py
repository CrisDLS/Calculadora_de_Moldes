import pytest
import os
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_proyecto_ida_y_vuelta(tmp_path):
    ent = BalloonInput(
        380, 30, 2, 1,
        usar_parametros_avanzados=True,
        diametro_boca=50.0,
        pestana_boca=4.0,
        diametro_mecha=25.0,
        masa_mecha_g=40.0,
        alambre_mm=1.5,
        varillas=2,
        altura_llama=40.0,
        holgura_min=10.0,
    )
    cond = Condiciones(t_ambiente=25.0, t_interior=75.0)
    ciclo = [(0, False), (1, False), (2, True), (1, True)]
    esq = EsquemaDiseno("personalizado", 4, ciclo=ciclo)
    p1 = Proyecto(2, "Test Completo", ent, cond, esq, "Nota test", hoja="a4", escala=15)
    
    ruta = tmp_path / "test.json"
    guardar_proyecto(p1, str(ruta))
    
    p2 = cargar_proyecto(str(ruta))
    assert p2.version == 2
    assert p2.nombre == "Test Completo"
    assert p2.entrada.altura_cuerpo == 380
    assert p2.entrada.usar_parametros_avanzados is True
    assert p2.entrada.diametro_boca == 50.0
    assert p2.entrada.pestana_boca == 4.0
    assert p2.condiciones.t_interior == 75.0
    assert p2.esquema.modo == "personalizado"
    assert p2.esquema.tam_grupo == 4
    assert p2.esquema.ciclo == [(0, False), (1, False), (2, True), (1, True)]
    assert p2.hoja == "a4"
    assert p2.escala == 15
    assert p2.notas == "Nota test"
    assert "superior" in p2.config_secciones
    assert "inferior" in p2.config_secciones
    assert "pico" in p2.config_secciones

def test_proyecto_migracion_v1_a_v2(tmp_path):
    ruta = tmp_path / "v1.json"
    contenido_v1 = {
        "version": 1,
        "nombre": "Proyecto V1",
        "entrada": {
            "altura_cuerpo": 380,
            "num_gajos": 20,
            "num_hileras_picos": 2,
            "ancho_costura": 1,
        },
        "esquema": {
            "modo": "repeticion",
            "tam_grupo": 4,
        },
        "hoja": "carta",
        "escala": "auto",
        "notas": "Proyecto antiguo",
    }
    import json
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido_v1, f)

    p = cargar_proyecto(str(ruta))
    assert p.version == 2
    assert p.nombre == "Proyecto V1"
    assert "superior" in p.config_secciones
    assert "inferior" in p.config_secciones
    assert "pico" in p.config_secciones
    assert p.config_secciones["superior"].esquema.modo == "repeticion"
    assert p.config_secciones["superior"].esquema.tam_grupo == 4
    assert p.config_secciones["inferior"].esquema.modo == "repeticion"

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
    # Archivo viejo: sin esquema, condiciones, notas, hoja ni escala
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min", "entrada": {"altura_cuerpo": 100, "num_gajos": 10, "num_hileras_picos": 1, "ancho_costura": 1}}')
    
    p = cargar_proyecto(str(ruta))
    assert p.esquema is None
    assert p.notas == ""
    assert p.hoja == "carta"
    assert p.escala == "auto"
    assert p.condiciones.t_ambiente == 28.0 # valor por defecto de Condiciones

def test_proyecto_falta_entrada(tmp_path):
    ruta = tmp_path / "sin_ent.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min"}')
    
    with pytest.raises(ValueError, match="Falta el campo requerido: entrada"):
        cargar_proyecto(str(ruta))
