"""
Calculadora de moldes - Globo de cantoya TROMPO ESTRELLA  (v2)
Base: Excel "CALCULADORA DE MOLDE TROMPO ESTRELLA MODEL 3".

Piezas por gajo: Cono superior + Pico (triángulo) + Cono inferior.
"altura" = largo TOTAL de papel sobre la superficie (cono sup + picos + cono inf),
NO la altura vertical del globo armado (esa se estima en el resultado).

Novedades v2: pestaña de la boca, chequeo de holgura de la mecha,
volumen / empuje / carga libre, y número de pliegos.
Todos los valores marcados "calibrar" son puntos de partida, no datos publicados.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

# --- Proporciones del modelo (salen del Excel) -------------------------------
F_DIAMETRO = 0.64      # diámetro máximo = 64 % de la altura
F_CONO_SUP = 0.43      # % del largo restante (sin picos)
F_CONO_INF = 0.57
F_BOCA = 0.11          # boca por defecto = 11 % de la altura
F_PICO = 1.20          # altura del pico = 120 % del ancho de gajo
F_MECHA = 0.50         # diámetro de la parrilla/mecha = 50 % de la boca (medición del autor)
DENSIDAD_ACERO = 7850  # kg/m³
INTERVALOS = {"Cono superior": 16, "Pico": 11, "Cono inferior": 24}
PLIEGO_CM = (50, 75)   # tamaño aprox. de pliego de papel china (confirmar con proveedor)


@dataclass(frozen=True)
class Entrada:
    altura: float
    gajos: int
    hileras_picos: int
    costura: float
    diametro_boca: float | None = None   # None -> 0.11 * altura
    pestana_boca: float = 4.0            # cm extra para doblar sobre el aro (calibrar)
    diametro_mecha: float | None = None  # cm; None -> F_MECHA * boca
    masa_mecha_g: float | None = None    # peso real de tu mecha+combustible (opcional)
    alambre_mm: float = 2.0              # grosor del alambre del aro y varillas
    varillas: int = 4                    # varillas de la parrilla
    altura_llama: float = 40.0           # cm que sube la llama sobre el plano de la boca
    holgura_min: float = 10.0            # cm mínimos mecha -> borde de papel (calibrar)

    def validar(self) -> None:
        if self.altura <= 0 or self.costura < 0 or self.pestana_boca < 0:
            raise ValueError("altura > 0, costura >= 0, pestana_boca >= 0")
        if self.gajos < 3 or self.hileras_picos < 0:
            raise ValueError("gajos >= 3 y hileras_picos >= 0")


@dataclass(frozen=True)
class Condiciones:
    papel_gm2: float = 20.0         # gramaje del papel
    extra_pegamento: float = 0.20   # +% de peso por pegamento/refuerzos (supuesto)
    t_ambiente: float = 28.0        # °C
    t_interior: float = 70.0        # °C promedio dentro del globo (supuesto)
    presion_pa: float = 101325.0    # nivel del mar
    desperdicio: float = 0.15       # +% de papel por recortes


@dataclass(frozen=True)
class Punto:
    paso: int
    largo: float
    acumulado: float
    ancho_mitad: float   # ya incluye costura/2


@dataclass(frozen=True)
class Pieza:
    nombre: str
    largo: float
    ancho_mitad_inicio: float
    ancho_mitad_fin: float
    puntos: list[Punto]
    pestana: float = 0.0   # tira extra DESPUÉS del paso 1 (solo cono inferior)

    def area(self) -> float:
        """Área de UNA pieza con costuras (cm²)."""
        a = self.largo * (self.ancho_mitad_inicio + self.ancho_mitad_fin)
        return a + self.pestana * 2 * self.ancho_mitad_inicio


@dataclass(frozen=True)
class Boca:
    diametro: float
    circunferencia_aro: float
    ancho_por_gajo: float
    pestana: float
    radio_pared_a_llama: float       # radio de la pared a la altura de la llama
    diametro_mecha: float
    holgura_plano_boca: float         # radio_boca - radio_mecha
    holgura_ok: bool
    diametro_minimo: float            # boca mínima para esa mecha


@dataclass(frozen=True)
class Vuelo:
    volumen_m3: float
    empuje_g: float
    masa_papel_g: float
    carga_libre_g: float             # empuje - papel
    masa_estructura_g: float         # aro + varillas (alambre)
    carga_neta_g: float              # lo que queda para mecha + combustible
    pliegos: float


@dataclass(frozen=True)
class Resultado:
    entrada: Entrada
    diametro_max: float
    ancho_gajo: float
    largo_picos_total: float
    superior: Pieza
    pico: Pieza
    inferior: Pieza
    boca: Boca
    vuelo: Vuelo
    gajos_min_70cm: int
    gajos_min_50cm: int
    altura_armada_estimada: float
    area_total_m2: float
    avisos: list[str]
    viable: bool


def _tabla(nombre, largo, intervalos, x0, x1, pestana=0.0) -> Pieza:
    paso = largo / intervalos
    pts = [Punto(i + 1, 0.0 if i == 0 else paso, paso * i,
                 x0 + (x1 - x0) * i / intervalos) for i in range(intervalos + 1)]
    return Pieza(nombre, largo, x0, x1, pts, pestana)


def _par_arriba(x: float) -> int:          # equivale a EVEN() de Excel
    n = math.ceil(x)
    return n + (n % 2)


def _geometria(l_sup, l_inf, r, rb, h_picos):
    """Alturas verticales y volumen (cm, cm³) con la boca de radio rb."""
    h_sup = math.sqrt(l_sup**2 - r**2)
    h_inf = math.sqrt(max(l_inf**2 - (r - rb) ** 2, 0.0))
    v = (math.pi * r**2 * h_sup / 3                       # cono superior
         + math.pi * r**2 * h_picos                       # banda de picos (cilindro: cota alta)
         + math.pi * h_inf / 3 * (r**2 + r * rb + rb**2))  # tronco inferior
    return h_sup, h_inf, v


def empuje_por_m3(c: Condiciones) -> float:
    """Gramos de empuje por m³ de aire caliente (gas ideal)."""
    ta, ti = c.t_ambiente + 273.15, c.t_interior + 273.15
    rho = c.presion_pa / (287.05 * ta)
    return rho * (1 - ta / ti) * 1000


def calcular(e: Entrada, c: Condiciones = Condiciones()) -> Resultado:
    e.validar()
    medio_cos = e.costura / 2
    d_max = e.altura * F_DIAMETRO
    r = d_max / 2
    ancho_gajo = math.pi * d_max / e.gajos
    d_boca = e.diametro_boca if e.diametro_boca else e.altura * F_BOCA
    rb = d_boca / 2
    ancho_boca = math.pi * d_boca / e.gajos

    largo_picos = ancho_gajo * e.hileras_picos
    restante = e.altura - largo_picos
    l_sup, l_inf = restante * F_CONO_SUP, restante * F_CONO_INF
    l_pico = ancho_gajo * F_PICO

    if l_sup <= r:
        raise ValueError("Cono superior imposible: reduce gajos/picos o sube la altura")
    if rb >= r:
        raise ValueError("La boca no puede ser mayor que el diámetro máximo")

    ancho_max_m = ancho_gajo / 2 + medio_cos
    sup = _tabla("Cono superior", l_sup, INTERVALOS["Cono superior"], medio_cos, ancho_max_m)
    pico = _tabla("Pico", l_pico, INTERVALOS["Pico"], medio_cos, ancho_max_m)
    inf = _tabla("Cono inferior", l_inf, INTERVALOS["Cono inferior"],
                 ancho_boca / 2 + medio_cos, ancho_max_m, pestana=e.pestana_boca)

    h_sup, h_inf, v_cm3 = _geometria(l_sup, l_inf, r, rb, largo_picos)
    altura_armada = h_sup + largo_picos + h_inf

    # --- Boca / mecha ---
    pared_llama = rb + min(e.altura_llama, h_inf) * (r - rb) / h_inf
    d_mecha = e.diametro_mecha or F_MECHA * d_boca
    hol = rb - d_mecha / 2
    boca = Boca(d_boca, math.pi * d_boca, ancho_boca, e.pestana_boca, pared_llama,
                d_mecha, hol, hol >= e.holgura_min, d_mecha + 2 * e.holgura_min)

    # --- Área, pliegos, empuje ---
    area_cm2 = e.gajos * (sup.area() + e.hileras_picos * pico.area() + inf.area())
    area_m2 = area_cm2 / 1e4
    vol = v_cm3 / 1e6
    empuje = vol * empuje_por_m3(c)
    masa = area_m2 * c.papel_gm2 * (1 + c.extra_pegamento)
    pliegos = area_cm2 * (1 + c.desperdicio) / (PLIEGO_CM[0] * PLIEGO_CM[1])
    # aro principal + varillas hacia el centro (cota alta: varillas de largo = radio de boca)
    long_alambre_m = (math.pi * d_boca + e.varillas * rb) / 100
    seccion_m2 = math.pi * (e.alambre_mm / 2000) ** 2
    m_estr = long_alambre_m * seccion_m2 * DENSIDAD_ACERO * 1000
    vuelo = Vuelo(vol, empuje, masa, empuje - masa, m_estr, empuje - masa - m_estr, pliegos)

    res = Resultado(e, d_max, ancho_gajo, largo_picos, sup, pico, inf, boca, vuelo,
                    _par_arriba(math.pi * d_max / 70), _par_arriba(math.pi * d_max / 50),
                    altura_armada, area_m2, [], True)
    avisos = _diagnostico(res)
    return Resultado(**{**res.__dict__, "avisos": avisos,
                        "viable": not any(a.startswith("ERROR") for a in avisos)})


def _diagnostico(r: Resultado) -> list[str]:
    """Chequeos de viabilidad para cualquier medida. 'ERROR' = no viable."""
    e, b, v = r.entrada, r.boca, r.vuelo
    av = []
    if r.ancho_gajo > 70:
        av.append(f"AVISO: gajo de {r.ancho_gajo:.0f} cm (>70). Usa ≥ {r.gajos_min_70cm} gajos.")
    elif r.ancho_gajo > PLIEGO_CM[1]:
        av.append("AVISO: el gajo no cabe en el lado largo del pliego; habrá que unir pliegos a lo ancho.")
    if not b.holgura_ok:
        av.append(f"ERROR: holgura mecha→papel {b.holgura_plano_boca:.1f} cm < {e.holgura_min:.0f} cm. "
                  f"Sube la boca a ≥ {b.diametro_minimo:.0f} cm o reduce la mecha.")
    if v.carga_libre_g <= 0:
        av.append("ERROR: el empuje no vence ni el peso del papel; el globo no vuela (aumenta el tamaño).")
    elif v.carga_neta_g <= 0:
        av.append("ERROR: el empuje no alcanza para papel + aro/parrilla.")
    elif e.masa_mecha_g is not None and v.carga_neta_g < e.masa_mecha_g:
        av.append(f"ERROR: tu mecha pesa {e.masa_mecha_g:.0f} g y solo hay {v.carga_neta_g:.0f} g de margen.")
    elif v.carga_neta_g < 0.25 * v.empuje_g:
        av.append("AVISO: margen de carga bajo (<25 % del empuje); poco colchón ante frío o viento.")
    if not av:
        av.append("OK: medidas viables con los supuestos actuales.")
    return av


def comparar_bocas(e: Entrada, fracciones=(0.08, 0.11, 0.14, 0.17),
                   c: Condiciones = Condiciones()) -> list[dict]:
    """Efecto del diámetro de boca (fracción de la altura) en vuelo y holgura."""
    filas = []
    for f in fracciones:
        r = calcular(Entrada(**{**e.__dict__, "diametro_boca": e.altura * f}), c)
        filas.append({"boca_cm": r.boca.diametro, "pct": f, "volumen_m3": r.vuelo.volumen_m3,
                      "carga_libre_g": r.vuelo.carga_libre_g,
                      "holgura_cm": r.boca.holgura_plano_boca,
                      "pared_a_llama_cm": r.boca.radio_pared_a_llama})
    return filas


def tabla_texto(p: Pieza) -> str:
    lineas = [f"\n--- {p.nombre} ---",
              f"{'Paso':<5}| {'Largo(cm)':>10} | {'Acum.(cm)':>10} | {'Ancho/2(cm)':>11}"]
    lineas += [f"#{q.paso:<4}| {q.largo:>10.4f} | {q.acumulado:>10.4f} | {q.ancho_mitad:>11.4f}"
               for q in p.puntos]
    if p.pestana:
        lineas.append(f"+ pestaña de {p.pestana:.1f} cm después del paso #1 "
                      f"(ancho recto = {2 * p.puntos[0].ancho_mitad:.2f} cm)")
    return "\n".join(lineas)


if __name__ == "__main__":
    # Ajusta diametro_mecha (cm) con la medida real de tu mecha
    e = Entrada(altura=950, gajos=30, hileras_picos=2, costura=1)   # mecha = 50 % de la boca
    res = calcular(e)
    for pieza in (res.superior, res.pico, res.inferior):
        print(tabla_texto(pieza))
    b, v = res.boca, res.vuelo
    print(f"\nBoca: Ø{b.diametro:.1f} cm | aro (perímetro) {b.circunferencia_aro:.1f} cm | "
          f"{b.ancho_por_gajo:.1f} cm por gajo")
    print(f"Mecha Ø{b.diametro_mecha:.1f} cm | holgura mecha->borde: {b.holgura_plano_boca:.1f} cm "
          f"({'OK' if b.holgura_ok else 'INSUFICIENTE'}) | boca mínima: {b.diametro_minimo:.1f} cm")
    print(f"Pared a {e.altura_llama:.0f} cm sobre la boca: radio {b.radio_pared_a_llama:.1f} cm")
    print(f"Volumen {v.volumen_m3:.1f} m³ | empuje {v.empuje_g/1000:.1f} kg | papel {v.masa_papel_g/1000:.1f} kg "
          f"| carga libre {v.carga_libre_g/1000:.1f} kg | pliegos ≈ {v.pliegos:.0f}")
    print(f"Estructura (aro+varillas) ≈ {v.masa_estructura_g:.0f} g | carga neta p/ mecha {v.carga_neta_g/1000:.1f} kg")
    for a in res.avisos:
        print(a)
    print(f"Altura armada ≈ {res.altura_armada_estimada:.0f} cm | papel {res.area_total_m2:.1f} m²")