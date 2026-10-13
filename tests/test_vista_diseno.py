import os
import pytest
from pathlib import Path
from PIL import Image

from app_flet.controlador import ControladorTrompo
from app_flet.vistas.trompo import VistaTrompo

SVG_PRUEBA = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="red" />
</svg>"""

@pytest.fixture
def controlador_calculado():
    c = ControladorTrompo()
    c.txt_altura = "950"
    c.txt_gajos = "30"
    c.txt_hileras = "2"
    c.txt_costura = "1"
    c.calcular()
    return c

@pytest.fixture
def recurso_svg(tmp_path):
    f = tmp_path / "figura.svg"
    f.write_text(SVG_PRUEBA, encoding="utf-8")
    return str(f)

@pytest.fixture
def recurso_png(tmp_path):
    f = tmp_path / "foto.png"
    im = Image.new("RGBA", (120, 80), color=(0, 128, 255, 255))
    im.save(str(f), format="PNG")
    return str(f)

def test_controlador_diseno_gestion_capas(controlador_calculado, recurso_svg, recurso_png, tmp_path):
    c = controlador_calculado
    vm = c.get_view_model()
    assert vm.svg_diseno != ""
    assert len(vm.capas_diseno) == 0

    # 1. Añadir capa SVG
    c.ruta_proyecto = str(tmp_path / "proy.json")
    capa1 = c.anadir_capa(recurso_svg)
    assert capa1.tipo == "svg"
    assert c.capa_seleccionada_id == capa1.id
    assert c.sin_guardar is True

    # 2. Añadir capa PNG
    capa2 = c.anadir_capa(recurso_png)
    assert capa2.tipo == "raster"
    assert c.capa_seleccionada_id == capa2.id
    vm = c.get_view_model()
    assert len(vm.capas_diseno) == 2
    assert vm.capas_diseno[1].id == capa2.id

    # 3. Mover capa
    c.mover_capa(capa2.id, -1)
    vm = c.get_view_model()
    assert vm.capas_diseno[0].id == capa2.id
    assert vm.capas_diseno[1].id == capa1.id

    # 4. Modificar capa seleccionada
    c.capa_seleccionada_id = capa1.id
    c.modificar_capa_seleccionada(x=12.5, y=45.0, rotacion=45.0, opacidad=0.8, reflejo_h=True)
    sel = c.obtener_capa_seleccionada()
    assert sel.x == 12.5
    assert sel.y == 45.0
    assert sel.rotacion == 45.0
    assert sel.opacidad == 0.8
    assert sel.reflejo_h is True

    # 5. Centrar y ajustar
    c.centrar_capa_seleccionada()
    assert sel.x == -sel.ancho / 2.0

    c.ajustar_capa_ancho()
    assert sel.ancho > 0
    c.ajustar_capa_alto()
    assert sel.alto > 0

    # 6. Eliminar capa
    c.eliminar_capa(capa1.id)
    vm = c.get_view_model()
    assert len(vm.capas_diseno) == 1
    assert vm.capas_diseno[0].id == capa2.id
    assert c.capa_seleccionada_id == capa2.id

def test_controlador_diseno_secciones_y_modos(controlador_calculado):
    c = controlador_calculado
    # Por defecto superior
    assert c.diseno_seccion == "superior"
    assert c.clave_diseno_activo() == "superior"

    # Cambiar a pico Variante A
    c.cambiar_diseno_seccion("pico", "A")
    assert c.diseno_seccion == "pico"
    assert c.diseno_variante == "A"
    assert c.clave_diseno_activo() == "pico_A"

    # Cambiar a pico Variante B
    c.cambiar_diseno_seccion("pico", "B")
    assert c.diseno_seccion == "pico"
    assert c.diseno_variante == "B"
    assert c.clave_diseno_activo() == "pico_B"

    # Cambiar a inferior
    c.cambiar_diseno_seccion("inferior")
    assert c.diseno_seccion == "inferior"
    assert c.clave_diseno_activo() == "inferior"

    # Cambiar modo lienzo
    c.cambiar_diseno_lienzo_modo("mitad")
    assert c.diseno_lienzo_modo == "mitad"
    vm = c.get_view_model()
    assert vm.diseno_lienzo_modo == "mitad"

def test_controlador_diseno_exportaciones(controlador_calculado, recurso_svg, tmp_path):
    c = controlador_calculado
    c.ruta_proyecto = str(tmp_path / "proy.json")
    c.anadir_capa(recurso_svg)

    # Exportar gajos decorados
    dest_gajos = tmp_path / "gajos_salida"
    dest_gajos.mkdir()
    archivos = c.exportar_gajos_diseno(str(dest_gajos))
    assert len(archivos) > 0
    for a in archivos:
        assert Path(a).exists()

    # Exportar hoja decorada
    dest_hoja = tmp_path / "hoja_decorada.svg"
    c.exportar_hoja_diseno(str(dest_hoja))
    assert dest_hoja.exists()
    contenido = dest_hoja.read_text(encoding="utf-8")
    assert "<svg" in contenido
    assert "layer-diseno" in contenido

def test_vista_trompo_pestana_diseno(controlador_calculado, recurso_svg, tmp_path):
    c = controlador_calculado
    vista = VistaTrompo()
    vista.controlador = c
    vista._sync_controlador_a_vista(c.get_view_model())

    # Verificar que existen las 6 pestañas en el orden correcto
    tab_bar = vista.tabs.content.controls[0]
    nombres_tabs = [t.label for t in tab_bar.tabs]
    assert nombres_tabs == [
        "Resumen",
        "Tablas de moldes",
        "Moldes 2D",
        "Hoja de trazo",
        "Diseño",
        "Vista 3D",
    ]

    # Verificar visibilidad inicial tras cálculo
    assert vista.lbl_vacio_diseno.visible is False
    assert vista.panel_contenido_diseno.visible is True

    # Añadir capa mediante controlador y verificar sync en la lista de capas de la vista
    c.anadir_capa(recurso_svg)
    vista._sync_controlador_a_vista(c.get_view_model())
    assert len(vista.col_lista_capas.controls) == 1
    assert vista.panel_inspector_capa.visible is True

    # Simular cambios en campos del inspector
    vista.txt_pos_x.value = "10.0"
    vista.on_pos_x_change(None)
    sel = c.obtener_capa_seleccionada()
    assert sel.x == 10.0

    vista.slider_rotacion.value = 90
    vista.on_rotacion_change(None)
    assert sel.rotacion == 90.0

    vista.slider_opacidad.value = 0.5
    vista.on_opacidad_change(None)
    assert sel.opacidad == 0.5

    # Reflejo horizontal
    vista.on_reflejo_h_click(None)
    assert sel.reflejo_h is True
