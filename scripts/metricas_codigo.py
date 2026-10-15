#!/usr/bin/env python3
"""Script para medir métricas de código, funciones largas, archivos grandes,
duplicados potenciales e importaciones circulares usando AST.
"""
import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

DIRECTORIOS_ANALIZAR = ["app_flet", "logic", "presentacion", "referencia"]

def obtener_archivos_py(raiz: Path) -> List[Path]:
    archivos = []
    for dir_nombre in DIRECTORIOS_ANALIZAR:
        d = raiz / dir_nombre
        if d.exists() and d.is_dir():
            for p in d.rglob("*.py"):
                archivos.append(p)
    # Agregar archivos .py en la raíz
    for p in raiz.glob("*.py"):
        archivos.append(p)
    return sorted(archivos)

def analizar_archivo(ruta: Path):
    try:
        texto = ruta.read_text(encoding="utf-8")
    except Exception:
        return None
    
    lineas_totales = len(texto.splitlines())
    
    try:
        arbol = ast.parse(texto, filename=str(ruta))
    except SyntaxError:
        return None
    
    funciones = []
    imports = []
    
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            inicio = nodo.lineno
            fin = getattr(nodo, "end_lineno", inicio)
            tam = fin - inicio + 1
            funciones.append((nodo.name, inicio, fin, tam))
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                imports.append(nodo.module)
    
    return {
        "lineas": lineas_totales,
        "funciones": funciones,
        "imports": imports,
    }

def detectar_ciclos(grafo: Dict[str, Set[str]]) -> List[List[str]]:
    visitados = {}
    ciclos = []
    camino = []

    def dfs(nodo: str):
        visitados[nodo] = 1 # en proceso
        camino.append(nodo)
        for vecino in grafo.get(nodo, []):
            if visitados.get(vecino, 0) == 1:
                # Ciclo encontrado
                idx = camino.index(vecino)
                ciclo = camino[idx:] + [vecino]
                ciclos.append(ciclo)
            elif visitados.get(vecino, 0) == 0:
                dfs(vecino)
        camino.pop()
        visitados[nodo] = 2 # finalizado

    for nodo in list(grafo.keys()):
        if visitados.get(nodo, 0) == 0:
            dfs(nodo)

    return ciclos

def ruta_a_modulo(raiz: Path, ruta: Path) -> str:
    rel = ruta.relative_to(raiz).with_suffix("")
    partes = list(rel.parts)
    if partes[-1] == "__init__":
        partes.pop()
    return ".".join(partes)

def modulo_a_ruta(raiz: Path, mod: str) -> Path:
    partes = mod.split(".")
    p1 = raiz.joinpath(*partes).with_suffix(".py")
    if p1.exists():
        return p1
    p2 = raiz.joinpath(*partes) / "__init__.py"
    if p2.exists():
        return p2
    return None

