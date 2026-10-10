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

@pytest.fixture(scope="module")
def calculos():
    calc = TrompoEstrellaCalculator()
    casos = [
        (950, 30, 2, 1, False, 0),
        (500, 12, 1, 1, True, 4.0),
        (400, 16, 1, 1, False, 0),
        (380, 60, 3, 1, True, 2.0)
    ]
    resultados = []
    for h, g, hil, c, av, p in casos:
        e = BalloonInput(h, g, hil, c, usar_parametros_avanzados=av, pestana_boca=p)
        r = calc.calcular(e)
        malla = construir_malla(e, r)
        resultados.append((e, r, malla))
    return resultados

def test_malla_conteo_caras_vertices(calculos):
    for e, r, malla in calculos:
        g, hil = e.num_gajos, e.num_hileras_picos
        esperadas_caras = g + g + 4 * g * hil
        assert len(malla.caras) == esperadas_caras
        
        esperados_vertices = g + g * (hil + 1) + 1 + g * hil
        assert len(malla.vertices) == esperados_vertices

def test_malla_caras_planas(calculos):
    for _, _, malla in calculos:
        for cara in malla.caras:
            # Si es cuadrilatero, verificar planaridad
            if len(cara.indices_vertices) == 4:
                v0, v1, v2, v3 = [malla.vertices[i] for i in cara.indices_vertices]
                # Volumen de tetraedro debe ser aprox 0
                u = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
                v = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
                w = (v3[0]-v0[0], v3[1]-v0[1], v3[2]-v0[2])
                dot_cross = u[0]*(v[1]*w[2]-v[2]*w[1]) - u[1]*(v[0]*w[2]-v[2]*w[0]) + u[2]*(v[0]*w[1]-v[1]*w[0])
                assert abs(dot_cross) < 1e-6

def test_malla_isometria_y_area(calculos):
    for e, r, malla in calculos:
        for cara in malla.caras:
            verts = [malla.vertices[i] for i in cara.indices_vertices]
            uvs = cara.uv_cm
            # Comprobar bordes UV == 3D
            for i in range(len(verts)):
                j = (i + 1) % len(verts)
                assert dist_3d(verts[i], verts[j]) == pytest.approx(dist_2d(uvs[i], uvs[j]), abs=1e-6)
            
            # Comprobar diagonales si es cuadrilátero
            if len(verts) == 4:
                assert dist_3d(verts[0], verts[2]) == pytest.approx(dist_2d(uvs[0], uvs[2]), abs=1e-6)
                assert dist_3d(verts[1], verts[3]) == pytest.approx(dist_2d(uvs[1], uvs[3]), abs=1e-6)
            
            # Area
            a = r.ancho_max_gajo
            if cara.seccion == "inferior":
                ab = r.boca.ancho_por_gajo if (e.usar_parametros_avanzados and r.boca) else (math.pi * r.diametro_boquilla_calculado / e.num_gajos)
                l_inf = r.seccion_inferior.generatriz_total
                area_plana = l_inf * (ab + a) / 2
                assert area_cuadrilatero(*verts) == pytest.approx(area_plana, abs=1e-6)
            elif cara.seccion == "superior":
                l_sup = r.seccion_superior.generatriz_total
                area_plana = l_sup * a / 2
                assert area_3d(*verts) == pytest.approx(area_plana, abs=1e-6)
            elif cara.seccion == "pico":
                l_pico = r.seccion_picos.generatriz_total
                area_plana = l_pico * a / 2
                assert area_3d(*verts) == pytest.approx(area_plana, abs=1e-6)

