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
            dibujar="una_cara",
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

    # Verificar que el interruptor es visible en pico (con opciones 'Una cara' | 'Lienzo completo') y en conos
    vista = VistaTrompo()
    vista.controlador = c
    c.cambiar_diseno_seccion("pico", "A")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is True
    assert [s.value for s in vista.selector_lienzo_diseno.segments] == ["una_cara", "mitad", "completo"]
    assert [s.label.value for s in vista.selector_lienzo_diseno.segments] == ["Una cara", "Mitad (espejo)", "Lienzo completo"]

    c.cambiar_diseno_seccion("superior")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is True
    assert [s.value for s in vista.selector_lienzo_diseno.segments] == ["completo", "mitad"]
    assert [s.label.value for s in vista.selector_lienzo_diseno.segments] == ["Lienzo completo", "Mitad (espejo)"]

    c.cambiar_diseno_seccion("inferior")
    vista._sync_controlador_a_vista(c.get_view_model())
    assert vista.selector_lienzo_diseno.visible is True
    assert [s.value for s in vista.selector_lienzo_diseno.segments] == ["completo", "mitad"]

    # Función única que decide el número de caras
    from logic.geometria.textura import num_caras_lienzo
    assert num_caras_lienzo("pico", dibujar="una_cara") == 1
    assert num_caras_lienzo("pico", dibujar="completo") == 4
    assert num_caras_lienzo("pico_A", dibujar="una_cara") == 1
    assert num_caras_lienzo("pico_B", dibujar="una_cara") == 1


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


