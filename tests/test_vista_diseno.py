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
    assert sel.x == pytest.approx(-sel.ancho / 2.0, abs=1e-3)

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

    # Con esquema por defecto (repetición), 'mitad' no se permite y queda en 'completo'
    c.cambiar_diseno_lienzo_modo("mitad")
    assert c.diseno_lienzo_modo == "completo"

    # Con esquema simétrico (central_espejo), 'mitad' es permitido
    c.cambiar_esquema_seccion("inferior", "central_espejo", 5)
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


def _parsear_puntos_path_svg(d: str):
    import re
    pares = re.findall(r"([-+]?\d+(?:\.\d+)?),([-+]?\d+(?:\.\d+)?)", d)
    return [(float(x), float(y)) for x, y in pares]


def test_lienzo_pico_una_sola_cara_misma_caja_y_clippath(controlador_calculado):
    import re
    import defusedxml.ElementTree as ET
    from logic.geometria.malla_trompo import construir_malla
    from logic.geometria.textura import mapear_textura, svg_textura
    from logic.exportacion.svg_abanico import calcular_parametros_proyeccion_abanico

    c = controlador_calculado
    malla = construir_malla(c.entrada_actual, c.resultado)
    mapa = mapear_textura(
        entrada=c.entrada_actual,
        resultado=c.resultado,
        malla=malla,
        configuraciones=c.config_secciones,
        disenos=c.disenos,
    )

    for var in ("A", "B"):
        clave = f"pico_{var}"
        c.cambiar_diseno_seccion("pico", var)
        c.cambiar_diseno_ver_rotulos(True)
        svg_diseno = c.svg_diseno

        # El lienzo SVG del pico en Diseño debe contener 1 sola cara (1 eje, 0 aristas internas, rótulo Cara 1)
        caras_rotuladas = re.findall(r"Cara \d+", svg_diseno)
        ejes_gajo = re.findall(r'id="eje-gajo-\d+"', svg_diseno)
        aristas_comunes = re.findall(r'id="arista-comun-\d+"', svg_diseno)
        assert caras_rotuladas == ["Cara 1"], f"Variante {var} esperaba ['Cara 1'], obtuvo {caras_rotuladas}"
        assert len(ejes_gajo) == 1
        assert len(aristas_comunes) == 0

        # Misma caja envolvente que svg_textura / mapear_textura
        vmin_x, vmin_y, vmax_x, vmax_y = c.ventana_lienzo()
        caja_ventana = (vmin_x, vmin_y, vmax_x - vmin_x, vmax_y - vmin_y)
        caja_tex = mapa.texturas[clave].caja_cm
        assert caja_ventana == pytest.approx(caja_tex, abs=1e-6)

        geom = calcular_parametros_proyeccion_abanico(
            resultado=c.resultado,
            entrada=c.entrada_actual,
            seccion="pico",
            hoja=c.hoja_tipo,
            dibujar="completo",
            modo_diseno=True,
        )
        assert geom["n"] == 1
        caja_geom = (geom["min_x_cm"], geom["min_y_cm"], geom["w_cm"], geom["h_cm"])
        assert caja_geom == pytest.approx(caja_tex, abs=1e-6)

        # Mismo clipPath (en cm) que svg_textura para el pico
        svg_tex = svg_textura(
            clave=clave,
            entrada=c.entrada_actual,
            resultado=c.resultado,
            diseno=c.obtener_diseno_activo(),
            config_seccion=c.obtener_config_seccion("pico"),
        )
        root_dis = ET.fromstring(svg_diseno.encode("utf-8"))
        root_tex = ET.fromstring(svg_tex.encode("utf-8"))

        ns = {"svg": "http://www.w3.org/2000/svg"}
        path_clip_dis = root_dis.find(".//svg:clipPath[@id='clip-abanico']/svg:path", ns)
        path_clip_tex = root_tex.find(".//svg:clipPath[@id='clip-textura']/svg:path", ns)
        assert path_clip_dis is not None and path_clip_tex is not None

        pts_dis_svg = _parsear_puntos_path_svg(path_clip_dis.attrib["d"])
        pts_tex_svg = _parsear_puntos_path_svg(path_clip_tex.attrib["d"])
        assert len(pts_dis_svg) == len(pts_tex_svg) == 4

        # Convertir puntos de clip-abanico (mm de página) a cm del lienzo y comparar con clip-textura (cm con y invertido)
        factor = geom["factor"]
        cx_page = geom["cx_page"]
        cy_page = geom["cy_page"]
        y_mid_cm = geom["y_mid_cm"]
        pts_dis_cm = [((xs - cx_page) / factor, y_mid_cm - (ys - cy_page) / factor) for xs, ys in pts_dis_svg]
        pts_tex_cm = [(xt, -yt) for xt, yt in pts_tex_svg]

        for (xd, yd), (xt, yt) in zip(pts_dis_cm, pts_tex_cm):
            assert xd == pytest.approx(xt, abs=1e-2)
            assert yd == pytest.approx(yt, abs=1e-2)

    # Verificar que el interruptor "Lienzo completo / Mitad (espejo)" se oculta en pico y es visible en conos
    vista = VistaTrompo()
    vista.controlador = c
    c.cambiar_diseno_seccion("pico", "A")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is False

    c.cambiar_diseno_seccion("superior")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is True

    c.cambiar_diseno_seccion("inferior")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is True

    # Función única que decide el número de caras
    from logic.geometria.textura import num_caras_lienzo
    assert num_caras_lienzo("pico") == 1
    assert num_caras_lienzo("pico_A") == 1
    assert num_caras_lienzo("pico_B") == 1


