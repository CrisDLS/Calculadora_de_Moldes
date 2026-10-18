from app_flet.controlador import ControladorTrompo
from app_flet.vistas.trompo import VistaTrompo

class MockClipboard:
    def __init__(self):
        self.text = ""
    def set(self, text):
        self.text = text

class MockFilePicker:
    pass

def test_controlador_vista_3d_y_compra():
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    vm = c.calcular()

    assert vm.items_compra is not None
    assert len(vm.items_compra) > 0
    # Por defecto blanco y amarillo
    colores_ids = [it.color.id for it in vm.items_compra]
    assert "blanco" in colores_ids
    assert "amarillo" in colores_ids

    total_pliegos = sum(it.pliegos for it in vm.items_compra)
    assert total_pliegos > 0

    # Servidor 3D
    servidor = c.obtener_servidor_3d()
    assert servidor is not None
    assert servidor.url.startswith("http://127.0.0.1:")
    
    vm2 = c.get_view_model()
    assert vm2.url_visor_3d == servidor.url

    # Actualizar pintura
    c.actualizar_pintura(color_sup="rojo", color_pic="azul_rey", color_inf="verde_limon")
    assert c.pintura.color_superior == "rojo"
    assert c.pintura.color_pico == "azul_rey"
    assert c.pintura.color_inferior == "verde_limon"
    assert c.sin_guardar is True

    vm3 = c.get_view_model()
    colores_ids_nuevos = [it.color.id for it in vm3.items_compra]
    assert "rojo" in colores_ids_nuevos
    assert "azul_rey" in colores_ids_nuevos
    assert "verde_limon" in colores_ids_nuevos

def test_vista_trompo_componentes_3d():
    mock_clip = MockClipboard()
    mock_fp = MockFilePicker()
    vista = VistaTrompo(servicio_clipboard=mock_clip, servicio_file_picker=mock_fp)

    # Inicialmente visible el aviso de vacío para 3D
    assert vista.lbl_vacio_3d.visible is True
    assert vista.panel_contenido_3d.visible is False

    # Calcular
    vista.on_calcular(None)

    assert vista.lbl_vacio_3d.visible is False
    assert vista.panel_contenido_3d.visible is True
    assert len(vista.tabla_compra.rows) > 0

    # Copiar lista de compra
    vista.on_copiar_lista_compra(None)
    assert "Color\tMarca\tCódigo\tSuperior\tPico" in mock_clip.text
    assert "Blanco" in mock_clip.text
    assert "\tPaquetes" in mock_clip.text

    # Cambiar modo de superior a alternado y color a rosa_mexicano
    vista.dd_modo_sup.value = "alternado"
    vista.on_cambio_patron_ui(None)
    vista.on_cambio_color_ciclo_sup(0, "rosa_mexicano")
    assert vista.controlador.pintura.color_superior == "rosa_mexicano"
    assert any("Rosa mexicano" in row.cells[0].content.value for row in vista.tabla_compra.rows)


def test_interruptor_mostrar_diseno_3d():
    mock_clip = MockClipboard()
    mock_fp = MockFilePicker()
    vista = VistaTrompo(servicio_clipboard=mock_clip, servicio_file_picker=mock_fp)

    # Abrir proyecto con diseño visible (prueba_imagen.json)
    ok, msg = vista.controlador.abrir("guardados/recursos_temp/prueba_imagen.json")
    assert ok is True
    vista._sync_controlador_a_vista(vista.controlador.get_view_model())

    srv = vista.controlador.obtener_servidor_3d()

    # 1. Por defecto, interruptor encendido (value=True) y habilitado (disabled=False porque hay capas visibles)
    sw = vista.pestana_vista3d.sw_mostrar_diseno_3d
    assert sw.value is True
    assert sw.disabled is False
    assert vista.controlador.mostrar_diseno_3d is True

    # Escena en el servidor debe tener texturas y caras con "uv"
    escena_on = srv.obtener_datos_escena()
    assert len(escena_on.get("texturas", {})) > 0
    assert any("uv" in cara for cara in escena_on.get("caras", []))

    # 2. Apagar el interruptor a través del evento del widget
    sw.value = False
    vista.pestana_vista3d.on_toggle_mostrar_diseno_3d(None)

    # El cambio llega al servidor al instante, sin pulsar Calcular ni recargar
    assert vista.controlador.mostrar_diseno_3d is False
    escena_off = srv.obtener_datos_escena()
    assert escena_off.get("texturas") == {}
    assert not any("uv" in cara for cara in escena_off.get("caras", []))

    # 3. Volver a encender
    sw.value = True
    vista.pestana_vista3d.on_toggle_mostrar_diseno_3d(None)

    escena_on2 = srv.obtener_datos_escena()
    assert len(escena_on2.get("texturas", {})) > 0
    assert any("uv" in cara for cara in escena_on2.get("caras", []))

    # 4. Deshabilitado si no hay capas visibles de diseño
    vista_vacia = VistaTrompo(servicio_clipboard=mock_clip, servicio_file_picker=mock_fp)
    vista_vacia.on_calcular(None)
    sw_vacio = vista_vacia.pestana_vista3d.sw_mostrar_diseno_3d
    assert sw_vacio.disabled is True

