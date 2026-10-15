#!/usr/bin/env python3
"""Generador y verificador de instantáneas (snapshots) del árbol de controles
y de las salidas SVG / 3D.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from typing import Any, Dict, Optional
import flet as ft

from app_flet.vistas.trompo import VistaTrompo
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto, svg_hoja
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.svg_perfil import svg_perfil
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_diseno import svg_gajo
from logic.exportacion.escena3d import escena_a_dict

SNAPSHOTS_DIR = Path(__file__).resolve().parent

class MockPage:
    def __init__(self):
        self.title = ""
        self.services = []
        self.update_count = 0
    def update(self):
        self.update_count += 1
    def run_thread(self, fn, *args, **kwargs):
        fn(*args, **kwargs)

def normalizar_valor(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (bool, int, float)):
        return val
    s = str(val)
    # Normalizar direcciones de memoria tipo 0x00000123ABC
    s = re.sub(r"0x[0-9a-fA-F]+", "<MEM_ADDR>", s)
    # Normalizar rutas Windows/Unix que contengan barras
    s = re.sub(r"[a-zA-Z]:\\[^\s\"'<>]+", "<PATH>", s)
    # Normalizar data URIs o SVG largos en base64
    if len(s) > 300 and ("data:image" in s or "<svg" in s or "base64" in s):
        h = hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
        return f"<CONTENT_LEN_{len(s)}_SHA_{h}>"
    return s

def serializar_arbol(control: Any) -> Optional[Dict[str, Any]]:
    if control is None:
        return None
    
    nodo = {
        "tipo": control.__class__.__name__
    }
    
    # Propiedades visuales y semánticas
    attrs = [
        "value", "text", "label", "visible", "disabled",
        "selected", "tooltip", "icon", "selected_index",
        "read_only", "dense", "wrap", "alignment"
    ]
    for attr in attrs:
        if hasattr(control, attr):
            v = getattr(control, attr)
            if v is not None:
                norm = normalizar_valor(v)
                if norm is not None:
                    nodo[attr] = norm

    # Recorrer hijos
    hijos = []
    if hasattr(control, "controls") and isinstance(control.controls, list):
        for h in control.controls:
            sh = serializar_arbol(h)
            if sh:
                hijos.append(sh)
    if hasattr(control, "content") and control.content is not None and isinstance(control.content, ft.Control):
        sh = serializar_arbol(control.content)
        if sh:
            hijos.append(sh)
    if hasattr(control, "tabs") and isinstance(control.tabs, list):
        for h in control.tabs:
            sh = serializar_arbol(h)
            if sh:
                hijos.append(sh)
    if hasattr(control, "leading") and isinstance(control.leading, ft.Control):
        sh = serializar_arbol(control.leading)
        if sh:
            hijos.append(sh)
    if hasattr(control, "trailing") and isinstance(control.trailing, ft.Control):
        sh = serializar_arbol(control.trailing)
        if sh:
            hijos.append(sh)
            
    if hijos:
        nodo["hijos"] = hijos
        nodo["num_hijos"] = len(hijos)
        
    return nodo

def sha256_texto(texto: str) -> str:
    # Normalizar saltos de línea CRLF/LF para determinismo multiplataforma
    norm = texto.replace("\r\n", "\n").strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def generar_snapshots_ui():
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    
    estados = {}
    
    # 1. Sin datos (arranque)
    v1 = VistaTrompo()
    v1._page = MockPage()
    estados["arbol_sin_datos.json"] = serializar_arbol(v1)
    
    # 2. Con 950/30/2/1 simple
    v2 = VistaTrompo()
    v2._page = MockPage()
    v2.txt_altura.value = "950"
    v2.txt_gajos.value = "30"
    v2.txt_hileras.value = "2"
    v2.txt_costura.value = "1.0"
    v2.switch_avanzado.value = False
    v2.on_calcular(None)
    estados["arbol_950_simple.json"] = serializar_arbol(v2)
    
    # 3. Con 950/30/2/1 avanzado
    v3 = VistaTrompo()
    v3._page = MockPage()
    v3.txt_altura.value = "950"
    v3.txt_gajos.value = "30"
    v3.txt_hileras.value = "2"
    v3.txt_costura.value = "1.0"
    v3.switch_avanzado.value = True
    v3.panel_avanzado.visible = True
    v3.on_calcular(None)
    estados["arbol_950_avanzado.json"] = serializar_arbol(v3)
    
    # 4. Cada una de las 6 pestañas
    for idx in range(6):
        vp = VistaTrompo()
        vp._page = MockPage()
        vp.txt_altura.value = "950"
        vp.txt_gajos.value = "30"
        vp.txt_hileras.value = "2"
        vp.txt_costura.value = "1.0"
        vp.on_calcular(None)
        vp.tabs.selected_index = idx
        vp._sync_controlador_a_vista(vp.controlador.get_view_model())
        estados[f"arbol_pestana_{idx}.json"] = serializar_arbol(vp)
        
    # 5. Tema claro y oscuro
    vo = VistaTrompo()
    vo._page = MockPage()
    vo.on_calcular(None)
    vo.on_toggle_tema(None) # Si estaba en dark, pasa a light o viceversa
    estados["arbol_tema_cambiado.json"] = serializar_arbol(vo)
    
    # 6. Con una capa de diseño cargada (SVG de ejemplo) en cono superior y modo mitad
    vd = VistaTrompo()
    vd._page = MockPage()
    vd.on_calcular(None)
    ej_svg = Path("docs/ejemplos/disenos/medallon.svg")
    rec_tmp = SNAPSHOTS_DIR / "_rec_tmp"
    rec_tmp.mkdir(exist_ok=True)
    if ej_svg.exists():
        vd.controlador.carpeta_recursos = rec_tmp
        vd.controlador.anadir_capa(ej_svg)
    vd.selector_seccion_diseno.selected = ["superior"]
    vd.selector_lienzo_diseno.selected = ["mitad"]
    vd.controlador.cambiar_diseno_seccion("superior")
    vd.controlador.cambiar_diseno_lienzo_modo("mitad")
    vd._sync_controlador_a_vista(vd.controlador.get_view_model())
    estados["arbol_diseno_capa_mitad.json"] = serializar_arbol(vd)
    
    for nombre, arbol in estados.items():
        p = SNAPSHOTS_DIR / nombre
        with open(p, "w", encoding="utf-8") as f:
            json.dump(arbol, f, indent=2, ensure_ascii=False)
        print(f"Guardado snapshot UI: {p.name}")

def obtener_capa_fija_ejemplo(rec_dir: Path) -> Optional[CapaDiseno]:
    import shutil
    ej_svg = Path("docs/ejemplos/disenos/medallon.svg")
    rec_dir.mkdir(parents=True, exist_ok=True)
    if ej_svg.exists():
        dest = rec_dir / "medallon.svg"
        shutil.copy(ej_svg, dest)
        return CapaDiseno(
            id="capa_fija_01",
            nombre="medallon",
            tipo="svg",
            archivo="medallon.svg",
            ancho_natural=15.0,
            alto_natural=15.0,
            ancho=15.0,
            alto=15.0,
            x=0.0,
            y=0.0,
            viewbox=(0.0, 0.0, 100.0, 100.0),
        )
    return None

def generar_snapshots_svg():
    calc = TrompoEstrellaCalculator()
    hashes = {}
    
    rec_tmp = SNAPSHOTS_DIR / "_rec_tmp"
    capa_ejemplo = obtener_capa_fija_ejemplo(rec_tmp)
    diseno_con_capa = Diseno(seccion="superior", capas=[capa_ejemplo]) if capa_ejemplo else None
    
    # Conjuntos de entradas fijas
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

    for clave_caso, inp in casos:
        res = calc.calcular(inp)
        esq = esquemas_map.get(clave_caso, EsquemaDiseno("repeticion", 5))
        
        for con_diseno in [False, True]:
            suf_dis = "_con_diseno" if con_diseno else "_sin_diseno"
            dis = diseno_con_capa if con_diseno else None
            
            # svg_pieza (las 3 secciones)
            for sec in ["superior", "pico", "inferior"]:
                svg_p = svg_pieza(res, inp, sec, escala=10.0)
                hashes[f"svg_pieza_{clave_caso}_{sec}{suf_dis}"] = sha256_texto(svg_p)
                
            # svg_conjunto
            svg_c = svg_conjunto(res, inp, escala=10.0)
            hashes[f"svg_conjunto_{clave_caso}{suf_dis}"] = sha256_texto(svg_c)
            
            # svg_hoja (las 3 secciones)
            for sec in ["superior", "pico", "inferior"]:
                svg_h = svg_hoja(res, inp, sec, esq, escala="auto", hoja="carta")
                hashes[f"svg_hoja_{clave_caso}_{sec}{suf_dis}"] = sha256_texto(svg_h)
                
            # svg_abanico
            for sec in ["superior", "pico", "inferior"]:
                svg_ab = svg_abanico(res, inp, sec, esquema=esq, diseno=dis, carpeta_recursos=rec_tmp)
                hashes[f"svg_abanico_{clave_caso}_{sec}{suf_dis}"] = sha256_texto(svg_ab)
                
            # svg_perfil
            perf = perfil_armado(inp, res)
            svg_perf = svg_perfil(perf)
            hashes[f"svg_perfil_{clave_caso}{suf_dis}"] = sha256_texto(svg_perf)
            
            # svg_gajo
            for idx_g in [0, 1]:
                svg_g = svg_gajo(res, inp, "superior", esquema=esq, diseno=dis, indice=idx_g, carpeta_recursos=rec_tmp)
                hashes[f"svg_gajo_{clave_caso}_g{idx_g}{suf_dis}"] = sha256_texto(svg_g)
                
            # escena3d (JSON)
            escena = escena_a_dict(inp, res)
            escena_json = json.dumps(escena, sort_keys=True)
            hashes[f"escena3d_{clave_caso}{suf_dis}"] = sha256_texto(escena_json)

    salida_hashes = SNAPSHOTS_DIR / "svg_hashes.json"
    with open(salida_hashes, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, sort_keys=True)
    print(f"Guardado hashes SVG: {salida_hashes.name} ({len(hashes)} hashes calculados)")

if __name__ == "__main__":
    generar_snapshots_ui()
    generar_snapshots_svg()
    rec_tmp = SNAPSHOTS_DIR / "_rec_tmp"
    if rec_tmp.exists():
        import shutil
        shutil.rmtree(rec_tmp, ignore_errors=True)
