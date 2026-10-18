"""Prueba mínima de vectorización con VTracer."""

from pathlib import Path
from PIL import Image, ImageDraw
import pytest
import vtracer


def test_vtracer_vectorizacion_minima(tmp_path: Path) -> None:
    # 1. Generar PNG RGBA de 200x100 con fondo transparente y 2 rectángulos
    # Rectángulo rojo de 80x60 (de x=10..89, y=10..69)
    # Rectángulo azul de 60x40 (de x=110..169, y=20..59)
    # Sin traslape
    im = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.rectangle([10, 10, 89, 69], fill=(255, 0, 0, 255))
    draw.rectangle([110, 20, 169, 59], fill=(0, 0, 255, 255))

    img_path = tmp_path / "minimo.png"
    svg_path = tmp_path / "minimo.svg"
    im.save(img_path)

    # 2. Vectorizar con vtracer
    vtracer.convert_image_to_svg_py(
        str(img_path),
        str(svg_path),
        colormode="color",
        hierarchical="cutout",
        mode="polygon",
        filter_speckle=0,
    )

    assert svg_path.exists(), "El archivo SVG no fue generado"
    svg_contenido = svg_path.read_text(encoding="utf-8")

    # 3. Imprimir el SVG completo (visible con pytest -s)
    print("\n--- SVG GENERADO POR VTRACER ---")
    print(svg_contenido)
    print("--- FIN SVG ---\n")

    # 4. Verificaciones
    num_paths = svg_contenido.count("<path")
    assert num_paths >= 2, f"Se esperaban al menos 2 <path>, se encontraron {num_paths}"

    svg_lower = svg_contenido.lower()
    # Verificar fill rojo y azul (en hex o rgb)
    assert "#ff0000" in svg_lower or "fill=\"red\"" in svg_lower, "No se encontró el relleno rojo en el SVG"
    assert "#0000ff" in svg_lower or "fill=\"blue\"" in svg_lower, "No se encontró el relleno azul en el SVG"

    # Verificar que el fondo transparente no generó una ruta extra
    assert num_paths == 2, f"Se esperaba que el fondo transparente se omitiera, paths encontrados: {num_paths}"
