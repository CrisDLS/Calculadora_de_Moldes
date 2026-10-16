"""Prueba de visibilidad y dimensiones de la capa fantasma en modo editar (Pestaña Diseño)."""

from pathlib import Path
from tempfile import TemporaryDirectory

import flet as ft
from PIL import Image
import pytest

from app_flet.vistas.trompo import VistaTrompo


class MockPage:
    def __init__(self):
        self.title = ""
        self.services = []
        self.controls = []
        self.overlay = []
        self.update_count = 0

    def update(self):
        self.update_count += 1

    def run_thread(self, fn, *args, **kwargs):
        fn(*args, **kwargs)


def _indice_en_stack(stack: ft.Stack, objetivo: ft.Control) -> int:
    """Devuelve el índice del control (o ancestro directo en stack) dentro de stack.controls."""

    def contiene(raiz: ft.Control, buscado: ft.Control) -> bool:
        if raiz is buscado:
            return True
        if hasattr(raiz, "controls") and isinstance(raiz.controls, list):
            for h in raiz.controls:
                if isinstance(h, ft.Control) and contiene(h, buscado):
                    return True
        if hasattr(raiz, "content") and isinstance(raiz.content, ft.Control):
            if contiene(raiz.content, buscado):
                return True
        return False

    for idx, ctrl in enumerate(stack.controls):
        if contiene(ctrl, objetivo):
            return idx
    return -1


@pytest.mark.parametrize("tipo_recurso", ["svg", "png"])
def test_capa_fantasma_visible_y_dimensionada_en_modo_editar(tipo_recurso):
    """Comprueba que en modo editar tanto capas SVG como PNG tienen capa fantasma visible y con medidas exactas."""
    with TemporaryDirectory() as td:
        tmp = Path(td)
        vista = VistaTrompo()
        page = MockPage()
        vista._page = page
        vista.on_calcular(None)

        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)
        vista.controlador.carpeta_recursos = rec_dir

        # Cargar capa SVG real de ejemplo y capa PNG
        ruta_svg = Path("docs/ejemplos/disenos/mosaico_geometrico.svg")
        assert ruta_svg.exists(), "Debe existir docs/ejemplos/disenos/mosaico_geometrico.svg"

        ruta_png = tmp / "flor_prueba.png"
        Image.new("RGBA", (240, 180), color=(220, 40, 90, 255)).save(ruta_png)

        capa_svg = vista.controlador.anadir_capa(str(ruta_svg))
        capa_png = vista.controlador.anadir_capa(str(ruta_png))

        # Configurar zona medida de ejemplo: 700x500
        pestana = vista.pestana_diseno
        gestor = pestana.gestor_visor
        gestor.visor.zona_medida = True
        gestor.visor.zona_ancho = 700.0
        gestor.visor.zona_alto = 500.0

        # Seleccionar la capa bajo prueba y activar modo editar
        capa_obj = capa_svg if tipo_recurso == "svg" else capa_png
        vista.controlador.capa_seleccionada_id = capa_obj.id
        vista._sync_controlador_a_vista(vista.controlador.get_view_model())

        exito = pestana.cambiar_modo_interaccion("editar")
        assert exito is True

        marco = gestor.marco_edicion
        caja_marco = marco.caja_marco
        fantasma = marco.img_preview

        # 1. El marco está dentro de la Stack superior (por encima del visor base)
        stack_visor = gestor.stack_visor
        idx_visor = _indice_en_stack(stack_visor, gestor.visor.img_svg)
        idx_fantasma = _indice_en_stack(stack_visor, fantasma)
        assert idx_visor >= 0, "El visor base debe estar en stack_visor"
        assert idx_fantasma > idx_visor, (
            f"La capa fantasma (idx={idx_fantasma}) debe estar POR ENCIMA del visor base (idx={idx_visor})"
        )

        # 2. Visibilidad y opacidad
        assert marco.stack.visible is True, "El stack del marco debe estar visible"
        assert caja_marco.visible is True, "El contenedor del marco debe estar visible"
        assert fantasma.visible is True, (
            f"Para capa {tipo_recurso}: fantasma.visible={fantasma.visible} (se esperaba True)"
        )
        assert fantasma.opacity is not None and fantasma.opacity > 0, (
            f"Para capa {tipo_recurso}: fantasma.opacity={fantasma.opacity} (se esperaba > 0)"
        )

        # 3. Contenido (src) no vacío
        src_val = fantasma.src
        assert src_val is not None and len(src_val) > 0, (
            f"Para capa {tipo_recurso}: fantasma.src está vacío"
        )

        # 4. Ancho y alto mayores que 0 y coincidentes (±1 px) con el marco
        assert fantasma.width is not None and fantasma.width > 0, (
            f"Para capa {tipo_recurso}: fantasma.width={fantasma.width} (se esperaba > 0)"
        )
        assert fantasma.height is not None and fantasma.height > 0, (
            f"Para capa {tipo_recurso}: fantasma.height={fantasma.height} (se esperaba > 0)"
        )
        assert abs(fantasma.width - caja_marco.width) <= 1.0, (
            f"Ancho fantasma ({fantasma.width}) != ancho marco ({caja_marco.width})"
        )
        assert abs(fantasma.height - caja_marco.height) <= 1.0, (
            f"Alto fantasma ({fantasma.height}) != alto marco ({caja_marco.height})"
        )

        # 5. Posición dentro de la zona (700x500)
        assert caja_marco.left is not None and 0.0 <= caja_marco.left < 700.0, (
            f"left={caja_marco.left} fuera de la zona [0, 700)"
        )
        assert caja_marco.top is not None and 0.0 <= caja_marco.top < 500.0, (
            f"top={caja_marco.top} fuera de la zona [0, 500)"
        )
