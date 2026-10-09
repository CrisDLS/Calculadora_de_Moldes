"""
Calculadora del TROMPO ESTRELLA. Reemplaza a la versión anterior.
Fuente de verdad: Excel "CALCULADORA DE MOLDE TROMPO ESTRELLA MODEL 3"
(portada de referencia/trompo_estrella.py). Todas las longitudes en cm.
NO imprime ni usa nada de interfaz gráfica; las entradas inválidas lanzan ValueError.

MODO SIMPLE (usar_parametros_avanzados=False): solo geometría. Boca por defecto (11 %),
sin pestaña; `boca`, `vuelo` y `viable` quedan en None.
MODO AVANZADO: boca personalizada, pestaña, mecha, empuje, carga, pliegos y viabilidad.
Las tres piezas son idénticas en ambos modos salvo la pestaña del cono inferior.
"""
import math
from typing import List, Optional

from logic.interfaces import BalloonCalculator
from logic.models import (BalloonInput, BalloonCalculationResult, SectionResult, Point2D,
                          BocaResult, VueloResult, Condiciones)


class TrompoEstrellaCalculator(BalloonCalculator):

    # --- Proporciones del modelo (salen del Excel) ---
    F_DIAMETRO = 0.64      # diámetro máximo = 64 % del largo de papel
    F_CONO_SUP = 0.43      # % del largo restante (sin picos)
    F_CONO_INF = 0.57
    F_BOCA = 0.11          # boca por defecto = 11 % del largo
    F_PICO = 1.20          # largo del pico = 120 % del ancho de gajo
    F_MECHA = 0.50         # mecha/parrilla = 50 % de la boca (medida del autor)
    INTERVALOS_SUP = 16
    INTERVALOS_PICO = 11
    INTERVALOS_INF = 24
    MIN_GAJOS = 3
    GAJO_IDEAL_MAX_CM = 70.0   # ancho de gajo máximo recomendado
    GAJO_REF_MIN_CM = 50.0     # ancho de gajo de referencia para gajos "máximos" recomendados

    # --- Física y unidades ---
    DENSIDAD_ACERO = 7850.0    # kg/m³
    R_AIRE = 287.05            # J/(kg·K), constante específica del aire seco
    KELVIN = 273.15
    MARGEN_CARGA_MIN = 0.25    # carga neta mínima recomendada (fracción del empuje)
    CM2_POR_M2 = 1e4
    CM3_POR_M3 = 1e6
    CM_POR_M = 100.0
    MM_POR_M = 1000.0
    G_POR_KG = 1000.0

    AVISO_MODO_SIMPLE = ("Modo simple: solo geometría. Activa parámetros avanzados para "
                         "verificar viabilidad (holgura de mecha y empuje).")

    def __init__(self, condiciones: Optional[Condiciones] = None):
        self.cond = condiciones or Condiciones()

    # ------------------------------------------------------------------ API
    def calcular(self, entrada: BalloonInput) -> BalloonCalculationResult:
        self._validar(entrada)
        e, c = entrada, self.cond
        av = e.usar_parametros_avanzados
        pestana = e.pestana_boca if av else 0.0
        medio_cos = e.ancho_costura / 2

        d_max = e.altura_cuerpo * self.F_DIAMETRO
        r = d_max / 2
        ancho_gajo = math.pi * d_max / e.num_gajos
        d_boca = e.diametro_boca if (av and e.diametro_boca is not None) else e.altura_cuerpo * self.F_BOCA
        rb = d_boca / 2
        ancho_boca = math.pi * d_boca / e.num_gajos

        largo_picos = ancho_gajo * e.num_hileras_picos
        restante = e.altura_cuerpo - largo_picos
        l_sup, l_inf = restante * self.F_CONO_SUP, restante * self.F_CONO_INF
        l_pico = ancho_gajo * self.F_PICO

        if l_sup <= r:
            raise ValueError("Cono superior imposible: reduce gajos/picos o sube la altura")
        if rb >= r:
            raise ValueError("La boca no puede ser mayor que el diámetro máximo")
        if l_inf <= r - rb:
            raise ValueError("Cono inferior imposible: reduce gajos/picos, sube la altura "
                             "o agranda la boca")

        # --- Geometría vertical y volumen ---
        h_sup = math.sqrt(l_sup ** 2 - r ** 2)
        h_inf = math.sqrt(l_inf ** 2 - (r - rb) ** 2)
        v_cm3 = (math.pi * r ** 2 * h_sup / 3 + math.pi * r ** 2 * largo_picos
                 + math.pi * h_inf / 3 * (r ** 2 + r * rb + rb ** 2))

        # --- Piezas ---
        ancho_max_m = ancho_gajo / 2 + medio_cos
        x_boca = ancho_boca / 2 + medio_cos
        pts_sup = self._puntos(l_sup, self.INTERVALOS_SUP, medio_cos, ancho_max_m)
        pts_pico = self._puntos(l_pico, self.INTERVALOS_PICO, medio_cos, ancho_max_m)
        pts_inf = self._puntos(l_inf, self.INTERVALOS_INF, x_boca, ancho_max_m)

        sup = SectionResult("Cono Superior", pts_sup, h_sup, l_sup, 0.0, r,
                            area_cm2=l_sup * (medio_cos + ancho_max_m))
        pico = SectionResult("Pico", pts_pico, ancho_gajo, l_pico, r, r,
                             area_cm2=l_pico * (medio_cos + ancho_max_m))
        inf = SectionResult("Cono Inferior", pts_inf, h_inf, l_inf, rb, r,
                            pestana=pestana,
                            area_cm2=l_inf * (x_boca + ancho_max_m) + pestana * 2 * x_boca)
        area_cm2 = e.num_gajos * (sup.area_cm2 + e.num_hileras_picos * pico.area_cm2 + inf.area_cm2)

        # --- Mecha / vuelo (solo modo avanzado) ---
        boca = vuelo = None
        if av:
            d_mecha = e.diametro_mecha if e.diametro_mecha is not None else self.F_MECHA * d_boca
            holgura = rb - d_mecha / 2
            vol = v_cm3 / self.CM3_POR_M3
            empuje = vol * self._empuje_por_m3()
            masa_papel = area_cm2 / self.CM2_POR_M2 * c.papel_gm2 * (1 + c.extra_pegamento)
            long_alambre_m = (math.pi * d_boca + e.varillas * rb) / self.CM_POR_M
            seccion_m2 = math.pi * (e.alambre_mm / 2 / self.MM_POR_M) ** 2
            masa_estr = long_alambre_m * seccion_m2 * self.DENSIDAD_ACERO * self.G_POR_KG
            pliegos = area_cm2 * (1 + c.desperdicio) / (c.pliego_cm[0] * c.pliego_cm[1])
            boca = BocaResult(
                diametro=d_boca, circunferencia_aro=math.pi * d_boca, ancho_por_gajo=ancho_boca,
                pestana=pestana, diametro_mecha=d_mecha, holgura=holgura,
                holgura_ok=holgura >= e.holgura_min,
                diametro_minimo=d_mecha + 2 * e.holgura_min,
                radio_pared_a_llama=rb + min(e.altura_llama, h_inf) * (r - rb) / h_inf)
            vuelo = VueloResult(vol, empuje, masa_papel, masa_estr, empuje - masa_papel,
                                empuje - masa_papel - masa_estr, pliegos)

        res = BalloonCalculationResult(
            altura_cuerpo_base=h_sup + h_inf, altura_picos=largo_picos,
            altura_total_real=h_sup + largo_picos + h_inf, diametro_globo=d_max,
            ancho_max_gajo=ancho_gajo,
            diametro_boquilla_calculado=d_boca, circumferencia_boquilla=math.pi * d_boca,
            seccion_superior=sup, seccion_picos=pico, seccion_inferior=inf,
            boca=boca, vuelo=vuelo,
            gajos_min_70cm=self._par_arriba(math.pi * d_max / self.GAJO_IDEAL_MAX_CM),
            gajos_min_50cm=self._par_arriba(math.pi * d_max / self.GAJO_REF_MIN_CM),
            area_total_m2=area_cm2 / self.CM2_POR_M2)
        res.avisos = self._diagnostico(e, res)
        if av:
            res.viable = not any(a.startswith("ERROR") for a in res.avisos)
        return res

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _puntos(largo: float, intervalos: int, x0: float, x1: float) -> List[Point2D]:
        paso = largo / intervalos
        return [Point2D(i + 1, 0.0 if i == 0 else paso, paso * i, x0 + (x1 - x0) * i / intervalos)
                for i in range(intervalos + 1)]

    @staticmethod
    def _par_arriba(x: float) -> int:        # equivale a EVEN() de Excel
        n = math.ceil(x)
        return n + (n % 2)

    def _empuje_por_m3(self) -> float:
        """Gramos de empuje por m³ de aire caliente (gas ideal)."""
        c = self.cond
        ta, ti = c.t_ambiente + self.KELVIN, c.t_interior + self.KELVIN
        return c.presion_pa / (self.R_AIRE * ta) * (1 - ta / ti) * self.G_POR_KG

    @staticmethod
    def _validar(e: BalloonInput) -> None:
        if e.altura_cuerpo <= 0 or e.ancho_costura < 0:
            raise ValueError("La altura debe ser > 0 y la costura >= 0")
        if e.num_gajos < TrompoEstrellaCalculator.MIN_GAJOS or e.num_hileras_picos < 0:
            raise ValueError(f"Gajos >= {TrompoEstrellaCalculator.MIN_GAJOS} e hileras de picos >= 0")
        if not e.usar_parametros_avanzados:
            return          # en modo simple los parámetros avanzados se ignoran
        if e.pestana_boca < 0:
            raise ValueError("La pestaña debe ser >= 0")
        if e.diametro_boca is not None and e.diametro_boca <= 0:
            raise ValueError("El diámetro de la boca debe ser > 0")
        if e.diametro_mecha is not None and e.diametro_mecha <= 0:
            raise ValueError("El diámetro de la mecha debe ser > 0")
        if e.masa_mecha_g is not None and e.masa_mecha_g < 0:
            raise ValueError("El peso de la mecha debe ser >= 0")
        if e.holgura_min < 0 or e.altura_llama < 0:
            raise ValueError("La holgura mínima y la altura de llama deben ser >= 0")
        if e.alambre_mm <= 0 or e.varillas < 0:
            raise ValueError("Alambre > 0 mm y varillas >= 0")

    def _diagnostico(self, e: BalloonInput, r: BalloonCalculationResult) -> List[str]:
        """Chequeos. 'ERROR' = no viable. En modo simple solo geometría + aviso de modo."""
        av = []
        if r.ancho_max_gajo > self.GAJO_IDEAL_MAX_CM:
            av.append(f"AVISO: gajo de {r.ancho_max_gajo:.0f} cm (>{self.GAJO_IDEAL_MAX_CM:.0f}). "
                      f"Usa ≥ {r.gajos_min_70cm} gajos.")
        if not e.usar_parametros_avanzados:
            av.append(self.AVISO_MODO_SIMPLE)
            return av
        b, v = r.boca, r.vuelo
        if not b.holgura_ok:
            av.append(f"ERROR: holgura mecha→papel {b.holgura:.1f} cm < {e.holgura_min:.0f} cm. "
                      f"Sube la boca a ≥ {b.diametro_minimo:.0f} cm o reduce la mecha.")
        if v.carga_libre_g <= 0:
            av.append("ERROR: el empuje no vence ni el peso del papel; no vuela (aumenta el tamaño).")
        elif v.carga_neta_g <= 0:
            av.append("ERROR: el empuje no alcanza para papel + aro/parrilla.")
        elif e.masa_mecha_g is not None and v.carga_neta_g < e.masa_mecha_g:
            av.append(f"ERROR: tu mecha pesa {e.masa_mecha_g:.0f} g y solo hay {v.carga_neta_g:.0f} g de margen.")
        elif v.carga_neta_g < self.MARGEN_CARGA_MIN * v.empuje_g:
            av.append(f"AVISO: margen de carga bajo (<{self.MARGEN_CARGA_MIN:.0%} del empuje); "
                      "poco colchón ante frío o viento.")
        return av or ["OK: medidas viables con los supuestos actuales."]