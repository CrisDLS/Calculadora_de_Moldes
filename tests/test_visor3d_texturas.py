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
