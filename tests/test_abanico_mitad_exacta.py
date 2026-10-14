import re
import math
import pytest
from pathlib import Path
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, CapaDiseno
from logic.geometria.abanico import (
    pieza_a_geometria_plana,
    abanico,
    contorno_abanico,
    area_poligono,
)
from logic.diseno.transformaciones import (
    transformacion_a_gajo,
    construir_grupo,
)
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.svg_diseno import exportar_diseno, svg_gajo

def test_poligono_mitad_exacta_y_area():
    """Verifica que el polígono de mitad tiene x >= 0, borde recto en x=0, y área = mitad exacta."""
    calc = TrompoEstrellaCalculator()
    
    # En conos, el tamaño del grupo es G (ej. 12 o 5); en picos son las 4 caras de la pirámide
    casos = [
        (24, 12, "superior"),
        (24, 12, "inferior"),
        (24, 4, "pico"),
        (20, 5, "superior"),
        (20, 5, "inferior"),
        (20, 4, "pico"),
    ]
    
    for n_gajos, tam_grupo, seccion in casos:
        inp = BalloonInput(altura_cuerpo=950.0, num_gajos=n_gajos, num_hileras_picos=2, ancho_costura=1.0)
        res = calc.calcular(inp)
        pieza = pieza_a_geometria_plana(res, inp, seccion)
        
        pts_comp = contorno_abanico(pieza, n=tam_grupo, dibujar="completo", pasos_arco=32)
        pts_mitad = contorno_abanico(pieza, n=tam_grupo, dibujar="mitad", pasos_arco=32)
        
        # 1. Todos los puntos de la mitad tienen x >= 0
        for pt in pts_mitad:
            assert pt[0] >= -1e-12, f"Punto con x negativa en {seccion} N={n_gajos} G={tam_grupo}: {pt}"
        
        # 2. Borde izquierdo recto sobre x=0
        assert abs(pts_mitad[0][0]) < 1e-12
        assert abs(pts_mitad[1][0]) < 1e-12
        if seccion == "inferior":
            assert pts_mitad[0][1] == pytest.approx(pieza.distancia_vertice, abs=1e-5)
            assert pts_mitad[1][1] == pytest.approx(pieza.radio_arco, abs=1e-5)
        elif seccion == "superior":
            assert pts_mitad[0][1] == pytest.approx(0.0, abs=1e-5)
            assert pts_mitad[1][1] == pytest.approx(pieza.radio_arco, abs=1e-5)
        
        # 3. Área de mitad es EXACTAMENTE la mitad del completo
        a_comp = area_poligono(pts_comp)
        a_mitad = area_poligono(pts_mitad)
        assert a_mitad == pytest.approx(a_comp / 2.0, rel=1e-9, abs=1e-9), \
            f"Fallo de área en {seccion} N={n_gajos} G={tam_grupo}: comp={a_comp}, mitad={a_mitad}"


