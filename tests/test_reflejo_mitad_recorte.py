"""Pruebas de recorte (clipPath) del reflejo en modo Mitad (espejo) en abanico y gajos exportados."""

from pathlib import Path
import re
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.lienzo import Diseno, importar_recurso
from logic.exportacion.svg_abanico import (
    calcular_parametros_proyeccion_abanico,
    svg_abanico,
)
from logic.models import BalloonInput


def _extraer_puntos_path(d_str: str):
    """Extrae lista de tuplas (x, y) de un atributo d='M x,y L x,y ... Z'."""
    pares = re.findall(r"([-+]?\d+(?:\.\d+)?),([-+]?\d+(?:\.\d+)?)", d_str)
    return [(float(x), float(y)) for x, y in pares]


@pytest.mark.parametrize(
    "modo_esquema,tam_grupo",
    [
        ("espejo_total", 4),
        ("central_espejo", 5),
    ],
)
def test_clip_path_reflejo_en_modo_mitad(modo_esquema, tam_grupo):
    """Paso 1: Verifica en el SVG generado en modo mitad con mostrar_reflejo=True:
    (a) El grupo del original tiene clip-path en x >= 0 dentro del abanico.
    (b) El grupo del reflejo tiene clip-path en x <= 0, espejo exacto del anterior.
    (c) El clip-path NO está en el mismo elemento que lleva la transformación del espejo.
    (d) Ningún grupo de diseño queda sin clip-path.
    """
    with TemporaryDirectory() as td:
        tmp = Path(td)
        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)

        entrada = BalloonInput(
            altura_cuerpo=950.0,
            num_gajos=20,
            num_hileras_picos=2,
            ancho_costura=1.0,
        )
        resultado = TrompoEstrellaCalculator().calcular(entrada)
        esquema = EsquemaDiseno(modo=modo_esquema, tam_grupo=tam_grupo)

        # Capa SVG y capa PNG que cruzan el eje x=0 (x=-20, ancho=50 -> va de x=-20 a x=+30)
        ruta_svg = Path("docs/ejemplos/disenos/mosaico_geometrico.svg")
        assert ruta_svg.exists()
        ruta_png = tmp / "cruzando_eje.png"
        Image.new("RGBA", (200, 120), color=(20, 160, 80, 255)).save(ruta_png)

        capa_svg = importar_recurso(ruta_svg, rec_dir)
        capa_svg.x = -20.0
        capa_svg.y = 140.0
        capa_svg.ancho = 50.0
        capa_svg.alto = 50.0

        capa_png = importar_recurso(ruta_png, rec_dir)
        capa_png.x = -15.0
        capa_png.y = 200.0
        capa_png.ancho = 40.0
        capa_png.alto = 30.0

        diseno = Diseno(seccion="superior", capas=[capa_svg, capa_png])

        geom = calcular_parametros_proyeccion_abanico(
            resultado=resultado,
            entrada=entrada,
            seccion="superior",
            esquema=esquema,
            hoja="carta",
            dibujar="mitad",
            mostrar_reflejo=True,
        )
        cx_page = geom["cx_page"]
        factor = geom["factor"]

        svg_str = svg_abanico(
            resultado=resultado,
            entrada=entrada,
            seccion="superior",
            esquema=esquema,
            hoja="carta",
            dibujar="mitad",
            diseno=diseno,
            carpeta_recursos=rec_dir,
            mostrar_reflejo=True,
        )

        root = ET.fromstring(svg_str.encode("utf-8"))

        # Mapa de clipPaths en <defs>
        clips = {}
        for cp in root.iter("{http://www.w3.org/2000/svg}clipPath"):
            cid = cp.attrib.get("id")
            path_el = cp.find("{http://www.w3.org/2000/svg}path")
            if cid and path_el is not None:
                clips[cid] = _extraer_puntos_path(path_el.attrib.get("d", ""))

        layer_diseno = None
        for g in root.iter("{http://www.w3.org/2000/svg}g"):
            if g.attrib.get("id") == "layer-diseno":
                layer_diseno = g
                break
        assert layer_diseno is not None, "Debe existir layer-diseno"

        grupos_hijos = [
            ch for ch in list(layer_diseno) if ch.tag.endswith("g")
        ]
        assert len(grupos_hijos) >= 2, "Debe haber grupo original y grupo reflejo en layer-diseno"

        # (d) Ningún grupo de diseño queda sin clip-path
        for g in grupos_hijos:
            gid = g.attrib.get("id", "<sin-id>")
            cp_attr = g.attrib.get("clip-path", "")
            assert cp_attr.startswith("url(#") and cp_attr.endswith(")"), (
                f"Condición (d) falló: el grupo de diseño '{gid}' no tiene clip-path (valor='{cp_attr}')"
            )

        g_orig = next((g for g in grupos_hijos if g.attrib.get("id") == "diseno-mitad-activa"), None)
        g_refl = next((g for g in grupos_hijos if g.attrib.get("id") == "diseno-mitad-reflejo"), None)
        assert g_orig is not None, "Debe existir diseno-mitad-activa"
        assert g_refl is not None, "Debe existir diseno-mitad-reflejo"

        # (a) El grupo del original tiene un clip-path cuyo polígono está en x >= 0 y dentro del abanico
        cp_orig_id = g_orig.attrib.get("clip-path", "")[5:-1]
        assert cp_orig_id in clips, f"No existe clipPath '{cp_orig_id}' en <defs>"
        pts_orig_svg = clips[cp_orig_id]
        assert len(pts_orig_svg) >= 3
        for xs, ys in pts_orig_svg:
            x_plano = (xs - cx_page) / factor
            assert x_plano >= -1e-2, f"Condición (a) falló: punto del clip original en x={x_plano} < 0"

        # (b) El grupo del reflejo tiene un clip-path cuyo polígono es el de la mitad izquierda (x <= 0, espejo exacto)
        cp_refl_attr = g_refl.attrib.get("clip-path", "")
        assert cp_refl_attr.startswith("url(#") and cp_refl_attr.endswith(")"), (
            f"Condición (b) falló: diseno-mitad-reflejo no tiene clip-path (tiene '{cp_refl_attr}')"
        )
        cp_refl_id = cp_refl_attr[5:-1]
        assert cp_refl_id in clips, f"No existe clipPath '{cp_refl_id}' en <defs>"
        pts_refl_svg = clips[cp_refl_id]
        assert len(pts_refl_svg) == len(pts_orig_svg), "El polígono de clip reflejado debe tener el mismo número de vértices"
        for (xs_o, ys_o), (xs_r, ys_r) in zip(pts_orig_svg, pts_refl_svg):
            x_plano_r = (xs_r - cx_page) / factor
            assert x_plano_r <= 1e-2, f"Condición (b) falló: punto del clip reflejo en x={x_plano_r} > 0"
            assert abs((xs_r - cx_page) + (xs_o - cx_page)) <= 0.05, (
                f"Condición (b) falló: xs_r={xs_r} no es espejo de xs_o={xs_o} respecto a cx_page={cx_page}"
            )
            assert abs(ys_r - ys_o) <= 0.05, f"Condición (b) falló: ys_r={ys_r} != ys_o={ys_o}"

        # (c) El clip-path NO está en el mismo elemento que lleva la transformación del espejo
        assert "transform" not in g_refl.attrib, (
            f"Condición (c) falló: el grupo '{g_refl.attrib.get('id')}' con clip-path también tiene transform='{g_refl.attrib.get('transform')}'"
        )
        for ch in g_refl.iter():
            if ch is not g_refl and "transform" in ch.attrib:
                assert "clip-path" not in ch.attrib, (
                    f"Condición (c) falló: el elemento hijo '{ch.attrib.get('id')}' tiene tanto transform como clip-path"
                )


