"""Script para rasterizar el diseño y la silueta exacta de una sección de globo."""

from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path
import sys
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

# Asegurar importación de módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.abanico import area_poligono, contorno_abanico, abanico, pieza_a_geometria_plana
from logic.geometria.textura import svg_textura, num_caras_lienzo
from logic.papel.silueta import mascara_silueta
from logic.proyecto.modelo import cargar_proyecto, obtener_carpeta_recursos


def rasterizar_svg_transparente(
    page,
    svg_str: str,
    tam_px: Tuple[int, int],
) -> Image.Image:
    """Rasteriza una cadena SVG en un canvas HTML5 con fondo transparente mediante Playwright."""
    w, h = tam_px
    b64 = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
    data_url = page.evaluate(
        """([b64, w, h]) => {
            return new Promise((resolve, reject) => {
                const bin = atob(b64);
                const bytes = new Uint8Array(bin.length);
                for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
                const blob = new Blob([bytes], {type: 'image/svg+xml;charset=utf-8'});
                const url = URL.createObjectURL(blob);
                const img = new Image();
                img.onload = () => {
                    URL.revokeObjectURL(url);
                    const canvas = document.createElement('canvas');
                    canvas.width = w;
                    canvas.height = h;
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, w, h);
                    ctx.drawImage(img, 0, 0, w, h);
                    resolve(canvas.toDataURL('image/png'));
                };
                img.onerror = () => {
                    URL.revokeObjectURL(url);
                    reject('Error cargando SVG en elemento Image');
                };
                img.src = url;
            });
        }""",
        [b64, w, h],
    )
    header, encoded = data_url.split(",", 1)
    png_bytes = base64.b64decode(encoded)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def procesar_seccion(
    ruta_proyecto: str | Path,
    seccion: str,
    px_por_cm: float = 5.0,
    page_playwright=None,
) -> dict:
    """Rasteriza el diseño y silueta para una sección y devuelve estadísticas y rutas generadas."""
    proyecto = cargar_proyecto(str(ruta_proyecto))
    calc = TrompoEstrellaCalculator()
    resultado = calc.calcular(proyecto.entrada)

    # Identificar sección geométrica y claves de configuración
    if seccion.startswith("pico"):
        seccion_geom = "pico"
        clave_textura = seccion
        cfg_seccion = proyecto.config_secciones.get("pico")
        diseno = proyecto.disenos.get(seccion) or proyecto.disenos.get("pico")
        espejo_pico = bool(cfg_seccion and (cfg_seccion.diseno_modo == "mitad" or cfg_seccion.espejo))
        dibujar = "mitad" if espejo_pico else "una_cara"
    else:
        seccion_geom = seccion
        clave_textura = seccion
        cfg_seccion = proyecto.config_secciones.get(seccion)
        diseno = proyecto.disenos.get(seccion)
        dibujar = cfg_seccion.dibujar if cfg_seccion else "completo"

    esquema = cfg_seccion.esquema if (cfg_seccion and seccion_geom != "pico") else None
    pz = pieza_a_geometria_plana(resultado, proyecto.entrada, seccion_geom)
    n = num_caras_lienzo(seccion_geom, esquema=esquema, num_gajos=proyecto.entrada.num_gajos, dibujar=dibujar)

    ab = abanico(pz, n=n, centrado=True)
    caja_cm = (ab.caja_min_x, ab.caja_min_y, ab.ancho_total, ab.alto_total)
    w_cm = ab.ancho_total
    h_cm = ab.alto_total

    w_px = max(1, int(round(w_cm * px_por_cm)))
    h_px = max(1, int(round(h_cm * px_por_cm)))
    cm_por_px_x = w_cm / w_px
    cm_por_px_y = h_cm / h_px

    # Silueta geométrica exacta
    pasos_arco = max(8, n * 6)
    pts_contorno = contorno_abanico(pz, n, dibujar=dibujar, pasos_arco=pasos_arco)

    mask_act, cm_por_px = mascara_silueta(pts_contorno, caja_cm, px_por_cm)
    if dibujar == "mitad":
        pts_contorno_ref = [(-x, y) for x, y in pts_contorno]
        mask_ref, _ = mascara_silueta(pts_contorno_ref, caja_cm, px_por_cm)
        mascara = mask_act | mask_ref
        area_exacta = area_poligono(pts_contorno) * 2.0
    else:
        mascara = mask_act
        area_exacta = area_poligono(pts_contorno)

    area_mask = float(np.sum(mascara) * (cm_por_px ** 2))
    diff_pct = abs(area_mask - area_exacta) / area_exacta * 100.0

    # Carpeta de recursos del proyecto
    carpeta_recursos = obtener_carpeta_recursos(ruta_proyecto)

    # Generación de SVG de textura
    svg_str = svg_textura(
        clave=clave_textura,
        entrada=proyecto.entrada,
        resultado=resultado,
        diseno=diseno,
        config_seccion=cfg_seccion,
        carpeta_recursos=carpeta_recursos,
        max_px=max(w_px, h_px),
    )

    # Rasterizado con Playwright
    t0 = time.perf_counter()
    if page_playwright is not None:
        img_rgba = rasterizar_svg_transparente(page_playwright, svg_str, (w_px, h_px))
    else:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": max(800, w_px), "height": max(800, h_px)})
            img_rgba = rasterizar_svg_transparente(page, svg_str, (w_px, h_px))
            browser.close()
    t_raster = time.perf_counter() - t0

    # Guardar salidas en scripts/_salida/
    salida_dir = Path(__file__).resolve().parent / "_salida"
    salida_dir.mkdir(parents=True, exist_ok=True)

    ruta_seccion_png = salida_dir / f"seccion_{seccion}.png"
    ruta_silueta_png = salida_dir / f"silueta_{seccion}.png"

    img_rgba.save(ruta_seccion_png, format="PNG")

    silueta_rgba = np.zeros((h_px, w_px, 4), dtype=np.uint8)
    silueta_rgba[mascara] = [255, 255, 255, 255]
    Image.fromarray(silueta_rgba, mode="RGBA").save(ruta_silueta_png, format="PNG")

    return {
        "seccion": seccion,
        "tam_px": (w_px, h_px),
        "cm_por_px_x": cm_por_px_x,
        "cm_por_px_y": cm_por_px_y,
        "cm_por_px": cm_por_px,
        "area_exacta_cm2": area_exacta,
        "area_mascara_cm2": area_mask,
        "diff_pct": diff_pct,
        "t_raster_s": t_raster,
        "ruta_seccion": ruta_seccion_png,
        "ruta_silueta": ruta_silueta_png,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rasteriza el diseño y silueta de una sección con escala conocida."
    )
    parser.add_argument("ruta_proyecto", type=str, help="Ruta al archivo .json del proyecto")
    parser.add_argument(
        "--seccion",
        type=str,
        required=True,
        choices=["superior", "inferior", "pico_A", "pico_B"],
        help="Sección a rasterizar (superior, inferior, pico_A, pico_B)",
    )
    parser.add_argument(
        "--px-por-cm",
        type=float,
        default=5.0,
        help="Píxeles por centímetro (por defecto: 5.0)",
    )

    args = parser.parse_args()

    res = procesar_seccion(args.ruta_proyecto, args.seccion, px_por_cm=args.px_por_cm)

    w_px, h_px = res["tam_px"]
    print("\n" + "=" * 62)
    print(f"RASTERIZADO DE SECCIÓN: {res['seccion']}")
    print("=" * 62)
    print(f"Tamaño en píxeles      : {w_px} × {h_px} px")
    print(f"cm_por_px (X)          : {res['cm_por_px_x']:.5f} cm/px")
    print(f"cm_por_px (Y)          : {res['cm_por_px_y']:.5f} cm/px")
    print(f"cm_por_px (nominal)    : {res['cm_por_px']:.5f} cm/px")
    print(f"Área exacta (polígono) : {res['area_exacta_cm2']:.2f} cm²")
    print(f"Área máscara (píxeles) : {res['area_mascara_cm2']:.2f} cm²")
    print(f"Diferencia de área     : {res['diff_pct']:.4f} %")
    print(f"Tiempo de rasterizado  : {res['t_raster_s']:.3f} s")
    print("-" * 62)
    print(f"Imagen diseño          : {res['ruta_seccion']}")
    print(f"Máscara silueta        : {res['ruta_silueta']}")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
