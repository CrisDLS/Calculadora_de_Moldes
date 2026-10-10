"""Reporte de consola del molde del trompo estrella.

Uso (desde la raíz del proyecto):
    python scripts/reporte_trompo_estrella.py 950 30 2 1
    python scripts/reporte_trompo_estrella.py 950 30 2 1 --avanzado

La presentación vive aquí; la lógica está en logic/calculators/trompo_estrella.py.
"""
import argparse
import os
import sys

# Permite ejecutar el script directamente sin instalar el proyecto.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.calculators.trompo_estrella import TrompoEstrellaCalculator  # noqa: E402
from logic.models import BalloonInput, SectionResult  # noqa: E402


def _configurar_consola() -> None:
    """Fuerza UTF-8 en stdout/stderr para que funcione en la consola de Windows."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")


def tabla_texto(s: SectionResult) -> str:
    lineas = [f"\n--- {s.nombre} (largo de papel: {s.generatriz_total:.4f} cm) ---",
              f"{'Paso':<5}| {'Largo(cm)':>10} | {'Acum.(cm)':>10} | {'Ancho/2(cm)':>11}"]
    lineas += [f"#{p.paso_numero:<4}| {p.largo_segmento:>10.4f} | {p.largo_acumulado:>10.4f} "
               f"| {p.ancho_medio:>11.4f}" for p in s.puntos]
    if s.pestana:
        lineas.append(f"+ pestaña de {s.pestana:.1f} cm después del paso #1 "
                      f"(ancho recto = {2 * s.puntos[0].ancho_medio:.2f} cm)")
    return "\n".join(lineas)


def resumen_texto(r) -> str:
    lineas = [
        "\n=== RESUMEN ===",
        f"Diámetro máximo: {r.diametro_globo:.1f} cm | ancho de gajo: {r.ancho_max_gajo:.4f} cm",
        f"Boca: Ø{r.diametro_boquilla_calculado:.1f} cm | aro (perímetro) {r.circumferencia_boquilla:.1f} cm",
        f"Gajos mínimos: {r.gajos_min_70cm} (gajo <= 70 cm) / {r.gajos_min_50cm} (gajo <= 50 cm)",
        f"Altura armada estimada: {r.altura_total_real:.0f} cm | papel: {r.area_total_m2:.1f} m2",
    ]
    if r.boca is not None:
        b = r.boca
        lineas.append(f"Mecha Ø{b.diametro_mecha:.1f} cm | holgura mecha->borde: {b.holgura:.1f} cm "
                      f"({'OK' if b.holgura_ok else 'INSUFICIENTE'}) | boca mínima: {b.diametro_minimo:.1f} cm")
        lineas.append(f"Pared a la altura de la llama: radio {b.radio_pared_a_llama:.1f} cm")
    if r.vuelo is not None:
        v = r.vuelo
        lineas.append(f"Volumen {v.volumen_m3:.1f} m3 | empuje {v.empuje_g / 1000:.1f} kg | "
                      f"papel {v.masa_papel_g / 1000:.1f} kg | carga libre {v.carga_libre_g / 1000:.1f} kg | "
                      f"pliegos ~ {v.pliegos:.0f}")
        lineas.append(f"Estructura (aro+varillas) ~ {v.masa_estructura_g:.0f} g | "
                      f"carga neta p/ mecha {v.carga_neta_g / 1000:.1f} kg")
    estado = {True: "SI", False: "NO", None: "no evaluada"}[r.viable]
    lineas.append(f"Viable: {estado}")
    lineas += [f"  {a}" for a in r.avisos]
    return "\n".join(lineas)


def main(argv=None) -> int:
    _configurar_consola()
    ap = argparse.ArgumentParser(description="Reporte del molde del trompo estrella (cm).")
    ap.add_argument("altura", type=float, help="largo total de papel sobre la superficie (cm)")
    ap.add_argument("gajos", type=int)
    ap.add_argument("hileras", type=int, help="hileras de picos")
    ap.add_argument("costura", type=float, help="ancho de costura (cm)")
    ap.add_argument("--avanzado", action="store_true",
                    help="activa pestaña, mecha, empuje y viabilidad")
    args = ap.parse_args(argv)

    entrada = BalloonInput(args.altura, args.gajos, args.hileras, args.costura,
                           usar_parametros_avanzados=args.avanzado)
    try:
        r = TrompoEstrellaCalculator().calcular(entrada)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    modo = "AVANZADO" if args.avanzado else "SIMPLE"
    print(f"REPORTE TROMPO ESTRELLA - modo {modo}")
    print(f"Entrada: altura {args.altura:g} cm | {args.gajos} gajos | {args.hileras} hileras | "
          f"costura {args.costura:g} cm")
    for seccion in (r.seccion_superior, r.seccion_picos, r.seccion_inferior):
        print(tabla_texto(seccion))
    print(resumen_texto(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
