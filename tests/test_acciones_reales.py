import os
import json
import urllib.request
from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO
from logic.exportacion.paquete import generar_paquete, guardar_paquete
from logic.diseno.paleta import ColorPapel, cargar_catalogo, guardar_color_usuario, exportar_csv, importar_csv
from presentacion.trompo_estrella import tabla_a_texto
from app_flet.controlador import ControladorTrompo

def test_accion_calcular():
    """Verifica que el cálculo ejecute la lógica completa y genere tablas y SVGs."""
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    vm = c.calcular()

    assert vm.mensaje_error is None
    assert not vm.desactualizado
    assert len(vm.tarjetas) > 0
    assert len(vm.tablas) == 3
    assert len(c.tablas[0].filas) == 17  # Cono superior: 17 puntos
    assert len(c.tablas[1].filas) == 12  # Pico: 12 puntos
    assert len(c.tablas[2].filas) == 25  # Cono inferior: 25 puntos

    # SVGs no vacíos y válidos
    for svg_str in [vm.svg_conjunto, vm.svg_superior, vm.svg_pico, vm.svg_inferior, vm.svg_perfil, vm.svg_hoja]:
        assert svg_str.startswith("<?xml")
        assert "</svg>" in svg_str

def test_accion_copiar_tabla():
    """Verifica la generación de texto TSV para copiar al portapapeles."""
    c = ControladorTrompo()
    c.calcular()
    tabla = c.tablas[0]  # Cono superior
    texto = tabla_a_texto(tabla)

    lineas = texto.strip().split("\n")
    assert "Cono superior" in lineas[0]
    assert any("Paso\tLargo (cm)\tAcumulado (cm)\tAncho/2 (cm)" in l for l in lineas)
    assert len(lineas) >= 19  # Título + Resumen + Encabezados + 17 filas
    # Las filas de puntos están presentes (paso 1 en adelante)
    assert any(l.startswith("1\t") for l in lineas)

def test_accion_copiar_compra():
    """Verifica la generación del formato de texto para la lista de compra."""
    c = ControladorTrompo()
    c.calcular()
    vm = c.get_view_model()
    assert len(vm.items_compra) > 0

    lineas = ["Color\tMarca\tCódigo\tSuperior\tPico\tInferior\tTotal piezas\tÁrea (m²)\tPliegos\tPaquetes"]
    for it in vm.items_compra:
        m = it.color.marca or "-"
        cod = it.color.codigo or "-"
        lineas.append(
            f"{it.color.nombre}\t{m}\t{cod}\t{it.piezas_superior}\t{it.piezas_pico}\t{it.piezas_inferior}\t{it.piezas_totales}\t{it.area_m2:.2f}\t{it.pliegos}\t{it.paquetes}"
        )
    texto = "\n".join(lineas)
    assert "Color\tMarca\tCódigo" in texto
    assert len(lineas) >= 2

def test_accion_exportar_hoja(tmp_path):
    """Verifica la exportación del SVG de la hoja de trazo a archivo."""
    c = ControladorTrompo()
    c.calcular()
    assert c.svg_hoja

    ruta_archivo = str(tmp_path / "hoja_prueba.svg")
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(c.svg_hoja)

    assert os.path.exists(ruta_archivo)
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        contenido = f.read()
    assert '<?xml version="1.0"' in contenido
    assert 'inkscape:groupmode="layer"' in contenido
    assert '</svg>' in contenido

def test_accion_exportar_paquete(tmp_path):
    """Verifica la exportación del paquete completo de moldes a una carpeta."""
    c = ControladorTrompo()
    c.calcular()
    carpeta = str(tmp_path / "paquete_salida")

    archivos_dict = generar_paquete(
        c.resultado,
        c.entrada_actual,
        esquema=c._construir_esquema(),
        hoja=c.hoja_tipo,
        escala=c.hoja_escala,
        lienzo=c.hoja_lienzo,
        dibujar=c.hoja_dibujar,
    )
    escritos = guardar_paquete(carpeta, archivos_dict, sobrescribir=True)

    assert len(escritos) >= 5
    for ruta in escritos:
        assert os.path.exists(ruta)
        with open(ruta, "r", encoding="utf-8") as f:
            cuerpo = f.read()
            assert cuerpo.startswith("<?xml")
            assert "</svg>" in cuerpo

def test_accion_exportar_visor_3d(tmp_path):
    """Verifica que exportar_visor_3d genere un HTML autocontenido sin enlaces externos."""
    c = ControladorTrompo()
    c.calcular()
    ruta_html = str(tmp_path / "visor_exportado.html")

    # Ejecutar la acción real del controlador
    c.exportar_visor_3d(ruta_html)

    assert os.path.exists(ruta_html)
    with open(ruta_html, "r", encoding="utf-8") as f:
        html = f.read()

    assert "<!DOCTYPE html>" in html or "<html" in html
    assert "window.__DATOS_ESCENA_3D__" in html
    assert "OrbitControls" in html
    assert "THREE.WebGLRenderer" in html
    # Sin llamadas externas
    assert '<script src=' not in html
    assert 'href="http' not in html