def test_coordenadas_capas_invariantes_completo_vs_mitad():
    """Verifica que el sistema de coordenadas no cambia y las capas no se mueven al conmutar completo/mitad."""
    diseno = Diseno(
        seccion="superior",
        capas=[
            CapaDiseno(
                id="capa_test",
                nombre="Flor",
                tipo="svg",
                archivo="flor.svg",
                ancho_natural=30.0,
                alto_natural=40.0,
                x=15.0,
                y=120.0,
                ancho=30.0,
                alto=40.0,
                rotacion=15.0,
            )
        ]
    )
    
    # Las coordenadas del modelo permanecen exactamente iguales
    assert diseno.capas[0].x == 15.0
    assert diseno.capas[0].y == 120.0
    
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(altura_cuerpo=950.0, num_gajos=24, num_hileras_picos=2, ancho_costura=1.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("espejo_total", 12)
    
    # Al generar SVG con mostrar_reflejo=True (vista previa en pantalla)
    svg_comp = svg_abanico(res, inp, "superior", esq, dibujar="completo", diseno=diseno, mostrar_reflejo=True)
    svg_mitad = svg_abanico(res, inp, "superior", esq, dibujar="mitad", diseno=diseno, mostrar_reflejo=True)
    
    # La capa se posiciona en las mismas coordenadas SVG relativas al centro
    match_comp = re.search(r'<[^>]+id="capa-capa_test"[^>]*>', svg_comp)
    match_mitad = re.search(r'<[^>]+id="capa-capa_test"[^>]*>', svg_mitad)
    assert match_comp is not None
    assert match_mitad is not None
    
    x_comp = float(re.search(r'x="([^"]+)"', match_comp.group(0)).group(1))
    y_comp = float(re.search(r'y="([^"]+)"', match_comp.group(0)).group(1))
    x_mitad = float(re.search(r'x="([^"]+)"', match_mitad.group(0)).group(1))
    y_mitad = float(re.search(r'y="([^"]+)"', match_mitad.group(0)).group(1))
    
    assert x_comp == pytest.approx(x_mitad, abs=1e-2)
    assert y_comp == pytest.approx(y_mitad, abs=1e-2)


def test_reflejo_afin_y_transformaciones_espejadas():
    """Verifica que T_j(-x, y) = (-x_c, y_c) para gajos opuestos en N=24/G=12 y N=20/G=5."""
    calc = TrompoEstrellaCalculator()
    
    for n_gajos, tam_grupo in [(24, 12), (20, 5)]:
        inp = BalloonInput(altura_cuerpo=950.0, num_gajos=n_gajos, num_hileras_picos=2, ancho_costura=1.0)
        res = calc.calcular(inp)
        
        for seccion in ["superior", "inferior", "pico"]:
            n_caras = 4 if seccion == "pico" else tam_grupo
            pieza = pieza_a_geometria_plana(res, inp, seccion)
            ab = abanico(pieza, n=n_caras, centrado=True)
            
            for i in range(n_caras):
                j = n_caras - 1 - i
                t_i = transformacion_a_gajo(ab, i)
                t_j = transformacion_a_gajo(ab, j)
                
                # Probar punto arbitrario (x, y) en la mitad derecha
                x, y = 20.0, 150.0
                xc_i, yc_i = t_i.transformar_punto((x, y))
                xc_j, yc_j = t_j.transformar_punto((-x, y))
                
                assert xc_j == pytest.approx(-xc_i, abs=1e-10)
                assert yc_j == pytest.approx(yc_i, abs=1e-10)


def test_svg_mitad_elementos_requeridos():
    """Verifica id=eje-espejo-recto, texto eje de espejo, clip-path de mitad y leyendas de par/impar."""
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(altura_cuerpo=950.0, num_gajos=24, num_hileras_picos=2, ancho_costura=1.0)
    res = calc.calcular(inp)
    
    # Caso G par
    esq_par = EsquemaDiseno("espejo_total", 12)
    svg_par = svg_abanico(res, inp, "inferior", esq_par, dibujar="mitad")
    
    assert 'id="eje-espejo-recto"' in svg_par
    assert '>eje de espejo</text>' in svg_par
    assert 'id="clip-abanico"' in svg_par
    assert "Eje de espejo sobre la costura central" in svg_par
    assert 'id="costura-lateral-der"' in svg_par
    assert 'id="costura-lateral-izq"' not in svg_par
    
    # Caso G impar
    esq_impar = EsquemaDiseno("central_espejo", 5)
    svg_impar = svg_abanico(res, inp, "superior", esq_impar, dibujar="mitad")
    
    assert 'id="eje-espejo-recto"' in svg_impar
    assert '>eje de espejo</text>' in svg_impar
    assert "Eje de espejo corta por el centro del gajo central (se asume simétrico)" in svg_impar


def test_exportar_diseno_mitad_produce_mismas_piezas_simetricas(tmp_path):
    """Verifica que exportar_diseno() en mitad produce las mismas piezas que en completo para diseño simétrico."""
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(altura_cuerpo=950.0, num_gajos=24, num_hileras_picos=2, ancho_costura=1.0)
    res = calc.calcular(inp)
    esq = EsquemaDiseno("espejo_total", 4)
    
    # Diseño en la mitad derecha (x >= 0)
    diseno = Diseno(
        seccion="superior",
        capas=[
            CapaDiseno(
                id="estrella",
                nombre="Estrella",
                tipo="svg",
                archivo="estrella.svg",
                ancho_natural=20.0,
                alto_natural=20.0,
                x=10.0,
                y=100.0,
                ancho=20.0,
                alto=20.0,
            )
        ]
    )
    
    # Carpeta temporal para exportación completa
    dir_comp = tmp_path / "comp"
    # Carpeta temporal para exportación mitad
    dir_mitad = tmp_path / "mitad"
    
    archivos_comp = exportar_diseno(
        carpeta=dir_comp,
        resultado=res,
        entrada=inp,
        esquema=esq,
        diseno=diseno,
        seccion="superior",
        dibujar="completo",
    )
    
    archivos_mitad = exportar_diseno(
        carpeta=dir_mitad,
        resultado=res,
        entrada=inp,
        esquema=esq,
        diseno=diseno,
        seccion="superior",
        dibujar="mitad",
    )
    
    assert len(archivos_comp) == len(archivos_mitad)
    
    # Para los gajos de la mitad derecha (gajo 3 y 4 en base 1 con G=4),
    # el contenido de la capa de diseno debe ser equivalente
    for i in range(1, 5):
        gajo_comp = (dir_comp / f"gajo_{i:02d}.svg").read_text(encoding="utf-8")
        gajo_mitad = (dir_mitad / f"gajo_{i:02d}.svg").read_text(encoding="utf-8")
        
        # En la mitad derecha (i=3, 4), el diseño está presente en ambos
        if i in [3, 4]:
            assert 'id="gajo-capa-estrella"' in gajo_comp
            assert 'id="gajo-capa-estrella"' in gajo_mitad
        # En la mitad izquierda (i=1, 2), en modo mitad se reconstruye el reflejo simétrico
        if i in [1, 2]:
            assert 'id="gajo-capa-estrella_reflejo"' in gajo_mitad
