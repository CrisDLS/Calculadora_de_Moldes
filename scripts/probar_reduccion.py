"""Script de consola para probar y visualizar la reducción de colores sobre imágenes."""

import argparse
from pathlib import Path
import sys
import time
from typing import Dict, Tuple

from PIL import Image

# Asegurar importación de módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic.papel.reduccion_colores import reducir_colores


def crear_comparacion_lado_a_lado(img_ref: Image.Image, img_rec: Image.Image) -> Image.Image:
    """Combina dos imágenes lado a lado sobre un lienzo transparente."""
    w1, h1 = img_ref.size
    w2, h2 = img_rec.size
    ancho_total = w1 + w2 + 10  # 10 px de separación
    alto_total = max(h1, h2)

    comp = Image.new("RGBA", (ancho_total, alto_total), (0, 0, 0, 0))
    comp.paste(img_ref, (0, 0), img_ref if img_ref.mode == "RGBA" else None)
    comp.paste(img_rec, (w1 + 10, 0), img_rec if img_rec.mode == "RGBA" else None)
    return comp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prueba la reducción de colores sobre una imagen y genera comparaciones visuales."
    )
    parser.add_argument("ruta_imagen", type=str, help="Ruta al archivo de imagen de entrada")
    parser.add_argument("--colores", type=int, default=8, help="Número de colores destino (por defecto: 8)")
    parser.add_argument(
        "--modo",
        type=str,
        choices=["color", "grises"],
        default="color",
        help="Modo de reducción: 'color' o 'grises' (por defecto: 'color')",
    )
    parser.add_argument(
        "--ancho",
        type=int,
        default=800,
        help="Ancho en píxeles para redimensionar manteniendo proporción (por defecto: 800)",
    )

    args = parser.parse_args()

    ruta_entrada = Path(args.ruta_imagen)
    if not ruta_entrada.exists():
        print(f"Error: No existe el archivo de imagen '{ruta_entrada}'", file=sys.stderr)
        sys.exit(1)

    # 1. Abrir imagen y redimensionar
    with Image.open(ruta_entrada) as raw_img:
        img_original = raw_img.convert("RGBA")

    if img_original.width != args.ancho and args.ancho > 0:
        factor = args.ancho / img_original.width
        nuevo_alto = max(1, int(round(img_original.height * factor)))
        img_redim = img_original.resize((args.ancho, nuevo_alto), Image.Resampling.LANCZOS)
    else:
        img_redim = img_original.copy()

    # 2. Aplicar reducción de colores y medir tiempo
    t0 = time.perf_counter()
    img_reducida = reducir_colores(img_redim, max_colores=args.colores, modo=args.modo)
    t_ms = (time.perf_counter() - t0) * 1000.0

    # 3. Guardar archivos en scripts/_salida/
    salida_dir = Path(__file__).resolve().parent / "_salida"
    salida_dir.mkdir(parents=True, exist_ok=True)

    nombre = ruta_entrada.stem
    ruta_ref = salida_dir / f"ref_{nombre}.png"
    ruta_rec = salida_dir / f"rec_{nombre}_{args.colores}_{args.modo}.png"
    ruta_comp = salida_dir / f"comparacion_{nombre}.png"

    img_redim.save(ruta_ref, format="PNG")
    img_reducida.save(ruta_rec, format="PNG")

    img_comparacion = crear_comparacion_lado_a_lado(img_redim, img_reducida)
    img_comparacion.save(ruta_comp, format="PNG")

    # 4. Conteo de colores opacos y tabla
    conteos: Dict[str, int] = {}
    total_opacos = 0
    total_transparentes = 0

    for p in img_reducida.getdata():
        if p[3] == 255:
            hex_str = f"#{p[0]:02X}{p[1]:02X}{p[2]:02X}"
            conteos[hex_str] = conteos.get(hex_str, 0) + 1
            total_opacos += 1
        else:
            total_transparentes += 1

    filas_ordenadas = sorted(conteos.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "=" * 55)
    print(f"REDUCCIÓN DE COLORES - {nombre}")
    print("=" * 55)
    print(f"Dimensiones      : {img_redim.width} × {img_redim.height} px")
    print(f"Modo solicitado  : {args.modo}")
    print(f"Colores objetivo : {args.colores}")
    print(f"Colores hallados : {len(filas_ordenadas)}")
    print(f"Tiempo empleado  : {t_ms:.2f} ms")
    print("-" * 55)
    print(f"{'Color HEX':<14} | {'Píxeles':<12} | {'% del total':<12}")
    print("-" * 55)

    base_calc = total_opacos if total_opacos > 0 else 1
    for hex_color, cant in filas_ordenadas:
        pct = (cant / base_calc) * 100.0
        print(f"{hex_color:<14} | {cant:<12d} | {pct:>8.2f} %")

    print("-" * 55)
    print(f"Total opacos     : {total_opacos} px")
    if total_transparentes > 0:
        pct_trans = (total_transparentes / (img_redim.width * img_redim.height)) * 100.0
        print(f"Transparentes    : {total_transparentes} px ({pct_trans:.1f} %)")
    print("=" * 55)
    print(f"Referencia   : {ruta_ref.relative_to(Path.cwd())}")
    print(f"Resultado    : {ruta_rec.relative_to(Path.cwd())}")
    print(f"Comparación  : {ruta_comp.relative_to(Path.cwd())}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