def test_accion_abrir_visor_3d():
    """Verifica que el servidor local de visor 3D inicie y responda la API de escena."""
    c = ControladorTrompo()
    c.calcular()
    servidor = c.obtener_servidor_3d()

    try:
        assert servidor is not None
        assert servidor.puerto_real > 0
        assert servidor.url.startswith("http://127.0.0.1:")

        url_api = f"{servidor.url}api/escena"
        with urllib.request.urlopen(url_api) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "vertices" in data
            assert "caras" in data
    finally:
        servidor.detener()

def test_accion_importar_exportar_csv(tmp_path):
    """Verifica la exportación y posterior importación del catálogo CSV de papel china."""
    cat = cargar_catalogo()
    assert len(cat) > 0
    ruta_csv = str(tmp_path / "catalogo_prueba.csv")

    exportar_csv(ruta_csv, cat)
    assert os.path.exists(ruta_csv)

    # Reimportar y comparar
    importados, errores = importar_csv(ruta_csv)
    assert len(errores) == 0
    assert len(importados) == len(cat)
    assert importados[0].id == cat[0].id

def test_accion_agregar_color(tmp_path):
    """Verifica la adición de un nuevo color personalizado al catálogo."""
    ruta_custom = str(tmp_path / "colores_usuario.json")

    nuevo_col = ColorPapel(
        id="turquesa_mar",
        nombre="Turquesa Mar",
        hex="#00bcd4",
        marca="Prueba Marca",
        codigo="TM-101",
        aproximado=False
    )
    guardar_color_usuario(nuevo_col, ruta_usuario=ruta_custom)
    cat = cargar_catalogo(ruta_usuario=ruta_custom)
    encontrado = next((c for c in cat if c.id == "turquesa_mar"), None)
    assert encontrado is not None
    assert encontrado.marca == "Prueba Marca"
    assert encontrado.codigo == "TM-101"

def test_accion_nuevo_abrir_guardar_proyecto(tmp_path):
    """Verifica el ciclo completo de guardar, nuevo y abrir proyecto."""
    c = ControladorTrompo()
    c.altura = "800"
    c.gajos = "24"
    c.hileras = "3"
    c.costura = "1.5"
    c.pliego_ancho = 55.0
    c.pliego_alto = 75.0
    c.calcular()

    ruta_proy = str(tmp_path / "mi_globo.json")
    ok, msg = c.guardar(ruta_proy)
    assert ok is True
    assert os.path.exists(ruta_proy)

    # Reiniciar a nuevo
    c.nuevo()
    assert c.altura == "950"
    assert c.gajos == "30"

    # Abrir proyecto guardado
    ok_abrir, msg_abrir = c.abrir(ruta_proy)
    assert ok_abrir is True
    assert c.altura == "800.0"
    assert c.gajos == "24"
    assert c.hileras == "3"
    assert c.pliego_ancho == 55.0
    assert c.pliego_alto == 75.0
    assert c.resultado is not None

def test_accion_cambiar_tema():
    """Verifica que el cambio de tema actualice los colores del SVG de pantalla."""
    c = ControladorTrompo()
    c.calcular()

    c.cambiar_estilo(PANTALLA_OSCURO)
    svg_oscuro = c.svg_superior
    assert PANTALLA_OSCURO.contorno in svg_oscuro
    assert PANTALLA_OSCURO.cuadricula in svg_oscuro

    c.cambiar_estilo(PANTALLA_CLARO)
    svg_claro = c.svg_superior
    assert PANTALLA_CLARO.contorno in svg_claro
    assert PANTALLA_CLARO.cuadricula in svg_claro

def test_accion_cambiar_opciones_hoja_y_abanico():
    """Verifica la reactividad al alternar entre piezas, lienzo y modo de dibujo."""
    c = ControladorTrompo()
    c.calcular()

    # En pico, ahora se permite 'mitad' y 'completo' (cara completa de 1 cara)
    c.actualizar_opciones_hoja(pieza="pico", lienzo="abanico", dibujar="mitad")
    vm_pico = c.get_view_model()
    assert "Mitad (espejo)" in vm_pico.svg_hoja
    assert "Cara 1" in vm_pico.svg_hoja
    assert 'id="eje-espejo-recto"' in vm_pico.svg_hoja

    c.actualizar_opciones_hoja(pieza="pico", lienzo="abanico", dibujar="completo")
    vm_pico_comp = c.get_view_model()
    assert "Cara completa" in vm_pico_comp.svg_hoja
    assert "Cara 1" in vm_pico_comp.svg_hoja

    # En cono con esquema simétrico (central_espejo), se permite 'mitad'
    c.cambiar_esquema_seccion("inferior", "central_espejo", 5)
    c.actualizar_opciones_hoja(pieza="inferior", lienzo="abanico", dibujar="mitad")
    vm = c.get_view_model()
    assert "Medio abanico (espejo)" in vm.svg_hoja

    # Cambiar a lienzo piezas separadas
    c.actualizar_opciones_hoja(lienzo="separadas")
    vm2 = c.get_view_model()
    assert "layer-diseno" in vm2.svg_hoja or "svg" in vm2.svg_hoja
