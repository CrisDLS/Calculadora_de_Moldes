import json
from pathlib import Path
import pytest
import flet as ft

from app_flet.vistas.trompo import VistaTrompo
from tests.snapshots.generar_snapshots import (
    SNAPSHOTS_DIR,
    MockPage,
    serializar_arbol,
)

def _cargar_snapshot(nombre: str):
    p = SNAPSHOTS_DIR / nombre
    assert p.exists(), f"No existe el archivo de snapshot {nombre}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def test_snapshot_ui_sin_datos():
    v = VistaTrompo()
    v._page = MockPage()
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot("arbol_sin_datos.json")
    assert actual == esperado

def test_snapshot_ui_950_simple():
    v = VistaTrompo()
    v._page = MockPage()
    v.txt_altura.value = "950"
    v.txt_gajos.value = "30"
    v.txt_hileras.value = "2"
    v.txt_costura.value = "1.0"
    v.switch_avanzado.value = False
    v.on_calcular(None)
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot("arbol_950_simple.json")
    assert actual == esperado

def test_snapshot_ui_950_avanzado():
    v = VistaTrompo()
    v._page = MockPage()
    v.txt_altura.value = "950"
    v.txt_gajos.value = "30"
    v.txt_hileras.value = "2"
    v.txt_costura.value = "1.0"
    v.switch_avanzado.value = True
    v.panel_avanzado.visible = True
    v.on_calcular(None)
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot("arbol_950_avanzado.json")
    assert actual == esperado

@pytest.mark.parametrize("idx", list(range(6)))
def test_snapshot_ui_pestanas(idx):
    v = VistaTrompo()
    v._page = MockPage()
    v.txt_altura.value = "950"
    v.txt_gajos.value = "30"
    v.txt_hileras.value = "2"
    v.txt_costura.value = "1.0"
    v.on_calcular(None)
    v.tabs.selected_index = idx
    v._sync_controlador_a_vista(v.controlador.get_view_model())
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot(f"arbol_pestana_{idx}.json")
    assert actual == esperado

def test_snapshot_ui_tema():
    v = VistaTrompo()
    v._page = MockPage()
    v.on_calcular(None)
    v.on_toggle_tema(None)
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot("arbol_tema_cambiado.json")
    assert actual == esperado

def test_snapshot_ui_diseno_capa_mitad(tmp_path):
    v = VistaTrompo()
    v._page = MockPage()
    v.on_calcular(None)
    ej_svg = Path("docs/ejemplos/disenos/medallon.svg")
    rec_tmp = tmp_path / "rec"
    rec_tmp.mkdir(exist_ok=True)
    if ej_svg.exists():
        v.controlador.carpeta_recursos = rec_tmp
        v.controlador.anadir_capa(ej_svg)
    v.selector_seccion_diseno.selected = ["superior"]
    v.selector_lienzo_diseno.selected = ["mitad"]
    v.controlador.cambiar_diseno_seccion("superior")
    v.controlador.cambiar_diseno_lienzo_modo("mitad")
    v._sync_controlador_a_vista(v.controlador.get_view_model())
    actual = serializar_arbol(v)
    esperado = _cargar_snapshot("arbol_diseno_capa_mitad.json")
    assert actual == esperado
