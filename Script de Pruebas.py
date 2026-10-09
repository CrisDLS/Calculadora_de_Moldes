from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator

def imprimir_tabla_estilo_excel(seccion):
    print(f"\n>>> MÓDULO: {seccion.nombre.upper()}")
    # Aquí mostramos el largo del papel. En los picos, esto debe ser el Ancho * 1.2
    print(f"    Generatriz (Largo Papel): {seccion.generatriz_total:.2f} cm")
    print("-" * 65)
    print(f"{'Paso':^6} | {'Largo (cm)':^12} | {'Acumulado':^15} | {'Ancho/2 (+Cost)':^16}")
    print("-" * 65)
    
    for pt in seccion.puntos:
        print(f" #{pt.paso_numero:^4} | {pt.largo_segmento:^12.2f} | {pt.largo_acumulado:^15.2f} | {pt.ancho_medio:^16.2f}")
    print("-" * 65)

def main():
    # DATOS DE ENTRADA (Simulación)
    # NOTA: Ya NO ponemos boquilla aquí, porque es automática (18.5%)
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0
    )

    calc = TrompoEstrellaCalculator()
    res = calc.calcular(entrada)

    print("\n" + "="*60)
    print(" 🌟 CALCULADORA TROMPO ESTRELLA - REPORTE FINAL")
    print("="*60)
    print(f" > Altura Cuerpo Base:    {res.altura_cuerpo_base} cm")
    print(f" > Ancho Máx Gajo (Base): {res.ancho_max_gajo:.2f} cm")
    print("-" * 60)
    print(f" GEOMETRÍA DE PICOS (Regla 120%):")
    print(f" > Base del Pico:         {res.ancho_max_gajo:.2f} cm (Igual al Ancho Gajo)")
    # Esta es la prueba de fuego: Debe ser Ancho * 1.2
    print(f" > Altura Triángulo Papel:{res.seccion_picos.generatriz_total:.2f} cm (Debe ser {res.ancho_max_gajo * 1.2:.2f})")
    print(f" > Hileras Totales:       {entrada.num_hileras_picos}")
    print("-" * 60)
    print(f" ALTURA TOTAL GLOBO (Aprox): {res.altura_total_real:.1f} cm")
    
    # Imprimir las tablas
    imprimir_tabla_estilo_excel(res.seccion_superior)
    imprimir_tabla_estilo_excel(res.seccion_picos)
    imprimir_tabla_estilo_excel(res.seccion_inferior)

if __name__ == "__main__":
    main()