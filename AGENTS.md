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
- Pliego ≈ 50×70 cm (+15 % desperdicio, configurable en Condiciones y proyecto). Gajo ideal ≤ 70 cm de ancho.

## Valores de referencia (test de regresión: 950 / 30 gajos / 2 hileras / 1 cm)
- ancho_gajo 63.6696 · cono sup: largo 353.7441, salto 22.1090, semiancho final 32.3348, 17 puntos
- pico: largo 76.4035, 12 puntos · cono inf: largo 468.9166, 25 puntos, semiancho inicial 5.9716
- boca 104.5 · gajos mín (70/50 cm): 28 / 40 · altura armada ≈ 704 · empuje ≈ 14.4 kg · pliegos ≈ 490 (489.85)

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
  - SVG en Flet: renderizado nativo en memoria con `ft.Image(src=svg.encode('utf-8'))` envuelto en `ft.GestureDetector` con manipulación directa de `viewBox` (`logic/exportacion/vista_svg.py`) para zoom y paneo nítidos sin recortes de Flutter/InteractiveViewer.
  - Portapapeles en Flet: `ft.Clipboard` / `CopyToClipboard` con notificación mediante `ft.SnackBar`.
  - Vista 3D futura con three.js embebida como HTML autocontenido (luces realistas).
- Arquitectura Flet:
  - `app_flet/tema.py`: diseño, colores, `ft.ThemeMode`, esquemas de color atómicos.
  - `app_flet/controlador.py`: almacena estado puro y manda a llamar la lógica/presentación. No sabe de UI.
  - `app_flet/vistas/`: árbol visual. Construye las vistas e inyecta el controlador.
