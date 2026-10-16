# Informe del Estado del Proyecto: Calculadora de Moldes "Trompo Estrella"

## Resumen Ejecutivo
1. La lógica de cálculo actual (`logic/calculators/trompo_estrella.py`) difiere radicalmente de la fuente de verdad (`referencia/trompo_estrella.py` y Excel), distorsionando generatrices, boca y cortes.
2. La interfaz gráfica en CustomTkinter (`ui/modulos_moldes/vista_trompo_estrella.py`) es puramente una maqueta visual sin conexión alguna con la lógica de negocio ni persistencia.
3. El proyecto carece de una suite de pruebas automatizadas formal (pytest); el único script de prueba existente falla al ejecutarse en consolas de Windows estándar debido a un error de codificación Unicode.
4. Existen inconsistencias estructurales en el repositorio (archivos duplicados como `sidebar_2.py`, imports tipo comodín `*`, errores tipográficos como `requiremets.txt` y caracteres no ASCII en nombres de archivo).
5. La sustitución de la calculadora vieja por la de referencia tiene impacto cero en la UI actual (al no estar acoplada), lo que permite refactorizar y blindar la capa `logic/` con pruebas unitarias antes de conectar la interfaz.

---

## 1. Estructura Real del Repositorio vs AGENTS.md

### Árbol de Directorios y Archivos Detectado

```text
Mi proyecto Globos/
│
├── .venv/                              # Entorno virtual Python 3.13
├── configuracion/
│   ├── __init__.py
│   └── constantes.py                   # Paleta de colores y tipografías
├── guardados/                          # Directorio de persistencia JSON (actualmente vacío)
├── logic/
│   ├── __init__.py
│   ├── gestor_archivos.py              # Clase GestorArchivos para guardar/cargar JSON
│   ├── interfaces.py                   # BalloonCalculator (ABC)
│   ├── models.py                       # BalloonInput, Point2D, SectionResult, BalloonCalculationResult
│   ├── utils.py                        # Funciones matemáticas puras (hipotenusa, ancho gajo)
│   └── calculators/
│       ├── __init__.py
│       └── trompo_estrella.py          # CALCULADORA VIEJA (a reemplazar)
├── recursos/
│   ├── GloboTE.ico / GloboTE.png
│   ├── guardados.png / info.png / inicio.png / moldes.png
│   └── trompoglobo.ico
├── referencia/
│   └── trompo_estrella.py              # FUENTE DE VERDAD (lógica validada v2)
├── ui/
│   ├── __init__.py
│   ├── vista_diseñar.py                # Nombre con 'ñ'
│   ├── vista_guardados.py
│   ├── vista_info.py
│   ├── vista_inicio.py
│   ├── vista_moldes.py
│   └── modulos_moldes/
│       ├── __init__.py
│       └── vista_trompo_estrella.py    # Maqueta UI de Trompo Estrella
├── utils/
│   └── gestor_image.py                 # Gestor de imágenes (clase GestorImagenes)
├── widgets/
│   ├── __init__.py
│   ├── sidebar.py                      # Versión antigua de sidebar (no usada por main.py)
│   └── sidebar_2.py                    # Versión activa de sidebar
├── AGENTS.md                           # Especificaciones y reglas de arquitectura
├── main.py                             # Aplicación principal CustomTkinter
├── requiremets.txt                     # Error tipográfico en el nombre
└── Script de Pruebas.py                # Script de prueba manual (espacios en el nombre)
```

### Comparación con AGENTS.md y Anomalías Encontradas

1. **Discrepancia en la ubicación de la calculadora vieja**:
   - `AGENTS.md` describe la arquitectura directa en `logic/` (`interfaces.py`, `models.py`, `utils.py`), pero la implementación de la calculadora vieja reside en una subcarpeta: `logic/calculators/trompo_estrella.py`.
   - `logic/gestor_archivos.py` existe en el disco pero no está documentado en `AGENTS.md`.