def main():
    raiz = Path(__file__).resolve().parent.parent
    archivos = obtener_archivos_py(raiz)
    
    datos_archivos = {}
    funciones_por_nombre = defaultdict(list)
    grafo_deps = defaultdict(set)
    
    for arch in archivos:
        info = analizar_archivo(arch)
        if info:
            rel_str = str(arch.relative_to(raiz)).replace("\\", "/")
            datos_archivos[rel_str] = info
            
            for nombre_fn, inicio, fin, tam in info["funciones"]:
                funciones_por_nombre[nombre_fn].append((rel_str, inicio, tam))
            
            for imp in info["imports"]:
                coincidencias = []
                for arch_dest in archivos:
                    mod_dest = ruta_a_modulo(raiz, arch_dest)
                    if imp == mod_dest or imp.startswith(mod_dest + "."):
                        coincidencias.append((mod_dest, arch_dest))
                if coincidencias:
                    _, mejor_arch = max(coincidencias, key=lambda x: len(x[0]))
                    rel_dest = str(mejor_arch.relative_to(raiz)).replace("\\", "/")
                    if rel_str != rel_dest:
                        grafo_deps[rel_str].add(rel_dest)

    # Reporte
    lineas_reporte = []
    lineas_reporte.append("=" * 80)
    lineas_reporte.append("REPORTE DE MÉTRICAS DE CÓDIGO (LÍNEA BASE)")
    lineas_reporte.append("=" * 80)
    
    # 1. Archivos > 700 líneas
    archivos_grandes = [
        (rel, info["lineas"])
        for rel, info in datos_archivos.items()
        if info["lineas"] > 700
    ]
    archivos_grandes.sort(key=lambda x: x[1], reverse=True)
    
    lineas_reporte.append(f"\n1. ARCHIVOS QUE SUPERAN 700 LÍNEAS ({len(archivos_grandes)} encontrados):")
    lineas_reporte.append("-" * 80)
    for rel, lin in archivos_grandes:
        lineas_reporte.append(f"  {lin:5d} líneas : {rel}")
    
    # 2. Funciones > 90 líneas
    funciones_largas = []
    for rel, info in datos_archivos.items():
        for fn_nombre, inicio, fin, tam in info["funciones"]:
            if tam > 90:
                funciones_largas.append((tam, rel, fn_nombre, inicio, fin))
    funciones_largas.sort(key=lambda x: x[0], reverse=True)
    
    lineas_reporte.append(f"\n2. FUNCIONES / MÉTODOS QUE SUPERAN 90 LÍNEAS ({len(funciones_largas)} encontrados):")
    lineas_reporte.append("-" * 80)
    for tam, rel, fn_nombre, inicio, fin in funciones_largas:
        lineas_reporte.append(f"  {tam:4d} líneas : {rel}:{inicio} -> {fn_nombre}()")
    
    # 3. Funciones con el mismo nombre en varios módulos (candidatas a duplicado)
    duplicados = [
        (nombre, ocurrencias)
        for nombre, ocurrencias in funciones_por_nombre.items()
        if len(ocurrencias) > 1 and not nombre.startswith("__")
    ]
    duplicados.sort(key=lambda x: len(x[1]), reverse=True)
    
    lineas_reporte.append(f"\n3. NOMBRES DE FUNCIONES COMPARTIDOS EN VARIOS MÓDULOS ({len(duplicados)} casos):")
    lineas_reporte.append("-" * 80)
    for nombre, ocurs in duplicados[:40]: # Top 40
        modulos_str = ", ".join(f"{r} ({tam} lin)" for r, _, tam in ocurs)
        lineas_reporte.append(f"  - {nombre}() en {len(ocurs)} archivos: {modulos_str}")
    
    # 4. Importaciones circulares
    ciclos = detectar_ciclos(grafo_deps)
    lineas_reporte.append(f"\n4. IMPORTACIONES CIRCULARES ({len(ciclos)} ciclos encontrados):")
    lineas_reporte.append("-" * 80)
    if ciclos:
        for c in ciclos:
            lineas_reporte.append("  CICLO: " + " -> ".join(c))
    else:
        lineas_reporte.append("  Ninguna importación circular detectada.")
    
    # 5. Resumen general por archivo
    lineas_reporte.append("\n5. RESUMEN COMPLETO POR ARCHIVO (ORDENADO POR LÍNEAS):")
    lineas_reporte.append("-" * 80)
    resumen_archivos = sorted(datos_archivos.items(), key=lambda x: x[1]["lineas"], reverse=True)
    for rel, info in resumen_archivos:
        num_fns = len(info["funciones"])
        lineas_reporte.append(f"  {info['lineas']:5d} líneas | {num_fns:3d} funciones/métodos : {rel}")
        for fn_nombre, inicio, fin, tam in sorted(info["funciones"], key=lambda x: x[3], reverse=True)[:5]:
            if tam > 50:
                lineas_reporte.append(f"         * {fn_nombre}() : {tam} líneas (L{inicio}-L{fin})")
    
    reporte_final = "\n".join(lineas_reporte) + "\n"
    
    import sys
    docs_dir = raiz / "docs"
    docs_dir.mkdir(exist_ok=True)
    salida_nombre = sys.argv[1] if len(sys.argv) > 1 else ("metricas_despues.txt" if (docs_dir / "metricas_antes.txt").exists() else "metricas_antes.txt")
    salida_txt = docs_dir / salida_nombre
    salida_txt.write_text(reporte_final, encoding="utf-8")
    
    print(reporte_final)
    print(f"\nReporte guardado exitosamente en: {salida_txt}")

if __name__ == "__main__":
    main()
