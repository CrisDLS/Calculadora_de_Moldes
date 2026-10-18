"""
Script para capturar pantallas del visor 3D con Playwright para el prompt 36:
- visor_diseno_on_frontal.png
- visor_diseno_on_picos.png
- visor_diseno_off_frontal.png
- visor_diseno_off_picos.png

Usa guardados/recursos_temp/prueba_imagen.json directamente a través de ControladorTrompo.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from app_flet.controlador import ControladorTrompo

def main():
    ctrl = ControladorTrompo()
    archivo_json = Path("guardados/recursos_temp/prueba_imagen.json").resolve()
    assert archivo_json.exists(), f"No existe {archivo_json}"

    # Cargar proyecto sin modificar archivo
    ctrl.abrir(archivo_json)
    srv = ctrl.obtener_servidor_3d()
    assert srv is not None, "El servidor 3D no se pudo obtener"

    url = srv.url
    print(f"Servidor 3D corriendo en {url}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # --- CASO 1: DISEÑO ON ---
        ctrl.cambiar_mostrar_diseno_3d(True)
        page.goto(url)
        page.wait_for_selector("#canvas-container canvas")
        # Esperar a que el modelo y texturas carguen completamente y se centren
        time.sleep(3.0)

        # 1. Frontal ON
        path_on_frontal = Path("docs/capturas/visor_diseno_on_frontal.png")
        page.screenshot(path=str(path_on_frontal))
        print(f"Capturado: {path_on_frontal}")

        # 2. Close-up Picos ON
        page.evaluate("""() => {
            const zPicos = 460;
            // Mirar hacia los picos frontales (Y negativo)
            controls.target.set(0, -320, zPicos);
            camera.position.set(0, -650, zPicos + 30);
            camera.lookAt(0, -320, zPicos);
            controls.update();
        }""")
        time.sleep(1.0)
        path_on_picos = Path("docs/capturas/visor_diseno_on_picos.png")
        page.screenshot(path=str(path_on_picos))
        print(f"Capturado: {path_on_picos}")

        # --- CASO 2: DISEÑO OFF ---
        ctrl.cambiar_mostrar_diseno_3d(False)
        # Recargar para asegurar que la escena actualizada sin texturas se refleje de inmediato
        page.reload()
        page.wait_for_selector("#canvas-container canvas")
        time.sleep(3.0)

        # 3. Frontal OFF
        path_off_frontal = Path("docs/capturas/visor_diseno_off_frontal.png")
        page.screenshot(path=str(path_off_frontal))
        print(f"Capturado: {path_off_frontal}")

        # 4. Close-up Picos OFF
        page.evaluate("""() => {
            const zPicos = 460;
            controls.target.set(0, -320, zPicos);
            camera.position.set(0, -650, zPicos + 30);
            camera.lookAt(0, -320, zPicos);
            controls.update();
        }""")
        time.sleep(1.0)
        path_off_picos = Path("docs/capturas/visor_diseno_off_picos.png")
        page.screenshot(path=str(path_off_picos))
        print(f"Capturado: {path_off_picos}")

        browser.close()

    srv.detener()
    print("Capturas completadas con éxito.")

if __name__ == "__main__":
    main()