2. **Archivos mal nombrados (typos, espacios y caracteres especiales)**:
   - `requiremets.txt`: Le falta la letra `n` (debe ser `requirements.txt`).
   - `Script de Pruebas.py`: Contiene espacios en el nombre, lo cual dificulta la ejecución automatizada y contraviene las convenciones de nomenclatura de módulos Python (`PEP 8`).
   - `ui/vista_diseñar.py`: Contiene la letra `ñ`. Puede causar problemas de codificación en herramientas de empaquetado (PyInstaller), git en diferentes sistemas operativos o linters.
   - `utils/gestor_image.py`: Nombre híbrido en inglés/español. La clase interna se llama `GestorImagenes` y el encabezado del archivo declara `# utils/gestor_imagenes.py`.
3. **Archivos redundantes o huérfanos**:
   - `widgets/sidebar.py` vs `widgets/sidebar_2.py`: `main.py` importa exclusivamente `widgets.sidebar_2.Sidebar`. El archivo `widgets/sidebar.py` quedó huérfano como versión preliminar obsoleta.
   - En `__pycache__` existen archivos de caché compilados correspondientes a módulos eliminados o renombrados previamente (`home_view.cpython-313.pyc`, `image.cpython-313.pyc`, `placeholder.cpython-313.pyc`).
4. **Imports tipo comodín (`from ... import *`)**:
   - Detectados 9 archivos que realizan `from configuracion.constantes import *`:
     - `main.py`
     - `ui/vista_diseñar.py`
     - `ui/vista_guardados.py`
     - `ui/vista_info.py`
     - `ui/vista_inicio.py`
     - `ui/vista_moldes.py`
     - `ui/modulos_moldes/vista_trompo_estrella.py`
     - `widgets/sidebar.py`
     - `widgets/sidebar_2.py`
   - Esto oculta el origen de los símbolos y puede generar colisiones de nombres inadvertidas.
5. **Errores ortográficos en textos de interfaz**:
   - `ui/vista_inicio.py` (L15): `"¡Crea tu Globo de Catonlla\nPerfecto!"` (dice *Catonlla* en vez de *Cantoya*).
   - `widgets/sidebar.py` (L34, L40): `"Mas\nInfomacion"` y `"Mas\ninfromación"`.

---

## 2. Comparación de Fórmulas: Calculadora Vieja vs Referencia

