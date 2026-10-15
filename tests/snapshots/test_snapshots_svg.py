import json
from pathlib import Path
import pytest

from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, importar_recurso
from logic.exportacion.estilos import IMPRESION
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto, svg_hoja
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.svg_perfil import svg_perfil
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_diseno import svg_gajo
from logic.exportacion.escena3d import escena_a_dict
from tests.snapshots.generar_snapshots import SNAPSHOTS_DIR, sha256_texto, obtener_capa_fija_ejemplo

@pytest.fixture(scope="module")
def hashes_esperados():
    p = SNAPSHOTS_DIR / "svg_hashes.json"
    assert p.exists(), "No existe svg_hashes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def test_comparar_todos_los_hashes_svg_y_3d(tmp_path, hashes_esperados):
    calc = TrompoEstrellaCalculator()
    
    rec_tmp = tmp_path / "rec"
    capa_ejemplo = obtener_capa_fija_ejemplo(rec_tmp)
    diseno_con_capa = Diseno(seccion="superior", capas=[capa_ejemplo]) if capa_ejemplo else None
    
    casos = [
        ("950_simple", BalloonInput(altura_cuerpo=950, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0, usar_parametros_avanzados=False)),
        ("950_avanzado", BalloonInput(altura_cuerpo=950, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0, usar_parametros_avanzados=True, diametro_boca=104.5, pestana_boca=4.0)),
        ("380_simple", BalloonInput(altura_cuerpo=380, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0, usar_parametros_avanzados=False)),
        ("380_avanzado", BalloonInput(altura_cuerpo=380, num_gajos=30, num_hileras_picos=2, ancho_costura=1.0, usar_parametros_avanzados=True, diametro_boca=53.2, pestana_boca=4.0)),
        ("N20_repeticion", BalloonInput(altura_cuerpo=600, num_gajos=20, num_hileras_picos=2, ancho_costura=1.0)),
        ("N20_central_espejo", BalloonInput(altura_cuerpo=600, num_gajos=20, num_hileras_picos=2, ancho_costura=1.0)),
        ("N20_espejo_total", BalloonInput(altura_cuerpo=600, num_gajos=20, num_hileras_picos=2, ancho_costura=1.0)),
        ("N24_G12", BalloonInput(altura_cuerpo=700, num_gajos=24, num_hileras_picos=2, ancho_costura=1.0)),
    ]
    
    esquemas_map = {
        "N20_repeticion": EsquemaDiseno("repeticion", 5),
        "N20_central_espejo": EsquemaDiseno("central_espejo", 5),
        "N20_espejo_total": EsquemaDiseno("espejo_total", 4),
        "N24_G12": EsquemaDiseno("espejo_total", 12),
    }

    discrepancias = []
    
    for clave_caso, inp in casos:
        res = calc.calcular(inp)
        esq = esquemas_map.get(clave_caso, EsquemaDiseno("repeticion", 5))
        
        for con_diseno in [False, True]:
            suf_dis = "_con_diseno" if con_diseno else "_sin_diseno"
            dis = diseno_con_capa if con_diseno else None
            
            # svg_pieza
            for sec in ["superior", "pico", "inferior"]:
                k = f"svg_pieza_{clave_caso}_{sec}{suf_dis}"
                svg_p = svg_pieza(res, inp, sec, escala=10.0)
                h = sha256_texto(svg_p)
                if h != hashes_esperados.get(k):
                    discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                    
            # svg_conjunto
            k = f"svg_conjunto_{clave_caso}{suf_dis}"
            svg_c = svg_conjunto(res, inp, escala=10.0)
            h = sha256_texto(svg_c)
            if h != hashes_esperados.get(k):
                discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                
            # svg_hoja
            for sec in ["superior", "pico", "inferior"]:
                k = f"svg_hoja_{clave_caso}_{sec}{suf_dis}"
                svg_h = svg_hoja(res, inp, sec, esq, escala="auto", hoja="carta")
                h = sha256_texto(svg_h)
                if h != hashes_esperados.get(k):
                    discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                    
            # svg_abanico
            for sec in ["superior", "pico", "inferior"]:
                k = f"svg_abanico_{clave_caso}_{sec}{suf_dis}"
                svg_ab = svg_abanico(res, inp, sec, esquema=esq, diseno=dis, carpeta_recursos=rec_tmp)
                h = sha256_texto(svg_ab)
                if h != hashes_esperados.get(k):
                    discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                    
            # svg_perfil
            k = f"svg_perfil_{clave_caso}{suf_dis}"
            perf = perfil_armado(inp, res)
            svg_perf = svg_perfil(perf)
            h = sha256_texto(svg_perf)
            if h != hashes_esperados.get(k):
                discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                
            # svg_gajo
            for idx_g in [0, 1]:
                k = f"svg_gajo_{clave_caso}_g{idx_g}{suf_dis}"
                svg_g = svg_gajo(res, inp, "superior", esquema=esq, diseno=dis, indice=idx_g, carpeta_recursos=rec_tmp)
                h = sha256_texto(svg_g)
                if h != hashes_esperados.get(k):
                    discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")
                    
            # escena3d
            k = f"escena3d_{clave_caso}{suf_dis}"
            escena = escena_a_dict(inp, res)
            escena_json = json.dumps(escena, sort_keys=True)
            h = sha256_texto(escena_json)
            if h != hashes_esperados.get(k):
                discrepancias.append(f"{k}: esperado {hashes_esperados.get(k)}, obtenido {h}")

    assert not discrepancias, f"Discrepancias en hashes SVG/3D:\n" + "\n".join(discrepancias)