- Plan F1-F5:
  - F1: Resumen y avisos con tarjetas reactivas (HECHO).
  - F2: Pestañas de Tablas y Moldes 2D en SVG (HECHO, con ajustes visuales y arquitectónicos completados):
    - Estilos de SVG (`logic/exportacion/estilos.py`): presets `IMPRESION` (fondo blanco, trazo base), `PANTALLA_OSCURO` (fondo `#1e1e24`, contraste WCAG ≥ 4.5), y `PANTALLA_CLARO` (fondo `#f8f9fa`), con `factor_trazo` y `factor_texto`.
    - Rótulos en SVG multilínea (`svg_conjunto` y `svg_hoja`): textos apilados y centrados con separación dinámica basada en bounding boxes estimados, evitando colisiones entre piezas contiguas.
    - Zoom y desplazamiento por `viewBox` (`logic/exportacion/vista_svg.py`): `VistaSvg` con zoom relativo al cursor, paneo por arrastre, doble clic o botón para ajustar, botones +/- y visualización de porcentaje, manteniendo el vector a resolución nativa del dispositivo.
    - Medición dinámica de zona (`app_flet/vistas/trompo.py`): el visor mide el tamaño real de su zona (`on_size_change` descontando padding y borde), asigna dimensiones exactas a la imagen (`img_svg.width`, `img_svg.height`), adapta la relación de aspecto conservando el centro y nivel de zoom (`adaptar_aspecto`), y recorta excedentes con `clip_behavior=ft.ClipBehavior.HARD_EDGE`.
    - Depuración visual con `GLOBOS_DEBUG=1`: muestra texto bajo el visor: `zona W×H px · imagen W×H · vista x,y,w,h · zoom %`.
    - Perfil armado proyectado (`logic/geometria/perfil.py` y `logic/exportacion/svg_perfil.py`): silueta lateral proyectada a partir de la malla 3D rotada $\pi/N$ para ver los picos al borde. Incluye cotas de alto total, $\varnothing$ con picos, $\varnothing$ cuerpo y $\varnothing$ boca, junto con la nota aclaratoria: "Medidas del polígono exacto (el Resumen usa una estimación circular, diferencia < 0.5 %)". Disponible como 5.ª opción en el selector de Moldes 2D.
    - Temas claro y oscuro atómicos (`app_flet/tema.py`): controles de UI usan `ft.Colors.*` del tema del sistema (`ft.ColorScheme` en `page.theme`), cambio de tema atómico desactivando animaciones con una sola llamada a `page.update()` para evitar estados intermedios.
    - Tabla de moldes personalizada (`app_flet/vistas/tabla_molde.py`): reemplaza `ft.DataTable` para garantizar ocupación de todo el ancho, encabezado fijo, `ft.ListView` con pesos proporcionales `[7, 10, 10, 10]`, alineación derecha, filas alternadas y reinicio de scroll al cambiar de pieza.
    - Portapapeles con API pública (`app_flet/vistas/trompo.py`): servicio inyectado para testabilidad con mock, registro en `page.services`, y retroalimentación mediante `ft.SnackBar` explícito ("Tabla copiada al portapapeles" / "No se pudo copiar").
  - F3: Hoja de trazo y proyectos (HECHO):
    - Esquemas de diseño: modos `repeticion`, `central_espejo`, `espejo_total` y `personalizado`. Formato de ciclo personalizado: lista separada por comas de motivos enteros seguidos opcionalmente por `E` (ejemplo: `0, 1, 2E, 1E`), validando que la longitud divida exactamente el número total de gajos $N$.
    - Resumen del esquema: cálculo de copias por motivo y advertencias de viabilidad cuando las dimensiones exceden el margen útil de la hoja.
    - Hojas de trazo (`logic/exportacion/svg_moldes.py`): soporte de hojas Carta y A4 con orientación óptima, cálculo de escala automática y cotas en mm reales. Visor interactivo en papel blanco con sombreado y zoom/paneo vectorial.
    - Paquete de exportación (`logic/exportacion/paquete.py`): genera en un solo paso las 3 hojas a escala común, el perfil armado proyectado y el conjunto de moldes, guardados en UTF-8 con nombres seguros para Windows.
    - Ciclo de vida de proyectos (`logic/proyecto/modelo.py` y `app_flet/controlador.py`): serialización a JSON versionado incluyendo geometría, condiciones, esquema, hoja y escala. Integración en UI con acciones Nuevo, Abrir…, Guardar, Guardar como…, sincronización reactiva de campos y título de ventana dinámico con asterisco para cambios sin guardar (`*`).
    - Deuda técnica: retransmisión de `viewBox` durante arrastre. En cada micro-evento de paneo (`on_pan_update`), la cadena SVG modificada se re-codifica y retransmite a Flutter vía `img.src`. Aunque en mediciones reales rinde a >30 act/s y ~1-2 ms/actualización con telemetría activa (`GLOBOS_DEBUG=1`), para mallas o decoraciones densas (F5) convendría explorar capas de transformación nativas cuando la API de Flet lo soporte sin provocar el recorte que sufría `InteractiveViewer`.
  - F4: Vista 3D con three.js y lista de compra (HECHO):
    - Paleta de colores de papel china (`datos/colores_papel.json`, `logic/diseno/paleta.py`): catálogo con colores comerciales tradicionales mexicanos, carga extensible para colores personalizados del usuario (`colores_usuario.json`).
    - Esquema de pintura por sección, motivo o cara (`logic/diseno/pintura.py`): mapeo reactivo a caras de la malla poligonal 3D.
    - Lista de compra (`logic/diseno/compra.py`): cálculo de piezas (superior, pico, inferior), superficie neta en m² y pliegos enteros (`math.ceil`) por cada color según tamaño de pliego (50×70 cm default) y desperdicio configurable. Serializado en `Proyecto`.
    - Escena 3D serializable (`logic/exportacion/escena3d.py`): caras trianguladas con normales exteriores consistentes, boca anclada en z=0 y soporte para texturas/motivos.
    - Visor 3D interactivo (`app_flet/assets/visor3d/`): three.js v0.128.0 empaquetado localmente para funcionamiento 100 % offline. Sombreado facetado, control orbital, modos día/noche, controles de iluminación y sondeo reactivo a `/api/escena`.
    - Servidor local daemon (`logic/exportacion/visor3d.py`): servidor HTTP ligero en `127.0.0.1:<puerto>` para alimentar el visor local en tiempo real sin recargar la página.
    - Exportación autocontenida de visor 3D HTML y soporte en paquete de exportación (`logic/exportacion/paquete.py`).
    - Pestaña "Vista 3D" en Flet (`app_flet/vistas/trompo.py`): selectores de color para cono superior, picos y cono inferior; botón de lanzamiento de visor 3D en navegador del sistema; botón de exportación HTML independiente; tabla de lista de compra detallada y botón para copiar al portapapeles en formato TSV.
  - F5: Diseños sobre cada pieza.