| Concepto | Versión Vieja (`logic/calculators/trompo_estrella.py`) | Versión de Referencia (`referencia/trompo_estrella.py`) | Impacto Técnico y Práctico |
| :--- | :--- | :--- | :--- |
| **Significado de `altura`** | Se asume como altura vertical del cuerpo ($h_{base}$). Luego suma picos para una `altura_total_real = h_base + h_picos`. | Largo **TOTAL** de papel sobre la superficie del gajo: $L_{total} = L_{sup} + L_{picos} + L_{inf}$. | **CRÍTICO**. La vieja calcula hipotenusas sobre dimensiones axiales infladas. Para altura 950 cm, la vieja genera más de 1180 cm de papel total. La referencia respeta exactamente los 950 cm de papel cortado. |
| **Porcentaje Cono Superior** | $0.42 \times h_{base}$ (calculado sobre la altura vertical antes de hipotenusa). | $0.43 \times restante$, donde $restante = altura - largo\_picos$. | En la referencia se descuenta primero el papel que consumen los picos. En la vieja no se descuenta y se usa el factor 0.42 en vez de 0.43. Para 950 cm: Cono sup mide **353.74 cm** (ref) vs **501.61 cm** (vieja). Error de +147.87 cm. |
| **Porcentaje Cono Inferior** | $0.58 \times h_{base}$ (calculado sobre altura vertical antes de hipotenusa). | $0.57 \times restante$, donde $restante = altura - largo\_picos$. | Factor 0.57 aplicado sobre tela restante. Para 950 cm: Cono inf mide **468.92 cm** (ref) vs **604.14 cm** (vieja). Error de +135.22 cm. |
| **Uso de Generatriz / Hipotenusa** | Calcula el largo de papel mediante hipotenusa: $\sqrt{h^2 + r^2}$. | **No usa hipotenusa** para obtener los largos de corte: los largos $L_{sup}$ e $L_{inf}$ YA son las medidas de papel. La hipotenusa inversa solo se usa para proyectar la altura armada vertical: $h_{sup} = \sqrt{L_{sup}^2 - r^2}$. | Inversión del modelo conceptual. La vieja parte de dimensiones espaciales imaginarias; la referencia parte del pliego de papel real en la mesa de trabajo. |
| **Boca / Boquilla** | Escala fija: $0.185 \times ancho\_gajo$. Para 950/30 gajos: $\varnothing 11.78\text{ cm}$. No configurable. | $0.11 \times altura$ por defecto ($\varnothing 104.5\text{ cm}$ para 950 cm). Configurable por el usuario. | **PELIGRO DE INCENDIO**. Una boca de 11.8 cm en un globo de 9.5 m concentra el fuego y quema el globo al instante. La boca real del Excel es de 104.5 cm (aro de 328 cm). |
| **Picos (Geometría y Deducción)** | Triángulo con altura $= 1.20 \times ancho\_gajo$. No descuenta papel de la altura restante. | Altura $= 1.20 \times ancho\_gajo$. Cada hilera descuenta $1.0 \times ancho\_gajo$ de la longitud total de papel disponible. | Si el usuario pide 2 hileras de picos, la referencia aparta $127.34\text{ cm}$ de papel antes de cortar los conos. La vieja superpone picos sobre los conos sin ajustar el largo total. |
| **Intervalos y Puntos** | Pasos: 17 (sup), 12 (pico), 25 (inf). Pero en paso 1 asigna `delta_l` al incremento individual. | Intervalos: 16 (sup), 11 (pico), 24 (inf). Puntos totales: 17, 12, 25. En paso 1: `largo=0.0`, `acumulado=0.0`. | La referencia produce tablas idénticas al Excel del taller (paso 1 es el origen $0.0$, el avance inicia en paso 2). |
| **Pestaña de Boca** | **Inexistente**. No contemplada en ningún cálculo. | Pestaña extra de **4.0 cm** (configurable) después del paso 1 en el cono inferior. | Sin pestaña, el fabricante no tiene margen de papel para doblar y asegurar el aro de alambre inferior. |
| **Orden del Cono Inferior** | De ancho máximo ($ancho/2$) a boca ($boca/2$). | **De boca ($boca/2$) a ancho máximo ($ancho/2$)**. | El orden de la vieja obliga al usuario a leer la tabla al revés; la referencia inicia en el aro de la boca (paso 1 con pestaña) y sube hacia el ecuador del globo. |
| **Física de Vuelo y Empuje** | **Inexistente**. No calcula volumen, empuje ni pesos. | Calcula volumen ($100.5\text{ m}^3$), empuje ($14.4\text{ kg}$), masa papel ($2.5\text{ kg}$), peso aro/varillas ($133\text{ g}$), carga libre y neta ($11.8\text{ kg}$). | La vieja no advierte si el globo puede despegar. La referencia calcula la capacidad de carga real para combustible. |
| **Consumo de Papel (Pliegos)** | **Inexistente**. | Calcula área total ($103.9\text{ m}^2$) y pliegos aproximados ($319$ pliegos de $50 \times 75\text{ cm}$ con $+15\%$ desperdicio). | Permite al artesano presupuestar y comprar el papel exacto antes de cortar. |
| **Validación y Viabilidad** | Ninguna. Acepta cualquier combinación de valores sin validar. | Chequea viabilidad: holgura mecha $\ge 10\text{ cm}$, ancho gajo $\le 70\text{ cm}$, carga libre $> 0$, carga neta $> 0$, cono superior viable ($L_{sup} > r$). | La referencia emite lista estructurada de `avisos` (`OK`, `AVISO`, `ERROR`) y booleano `viable`. |

