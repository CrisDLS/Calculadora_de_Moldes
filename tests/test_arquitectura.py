"""
Pruebas de reglas de arquitectura, dependencias y límites de tamaño.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# Excepciones temporales justificadas de archivos > 700 líneas.
# El refactor modularizará app_flet/ y logic/ para vaciar estas listas.
EXCEPCIONES_ARCHIVOS: Dict[str, str] = {
    "app_flet/vistas/trompo.py": "Monolito original de vista UI; se dividirá en compositor y pestañas en Parte 4",
}

# Excepciones temporales justificadas de funciones > 90 líneas.
# En Parte 4 se eliminarán todas las de app_flet/, y en Parte 5 las de logic/exportacion.
EXCEPCIONES_FUNCIONES: Dict[Tuple[str, str], str] = {
    ("app_flet/vistas/trompo.py", "__init__"): "Constructor del monolito original con montaje completo de UI",
    ("app_flet/vistas/trompo.py", "_crear_tab_resumen"): "Construcción de controles de la pestaña resumen",
    ("app_flet/vistas/trompo.py", "_crear_tab_tablas"): "Construcción de controles de la pestaña tablas",
    ("app_flet/vistas/trompo.py", "_crear_tab_moldes"): "Construcción de controles de la pestaña moldes 2D",
    ("app_flet/vistas/trompo.py", "_crear_tab_hoja"): "Construcción de controles de la pestaña hoja de trazo",
    ("app_flet/vistas/trompo.py", "_crear_tab_vista_3d"): "Construcción de controles de la pestaña vista 3D",
    ("app_flet/vistas/trompo.py", "_crear_tab_diseno"): "Construcción de controles de la pestaña diseño",
    ("app_flet/vistas/trompo.py", "_actualizar_panel_capas_y_inspector"): "Inspector lateral de capas y propiedades en diseño",
    ("app_flet/vistas/trompo.py", "_sync_controlador_a_vista"): "Sincronización monolítica de estado UI",
    ("app_flet/vistas/trompo.py", "_exportar_hoja_diseno"): "Exportación de hoja de trazo decorada",
    ("logic/calculators/trompo_estrella.py", "calcular"): "Algoritmo central de cálculo de moldes del globo",
    ("logic/diseno/lienzo.py", "_validar_y_procesar_svg"): "Validación XML estricta y reescritura de prefijos en SVGs importados",
    ("logic/diseno/lienzo.py", "ajustar_capa"): "Cálculo de ajuste de capas a límites del abanico",
    ("logic/diseno/lienzo.py", "componer_svg_diseno"): "Composición de capas raster y vectoriales sobre abanico",
    ("logic/diseno/paleta.py", "importar_csv"): "Parser CSV de colores con detección de delimitadores y validación",
    ("logic/exportacion/escena3d.py", "escena_a_dict"): "Triangulación y empaquetado de mallas 3D para exportación",
    ("logic/exportacion/paquete.py", "generar_paquete"): "Generación del paquete completo de exportación SVG/HTML",
    ("logic/exportacion/svg_abanico.py", "svg_abanico"): "Generación de SVG del abanico completo y mitad",
    ("logic/exportacion/svg_diseno.py", "svg_gajo"): "Generación de SVG de gajo decorado con máscara y transformaciones",
    ("logic/exportacion/svg_moldes.py", "svg_pieza"): "Generación de SVG de pieza individual suelta",
    ("logic/exportacion/svg_moldes.py", "svg_conjunto"): "Generación de SVG de conjunto de moldes sueltos",
    ("logic/exportacion/svg_moldes.py", "svg_hoja"): "Generación de SVG de hoja de trazo con cotas",
    ("logic/exportacion/svg_perfil.py", "svg_perfil"): "Generación de SVG del perfil armado proyectado",
    ("logic/geometria/abanico.py", "abanico"): "Geometría analítica de despliegue de piezas a abanico",
    ("logic/geometria/abanico.py", "contorno_abanico"): "Cálculo analítico del contorno exterior del abanico",
    ("logic/geometria/malla_trompo.py", "construir_malla"): "Construcción geométrica 3D de vértices, anillos y caras",
    ("logic/geometria/perfil.py", "perfil_armado"): "Cálculo de silueta lateral rotada y cotas del perfil armado",
    ("logic/proyecto/modelo.py", "from_dict"): "Deserialización y migración versionada de proyecto desde JSON",
}


def _obtener_arbol_ast(ruta: Path) -> ast.AST:
    texto = ruta.read_text(encoding="utf-8")
    return ast.parse(texto, filename=str(ruta))


def _extraer_imports(arbol: ast.AST) -> List[str]:
    imports = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                imports.append(nodo.module)
    return imports


def test_reglas_dependencias_capas():
    """
    Verifica las reglas de aislamiento arquitectónico:
    - logic/ y presentacion/ NO importan flet ni app_flet.
    - logic/ NO importa presentacion.
    - app_flet/controlador* NO importa flet.
    """
    violaciones = []

    # 1. logic/
    for arch in (RAIZ / "logic").rglob("*.py"):
        arbol = _obtener_arbol_ast(arch)
        for imp in _extraer_imports(arbol):
            if imp == "flet" or imp.startswith("flet."):
                violaciones.append(f"{arch.name} importa flet ({imp})")
            if imp == "app_flet" or imp.startswith("app_flet."):
                violaciones.append(f"{arch.name} importa app_flet ({imp})")
            if imp == "presentacion" or imp.startswith("presentacion."):
                violaciones.append(f"{arch.name} importa presentacion ({imp})")

    # 2. presentacion/
    for arch in (RAIZ / "presentacion").rglob("*.py"):
        arbol = _obtener_arbol_ast(arch)
        for imp in _extraer_imports(arbol):
            if imp == "flet" or imp.startswith("flet."):
                violaciones.append(f"{arch.name} importa flet ({imp})")
            if imp == "app_flet" or imp.startswith("app_flet."):
                violaciones.append(f"{arch.name} importa app_flet ({imp})")

    # 3. app_flet/controlador*
    for arch in (RAIZ / "app_flet").rglob("*.py"):
        rel = str(arch.relative_to(RAIZ)).replace("\\", "/")
        if "controlador" in rel:
            arbol = _obtener_arbol_ast(arch)
            for imp in _extraer_imports(arbol):
                if imp == "flet" or imp.startswith("flet."):
                    violaciones.append(f"{rel} importa flet ({imp})")

    assert not violaciones, "Violaciones de reglas de arquitectura:\n" + "\n".join(violaciones)


def test_sin_importaciones_circulares_en_app_flet():
    """
    Verifica que no existan ciclos de importación entre módulos dentro de app_flet.
    """
    archivos = list((RAIZ / "app_flet").rglob("*.py"))
    modulo_a_ruta = {}
    grafo_deps: Dict[str, Set[str]] = {}

    for arch in archivos:
        rel = arch.relative_to(RAIZ).with_suffix("")
        partes = list(rel.parts)
        if partes[-1] == "__init__":
            partes = partes[:-1]
        mod_nombre = ".".join(partes)
        modulo_a_ruta[mod_nombre] = arch
        grafo_deps[mod_nombre] = set()

    for mod_nombre, arch in modulo_a_ruta.items():
        arbol = _obtener_arbol_ast(arch)
        for imp in _extraer_imports(arbol):
            coincidencias = [
                otro for otro in modulo_a_ruta
                if imp == otro or imp.startswith(otro + ".")
            ]
            if coincidencias:
                mejor = max(coincidencias, key=len)
                if mejor != mod_nombre:
                    grafo_deps[mod_nombre].add(mejor)

    # Detectar ciclos con DFS
    visitado: Set[str] = set()
    en_pila: Set[str] = set()
    ciclos = []

    def dfs(nodo: str, camino: List[str]):
        visitado.add(nodo)
        en_pila.add(nodo)
        camino.append(nodo)

        for vecino in grafo_deps.get(nodo, []):
            if vecino not in visitado:
                dfs(vecino, camino)
            elif vecino in en_pila:
                idx = camino.index(vecino)
                ciclos.append(" -> ".join(camino[idx:] + [vecino]))

        camino.pop()
        en_pila.remove(nodo)

    for mod in modulo_a_ruta:
        if mod not in visitado:
            dfs(mod, [])

    assert not ciclos, "Ciclos de importación detectados en app_flet:\n" + "\n".join(ciclos)


def test_limites_de_tamano_archivos_y_funciones():
    """
    Verifica que ningún archivo en logic/ o app_flet/ supere 700 líneas
    y ninguna función supere 90 líneas, salvo excepciones justificadas.
    """
    directorios = [RAIZ / "app_flet", RAIZ / "logic"]
    archivos_excesivos = []
    funciones_excesivas = []

    for d in directorios:
        for arch in d.rglob("*.py"):
            rel = str(arch.relative_to(RAIZ)).replace("\\", "/")
            texto = arch.read_text(encoding="utf-8")
            lineas = len(texto.splitlines())

            if lineas > 700:
                if rel not in EXCEPCIONES_ARCHIVOS:
                    archivos_excesivos.append(f"{rel} tiene {lineas} líneas (límite 700)")

            arbol = ast.parse(texto, filename=str(arch))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(nodo, "end_lineno") and hasattr(nodo, "lineno"):
                        tam = nodo.end_lineno - nodo.lineno + 1
                        if tam > 90:
                            clave = (rel, nodo.name)
                            if clave not in EXCEPCIONES_FUNCIONES:
                                funciones_excesivas.append(f"{rel}::{nodo.name} tiene {tam} líneas (límite 90)")

    errores = []
    if archivos_excesivos:
        errores.append("Archivos que superan 700 líneas sin justificación:\n" + "\n".join(archivos_excesivos))
    if funciones_excesivas:
        errores.append("Funciones que superan 90 líneas sin justificación:\n" + "\n".join(funciones_excesivas))

    assert not errores, "\n\n".join(errores)
