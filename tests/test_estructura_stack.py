"""Prueba estructural del árbol de controles para componentes posicionados.

Verifica que cualquier control con propiedades de posicionamiento absoluto
(left, top, right, bottom) sea hijo DIRECTO de un ft.Stack (o resida en page.overlay),
según la regla estricta de composición de Flutter/Flet.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import flet as ft
import pytest
from PIL import Image

import scripts.demo_marco as dm
from app_flet.vistas.trompo import VistaTrompo


class MockWindow:
    width = 900
    height = 700


class MockPage:
    def __init__(self):
        self.title = ""
        self.window = MockWindow()
        self.padding = 0
        self.theme_mode = None
        self.controls = []
        self.overlay = []
        self.services = []
        self.update_count = 0

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.update_count += 1

    def run_thread(self, fn, *args, **kwargs):
        fn(*args, **kwargs)


def buscar_posicionados_invalidos(raiz, ruta=None, padre=None, overlay=None):
    """Recorre el árbol de controles buscando controles posicionados sin un Stack padre."""
    if overlay is None:
        overlay = []
    if ruta is None:
        ruta = [raiz.__class__.__name__]
    invalidos = []

    tiene_pos = (
        getattr(raiz, "left", None) is not None
        or getattr(raiz, "top", None) is not None
        or getattr(raiz, "right", None) is not None
        or getattr(raiz, "bottom", None) is not None
    )
    if tiene_pos:
        if not (isinstance(padre, ft.Stack) or raiz in overlay):
            invalidos.append({
                "ruta": " -> ".join(ruta),
                "control": raiz,
                "padre": padre,
                "padre_tipo": padre.__class__.__name__ if padre else "None",
                "left": getattr(raiz, "left", None),
                "top": getattr(raiz, "top", None),
                "right": getattr(raiz, "right", None),
                "bottom": getattr(raiz, "bottom", None),
            })

    hijos = []
    if hasattr(raiz, "controls") and isinstance(raiz.controls, list):
        hijos.extend([c for c in raiz.controls if isinstance(c, ft.Control)])
    if hasattr(raiz, "content") and isinstance(raiz.content, ft.Control):
        hijos.append(raiz.content)
    for attr in ["leading", "title", "trailing", "actions", "tabs"]:
        val = getattr(raiz, attr, None)
        if isinstance(val, ft.Control):
            hijos.append(val)
        elif isinstance(val, list):
            hijos.extend([x for x in val if isinstance(x, ft.Control)])

    for h in hijos:
        sub_ruta = ruta + [h.__class__.__name__]
        invalidos.extend(buscar_posicionados_invalidos(h, sub_ruta, raiz, overlay))
    return invalidos


def test_posicionamiento_stack_pestana_diseno():
    """Verifica que en pestaña Diseño (modo editar con capa) todos los controles con left/top son hijos directos de ft.Stack."""
    with TemporaryDirectory() as td:
        tmp = Path(td)
        vista = VistaTrompo()
        page = MockPage()
        vista._page = page
        vista.on_calcular(None)

        img_path = tmp / "cuadrado.png"
        Image.new("RGBA", (200, 200), color=(0, 128, 255, 255)).save(img_path)
        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)
        vista.controlador.carpeta_recursos = rec_dir

        capa = vista.controlador.anadir_capa(str(img_path))
        vista.controlador.capa_seleccionada_id = capa.id
        vista._sync_controlador_a_vista(vista.controlador.get_view_model())

        pestana = vista.pestana_diseno
        gestor = pestana.gestor_visor
        gestor.visor.zona_medida = True
        gestor.visor.zona_ancho = 800.0
        gestor.visor.zona_alto = 600.0

        pestana.cambiar_modo_interaccion("editar")

        arbol = pestana.construir()
        invalidos = buscar_posicionados_invalidos(arbol, overlay=page.overlay)

        if invalidos:
            msg_lineas = [f"Se encontraron {len(invalidos)} controles posicionados fuera de ft.Stack:"]
            for inv in invalidos:
                msg_lineas.append(
                    f"  - Ruta: {inv['ruta']} (Padre: {inv['padre_tipo']}) "
                    f"[left={inv['left']}, top={inv['top']}]"
                )
            pytest.fail("\n".join(msg_lineas))


def test_posicionamiento_stack_demo_marco():
    """Verifica que en demo_marco (modo editar) todos los controles con left/top son hijos directos de ft.Stack."""
    page = MockPage()
    dm.main(page)

    sel_modo = page.controls[0].controls[1]
    sel_modo.selected = ["editar"]
    sel_modo.on_change(None)

    invalidos = []
    for c in page.controls:
        invalidos.extend(buscar_posicionados_invalidos(c, overlay=page.overlay))

    if invalidos:
        msg_lineas = [f"Se encontraron {len(invalidos)} controles posicionados fuera de ft.Stack en demo_marco:"]
        for inv in invalidos:
            msg_lineas.append(
                f"  - Ruta: {inv['ruta']} (Padre: {inv['padre_tipo']}) "
                f"[left={inv['left']}, top={inv['top']}]"
            )
        pytest.fail("\n".join(msg_lineas))


def test_elementos_visibles_en_modo_editar():
    """Verifica que en modo editar con capa existen en el árbol el visor base, capa fantasma, marco y 8 tiradores."""
    with TemporaryDirectory() as td:
        tmp = Path(td)
        vista = VistaTrompo()
        page = MockPage()
        vista._page = page
        vista.on_calcular(None)

        img_path = tmp / "cuadrado.png"
        Image.new("RGBA", (200, 200), color=(0, 128, 255, 255)).save(img_path)
        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)
        vista.controlador.carpeta_recursos = rec_dir

        capa = vista.controlador.anadir_capa(str(img_path))
        vista.controlador.capa_seleccionada_id = capa.id
        vista._sync_controlador_a_vista(vista.controlador.get_view_model())

        pestana = vista.pestana_diseno
        gestor = pestana.gestor_visor
        gestor.visor.zona_medida = True
        gestor.visor.zona_ancho = 800.0
        gestor.visor.zona_alto = 600.0

        pestana.cambiar_modo_interaccion("editar")

        marco = gestor.marco_edicion
        assert marco.stack.visible is True
        assert marco.caja_marco.visible is True
        assert marco.img_preview.visible is True  # Imagen raster cargada visible dentro del marco
        assert gestor.img_svg.src != ""  # Visor SVG base cargado

        tiradores_visibles = [tid for tid, cont in marco.tiradores_controles.items() if cont.visible]
        assert len(tiradores_visibles) == 8, f"Se esperaban 8 tiradores visibles, hay {len(tiradores_visibles)}"