---

## 3. Modelos e Interfaz (`logic/models.py` y `logic/interfaces.py`)

### Estado Actual en `logic/models.py`
Actualmente define:
- `BalloonInput(altura_cuerpo, num_gajos, num_hileras_picos, ancho_costura)`
- `Point2D(paso_numero, largo_segmento, largo_acumulado, ancho_medio)`
- `SectionResult(nombre, puntos, altura_vertical, generatriz_total, radio_inicio, radio_fin)`
- `BalloonCalculationResult(...)`

### Deficiencias y Campos Faltantes

1. **En `BalloonInput`**:
   - `altura_cuerpo`: Cambia semánticamente a `altura` (largo total de papel extendido). Se recomienda mantener `altura` como campo principal y permitir `altura_cuerpo` como alias retrocompatible.
   - Faltan parámetros clave de la referencia:
     - `diametro_boca: Optional[float] = None` (None $\rightarrow 0.11 \times altura$).
     - `pestana_boca: float = 4.0` (cm extra en la boca).
     - `diametro_mecha: Optional[float] = None` (None $\rightarrow 0.50 \times boca$).
     - `masa_mecha_g: Optional[float] = None` (peso real mecha + parafina).
     - `alambre_mm: float = 2.0` (calibre del alambre de estructura).
     - `varillas: int = 4` (varillas cruzadas de soporte).
     - `altura_llama: float = 40.0` (cm sobre la boca).
     - `holgura_min: float = 10.0` (distancia mínima de seguridad mecha-papel).

2. **En `SectionResult` / `Pieza`**:
   - Falta el atributo `pestana: float = 0.0` (para registrar los 4 cm de pestaña del cono inferior).
   - Falta el método o propiedad `area: float` para calcular metros cuadrados de la pieza.
   - Los campos `radio_inicio`, `radio_fin` de la clase vieja eran radios axiales tridimensionales; en la referencia se usan `ancho_mitad_inicio` y `ancho_mitad_fin` (semianchos reales en el papel).
   - En `Point2D`: `paso_numero`, `largo_segmento`, `largo_acumulado`, `ancho_medio` coinciden en concepto con `Punto` de la referencia (`paso`, `largo`, `acumulado`, `ancho_mitad`). Conviene añadir propiedades/aliases para compatibilidad.

3. **En `BalloonCalculationResult`**:
   - Faltan los objetos y campos de física y diagnóstico:
     - `boca`: Objeto o dataclass con diámetro, circunferencia del aro, ancho de boca por gajo, pestaña, holgura de mecha, radio de pared a la llama y viabilidad de holgura.
     - `vuelo`: Objeto o dataclass con volumen ($m^3$), empuje ($g$), masa de papel ($g$), carga libre ($g$), masa de estructura ($g$), carga neta para combustible ($g$) y número de pliegos.
     - `gajos_min_70cm: int` y `gajos_min_50cm: int` (recomendación según tamaño comercial de pliego).
     - `altura_armada_estimada: float` (reemplaza a la errónea `altura_total_real`).
     - `area_total_m2: float`.
     - `avisos: List[str]` (diagnósticos explicativos).
     - `viable: bool` (indicador booleano global de seguridad y viabilidad).

4. **En `logic/interfaces.py`**:
   - `BalloonCalculator` define `calcular(self, entrada: BalloonInput) -> BalloonCalculationResult`.
   - La firma abstracta es limpia y adecuada. Solo requiere que los modelos enriquecidos mantengan compatibilidad.

---

## 4. Dependencias y Análisis de Impacto

### Búsqueda de Usos en todo el Proyecto

