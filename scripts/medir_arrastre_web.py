#!/usr/bin/env python3
"""Script reproducible con Playwright (modo web) para medir el rendimiento de arrastre en Editar capa.

Simula con ratón real en navegador headless para una capa PNG (~180 KB) y una capa SVG:
- 3 arrastres del cuerpo:
  1) Lento: 60 pasos en 1.5 s
  2) Normal: 30 pasos en 0.6 s
  3) Brusco: 6 pasos en 0.1 s
- 1 arrastre de un tirador ('br'):
  4) Tirador normal: 30 pasos en 0.6 s

Mide:
- Eventos recibidos por Python en el manejador
- Tiempo de procesamiento por evento en Python (media y máximo en ms, con time.perf_counter)
- Llamadas a control.update() por evento y tramas/bytes WebSocket enviados al cliente por evento
- Retraso final (ms): tiempo desde mouse.up() hasta que el marco queda en su posición final
- Error de posición (cm): diferencia entre el desplazamiento esperado del cursor y el desplazamiento real de la capa

Uso:
  python scripts/medir_arrastre_web.py antes
  python scripts/medir_arrastre_web.py despues
"""

import os
from pathlib import Path
import socket
import statistics
import sys
import threading
import time
from typing import Dict, List

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import flet as ft
from PIL import Image
from playwright.sync_api import sync_playwright

from app_flet import tema
from app_flet.vistas.trompo import VistaTrompo
from logic.registro import inicializar_registro


def puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def crear_png_180kb(ruta: Path) -> int:
    """Genera un archivo PNG determinista de ~180 KB."""
    w, h = 520, 520
    buf = bytearray(w * h * 4)
    val = 1234567
    for i in range(0, len(buf), 4):
        val = (val * 1103515245 + 12345) & 0x7FFFFFFF
        buf[i] = (val >> 16) & 0xFF
        buf[i + 1] = (val >> 8) & 0xFF
        buf[i + 2] = val & 0xFF
        buf[i + 3] = 255
    img = Image.frombytes("RGBA", (w, h), bytes(buf))
    # Ajustar tamaño a ~180 KB recortando según compresión zlib
    img_crop = img.crop((0, 0, 250, 250))
    img_crop.save(ruta, format="PNG", compress_level=6)
    return ruta.stat().st_size


