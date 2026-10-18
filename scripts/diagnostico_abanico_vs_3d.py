"""
Diagnóstico comparativo entre el abanico 2D de la pestaña Diseño (referencia)
y la reconstrucción del abanico a partir del mapeo UV y texturas 3D.

Solo lectura sobre guardados/recursos_temp/prueba_imagen.json; no modifica ningún
archivo de usuario ni la lógica o el visor.
"""
import base64
import io
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

# Asegurar raíz del proyecto en sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from logic.proyecto.modelo import Proyecto
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.abanico import pieza_a_geometria_plana, abanico, contorno_abanico
from logic.geometria.malla_trompo import construir_malla, Cara
from logic.geometria.textura import mapear_textura, mapear_vertice_a_abanico, _calcular_tam_px, num_caras_lienzo
from logic.diseno.pintura import color_de_cara, EsquemaPintura
from logic.diseno.paleta import cargar_catalogo, color_por_id
from logic.exportacion.svg_abanico import _renderizar_capa_en_abanico
from logic.diseno.transformaciones import construir_grupo


def _hex_a_rgb(color_hex: str) -> Tuple[int, int, int]:
    h = color_hex.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def generar_svg_referencia_abanico(
    proy: Proyecto,
    res,
    seccion: str,
    carpeta_recursos: Path,
    color_papel_hex: str,
    max_px: int = 1024,
) -> Tuple[str, Tuple[int, int], Tuple[float, float, float, float], any]:
    """
    Genera el SVG del abanico de la sección usando exactamente la misma geometría,
    número de gajos (num_caras_lienzo: 1 para pico, tam_grupo para conos) y función de renderizado
    de capas (_renderizar_capa_en_abanico) que usa la pestaña Diseño en svg_abanico.
    """
    cfg = proy.config_secciones.get(seccion)
    esquema = cfg.esquema if (cfg and cfg.esquema) else proy.esquema
    if seccion == "pico":
        dibujar = "mitad" if (cfg and (cfg.diseno_modo == "mitad" or cfg.espejo)) else (cfg.diseno_modo if cfg else "una_cara")
    else:
        dibujar = cfg.dibujar if cfg else "completo"
    clave_dis = "pico_A" if seccion == "pico" else seccion
    diseno = proy.disenos.get(clave_dis)

    n = num_caras_lienzo(seccion, esquema=esquema, num_gajos=proy.entrada.num_gajos, dibujar=dibujar)
    pz = pieza_a_geometria_plana(res, proy.entrada, seccion)
    ab = abanico(pz, n=n, centrado=True)

    xmin, xmax = ab.caja_min_x, ab.caja_max_x
    ymin, ymax = ab.caja_min_y, ab.caja_max_y
    w_cm = ab.ancho_total
    h_cm = ab.alto_total

    px_w, px_h = _calcular_tam_px(w_cm, h_cm, max_px=max_px)

    # En svg_abanico: xs = cx_page + x * factor, ys = cy_page - (y - y_mid_cm) * factor
    # Con factor = 1.0 (unidades de cm directo en viewBox) y origen en (xmin, ymax):
    def to_svg(x: float, y: float) -> Tuple[float, float]:
        return (x - xmin, ymax - y)

    pasos_arco = max(8, n * 6)
    pts_contorno_cm = contorno_abanico(pz, n, dibujar=dibujar, pasos_arco=pasos_arco)
    pts_contorno_svg = [to_svg(x, y) for x, y in pts_contorno_cm]
    d_contorno = "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts_contorno_svg) + " Z"

    # Contorno completo para pintar el color de papel de fondo del abanico
    pts_full_cm = contorno_abanico(pz, n, dibujar="completo", pasos_arco=pasos_arco)
    pts_full_svg = [to_svg(x, y) for x, y in pts_full_cm]
    d_full = "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts_full_svg) + " Z"

    d_contorno_ref = ""
    if dibujar == "mitad":
        pts_ref_cm = [(-x, y) for x, y in pts_contorno_cm]
        pts_ref_svg = [to_svg(x, y) for x, y in pts_ref_cm]
        d_contorno_ref = "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts_ref_svg) + " Z"

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg width="{px_w}" height="{px_h}" viewBox="0 0 {w_cm:.4f} {h_cm:.4f}"',
        '     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',
        '  <defs>',
        '    <clipPath id="clip-abanico">',
        f'      <path d="{d_contorno}"/>',
        '    </clipPath>',
    ]
    if d_contorno_ref:
        lines.extend([
            '    <clipPath id="clip-abanico-reflejo">',
            f'      <path d="{d_contorno_ref}"/>',
            '    </clipPath>',
        ])
    lines.append('  </defs>')
    lines.append(f'  <rect width="100%" height="100%" fill="#ffffff"/>')
    lines.append(f'  <path d="{d_full}" fill="{color_papel_hex}"/>')

    if diseno and diseno.capas:
        if dibujar == "mitad":
            lines.append('  <g id="diseno-mitad-activa" clip-path="url(#clip-abanico)">')
            for c in diseno.capas:
                elem = _renderizar_capa_en_abanico(
                    c, to_svg, factor=1.0, carpeta_recursos=carpeta_recursos,
                    opacidad_mult=1.0, vista_previa=False, modo_fantasma=False
                )
                if elem:
                    lines.append(f'    {elem}')
            lines.append('  </g>')
            if d_contorno_ref:
                todas = construir_grupo(diseno, esquema, modo_lienzo="mitad")
                lines.append('  <g id="diseno-mitad-reflejo" clip-path="url(#clip-abanico-reflejo)">')
                for c in todas:
                    if c.id.endswith("_reflejo"):
                        elem = _renderizar_capa_en_abanico(
                            c, to_svg, factor=1.0, carpeta_recursos=carpeta_recursos,
                            opacidad_mult=1.0, vista_previa=False, modo_fantasma=False
                        )
                        if elem:
                            lines.append(f'    {elem}')
                lines.append('  </g>')
        else:
            lines.append('  <g id="diseno-completo" clip-path="url(#clip-abanico)">')
            for c in diseno.capas:
                elem = _renderizar_capa_en_abanico(
                    c, to_svg, factor=1.0, carpeta_recursos=carpeta_recursos,
                    opacidad_mult=1.0, vista_previa=False, modo_fantasma=False
                )
                if elem:
                    lines.append(f'    {elem}')
            lines.append('  </g>')

    lines.append('</svg>')
    caja_cm = (xmin, ymin, w_cm, h_cm)
    return "\n".join(lines), (px_w, px_h), caja_cm, ab


