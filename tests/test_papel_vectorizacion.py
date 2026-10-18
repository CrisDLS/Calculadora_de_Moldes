"""Pruebas de medición de área por color con VTracer."""

from PIL import Image, ImageDraw
import pytest

from logic.papel.vectorizacion import medir_regiones


def test_rectangulos_rojo_y_azul() -> None:
    """Verifica áreas exactas de rectángulos rojo (80x60) y azul (60x40)."""
    im = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Rectángulo rojo de 80x60: x de 10 a 89, y de 10 a 69
    draw.rectangle([10, 10, 89, 69], fill=(255, 0, 0, 255))
    # Rectángulo azul de 60x40: x de 110 a 169, y de 20 a 59
    draw.rectangle([110, 20, 169, 59], fill=(0, 0, 255, 255))

    areas = medir_regiones(im)

    assert len(areas) == 2
    assert areas["#FF0000"] == 4800.0
    assert areas["#0000FF"] == 2400.0
    # Verificación de búsqueda insensible a mayúsculas
    assert areas["#ff0000"] == 4800.0
    assert areas["#0000ff"] == 2400.0


def test_rectangulo_con_hueco() -> None:
    """Verifica que los huecos resten correctamente del área exterior."""
    im = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Rectángulo exterior de 100x100 (área 10,000 px²)
    draw.rectangle([10, 10, 109, 109], fill=(255, 0, 0, 255))
    # Hueco interior transparente de 40x40 (área 1,600 px²)
    draw.rectangle([40, 40, 79, 79], fill=(0, 0, 0, 0))

    areas = medir_regiones(im)

    assert len(areas) == 1
    # Área esperada = 10,000 - 1,600 = 8,400 px²
    assert areas["#FF0000"] == 8400.0


def test_fondo_transparente_no_suma_color() -> None:
    """Verifica que el fondo transparente no genere rutas ni sume ningún color."""
    # Imagen 100% transparente
    im_vacia = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    areas_vacia = medir_regiones(im_vacia)
    assert len(areas_vacia) == 0

    # Imagen con figura sobre fondo transparente amplio
    im_figura = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im_figura)
    draw.rectangle([50, 50, 99, 99], fill=(255, 255, 0, 255))  # 50x50 amarillo

    areas_figura = medir_regiones(im_figura)
    assert len(areas_figura) == 1
    assert "#FFFF00" in areas_figura
    assert areas_figura["#FFFF00"] == 2500.0
    assert "#000000" not in areas_figura


def test_circulo_diferencia_menor_un_porciento() -> None:
    """Verifica que el área vectorizada de un círculo difiera menos de 1% respecto al conteo de píxeles."""
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Círculo verde (bounding box de 101x101 px)
    draw.ellipse([50, 50, 150, 150], fill=(0, 255, 0, 255))

    # Conteo exacto de píxeles con Pillow
    conteo_pixeles = sum(1 for p in im.getdata() if p[3] > 0)

    # Medición vectorial con VTracer
    areas = medir_regiones(im)
    assert "#00FF00" in areas
    area_vectorizada = areas["#00FF00"]

    diferencia_pct = abs(area_vectorizada - conteo_pixeles) / conteo_pixeles * 100.0

    print(
        f"\n[Circulo] Conteo pixeles: {conteo_pixeles} px² | "
        f"Area vectorizada VTracer: {area_vectorizada:.1f} px² | "
        f"Diferencia: {diferencia_pct:.4f}%"
    )

    assert diferencia_pct < 1.0, f"La diferencia ({diferencia_pct:.4f}%) supera el 1% permitido"
