import sys
import os
import time
import math
from pathlib import Path
from PIL import Image

# Asegurar path
sys.path.insert(0, os.path.abspath("."))

from app_flet.vistas.trompo import VistaTrompo


class DoublePage:
    """Doble de página Flet para medir llamadas y bytes sin abrir ventana."""
    def __init__(self):
        self.updates_count = 0
        self.bytes_enviados = 0
        self.services = []
        self.overlay = []

    def update(self):
        self.updates_count += 1

    def run_task(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)

    def run_thread(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


class DoubleEvent:
    """Doble de DragUpdateEvent."""
    def __init__(self, dx, dy):
        self.delta_x = dx
        self.delta_y = dy
        self.local_delta = type("Delta", (), {"x": dx, "y": dy})()
        self.global_delta = self.local_delta


def crear_svg_triangulos(num_triangulos: int, ruta: Path):
    lineas = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">',
        '  <defs/>',
        '  <g id="capa-triangulos">'
    ]
    # Generar num_triangulos polígonos
    cols = int(math.ceil(math.sqrt(num_triangulos)))
    paso = 500.0 / max(1, cols)
    for i in range(num_triangulos):
        r = i // cols
        c = i % cols
        x0 = c * paso
        y0 = r * paso
        color = f"#{((i * 1234567) & 0xFFFFFF):06x}"
        lineas.append(f'    <polygon points="{x0:.1f},{y0:.1f} {x0+paso:.1f},{y0:.1f} {x0+paso/2:.1f},{y0+paso:.1f}" fill="{color}"/>')
    lineas.append('  </g>')
    lineas.append('</svg>')
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def crear_raster_4000(ruta: Path):
    img = Image.new("RGB", (4000, 4000), color=(120, 180, 240))
    img.save(ruta, format="JPEG", quality=85)


