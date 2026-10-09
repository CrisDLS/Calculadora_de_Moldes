import math
from logic.interfaces import BalloonCalculator
from logic.models import BalloonInput, BalloonCalculationResult, SectionResult, Point2D
from logic.utils import calcular_hipotenusa, calcular_ancho_gajo

class TrompoEstrellaCalculator(BalloonCalculator):
   
    # CONSTANTES DE PROPORCIÓN DEL CUERPO
    F_DIAMETRO = 0.64
    F_ALTO_SUP = 0.42
    F_ALTO_INF = 0.58
   
    # FACTORES ESPECÍFICOS
    FACTOR_ESCALA_BOQUILLA = 0.185
   
    # TU REGLA DE ORO: Altura del triángulo en papel = Ancho Gajo * 120%
    FACTOR_ALTURA_PICO = 1.20

    def calcular(self, entrada: BalloonInput) -> BalloonCalculationResult:
        # 1. Dimensiones Maestras del CUERPO
        h_base = entrada.altura_cuerpo
        costura_media = entrada.ancho_costura / 2.0
       
        diametro_globo = h_base * self.F_DIAMETRO
        radio_globo = diametro_globo / 2
        ancho_gajo_max = calcular_ancho_gajo(radio_globo, entrada.num_gajos)
       
        # 2. Geometría de los PICOS (LÓGICA IMPLEMENTADA)
        # Regla: Base = Ancho Gajo, Altura = Ancho Gajo * 120%
       
        # A. Definimos la Altura del Triángulo que se dibuja en el papel
        altura_triangulo_papel = ancho_gajo_max * self.FACTOR_ALTURA_PICO
       
        # B. Altura Vertical (Estadística para saber qué tan alto queda el globo armado)
        # Asumimos que verticalmente ocupa lo mismo que el ancho (módulo cuadrado)
        # y el excedente del 20% es lo que se "sale" hacia afuera.
        h_vertical_ocupada = ancho_gajo_max * entrada.num_hileras_picos
       
        # 3. Cálculo de Boquilla
        ancho_gajo_boca_real = ancho_gajo_max * self.FACTOR_ESCALA_BOQUILLA
        circunferencia_boquilla = ancho_gajo_boca_real * entrada.num_gajos
        diametro_boquilla_calc = circunferencia_boquilla / math.pi
        radio_boquilla_calc = diametro_boquilla_calc / 2
       
        # 4. Alturas y Generatrices del CUERPO
        h_sup = h_base * self.F_ALTO_SUP
        h_inf = h_base * self.F_ALTO_INF
       
        l_sup = calcular_hipotenusa(h_sup, radio_globo)
       
        cateto_radial_inf = radio_globo - radio_boquilla_calc
        if cateto_radial_inf < 0: cateto_radial_inf = 0
        l_inf_real = calcular_hipotenusa(h_inf, cateto_radial_inf)

        # 5. Generación de Puntos (El Trazado)
       
        # --- A. CONO SUPERIOR ---
        pts_sup = self._generar_diagonal_con_costura(
            largo_generatriz=l_sup,
            ancho_inicio_puro=0.0,      
            ancho_fin_puro=ancho_gajo_max/2,
            costura=costura_media,
            pasos=17
        )
       
        # --- B. PICOS (MOLDE UNITARIO) ---
        # Trazamos la diagonal del triángulo.
        # Largo (Eje Y del papel) = altura_triangulo_papel (El 120% del ancho)
        # Inicio (Eje X) = Ancho Máximo / 2
        # Fin (Eje X) = 0
        pts_pico = self._generar_diagonal_con_costura(
            largo_generatriz=altura_triangulo_papel, # ¡AQUÍ SE APLICA TU REGLA!
            ancho_inicio_puro=ancho_gajo_max/2,
            ancho_fin_puro=0.0,
            costura=costura_media,
            pasos=12
        )

        # --- C. CONO INFERIOR ---
        pts_inf = self._generar_diagonal_con_costura(
            largo_generatriz=l_inf_real,
            ancho_inicio_puro=ancho_gajo_max/2,    
            ancho_fin_puro=ancho_gajo_boca_real/2,
            costura=costura_media,
            pasos=25
        )

        return BalloonCalculationResult(
            altura_cuerpo_base=h_base,
            altura_picos=h_vertical_ocupada,
            altura_total_real=h_base + h_vertical_ocupada,
            diametro_globo=diametro_globo,
            ancho_max_gajo=ancho_gajo_max,
           
            diametro_boquilla_calculado=diametro_boquilla_calc,
            circumferencia_boquilla=circunferencia_boquilla,
           
            seccion_superior=SectionResult("Cono Superior", pts_sup, h_sup, l_sup, 0, radio_globo),
            # Reportamos que este es un molde unitario con la altura del 120%
            seccion_picos=SectionResult("Molde Pico (Altura=120% Ancho)", pts_pico, ancho_gajo_max, altura_triangulo_papel, radio_globo, 0),
            seccion_inferior=SectionResult("Cono Inferior", pts_inf, h_inf, l_inf_real, radio_globo, radio_boquilla_calc)
        )

    def _generar_diagonal_con_costura(self, largo_generatriz, ancho_inicio_puro, ancho_fin_puro, costura, pasos):
        puntos = []
        if pasos <= 1: return puntos
        delta_l = largo_generatriz / (pasos - 1)
       
        for i in range(pasos):
            l_acumulado = i * delta_l
            progreso = i / (pasos - 1)
            ancho_geo = ancho_inicio_puro + (ancho_fin_puro - ancho_inicio_puro) * progreso
            ancho_final = ancho_geo + costura
           
            puntos.append(Point2D(i + 1, delta_l, l_acumulado, ancho_final))
        return puntos