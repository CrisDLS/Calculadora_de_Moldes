import os
import io
import pytest
from pathlib import Path
from PIL import Image
from logic.models import BalloonInput, Condiciones
from logic.diseno.lienzo import (
    CapaDiseno,
    Diseno,
    importar_recurso,
    MAX_RASTER_DIM,
    MAX_RASTER_BYTES,
    MAX_SVG_BYTES,
)
from logic.proyecto.modelo import (
    Proyecto,
    guardar_proyecto,
    cargar_proyecto,
    obtener_carpeta_recursos,
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
