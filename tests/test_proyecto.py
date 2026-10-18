import pytest
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_proyecto_ida_y_vuelta(tmp_path):
    ent = BalloonInput(
        380, 30, 2, 1,
        usar_parametros_avanzados=True,
        diametro_boca=50.0,
        pestana_boca=4.0,
        diametro_mecha=25.0,
        masa_mecha_g=40.0,
        alambre_mm=1.5,
        varillas=2,
        altura_llama=40.0,
        holgura_min=10.0,
    )
    cond = Condiciones(t_ambiente=25.0, t_interior=75.0)
    ciclo = [(0, False), (1, False), (2, True), (1, True)]
    esq = EsquemaDiseno("personalizado", 4, ciclo=ciclo)
    p1 = Proyecto(2, "Test Completo", ent, cond, esq, "Nota test", hoja="a4", escala=15)
    
    ruta = tmp_path / "test.json"
    guardar_proyecto(p1, str(ruta))
    
    p2 = cargar_proyecto(str(ruta))
    assert p2.version == 2
    assert p2.nombre == "Test Completo"
    assert p2.entrada.altura_cuerpo == 380
    assert p2.entrada.usar_parametros_avanzados is True
    assert p2.entrada.diametro_boca == 50.0
    assert p2.entrada.pestana_boca == 4.0
    assert p2.condiciones.t_interior == 75.0
    assert p2.esquema.modo == "personalizado"
    assert p2.esquema.tam_grupo == 4
    assert p2.esquema.ciclo == [(0, False), (1, False), (2, True), (1, True)]
    assert p2.hoja == "a4"
    assert p2.escala == 15
    assert p2.notas == "Nota test"
    assert "superior" in p2.config_secciones
    assert "inferior" in p2.config_secciones
    assert "pico" in p2.config_secciones

def test_proyecto_migracion_v1_a_v2(tmp_path):
    ruta = tmp_path / "v1.json"
    contenido_v1 = {
        "version": 1,
        "nombre": "Proyecto V1",
        "entrada": {
            "altura_cuerpo": 380,
            "num_gajos": 20,
            "num_hileras_picos": 2,
            "ancho_costura": 1,
        },
        "esquema": {
            "modo": "repeticion",
            "tam_grupo": 4,
        },
        "hoja": "carta",
        "escala": "auto",
        "notas": "Proyecto antiguo",
    }
    import json
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido_v1, f)

    p = cargar_proyecto(str(ruta))
    assert p.version == 2
    assert p.nombre == "Proyecto V1"
    assert "superior" in p.config_secciones
    assert "inferior" in p.config_secciones
    assert "pico" in p.config_secciones
    assert p.config_secciones["superior"].esquema.modo == "repeticion"
    assert p.config_secciones["superior"].esquema.tam_grupo == 4
    assert p.config_secciones["inferior"].esquema.modo == "repeticion"

def test_proyecto_version_desconocida(tmp_path):
    ruta = tmp_path / "bad_v.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 99, "nombre": "bad"}')
    with pytest.raises(ValueError, match="Versión de proyecto desconocida"):
        cargar_proyecto(str(ruta))

def test_proyecto_json_corrupto(tmp_path):
    ruta = tmp_path / "corrupto.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{version: 1')
    with pytest.raises(ValueError, match="El archivo no es un JSON válido"):
        cargar_proyecto(str(ruta))

def test_proyecto_campos_faltantes_valores_defecto(tmp_path):
    ruta = tmp_path / "faltantes.json"
    # Archivo viejo: sin esquema, condiciones, notas, hoja ni escala
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min", "entrada": {"altura_cuerpo": 100, "num_gajos": 10, "num_hileras_picos": 1, "ancho_costura": 1}}')
    
    p = cargar_proyecto(str(ruta))
    assert p.esquema is None
    assert p.notas == ""
    assert p.hoja == "carta"
    assert p.escala == "auto"
    assert p.condiciones.t_ambiente == 28.0 # valor por defecto de Condiciones

def test_proyecto_falta_entrada(tmp_path):
    ruta = tmp_path / "sin_ent.json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('{"version": 1, "nombre": "min"}')
    
    with pytest.raises(ValueError, match="Falta el campo requerido: entrada"):
        cargar_proyecto(str(ruta))


