import math
import pytest
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.geometria.malla_trompo import construir_malla, malla_a_dict, Malla, Cara

def dist_3d(v1, v2):
    return math.hypot(v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2])

def dist_2d(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def area_3d(v0, v1, v2):
    u = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
    v = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    return math.hypot(nx, ny, nz) / 2.0

def area_cuadrilatero(v0, v1, v2, v3):
    return area_3d(v0, v1, v2) + area_3d(v0, v2, v3)

def test_malla_propiedades():
    calc = TrompoEstrellaCalculator()
    casos = [
        (950, 30, 2, 1, False, 0),
        (500, 12, 1, 1, True, 4.0),
        (400, 16, 1, 1, False, 0),
        (380, 60, 2, 1, True, 2.0)
    ]
    
    for h, g, hil, c, av, p in casos:
        e = BalloonInput(h, g, hil, c, usar_parametros_avanzados=av, pestana_boca=p)
        r = calc.calcular(e)
        malla = construir_malla(e, r)
        
        # 1. Cantidad de caras
        # inferior: N, superior: N, picos: 4 * N * hileras
        esperadas_caras = g + g + 4 * g * hil
        assert len(malla.caras) == esperadas_caras
        
        # 2. Cantidad de vértices
        # boca: N, bandas (hileras+1): N*(hil+1), apex: 1, apices picos: N*hil
        esperados_vertices = g + g * (hil + 1) + 1 + g * hil
        assert len(malla.vertices) == esperados_vertices
        
        # 3. Z mínimo y máximo
        zs = [v[2] for v in malla.vertices]
        rs = [math.hypot(v[0], v[1]) for v in malla.vertices]
        
        assert min(zs) == pytest.approx(0.0)
        assert max(zs) == pytest.approx(r.altura_total_real, rel=0.03) # Tolerancia ~3% por N=12
        assert max(rs) == pytest.approx(r.ancho_total_con_picos / 2, rel=0.03)
        
        a = r.ancho_max_gajo
        ab = r.boca.ancho_por_gajo if (av and r.boca) else (math.pi * r.diametro_boquilla_calculado / g)
        l_sup = r.seccion_superior.generatriz_total
        l_inf = r.seccion_inferior.generatriz_total
        l_pico = r.seccion_picos.generatriz_total

        # 4. Chequeo por cara: planaridad, isometría, área y normales
        aristas = {}
        def add_arista(i, j, cara_idx):
            edge = tuple(sorted([i, j]))
            aristas.setdefault(edge, []).append(cara_idx)

        for idx_c, cara in enumerate(malla.caras):
            if cara.seccion == "inferior":
                # Trapecio
                v0, v1, v2, v3 = [malla.vertices[i] for i in cara.indices_vertices]
                uv0, uv1, uv2, uv3 = cara.uv_cm
                
                assert dist_3d(v0, v1) == pytest.approx(ab, abs=1e-6)
                assert dist_3d(v3, v2) == pytest.approx(a, abs=1e-6)
                borde_3d = math.sqrt(l_inf**2 + ((a - ab)/2)**2)
                assert dist_3d(v1, v2) == pytest.approx(borde_3d, abs=1e-6)
                
                area_plana = l_inf * (ab + a) / 2
                assert area_cuadrilatero(v0, v1, v2, v3) == pytest.approx(area_plana, abs=1e-6)
                
                # isometria
                assert dist_3d(v0, v1) == pytest.approx(dist_2d(uv0, uv1), abs=1e-6)
                assert dist_3d(v1, v2) == pytest.approx(dist_2d(uv1, uv2), abs=1e-6)
                assert dist_3d(v0, v2) == pytest.approx(dist_2d(uv0, uv2), abs=1e-6)
                
                add_arista(cara.indices_vertices[0], cara.indices_vertices[1], idx_c)
                add_arista(cara.indices_vertices[1], cara.indices_vertices[2], idx_c)
                add_arista(cara.indices_vertices[2], cara.indices_vertices[3], idx_c)
                add_arista(cara.indices_vertices[3], cara.indices_vertices[0], idx_c)

            elif cara.seccion == "superior":
                v0, v1, v2 = [malla.vertices[i] for i in cara.indices_vertices]
                uv0, uv1, uv2 = cara.uv_cm
                
                assert dist_3d(v0, v1) == pytest.approx(a, abs=1e-6)
                borde_3d = math.sqrt(l_sup**2 + (a/2)**2)
                assert dist_3d(v0, v2) == pytest.approx(borde_3d, abs=1e-6)
                
                area_plana = l_sup * a / 2
                assert area_3d(v0, v1, v2) == pytest.approx(area_plana, abs=1e-6)
                
                assert dist_3d(v0, v1) == pytest.approx(dist_2d(uv0, uv1), abs=1e-6)
                assert dist_3d(v0, v2) == pytest.approx(dist_2d(uv0, uv2), abs=1e-6)
                
                add_arista(cara.indices_vertices[0], cara.indices_vertices[1], idx_c)
                add_arista(cara.indices_vertices[1], cara.indices_vertices[2], idx_c)
                add_arista(cara.indices_vertices[2], cara.indices_vertices[0], idx_c)

            elif cara.seccion == "pico":
                v0, v1, v2 = [malla.vertices[i] for i in cara.indices_vertices]
                uv0, uv1, uv2 = cara.uv_cm
                
                assert dist_3d(v0, v1) == pytest.approx(a, abs=1e-6)
                # OJO: Por cómo definimos h_p, el apotema del pico (altura 2D) no es el lado. 
                # El lado inclinado es sqrt(l_pico^2 + (a/2)^2) 
                lado_esperado = math.sqrt(l_pico**2 + (a/2)**2)
                assert dist_3d(v1, v2) == pytest.approx(lado_esperado, abs=1e-6)
                assert dist_3d(v0, v2) == pytest.approx(lado_esperado, abs=1e-6)
                
                area_plana = a * l_pico / 2
                assert area_3d(v0, v1, v2) == pytest.approx(area_plana, abs=1e-6)
                
                assert dist_3d(v0, v1) == pytest.approx(dist_2d(uv0, uv1), abs=1e-6)
                assert dist_3d(v1, v2) == pytest.approx(dist_2d(uv1, uv2), abs=1e-6)
                
                add_arista(cara.indices_vertices[0], cara.indices_vertices[1], idx_c)
                add_arista(cara.indices_vertices[1], cara.indices_vertices[2], idx_c)
                add_arista(cara.indices_vertices[2], cara.indices_vertices[0], idx_c)
                
            # Todas las normales apuntan hacia afuera (producto punto con centro o vector de posición debe ser > 0 aprox)
            v0 = malla.vertices[cara.indices_vertices[0]]
            nx, ny, nz = cara.normal
            if nz != 0 or nx != 0 or ny != 0:
                # El origen (0,0,z) está adentro, así que v0 - (0,0,z) apunta hacia afuera 
                out_vec = (v0[0], v0[1], 0)
                # Producto punto
                dot = out_vec[0]*nx + out_vec[1]*ny
                if cara.seccion != "superior" and cara.seccion != "inferior": 
                     assert dot >= -1e-6

        # 5. Superficie cerrada salvo la boca
        # Las aristas de la boca pertenecen a 1 sola cara (cono inferior).
        # El resto debe pertenecer a exactamente 2 caras.
        aristas_boca = 0
        for edge, faces in aristas.items():
            if len(faces) == 1:
                # Debe ser de la boca (z=0)
                v1 = malla.vertices[edge[0]]
                v2 = malla.vertices[edge[1]]
                assert v1[2] == pytest.approx(0.0)
                assert v2[2] == pytest.approx(0.0)
                aristas_boca += 1
            else:
                assert len(faces) == 2, f"Arista compartida por {len(faces)} caras"
        assert aristas_boca == g

def test_serializacion():
    calc = TrompoEstrellaCalculator()
    e = BalloonInput(380, 12, 1, 1, usar_parametros_avanzados=False)
    r = calc.calcular(e)
    malla = construir_malla(e, r)
    
    d = malla_a_dict(malla)
    assert "vertices" in d
    assert "caras" in d
    assert "anillos" in d
    assert len(d["vertices"]) == len(malla.vertices)
    assert len(d["caras"]) == len(malla.caras)
    
    import json
    json_str = json.dumps(d)
    assert isinstance(json_str, str)
    assert len(json_str) > 0
