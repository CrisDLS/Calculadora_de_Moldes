"""
Exportación de paquete de moldes, resumen de esquema y ciclo personalizado.
"""
import os
import re
from typing import Dict, List, Tuple, Union, Optional
from logic.models import BalloonInput, BalloonCalculationResult
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.estilos import IMPRESION
from logic.exportacion.comun import guardar_svg
from logic.exportacion.svg_moldes import svg_hoja, svg_conjunto
from logic.exportacion.svg_abanico import svg_abanico
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_perfil import svg_perfil


def parsear_ciclo(texto: str) -> List[Tuple[int, bool]]:
    """Parsea un ciclo de motivos personalizados desde una cadena separada por comas.
    
    Formato esperado: "0, 1, 2E, 1E" (número entero seguido opcionalmente de 'E' o 'e' para indicar espejo).
    Lanza ValueError con descripción en español y posición ante cualquier error de sintaxis.
    """
    if not texto or not texto.strip():
        raise ValueError("El ciclo no puede estar vacío.")

    elementos = [item.strip() for item in texto.split(",") if item.strip()]
    if not elementos:
        raise ValueError("El ciclo no contiene elementos válidos.")

    resultado = []
    for idx, item in enumerate(elementos, start=1):
        m = re.match(r"^(\d+)([eE]?)$", item)
        if not m:
            raise ValueError(
                f"Elemento inválido en posición {idx}: '{item}'. "
                "Formato esperado: número o número seguido de 'E' (ej. '0', '1', '2E')."
            )
        motivo = int(m.group(1))
        espejo = bool(m.group(2))
        resultado.append((motivo, espejo))

    return resultado


def resumen_esquema(
    esquema: EsquemaDiseno,
    entrada: BalloonInput,
    resultado: BalloonCalculationResult
) -> List[str]:
    """Genera las líneas de resumen del esquema de diseño por motivo para la UI."""
    num_gajos = entrada.num_gajos
    asignaciones = esquema.asignar(num_gajos)
    res_motivos = esquema.resumen_motivos(asignaciones)

    # Cantidad de piezas por gajo
    cant_sup_por_gajo = int(round(resultado.seccion_superior.cantidad / num_gajos))
    cant_pico_por_gajo = int(round(resultado.seccion_picos.cantidad / num_gajos))
    cant_inf_por_gajo = int(round(resultado.seccion_inferior.cantidad / num_gajos))

    lineas = []
    for motivo in sorted(res_motivos.keys()):
        total_gajos, en_espejo, sin_espejo = res_motivos[motivo]
        total_sup = total_gajos * cant_sup_por_gajo
        total_pico = total_gajos * cant_pico_por_gajo
        total_inf = total_gajos * cant_inf_por_gajo

        detalles_espejo = ""
        if en_espejo > 0:
            detalles_espejo = f" (de ellos {en_espejo} en espejo)"

        lineas.append(
            f"Molde {motivo}: cono superior ×{total_sup} · pico ×{total_pico} · cono inferior ×{total_inf}{detalles_espejo}"
        )

    return lineas


def _calcular_escala_comun_hojas(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    esquema: EsquemaDiseno,
    hoja: str,
    margen_mm: float = 10.0,
    gap_mm: float = 5.0
) -> float:
    """Calcula la menor escala entera (o auto) que permita que las tres piezas quepan en la hoja."""
    hoja_w, hoja_h = (215.9, 279.4) if hoja == "carta" else (210.0, 297.0)
    motivos = list(range(esquema.motivos_a_dibujar))
    n_copias = len(motivos)

    piezas = [
        ("superior", resultado.seccion_superior, 0.0),
        ("pico", resultado.seccion_picos, 0.0),
        ("inferior", resultado.seccion_inferior, entrada.pestana_boca if entrada.usar_parametros_avanzados else 0.0),
    ]

    escalas_minimas = []
    for clave, sec, pestana in piezas:
        l_real = sec.generatriz_total + pestana
        w_real = max(p.ancho_medio for p in sec.puntos) * 2

        best_s_pieza = float("inf")
        for orientacion in ["vertical", "horizontal"]:
            w_page, h_page = (hoja_w, hoja_h) if orientacion == "vertical" else (hoja_h, hoja_w)
            for cols in range(1, n_copias + 1):
                rows = (n_copias + cols - 1) // cols
                avail_w = w_page - 2 * margen_mm - (cols - 1) * gap_mm
                avail_h = h_page - 2 * margen_mm - (rows - 1) * gap_mm
                if avail_w <= 0 or avail_h <= 0:
                    continue
                req_s_x = (cols * w_real * 10) / avail_w
                req_s_y = (rows * l_real * 10) / avail_h
                min_s = max(req_s_x, req_s_y)
                if min_s < best_s_pieza:
                    best_s_pieza = min_s
        escalas_minimas.append(best_s_pieza)

    return max(escalas_minimas)