def test_svg_gajo_y_exportar_diseno_modo_mitad():
    """Paso 4: Verifica svg_gajo y exportar_diseno en modo mitad con capa cruzando el eje:
    - En los gajos de la izquierda solo aparece el reflejo de lo que hay a la derecha.
    - En los gajos de la derecha solo aparece el original.
    - En el gajo CENTRAL de un grupo impar (G=5, índice 2), la mitad derecha viene del original
      (recortada a x >= cx) y la mitad izquierda viene del reflejo (recortada a x <= cx),
      sin superponerse el original completo y el reflejo completo.
    """
    from logic.exportacion.svg_diseno import exportar_diseno, svg_gajo

    with TemporaryDirectory() as td:
        tmp = Path(td)
        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)
        out_dir = tmp / "exportados"

        entrada = BalloonInput(
            altura_cuerpo=950.0,
            num_gajos=20,
            num_hileras_picos=2,
            ancho_costura=1.0,
        )
        resultado = TrompoEstrellaCalculator().calcular(entrada)
        esquema = EsquemaDiseno(modo="central_espejo", tam_grupo=5)

        ruta_svg = Path("docs/ejemplos/disenos/mosaico_geometrico.svg")
        capa = importar_recurso(ruta_svg, rec_dir)
        # Cruza el eje x=0: va de x=-20 a x=+30
        capa.x = -20.0
        capa.y = 150.0
        capa.ancho = 50.0
        capa.alto = 50.0
        diseno = Diseno(seccion="superior", capas=[capa])

        # 1. Gajo izquierdo (índice 0 y 1): solo debe contener la capa reflejada, NO la original
        for idx_izq in (0, 1):
            svg_izq = svg_gajo(
                resultado=resultado,
                entrada=entrada,
                seccion="superior",
                esquema=esquema,
                diseno=diseno,
                indice=idx_izq,
                carpeta_recursos=rec_dir,
                dibujar="mitad",
            )
            assert f'id="gajo-capa-{capa.id}_reflejo"' in svg_izq, (
                f"En gajo izquierdo {idx_izq} debe estar la capa reflejada"
            )
            assert f'id="gajo-capa-{capa.id}"' not in svg_izq, (
                f"En gajo izquierdo {idx_izq} NO debe estar la capa original sin reflejar"
            )

        # 2. Gajo derecho (índice 3 y 4): solo debe contener la capa original, NO la reflejada
        for idx_der in (3, 4):
            svg_der = svg_gajo(
                resultado=resultado,
                entrada=entrada,
                seccion="superior",
                esquema=esquema,
                diseno=diseno,
                indice=idx_der,
                carpeta_recursos=rec_dir,
                dibujar="mitad",
            )
            assert f'id="gajo-capa-{capa.id}"' in svg_der, (
                f"En gajo derecho {idx_der} debe estar la capa original"
            )
            assert f'id="gajo-capa-{capa.id}_reflejo"' not in svg_der, (
                f"En gajo derecho {idx_der} NO debe estar la capa reflejada"
            )

        # 3. Gajo central (índice 2 en G=5 impar): mitad derecha del original y mitad izquierda del reflejo
        svg_central = svg_gajo(
            resultado=resultado,
            entrada=entrada,
            seccion="superior",
            esquema=esquema,
            diseno=diseno,
            indice=2,
            carpeta_recursos=rec_dir,
            dibujar="mitad",
        )
        root_c = ET.fromstring(svg_central.encode("utf-8"))
        clips_c = {}
        for cp in root_c.iter("{http://www.w3.org/2000/svg}clipPath"):
            cid = cp.attrib.get("id")
            path_el = cp.find("{http://www.w3.org/2000/svg}path")
            if cid and path_el is not None:
                clips_c[cid] = _extraer_puntos_path(path_el.attrib.get("d", ""))

        assert "clip-gajo-2-der" in clips_c, "El gajo central debe definir clip-gajo-2-der para la mitad derecha"
        assert "clip-gajo-2-izq" in clips_c, "El gajo central debe definir clip-gajo-2-izq para la mitad izquierda"

        # Verificar que clip-gajo-2-der está en x >= cx y clip-gajo-2-izq en x <= cx
        pts_all = clips_c["clip-gajo-2"]
        cx_gajo = sum(p[0] for p in pts_all) / len(pts_all)
        for x_d, _ in clips_c["clip-gajo-2-der"]:
            assert x_d >= cx_gajo - 0.5, f"Punto de clip-gajo-2-der ({x_d}) a la izquierda de cx ({cx_gajo})"
        for x_i, _ in clips_c["clip-gajo-2-izq"]:
            assert x_i <= cx_gajo + 0.5, f"Punto de clip-gajo-2-izq ({x_i}) a la derecha de cx ({cx_gajo})"

        g_der_c = next(
            (g for g in root_c.iter("{http://www.w3.org/2000/svg}g") if g.attrib.get("id") == "diseno-gajo-central-der"),
            None,
        )
        g_izq_c = next(
            (g for g in root_c.iter("{http://www.w3.org/2000/svg}g") if g.attrib.get("id") == "diseno-gajo-central-izq"),
            None,
        )
        assert g_der_c is not None and g_der_c.attrib.get("clip-path") == "url(#clip-gajo-2-der)"
        assert g_izq_c is not None and g_izq_c.attrib.get("clip-path") == "url(#clip-gajo-2-izq)"

        ids_en_der = [el.attrib.get("id") for el in g_der_c.iter() if el.attrib.get("id")]
        ids_en_izq = [el.attrib.get("id") for el in g_izq_c.iter() if el.attrib.get("id")]
        assert f"gajo-capa-{capa.id}" in ids_en_der
        assert f"gajo-capa-{capa.id}_reflejo" not in ids_en_der
        assert f"gajo-capa-{capa.id}_reflejo" in ids_en_izq
        assert f"gajo-capa-{capa.id}" not in ids_en_izq

        # 4. Verificar exportar_diseno completo en modo mitad
        archivos = exportar_diseno(
            carpeta=out_dir,
            resultado=resultado,
            entrada=entrada,
            esquema=esquema,
            diseno=diseno,
            carpeta_recursos=rec_dir,
            seccion="superior",
            dibujar="mitad",
        )
        assert len(archivos) == 6  # 1 abanico + 5 gajos
        svg_ab_exp = (out_dir / "hoja_abanico_superior.svg").read_text(encoding="utf-8")
        assert 'id="diseno-mitad-activa"' in svg_ab_exp
        assert 'clip-path="url(#clip-abanico)"' in svg_ab_exp
        svg_g1_exp = (out_dir / "gajo_01.svg").read_text(encoding="utf-8")
        assert f'id="gajo-capa-{capa.id}_reflejo"' in svg_g1_exp
        assert f'id="gajo-capa-{capa.id}"' not in svg_g1_exp
        svg_g3_exp = (out_dir / "gajo_03.svg").read_text(encoding="utf-8")
        assert 'clip-path="url(#clip-gajo-2-der)"' in svg_g3_exp
        assert 'clip-path="url(#clip-gajo-2-izq)"' in svg_g3_exp
        svg_g5_exp = (out_dir / "gajo_05.svg").read_text(encoding="utf-8")
        assert f'id="gajo-capa-{capa.id}"' in svg_g5_exp
        assert f'id="gajo-capa-{capa.id}_reflejo"' not in svg_g5_exp


