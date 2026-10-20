"""Pruebas para el cálculo de consumo de papel en cm² por color."""

import numpy as np
from PIL import Image
import pytest

from logic.papel.consumo import medir_cm2_por_color


def test_consumo_basico_rojo_azul_base() -> None:
    """Máscara 100x100 px con cm_por_px=0.1 (=100 cm²):
    cuadro rojo 50x40 px (=20 cm²), azul 20x20 px (=4 cm²):
    rojo 20, azul 4, base 76 (+-1%).
    """
    w, h = 100, 100
    mascara = np.ones((h, w), dtype=bool)

    # Imagen transparente con dos cuadros opacos
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Cuadro rojo 50x40 px (de x=10 a 60, y=10 a 50) -> 2000 px
    for x in range(10, 60):
        for y in range(10, 50):
            im.putpixel((x, y), (255, 0, 0, 255))
    # Cuadro azul 20x20 px (de x=70 a 90, y=60 a 80) -> 400 px
    for x in range(70, 90):
        for y in range(60, 80):
            im.putpixel((x, y), (0, 0, 255, 255))

    res = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.1,
        color_base_hex="#FFFFFF",
        max_colores=8,
        modo="color",
    )

    rojo_key = next((k for k in res if k.upper() == "#FF0000"), None)
    azul_key = next((k for k in res if k.upper() == "#0000FF"), None)
    base_key = next((k for k in res if k.upper() == "#FFFFFF"), None)

    assert rojo_key is not None, f"No se encontró el color rojo en {res}"
    assert azul_key is not None, f"No se encontró el color azul en {res}"
    assert base_key is not None, f"No se encontró el color base en {res}"

    assert pytest.approx(20.0, rel=0.01) == res[rojo_key]
    assert pytest.approx(4.0, rel=0.01) == res[azul_key]
    assert pytest.approx(76.0, rel=0.01) == res[base_key]


def test_suma_de_colores_igual_a_area_mascara() -> None:
    """Verifica que la suma de todos los colores = área de la máscara (+-1%)."""
    w, h = 120, 80
    # Máscara elíptica o circular
    y_idx, x_idx = np.ogrid[:h, :w]
    mascara = ((x_idx - 60) ** 2) / (50 ** 2) + ((y_idx - 40) ** 2) / (30 ** 2) <= 1.0
    num_px_mascara = int(np.sum(mascara))

    cm_por_px = 0.15
    area_esperada_cm2 = num_px_mascara * (cm_por_px ** 2)

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Algunas figuras aleatorias dentro de la imagen
    for x in range(30, 70):
        for y in range(25, 45):
            im.putpixel((x, y), (0, 200, 0, 255))

    res = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=cm_por_px,
        color_base_hex="#E5E5E5",
    )

    suma_cm2 = sum(res.values())
    assert pytest.approx(area_esperada_cm2, rel=0.01) == suma_cm2


def test_escalado_cm_por_px_cuadratico() -> None:
    """Con cm_por_px=0.2 las áreas se multiplican por 4 respecto a cm_por_px=0.1."""
    w, h = 60, 60
    mascara = np.ones((h, w), dtype=bool)

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for x in range(10, 40):
        for y in range(10, 40):
            im.putpixel((x, y), (255, 128, 0, 255))

    res_01 = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.1,
        color_base_hex="#FFFFFF",
    )
    res_02 = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.2,
        color_base_hex="#FFFFFF",
    )

    for k in res_01:
        assert k in res_02
        assert pytest.approx(res_01[k] * 4.0, rel=0.01) == res_02[k]


def test_lo_pintado_fuera_de_la_mascara_no_cuenta() -> None:
    """Verifica que los píxeles pintados fuera de la máscara no se cuenten ni sumen."""
    w, h = 100, 100
    mascara = np.zeros((h, w), dtype=bool)
    mascara[20:80, 20:80] = True  # Máscara central de 60x60 = 3600 px

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Pintado FUERA de la máscara (amarillo)
    for x in range(0, 15):
        for y in range(0, 15):
            im.putpixel((x, y), (255, 255, 0, 255))
    # Pintado DENTRO de la máscara (verde 20x20 = 400 px)
    for x in range(30, 50):
        for y in range(30, 50):
            im.putpixel((x, y), (0, 255, 0, 255))

    res = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.1,
        color_base_hex="#FFFFFF",
    )

    # El amarillo no debe aparecer
    amarillo_key = next((k for k in res if k.upper() in ("#FFFF00", "#FFFF01")), None)
    assert amarillo_key is None, f"El color fuera de la máscara no debió sumarse: {res}"

    verde_key = next((k for k in res if k.upper() == "#00FF00"), None)
    base_key = next((k for k in res if k.upper() == "#FFFFFF"), None)

    assert verde_key is not None
    assert base_key is not None

    # Dentro de la máscara: verde = 400 px * 0.01 = 4.0 cm²
    # base = (3600 - 400) px * 0.01 = 32.0 cm²
    assert pytest.approx(4.0, rel=0.01) == res[verde_key]
    assert pytest.approx(32.0, rel=0.01) == res[base_key]
    assert pytest.approx(36.0, rel=0.01) == sum(res.values())


def test_imagen_totalmente_transparente_todo_es_color_base() -> None:
    """Imagen totalmente transparente: todo el área de la máscara es color_base."""
    w, h = 80, 50
    mascara = np.ones((h, w), dtype=bool)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    res = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.1,
        color_base_hex="#FFFFFF",
    )

    base_key = next((k for k in res if k.upper() == "#FFFFFF"), None)
    assert base_key is not None
    assert len(res) == 1
    # 80 * 50 = 4000 px * 0.01 = 40.0 cm²
    assert pytest.approx(40.0, rel=0.001) == res[base_key]


def test_diseno_con_mismo_color_base_se_suman() -> None:
    """Si el color base coincide con uno del diseño, sus áreas se suman."""
    w, h = 100, 100
    mascara = np.ones((h, w), dtype=bool)

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Cuadro blanco explícito en el diseño: 50x40 = 2000 px (=20 cm²)
    for x in range(10, 60):
        for y in range(10, 50):
            im.putpixel((x, y), (255, 255, 255, 255))
    # Cuadro rojo: 20x50 = 1000 px (=10 cm²)
    for x in range(70, 90):
        for y in range(10, 60):
            im.putpixel((x, y), (255, 0, 0, 255))
    # Zona vacía: 10000 - 2000 - 1000 = 7000 px (=70 cm²)

    res = medir_cm2_por_color(
        imagen_rgba=im,
        mascara_silueta=mascara,
        cm_por_px=0.1,
        color_base_hex="#FFFFFF",
    )

    base_key = next((k for k in res if k.upper() == "#FFFFFF"), None)
    rojo_key = next((k for k in res if k.upper() == "#FF0000"), None)

    assert base_key is not None
    assert rojo_key is not None
    assert pytest.approx(10.0, rel=0.01) == res[rojo_key]
    assert pytest.approx(90.0, rel=0.01) == res[base_key]
    assert pytest.approx(100.0, rel=0.01) == sum(res.values())