from logic.diseno.pintura import EsquemaPintura
from logic.exportacion.escena3d import escena_a_dict

from logic.diseno.config_seccion import ConfigSeccion

def generar_paquete(
    resultado: BalloonCalculationResult,
    entrada: BalloonInput,
    esquema: Optional[EsquemaDiseno] = None,
    hoja: str = "carta",
    escala: Union[str, float, int] = "auto",
    pintura: Optional[EsquemaPintura] = None,
    incluir_3d: bool = False,
    lienzo: str = "separadas",
    dibujar: str = "completo",
    incluir_abanico: bool = False,
    config_secciones: Optional[Dict[str, ConfigSeccion]] = None,
) -> Dict[str, str]:
    """Genera un diccionario de nombre_archivo -> contenido_SVG/HTML con las hojas de trazo, perfil y conjunto.
    
    Opcionalmente incluye el visor 3D si incluir_3d=True.
    Si se proporciona config_secciones, cada sección utiliza su propio esquema, lienzo y modo de dibujo.
    Todas las hojas usan el estilo IMPRESION.
    """
    if esquema is None:
        if config_secciones and config_secciones.get("superior") and config_secciones["superior"].esquema:
            esquema = config_secciones["superior"].esquema
        else:
            esquema = EsquemaDiseno("repeticion", 5)

    if escala == "auto":
        escala_comun = _calcular_escala_comun_hojas(resultado, entrada, esquema, hoja)
    else:
        escala_comun = float(escala)

    archivos: Dict[str, str] = {}

    if config_secciones:
        # Configuración independiente por sección (Parte 1)
        cfg_sup = config_secciones.get("superior")
        cfg_pico = config_secciones.get("pico")
        cfg_inf = config_secciones.get("inferior")

        esq_sup = cfg_sup.esquema if (cfg_sup and cfg_sup.esquema) else esquema
        esq_pico = cfg_pico.esquema if (cfg_pico and cfg_pico.esquema) else esquema
        esq_inf = cfg_inf.esquema if (cfg_inf and cfg_inf.esquema) else esquema

        lienzo_sup = cfg_sup.lienzo if cfg_sup else lienzo
        lienzo_pico = cfg_pico.lienzo if cfg_pico else lienzo
        lienzo_inf = cfg_inf.lienzo if cfg_inf else lienzo

        dibujar_sup = cfg_sup.dibujar if cfg_sup else dibujar
        dibujar_pico = cfg_pico.dibujar if cfg_pico else dibujar
        dibujar_inf = cfg_inf.dibujar if cfg_inf else dibujar

        esc_sup = cfg_sup.escala if (cfg_sup and cfg_sup.escala != "auto") else escala_comun
        esc_pico = cfg_pico.escala if (cfg_pico and cfg_pico.escala != "auto") else escala_comun
        esc_inf = cfg_inf.escala if (cfg_inf and cfg_inf.escala != "auto") else escala_comun

        # Cono superior
        if lienzo_sup in ("separadas", "ambas"):
            archivos["hoja_cono_superior.svg"] = svg_hoja(
                resultado, entrada, "superior", esq_sup, hoja=hoja, escala=esc_sup, estilo=IMPRESION
            )
        if lienzo_sup in ("abanico", "ambas") or incluir_abanico:
            archivos["hoja_abanico_superior.svg"] = svg_abanico(
                resultado, entrada, "superior", esq_sup, hoja=hoja, escala=esc_sup, estilo=IMPRESION, dibujar=dibujar_sup
            )

        # Pico
        if lienzo_pico in ("separadas", "ambas"):
            archivos["hoja_pico.svg"] = svg_hoja(
                resultado, entrada, "pico", esq_pico, hoja=hoja, escala=esc_pico, estilo=IMPRESION
            )
        if lienzo_pico in ("abanico", "ambas") or incluir_abanico:
            archivos["hoja_abanico_pico.svg"] = svg_abanico(
                resultado, entrada, "pico", esq_pico, hoja=hoja, escala=esc_pico, estilo=IMPRESION, dibujar=dibujar_pico
            )

        # Cono inferior
        if lienzo_inf in ("separadas", "ambas"):
            archivos["hoja_cono_inferior.svg"] = svg_hoja(
                resultado, entrada, "inferior", esq_inf, hoja=hoja, escala=esc_inf, estilo=IMPRESION
            )
        if lienzo_inf in ("abanico", "ambas") or incluir_abanico:
            archivos["hoja_abanico_inferior.svg"] = svg_abanico(
                resultado, entrada, "inferior", esq_inf, hoja=hoja, escala=esc_inf, estilo=IMPRESION, dibujar=dibujar_inf
            )
    else:
        # Modo clásico compatible
        if lienzo in ("separadas", "ambas") or not (lienzo == "abanico" or incluir_abanico):
            archivos["hoja_cono_superior.svg"] = svg_hoja(
                resultado, entrada, "superior", esquema, hoja=hoja, escala=escala_comun, estilo=IMPRESION
            )
            archivos["hoja_pico.svg"] = svg_hoja(
                resultado, entrada, "pico", esquema, hoja=hoja, escala=escala_comun, estilo=IMPRESION
            )
            archivos["hoja_cono_inferior.svg"] = svg_hoja(
                resultado, entrada, "inferior", esquema, hoja=hoja, escala=escala_comun, estilo=IMPRESION
            )

        if lienzo in ("abanico", "ambas") or incluir_abanico:
            archivos["hoja_abanico_superior.svg"] = svg_abanico(
                resultado, entrada, "superior", esquema, hoja=hoja, escala=escala, estilo=IMPRESION, dibujar=dibujar
            )
            archivos["hoja_abanico_pico.svg"] = svg_abanico(
                resultado, entrada, "pico", esquema, hoja=hoja, escala=escala, estilo=IMPRESION, dibujar=dibujar
            )
            archivos["hoja_abanico_inferior.svg"] = svg_abanico(
                resultado, entrada, "inferior", esquema, hoja=hoja, escala=escala, estilo=IMPRESION, dibujar=dibujar
            )

    # 3. Perfil armado (estilo IMPRESION a escala 10 o la de las hojas)
    perf = perfil_armado(entrada, resultado, mostrar_picos_al_borde=True)
    archivos["perfil_armado.svg"] = svg_perfil(perf, estilo=IMPRESION, escala=escala_comun)

    # 4. Conjunto de moldes
    archivos["conjunto_moldes.svg"] = svg_conjunto(resultado, entrada, escala=escala_comun, estilo=IMPRESION)

    # 4. Visor 3D interactivo autocontenido (opcional)
    if incluir_3d:
        try:
            escena = escena_a_dict(entrada, resultado, esquema_pintura=pintura, esquema_diseno=esquema)
            from logic.exportacion.visor3d import generar_html_visor_autocontenido
            archivos["visor_3d.html"] = generar_html_visor_autocontenido(escena)
        except Exception:
            pass

    return archivos