def ejecutar_benchmark():
    tmp_dir = Path("guardados/recursos_temp/benchmark")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    arch_500 = tmp_dir / "triangulos_500.svg"
    arch_5000 = tmp_dir / "triangulos_5000.svg"
    arch_20000 = tmp_dir / "triangulos_20000.svg"
    arch_raster = tmp_dir / "raster_4000x4000.jpg"

    print("Generando archivos de prueba sintéticos...")
    if not arch_500.exists():
        crear_svg_triangulos(500, arch_500)
    if not arch_5000.exists():
        crear_svg_triangulos(5000, arch_5000)
    if not arch_20000.exists():
        crear_svg_triangulos(20000, arch_20000)
    if not arch_raster.exists():
        crear_raster_4000(arch_raster)

    arch_usuario_svg = Path("docs/ejemplos/disenos/_prueba_usuario.svg")
    arch_usuario_jpg = Path("docs/ejemplos/disenos/_prueba_usuario.jpg")

    casos = [
        ("Usuario SVG", arch_usuario_svg, 4),
        ("Usuario JPG", arch_usuario_jpg, 1),
        ("SVG 500 tri.", arch_500, 500),
        ("SVG 5 000 tri.", arch_5000, 5000),
        ("SVG 20 000 tri.", arch_20000, 20000),
        ("JPG 4000x4000", arch_raster, 1),
    ]

    print("\n--- INICIO DE PRUEBA DE ESTRÉS (CÓDIGO ACTUAL) ---")
    resultados = []

    for nombre, ruta, num_elem in casos:
        if not ruta.exists():
            print(f"Saltando {nombre}: archivo no encontrado")
            continue

        tam_kb = ruta.stat().st_size / 1024.0

        # Crear vista y simular página Flet
        page = DoublePage()
        vista = VistaTrompo()
        vista._page = page

        # Calcular modelo base
        vista.on_calcular(None)
        ctrl = vista.controlador
        ctrl.ruta_proyecto = str(tmp_dir / f"proy_{nombre}.json")

        # Añadir capa
        ctrl.anadir_capa(str(ruta))
        vista.modo_interaccion_diseno = "mover"
        vista._sync_controlador_a_vista(ctrl.get_view_model())

        # Reset métricas de página
        page.updates_count = 0
        vista_updates_count = 0
        def count_vista_update():
            nonlocal vista_updates_count
            vista_updates_count += 1
            page.updates_count += 1
        vista.update = count_vista_update

        # Simular arrastre: 300 eventos a 60 Hz
        tiempos_ms = []
        bytes_totales = 0
        termino = True

        for i in range(300):
            ev = DoubleEvent(dx=1.0, dy=0.5)
            t0 = time.perf_counter()
            try:
                vista._on_gesture_diseno_pan_update(ev)
            except Exception as e:
                termino = False
                print(f"Error en iteración {i}: {e}")
                break
            t1 = time.perf_counter()
            tiempos_ms.append((t1 - t0) * 1000.0)

            # Estimar bytes del SVG generado si se envió al visor
            if hasattr(vista, "img_svg_diseno") and vista.img_svg_diseno.src:
                src_val = vista.img_svg_diseno.src
                if isinstance(src_val, (bytes, bytearray)):
                    bytes_totales += len(src_val)
                elif isinstance(src_val, str):
                    bytes_totales += len(src_val.encode("utf-8"))

        time.perf_counter()

        media_ms = sum(tiempos_ms) / len(tiempos_ms) if tiempos_ms else 0.0
        max_ms = max(tiempos_ms) if tiempos_ms else 0.0

        banderas_activas = getattr(vista, "arrastrando", False)

        resultados.append({
            "diseno": nombre,
            "elementos": num_elem,
            "tam_kb": f"{tam_kb:.1f} KB",
            "media_ms": f"{media_ms:.2f}",
            "max_ms": f"{max_ms:.2f}",
            "updates": vista_updates_count,
            "bytes_mb": f"{bytes_totales / (1024*1024):.2f} MB",
            "termino": "Sí" if termino else "No",
            "banderas": "Ninguna" if not banderas_activas else "arrastrando=True"
        })

        print(f"Completado {nombre}: {vista_updates_count} updates, {bytes_totales / (1024*1024):.2f} MB enviados, media {media_ms:.2f} ms")

    print("\n--- RESULTADOS TABLA ---")
    headers = ["Diseño", "Elementos", "Tamaño", "Media ms", "Máx ms", "Updates", "Bytes enviados", "¿Terminó?", "Banderas"]
    print(f"{headers[0]:<16} | {headers[1]:<10} | {headers[2]:<10} | {headers[3]:<9} | {headers[4]:<9} | {headers[5]:<8} | {headers[6]:<14} | {headers[7]:<9} | {headers[8]}")
    print("-" * 115)
    for r in resultados:
        print(f"{r['diseno']:<16} | {str(r['elementos']):<10} | {r['tam_kb']:<10} | {r['media_ms']:<9} | {r['max_ms']:<9} | {str(r['updates']):<8} | {r['bytes_mb']:<14} | {r['termino']:<9} | {r['banderas']}")

    # Inyección de fallos
    print("\n--- PRUEBA DE INYECCIÓN DE FALLOS ---")
    page_f = DoublePage()
    vista_f = VistaTrompo()
    vista_f._page = page_f
    vista_f.on_calcular(None)
    ctrl_f = vista_f.controlador
    ctrl_f.ruta_proyecto = str(tmp_dir / "proy_fallo.json")
    ctrl_f.anadir_capa(str(arch_500))
    vista_f.modo_interaccion_diseno = "mover"
    vista_f._sync_controlador_a_vista(ctrl_f.get_view_model())

    # Inyectar fallo a mitad
    def fallo_empujar(*args, **kwargs):
        raise RuntimeError("Fallo simulado a mitad del arrastre")

    ctrl_f.empujar_capa_seleccionada = fallo_empujar

    try:
        vista_f._on_gesture_diseno_pan_update(DoubleEvent(dx=1.0, dy=1.0))
    except RuntimeError as ex:
        print("Excepción capturada durante arrastre:", ex)

    # Comprobar si "Calcular" funciona después
    calcular_ok = False
    try:
        vista_f.on_calcular(None)
        vm_calc = ctrl_f.get_view_model()
        calcular_ok = (vm_calc.resultado is not None)
        print("¿Calcular funcionó después del fallo?:", "Sí" if calcular_ok else "No")
    except Exception as ex_calc:
        print("Calcular falló después del error de arrastre:", ex_calc)


if __name__ == "__main__":
    ejecutar_benchmark()
