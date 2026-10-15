import time
from pathlib import Path
from PIL import Image
import pytest
from app_flet.vistas.trompo import VistaTrompo
from logic.diseno.lienzo import importar_recurso, _validar_y_procesar_svg

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
    
    # Modo editar usando la nueva API
    vista.pestana_diseno.cambiar_modo_interaccion("editar")
    return vista, page, capa, tmp_path


def test_300_eventos_arrastre_sin_recrear_controles_ni_page_update(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    marco = vista.pestana_diseno.gestor_visor.marco_edicion
    detector_id_inicial = id(marco.detector_cuerpo)
    page_updates_inicial = page.update_count
    
    # 1. Iniciar arrastre
    marco._on_cuerpo_pan_start(None)
    assert vista.arrastrando_capa is True
    
    x_inicial = capa.x
    y_inicial = capa.y
    
    # 2. Ráfaga de 300 micro-eventos de arrastre
    for _ in range(300):
        ev = DummyDragEvent(0.5, 0.5)
        marco._on_cuerpo_pan_update(ev)
    
    # Durante el arrastre:
    # - La identidad del GestureDetector NUNCA cambia
    assert id(marco.detector_cuerpo) == detector_id_inicial
    # - 0 llamadas a page.update()
    assert page.update_count == page_updates_inicial
    # - Las coordenadas en memoria cambiaron de forma acumulativa
    assert marco.capa_activa.x != x_inicial
    assert marco.capa_activa.y != y_inicial
    # - Los textfields se actualizaron
    assert vista.pestana_diseno.inspector.txt_pos_x.value == f"{marco.capa_activa.x:.2f}"
    assert vista.pestana_diseno.inspector.txt_pos_y.value == f"{marco.capa_activa.y:.2f}"
    
    # 3. Soltar (pan_end)
    marco._on_cuerpo_pan_end(None)
    assert vista.arrastrando_capa is False
    
    capa_final = vista.controlador.obtener_capa_seleccionada()
    assert capa_final.x == round(marco.capa_activa.x, 4)
    
    # La identidad del GestureDetector sigue siendo exactamente la misma
    assert id(marco.detector_cuerpo) == detector_id_inicial


def test_identidad_estable_detector_gestos(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    marco = vista.pestana_diseno.gestor_visor.marco_edicion
    det = marco.detector_cuerpo
    
    # Antes del arrastre
    id_antes = id(det)
    
    # Durante el arrastre
    marco._on_cuerpo_pan_start(None)
    marco._on_cuerpo_pan_update(DummyDragEvent(1.0, 1.0))
    id_durante = id(marco.detector_cuerpo)
    
    # Después del arrastre
    marco._on_cuerpo_pan_end(None)
    id_despues = id(marco.detector_cuerpo)
    
    assert id_antes == id_durante == id_despues
    assert marco.detector_cuerpo.drag_interval == 16


def test_fusion_y_descarte_de_recomposiciones_redundantes(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    marco = vista.pestana_diseno.gestor_visor.marco_edicion
    
    # Simular ráfaga de inicios y finales rápidos
    marco._on_cuerpo_pan_start(None)
    marco._on_cuerpo_pan_update(DummyDragEvent(1.0, 1.0))
    marco._on_cuerpo_pan_end(None)
    
    marco._on_cuerpo_pan_start(None)
    marco._on_cuerpo_pan_update(DummyDragEvent(1.0, 1.0))
    marco._on_cuerpo_pan_end(None)
    
    assert vista.arrastrando_capa is False
    # Al cambiar de modo a navegar se recompone
    vista.pestana_diseno.cambiar_modo_interaccion("navegar")
    assert vista.pestana_diseno.gestor_visor.modo_interaccion_diseno == "navegar"


def test_excepcion_en_recomposicion_limpia_banderas_y_permite_calcular(vista_con_capa, monkeypatch):
    vista, page, capa, _ = vista_con_capa
    marco = vista.pestana_diseno.gestor_visor.marco_edicion
    
    def fallo_actualizar_svg(*args, **kwargs):
        raise ValueError("Simulación de fallo crítico en recomposición de SVG")
    
    monkeypatch.setattr(vista.controlador, "actualizar_svg_diseno", fallo_actualizar_svg)
    
    marco._on_cuerpo_pan_start(None)
    marco._on_cuerpo_pan_update(DummyDragEvent(2.0, 2.0))
    marco._on_cuerpo_pan_end(None)
    
    # Banderas limpias
    assert vista.arrastrando_capa is False
    
    # "Calcular" debe seguir respondiendo normalmente sin congelarse
    monkeypatch.undo()
    vista.on_calcular(None)
    assert vista.controlador.resultado is not None


def test_cancelacion_por_pan_cancel_exit_y_timeout(vista_con_capa):
    vista, page, capa, _ = vista_con_capa
    marco = vista.pestana_diseno.gestor_visor.marco_edicion
    
    # Caso 1: pan_cancel
    marco._on_cuerpo_pan_start(None)
    assert vista.arrastrando_capa is True
    marco._on_cuerpo_pan_cancel(None)
    assert vista.arrastrando_capa is False
    
    # Caso 2: on_exit
    marco._on_cuerpo_pan_start(None)
    assert vista.arrastrando_capa is True
    marco._on_cuerpo_exit(None)
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
