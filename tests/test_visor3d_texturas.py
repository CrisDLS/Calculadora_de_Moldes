"""
Prueba automatizada con Playwright para verificar el visor 3D con texturas de diseño.
Comprueba que el visor cargue la escena con texturas, no genere errores en consola,
y que el canvas renderizado muestre contenido gráfico no uniforme (píxeles con variedad de color).
"""
import json
import time
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

from logic.proyecto.modelo import Proyecto
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.exportacion.escena3d import escena_a_dict
from logic.exportacion.visor3d import ServidorVisor
from logic.diseno.lienzo import CapaDiseno


def test_visor3d_texturas_playwright():
    p = Path("guardados/recursos_temp/prueba_imagen.json")
    assert p.exists(), "No se encontró el archivo de prueba guardados/recursos_temp/prueba_imagen.json"

    data = json.loads(p.read_text(encoding="utf-8"))
    proy = Proyecto.from_dict(data)

    # Añadir diseño visible al pico
    capa_pico = CapaDiseno(
        id="pico_flor",
        nombre="Flor",
        tipo="raster",
        archivo="flor_cantoya_e96542ec.png",
        ancho_natural=20.0,
        alto_natural=20.0,
        x=-10.0,
        y=10.0,
        ancho=20.0,
        alto=20.0,
    )
    proy.disenos["pico_A"].capas = [capa_pico]

    calc = TrompoEstrellaCalculator()
    res = calc.calcular(proy.entrada)

    escena = escena_a_dict(
        proy.entrada,
        res,
        esquema_pintura=proy.pintura,
        esquema_diseno=proy.esquema,
        configuraciones=proy.config_secciones,
        disenos=proy.disenos,
        carpeta_recursos=p.parent,
    )

    assert "texturas" in escena
    assert "superior" in escena["texturas"]
    assert "pico_A" in escena["texturas"]

    servidor = ServidorVisor(puerto=0)
    puerto = servidor.iniciar()
    servidor.actualizar_datos_escena(escena)

    errores_consola = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            # Capturar logs y errores de consola
            def _on_console(msg):
                if msg.type == "error":
                    errores_consola.append(msg.text)

            page.on("console", _on_console)
            page.on("pageerror", lambda exc: errores_consola.append(str(exc)))

            page.goto(servidor.url)
            page.wait_for_selector("#canvas-container canvas")
            time.sleep(2.5)

            # Comprobar que no hubo errores en consola
            assert len(errores_consola) == 0, f"Errores en consola del navegador: {errores_consola}"

            # Comprobar que el canvas no es uniforme extrayendo píxeles de una zona del globo
            # Usamos getImageData en un canvas 2D auxiliar renderizando una muestra
            muestras_color = page.evaluate("""() => {
                const canvas = document.querySelector('#canvas-container canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
                if (!gl) return [];
                const width = canvas.width;
                const height = canvas.height;
                // Leer un bloque central de 100x100 píxeles
                const x0 = Math.floor(width / 2) - 50;
                const y0 = Math.floor(height / 2) - 50;
                const pixels = new Uint8Array(100 * 100 * 4);
                gl.readPixels(x0, y0, 100, 100, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                const colors = new Set();
                for (let i = 0; i < pixels.length; i += 16) {
                    const r = pixels[i];
                    const g = pixels[i+1];
                    const b = pixels[i+2];
                    colors.add(`${r},${g},${b}`);
                }
                return Array.from(colors);
            }""")

            # Debe haber múltiples colores distintos en la superficie visible del canvas
            assert len(muestras_color) > 5, f"El canvas parece uniforme o vacío: {len(muestras_color)} colores encontrados"

            browser.close()
    finally:
        servidor.detener()


