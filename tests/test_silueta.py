"""Pruebas de rasterización de siluetas exactas en lógica pura."""

import numpy as np
import pytest

from logic.geometria.abanico import area_poligono, pieza_a_geometria_plana, contorno_abanico, abanico
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.papel.silueta import mascara_silueta


def test_silueta_triangulo_precision_area() -> None:
    """Un triángulo con base 40 cm y altura 60 cm a 5 px/cm:
    el área de la máscara (píxeles * cm_por_px²) difiere menos de 0.5% del área exacta.
    """
    pts_tri = [(-20.0, 0.0), (20.0, 0.0), (0.0, 60.0)]
    caja_tri = (-20.0, 0.0, 40.0, 60.0)
    px_por_cm = 5.0

    mask, cm_por_px = mascara_silueta(pts_tri, caja_tri, px_por_cm)

    assert mask.dtype == bool
    assert cm_por_px == pytest.approx(0.2, rel=1e-5)

    area_exacta = area_poligono(pts_tri)
    area_mask = np.sum(mask) * (cm_por_px ** 2)

    diff_pct = abs(area_mask - area_exacta) / area_exacta * 100.0
    print(f"\n[Triángulo] Exacta: {area_exacta:.2f} cm² | Máscara: {area_mask:.2f} cm² | Dif: {diff_pct:.4f}%")
    assert diff_pct < 0.5


def test_silueta_abanico_precision_area() -> None:
    """Un sector de abanico superior a 5 px/cm:
    el área de la máscara (píxeles * cm_por_px²) difiere menos de 0.5% del área exacta.
    """
    entrada = BalloonInput(altura_cuerpo=700.0, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0)
    calc = TrompoEstrellaCalculator()
    resultado = calc.calcular(entrada)
    pz = pieza_a_geometria_plana(resultado, entrada, "superior")
    ab = abanico(pz, n=5, centrado=True)
    caja_ab = (ab.caja_min_x, ab.caja_min_y, ab.ancho_total, ab.alto_total)
    pts_ab = contorno_abanico(pz, 5, dibujar="completo", pasos_arco=64)

    px_por_cm = 5.0
    mask, cm_por_px = mascara_silueta(pts_ab, caja_ab, px_por_cm)

    assert mask.dtype == bool
    assert cm_por_px == pytest.approx(0.2, rel=1e-5)

    area_exacta = area_poligono(pts_ab)
    area_mask = np.sum(mask) * (cm_por_px ** 2)

    diff_pct = abs(area_mask - area_exacta) / area_exacta * 100.0
    print(f"[Abanico] Exacta: {area_exacta:.2f} cm² | Máscara: {area_mask:.2f} cm² | Dif: {diff_pct:.4f}%")
    assert diff_pct < 0.5
