# Calculadora de moldes — globo de cantoya "trompo estrella"

## Objetivo
Dadas altura, gajos, hileras de picos y costura, calcular las TRES piezas planas de
cada gajo (cono superior, pico, cono inferior) para cortar el molde de un globo de
papel china que se eleva con aire caliente (tradición de Veracruz). Cualquier medida
que el usuario ponga debe validarse como viable o explicar por qué no.
* Flujo del usuario y diseño a escala:
  El usuario diseña las caras del globo sobre los moldes planos dibujando en grupos de $G$ gajos vecinos.
  Hoy el usuario calcula los moldes a escala en GeoGebra, los exporta a SVG, los decora/pinta en Inkscape, y al final los ajusta en una hoja tamaño Carta como referencia para imprimir y transferir.
  La app reemplaza la calculadora manual (GeoGebra) y la generación de la hoja (generando directamente SVGs configurados).
  Existen 3 modos de esquemas de pintura basados en el tamaño de grupo ($G$):
  - Repetición: Los $G$ gajos son motivos distintos ($G$ motivos en total), repetidos secuencialmente sin espejos. (Ejemplo: con $N=20$ y $G=5$, 4 grupos de motivos 1-2-3-4-5).
  - Central con espejo: $G$ debe ser impar. Hay un motivo central (no espejeado) y los demás se espejean simétricamente hacia los bordes. (Ejemplo: con $N=20$ y $G=5$, motivo central 3 con vecinos 2, 1 espejeados: 1-2-3-2'-1').
  - Espejo total: $G$ debe ser par. Los motivos se abren en espejo desde el centro del grupo (sin un motivo impar al medio) y el espejo continúa en la unión entre grupos. (Ejemplo: con $N=20$ y $G=4$, mitad y mitad en espejo: 1-2-2'-1').

## Estructura real del repositorio
- `main.py` → punto de entrada de la app en Flet (`ft.run(main)`).
- `app_flet/` → interfaz en Flet:
  - `main.py`: configuración de ventana y montaje de vistas.
  - `tema.py`: diseño, paleta y estilos.
  - `controlador.py`: estado puro en Python y puente con la lógica/presentación.
  - `vistas/trompo.py`: vista principal del trompo estrella.
- `logic/` → lógica de negocio pura:
  - `interfaces.py` (`BalloonCalculator`).
  - `models.py` (`BalloonInput`, `BalloonCalculationResult`, `SectionResult`, `Point2D`).
  - `proyecto/modelo.py` (`Proyecto` guardado en JSON, versionado).
  - `diseno/esquema.py` (esquemas `repeticion`, `central_espejo`, `espejo_total` con tamaño de grupo).
  - `exportacion/svg_moldes.py` (generación de moldes sueltos en mm a escala real y hojas de trazo automáticas en Carta/A4 con múltiples copias).
  - `geometria/malla_trompo.py` para construir una malla 3D exacta mapeando isométricamente 2D a 3D (para exportar a JSON/three.js).
  - `gestor_archivos.py` (`GestorArchivos`: guarda/carga/lista JSON en `guardados/`).
- `presentacion/` → capa pura compartida de formateo de datos para la UI (`presentacion/trompo_estrella.py`, define `DECIMALES_TABLA`).
- `recursos/` → iconos e imágenes del proyecto.
- `scripts/reporte_trompo_estrella.py` → runner de consola (argparse: altura gajos hileras costura `--avanzado`).
- `referencia/trompo_estrella.py` → prototipo autocontenido con la lógica CORRECTA y validada.
- `tests/` → pruebas con pytest (se corren desde la raíz; `pytest.ini` fija `pythonpath = .`).
- `requirements.txt` → dependencias (`pytest`, `flet`).
- La interfaz previa en CustomTkinter fue retirada y queda preservada en la etiqueta `ctk-final` (`git checkout ctk-final` para consultarla).

## Reglas de arquitectura
- `logic/` NUNCA importa `flet`, y NUNCA imprime ni lee consola:
  `calcular()` devuelve objetos. Nuevos tipos de globo implementan `BalloonCalculator`.
- La UI solo recoge entradas, llama a `calcular()` y muestra resultados; no contiene fórmulas.
- Tareas largas (dibujar moldes, exportar PDF/DXF) reciben un callback `on_progress(fraccion, texto)`
  y se ejecutan fuera del hilo de la interfaz.
- 3D futuro: three.js (luces realistas) como HTML autocontenido; la geometría vivirá en Python puro y se serializa a JSON.
  - CONVENCIÓN: El "largo" (generatriz) de las piezas es el eje central (apotema de la cara 3D), no el borde lateral (que mide sqrt(largo² + (a/2)²)).
  - La malla usa polígonos exactos (R = a / (2*sin(pi/N))) y alturas calculadas con apotemas para que las áreas y ejes coincidan perfectamente.
  - DIFERENCIA: La calculadora estima un globo circular (altura armada ≈703.8 cm). La malla exacta (polígono) resulta en una altura Z máx ligeramente mayor (≈706.3 cm) por la diferencia entre circunferencia y perímetro poligonal (diferencia de ~0.35 %). NO cambiar la calculadora.
- Nombres de archivo sin `ñ`, sin espacios y sin typos (`requirements.txt`).