def test_zonas_transparentes_color_papel_no_negras(tmp_path):
    """
    Comprueba que una zona transparente de un diseño en una cara con papel de color
    (por ejemplo, blanco #ffffff) NO se renderice de color negro en el visor 3D,
    sino con el tono de papel iluminado (valores RGB significativamente mayores a negro).
    """
    from logic.models import BalloonInput
    from logic.diseno.esquema import EsquemaDiseno
    from logic.diseno.pintura import EsquemaPintura
    from logic.diseno.config_seccion import ConfigSeccion
    from logic.diseno.lienzo import Diseno, CapaDiseno

    # Globo con 20 gajos, cono superior blanco (#ffffff)
    entrada = BalloonInput(
        altura_cuerpo=600.0,
        num_gajos=20,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )
    calc = TrompoEstrellaCalculator()
    res = calc.calcular(entrada)

    # Creamos un SVG con fondo 100% transparente y un círculo rojo en el centro
    archivo_svg = tmp_path / "transparente.svg"
    archivo_svg.write_text(
        '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="50" cy="50" r="10" fill="red"/>'
        '</svg>',
        encoding="utf-8"
    )

    capa_transparente = CapaDiseno(
        id="c_trans",
        nombre="Transparente",
        tipo="svg",
        archivo="transparente.svg",
        ancho_natural=20.0,
        alto_natural=20.0,
        x=-10.0,
        y=100.0,
        ancho=20.0,
        alto=20.0,
    )
    disenos = {
        "inferior": Diseno(seccion="inferior", capas=[capa_transparente]),
        "superior": Diseno(seccion="superior", capas=[capa_transparente]),
    }
    configs = {
        "inferior": ConfigSeccion(seccion="inferior", esquema=EsquemaDiseno("repeticion", 5)),
        "superior": ConfigSeccion(seccion="superior", esquema=EsquemaDiseno("repeticion", 5)),
    }
    pintura = EsquemaPintura(colores_superior=["blanco"], colores_inferior=["blanco"])

    escena = escena_a_dict(
        entrada,
        res,
        esquema_pintura=pintura,
        esquema_diseno=configs["inferior"].esquema,
        configuraciones=configs,
        disenos=disenos,
        carpeta_recursos=tmp_path,
    )

    assert "inferior" in escena["texturas"]

    servidor = ServidorVisor(puerto=0)
    puerto = servidor.iniciar()
    servidor.actualizar_datos_escena(escena)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(servidor.url)
            page.wait_for_selector("#canvas-container canvas")
            time.sleep(2.0)

            # Cambiar a modo Día para tener buena iluminación solar uniforme sobre el papel blanco
            page.click("#btn-dia")
            time.sleep(1.0)

            # Muestrear píxeles del cono inferior (tercio inferior del canvas en GL)
            # En la escena, el cono inferior tiene textura 'inferior' con fondo transparente sobre papel blanco (#ffffff).
            # Con el bug actual, la zona transparente del canvas se renderiza negra en lugar del color blanco iluminado.
            colores_cono = page.evaluate("""() => {
                const canvas = document.querySelector('#canvas-container canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
                if (!gl) return [];
                const width = canvas.width;
                const height = canvas.height;
                // Tercio inferior del canvas (cono inferior): x central, y a 35% de altura en gl
                const x0 = Math.floor(width / 2);
                const y0 = Math.floor(height * 0.35);
                const pixels = new Uint8Array(20 * 20 * 4);
                gl.readPixels(x0 - 10, y0 - 10, 20, 20, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                const lista = [];
                for (let i = 0; i < pixels.length; i += 4) {
                    lista.push([pixels[i], pixels[i+1], pixels[i+2]]);
                }
                return lista;
            }""")

            assert len(colores_cono) > 0, "No se obtuvieron píxeles del cono"

            # En el fondo transparente sobre papel blanco con luz de día, el brillo R+G+B debe ser alto (> 150)
            # Si el fondo transparente se dibuja negro, el valor será [0, 0, 0] o < 30
            pixeles_blancos_o_claros = [p for p in colores_cono if (p[0] + p[1] + p[2]) > 150]
            pixeles_negros = [p for p in colores_cono if (p[0] < 30 and p[1] < 30 and p[2] < 30)]

            assert len(pixeles_blancos_o_claros) > 0.5 * len(colores_cono), (
                f"La zona transparente se ve oscura o negra: {len(pixeles_negros)} negros de {len(colores_cono)} muestreados. "
                f"Muestra de colores: {colores_cono[:5]}"
            )

            browser.close()
    finally:
        servidor.detener()