def test_proyectos_viejos_intactos_al_abrir():
    import hashlib
    import json

    raiz = Path(__file__).resolve().parent.parent
    rutas = [
        raiz / "guardados" / "recursos_temp" / "prueba_imagen.json",
        raiz / "docs" / "ejemplos" / "disenos" / "ejemplo_espejo_12.json",
    ]
    rutas_existentes = [r for r in rutas if r.exists()]
    assert len(rutas_existentes) == 2

    for ruta in rutas_existentes:
        bytes_antes = ruta.read_bytes()
        sha_antes = hashlib.sha256(bytes_antes).hexdigest()
        datos_orig = json.loads(bytes_antes.decode("utf-8"))
        disenos_orig = datos_orig.get("disenos", {})

        c = ControladorTrompo()
        ok, msg = c.abrir(str(ruta))
        assert ok is True, f"Error abriendo {ruta.name}: {msg}"

        # Verificar que ninguna capa fue borrada ni movida
        for clave, d_dict in disenos_orig.items():
            capas_orig = d_dict.get("capas", [])
            assert clave in c.disenos
            capas_cargadas = c.disenos[clave].capas
            assert len(capas_cargadas) == len(capas_orig)
            for c_orig, c_carg in zip(capas_orig, capas_cargadas):
                assert c_carg.id == c_orig["id"]
                assert c_carg.x == pytest.approx(c_orig["x"], abs=1e-9)
                assert c_carg.y == pytest.approx(c_orig["y"], abs=1e-9)
                assert c_carg.ancho == pytest.approx(c_orig["ancho"], abs=1e-9)
                assert c_carg.alto == pytest.approx(c_orig["alto"], abs=1e-9)
                assert c_carg.rotacion == pytest.approx(c_orig.get("rotacion", 0.0), abs=1e-9)

        # Cambiar a sección pico A y B y verificar que renderiza sin error y sin tocar coordenadas
        c.cambiar_diseno_seccion("pico", "A")
        assert "<svg" in c.svg_diseno
        c.cambiar_diseno_seccion("pico", "B")
        assert "<svg" in c.svg_diseno

        for clave, d_dict in disenos_orig.items():
            for c_orig, c_carg in zip(d_dict.get("capas", []), c.disenos[clave].capas):
                assert c_carg.x == pytest.approx(c_orig["x"], abs=1e-9)
                assert c_carg.y == pytest.approx(c_orig["y"], abs=1e-9)
                assert c_carg.ancho == pytest.approx(c_orig["ancho"], abs=1e-9)
                assert c_carg.alto == pytest.approx(c_orig["alto"], abs=1e-9)

        # Confirmar que el archivo .json en disco no cambió
        sha_despues = hashlib.sha256(ruta.read_bytes()).hexdigest()
        assert sha_despues == sha_antes