| Clase / Símbolo | Dónde se define | Dónde se importa / usa | ¿Está en la UI? |
| :--- | :--- | :--- | :--- |
| `TrompoEstrellaCalculator` | `logic/calculators/trompo_estrella.py` | Únicamente en `Script de Pruebas.py` (L2, L26). | **NO** |
| `BalloonInput` | `logic/models.py` | `logic/interfaces.py`, `logic/calculators/trompo_estrella.py`, `Script de Pruebas.py`. | **NO** |
| `BalloonCalculationResult`| `logic/models.py` | `logic/interfaces.py`, `logic/calculators/trompo_estrella.py`. | **NO** |
| `SectionResult` | `logic/models.py` | `logic/calculators/trompo_estrella.py`. | **NO** |

### Consecuencia Directa
- **La interfaz de usuario (`ui/modulos_moldes/vista_trompo_estrella.py`) NO importa ni utiliza ninguna clase de `logic/`**.
- Al reemplazar `TrompoEstrellaCalculator` por la lógica de referencia, **NADA en la interfaz gráfica se romperá**, porque la interfaz actualmente es una maqueta aislada.
- El único consumidor externo es `Script de Pruebas.py`.

---

## 5. Estado de la UI (`vista_trompo_estrella.py` y `main.py`)

### Diagnóstico de Conexión vs Maqueta

| Elemento UI | Estado Actual | Detalle Técnico |
| :--- | :--- | :--- |
| **Botón "Calcular"** | **Desconectado** | Se instancia como `ctk.CTkButton` sin el parámetro `command`. No ejecuta ninguna función ni valida datos. |
| **Campos de Entrada** | **Incompletos / Sin lectura** | Existen 4 inputs (`entry_altura`, `entry_gajos`, `entry_costura`, `entry_hileras`). Nunca se llama a `.get()`. Faltan campos para boca, mecha y pestaña. |
| **Tabla Resumen** | **Estática** | Genera 4 filas con texto `"-"` fijo. No guarda variables ni referencias a los labels para actualizarlos dinámicamente. |
| **Tablas Detalladas** | **Falsas (Mockup)** | Hardcodea un bucle `range(1, 11)` mostrando únicamente 10 filas vacías con números del 1 al 10. |
| **Avisos de Viabilidad** | **Inexistente** | No hay ningún contenedor, badge o banner para mostrar si el globo es viable, advertencias de holgura o errores físicos. |
| **Caja de Gráfica** | **Maqueta estática** | Un frame morado con un label `Graficacion de medidas`. No tiene lienzo `Canvas` ni integración de renderizado. |
| **Botón "Guardar Medidas"** | **Sin implementar** | Su comando apunta a `self.evento_guardar_medidas`, que únicamente ejecuta `print("Guardando...")`. |

### Requisitos para Tablas Dinámicas, Avisos y Gráfica
1. **Tablas Dinámicas (17, 12 y 25 filas)**:
   - Crear un componente o función que borre las filas previas del frame y reconstruya los renglones iterando sobre la lista de puntos (`len(puntos)` exacto: 17 para Superior, 12 para Pico, 25 para Inferior).
   - Añadir soporte visual para la fila o pie de página con la **pestaña de 4 cm** en el cono inferior.
2. **Panel de Viabilidad y Vuelo**:
   - Diseñar una sección de alertas con código de colores (verde para `OK`, amarillo para `AVISO`, rojo para `ERROR`).
   - Mostrar métricas de vuelo calculadas: volumen, empuje total, carga libre disponible para combustible y cantidad de pliegos china estimados.
3. **Graficación**:
   - Implementar un widget de visualización 2D (bien mediante `tkinter.Canvas` nativo dibujando el polígono de cada molde o con `matplotlib`).
4. **Persistencia**:
   - Conectar el botón de guardado a `GestorArchivos.guardar_globo` serializando las medidas y resultados en `guardados/<nombre>.json`.

