import os
import pytest
from pathlib import Path
from PIL import Image
import defusedxml.ElementTree as ET
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno, importar_recurso
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.svg_diseno import svg_gajo, exportar_diseno

@pytest.fixture
def calc_y_resultado():
    calc = TrompoEstrellaCalculator()
    entrada = BalloonInput(950, 30, 2, 1)
    res = calc.calcular(entrada)
    return calc, entrada, res

def test_svg_abanico_con_diseno_raster_y_svg(tmp_path, calc_y_resultado):
    _, entrada, res = calc_y_resultado

    # Crear imagen raster y svg
    img_path = tmp_path / "sol.png"
    Image.new("RGBA", (50, 50), color=(255, 200, 0, 255)).save(img_path)

    svg_path = tmp_path / "luna.svg"
    svg_path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50"><circle cx="25" cy="25" r="20" fill="navy"/></svg>', encoding="utf-8")

    carpeta_recursos = tmp_path / "rec"
    capa_raster = importar_recurso(img_path, carpeta_recursos)
    capa_svg = importar_recurso(svg_path, carpeta_recursos)

    diseno = Diseno(seccion="superior", capas=[capa_raster, capa_svg])

    svg_output = svg_abanico(
        resultado=res,
        entrada=entrada,
        seccion="superior",
        diseno=diseno,
        carpeta_recursos=carpeta_recursos,
    )

    # Verificar que el SVG generado sea XML válido
    root = ET.fromstring(svg_output.encode("utf-8"))
    assert root is not None

    # Verificar presencia de clipPath y capa diseno
    assert 'id="clip-abanico"' in svg_output
    assert 'inkscape:label="diseno"' in svg_output
    assert 'data:image/png;base64,' in svg_output
    assert 'data:image/svg+xml;base64,' in svg_output

def test_svg_gajo_central_espejo(tmp_path, calc_y_resultado):
    _, entrada, res = calc_y_resultado
    esq = EsquemaDiseno("central_espejo", 5)

    img_path = tmp_path / "figura.png"
    Image.new("RGBA", (30, 30), color="red").save(img_path)
    carpeta_recursos = tmp_path / "rec"
    capa = importar_recurso(img_path, carpeta_recursos)
    diseno = Diseno(seccion="superior", capas=[capa])

    # Gajo 0 en central_espejo con G=5 es espejo (ciclo: [(2, True), (1, True), (0, False), (1, False), (2, False)])
    svg_gajo_0 = svg_gajo(
        resultado=res,
        entrada=entrada,
        seccion="superior",
        esquema=esq,
        diseno=diseno,
        indice=0,
        carpeta_recursos=carpeta_recursos,
    )
    assert "(Espejo)" in svg_gajo_0
    assert 'id="clip-gajo-0"' in svg_gajo_0
    # Validar XML
    ET.fromstring(svg_gajo_0.encode("utf-8"))

    # Gajo 2 es el central (no espejo)
    svg_gajo_2 = svg_gajo(
        resultado=res,
        entrada=entrada,
        seccion="superior",
        esquema=esq,
        diseno=diseno,
        indice=2,
        carpeta_recursos=carpeta_recursos,
    )
    assert "(Espejo)" not in svg_gajo_2
    ET.fromstring(svg_gajo_2.encode("utf-8"))

def test_exportar_diseno_archivos_validos(tmp_path, calc_y_resultado):
    _, entrada, res = calc_y_resultado
    esq = EsquemaDiseno("repeticion", 3)

    img_path = tmp_path / "icono.png"
    Image.new("RGB", (20, 20), "blue").save(img_path)
    carp_rec = tmp_path / "recursos_proy"
    capa = importar_recurso(img_path, carp_rec)
    diseno = Diseno(seccion="superior", capas=[capa])

    carpeta_salida = tmp_path / "salida_diseno"
    archivos = exportar_diseno(
        carpeta=carpeta_salida,
        resultado=res,
        entrada=entrada,
        esquema=esq,
        diseno=diseno,
        carpeta_recursos=carp_rec,
        seccion="superior",
    )

    assert len(archivos) >= 4  # 1 abanico + 3 gajos del grupo
    for arch in archivos:
        assert arch.exists()
        contenido = arch.read_text(encoding="utf-8")
        # Asegurar que cada archivo sea un SVG válido sin excepciones de parseo
        root = ET.fromstring(contenido.encode("utf-8"))
        assert root is not None
