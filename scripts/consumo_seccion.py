"""Script para calcular y analizar el consumo de papel en cm² por color para una sección de globo."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from playwright.sync_api import sync_playwright

# Asegurar importación de módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic.papel.consumo import medir_cm2_por_color
from logic.papel.reduccion_colores import UMBRAL_FUSION_RGB, _fusionar_colores_cercanos
from logic.papel.vectorizacion import _normalizar_color
from scripts.rasterizar_seccion import procesar_seccion


def _hex_a_rgb(h: str) -> List[int]:
    """Convierte un color '#RRGGBB' a lista [R, G, B]."""
    h_clean = h.lstrip("#")
    if len(h_clean) == 3:
        h_clean = "".join(c * 2 for c in h_clean)
    return [int(h_clean[0:2], 16), int(h_clean[2:4], 16), int(h_clean[4:6], 16)]


def _rgb_a_hex(rgb: Sequence[int]) -> str:
    """Convierte una terna [R, G, B] a string '#RRGGBB'."""
    return f"#{int(round(rgb[0])):02X}{int(round(rgb[1])):02X}{int(round(rgb[2])):02X}"


def consolidar_colores_cercanos(
    dict_colores: Dict[str, float],
    color_base_hex: str = "#FFFFFF",
    umbral_rgb: float = UMBRAL_FUSION_RGB,
) -> Dict[str, float]:
    """Consolida micro-variaciones de color (p. ej. generadas por VTracer en bordes) menores a umbral_rgb."""
    if not dict_colores:
        return {}
    base_norm = _normalizar_color(color_base_hex) or color_base_hex.upper()

    # Separar color base para no fusionarlo con tonos vecinos
    area_base = dict_colores.get(base_norm, 0.0)
    sin_base = {c: w for c, w in dict_colores.items() if c != base_norm and w > 0.0}

    if not sin_base:
        return {base_norm: area_base} if area_base > 0.0 else {}

    cols_list = [_hex_a_rgb(c) for c in sin_base]
    w_list = [sin_base[c] for c in sin_base]

    pal_fused = _fusionar_colores_cercanos(np.array(cols_list), np.array(w_list), umbral_rgb)
    fused_hexes = [_rgb_a_hex(c) for c in pal_fused]

    res = {c: 0.0 for c in fused_hexes}
    for c, w in sin_base.items():
        rgb = _hex_a_rgb(c)
        best = min(fused_hexes, key=lambda fh: math.dist(rgb, _hex_a_rgb(fh)))
        res[best] += w

    if area_base > 0.0:
        res[base_norm] = area_base

    return res


def alinear_a_paleta_referencia(
    dict_colores: Dict[str, float],
    paleta_ref: List[str],
) -> Dict[str, float]:
    """Agrupa las mediciones de un dict al color euclidiano más cercano de paleta_ref."""
    if not paleta_ref:
        return dict(dict_colores)
    ref_rgbs = {c: _hex_a_rgb(c) for c in paleta_ref}
    agrupado = {c: 0.0 for c in paleta_ref}
    for c, area in dict_colores.items():
        rgb = _hex_a_rgb(c)
        mejor_ref = min(paleta_ref, key=lambda ref: math.dist(rgb, ref_rgbs[ref]))
        agrupado[mejor_ref] += area
    return agrupado


def medir_seccion_con_tiempos(
    ruta_proyecto: str | Path,
    seccion: str,
    px_por_cm: float = 5.0,
    max_colores: int = 8,
    color_base_hex: str = "#FFFFFF",
    page_playwright=None,
) -> dict:
    """Ejecuta rasterizado y medición de consumo para una sección y resolución dadas."""
    res_rast = procesar_seccion(
        ruta_proyecto=ruta_proyecto,
        seccion=seccion,
        px_por_cm=px_por_cm,
        page_playwright=page_playwright,
    )

    img = res_rast["img_rgba"]
    mascara = res_rast["mascara"]
    cm_por_px = res_rast["cm_por_px"]
    factor_cm2 = cm_por_px ** 2

    arr = np.array(img, dtype=np.uint8)
    num_px_vacios = int(np.sum(mascara & (arr[:, :, 3] < 128)))
    area_vacia_cm2 = num_px_vacios * factor_cm2

    t0_med = time.perf_counter()
    consumo = medir_cm2_por_color(
        imagen_rgba=img,
        mascara_silueta=mascara,
        cm_por_px=cm_por_px,
        color_base_hex=color_base_hex,
        max_colores=max_colores,
        modo="color",
    )
    t_med = time.perf_counter() - t0_med

    return {
        "seccion": seccion,
        "px_por_cm": px_por_cm,
        "tam_px": res_rast["tam_px"],
        "cm_por_px": cm_por_px,
        "area_exacta_cm2": res_rast["area_exacta_cm2"],
        "area_mascara_cm2": res_rast["area_mascara_cm2"],
        "area_vacia_cm2": area_vacia_cm2,
        "t_raster_s": res_rast["t_raster_s"],
        "t_medir_s": t_med,
        "consumo": consumo,
    }


def imprimir_reporte_individual(datos: dict, color_base_hex: str = "#FFFFFF") -> None:
    """Imprime el reporte detallado para una corrida individual."""
    base_norm = _normalizar_color(color_base_hex) or color_base_hex.upper()
    w_px, h_px = datos["tam_px"]
    area_silueta = datos["area_mascara_cm2"]
    area_exacta = datos["area_exacta_cm2"]
    consumo = datos["consumo"]

    # Separar zona vacía (papel base sin diseño)
    area_vacia = datos["area_vacia_cm2"]
    pct_vacia = (area_vacia / area_silueta * 100.0) if area_silueta > 0 else 0.0

    print("\n" + "=" * 65)
    print(f"CONSUMO DE PAPEL POR COLOR: {datos['seccion'].upper()}")
    print("=" * 65)
    print(f"Resolución        : {datos['px_por_cm']:.1f} px/cm ({datos['cm_por_px']:.5f} cm/px)")
    print(f"Dimensiones imagen: {w_px} × {h_px} px ({w_px * h_px:,} píxeles)")
    print(f"Tiempo rasterizado: {datos['t_raster_s']:.3f} s")
    print(f"Tiempo de medición: {datos['t_medir_s']:.3f} s")
    print("-" * 65)
    print(f"{'Color HEX':<14} | {'Superficie (cm²)':<18} | {'% de la silueta':<16}")
    print("-" * 65)

    # Consolidar micro-variaciones de color generadas por VTracer en bordes
    filas = sorted(
        consolidar_colores_cercanos(consumo, color_base_hex=color_base_hex).items(),
        key=lambda x: x[1],
        reverse=True,
    )
    for c_hex, area_cm2 in filas:
        pct = (area_cm2 / area_silueta * 100.0) if area_silueta > 0 else 0.0
        nota = " (incluye base)" if c_hex == base_norm and area_vacia > 0 else ""
        print(f"{c_hex:<14} | {area_cm2:>14.2f} cm²   | {pct:>12.2f} %{nota}")

    print("-" * 65)
    print(f"Zona vacía (base): {area_vacia:.2f} cm² ({pct_vacia:.2f} % de la silueta)")
    suma_total = sum(consumo.values())
    diff_exacta = abs(suma_total - area_exacta)
    diff_pct = (diff_exacta / area_exacta * 100.0) if area_exacta > 0 else 0.0

    print(f"Suma total medida: {suma_total:.2f} cm²")
    print(f"Área exacta geom : {area_exacta:.2f} cm²")
    print(f"Diferencia vs geom: {diff_exacta:.2f} cm² ({diff_pct:.4f} %)")
    print("=" * 65 + "\n")


def ejecutar_estudio_resolucion(
    ruta_proyecto: str | Path,
    seccion: str,
    max_colores: int = 8,
    color_base_hex: str = "#FFFFFF",
) -> None:
    """Ejecuta el estudio comparativo a 2, 3, 5 px/cm (y 10 solo en pico_A)."""
    resoluciones = [2, 3, 5]
    if seccion == "pico_A":
        resoluciones.append(10)

    print("\n" + "#" * 70)
    print(f"ESTUDIO DE RESOLUCIÓN - SECCIÓN: {seccion.upper()}")
    print(f"Resoluciones a evaluar: {resoluciones} px/cm")
    print("#" * 70)

    resultados: Dict[int, dict] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 3000, "height": 3000})

        for r in resoluciones:
            t_ini = time.perf_counter()
            datos = medir_seccion_con_tiempos(
                ruta_proyecto=ruta_proyecto,
                seccion=seccion,
                px_por_cm=float(r),
                max_colores=max_colores,
                color_base_hex=color_base_hex,
                page_playwright=page,
            )
            t_total_r = time.perf_counter() - t_ini
            datos["t_total_r"] = t_total_r
            resultados[r] = datos
            w_px, h_px = datos["tam_px"]
            print(
                f"  -> {r:2d} px/cm completado en {t_total_r:6.2f}s "
                f"(raster: {datos['t_raster_s']:5.2f}s, medir: {datos['t_medir_s']:5.2f}s, tamaño: {w_px}×{h_px})"
            )
        browser.close()

    r_max = resoluciones[-1]
    datos_max = resultados[r_max]

    # Paleta de referencia consolidada de la máxima resolución (ordenada por cm²)
    consumo_max_cons = consolidar_colores_cercanos(datos_max["consumo"], color_base_hex=color_base_hex)
    paleta_ref = sorted(consumo_max_cons.keys(), key=lambda c: consumo_max_cons[c], reverse=True)

    # Alinear todas las resoluciones a los clusters de la máxima resolución
    alineados: Dict[int, Dict[str, float]] = {}
    for r in resoluciones:
        cons_r = consolidar_colores_cercanos(resultados[r]["consumo"], color_base_hex=color_base_hex)
        alineados[r] = alinear_a_paleta_referencia(cons_r, paleta_ref)

    # Imprimir tabla comparativa de colores
    print("\n" + "=" * 90)
    print(f"TABLA COMPARATIVA DE CONSUMO POR RESOLUCIÓN: {seccion.upper()}")
    print(f"Referencia de máxima resolución: {r_max} px/cm")
    print("=" * 90)

    header = f"{'Color HEX':<12} | "
    for r in resoluciones[:-1]:
        header += f"{r} px/cm (cm²) | Dif vs {r_max} | "
    header += f"{r_max} px/cm (cm²)"
    print(header)
    print("-" * 90)

    # Mostrar colores principales (hasta los 8 mayores o significativos)
    for c_hex in paleta_ref:
        area_max = alineados[r_max][c_hex]
        if area_max < 0.1 and all(alineados[r][c_hex] < 0.1 for r in resoluciones):
            continue
        fila = f"{c_hex:<12} | "
        for r in resoluciones[:-1]:
            area_r = alineados[r][c_hex]
            dif_pct = ((area_r - area_max) / area_max * 100.0) if area_max > 0.0 else 0.0
            fila += f"{area_r:>11.1f}   | {dif_pct:>+8.2f} % | "
        fila += f"{area_max:>12.1f}"
        print(fila)

    print("-" * 90)
    # Fila: Zona vacía (papel base)
    fila_vacia = f"{'Papel base':<12} | "
    for r in resoluciones[:-1]:
        av_r = resultados[r]["area_vacia_cm2"]
        av_max = datos_max["area_vacia_cm2"]
        dif_pct = ((av_r - av_max) / av_max * 100.0) if av_max > 0.0 else 0.0
        fila_vacia += f"{av_r:>11.1f}   | {dif_pct:>+8.2f} % | "
    fila_vacia += f"{datos_max['area_vacia_cm2']:>12.1f}"
    print(fila_vacia)

    # Fila: Total medido
    fila_tot = f"{'Total medido':<12} | "
    tot_max = sum(consumo_max_cons.values())
    for r in resoluciones[:-1]:
        tot_r = sum(alineados[r].values())
        dif_pct = ((tot_r - tot_max) / tot_max * 100.0) if tot_max > 0.0 else 0.0
        fila_tot += f"{tot_r:>11.1f}   | {dif_pct:>+8.2f} % | "
    fila_tot += f"{tot_max:>12.1f}"
    print(fila_tot)

    # Fila: Área geométrica exacta
    area_geom = datos_max["area_exacta_cm2"]
    fila_geom = f"{'Geom exacta':<12} | "
    for r in resoluciones[:-1]:
        fila_geom += f"{area_geom:>11.1f}   | {'-':>10} | "
    fila_geom += f"{area_geom:>12.1f}"
    print(fila_geom)

    # Fila: Tiempos totales
    fila_t = f"{'Tiempo total':<12} | "
    for r in resoluciones[:-1]:
        t_r = resultados[r]["t_total_r"]
        fila_t += f"{t_r:>10.2f} s | {'-':>10} | "
    fila_t += f"{datos_max['t_total_r']:>11.2f} s"
    print(fila_t)
    print("=" * 90 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula y analiza el consumo de papel en cm² por color de una sección de globo."
    )
    parser.add_argument("ruta_proyecto", type=str, help="Ruta al archivo .json del proyecto")
    parser.add_argument(
        "--seccion",
        type=str,
        required=True,
        choices=["superior", "inferior", "pico_A", "pico_B"],
        help="Sección a analizar (superior, inferior, pico_A, pico_B)",
    )
    parser.add_argument(
        "--px-por-cm",
        type=float,
        default=5.0,
        help="Píxeles por centímetro para corrida individual (por defecto: 5.0)",
    )
    parser.add_argument(
        "--colores",
        type=int,
        default=8,
        help="Número máximo de colores a agrupar (por defecto: 8)",
    )
    parser.add_argument(
        "--color-base",
        type=str,
        default="#FFFFFF",
        help="Color hexadecimal asignado a las zonas vacías (por defecto: #FFFFFF)",
    )
    parser.add_argument(
        "--estudio",
        action="store_true",
        help="Ejecuta estudio de resolución a 2, 3 y 5 px/cm (y 10 en pico_A) con tabla comparativa",
    )

    args = parser.parse_args()

    if args.estudio:
        ejecutar_estudio_resolucion(
            ruta_proyecto=args.ruta_proyecto,
            seccion=args.seccion,
            max_colores=args.colores,
            color_base_hex=args.color_base,
        )
    else:
        datos = medir_seccion_con_tiempos(
            ruta_proyecto=args.ruta_proyecto,
            seccion=args.seccion,
            px_por_cm=args.px_por_cm,
            max_colores=args.colores,
            color_base_hex=args.color_base,
        )
        imprimir_reporte_individual(datos, color_base_hex=args.color_base)


if __name__ == "__main__":
    main()
