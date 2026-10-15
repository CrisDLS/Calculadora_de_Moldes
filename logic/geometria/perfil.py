"""
Cálculo del perfil armado proyectado de la malla 3D.
"""
from dataclasses import dataclass
from typing import List, Tuple
import math
from logic.models import BalloonInput, BalloonCalculationResult
from logic.geometria.malla_trompo import construir_malla

@dataclass
class AnilloPerfil:
    nombre: str
    z: float
    radio: float
    semiancho_silueta: float

@dataclass
class PiramidePerfil:
    hilera: int
    gajo: int
    apex_x: float
    apex_z: float
    base_superior_z: float
    base_inferior_z: float
    lado: str  # "derecha" o "izquierda"
    es_borde_extremo: bool

@dataclass
class DimensionesPerfil:
    alto_total: float
    diametro_cuerpo: float
    ancho_con_picos: float
    diametro_boca: float
    alturas_hileras: List[float]

@dataclass
class PerfilArmado:
    contorno_derecho: List[Tuple[float, float]]   # (x, z) de abajo (z=0) hacia arriba (z=alto)
    contorno_izquierdo: List[Tuple[float, float]] # (x, z) simétrico (-x, z)
    anillos: List[AnilloPerfil]
    piramides: List[PiramidePerfil]
    dimensiones: DimensionesPerfil
    mostrar_picos_al_borde: bool


def perfil_armado(
    entrada: BalloonInput,
    resultado: BalloonCalculationResult,
    mostrar_picos_al_borde: bool = True
) -> PerfilArmado:
    """Calcula la silueta y cotas del perfil armado proyectando la malla 3D sobre el plano vertical X-Z."""
    malla = construir_malla(entrada, resultado)
    N = entrada.num_gajos
    hileras = entrada.num_hileras_picos

    # Si mostrar_picos_al_borde=True, rotamos pi / N para que un pico quede exactamente
    # alineado con el eje X (máxima extensión lateral).
    rot_angle = (math.pi / N) if mostrar_picos_al_borde else 0.0

    verts_rot = []
    cos_rot = math.cos(rot_angle)
    sin_rot = math.sin(rot_angle)
    for (x, y, z) in malla.vertices:
        x_rot = x * cos_rot - y * sin_rot
        verts_rot.append((x_rot, z))

    # Anillos en Z
    idx_boca = malla.anillos["boca"]
    z_boca = verts_rot[idx_boca[0]][1]
    xs_boca = [verts_rot[i][0] for i in idx_boca]
    r_boca_silueta = max(xs_boca)

    anillos_picos = malla.anillos["picos"]
    zs_picos = [verts_rot[anillo[0]][1] for anillo in anillos_picos]
    r_cuerpo_silueta = max(max(verts_rot[i][0] for i in anillo) for anillo in anillos_picos)

    idx_apex = malla.anillos["apex"]
    z_apex = verts_rot[idx_apex][1]

    # Altura de cada hilera (distancia entre anillos consecutivos de picos)
    alturas_hileras = []
    for j in range(hileras):
        alturas_hileras.append(zs_picos[j+1] - zs_picos[j])

    # Lista de anillos: boca, borde inferior de banda, y uno por hilera (hileras + 2 anillos en total)
    anillos_lista: List[AnilloPerfil] = []
    anillos_lista.append(AnilloPerfil("Boca", z_boca, malla.anillos["rb_boca"], r_boca_silueta))
    anillos_lista.append(AnilloPerfil("Banda inferior", zs_picos[0], malla.anillos["r_cuerpo"], r_cuerpo_silueta))
    for j in range(1, hileras + 1):
        nombre = f"Hilera {j}" if j < hileras else "Banda superior"
        anillos_lista.append(AnilloPerfil(nombre, zs_picos[j], malla.anillos["r_cuerpo"], r_cuerpo_silueta))

    # Pirámides proyectadas
    piramides_lista: List[PiramidePerfil] = []
    # Encontrar ápices de pirámides
    for j in range(hileras):
        z_base_inf = zs_picos[j]
        z_base_sup = zs_picos[j+1]
        for k in range(N):
            # Tomamos una cara de la pirámide (j, k)
            caras_pir = [c for c in malla.caras if c.seccion == "pico" and c.hilera == j and c.gajo == k]
            if not caras_pir:
                continue
            apex_idx = caras_pir[0].indices_vertices[2]
            ax, az = verts_rot[apex_idx]

            # Determinamos si está en el lado derecho o izquierdo
            if ax > r_cuerpo_silueta * 0.5:
                # Es visible en la derecha
                es_extremo = abs(ax - max(v[0] for v in verts_rot)) < 1e-4
                piramides_lista.append(PiramidePerfil(
                    hilera=j,
                    gajo=k,
                    apex_x=ax,
                    apex_z=az,
                    base_superior_z=z_base_sup,
                    base_inferior_z=z_base_inf,
                    lado="derecha",
                    es_borde_extremo=es_extremo,
                ))
            elif ax < -r_cuerpo_silueta * 0.5:
                # Es visible en la izquierda
                es_extremo = abs(ax - min(v[0] for v in verts_rot)) < 1e-4
                piramides_lista.append(PiramidePerfil(
                    hilera=j,
                    gajo=k,
                    apex_x=ax,
                    apex_z=az,
                    base_superior_z=z_base_sup,
                    base_inferior_z=z_base_inf,
                    lado="izquierda",
                    es_borde_extremo=es_extremo,
                ))

    # Construir contorno derecho (de z=0 a z=apex)
    contorno_der: List[Tuple[float, float]] = []
    contorno_der.append((r_boca_silueta, z_boca))
    contorno_der.append((r_cuerpo_silueta, zs_picos[0]))

    # Para cada hilera, si hay pirámide extrema al borde, el contorno sale hacia el ápice
    for j in range(hileras):
        z_sup = zs_picos[j+1]
        pir_extrema = next((p for p in piramides_lista if p.hilera == j and p.lado == "derecha" and p.es_borde_extremo), None)
        if pir_extrema:
            contorno_der.append((pir_extrema.apex_x, pir_extrema.apex_z))
        contorno_der.append((r_cuerpo_silueta, z_sup))

    contorno_der.append((0.0, z_apex))

    # Contorno izquierdo simétrico
    contorno_izq = [(-x, z) for x, z in contorno_der]

    # Dimensiones
    ancho_con_picos = max(p[0] for p in contorno_der) * 2.0
    diametro_cuerpo = r_cuerpo_silueta * 2.0
    diametro_boca = r_boca_silueta * 2.0
    alto_total = z_apex - z_boca

    dimensiones = DimensionesPerfil(
        alto_total=alto_total,
        diametro_cuerpo=diametro_cuerpo,
        ancho_con_picos=ancho_con_picos,
        diametro_boca=diametro_boca,
        alturas_hileras=alturas_hileras,
    )

    return PerfilArmado(
        contorno_derecho=contorno_der,
        contorno_izquierdo=contorno_izq,
        anillos=anillos_lista,
        piramides=piramides_lista,
        dimensiones=dimensiones,
        mostrar_picos_al_borde=mostrar_picos_al_borde,
    )
