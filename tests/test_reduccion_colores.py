"""Pruebas de reducción de colores con Pillow (agrupación de colores parecidos)."""

from PIL import Image
import pytest

from logic.papel.reduccion_colores import reducir_colores
from logic.papel.vectorizacion import medir_regiones


def test_degradado_sin_dithering() -> None:
    """Degradado horizontal rojo->azul de 256 px con max_colores=4:
    como máximo 4 colores opacos distintos y cada fila forma como máximo 4 franjas continuas.
    """
    im = Image.new("RGBA", (256, 10))
    for x in range(256):
        for y in range(10):
            im.putpixel((x, y), (255 - x, 0, x, 255))

    res = reducir_colores(im, max_colores=4, modo="color")

    # 1. Máximo 4 colores opacos distintos
    colores_opacos = {p[:3] for p in res.getdata() if p[3] == 255}
    assert 1 <= len(colores_opacos) <= 4

    # 2. Prueba de no dithering: cada fila forma como máximo 4 franjas continuas
    for y in range(10):
        fila = [res.getpixel((x, y))[:3] for x in range(256)]
        transiciones = sum(1 for i in range(len(fila) - 1) if fila[i] != fila[i + 1])
        num_franjas = transiciones + 1
        assert num_franjas <= 4, f"Fila {y} tiene {num_franjas} franjas continuas (esperado <= 4)"


def test_imagen_con_menos_colores_queda_identica() -> None:
    """Imagen con 3 colores planos y max_colores=8: queda idéntica."""
    im = Image.new("RGBA", (90, 30))
    # 3 franjas de colores planos
    for x in range(90):
        for y in range(30):
            if x < 30:
                c = (255, 0, 0, 255)
            elif x < 60:
                c = (0, 255, 0, 255)
            else:
                c = (0, 0, 255, 255)
            im.putpixel((x, y), c)

    res = reducir_colores(im, max_colores=8, modo="color")
    assert list(res.getdata()) == list(im.getdata())


def test_conservacion_transparencia() -> None:
    """Verifica que alpha < 128 quede en 0 y alpha >= 128 quede en 255."""
    im = Image.new("RGBA", (4, 1))
    im.putpixel((0, 0), (255, 0, 0, 0))    # 0 < 128 -> 0
    im.putpixel((1, 0), (255, 0, 0, 100))  # 100 < 128 -> 0
    im.putpixel((2, 0), (255, 0, 0, 128))  # 128 >= 128 -> 255
    im.putpixel((3, 0), (255, 0, 0, 255))  # 255 >= 128 -> 255

    res = reducir_colores(im, max_colores=4, modo="color")
    alphas = [p[3] for p in res.getdata()]
    assert alphas == [0, 0, 255, 255]


def test_modo_grises() -> None:
    """modo 'grises': todo píxel opaco cumple R=G=B y hay máximo N niveles."""
    im = Image.new("RGBA", (256, 10))
    for x in range(256):
        for y in range(10):
            im.putpixel((x, y), (255 - x, 0, x, 255))

    res = reducir_colores(im, max_colores=4, modo="grises")

    colores_opacos = {p[:3] for p in res.getdata() if p[3] == 255}
    assert 1 <= len(colores_opacos) <= 4

    for r, g, b in colores_opacos:
        assert r == g == b, f"El color ({r}, {g}, {b}) no es un nivel de gris (R != G o G != B)"


def test_integracion_medir_regiones() -> None:
    """Integración: reducir el degradado y pasarlo por medir_regiones:
    colores <= N y suma de áreas = píxeles opacos (+-1%).
    """
    im = Image.new("RGBA", (256, 20))
    for x in range(256):
        for y in range(20):
            im.putpixel((x, y), (255 - x, 0, x, 255))

    res = reducir_colores(im, max_colores=4, modo="color")
    areas = medir_regiones(res)

    # Imprimir con -s los hex resultantes del degradado
    print("\n[Degradado reducido] Colores HEX detectados por medir_regiones:")
    for hex_color, area in sorted(areas.items()):
        print(f"  {hex_color}: {area:.1f} px²")

    assert len(areas) <= 4
    total_pixeles_opacos = 256 * 20
    suma_areas = sum(areas.values())
    diff_pct = abs(suma_areas - total_pixeles_opacos) / total_pixeles_opacos * 100.0
    print(f"Suma áreas: {suma_areas:.1f} | Píxeles opacos: {total_pixeles_opacos} | Diferencia: {diff_pct:.4f}%\n")
    assert diff_pct <= 1.0


def _generar_degradado_tres_tonos_desigual(w: int = 400, h: int = 100) -> Image.Image:
    """Genera un degradado naranja -> verde -> azul donde el verde central ocupa mayor área."""
    import math

    im = Image.new("RGBA", (w, h))
    for x in range(w):
        if x < 60:
            t = x / 60.0
            r = int(255 * (1.0 - t) + 40 * t)
            g = int(120 * (1.0 - t) + 200 * t)
            b = int(0 * (1.0 - t) + 60 * t)
        elif x < 340:
            t = (x - 60) / 280.0
            r = int(40 + 20 * math.sin(t * math.pi))
            g = int(200 + 30 * math.cos(t * math.pi))
            b = int(60 + 20 * t)
        else:
            t = (x - 340) / 60.0
            r = int(40 * (1.0 - t) + 0 * t)
            g = int(170 * (1.0 - t) + 80 * t)
            b = int(80 * (1.0 - t) + 255 * t)
        for y in range(h):
            im.putpixel((x, y), (r, g, b, 255))
    return im