---

## 6. Diagnóstico de Pruebas

### Evaluación de `Script de Pruebas.py`
- Al ejecutar directamente con Python en Windows:
  ```powershell
  .venv\Scripts\python.exe "Script de Pruebas.py"
  ```
  **Resultado: FALLO CRÍTICO CON CRASH**.
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f31f' in position 1: character maps to <undefined>
  ```
  Ocurre en la línea 30: `print(" 🌟 CALCULADORA TROMPO ESTRELLA - REPORTE FINAL")`. El intérprete intenta imprimir el emoji `🌟` en la consola de Windows (CP1252/cp850), provocando la terminación inmediata del proceso.
- Al forzar codificación UTF-8 en el entorno (`PYTHONIOENCODING=utf-8`):
  El script corre, pero reporta los valores viejos e incorrectos (Cono superior: 501.61 cm en vez de 353.74 cm; Cono inferior: 604.14 cm en vez de 468.92 cm; Boquilla: 11.78 cm en vez de 104.5 cm).
- **Cobertura**: 0% de aserciones automatizadas. Es un script de inspección visual humana, no una prueba unitaria de software.

### Pruebas Existentes en el Repositorio
- No existe suite de pruebas automatizadas con `pytest` o `unittest`.
- Faltan pruebas de regresión contra los valores canónicos del Excel estipulados en `AGENTS.md`.

---

## 7. Matriz de Riesgos Ordenados por Gravedad

| Nivel | Riesgo | Causa Raíz | Impacto Potencial | Mitigación |
| :---: | :--- | :--- | :--- | :--- |
| **CRÍTICO** | **Fabricación de moldes defectuosos y riesgo de incendio** | Fórmulas viejas en `logic/calculators/trompo_estrella.py` (boquilla de 11.8 cm en vez de 104.5 cm, generatrices disparadas en +140 cm). | Pérdida de material para el artesano, globo incapaz de elevarse o incendio en la boca por llama atrapada sin holgura. | Sustituir de inmediato la clase vieja por el algoritmo validado de `referencia/trompo_estrella.py`. |
| **ALTO** | **Inoperatividad total de la aplicación para el usuario final** | `ui/modulos_moldes/vista_trompo_estrella.py` no está conectada a la lógica; botón Calcular inerte. | El usuario percibe la aplicación como rota o congelada al no recibir respuesta. | Implementar el manejador de eventos del botón Calcular y el enlace con `logic/`. |
| **MEDIO** | **Falta de red de seguridad contra regresiones** | Ausencia de suite de pruebas con `pytest`. El script manual crashea por codificación de caracteres. | Futuras modificaciones podrían alterar sutilmente las proporciones sin ser detectadas. | Crear suite de pruebas unitarias (`tests/test_trompo_estrella.py`) con los valores canónicos de `AGENTS.md`. |
| **MEDIO** | **Incompatibilidades en plataformas y despliegue** | Archivos con caracteres especiales (`vista_diseñar.py`), espacios (`Script de Pruebas.py`) y typos (`requiremets.txt`). | Fallos en empaquetado (.exe con PyInstaller), problemas en pipelines CI/CD o en sistemas Linux/macOS. | Normalizar nombres de archivo a estándar PEP 8 en minúsculas y sin acentos ni eñes. |
| **BAJO** | **Código muerto y deuda técnica visual** | `widgets/sidebar.py` en desuso frente a `sidebar_2.py`, imports con comodín `*`. | Confusión para mantenedores del código y riesgo de colisión de variables globales. | Limpiar archivos obsoletos y convertir imports comodín en imports específicos. |

---

## 8. Plan de Pasos Pequeños (Commits Atómicos)

Cada paso es un commit independiente, seguro y verificable:

### Paso 1: Configuración de dependencias y suite de tests de regresión inicial
- **Archivos que toca**:
  - Renombrar `requiremets.txt` $\rightarrow$ `requirements.txt` y agregar `pytest`.
  - Crear carpeta `tests/` y archivo `tests/test_regresion_referencia.py`.
- **Descripción**: Escribir un test unitario formal que ejecute la lógica de `referencia/trompo_estrella.py` con el caso de prueba canónico (950 cm, 30 gajos, 2 hileras, 1 cm) y verifique con `assert math.isclose(...)`:
  - Ancho de gajo: $63.6696\text{ cm}$
  - Cono superior: largo $353.7441\text{ cm}$, salto $22.1090\text{ cm}$, semiancho final $32.3348\text{ cm}$, 17 puntos
  - Pico: largo $76.4035\text{ cm}$, 12 puntos
  - Cono inferior: largo $468.9166\text{ cm}$, 25 puntos, semiancho inicial $5.9716\text{ cm}$
  - Boca: $104.5\text{ cm}$, gajos mín: 28 / 40, altura armada: $\approx 704\text{ cm}$, empuje: $\approx 14.4\text{ kg}$
- **Cómo verificar**: Ejecutar `pytest` y comprobar que pasa en verde (100% pass).

### Paso 2: Actualización de modelos de datos en `logic/models.py`
- **Archivos que toca**:
  - `logic/models.py`
- **Descripción**: Enriquecer `BalloonInput` con los campos opcionales (`diametro_boca`, `pestana_boca`, `diametro_mecha`, `masa_mecha_g`, `alambre_mm`, `varillas`, `altura_llama`, `holgura_min`) con sus valores por defecto. Enriquecer `SectionResult` con `pestana` y `area()`. Agregar dataclasses `BocaResult`, `VueloResult` y actualizar `BalloonCalculationResult` manteniendo aliases para no romper retrocompatibilidad.
- **Cómo verificar**: Ejecutar `python -c "from logic.models import BalloonInput, BalloonCalculationResult"` y los tests de `pytest`.

### Paso 3: Portabilidad de la lógica de referencia a `logic/calculators/trompo_estrella.py`
- **Archivos que toca**:
  - `logic/calculators/trompo_estrella.py`
  - Crear `tests/test_trompo_estrella_logic.py`
- **Descripción**: Reemplazar la clase vieja `TrompoEstrellaCalculator` con la implementación portada de la referencia adaptada a los modelos de `logic/`, implementando la interfaz `BalloonCalculator`. No tocar la UI aún.
- **Cómo verificar**: Ejecutar `pytest` comprobando que `TrompoEstrellaCalculator().calcular(entrada)` genera con exactitud los mismos valores de referencia.

### Paso 4: Limpieza de nombres de archivos, imports comodín y código muerto
- **Archivos que toca**:
  - Renombrar `widgets/sidebar_2.py` $\rightarrow$ `widgets/sidebar.py` (sustituyendo la versión vieja).
  - Renombrar `ui/vista_diseñar.py` $\rightarrow$ `ui/vista_disenar.py` (actualizando la importación en `main.py`).
  - Renombrar `utils/gestor_image.py` $\rightarrow$ `utils/gestor_imagenes.py`.
  - Reemplazar `from configuracion.constantes import *` por imports explícitos en los archivos correspondientes.
  - Corregir el script de prueba o reemplazarlo por un runner de consola limpio en UTF-8.
- **Cómo verificar**: Ejecutar `python main.py` y verificar que la ventana principal abre, navega entre pestañas y no arroja errores en consola.

### Paso 5: Conexión de inputs, cálculo y resumen en `vista_trompo_estrella.py`
- **Archivos que toca**:
  - `ui/modulos_moldes/vista_trompo_estrella.py`
- **Descripción**: Conectar `btn_calcular` a un método manejador `_on_calcular()`. Leer los valores de los `CTkEntry`, instanciar `BalloonInput` y llamar a `TrompoEstrellaCalculator().calcular()`. Guardar referencias a las etiquetas de la tabla de resumen y actualizar sus textos con los valores calculados reales (diámetro boca, ancho máx, gajos recomendados).
- **Cómo verificar**: Abrir la aplicación, ingresar 950, 30, 1, 2, hacer clic en "Calcular" y verificar que la tabla de resumen muestra de inmediato los valores exactos (104.5 cm de boca, 63.7 cm de ancho, etc.).

### Paso 6: Generación dinámica de tablas detalladas (17, 12 y 25 filas) y avisos de viabilidad
- **Archivos que toca**:
  - `ui/modulos_moldes/vista_trompo_estrella.py`
- **Descripción**: Sustituir el bucle estático de 10 filas por un renderizador dinámico que construya las filas exactas según `len(puntos)` (17, 12 y 25 renglones) con sus valores de paso, largo, acumulado y ancho/2. Agregar banner visual de avisos de viabilidad (indicando si la holgura de la mecha es segura y si el globo vuela).
- **Cómo verificar**: Probar con datos normales (verifica que se listan las 17, 12 y 25 filas con la pestaña de 4 cm al pie del cono inferior) y con datos inviables (p. ej. boca muy chica o altura mínima) comprobando que aparecen los avisos en amarillo/rojo.

### Paso 7: Persistencia y visualización gráfica
- **Archivos que toca**:
  - `ui/modulos_moldes/vista_trompo_estrella.py`
  - `logic/gestor_archivos.py`
- **Descripción**: Conectar el botón "Guardar Medidas" a `GestorArchivos.guardar_globo` guardando el resultado en `guardados/`. Implementar en el panel derecho un dibujo 2D esquemático de los moldes o del perfil del globo usando `Canvas`.
- **Cómo verificar**: Hacer clic en "Guardar Medidas" y verificar que se genera un archivo `.json` legible en la carpeta `guardados/`.

---

## 9. Preguntas Clave para el Usuario

Antes de comenzar a ejecutar los pasos de código, es necesario acordar los siguientes puntos:

1. **Ubicación canónica de la calculadora**:
   ¿Prefieres mantener la calculadora en `logic/calculators/trompo_estrella.py` (lo cual permite tener una subcarpeta para futuros tipos de globo como Piao, Bagda, etc.) o prefieres ubicarla directamente en `logic/trompo_estrella.py` como menciona el esquema general de `AGENTS.md`?
2. **Normalización de nombres de archivo**:
   ¿Autorizas renombrar `ui/vista_diseñar.py` a `ui/vista_disenar.py` (sin la ñ) y `utils/gestor_image.py` a `utils/gestor_imagenes.py` para prevenir problemas de codificación y mantener consistencia?
3. **Consolidación de Sidebar**:
   Actualmente existen `widgets/sidebar.py` (antiguo) y `widgets/sidebar_2.py` (activo). ¿Estás de acuerdo en eliminar el viejo y dejar únicamente `widgets/sidebar.py`?
4. **Campos adicionales en la UI**:
   La referencia incluye parámetros muy importantes: diámetro de boca personalizado, pestaña de boca, diámetro de mecha y peso de mecha. ¿Prefieres que estos campos aparezcan directamente visibles en la columna izquierda o en una sección desplegable/botón de *"Parámetros Avanzados"* para no saturar la vista inicial?
5. **Tecnología para la gráfica 2D**:
   Para el área de *"Graficación de medidas"*: ¿prefieres usar `tkinter.Canvas` nativo (dibujo vectorial ligero sin dependencias externas) o deseas incorporar `matplotlib` en `requirements.txt` para graficar curvas y puntos con ejes numéricos?
6. **Estrategia respecto a Flet**:
   ¿Confirmamos que completaremos primero toda la aplicación funcional y probada en CustomTkinter antes de crear una rama independiente para evaluar la migración a Flet?