## Modos de cálculo (campo `usar_parametros_avanzados: bool = False` en `BalloonInput`)
- MODO SIMPLE (por defecto): calcula las 3 piezas con la boca por defecto (11 % del largo, necesaria
  para el cono inferior), SIN pestaña. Muestra ancho de gajo, gajos recomendados y área de papel.
  NO calcula mecha, holgura, empuje, carga ni viabilidad: el resultado deja `boca` y `vuelo` en `None`,
  `viable` en `None` y un único aviso: "Modo simple: solo geometría. Activa parámetros avanzados para
  verificar viabilidad".
- MODO AVANZADO (casilla/sección desplegable "Parámetros avanzados"): boca personalizada, pestaña,
  diámetro y peso de mecha; en una subsección alambre, varillas, altura de llama y holgura. Activa
  pestaña, holgura, empuje, carga neta, pliegos y viabilidad.

## Fuente de verdad
Excel `CALCULADORA_DE_MOLDE_TROMPO_ESTRELLA_MODEL_3_EDITABLE_.xlsx`.
La clase vieja `TrompoEstrellaCalculator` (0.42/0.58 sobre toda la altura y generatriz
con hipotenusa) NO coincide con el Excel: reemplazarla.

## Modelo (todas las longitudes en cm)
- `altura` = largo TOTAL de papel sobre la superficie (no la altura vertical armada).
- diámetro máx = 0.64·altura · radio r = diámetro/2 · ancho_gajo = π·diámetro/gajos
- largo_picos = ancho_gajo · hileras · restante = altura − largo_picos
- cono superior = 0.43·restante · cono inferior = 0.57·restante · pico = 1.20·ancho_gajo
- boca (diámetro) = 0.11·altura por defecto, configurable · ancho_boca_gajo = π·boca/gajos
- Cada pieza: puntos con semiancho lineal; todo semiancho suma costura/2.
  Intervalos: superior 16, pico 11, inferior 24 (puntos = intervalos + 1).
  Superior: 0 → ancho_gajo/2 · Pico: 0 → ancho_gajo/2 · Inferior: ancho_boca/2 → ancho_gajo/2.
- Cono inferior lleva PESTAÑA extra (default 4 cm) después del paso 1 para doblar sobre el aro.
- Mecha/parrilla: diámetro = 50 % de la boca (medida del usuario). Holgura = radio_boca − radio_mecha;
  mínimo 10 cm (criterio inicial). Boca mínima = mecha + 2·holgura_min.
- Empuje: gas ideal, 28 °C ambiente, 70 °C interior, papel 20 g/m² (+20 % pegamento).
- Pliego ≈ 50×75 cm (+15 % desperdicio). Gajo ideal ≤ 70 cm de ancho.

## Valores de referencia (test de regresión: 950 / 30 gajos / 2 hileras / 1 cm)
- ancho_gajo 63.6696 · cono sup: largo 353.7441, salto 22.1090, semiancho final 32.3348, 17 puntos
- pico: largo 76.4035, 12 puntos · cono inf: largo 468.9166, 25 puntos, semiancho inicial 5.9716
- boca 104.5 · gajos mín (70/50 cm): 28 / 40 · altura armada ≈ 704 · empuje ≈ 14.4 kg

## Supuestos por calibrar con prototipo (no son datos publicados)
pestaña 4 cm · holgura 10 cm · altura de llama 40 cm · 70 °C interior · +20 % pegamento ·
Cada pico es una pirámide de base cuadrada armada con 4 triángulos del molde del pico, una pirámide por gajo y por hilera. Prototipo mínimo recomendado: ~380 cm de papel.

## Reglas para el agente
- Antes de cambiar una fórmula, di cuál y por qué; no toques las constantes sin avisar.
- Todo parámetro nuevo va como campo con valor por defecto, no número mágico.
- Escribe tests con los valores de referencia y corre pruebas tras cada cambio.
- Responde en español.

## Migración a Flet (en progreso)
- La interfaz es SOLO Flet; CustomTkinter queda en la etiqueta `ctk-final` (`git checkout ctk-final`).
- `main.py` levanta la app Flet (`python main.py` o `.venv\Scripts\flet.exe run main.py`).
- Decisiones:
  - `presentacion/` compartida entre CustomTkinter y Flet (sin dependencias de UI).
  - Controlador Flet (`app_flet/controlador.py`) en Python puro, sin importar Flet ni UI, cálculo instantáneo síncrono sin hilos.
  - Diseños sobre cada pieza y hojas de trazo generados directamente en SVG para Inkscape e impresión.
  - Vista 3D futura con three.js embebida como HTML autocontenido (luces realistas).
- Arquitectura Flet:
  - `app_flet/tema.py`: diseño, colores.
  - `app_flet/controlador.py`: almacena estado puro y manda a llamar la lógica/presentación. No sabe de UI.
  - `app_flet/vistas/`: árbol visual. Construye las vistas e inyecta el controlador.
- Plan F1-F5:
  - F1: Resumen y avisos con tarjetas reactivas (HECHO).
  - F2: Pestañas de Tablas y Moldes 2D en SVG.
  - F3: Hoja de trazo (esquema, grupo, Carta, escala, exportar SVG) y guardar/abrir proyecto.
  - F4: Vista 3D con three.js.
  - F5: Diseños sobre cada pieza.