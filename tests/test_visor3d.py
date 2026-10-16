import urllib.request
import json
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.exportacion.escena3d import escena_a_dict
from logic.exportacion.visor3d import ServidorVisor, exportar_visor_autocontenido

def test_servidor_visor_y_api():
    servidor = ServidorVisor()
    puerto = servidor.iniciar()
    assert puerto > 0
    assert servidor.url == f"http://127.0.0.1:{puerto}/"

    try:
        datos_prueba = {"test": 123, "metadata": {"altura": 950}}
        servidor.actualizar_datos_escena(datos_prueba)

        # Probar endpoint API
        url_api = f"{servidor.url}api/escena"
        with urllib.request.urlopen(url_api) as resp:
            assert resp.status == 200
            content = json.loads(resp.read().decode("utf-8"))
            assert content["test"] == 123

        # Probar servir visor.html
        with urllib.request.urlopen(servidor.url) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "Trompo Estrella 3D" in html

        # Probar servir vendor/three.min.js
        with urllib.request.urlopen(f"{servidor.url}vendor/three.min.js") as resp:
            assert resp.status == 200
            js = resp.read()
            assert len(js) > 10000
    finally:
        servidor.detener()

def test_exportar_visor_autocontenido(tmp_path):
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(380, 20, 1, 1)
    res = calc.calcular(inp)
    escena = escena_a_dict(inp, res)

    ruta_html = tmp_path / "globo_visor_3d.html"
    exportar_visor_autocontenido(escena, str(ruta_html))

    assert ruta_html.exists()
    contenido = ruta_html.read_text(encoding="utf-8")
    assert "window.__DATOS_ESCENA_3D__ =" in contenido
    assert "Trompo Estrella 3D" in contenido
    # No debe requerir links externos
    assert '<script src="/vendor/' not in contenido