def test_lienzo_completo_pico_4_caras_identicas_y_sin_replicas_en_json(tmp_path):
    """
    Comprueba que:
    1. En 'Una cara', el lienzo del pico muestra 1 sola cara.
    2. En 'Lienzo completo', el pico muestra 4 caras ('Cara 1'..'Cara 4').
    3. Cada una de las 4 caras en 'Lienzo completo' es idéntica a la cara única
       tras girarla a la posición vertical (comparación de píxeles < 2% diferencia).
    4. El proyecto guardado en JSON NO almacena ninguna réplica (solo la capa original).
    """
    import io
    import math
    import re
    import numpy as np
    from PIL import Image
    from playwright.sync_api import sync_playwright
    from logic.diseno.lienzo import CapaDiseno
    from logic.exportacion.svg_abanico import calcular_parametros_proyeccion_abanico

    c = ControladorTrompo()
    c.altura = "950"
    c.num_gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    c.calcular()

    c.cambiar_diseno_seccion("pico", "A")

    # Agregar diseño asimétrico sobre la cara del pico
    capa = CapaDiseno(
        id="capa_asimetrica_pico",
        nombre="Capa Asimétrica",
        tipo="svg",
        archivo="triangulo.svg",
        ancho_natural=20.0,
        alto_natural=30.0,
        x=2.0,
        y=20.0,
        ancho=12.0,
        alto=16.0,
        rotacion=10.0,
    )
    # Crear archivo SVG temporal para la capa
    from logic.diseno.lienzo import limpiar_cache_fragmentos
    limpiar_cache_fragmentos()
    svg_archivo = tmp_path / "triangulo.svg"
    svg_archivo.write_text(
        '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        '<polygon points="10,10 90,20 40,90" fill="#E91E63"/>'
        '</svg>',
        encoding="utf-8",
    )
    c.carpeta_recursos_proyecto = str(tmp_path)
    dis_pico = c.obtener_diseno_activo()
    dis_pico.capas = [capa]
    c.cambiar_diseno_ver_rotulos(True)

    # 1. Modo "Una cara": debe tener 1 sola cara
    c.cambiar_diseno_lienzo_modo("una_cara")
    svg_una_cara = c.svg_diseno
    caras_una = re.findall(r'Cara \d+', svg_una_cara)
    assert caras_una == ["Cara 1"], f"Se esperaba ['Cara 1'], se obtuvo {caras_una}"

    # 2. Modo "Lienzo completo": debe tener 4 caras
    c.cambiar_diseno_lienzo_modo("completo")
    svg_completo = c.svg_diseno
    caras_comp = re.findall(r'Cara \d+', svg_completo)
    assert caras_comp == ["Cara 1", "Cara 2", "Cara 3", "Cara 4"], (
        f"Se esperaba ['Cara 1', 'Cara 2', 'Cara 3', 'Cara 4'], se obtuvo {caras_comp}"
    )

    # 3. Comparación de píxeles tras girar cada una de las 4 caras
    # Usamos una escala fija para que las dimensiones en mm/página sean idénticas
    geom_una = calcular_parametros_proyeccion_abanico(
        resultado=c.resultado,
        entrada=c.entrada_actual,
        seccion="pico",
        hoja="carta",
        escala=10.0,
        dibujar="una_cara",
        modo_diseno=True,
    )
    geom_comp = calcular_parametros_proyeccion_abanico(
        resultado=c.resultado,
        entrada=c.entrada_actual,
        seccion="pico",
        hoja="carta",
        escala=10.0,
        dibujar="completo",
        modo_diseno=True,
    )

    from logic.exportacion.svg_abanico import svg_abanico
    svg_u_fixed = svg_abanico(
        resultado=c.resultado,
        entrada=c.entrada_actual,
        seccion="pico",
        escala=10.0,
        hoja="carta",
        dibujar="una_cara",
        diseno=dis_pico,
        carpeta_recursos=tmp_path,
        ver_cuadricula=False,
        ver_rotulos=False,
        ver_costuras=False,
    )
    svg_c_fixed = svg_abanico(
        resultado=c.resultado,
        entrada=c.entrada_actual,
        seccion="pico",
        escala=10.0,
        hoja="carta",
        dibujar="completo",
        diseno=dis_pico,
        carpeta_recursos=tmp_path,
        ver_cuadricula=False,
        ver_rotulos=False,
        ver_costuras=False,
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1400})

        page.set_content(f'<body style="margin:0;padding:0;background:#ffffff;"><div id="cont_u" style="display:inline-block;">{svg_u_fixed}</div></body>')
        img_u_bytes = page.locator("#cont_u").screenshot()
        img_u = Image.open(io.BytesIO(img_u_bytes)).convert("RGB")

        page.set_content(f'<body style="margin:0;padding:0;background:#ffffff;"><div id="cont_c" style="display:inline-block;">{svg_c_fixed}</div></body>')
        img_c_bytes = page.locator("#cont_c").screenshot()
        img_c = Image.open(io.BytesIO(img_c_bytes)).convert("RGB")

        browser.close()

    # Apex en coordenadas de imagen (w_page, h_page en Carta)
    factor_px_u = img_u.width / geom_una["w_page"]
    apex_u_px = (geom_una["cx_page"] * factor_px_u, (geom_una["cy_page"] + geom_una["y_mid_cm"] * geom_una["factor"]) * factor_px_u)

    factor_px_c = img_c.width / geom_comp["w_page"]
    apex_c_px = (geom_comp["cx_page"] * factor_px_c, (geom_comp["cy_page"] + geom_comp["y_mid_cm"] * geom_comp["factor"]) * factor_px_c)

    psi = geom_comp["pieza"].angulo_abertura_rad
    arr_u = np.array(img_u)

    # Mascara de la cara vertical única: píxeles con color del diseño (descartando blanco y líneas monocromáticas)
    from PIL import ImageFilter
    arr_u_int = arr_u.astype(int)
    sat = (
        np.abs(arr_u_int[:, :, 0] - arr_u_int[:, :, 1])
        + np.abs(arr_u_int[:, :, 1] - arr_u_int[:, :, 2])
        + np.abs(arr_u_int[:, :, 2] - arr_u_int[:, :, 0])
    )
    mascara_diseno = sat > 30
    # Erosión morfológica de 3 px para evitar diferencias por suavizado (anti-aliasing) y remuestreo de rotación en los bordes
    mask_im = Image.fromarray((mascara_diseno * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7))
    mascara_cara = np.array(mask_im) > 0
    assert np.sum(mascara_cara) > 50, "La cara de referencia no contiene diseño visible suficiente"

    # Alineación subpíxel exacta del lienzo completo al ápice de la cara única
    dx = apex_u_px[0] - apex_c_px[0]
    dy = apex_u_px[1] - apex_c_px[1]
    matriz_afine = (1.0, 0.0, -dx, 0.0, 1.0, -dy)
    img_c_alineado = img_c.transform(img_u.size, Image.AFFINE, matriz_afine, resample=Image.BICUBIC, fillcolor=(255, 255, 255))

    pcts = []
    for i in range(4):
        theta_i = (i - 1.5) * psi
        deg_rot = math.degrees(theta_i)

        # Rotar la cara i para alinearla verticalmente con la cara única
        img_i_rot = img_c_alineado.rotate(deg_rot, center=apex_u_px, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
        arr_i = np.array(img_i_rot)

        diff = np.sum(np.abs(arr_u[mascara_cara].astype(int) - arr_i[mascara_cara].astype(int)), axis=1)
        pct_dist = (np.sum(diff > 30) / len(diff)) * 100.0
        pcts.append(pct_dist)

    for i, pct in enumerate(pcts):
        assert pct < 2.0, f"Cara {i+1} difiere {pct:.2f}% de la cara única (máx 2%)"

    # 4. Comprobar que en el JSON no se almacena ninguna réplica
    from dataclasses import asdict
    datos_proy = asdict(c.a_proyecto())
    capas_guardadas = datos_proy["disenos"]["pico_A"]["capas"]
    assert len(capas_guardadas) == 1
    assert capas_guardadas[0]["id"] == "capa_asimetrica_pico"
    assert "reflejo" not in capas_guardadas[0]["id"]





SVG_ASIMETRICO_PICO = (
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="0" y="0" width="100" height="100" fill="#FFEB3B"/>'
    '<rect x="0" y="0" width="35" height="35" fill="#1565C0"/>'
    '<polygon points="10,40 90,20 60,95" fill="#E91E63"/>'
    '<circle cx="80" cy="80" r="12" fill="#2E7D32"/>'
    '</svg>'
)


def _rasterizar_svg(svg_txt: str):
    import io
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1400})
        page.set_content(
            '<body style="margin:0;padding:0;background:#ffffff;">'
            f'<div id="cont" style="display:inline-block;line-height:0;">{svg_txt}</div></body>'
        )
        png = page.locator("#cont").screenshot()
        browser.close()
    return Image.open(io.BytesIO(png)).convert("RGB")