def _nombre_seguro(nombre: str) -> str:
    """Elimina caracteres inválidos en nombres de archivo de Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', nombre)


def guardar_paquete(
    carpeta: str,
    archivos: Dict[str, str],
    sobrescribir: bool = False
) -> List[str]:
    """Guarda los archivos del paquete en la carpeta especificada en codificación UTF-8.
    
    Crea la carpeta si no existe.
    Si algún archivo ya existe y sobrescribir=False, lanza FileExistsError con la lista de archivos que chocan.
    Devuelve la lista de rutas absolutas escritas.
    """
    os.makedirs(carpeta, exist_ok=True)

    rutas_chocan = []
    for nombre in archivos:
        seguro = _nombre_seguro(nombre)
        ruta = os.path.join(carpeta, seguro)
        if os.path.exists(ruta) and not sobrescribir:
            rutas_chocan.append(ruta)

    if rutas_chocan:
        raise FileExistsError(f"Archivos existentes que colisionan: {rutas_chocan}")

    rutas_escritas = []
    for nombre, contenido in archivos.items():
        seguro = _nombre_seguro(nombre)
        ruta = os.path.join(carpeta, seguro)
        guardar_svg(ruta, contenido)
        rutas_escritas.append(os.path.abspath(ruta))

    return rutas_escritas
