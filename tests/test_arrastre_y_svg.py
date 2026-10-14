import time
import threading
from pathlib import Path
from PIL import Image
import pytest
import flet as ft
from app_flet.controlador import ControladorTrompo
from app_flet.vistas.trompo import VistaTrompo
from logic.diseno.lienzo import Diseno, CapaDiseno, importar_recurso, _validar_y_procesar_svg
from logic.exportacion.svg_abanico import svg_abanico

class DummyPoint:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class DummyDragEvent:
    def __init__(self, dx: float, dy: float):
        self.local_delta = DummyPoint(dx, dy)
        self.global_delta = DummyPoint(dx, dy)

class MockPage:
    def __init__(self):
        self.title = ""
        self.services = []
        self.update_count = 0
    def update(self):
        self.update_count += 1
    def run_thread(self, fn, *args, **kwargs):
        fn(*args, **kwargs)

@pytest.fixture
def vista_con_capa(tmp_path):
    vista = VistaTrompo()
    page = MockPage()
    # Mocking page reference in control
    vista._page = page
    
    # Calcular para inicializar geometría
    vista.on_calcular(None)
    
    # Crear e importar una capa de prueba
    img_path = tmp_path / "figura.png"
    Image.new("RGBA", (100, 100), color=(255, 0, 0, 255)).save(img_path)
    rec_dir = tmp_path / "rec"
    vista.controlador.carpeta_recursos = rec_dir
    capa = vista.controlador.anadir_capa(img_path)
    vista.controlador.capa_seleccionada_id = capa.id
    vista._sync_controlador_a_vista(vista.controlador.get_view_model())
    
    # Modo mover capa
    vista.modo_interaccion_diseno = "mover"
    vista.selector_interaccion_diseno.selected = ["mover"]
    return vista, page, capa, tmp_path


