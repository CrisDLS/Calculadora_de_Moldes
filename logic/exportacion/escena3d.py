from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from logic.models import BalloonInput, BalloonCalculationResult
from logic.geometria.malla_trompo import construir_malla, normal_triangulo, Cara
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, color_de_cara
from logic.diseno.paleta import ColorPapel, color_por_id, cargar_catalogo
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.lienzo import Diseno
from logic.geometria.textura import mapear_textura


def _empaquetar_triangulo_cara(
    cara: Cara,
    indices: List[int],
    normal: List[float],
    color_hex: str,
    uv: Optional[List[Tuple[float, float]]] = None,
    textura: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea el diccionario serializable de un triángulo individual para Three.js."""
    d: Dict[str, Any] = {
        "indices": indices,
        "normal": normal,
        "color": color_hex,
        "seccion": cara.seccion,
        "gajo": cara.gajo,
        "hilera": cara.hilera,
        "sub": cara.sub,
    }
    if uv is not None:
        d["uv"] = [[round(float(u), 6), round(float(v), 6)] for u, v in uv]
        d["textura"] = textura
    return d


def escena_a_dict(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    esquema_pintura: Optional[EsquemaPintura] = None,
    esquema_diseno: Optional[EsquemaDiseno] = None,
    catalogo: Optional[List[ColorPapel]] = None,
    configuraciones: Optional[Dict[str, ConfigSeccion]] = None,
    disenos: Optional[Dict[str, Diseno]] = None,
    carpeta_recursos: Optional[Union[str, Path]] = None,
    max_px: int = 2048,
) -> Dict[str, Any]:
    """Genera la estructura de datos serializable para renderizado 3D en three.js.
    
    Cada cara cuadrilátera se triangula explícitamente en dos triángulos.
    Todas las normales apuntan hacia el exterior del globo.
    El z de la boca está en z = 0.
    Si se proporcionan configuraciones/diseños, mapea UVs y empaqueta texturas SVG.
    """
    pintura = esquema_pintura or EsquemaPintura()
    cat = catalogo if catalogo is not None else cargar_catalogo()
    malla = construir_malla(entrada, resultado)
    verts = malla.vertices

    # Mapeo de texturas y coordenadas UV
    mapa_tex = None
    if configuraciones is not None or disenos is not None:
        mapa_tex = mapear_textura(
            entrada=entrada,
            resultado=resultado,
            malla=malla,
            configuraciones=configuraciones,
            disenos=disenos,
            carpeta_recursos=carpeta_recursos,
            max_px=max_px,
        )

    # Triangulación de caras y empaquetado para three.js
    caras_3d: List[Dict[str, Any]] = []

    for i_cara, cara in enumerate(malla.caras):
        id_color = color_de_cara(pintura, cara, esquema_diseno, entrada.num_gajos)
        obj_color = color_por_id(id_color, cat)
        color_hex = obj_color.hex

        clave_tex = None
        uv_v = None
        if mapa_tex is not None:
            clave_tex, uv_v = mapa_tex.caras_uv[i_cara]

        # Índices de vértices de la cara
        iv = cara.indices_vertices

        if len(iv) == 3:
            # Triángulo: [iv[0], iv[1], iv[2]]
            n = normal_triangulo(verts[iv[0]], verts[iv[1]], verts[iv[2]])
            tri_uv = [uv_v[0], uv_v[1], uv_v[2]] if uv_v is not None else None
            caras_3d.append(_empaquetar_triangulo_cara(cara, [iv[0], iv[1], iv[2]], n, color_hex, tri_uv, clave_tex))
        elif len(iv) == 4:
            # Trapecio o cuadrilátero: dividir en 2 triángulos [v0, v1, v2] y [v0, v2, v3]
            n1 = normal_triangulo(verts[iv[0]], verts[iv[1]], verts[iv[2]])
            tri1_uv = [uv_v[0], uv_v[1], uv_v[2]] if uv_v is not None else None
            caras_3d.append(_empaquetar_triangulo_cara(cara, [iv[0], iv[1], iv[2]], n1, color_hex, tri1_uv, clave_tex))

            n2 = normal_triangulo(verts[iv[0]], verts[iv[2]], verts[iv[3]])
            tri2_uv = [uv_v[0], uv_v[2], uv_v[3]] if uv_v is not None else None
            caras_3d.append(_empaquetar_triangulo_cara(cara, [iv[0], iv[2], iv[3]], n2, color_hex, tri2_uv, clave_tex))

    # Centro y dimensiones para centrado de cámara
    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)
    min_z = min(v[2] for v in verts)
    max_z = max(v[2] for v in verts)

    # Normalización: vértices float serializables
    vertices_serializables = [[float(v[0]), float(v[1]), float(v[2])] for v in verts]

    # Diccionario de texturas para Three.js
    texturas_dict: Dict[str, Any] = {}
    if mapa_tex is not None:
        for k, info in mapa_tex.texturas.items():
            if info.svg is not None:
                texturas_dict[k] = {
                    "caja": [round(float(val), 4) for val in info.caja_cm],
                    "px": [int(info.tam_px[0]), int(info.tam_px[1])],
                    "svg": info.svg,
                }

    return {
        "metadata": {
            "num_gajos": entrada.num_gajos,
            "hileras": entrada.num_hileras_picos,
            "altura_total": resultado.altura_total_real,
            "ancho_con_picos": resultado.ancho_total_con_picos,
            "bbox": {
                "min": [min_x, min_y, min_z],
                "max": [max_x, max_y, max_z],
                "centro": [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0]
            }
        },
        "vertices": vertices_serializables,
        "caras": caras_3d,
        "anillos": malla.anillos,
        "texturas": texturas_dict,
    }