def test_reconstruccion_abanico_conos_asimetrica(tmp_path):
    """
    Comprueba que el abanico reconstruido desde la correspondencia 3D y texturas
    coincida con el abanico exportado de la pestaña Diseño (< 5% de píxeles distintos)
    tanto en el cono superior como en el cono inferior usando una imagen sintética
    asimétrica (letra F con esquina superior izquierda roja y franja inferior azul).
    """
    import re
    from PIL import Image, ImageDraw
    from logic.models import BalloonInput
    from logic.geometria.malla_trompo import construir_malla
    from logic.geometria.abanico import pieza_a_geometria_plana, abanico
    from logic.geometria.textura import mapear_textura
    from logic.diseno.esquema import EsquemaDiseno
    from logic.diseno.config_seccion import ConfigSeccion
    from logic.diseno.lienzo import Diseno, CapaDiseno
    from scripts.diagnostico_abanico_vs_3d import reconstruir_abanico_seccion

    # Crear imagen PNG asimétrica (letra F + esquina roja + base azul)
    img_asim = Image.new("RGB", (400, 400), (240, 240, 240))
    draw = ImageDraw.Draw(img_asim)
    # Esquina superior izquierda roja
    draw.rectangle([0, 0, 140, 140], fill=(220, 20, 20))
    # Base inferior azul
    draw.rectangle([0, 320, 400, 400], fill=(20, 60, 220))
    # Letra F grande en verde oscuro en el centro-derecha
    draw.rectangle([160, 60, 200, 300], fill=(20, 150, 40))   # tallo vertical
    draw.rectangle([160, 60, 340, 100], fill=(20, 150, 40))   # barra superior
    draw.rectangle([160, 160, 290, 200], fill=(20, 150, 40))  # barra media
    ruta_png = tmp_path / "asimetrica_f.png"
    img_asim.save(ruta_png)

    entrada = BalloonInput(altura_cuerpo=950.0, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0)
    calc = TrompoEstrellaCalculator()
    res = calc.calcular(entrada)
    malla = construir_malla(entrada, res)

    esquema = EsquemaDiseno(modo="repeticion", tam_grupo=5)
    configs = {
        "superior": ConfigSeccion(seccion="superior", esquema=esquema, dibujar="completo"),
        "inferior": ConfigSeccion(seccion="inferior", esquema=esquema, dibujar="completo"),
    }

    # Ubicar la capa cubriendo la caja de cada abanico
    pz_sup = pieza_a_geometria_plana(res, entrada, "superior")
    ab_sup = abanico(pz_sup, n=5, centrado=True)
    capa_sup = CapaDiseno(
        id="f_sup",
        nombre="F Superior",
        tipo="raster",
        archivo="asimetrica_f.png",
        ancho_natural=20.0,
        alto_natural=20.0,
        x=ab_sup.caja_min_x,
        y=ab_sup.caja_min_y,
        ancho=ab_sup.ancho_total,
        alto=ab_sup.alto_total,
    )

    pz_inf = pieza_a_geometria_plana(res, entrada, "inferior")
    ab_inf = abanico(pz_inf, n=5, centrado=True)
    capa_inf = CapaDiseno(
        id="f_inf",
        nombre="F Inferior",
        tipo="raster",
        archivo="asimetrica_f.png",
        ancho_natural=20.0,
        alto_natural=20.0,
        x=ab_inf.caja_min_x,
        y=ab_inf.caja_min_y,
        ancho=ab_inf.ancho_total,
        alto=ab_inf.alto_total,
    )

    disenos = {
        "superior": Diseno(seccion="superior", capas=[capa_sup]),
        "inferior": Diseno(seccion="inferior", capas=[capa_inf]),
    }

    from logic.models import Condiciones

    proy = Proyecto(
        version=2,
        nombre="test_asim",
        entrada=entrada,
        condiciones=Condiciones(),
        esquema=esquema,
        config_secciones=configs,
        disenos=disenos,
    )

    mapa_tex = mapear_textura(
        entrada=entrada,
        resultado=res,
        malla=malla,
        configuraciones=configs,
        disenos=disenos,
        carpeta_recursos=tmp_path,
        max_px=512,
    )

    # Leer de visor.js cómo está configurado texture.flipY realmente
    visor_js = Path("app_flet/assets/visor3d/visor.js").read_text(encoding="utf-8")
    m_flip = re.search(r"texture\.flipY\s*=\s*(true|false)", visor_js)
    flip_y_actual = (m_flip.group(1) == "true") if m_flip else True

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("<html><body></body></html>")

        rep_sup = reconstruir_abanico_seccion(
            page, proy, res, malla, mapa_tex, "superior", tmp_path, max_px=512, flip_y_webgl=flip_y_actual
        )
        rep_inf = reconstruir_abanico_seccion(
            page, proy, res, malla, mapa_tex, "inferior", tmp_path, max_px=512, flip_y_webgl=flip_y_actual
        )
        browser.close()

    pct_sup = rep_sup["pct_distinto"]
    pct_inf = rep_inf["pct_distinto"]

    assert pct_sup < 5.0 and pct_inf < 5.0, (
        f"Diferencia excesiva en reconstrucción 3D vs Diseño 2D (flipY={flip_y_actual}): "
        f"superior={pct_sup:.2f}% (máx 5%), inferior={pct_inf:.2f}% (máx 5%)"
    )