def rasterizar_svg_con_playwright(page, svg_str: str, tam_px: Tuple[int, int], color_fondo: Optional[str] = None) -> Image.Image:
    """Rasteriza un SVG en un canvas HTML5 con Playwright y devuelve una imagen PIL RGBA."""
    w, h = tam_px
    b64 = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
    data_url = page.evaluate(
        """([b64, w, h, bg]) => {
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
                    if (bg) {
                        ctx.fillStyle = bg;
                        ctx.fillRect(0, 0, w, h);
                    }
                    ctx.drawImage(img, 0, 0, w, h);
                    resolve(canvas.toDataURL('image/png'));
                };
                img.onerror = (e) => {
                    URL.revokeObjectURL(url);
                    reject('Error cargando SVG en Image');
                };
                img.src = url;
            });
        }""",
        [b64, w, h, color_fondo],
    )
    header, encoded = data_url.split(",", 1)
    png_bytes = base64.b64decode(encoded)
    return Image.open(io.BytesIO(png_bytes)).convert("RGB")


def warpear_triangulo_textura(
    img_dst: np.ndarray,
    mask_dst: np.ndarray,
    pts_dst: List[Tuple[float, float]],
    img_tex: Optional[np.ndarray],
    uvs_tex: List[Tuple[float, float]],
    color_papel_rgb: Tuple[int, int, int],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Pinta el triángulo definido por pts_dst (en píxeles de imagen destino)
    muestreando bilinealmente/por coordenadas baricéntricas la textura img_tex en uvs_tex.
    Devuelve la máscara booleana de los píxeles pertenecientes a este triángulo.
    """
    h_dst, w_dst, _ = img_dst.shape
    (x0, y0), (x1, y1), (x2, y2) = pts_dst

    xmin = max(0, int(np.floor(min(x0, x1, x2))))
    xmax = min(w_dst - 1, int(np.ceil(max(x0, x1, x2))))
    ymin = max(0, int(np.floor(min(y0, y1, y2))))
    ymax = min(h_dst - 1, int(np.ceil(max(y0, y1, y2))))

    tri_mask = np.zeros((h_dst, w_dst), dtype=bool)
    if xmin > xmax or ymin > ymax:
        return img_dst, tri_mask

    xs = np.arange(xmin, xmax + 1) + 0.5
    ys = np.arange(ymin, ymax + 1) + 0.5
    gx, gy = np.meshgrid(xs, ys)

    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denom) < 1e-9:
        return img_dst, tri_mask

    w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
    w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
    w2 = 1.0 - w0 - w1

    eps = -1e-4
    inside = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
    if not np.any(inside):
        return img_dst, tri_mask

    sub_mask = tri_mask[ymin:ymax + 1, xmin:xmax + 1]
    sub_mask[inside] = True
    mask_dst[ymin:ymax + 1, xmin:xmax + 1] |= inside

    if img_tex is None or len(uvs_tex) < 3:
        sub_img = img_dst[ymin:ymax + 1, xmin:xmax + 1]
        sub_img[inside] = color_papel_rgb
        return img_dst, tri_mask

    (u0, v0), (u1, v1), (u2, v2) = uvs_tex
    u = w0[inside] * u0 + w1[inside] * u1 + w2[inside] * u2
    v = w0[inside] * v0 + w1[inside] * v1 + w2[inside] * v2

    # Convención de visor.js: texture.flipY = false
    #En WebGL con flipY=false, v=0 es la fila superior (py=0) y v=1 es la fila inferior (py=H-1)
    # Pero en textura.py: v = (y - ymin) / h (v=0 abajo, v=1 arriba) y el SVG tiene <g transform="scale(1,-1)">
    # con viewBox min_y = -ymax (arriba del canvas es ymax, que corresponde a v=1).
    # Vamos a verificar: si en el canvas de la textura py=0 es ymax (arriba), y en Three.js con flipY=false
    # v=0 lee la fila 0 del canvas (arriba) o v=1 lee la fila H-1 (abajo)!
    # Usemos exactamente cómo Three.js muestrea con flipY=false:
    # En WebGL texImage2D con UNPACK_FLIP_Y_WEBGL=false: la primera fila subida (fila 0 del canvas HTML, arriba)
    # queda en t=0 (v=0)! Y la última fila del canvas (fila H-1, abajo) queda en t=1 (v=1)!
    h_tex, w_tex, _ = img_tex.shape
    u_clamped = np.clip(u, 0.0, 1.0)
    v_clamped = np.clip(v, 0.0, 1.0)

    tx = np.clip(np.round(u_clamped * (w_tex - 1)).astype(int), 0, w_tex - 1)
    # Con flipY = false en Three.js, v=0 mapea a fila 0 del canvas y v=1 mapea a fila h_tex-1:
    ty = np.clip(np.round(v_clamped * (h_tex - 1)).astype(int), 0, h_tex - 1)

    sub_img = img_dst[ymin:ymax + 1, xmin:xmax + 1]
    sub_img[inside] = img_tex[ty, tx]

    return img_dst, tri_mask


def reconstruir_abanico_seccion(
    page,
    proy: Proyecto,
    res,
    malla,
    mapa_tex,
    seccion: str,
    carpeta_recursos: Path,
    max_px: int = 1024,
    umbral_diff: int = 30,
    flip_y_webgl: bool = False,
) -> Dict[str, any]:
    """
    Rasteriza el abanico de referencia (ref) y reconstruye el abanico desde las caras 3D (rec)
    para una sección dada, devolviendo los arreglos de imagen, máscara, porcentaje global de
    diferencia y estadísticas por cara.
    """
    catalogo = cargar_catalogo()
    pintura = proy.pintura or EsquemaPintura()
    caras_sec = [(idx, c) for idx, c in enumerate(malla.caras) if c.seccion == seccion]
    id_col_base = color_de_cara(pintura, caras_sec[0][1], proy.esquema, proy.entrada.num_gajos)
    col_papel_hex = color_por_id(id_col_base, catalogo).hex.lower()

    svg_ref, tam_px, caja_ref, ab_ref = generar_svg_referencia_abanico(
        proy, res, seccion, carpeta_recursos, col_papel_hex, max_px=max_px
    )
    img_ref_pil = rasterizar_svg_con_playwright(page, svg_ref, tam_px, color_fondo="#ffffff")
    arr_ref = np.array(img_ref_pil)

    px_w, px_h = tam_px
    xmin, ymin, w_cm, h_cm = caja_ref
    ymax = ymin + h_cm

    def cm_a_px_ref(x_cm: float, y_cm: float) -> Tuple[float, float]:
        px = ((x_cm - xmin) / w_cm) * px_w
        py = ((ymax - y_cm) / h_cm) * px_h
        return (px, py)

    arr_rec = np.full((px_h, px_w, 3), 255, dtype=np.uint8)
    mask_abanico = np.zeros((px_h, px_w), dtype=bool)

    if seccion in ("superior", "inferior"):
        n_grupo = ab_ref.n
        caras_grupo = [(idx, c) for idx, c in caras_sec if c.gajo < n_grupo]
    else:
        caras_grupo = [(idx, c) for idx, c in caras_sec if c.gajo == 0 and c.hilera == 0 and (c.sub or 0) < ab_ref.n]

    cache_tex_sec: Dict[Tuple[str, str], np.ndarray] = {}
    stats_caras_sec = []

    for idx_cara, cara in caras_grupo:
        clave_tex, uvs_cara = mapa_tex.caras_uv[idx_cara]
        id_col = color_de_cara(pintura, cara, proy.esquema, proy.entrada.num_gajos)
        col_hex = color_por_id(id_col, catalogo).hex.lower()
        col_rgb = _hex_a_rgb(col_hex)

        img_tex_np = None
        if clave_tex and clave_tex in mapa_tex.texturas:
            info_t = mapa_tex.texturas[clave_tex]
            if info_t.svg:
                par = (clave_tex, col_hex)
                if par not in cache_tex_sec:
                    im_t = np.array(rasterizar_svg_con_playwright(page, info_t.svg, info_t.tam_px, color_fondo=col_hex))
                    if flip_y_webgl:
                        im_t = im_t[::-1, :, :]
                    cache_tex_sec[par] = im_t
                img_tex_np = cache_tex_sec[par]

        i_pos = (cara.sub if seccion == "pico" else cara.gajo) % ab_ref.n
        pts_2d_cm = [mapear_vertice_a_abanico(pt_uv_cm, ab_ref, i_pos) for pt_uv_cm in cara.uv_cm]
        pts_2d_px = [cm_a_px_ref(x, y) for x, y in pts_2d_cm]

        if len(pts_2d_px) == 3:
            tris = [(pts_2d_px, uvs_cara)]
        else:
            tris = [
                ([pts_2d_px[0], pts_2d_px[1], pts_2d_px[2]], [uvs_cara[0], uvs_cara[1], uvs_cara[2]]),
                ([pts_2d_px[0], pts_2d_px[2], pts_2d_px[3]], [uvs_cara[0], uvs_cara[2], uvs_cara[3]]),
            ]

        mask_cara_total = np.zeros((px_h, px_w), dtype=bool)
        for tri_px, tri_uv in tris:
            arr_rec, m_tri = warpear_triangulo_textura(
                arr_rec, mask_abanico, tri_px, img_tex_np, tri_uv, col_rgb
            )
            mask_cara_total |= m_tri

        n_px_cara = int(np.sum(mask_cara_total))
        if n_px_cara > 0:
            diff_cara = np.sum(np.abs(arr_ref[mask_cara_total].astype(int) - arr_rec[mask_cara_total].astype(int)), axis=1)
            n_dist_cara = int(np.sum(diff_cara > umbral_diff))
            pct_cara = (n_dist_cara / n_px_cara) * 100.0
        else:
            pct_cara = 0.0

        etiqueta_gajo = f"g={cara.gajo}" if seccion != "pico" else f"g={cara.gajo},h={cara.hilera},sub={cara.sub}"
        stats_caras_sec.append({
            "seccion": seccion,
            "gajo": etiqueta_gajo,
            "clave_tex": str(clave_tex),
            "pct_distinto": pct_cara,
            "uv_min_max": (
                min(u for u, v in uvs_cara), max(u for u, v in uvs_cara),
                min(v for u, v in uvs_cara), max(v for u, v in uvs_cara),
            ),
        })

    diff_abs = np.sum(np.abs(arr_ref.astype(int) - arr_rec.astype(int)), axis=2)
    es_distinto = (diff_abs > umbral_diff) & mask_abanico
    arr_dif = np.full((px_h, px_w, 3), 255, dtype=np.uint8)
    arr_dif[es_distinto] = [220, 30, 30]

    total_px_ab = int(np.sum(mask_abanico))
    dist_px_ab = int(np.sum(es_distinto))
    pct_sec = (dist_px_ab / total_px_ab * 100.0) if total_px_ab > 0 else 0.0

    return {
        "seccion": seccion,
        "tam_px": f"{px_w}x{px_h}",
        "px_abanico": total_px_ab,
        "px_distintos": dist_px_ab,
        "pct_distinto": pct_sec,
        "arr_ref": arr_ref,
        "arr_rec": arr_rec,
        "arr_dif": arr_dif,
        "stats_caras": stats_caras_sec,
    }


def _preparar_carpeta_recursos_lectura(ruta_json: Path) -> Tuple[Path, Optional[object]]:
    """
    Si algunos recursos citados por prueba_imagen.json están en Downloads/prueba_imagen_recursos
    o con otro hash en guardados/recursos_temp, arma un directorio temporal de solo lectura
    combinándolos para no tocar ni modificar guardados/.
    """
    import shutil
    import tempfile

    carpeta_local = ruta_json.parent
    downloads_rec = Path.home() / "Downloads" / "prueba_imagen_recursos"
    if not downloads_rec.exists():
        return carpeta_local, None

    tmp_obj = tempfile.TemporaryDirectory()
    tmp_dir = Path(tmp_obj.name)

    for orig_dir in [downloads_rec, carpeta_local]:
        if orig_dir.exists():
            for f in orig_dir.iterdir():
                if f.is_file():
                    dst = tmp_dir / f.name
                    if not dst.exists():
                        shutil.copy2(f, dst)

    return tmp_dir, tmp_obj


def ejecutar_diagnostico():
    ruta_json = ROOT / "guardados" / "recursos_temp" / "prueba_imagen.json"
    if not ruta_json.exists():
        print(f"ERROR: No existe {ruta_json}")
        sys.exit(1)

    data = json.loads(ruta_json.read_text(encoding="utf-8"))
    proy = Proyecto.from_dict(data)
    # Paso 4 del prompt: con el pico en modo espejo, el diagnóstico debe dar < 5% de diferencia en el pico
    if "pico" in proy.config_secciones:
        proy.config_secciones["pico"].diseno_modo = "mitad"
        proy.config_secciones["pico"].espejo = True
        proy.config_secciones["pico"].dibujar = "mitad"
    carpeta_recursos, _tmp_holder = _preparar_carpeta_recursos_lectura(ruta_json)

    calc = TrompoEstrellaCalculator()
    res = calc.calcular(proy.entrada)
    malla = construir_malla(proy.entrada, res)
    catalogo = cargar_catalogo()

    mapa_tex = mapear_textura(
        entrada=proy.entrada,
        resultado=res,
        malla=malla,
        configuraciones=proy.config_secciones,
        disenos=proy.disenos,
        carpeta_recursos=carpeta_recursos,
        max_px=1024,
    )

    out_dir = ROOT / "docs" / "capturas"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Umbral de diferencia por píxel: distancia Manhattan |dR| + |dG| + |dB| > 30 (promedio > 10 por canal de 255)
    UMBRAL_DIFF = 30

    resumen_secciones = []
    stats_caras = []

    # Leer de visor.js cómo está configurado texture.flipY realmente
    import re
    visor_js = (ROOT / "app_flet" / "assets" / "visor3d" / "visor.js").read_text(encoding="utf-8")
    m_flip = re.search(r"texture\.flipY\s*=\s*(true|false)", visor_js)
    flip_y_actual = (m_flip.group(1) == "true") if m_flip else True

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("<html><body></body></html>")

        for seccion in ["superior", "pico", "inferior"]:
            rep = reconstruir_abanico_seccion(
                page=page,
                proy=proy,
                res=res,
                malla=malla,
                mapa_tex=mapa_tex,
                seccion=seccion,
                carpeta_recursos=carpeta_recursos,
                max_px=1024,
                umbral_diff=UMBRAL_DIFF,
                flip_y_webgl=flip_y_actual,
            )

            Image.fromarray(rep["arr_ref"]).save(out_dir / f"ref_{seccion}.png")
            Image.fromarray(rep["arr_rec"]).save(out_dir / f"rec_{seccion}.png")
            Image.fromarray(rep["arr_dif"]).save(out_dir / f"dif_{seccion}.png")

            resumen_secciones.append({
                "seccion": seccion,
                "tam_px": rep["tam_px"],
                "px_abanico": rep["px_abanico"],
                "px_distintos": rep["px_distintos"],
                "pct_distinto": rep["pct_distinto"],
            })
            stats_caras.extend(rep["stats_caras"])

        # Regenerar las 4 capturas del visor 3D (frontal día/noche, pico día/noche)
        from logic.exportacion.escena3d import escena_a_dict
        from logic.exportacion.visor3d import ServidorVisor
        import time

        escena = escena_a_dict(
            proy.entrada,
            res,
            esquema_pintura=proy.pintura,
            esquema_diseno=proy.esquema,
            configuraciones=proy.config_secciones,
            disenos=proy.disenos,
            carpeta_recursos=carpeta_recursos,
        )
        servidor = ServidorVisor(puerto=0)
        servidor.iniciar()
        servidor.actualizar_datos_escena(escena)
        try:
            page_v = browser.new_page(viewport={"width": 1280, "height": 800})
            page_v.goto(servidor.url)
            page_v.wait_for_selector("#canvas-container canvas")
            time.sleep(2.5)

            # Vista frontal noche (por defecto)
            page_v.screenshot(path=str(out_dir / "visor_frontal_noche.png"))

            # Vista frontal día
            page_v.click("#btn-dia")
            time.sleep(0.5)
            page_v.screenshot(path=str(out_dir / "visor_frontal_dia.png"))

            # Acercar cámara a la zona de los picos
            page_v.evaluate("""() => {
                if (currentMetadata && currentMetadata.bbox) {
                    const bbox = currentMetadata.bbox;
                    const c = bbox.centro;
                    const maxDim = Math.max(
                        bbox.max[0] - bbox.min[0],
                        bbox.max[1] - bbox.min[1],
                        bbox.max[2] - bbox.min[2]
                    );
                    const zPico = c[2] + maxDim * 0.08;
                    controls.target.set(c[0], c[1], zPico);
                    camera.position.set(c[0], c[1] - maxDim * 0.85, zPico + maxDim * 0.05);
                    camera.lookAt(c[0], c[1], zPico);
                    controls.update();
                    renderer.render(scene, camera);
                }
            }""")
            time.sleep(0.4)
            page_v.screenshot(path=str(out_dir / "visor_pico_dia.png"))

            page_v.click("#btn-noche")
            time.sleep(0.4)
            page_v.screenshot(path=str(out_dir / "visor_pico_noche.png"))
            page_v.close()
        finally:
            servidor.detener()

        browser.close()

    # Imprimir reporte
    print("=" * 78)
    print("UMBRAL DE DIFERENCIA: |dR| + |dG| + |dB| > 30 (~10 niveles por canal RGB sobre 255) para")
    print("ignorar pequeñas diferencias de antialiasing en bordes y compresión JPEG.")
    print("=" * 78)
    print(f"{'SECCIÓN':<12} | {'RESOLUCIÓN':<12} | {'PX ABANICO':>12} | {'PX DISTINTOS':>14} | {'% DISTINTO':>10}")
    print("-" * 78)
    for r in resumen_secciones:
        print(f"{r['seccion']:<12} | {r['tam_px']:<12} | {r['px_abanico']:>12} | {r['px_distintos']:>14} | {r['pct_distinto']:>9.2f}%")
    print("=" * 78)

    print("\nTOP 10 PEORES CARAS / GAJOS RECONSTRUIDOS:")
    print(f"{'SECCIÓN':<12} | {'GAJO / CARA':<18} | {'TEXTURA':<12} | {'% DISTINTO':>10} | {'RANGO UV (u_min..u_max, v_min..v_max)'}")
    print("-" * 95)
    peores = sorted(stats_caras, key=lambda x: x["pct_distinto"], reverse=True)[:10]
    for p in peores:
        u0, u1, v0, v1 = p["uv_min_max"]
        print(f"{p['seccion']:<12} | {p['gajo']:<18} | {p['clave_tex']:<12} | {p['pct_distinto']:>9.2f}% | u=[{u0:.2f}..{u1:.2f}], v=[{v0:.2f}..{v1:.2f}]")
    print("-" * 95)


if __name__ == "__main__":
    ejecutar_diagnostico()