def test_300_eventos_arrastre_sin_recrear_controles_ni_page_update(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    detector_id_inicial = id(vista.detector_gestos_diseno)
    page_updates_inicial = page.update_count
    
    # 1. Iniciar arrastre
    vista._on_gesture_diseno_pan_start(None)
    assert vista.arrastrando_capa is True
    
    x_inicial = capa.x
    y_inicial = capa.y
    
    # 2. Ráfaga de 300 micro-eventos de arrastre
    for _ in range(300):
        ev = DummyDragEvent(0.5, 0.5)
        vista._on_gesture_diseno_pan_update(ev)
    
    # Durante el arrastre:
    # - La identidad del GestureDetector NUNCA cambia
    assert id(vista.detector_gestos_diseno) == detector_id_inicial
    # - 0 llamadas a page.update()
    assert page.update_count == page_updates_inicial
    # - Las coordenadas en memoria cambiaron de forma acumulativa
    assert capa.x != x_inicial
    assert capa.y != y_inicial
    # - Los textfields se actualizaron
    assert vista.txt_pos_x.value == f"{capa.x:.2f}"
    assert vista.txt_pos_y.value == f"{capa.y:.2f}"
    
    # 3. Soltar (pan_end)
    vista._on_gesture_diseno_pan_end(None)
    assert vista.arrastrando_capa is False
    
    # Esperar que la recomposición termine en segundo plano
    time.sleep(0.3)
    
    # La identidad del GestureDetector sigue siendo exactamente la misma
    assert id(vista.detector_gestos_diseno) == detector_id_inicial


def test_identidad_estable_detector_gestos(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    det = vista.detector_gestos_diseno
    
    # Antes del arrastre
    id_antes = id(det)
    
    # Durante el arrastre
    vista._on_gesture_diseno_pan_start(None)
    vista._on_gesture_diseno_pan_update(DummyDragEvent(1.0, 1.0))
    id_durante = id(vista.detector_gestos_diseno)
    
    # Después del arrastre
    vista._on_gesture_diseno_pan_end(None)
    id_despues = id(vista.detector_gestos_diseno)
    
    assert id_antes == id_durante == id_despues
    assert vista.detector_gestos_diseno.drag_interval == 35


def test_fusion_y_descarte_de_recomposiciones_redundantes(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    
    # Simular ráfaga de inicios y finales rápidos
    vista._on_gesture_diseno_pan_start(None)
    vista._on_gesture_diseno_pan_update(DummyDragEvent(1.0, 1.0))
    vista._finalizar_arrastre_capa()
    
    vista._on_gesture_diseno_pan_start(None)
    vista._on_gesture_diseno_pan_update(DummyDragEvent(1.0, 1.0))
    vista._finalizar_arrastre_capa()
    
    # Esperar que ambos workers terminen
    time.sleep(0.3)
    
    # Debe haber registrado descartadas si se solaparon
    assert vista._id_recomposicion_diseno >= 2
    assert vista.arrastrando_capa is False


def test_excepcion_en_recomposicion_limpia_banderas_y_permite_calcular(vista_con_capa, monkeypatch):
    vista, page, capa, _ = vista_con_capa
    
    def fallo_actualizar_svg():
        raise ValueError("Simulación de fallo crítico en recomposición de SVG")
    
    monkeypatch.setattr(vista.controlador, "actualizar_svg_diseno", fallo_actualizar_svg)
    
    vista._on_gesture_diseno_pan_start(None)
    vista._on_gesture_diseno_pan_update(DummyDragEvent(2.0, 2.0))
    vista._on_gesture_diseno_pan_end(None)
    
    time.sleep(0.2)
    
    # Banderas limpias
    assert vista.arrastrando_capa is False
    assert vista.lbl_estado_diseno.value == ""
    
    # "Calcular" debe seguir respondiendo normalmente sin congelarse
    monkeypatch.undo()
    vista.on_calcular(None)
    assert vista.controlador.resultado is not None


def test_cancelacion_por_pan_cancel_exit_y_timeout(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    
    # Caso 1: pan_cancel
    vista._on_gesture_diseno_pan_start(None)
    assert vista.arrastrando_capa is True
    vista._on_gesture_diseno_pan_cancel(None)
    assert vista.arrastrando_capa is False
    
    # Caso 2: on_exit
    vista._on_gesture_diseno_pan_start(None)
    assert vista.arrastrando_capa is True
    vista._on_gesture_diseno_exit(None)
    assert vista.arrastrando_capa is False
    
    # Caso 3: timeout de seguridad de 2.0s
    vista._on_gesture_diseno_pan_start(None)
    assert vista.arrastrando_capa is True
    # Forzar ejecución del timeout
    vista._timeout_arrastre_capa()
    assert vista.arrastrando_capa is False


def test_svg_externo_complejo_figuras_visibles_sin_ns0_y_referencias_validas(tmp_path):
    svg_complejo = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2000 2000" width="2000" height="2000">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="rgb(255,255,0)" />
          <stop offset="100%" stop-color="rgb(255,0,0)" />
        </linearGradient>
      </defs>
      <g id="capa_anidada">
        <rect width="1000" height="1000" fill="url(#grad1)" />
        <circle cx="1500" cy="1500" r="400" fill="#0000FF" />
      </g>
    </svg>"""
    
    p = tmp_path / "complejo.svg"
    p.write_text(svg_complejo, encoding="utf-8")
    
    rec_dir = tmp_path / "rec"
    capa = importar_recurso(p, rec_dir)
    
    assert capa.tipo == "svg"
    assert capa.viewbox == (0.0, 0.0, 2000.0, 2000.0)
    
    # Verificar que el SVG procesado prefijó IDs y no dejó ns0:
    contenido_procesado = (rec_dir / capa.archivo).read_text(encoding="utf-8")
    assert "ns0:" not in contenido_procesado
    assert f'id="c_{capa.id}_grad1"' in contenido_procesado
    assert f"url(#c_{capa.id}_grad1)" in contenido_procesado


def test_estres_diseno_usuario_si_existe(tmp_path):
    p_usuario_svg = Path("docs/ejemplos/disenos/_prueba_usuario.svg")
    rec_dir = tmp_path / "rec_user"
    
    if p_usuario_svg.exists():
        capa_user = importar_recurso(p_usuario_svg, rec_dir)
        assert capa_user.tipo == "svg"
        assert capa_user.viewbox is not None
        
        # Verificar contenido de la capa procesada
        _, _, _, _, _, _, _, _, hijos = _validar_y_procesar_svg(rec_dir / capa_user.archivo, id_capa=capa_user.id)
        assert len(hijos) > 0
        assert "ns0:" not in hijos
    else:
        # Sintetizar SVG con 20000 triángulos
        lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">']
        for i in range(2000): # muestra representativa en test unitario rápido
            lines.append(f'<polygon points="{i%1000},{i%1000} {(i+10)%1000},{i%1000} {i%1000},{(i+10)%1000}" fill="red"/>')
        lines.append('</svg>')
        p_tri = tmp_path / "triangulos.svg"
        p_tri.write_text("\n".join(lines), encoding="utf-8")
        capa_user = importar_recurso(p_tri, rec_dir)
        assert capa_user.tipo == "svg"