def ejecutar_medicion(etapa: str) -> List[Dict]:
    os.chdir(RAIZ)
    rec_dir = RAIZ / "guardados" / "recursos_temp"
    rec_dir.mkdir(parents=True, exist_ok=True)

    ruta_png = rec_dir / "_bench_180kb.png"
    bytes_png = crear_png_180kb(ruta_png)
    ruta_svg = RAIZ / "docs" / "ejemplos" / "disenos" / "mosaico_geometrico.svg"

    port = puerto_libre()
    estado = {
        "vista": None,
        "page": None,
        "capa_png_id": None,
        "capa_svg_id": None,
        "listo": threading.Event(),
    }

    # Estado de instrumentación por gesto
    instrumentacion = {
        "activo": False,
        "en_movimiento": False,
        "eventos_recibidos": 0,
        "tiempos_handler_ms": [],
        "updates_control": 0,
        "ws_mensajes_enviados": 0,
        "ws_bytes_enviados": 0,
        "ultimo_cambio_ui_ts": 0.0,
        "stack_origin_global": None,
    }

    # Hook global en ft.Control.update para contar cuántas llamadas a .update() ocurren
    orig_control_update = ft.Control.update

    def hooked_control_update(self_ctrl, *args, **kwargs):
        if instrumentacion["activo"]:
            instrumentacion["ultimo_cambio_ui_ts"] = time.perf_counter()
        if instrumentacion["en_movimiento"]:
            instrumentacion["updates_control"] += 1
        return orig_control_update(self_ctrl, *args, **kwargs)

    ft.Control.update = hooked_control_update

    def app_target(page: ft.Page):
        inicializar_registro()
        page.title = "Benchmark Arrastre Marco"
        page.theme = tema.tema_oscuro
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0

        vista = VistaTrompo()
        page.add(vista)
        vista.on_calcular(None)

        c_png = vista.controlador.anadir_capa(str(ruta_png))
        c_png.nombre = f"png_{bytes_png // 1024}kb"
        c_png.x = 0.0
        c_png.y = 175.0
        c_png.ancho = 45.0
        c_png.alto = 45.0

        c_svg = vista.controlador.anadir_capa(str(ruta_svg))
        c_svg.nombre = "mosaico_svg"
        c_svg.x = 0.0
        c_svg.y = 175.0
        c_svg.ancho = 45.0
        c_svg.alto = 45.0

        vista.controlador.capa_seleccionada_id = c_png.id
        vista.controlador.actualizar_svg_diseno(modo_fantasma=False)
        vista.tabs.selected_index = 4
        vista._sync_controlador_a_vista(vista.controlador.get_view_model())
        page.update()

        # Instrumentar manejadores de MarcoEdicion
        marco = vista.pestana_diseno.gestor_visor.marco_edicion

        orig_cuerpo_start = marco._on_cuerpo_pan_start
        orig_cuerpo_update = marco._on_cuerpo_pan_update
        orig_cuerpo_end = marco._on_cuerpo_pan_end
        orig_tir_start = marco._on_tirador_pan_start
        orig_tir_update = marco._on_tirador_pan_update
        orig_tir_end = marco._on_tirador_pan_end

        def wrap_cuerpo_start(e):
            gp = getattr(e, "global_position", None)
            lp = getattr(e, "local_position", None)
            if gp and lp and hasattr(gp, "x") and hasattr(lp, "x"):
                # Calcular origen global de stack_visor a partir de la posición absoluta de caja_marco
                g_pos = getattr(marco, "grupo_edicion", None)
                left_g = float(g_pos.left or 0.0) if g_pos is not None else 0.0
                top_g = float(g_pos.top or 0.0) if g_pos is not None else 0.0
                left_c = left_g + float(marco.caja_marco.left or 0.0)
                top_c = top_g + float(marco.caja_marco.top or 0.0)
                instrumentacion["stack_origin_global"] = (
                    gp.x - lp.x - left_c,
                    gp.y - lp.y - top_c,
                )
            return orig_cuerpo_start(e)

        def wrap_cuerpo_update(e):
            t0 = time.perf_counter()
            res = orig_cuerpo_update(e)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            if instrumentacion["activo"]:
                instrumentacion["eventos_recibidos"] += 1
                instrumentacion["tiempos_handler_ms"].append(dt_ms)
                instrumentacion["ultimo_cambio_ui_ts"] = time.perf_counter()
            return res

        def wrap_cuerpo_end(e):
            res = orig_cuerpo_end(e)
            if instrumentacion["activo"]:
                instrumentacion["ultimo_cambio_ui_ts"] = time.perf_counter()
            return res

        def wrap_tir_start(tid, e):
            return orig_tir_start(tid, e)

        def wrap_tir_update(tid, e):
            t0 = time.perf_counter()
            res = orig_tir_update(tid, e)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            if instrumentacion["activo"]:
                instrumentacion["eventos_recibidos"] += 1
                instrumentacion["tiempos_handler_ms"].append(dt_ms)
                instrumentacion["ultimo_cambio_ui_ts"] = time.perf_counter()
            return res

        def wrap_tir_end(tid, e):
            res = orig_tir_end(tid, e)
            if instrumentacion["activo"]:
                instrumentacion["ultimo_cambio_ui_ts"] = time.perf_counter()
            return res

        marco._on_cuerpo_pan_start = wrap_cuerpo_start
        marco._on_cuerpo_pan_update = wrap_cuerpo_update
        marco._on_cuerpo_pan_end = wrap_cuerpo_end
        marco.detector_cuerpo.on_pan_start = wrap_cuerpo_start
        marco.detector_cuerpo.on_pan_update = wrap_cuerpo_update
        marco.detector_cuerpo.on_pan_end = wrap_cuerpo_end

        marco._on_tirador_pan_start = wrap_tir_start
        marco._on_tirador_pan_update = wrap_tir_update
        marco._on_tirador_pan_end = wrap_tir_end
        for tid, det in marco.detectores_tiradores.items():
            det.on_pan_start = lambda e, t=tid: wrap_tir_start(t, e)
            det.on_pan_update = lambda e, t=tid: wrap_tir_update(t, e)
            det.on_pan_end = lambda e, t=tid: wrap_tir_end(t, e)

        estado["vista"] = vista
        estado["page"] = page
        estado["capa_png_id"] = c_png.id
        estado["capa_svg_id"] = c_svg.id
        estado["listo"].set()

    resultados: List[Dict] = []

    def hilo_playwright():
        time.sleep(2.5)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome", headless=True)
                context = browser.new_context(viewport={"width": 1366, "height": 820})
                web_page = context.new_page()

                def on_ws(ws):
                    def on_frame_received(payload):
                        if instrumentacion["en_movimiento"]:
                            instrumentacion["ws_mensajes_enviados"] += 1
                            tam = len(payload) if isinstance(payload, (bytes, str)) else 0
                            instrumentacion["ws_bytes_enviados"] += tam

                    ws.on("framereceived", on_frame_received)

                web_page.on("websocket", on_ws)
                web_page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
                estado["listo"].wait(timeout=15)
                time.sleep(5.0)

                vista = estado["vista"]
                flet_page = estado["page"]
                pestana = vista.pestana_diseno
                marco = pestana.gestor_visor.marco_edicion

                def preparar_capa(capa_id: str):
                    vista.controlador.capa_seleccionada_id = capa_id
                    c = vista.controlador.obtener_capa_seleccionada()
                    c.x = 0.0
                    c.y = 175.0
                    c.ancho = 45.0
                    c.alto = 45.0
                    c.rotacion = 0.0
                    vista.controlador.mantener_proporcion = False
                    pestana.cambiar_modo_interaccion("editar")
                    conv = pestana.gestor_visor.obtener_conversion()
                    carp = vista.controlador.obtener_carpeta_recursos_activa()
                    marco.mostrar(c, conv, carp, mantener_proporcion=False)
                    try:
                        flet_page.update()
                    except Exception:
                        pass
                    time.sleep(0.6)

                # Calibrar stack_origin_global con un micro-arrastre inicial sobre el centro del visor
                preparar_capa(estado["capa_png_id"])
                # El centro del marco en (x=0, y=175) cae aprox en (1015, 360) en ventana 1366x820
                conv0 = pestana.gestor_visor.obtener_conversion()
                px_cx0, py_cy0 = conv0.plano_a_px(22.5, 197.5)
                # Estimación inicial antes de calibrar:
                est_ox, est_oy = 676.0, 203.0
                web_page.mouse.move(est_ox + px_cx0, est_oy + py_cy0)
                web_page.mouse.down()
                web_page.mouse.move(est_ox + px_cx0 + 5, est_oy + py_cy0 + 5, steps=2)
                time.sleep(0.1)
                web_page.mouse.up()
                time.sleep(0.3)

                ox, oy = instrumentacion["stack_origin_global"] or (est_ox, est_oy)
                print(f"[Calibración] Origen global de stack_visor: ({ox:.1f}, {oy:.1f})", flush=True)

                escenarios = [
                    ("cuerpo_lento", "cuerpo", 60, 1.5, 90.0, -60.0),
                    ("cuerpo_normal", "cuerpo", 30, 0.6, 90.0, -60.0),
                    ("cuerpo_brusco", "cuerpo", 6, 0.1, 90.0, -60.0),
                    ("tirador_br", "br", 30, 0.6, 45.0, 35.0),
                ]

                for tipo_capa, capa_id in [("PNG (~180 KB)", estado["capa_png_id"]), ("SVG", estado["capa_svg_id"])]:
                    for nombre_esc, objetivo, pasos, duracion_s, dx_total, dy_total in escenarios:
                        preparar_capa(capa_id)
                        conv = pestana.gestor_visor.obtener_conversion()
                        c_ini = vista.controlador.obtener_capa_seleccionada()
                        x_ini, y_ini, w_ini, h_ini = c_ini.x, c_ini.y, c_ini.ancho, c_ini.alto

                        if objetivo == "cuerpo":
                            cx_cm = c_ini.x + c_ini.ancho / 2.0
                            cy_cm = c_ini.y + c_ini.alto / 2.0
                            lx, ly = conv.plano_a_px(cx_cm, cy_cm)
                        else:
                            from logic.diseno.gestos_lienzo import tiradores
                            t_map = tiradores(c_ini)
                            tx_cm, ty_cm = t_map[objetivo]
                            lx, ly = conv.plano_a_px(tx_cm, ty_cm)

                        start_x = ox + lx
                        start_y = oy + ly

                        # Reiniciar contadores de instrumentación
                        instrumentacion["eventos_recibidos"] = 0
                        instrumentacion["tiempos_handler_ms"] = []
                        instrumentacion["updates_control"] = 0
                        instrumentacion["ws_mensajes_enviados"] = 0
                        instrumentacion["ws_bytes_enviados"] = 0
                        instrumentacion["ultimo_cambio_ui_ts"] = 0.0
                        instrumentacion["activo"] = True
                        instrumentacion["en_movimiento"] = True

                        web_page.mouse.move(start_x, start_y)
                        web_page.mouse.down()
                        dt_paso = duracion_s / max(1, pasos)
                        for step in range(1, pasos + 1):
                            frac = step / pasos
                            cur_x = start_x + dx_total * frac
                            cur_y = start_y + dy_total * frac
                            t_step0 = time.perf_counter()
                            web_page.mouse.move(cur_x, cur_y)
                            restante = dt_paso - (time.perf_counter() - t_step0)
                            if restante > 0:
                                time.sleep(restante)

                        instrumentacion["en_movimiento"] = False
                        t_mouseup = time.perf_counter()
                        web_page.mouse.up()

                        # Esperar a que terminen todos los eventos en cola post-mouseup
                        time.sleep(0.5)
                        instrumentacion["activo"] = False

                        t_ult = instrumentacion["ultimo_cambio_ui_ts"]
                        retraso_final_ms = max(0.0, (t_ult - t_mouseup) * 1000.0) if t_ult > 0 else 0.0

                        evs = instrumentacion["eventos_recibidos"]
                        tiempos = instrumentacion["tiempos_handler_ms"]
                        media_ms = statistics.mean(tiempos) if tiempos else 0.0
                        max_ms = max(tiempos) if tiempos else 0.0
                        upds = instrumentacion["updates_control"]
                        upds_por_ev = upds / max(1, evs)
                        ws_msgs = instrumentacion["ws_mensajes_enviados"]
                        ws_msgs_por_ev = ws_msgs / max(1, evs)
                        ws_bytes = instrumentacion["ws_bytes_enviados"]
                        ws_bytes_por_ev = ws_bytes / max(1, evs)

                        # Error de posición final respecto a lo esperado en cm
                        c_fin = marco.capa_activa or vista.controlador.obtener_capa_seleccionada()
                        dx_esp_cm, dy_esp_cm = conv.delta_px_a_plano(dx_total, dy_total)
                        if objetivo == "cuerpo":
                            err_x = abs((c_fin.x - x_ini) - dx_esp_cm)
                            err_y = abs((c_fin.y - y_ini) - dy_esp_cm)
                            err_cm = (err_x ** 2 + err_y ** 2) ** 0.5
                        else:
                            # En tirador 'br', ancho cambia en +dx_esp_cm y alto en -dy_esp_cm
                            err_w = abs((c_fin.ancho - w_ini) - dx_esp_cm)
                            err_h = abs((c_fin.alto - h_ini) - (-dy_esp_cm))
                            err_cm = (err_w ** 2 + err_h ** 2) ** 0.5

                        fila = {
                            "capa": tipo_capa,
                            "gesto": f"{nombre_esc} ({pasos}p/{duracion_s}s)",
                            "eventos_py": evs,
                            "proc_media_ms": media_ms,
                            "proc_max_ms": max_ms,
                            "updates_total": upds,
                            "updates_por_ev": upds_por_ev,
                            "ws_msgs_por_ev": ws_msgs_por_ev,
                            "ws_bytes_por_ev": ws_bytes_por_ev,
                            "retraso_final_ms": retraso_final_ms,
                            "error_pos_cm": err_cm,
                        }
                        resultados.append(fila)
                        print(
                            f"[{etapa.upper()}] {tipo_capa} | {fila['gesto']} -> "
                            f"ev={evs}, proc={media_ms:.2f}/{max_ms:.2f}ms, "
                            f"upds/ev={upds_por_ev:.1f}, ws_msgs/ev={ws_msgs_por_ev:.1f}, "
                            f"ws_bytes/ev={ws_bytes_por_ev:.0f}B, retraso_final={retraso_final_ms:.1f}ms, "
                            f"err={err_cm:.2f}cm",
                            flush=True,
                        )

                browser.close()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"Error en benchmark: {exc}", flush=True)
        finally:
            guardar_markdown(etapa, resultados)
            os._exit(0)

    os.environ["FLET_FORCE_WEB_SERVER"] = "true"
    t = threading.Thread(target=hilo_playwright, daemon=True)
    t.start()

    ft.run(
        app_target,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="127.0.0.1",
    )
    return resultados