def test_modo_editar_no_dibuja_reflejo_y_muestra_nota():
    """Paso 3: En modo EDITAR no se dibuja el reflejo y se muestra la nota discreta."""
    from app_flet.vistas.trompo import VistaTrompo

    class MockPage:
        def __init__(self):
            self.title = ""
            self.services = []
            self.controls = []
            self.overlay = []

        def update(self):
            pass

        def run_thread(self, fn, *args, **kwargs):
            fn(*args, **kwargs)

    with TemporaryDirectory() as td:
        tmp = Path(td)
        vista = VistaTrompo()
        vista._page = MockPage()
        vista.on_calcular(None)

        rec_dir = tmp / "recursos"
        rec_dir.mkdir(parents=True, exist_ok=True)
        vista.controlador.carpeta_recursos = rec_dir

        cfg = vista.controlador.obtener_config_seccion("superior")
        cfg.esquema = EsquemaDiseno(modo="central_espejo", tam_grupo=5)
        cfg.dibujar = "mitad"
        vista.controlador.diseno_lienzo_modo = "mitad"
        vista.controlador.diseno_mostrar_reflejo = True

        ruta_svg = Path("docs/ejemplos/disenos/mosaico_geometrico.svg")
        capa = vista.controlador.anadir_capa(str(ruta_svg))
        vista.controlador.capa_seleccionada_id = capa.id
        vista._sync_controlador_a_vista(vista.controlador.get_view_model())

        pestana = vista.pestana_diseno
        pestana.visor.zona_medida = True
        pestana.visor.zona_ancho = 700.0
        pestana.visor.zona_alto = 500.0

        exito = pestana.cambiar_modo_interaccion("editar")
        assert exito is True
        assert "diseno-mitad-reflejo" not in vista.controlador.svg_diseno
        assert "El reflejo se muestra al volver a Navegar" in pestana.lbl_estado_diseno.value