def test_reparto_degradado_tres_tonos_areas_desiguales() -> None:
    """Degradado naranja->verde->azul con áreas desiguales reducido a 8 colores:
    - Cada extremo debe quedar a menos de 60.0 de distancia RGB de su color resultante.
    - No debe haber dos colores resultantes casi iguales (distancia RGB >= 25.0 en color,
      y diferencia >= 15 niveles en grises).
    """
    import math

    im = _generar_degradado_tres_tonos_desigual(400, 100)

    # 1. Modo color
    res_color = reducir_colores(im, max_colores=8, modo="color")
    colores_c = sorted({p[:3] for p in res_color.getdata() if p[3] == 255})
    assert 3 <= len(colores_c) <= 8

    ext_izq_orig = im.getpixel((0, 0))[:3]
    ext_der_orig = im.getpixel((399, 0))[:3]
    ext_izq_res = res_color.getpixel((0, 0))[:3]
    ext_der_res = res_color.getpixel((399, 0))[:3]

    dist_izq = math.dist(ext_izq_orig, ext_izq_res)
    dist_der = math.dist(ext_der_orig, ext_der_res)
    dist_min_color = min(
        math.dist(c1, c2)
        for i, c1 in enumerate(colores_c)
        for c2 in colores_c[i + 1 :]
    )

    # 2. Modo grises
    res_grises = reducir_colores(im, max_colores=8, modo="grises")
    colores_g = sorted({p[0] for p in res_grises.getdata() if p[3] == 255})
    assert 2 <= len(colores_g) <= 8
    dist_min_gris = min(
        abs(g1 - g2)
        for i, g1 in enumerate(colores_g)
        for g2 in colores_g[i + 1 :]
    )

    print(
        f"\n[3 tonos desigual] Color ({len(colores_c)}): dist_izq={dist_izq:.2f}, "
        f"dist_der={dist_der:.2f}, dist_min_par={dist_min_color:.2f} | "
        f"Grises ({len(colores_g)}): niveles={colores_g}, diff_min_gris={dist_min_gris}"
    )

    assert dist_izq < 60.0, f"Extremo naranja perdió su tono: orig={ext_izq_orig}, res={ext_izq_res}, dist={dist_izq:.2f}"
    assert dist_der < 60.0, f"Extremo azul perdió su tono: orig={ext_der_orig}, res={ext_der_res}, dist={dist_der:.2f}"
    assert dist_min_color >= 25.0, f"Hay colores demasiado parecidos entre sí: dist_min={dist_min_color:.2f}"
    assert dist_min_gris >= 15, f"Hay niveles de gris casi idénticos: {colores_g} (diff_min={dist_min_gris})"


def test_conserva_azul_en_fondo_con_grano() -> None:
    """Imagen sintética 400x600: fondo grande cálido con grano (6 tonos base con ruido +-25 por canal)
    y una zona azul sólida de ~8 %. Con max_colores=6 debe quedar al menos un color azul
    (matiz 190°–250°, saturación > 0.35).
    """
    import colorsys
    import numpy as np

    np.random.seed(42)
    w, h = 400, 600
    arr = np.zeros((h, w, 4), dtype=np.uint8)

    tonos_base = [
        [220, 140, 80],
        [200, 110, 60],
        [230, 170, 100],
        [180, 80, 40],
        [240, 190, 120],
        [190, 100, 50],
    ]
    indices = np.random.randint(0, 6, size=(h, w))
    base = np.array(tonos_base, dtype=np.int16)[indices]
    ruido = np.random.randint(-25, 26, size=(h, w, 3), dtype=np.int16)
    fondo = np.clip(base + ruido, 0, 255).astype(np.uint8)

    arr[:, :, :3] = fondo
    arr[:, :, 3] = 255

    # Zona azul sólida de ~8 % (160 x 120 = 19 200 px de 240 000 px = 8.0 %)
    arr[200:320, 120:280, :3] = [20, 80, 220]

    im = Image.fromarray(arr, mode="RGBA")
    res = reducir_colores(im, max_colores=6, modo="color")

    colores = sorted({p[:3] for p in res.getdata() if p[3] == 255})
    print(f"\n[Fondo con grano] Colores resultantes ({len(colores)}):")
    hay_azul = False
    for r, g, b in colores:
        h_norm, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        matiz = h_norm * 360.0
        print(f"  RGB: ({r}, {g}, {b}) -> Matiz: {matiz:.1f}°, Sat: {s:.2f}")
        if 190.0 <= matiz <= 250.0 and s > 0.35:
            hay_azul = True

    assert hay_azul, (
        f"Se perdió la zona azul entre el grano del fondo cálido. Colores resultantes: {colores}"
    )