def formatear_tabla_md(titulo: str, filas: List[Dict]) -> str:
    lineas = [
        f"## {titulo}",
        "",
        "| Capa | Gesto | Eventos Python | Proc. media (ms) | Proc. máx (ms) | `update()` / ev | Mensajes WS / ev | Bytes WS / ev | Retraso final (ms) | Error pos. (cm) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in filas:
        lineas.append(
            f"| {r['capa']} | {r['gesto']} | {r['eventos_py']} | "
            f"{r['proc_media_ms']:.2f} | {r['proc_max_ms']:.2f} | "
            f"{r['updates_por_ev']:.1f} ({r['updates_total']}) | "
            f"{r['ws_msgs_por_ev']:.1f} | {r['ws_bytes_por_ev']:.0f} B | "
            f"{r['retraso_final_ms']:.1f} | {r['error_pos_cm']:.2f} |"
        )
    lineas.append("")
    return "\n".join(lineas)


def guardar_markdown(etapa: str, filas: List[Dict]) -> None:
    docs_dir = RAIZ / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    ruta_md = docs_dir / "medidas_arrastre.md"

    bloque = formatear_tabla_md(f"Medición: {etapa.upper()}", filas)

    if etapa.lower() == "antes" or not ruta_md.exists():
        encabezado = (
            "# Medidas de rendimiento de arrastre en modo Editar capa\n\n"
            "Mediciones tomadas con `scripts/medir_arrastre_web.py` (Flet Web + Playwright Chromium headless).\n\n"
        )
        ruta_md.write_text(encabezado + bloque, encoding="utf-8")
    else:
        actual = ruta_md.read_text(encoding="utf-8")
        if "## Medición: DESPUES" in actual:
            actual = actual.split("## Medición: DESPUES")[0]
        ruta_md.write_text(actual + "\n" + bloque, encoding="utf-8")
    print(f"Tabla guardada en: {ruta_md}", flush=True)


if __name__ == "__main__":
    etapa_arg = sys.argv[1] if len(sys.argv) > 1 else "antes"
    ejecutar_medicion(etapa_arg)
