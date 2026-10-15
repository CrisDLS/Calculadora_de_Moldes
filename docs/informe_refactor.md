# Informe de Refactor y Modularización

Este documento complementa el informe del refactor estructural realizado en la rama `flet-ui`.

---

## 1. Inventario de Archivos Eliminados

| Archivo o Carpeta Borrado | Evidencia de que no se usa | Decisión |
| :--- | :--- | :--- |
| `logic/gestor_archivos.py` | 0 importaciones en todo el código base (`git grep`). Reemplazado por `logic/proyecto/modelo.py` (`Proyecto.guardar` y `Proyecto.cargar`). | Borrado |
| `logic/utils.py` | Módulo residual de prototipo con 0 referencias en `app_flet/`, `logic/` y `tests/`. | Borrado |
| `recursos/guardados.png` | Icono PNG de la antigua interfaz CustomTkinter (preservada en etiqueta `ctk-final`). Flet usa iconos vectoriales (`ft.Icons.*`). | Borrado |
| `recursos/info.png` | Icono PNG de CustomTkinter, sin uso en Flet. | Borrado |
| `recursos/inicio.png` | Icono PNG de CustomTkinter, sin uso en Flet. | Borrado |
| `recursos/moldes.png` | Icono PNG de CustomTkinter, sin uso en Flet. | Borrado |
| `referencia/parche/` (`models.py`, `trompo_estrella.py`, `test_trompo_estrella.py`) | Copia temporal obsoleta de parcheado previa a la unificación. El oráculo validado es `referencia/trompo_estrella.py`. | Borrado |

---

## 2. Archivos "Dudosos" Conservados para Decisión del Usuario

Los siguientes archivos se identificaron como no requeridos directamente por la interfaz Flet en tiempo de ejecución, pero se conservaron intactos para decisión explícita del usuario:

1. `scripts/reporte_trompo_estrella.py`: Runner de consola por línea de comandos (CLI) con `argparse`. No es importado por Flet pero sirve para generar reportes en terminal sin levantar la UI.
2. `recursos/icono_globo.ico` y `recursos/icono_globo.png`: Icono de ventana y marca del ejecutable/distribución.
3. `guardados/`: Directorio donde el usuario almacena los archivos `.json` de sus proyectos.
4. `referencia/trompo_estrella.py` y `tests/test_regresion_referencia.py`: Oráculo de paridad matemática con el Excel (intocable según AGENTS.md).
5. `datos/colores_papel.json`: Catálogo de colores tradicionales de papel china.

---

## 3. Aspectos No Verificados Visualmente en Entorno Headless

Al ejecutarse las pruebas automatizadas en un entorno sin pantalla interactiva física (headless), se verificó el 100% de la lógica, el árbol de controles de Flet y las salidas hash SHA-256 de los SVGs. No obstante, no se pudo comprobar visualmente en pantalla:
- El renderizado gráfico final de Flutter en el monitor físico del usuario (rasterización de fuentes, antialiasing y renderizado exacto de sombras nativas).
- La latencia o sensación táctil del cursor del ratón durante eventos continuos de entrada en hardware real antes de las correcciones de la presente sesión.

---

## 4. Verificación de Invarianza de Instantáneas (Snapshots)

Salida de `git diff --stat bbe0315 HEAD -- tests/snapshots`:
```text
 tests/snapshots/generar_snapshots.py  | 9 +++------
 tests/snapshots/test_snapshots_svg.py | 4 +---
 tests/snapshots/test_snapshots_ui.py  | 1 -
 3 files changed, 4 insertions(+), 10 deletions(-)
```

### Explicación:
- Los archivos de datos `.json` que contienen las instantáneas del árbol de controles de la interfaz y `tests/snapshots/svg_hashes.json` tienen **CERO diferencias** (`git diff bbe0315 HEAD -- "tests/snapshots/*.json"` retorna vacío).
- Las únicas diferencias en los tres archivos `.py` corresponden a la limpieza de importaciones no utilizadas aplicada por Ruff (`style: limpiar importaciones y variables sin usar`), sin modificar ninguna aserción, lógica ni valor de prueba.
