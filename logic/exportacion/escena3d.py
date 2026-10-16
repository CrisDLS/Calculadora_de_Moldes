from typing import Dict, Any, List, Optional
from logic.models import BalloonInput, BalloonCalculationResult
from logic.geometria.malla_trompo import construir_malla, normal_triangulo
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, color_de_cara
from logic.diseno.paleta import ColorPapel, color_por_id, cargar_catalogo

def escena_a_dict(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    esquema_pintura: Optional[EsquemaPintura] = None,
    esquema_diseno: Optional[EsquemaDiseno] = None,
    catalogo: Optional[List[ColorPapel]] = None
) -> Dict[str, Any]:
    """Genera la estructura de datos serializable para renderizado 3D en three.js.
    
    Cada cara cuadrilátera se triangula explícitamente en dos triángulos.
    Todas las normales apuntan hacia el exterior del globo.
    El z de la boca está en z = 0.
    """
    pintura = esquema_pintura or EsquemaPintura()
    cat = catalogo if catalogo is not None else cargar_catalogo()
    malla = construir_malla(entrada, resultado)
    verts = malla.vertices

    # Triangulación de caras y empaquetado para three.js
    caras_3d: List[Dict[str, Any]] = []

    for cara in malla.caras:
        id_color = color_de_cara(pintura, cara, esquema_diseno, entrada.num_gajos)
        obj_color = color_por_id(id_color, cat)
        color_hex = obj_color.hex

        # Índices de vértices de la cara
        iv = cara.indices_vertices

        if len(iv) == 3:
            # Ya es un triángulo
            # Normal hacia afuera
            n = normal_triangulo(verts[iv[0]], verts[iv[1]], verts[iv[2]])
            caras_3d.append({
                "indices": [iv[0], iv[1], iv[2]],
                "normal": n,
                "color": color_hex,
                "seccion": cara.seccion,
                "gajo": cara.gajo,
                "hilera": cara.hilera,
                "sub": cara.sub,
            })
        elif len(iv) == 4:
            # Trapecio o cuadrilátero: dividir en 2 triángulos [v0, v1, v2] y [v0, v2, v3]
            n1 = normal_triangulo(verts[iv[0]], verts[iv[1]], verts[iv[2]])
            caras_3d.append({
                "indices": [iv[0], iv[1], iv[2]],
                "normal": n1,
                "color": color_hex,
                "seccion": cara.seccion,
                "gajo": cara.gajo,
                "hilera": cara.hilera,
                "sub": cara.sub,
            })
            n2 = normal_triangulo(verts[iv[0]], verts[iv[2]], verts[iv[3]])
            caras_3d.append({
                "indices": [iv[0], iv[2], iv[3]],
                "normal": n2,
                "color": color_hex,
                "seccion": cara.seccion,
                "gajo": cara.gajo,
                "hilera": cara.hilera,
                "sub": cara.sub,
            })

    # Centro y dimensiones para centrado de cámara
    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)
    min_z = min(v[2] for v in verts)
    max_z = max(v[2] for v in verts)

    # Normalización: vértices float serializables
    vertices_serializables = [[float(v[0]), float(v[1]), float(v[2])] for v in verts]

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
        "texturas": {}  # Reservado para F5 (decoraciones y motivos)
    }