def test_malla_eje_central_y_bordes(calculos):
    for e, r, malla in calculos:
        a = r.ancho_max_gajo
        ab = r.boca.ancho_por_gajo if (e.usar_parametros_avanzados and r.boca) else (math.pi * r.diametro_boquilla_calculado / e.num_gajos)
        l_sup = r.seccion_superior.generatriz_total
        l_inf = r.seccion_inferior.generatriz_total
        
        for cara in malla.caras:
            verts = [malla.vertices[i] for i in cara.indices_vertices]
            if cara.seccion == "inferior":
                v0, v1, v2, v3 = verts
                assert dist_3d(v0, v1) == pytest.approx(ab, abs=1e-6) # boca
                assert dist_3d(v3, v2) == pytest.approx(a, abs=1e-6)  # banda superior
                # Eje central = l_inf
                mid_bottom = ((v0[0]+v1[0])/2, (v0[1]+v1[1])/2, (v0[2]+v1[2])/2)
                mid_top = ((v2[0]+v3[0])/2, (v2[1]+v3[1])/2, (v2[2]+v3[2])/2)
                assert dist_3d(mid_bottom, mid_top) == pytest.approx(l_inf, abs=1e-6)
            elif cara.seccion == "superior":
                v0, v1, v2 = verts
                assert dist_3d(v0, v1) == pytest.approx(a, abs=1e-6) # banda inferior
                # Eje central = l_sup
                mid_base = ((v0[0]+v1[0])/2, (v0[1]+v1[1])/2, (v0[2]+v1[2])/2)
                assert dist_3d(mid_base, v2) == pytest.approx(l_sup, abs=1e-6)

def test_malla_pico_geometria(calculos):
    for e, r, malla in calculos:
        a = r.ancho_max_gajo
        l_pico = r.seccion_picos.generatriz_total
        for cara in malla.caras:
            if cara.seccion == "pico":
                v0, v1, v2 = [malla.vertices[i] for i in cara.indices_vertices]
                assert dist_3d(v0, v1) == pytest.approx(a, abs=1e-6)
                # Eje central
                mid_base = ((v0[0]+v1[0])/2, (v0[1]+v1[1])/2, (v0[2]+v1[2])/2)
                assert dist_3d(mid_base, v2) == pytest.approx(l_pico, abs=1e-6)
                # Lados
                lado = math.sqrt(l_pico**2 + (a/2)**2)
                assert dist_3d(v0, v2) == pytest.approx(lado, abs=1e-6)
                assert dist_3d(v1, v2) == pytest.approx(lado, abs=1e-6)

def test_malla_normales_hacia_afuera(calculos):
    for _, _, malla in calculos:
        for cara in malla.caras:
            v0 = malla.vertices[cara.indices_vertices[0]]
            nx, ny, nz = cara.normal
            if nz != 0 or nx != 0 or ny != 0:
                # Centroide aproximado 
                cx = sum(malla.vertices[i][0] for i in cara.indices_vertices) / len(cara.indices_vertices)
                cy = sum(malla.vertices[i][1] for i in cara.indices_vertices) / len(cara.indices_vertices)
                
                dot = cx*nx + cy*ny
                if cara.seccion != "superior" and cara.seccion != "inferior":
                    assert dot > 0.0

def test_malla_dimensiones_globales(calculos):
    for _, r, malla in calculos:
        zs = [v[2] for v in malla.vertices]
        rs = [math.hypot(v[0], v[1]) for v in malla.vertices]
        assert min(zs) == pytest.approx(0.0)
        assert max(zs) == pytest.approx(r.altura_total_real, rel=0.03) # relajamos tol a 3% debido a polígono (mencionado docstring)
        assert max(rs) == pytest.approx(r.ancho_total_con_picos / 2, rel=0.03)

def test_malla_superficie_cerrada(calculos):
    for e, _, malla in calculos:
        aristas = {}
        for cara in malla.caras:
            for i in range(len(cara.indices_vertices)):
                edge = tuple(sorted([cara.indices_vertices[i], cara.indices_vertices[(i+1)%len(cara.indices_vertices)]]))
                aristas.setdefault(edge, []).append(cara)
                
        aristas_boca = 0
        for edge, faces in aristas.items():
            if len(faces) == 1:
                v1 = malla.vertices[edge[0]]
                v2 = malla.vertices[edge[1]]
                assert v1[2] == pytest.approx(0.0)
                assert v2[2] == pytest.approx(0.0)
                aristas_boca += 1
            else:
                assert len(faces) == 2, f"Arista compartida por {len(faces)} caras"
        assert aristas_boca == e.num_gajos

def test_malla_serializacion_json(calculos):
    _, _, malla = calculos[0]
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