def test_proyecto_guardar_como_con_recursos_persistencia(tmp_path):
    from PIL import Image
    from app_flet.controlador import ControladorTrompo
    import shutil

    # 1. Crear imágenes en una carpeta temporal
    dir_origen = tmp_path / "archivos_fuente"
    dir_origen.mkdir()
    png_path = dir_origen / "foto.png"
    Image.new("RGB", (80, 80), color="red").save(png_path)
    svg_path = dir_origen / "logo.svg"
    svg_path.write_text('<svg viewBox="0 0 100 100"><rect width="100" height="100" fill="blue"/></svg>')

    # 2. Proyecto nuevo sin título, añadir PNG y SVG
    ctrl = ControladorTrompo()
    ctrl.calcular()
    ctrl.cambiar_diseno_seccion("superior")
    c_png = ctrl.anadir_capa(str(png_path))
    c_svg = ctrl.anadir_capa(str(svg_path))

    # 3. Guardar como en una carpeta de destino
    dir_guardado = tmp_path / "guardados_test"
    dir_guardado.mkdir()
    ruta_proy = dir_guardado / "mi_proyecto.json"

    ok, msg = ctrl.guardar(str(ruta_proy))
    assert ok is True

    # Los archivos deben existir junto al .json en <nombre>_recursos
    rec_dir = dir_guardado / "mi_proyecto_recursos"
    assert rec_dir.exists(), "La carpeta mi_proyecto_recursos no fue creada"
    assert (rec_dir / c_png.archivo).exists(), f"El archivo {c_png.archivo} no existe en {rec_dir}"
    assert (rec_dir / c_svg.archivo).exists(), f"El archivo {c_svg.archivo} no existe en {rec_dir}"

    # 4. Abrir con un controlador nuevo: las capas deben resolver sus archivos sin faltantes
    ctrl2 = ControladorTrompo()
    ok_abrir, msg_abrir = ctrl2.abrir(str(ruta_proy))
    assert ok_abrir is True
    assert ctrl2.recursos_faltantes == []
    # El SVG de diseño generado debe contener las imágenes resueltas
    assert "data:image" in ctrl2.svg_diseno or 'fill="blue"' in ctrl2.svg_diseno

    # 5. Añadir una imagen a un proyecto ya guardado y Guardar directamente
    svg_extra = dir_origen / "extra.svg"
    svg_extra.write_text('<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="green"/></svg>')
    c_extra = ctrl2.anadir_capa(str(svg_extra))
    ok_g2, msg_g2 = ctrl2.guardar()
    assert ok_g2 is True
    assert (rec_dir / c_extra.archivo).exists(), f"La nueva capa {c_extra.archivo} no está en {rec_dir}"

    # 6. Copiar el .json con su carpeta de recursos a otro lugar y abrirlo
    dir_movido = tmp_path / "otro_lugar"
    dir_movido.mkdir()
    ruta_movida = dir_movido / "mi_proyecto.json"
    shutil.copy2(ruta_proy, ruta_movida)
    shutil.copytree(rec_dir, dir_movido / "mi_proyecto_recursos")

    ctrl3 = ControladorTrompo()
    ok_abrir3, msg_abrir3 = ctrl3.abrir(str(ruta_movida))
    assert ok_abrir3 is True
    assert ctrl3.recursos_faltantes == []
    dis_sup3 = ctrl3.disenos["superior"]
    assert len(dis_sup3.capas) == 3

    # 7. Si al abrir falta una imagen: no se borra la capa y aparece en recursos_faltantes
    (rec_dir / c_png.archivo).unlink()
    contenido_antes = ruta_proy.read_text(encoding="utf-8")
    ctrl4 = ControladorTrompo()
    ok_abrir4, msg_abrir4 = ctrl4.abrir(str(ruta_proy))
    assert ok_abrir4 is True
    assert c_png.archivo in ctrl4.recursos_faltantes
    assert len(ctrl4.disenos["superior"].capas) == 3  # No se borró la capa
    # El .json NO se modificó al abrir
    assert ruta_proy.read_text(encoding="utf-8") == contenido_antes

    # 8. Comprobar que la vista muestra el aviso visible con el nombre del archivo faltante
    from app_flet.vistas.trompo import VistaTrompo
    vista = VistaTrompo()
    vista.controlador = ctrl4
    vista._sync_controlador_a_vista(ctrl4.get_view_model())

    col_capas = vista.pestana_diseno.inspector.col_lista_capas
    textos_aviso = []
    def _extraer_textos(control):
        if hasattr(control, "value") and control.value:
            textos_aviso.append(control.value)
        if hasattr(control, "content") and control.content:
            _extraer_textos(control.content)
        if hasattr(control, "controls") and control.controls:
            for child in control.controls:
                _extraer_textos(child)
    _extraer_textos(col_capas)
    assert any(c_png.archivo in t for t in textos_aviso), f"El archivo faltante {c_png.archivo} no se muestra en la vista: {textos_aviso}"