def _pct_asimetria_horizontal(img) -> float:
    """% de píxeles con diseño cuya imagen especular (eje vertical central) difiere."""
    import numpy as np
    from PIL import ImageFilter, ImageOps

    arr = np.array(img).astype(int)
    arr_esp = np.array(ImageOps.mirror(img)).astype(int)

    def _sat(a):
        return np.abs(a[:, :, 0] - a[:, :, 1]) + np.abs(a[:, :, 1] - a[:, :, 2]) + np.abs(a[:, :, 2] - a[:, :, 0])

    mascara = (_sat(arr) > 30) | (_sat(arr_esp) > 30)
    # Erosión para ignorar el suavizado de bordes (anti-aliasing)
    mascara = np.array(Image.fromarray((mascara * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    assert mascara.sum() > 500, "La cara no contiene diseño visible suficiente"
    diff = np.abs(arr[mascara] - arr_esp[mascara]).sum(axis=1)
    return float((diff > 60).sum()) / float(mascara.sum()) * 100.0


def test_pico_mitad_espejo_refleja_la_cara(tmp_path):
    """
    Modo "Mitad (espejo)" del pico:
    1. El lienzo de la cara (textura de la cara, misma caja y clip que Diseño) es simétrico:
       su mitad derecha es el reflejo exacto de la izquierda (diferencia < 5%) con un diseño asimétrico.
    2. Diseño muestra la mitad activa, el reflejo recortado y el eje de espejo.
    3. "Lienzo completo" conserva el espejo; "Una cara" lo desactiva.
    4. El proyecto guarda solo las capas de una cara y el modo (nunca la réplica) y lo restaura al abrir.
    """
    from dataclasses import asdict
    from logic.diseno.lienzo import CapaDiseno, limpiar_cache_fragmentos
    from logic.geometria.textura import svg_textura

    limpiar_cache_fragmentos()
    (tmp_path / "asimetrico.svg").write_text(SVG_ASIMETRICO_PICO, encoding="utf-8")

    c = ControladorTrompo()
    c.calcular()
    c.carpeta_recursos = str(tmp_path)
    c.cambiar_diseno_seccion("pico", "A")
    c.obtener_diseno_activo().capas = [
        CapaDiseno(
            id="capa_asim", nombre="Asimétrica", tipo="svg", archivo="asimetrico.svg",
            ancho_natural=100.0, alto_natural=100.0,
            x=-34.0, y=-1.0, ancho=68.0, alto=80.0,
        )
    ]

    c.cambiar_diseno_lienzo_modo("mitad")

    # 1. Simetría por píxeles del lienzo de la cara
    svg_cara = svg_textura(
        clave="pico_A",
        entrada=c.entrada_actual,
        resultado=c.resultado,
        diseno=c.obtener_diseno_activo(),
        config_seccion=c.obtener_config_seccion("pico"),
        carpeta_recursos=tmp_path,
        max_px=600,
    )
    pct = _pct_asimetria_horizontal(_rasterizar_svg(svg_cara))
    print(f"Asimetría del lienzo de la cara del pico en modo espejo: {pct:.2f}%")
    assert pct < 5.0, f"La mitad derecha no es el reflejo de la izquierda: {pct:.2f}% distinto (máx 5%)"

    # 2. Diseño en mitad: mitad activa + reflejo recortado + eje de espejo
    vm = c.get_view_model()
    assert vm.diseno_lienzo_modo == "mitad"
    assert 'id="diseno-mitad-activa"' in c.svg_diseno
    assert 'id="diseno-mitad-reflejo"' in c.svg_diseno
    assert 'id="eje-espejo-recto"' in c.svg_diseno

    # Interruptor del pico con 3 opciones en orden; los conos sin cambios
    vista = VistaTrompo()
    vista.controlador = c
    vista._sync_controlador_a_vista(c.get_view_model())
    assert [s.value for s in vista.selector_lienzo_diseno.segments] == ["una_cara", "mitad", "completo"]
    assert [s.label.value for s in vista.selector_lienzo_diseno.segments] == [
        "Una cara", "Mitad (espejo)", "Lienzo completo"
    ]
    assert vista.selector_lienzo_diseno.selected == ["mitad"]

    # 3. Lienzo completo respeta el espejo; Una cara lo desactiva
    c.cambiar_diseno_lienzo_modo("completo")
    assert c.obtener_config_seccion("pico").espejo is True
    assert "capa_asim_reflejo" in c.svg_diseno

    # 4. JSON: solo una capa y el modo
    datos = asdict(c.a_proyecto())
    capas = datos["disenos"]["pico_A"]["capas"]
    assert [k["id"] for k in capas] == ["capa_asim"]
    assert datos["config_secciones"]["pico"]["diseno_modo"] == "completo"
    assert datos["config_secciones"]["pico"]["espejo"] is True

    ruta = tmp_path / "proy_espejo.json"
    ok, msg = c.guardar(str(ruta))
    assert ok is True, msg
    texto = ruta.read_text(encoding="utf-8")
    assert "capa_asim_reflejo" not in texto

    c2 = ControladorTrompo()
    ok2, msg2 = c2.abrir(str(ruta))
    assert ok2 is True, msg2
    cfg2 = c2.obtener_config_seccion("pico")
    assert cfg2.diseno_modo == "completo" and cfg2.espejo is True
    assert cfg2.dibujar == "completo"  # la hoja de trazo del pico no cambia

    c.cambiar_diseno_lienzo_modo("una_cara")
    assert c.obtener_config_seccion("pico").espejo is False
    assert "capa_asim_reflejo" not in c.svg_diseno
