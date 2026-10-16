import pytest
from PIL import Image
from logic.models import BalloonInput, Condiciones
from logic.diseno.lienzo import (
    CapaDiseno,
    Diseno,
    importar_recurso,
    MAX_RASTER_DIM,
)
from logic.proyecto.modelo import (
    Proyecto,
    guardar_proyecto,
    cargar_proyecto,
    obtener_carpeta_recursos,
    obtener_archivos_referenciados_por_proyectos,
    recursos_sin_uso,
    mover_a_papelera,
)

def test_importar_raster_valido(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGBA", (100, 200), color=(255, 0, 0, 255))
    img.save(img_path)

    carpeta_recursos = tmp_path / "recursos"
    capa = importar_recurso(img_path, carpeta_recursos)

    assert capa.tipo == "raster"
    assert capa.nombre == "test"
    assert capa.archivo.endswith(".png")
    assert (carpeta_recursos / capa.archivo).exists()
    assert capa.ancho_natural > 0
    assert capa.alto_natural > 0
    # Relación de aspecto 1:2
    assert pytest.approx(capa.alto_natural / capa.ancho_natural, rel=1e-2) == 2.0


def test_importar_raster_exif_rotado(tmp_path):
    # Imagen con metadatos EXIF de rotación (Orientation = 6: 90 deg CW)
    img_path = tmp_path / "foto.jpg"
    img = Image.new("RGB", (100, 200), color="blue")
    exif = img.getexif()
    exif[0x0112] = 6  # Rotación 90 grados
    img.save(img_path, exif=exif)

    carpeta_recursos = tmp_path / "recursos"
    capa = importar_recurso(img_path, carpeta_recursos)

    # Con la orientación 6 corregida, las dimensiones pasan de 100x200 a 200x100
    assert capa.ancho_natural > capa.alto_natural


def test_importar_raster_limites(tmp_path):
    # Dimensión excesiva
    img_path = tmp_path / "gigante.png"
    # Simulamos o creamos una imagen que supere MAX_RASTER_DIM
    # Para no gastar memoria, podemos probar con un archivo que reporte dimensiones falsas o un límite
    # O mockeando Image.open
    with pytest.raises(ValueError, match="dimensiones máximas"):
        img = Image.new("L", (MAX_RASTER_DIM + 10, 10))
        img.save(img_path)
        importar_recurso(img_path, tmp_path / "rec")


def test_importar_svg_valido(tmp_path):
    svg_path = tmp_path / "estrella.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100" width="200mm" height="100mm">
        <circle cx="100" cy="50" r="40" fill="gold" />
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    carpeta_recursos = tmp_path / "recursos"
    capa = importar_recurso(svg_path, carpeta_recursos)

    assert capa.tipo == "svg"
    assert capa.archivo.endswith(".svg")
    assert (carpeta_recursos / capa.archivo).exists()
    # 200 mm = 20.0 cm, 100 mm = 10.0 cm
    assert pytest.approx(capa.ancho_natural, rel=1e-2) == 20.0
    assert pytest.approx(capa.alto_natural, rel=1e-2) == 10.0


def test_importar_svg_rechaza_script(tmp_path):
    svg_path = tmp_path / "malicioso_script.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <script>alert('xss');</script>
        <rect width="50" height="50" />
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    with pytest.raises(ValueError, match="<script>"):
        importar_recurso(svg_path, tmp_path / "rec")


def test_importar_svg_rechaza_foreign_object(tmp_path):
    svg_path = tmp_path / "malicioso_fo.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <foreignObject width="100" height="100">
            <div>Inyección</div>
        </foreignObject>
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    with pytest.raises(ValueError, match="<foreignObject>"):
        importar_recurso(svg_path, tmp_path / "rec")


def test_importar_svg_rechaza_doctype_entity(tmp_path):
    svg_path = tmp_path / "malicioso_entity.svg"
    svg_content = """<?xml version="1.0"?>
    <!DOCTYPE svg [
      <!ENTITY xxe SYSTEM "file:///etc/passwd">
    ]>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <text>&xxe;</text>
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    with pytest.raises(ValueError, match="DOCTYPE o ENTITY"):
        importar_recurso(svg_path, tmp_path / "rec")


def test_importar_svg_rechaza_evento_onload(tmp_path):
    svg_path = tmp_path / "malicioso_onload.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" onload="alert(1)">
        <rect width="10" height="10" />
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    with pytest.raises(ValueError, match="evento no permitido"):
        importar_recurso(svg_path, tmp_path / "rec")


def test_importar_svg_rechaza_url_externa(tmp_path):
    svg_path = tmp_path / "malicioso_url.svg"
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100">
        <image xlink:href="https://sitio-externo.com/malware.png" width="100" height="100" />
    </svg>"""
    svg_path.write_text(svg_content, encoding="utf-8")

    with pytest.raises(ValueError, match="enlace externo no permitido"):
        importar_recurso(svg_path, tmp_path / "rec")


def test_serializacion_proyecto_con_disenos_y_recursos(tmp_path):
    # Crear recurso y capa
    img_path = tmp_path / "flor.png"
    Image.new("RGB", (50, 50), "red").save(img_path)

    proy_path = tmp_path / "globo_arte.json"
    carpeta_recursos = obtener_carpeta_recursos(proy_path)
    capa = importar_recurso(img_path, carpeta_recursos)

    diseno_sup = Diseno(seccion="superior", capas=[capa])
    proy = Proyecto(
        version=1,
        nombre="Globo Arte",
        entrada=BalloonInput(950, 30, 2, 1),
        condiciones=Condiciones(),
        esquema=None,
        notas="Con diseño floral",
        disenos={"superior": diseno_sup},
    )

    guardar_proyecto(proy, str(proy_path))
    assert proy_path.exists()
    assert (carpeta_recursos / capa.archivo).exists()

    # Cargar proyecto
    cargado = cargar_proyecto(str(proy_path))
    assert "superior" in cargado.disenos
    assert len(cargado.disenos["superior"].capas) == 1
    c_capa = cargado.disenos["superior"].capas[0]
    assert c_capa.archivo == capa.archivo
    assert c_capa.nombre == "flor"
    assert len(cargado.recursos_faltantes) == 0


def test_guardar_como_copia_recursos(tmp_path):
    img_path = tmp_path / "textura.png"
    Image.new("RGB", (40, 40), "green").save(img_path)

    proy1_path = tmp_path / "globo1.json"
    carp1 = obtener_carpeta_recursos(proy1_path)
    capa = importar_recurso(img_path, carp1)

    proy = Proyecto(
        version=1,
        nombre="Globo 1",
        entrada=BalloonInput(950, 30, 2, 1),
        condiciones=Condiciones(),
        esquema=None,
        notas="",
        disenos={"superior": Diseno(seccion="superior", capas=[capa])},
    )
    guardar_proyecto(proy, str(proy1_path))

    # Guardar como globo2.json
    proy2_path = tmp_path / "globo2.json"
    guardar_proyecto(proy, str(proy2_path), ruta_anterior=str(proy1_path))

    carp2 = obtener_carpeta_recursos(proy2_path)
    assert carp2.exists()
    assert (carp2 / capa.archivo).exists()


def test_tolerancia_recursos_faltantes(tmp_path):
    proy_path = tmp_path / "globo_incompleto.json"
    capa_fantasma = CapaDiseno(
        id="c1",
        nombre="Inexistente",
        tipo="raster",
        archivo="desaparecido.png",
        ancho_natural=10.0,
        alto_natural=10.0,
    )
    proy = Proyecto(
        version=1,
        nombre="Globo Incompleto",
        entrada=BalloonInput(950, 30, 2, 1),
        condiciones=Condiciones(),
        esquema=None,
        notas="",
        disenos={"superior": Diseno(seccion="superior", capas=[capa_fantasma])},
    )
    guardar_proyecto(proy, str(proy_path))

    # Cargar cuando el archivo no existe en disco
    cargado = cargar_proyecto(str(proy_path))
    assert len(cargado.recursos_faltantes) == 1
    assert "desaparecido.png" in cargado.recursos_faltantes
    assert len(cargado.disenos["superior"].capas) == 1


def test_importar_recurso_deduplicacion(tmp_path):
    """Importar el mismo archivo dos veces produce una sola copia en disco y dos capas."""
    img_path = tmp_path / "original.png"
    Image.new("RGB", (50, 50), "yellow").save(img_path)

    carpeta_recursos = tmp_path / "recursos"

    capa1 = importar_recurso(img_path, carpeta_recursos)
    capa2 = importar_recurso(img_path, carpeta_recursos)

    # Dos capas distintas
    assert capa1.id != capa2.id
    # Apuntan al mismo archivo físico
    assert capa1.archivo == capa2.archivo

    # Solo existe un archivo en la carpeta de recursos
    archivos_disco = [f.name for f in carpeta_recursos.iterdir() if f.is_file()]
    assert len(archivos_disco) == 1
    assert archivos_disco[0] == capa1.archivo


def test_importar_recurso_mismo_nombre_distinto_contenido(tmp_path):
    """Archivos con el mismo nombre pero diferente contenido no se confunden ni se sobrescriben."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    img_a = dir_a / "icono.png"
    img_b = dir_b / "icono.png"

    Image.new("RGB", (20, 20), "red").save(img_a)
    Image.new("RGB", (40, 40), "blue").save(img_b)

    carpeta_recursos = tmp_path / "recursos"

    capa_a = importar_recurso(img_a, carpeta_recursos)
    capa_b = importar_recurso(img_b, carpeta_recursos)

    assert capa_a.archivo != capa_b.archivo
    assert (carpeta_recursos / capa_a.archivo).exists()
    assert (carpeta_recursos / capa_b.archivo).exists()

    archivos_disco = [f.name for f in carpeta_recursos.iterdir() if f.is_file()]
    assert len(archivos_disco) == 2


def test_limpieza_segura_recursos(tmp_path):
    """Archivos sin uso se mueven a _papelera/<fecha>/ sin borrar nada y se pueden restaurar."""
    carpeta_proyectos = tmp_path / "guardados"
    carpeta_proyectos.mkdir()

    carp_rec = carpeta_proyectos / "mi_globo_recursos"
    carp_rec.mkdir()

    # Archivo 1: en uso por proyecto guardado
    img_usada = carp_rec / "flor_12345678.png"
    Image.new("RGB", (10, 10), "red").save(img_usada)

    # Archivo 2: huérfano (sin uso)
    img_huerfana1 = carp_rec / "viejo_no_usado_1.png"
    Image.new("RGB", (10, 10), "blue").save(img_huerfana1)

    # Archivo 3: otro huérfano
    img_huerfana2 = carp_rec / "viejo_no_usado_2.svg"
    img_huerfana2.write_text("<svg></svg>", encoding="utf-8")

    # Guardar proyecto que referencia flor_12345678.png
    proy_path = carpeta_proyectos / "mi_globo.json"
    capa = CapaDiseno(
        id="c1",
        nombre="Flor",
        tipo="raster",
        archivo="flor_12345678.png",
        ancho_natural=10.0,
        alto_natural=10.0,
    )
    proy = Proyecto(
        version=2,
        nombre="mi_globo",
        entrada=BalloonInput(950, 30, 2, 1),
        condiciones=Condiciones(),
        disenos={"superior": Diseno(seccion="superior", capas=[capa])},
    )
    guardar_proyecto(proy, str(proy_path))

    # Identificar referenciados y sin uso
    refs = obtener_archivos_referenciados_por_proyectos(carpeta_proyectos)
    assert "flor_12345678.png" in refs
    assert "viejo_no_usado_1.png" not in refs

    sin_uso = recursos_sin_uso(carp_rec, refs)
    nombres_sin_uso = [p.name for p in sin_uso]
    assert "flor_12345678.png" not in nombres_sin_uso
    assert "viejo_no_usado_1.png" in nombres_sin_uso
    assert "viejo_no_usado_2.svg" in nombres_sin_uso
    assert len(sin_uso) == 2

    # Ejecutar traslado a papelera
    papelera = mover_a_papelera(sin_uso, carp_rec, subdirectorio_fecha="20261016_120000")
    assert papelera.exists()
    assert (papelera / "viejo_no_usado_1.png").exists()
    assert (papelera / "viejo_no_usado_2.svg").exists()

    # El archivo en uso sigue intacto en la carpeta original
    assert img_usada.exists()
    # Los huérfanos ya no están en la raíz de recursos
    assert not (carp_rec / "viejo_no_usado_1.png").exists()
    assert not (carp_rec / "viejo_no_usado_2.svg").exists()

    # Reversibilidad: moverlos de vuelta restaura su estado
    import shutil
    shutil.move(str(papelera / "viejo_no_usado_1.png"), str(carp_rec / "viejo_no_usado_1.png"))
    assert (carp_rec / "viejo_no_usado_1.png").exists()


def test_limpieza_segura_respeta_otros_proyectos(tmp_path):
    """Archivos referenciados por otro proyecto guardado o en memoria NO se consideran sin uso."""
    carpeta_proyectos = tmp_path / "guardados"
    carpeta_proyectos.mkdir()
    carp_rec = carpeta_proyectos / "recursos_temp"
    carp_rec.mkdir()

    img_otro = carp_rec / "otro_proyecto_img.png"
    Image.new("RGB", (10, 10), "green").save(img_otro)

    # Otro proyecto en guardados/ que referencia esta imagen
    proy_otro = Proyecto(
        version=2,
        nombre="otro",
        entrada=BalloonInput(950, 30, 2, 1),
        condiciones=Condiciones(),
        disenos={"inferior": Diseno(seccion="inferior", capas=[
            CapaDiseno(id="c2", nombre="Otro", tipo="raster", archivo="otro_proyecto_img.png", ancho_natural=5.0, alto_natural=5.0)
        ])},
    )
    guardar_proyecto(proy_otro, str(carpeta_proyectos / "otro.json"))

    refs = obtener_archivos_referenciados_por_proyectos(carpeta_proyectos)
    assert "otro_proyecto_img.png" in refs

    sin_uso = recursos_sin_uso(carp_rec, refs)
    assert len(sin_uso) == 0

