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
  - `tema.py`: diseño, paleta y estilos atómicos.
  - `controlador/`: paquete modular con fachada delgada (`__init__.py`) y mixins especializados (`entradas.py`, `hoja.py`, `diseno.py`, `vista3d.py`, `proyecto.py`, `modelos.py`).
  - `vistas/`:
    - `trompo.py`: compositor principal (`VistaTrompo`, ≤ 400 líneas).
    - `panel_entradas.py`: panel izquierdo con campos de geometría y cálculo.
    - `barra_proyecto.py`: barra de estado y operaciones de proyecto (nuevo, abrir, guardar).
    - `trompo_compat.py`: capa de compatibilidad y delegación de proxies para tests.
    - `pestanas/`: módulos desacoplados para cada pestaña (`base.py`, `resumen.py`, `tablas.py`, `moldes2d.py`, `hoja.py`, `diseno.py`, `diseno_inspector.py`, `diseno_visor.py`, `vista3d.py`, `vista3d_aux.py`, `dialogos_catalogo.py`).
    - `componentes/`: controles reutilizables (`visor_svg.py`).
- `logic/` → lógica de negocio pura:
  - `interfaces.py` (`BalloonCalculator`).
  - `models.py` (`BalloonInput`, `BalloonCalculationResult`, `SectionResult`, `Point2D`).
  - `proyecto/modelo.py` (`Proyecto` guardado en JSON, versionado).
  - `diseno/`: `esquema.py`, `lienzo.py`, `paleta.py`, `pintura.py`, `compra.py`, `diseno_pico.py`, `config_seccion.py`, `transformaciones.py`.
  - `exportacion/`:
    - `comun.py`: ayudantes compartidos de SVG (paths con precisión fija, marcadores de flechas, Inkscape, guardado UTF-8).
    - `svg_moldes.py`: moldes sueltos y hojas de trazo automáticas en Carta/A4.
    - `svg_abanico.py`: hojas de trazo en abanico completo y mitad.
    - `svg_diseno.py`: piezas decoradas individuales y por lote.
    - `svg_perfil.py`: perfil armado proyectado con cotas.
    - `paquete.py`: generador integral de paquete de exportación.
    - `escena3d.py`, `visor3d.py`: exportación y servidor Three.js.
  - `geometria/`: `malla_trompo.py`, `perfil.py`, `abanico.py`.
  - `gestor_archivos.py` (`GestorArchivos`: guarda/carga/lista JSON en `guardados/`).
- `presentacion/` → capa pura compartida de formateo de datos para la UI (`presentacion/trompo_estrella.py`, define `DECIMALES_TABLA`).
- `recursos/` → iconos e imágenes del proyecto.
- `scripts/` → runners de consola y utilidades de métricas de código (`metricas_codigo.py`).
- `referencia/trompo_estrella.py` → prototipo autocontenido con la lógica CORRECTA y validada.
- `tests/` → pruebas con pytest y snapshots (`tests/snapshots/`).
- `requirements.txt`, `requirements-dev.txt` → dependencias de producción y desarrollo.
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
    - Paleta de colores de papel china (`datos/colores_papel.json`, `logic/diseno/paleta.py`): catálogo con colores comerciales tradicionales mexicanos, campos `marca`, `codigo` y `notas`; importación y exportación a CSV con tolerancia a delimitadores (coma o punto y coma), BOM UTF-8 y filas inválidas; soporte de colores calibrados (`aproximado=False`).
    - Esquema de pintura por sección y patrones (`logic/diseno/pintura.py`):
      - Conos superior e inferior: modos `liso`, `alternado por gajo`, `bloques de G gajos`, con ciclos de 1 a 6 colores; opción de replicar automáticamente el esquema del cono superior en el inferior.
      - Picos: variantes A y B con modos de caras (`igual en las 4`, `alternando 2`, `4 distintos`), y modos de repetición entre pirámides (`todas A`, `alternar por gajo`, `alternar por hilera`, `ajedrez`).
      - Vista previa 2D reactiva en la pestaña: franjas por gajo para conos y cuadrícula $H \times N$ para picos con `color_de_cara`.
    - Lista de compra y paquetes (`logic/diseno/compra.py`): cálculo de piezas, superficie neta en m², pliegos enteros y cálculo de paquetes según pliegos por paquete configurable (default 100). Coherencia exacta de áreas con el Resumen. Serializado en `Proyecto`.
    - Escena 3D serializable (`logic/exportacion/escena3d.py`): caras trianguladas con normales exteriores consistentes, boca anclada en z=0 y soporte para texturas/motivos.
    - Visor 3D interactivo (`app_flet/assets/visor3d/`): three.js v0.128.0 empaquetado localmente con licencias MIT en `vendor/LICENSE`. Sombreado facetado, control orbital, modos día/noche, controles de iluminación solar con deslizadores de azimut (0..360°) y elevación (5..85°), intensidad, exposición ACESFilmic, sombras suaves `PCFSoftShadowMap`, botones separados para Wireframe y Costuras (`EdgesGeometry`), centrado de cámara y guardado de captura en PNG.
    - Servidor local daemon (`logic/exportacion/visor3d.py`): servidor HTTP ligero en `127.0.0.1:<puerto>` para alimentar el visor local en tiempo real sin recargar la página.
    - Exportación autocontenida de visor 3D HTML sin enlaces externos ni llamadas a red, y soporte en paquete de exportación (`logic/exportacion/paquete.py`).
    - Pestaña "Vista 3D" en Flet (`app_flet/vistas/trompo.py`): selectores de patrones de pintura, gestión de colores/marcas y CSV, vista previa de franjas/cuadrícula 2D, botón de lanzamiento de visor 3D en navegador del sistema, botón de exportación HTML independiente, aviso fijo de colores aproximados, configuración de dimensiones de pliego, tabla de lista de compra detallada con paquetes y copiado al portapapeles.
    - Etiquetado en git con `f4-3d-pintura`. Nota de historial: el commit `2431103` quedó vacío ya que sus cambios se incluyeron en el commit anterior.
  - F5: Hoja de trazo en abanico y diseño del pico (HECHO):
    - Geometría de abanico pura (`logic/geometria/abanico.py`): `PiezaPlana` con distancias al vértice virtual $s_0$ ($0$ en cono superior y pico, $l \cdot ab / (a - ab)$ en cono inferior), radio de arco $s_1 = s_0 + l$, ángulo $\psi = 2 \cdot \text{atan}((a/2) / s_1)$, y `abanico(pieza, n, centrado=True)` que calcula la disposición plana de $n$ gajos unidos por aristas comunes en cm sin distorsión de distancias.
    - SVG de hoja en abanico (`logic/exportacion/svg_abanico.py`): orientación con ápice abajo, cálculo de escala óptima horizontal/vertical para hojas Carta y A4 con margen de 10 mm. Capas Inkscape con `inkscape:groupmode="layer"` (`papel`, `cuadricula`, `ejes`, `aristas_comunes`, `contorno`, `costura`, `rotulos`, `pestana`). Soporta modo `"completo"` ($G$ gajos o 4 caras) y `"mitad"` ($\lceil G/2 \rceil$ gajos o 2 caras) para trazo y corte sobre papel doblado en simetría.
    - Decisión arquitectónica sobre margen de costura: en moldes de piezas sueltas la costura se traza en ambos lados de cada pieza; en la hoja en abanico el margen de costura se dibuja ÚNICAMENTE en los dos bordes laterales extremos del abanico completo (no en las aristas intermedias), ya que los gajos interiores se cortan continuos en el mismo papel.
    - Diseño del pico (`logic/diseno/diseno_pico.py`): selector compartido de variante de pirámide `variante_de_piramide(modo, hilera, gajo)`, dataclass `EsquemaDisenoPico` (modos `todas_a`, `alternar_gajo`, `alternar_hilera`, `ajedrez`, variantes A y B) y `resumen_pico` con conteo exacto de pirámides ($H \times N$) y piezas triangulares ($H \times N \times 4$). Serializado en `Proyecto`.
    - Paquete de exportación (`logic/exportacion/paquete.py`): genera `hoja_abanico_superior.svg`, `hoja_abanico_pico.svg` y `hoja_abanico_inferior.svg` según la selección de lienzo.
    - Pestaña "Hoja de trazo" en Flet (`app_flet/vistas/trompo.py`): selector de lienzo ("Abanico" vs "Piezas separadas"), selector de modo ("Completo" vs "Mitad (espejo)"), panel reactivo de diseño de pico con resumen cuantitativo y visor vectorial dinámico.
  - F6a: Diseño gráfico y motivos sobre el abanico (HECHO):
    - Modelo de diseño y recursos seguros (`logic/diseno/lienzo.py`): dataclasses `CapaDiseno` y `Diseno`. Importación segura con `defusedxml` para SVGs (bloqueo estricto de scripts, DOCTYPE/ENTITY, foreignObject, eventos inline on* y URLs externas) y `Pillow` para imágenes raster (límite de seguridad 10000 px, 30 MB y corrección de orientación EXIF).
    - Carpeta de recursos del proyecto (`logic/proyecto/modelo.py`): almacenamiento en `<nombre>_recursos/` relativo al archivo `.json` del proyecto con detección de recursos faltantes (`recursos_faltantes`) y copia/empaquetado íntegro en `guardar_proyecto`.
    - Geometría de transformaciones e isometrías (`logic/diseno/transformaciones.py`): clase `Transformacion2D` con matrices afines 3×3 e inversión exacta ($<10^{-15}$ error). Mapeo de gajos en abanico (`transformacion_a_gajo`), reflejo rígido en simetría (`reflejo_del_abanico`), polígono de recorte con o sin sangrado (`recorte_gajo`), y resolución de gajos equivalentes (`gajos_equivalentes`, `construir_grupo`) para los esquemas repetición, central con espejo, espejo total y personalizado.
    - Salidas SVG decoradas (`logic/exportacion/svg_abanico.py`, `logic/exportacion/svg_diseno.py`): capa `diseno` con `clipPath` del abanico, eje de simetría resaltado en modo mitad, función `svg_gajo` para moldes individuales recortados y proyectados con marcas de espejo y motivo, y exportador por lotes `exportar_diseno`.
    - 5.ª Pestaña "Diseño" en Flet (`app_flet/vistas/trompo.py`): colocada entre "Hoja de trazo" y "Vista 3D" (orden: Resumen, Tablas de moldes, Moldes 2D, Hoja de trazo, Diseño, Vista 3D). Selector de sección (cono superior, pico variante A/B, cono inferior) y modo de lienzo (completo / mitad). Panel lateral de capas con lista reordenable, botones de visibilidad, bloqueo y eliminación. Inspector de propiedades (nombre, coordenadas X/Y en cm, dimensiones, bloqueo de proporción, rotación -180..180°, opacidad 0..100%, reflejo H/V, botones de centrado y ajuste rápido a bordes). Visor vectorial interactivo con zoom y paneo por viewBox. Exportación de gajos individuales decorados y hoja de trazo decorada en SVG.
    - Configuración independiente por sección (`logic/diseno/config_seccion.py`): cada sección (superior, inferior, pico) tiene su propio esquema de pintura/diseño, modo de dibujo (`completo` / `mitad`), lienzo (`abanico` / `separadas`) y escala, desacopladas entre sí. Proyecto serializado en versión 2 con migración transparente desde v1.
    - Mitad exacta del abanico (`logic/geometria/abanico.py`, `logic/exportacion/svg_abanico.py`): el modo `mitad` representa la mitad derecha exacta ($x \ge 0$) del abanico completo con un eje vertical recto en $x=0$, área exactamente la mitad, invariancia de coordenadas (la imagen no salta de posición al alternar entre completo y mitad) y visualización opcional del reflejo simétrico fantasma.
    - Manipulación y ajuste rápido sobre el lienzo (`logic/diseno/lienzo.py`, `app_flet/controlador.py`, `app_flet/vistas/trompo.py`):
      - 6 modos de ajuste rápido: `[Cubrir]`, `[Contener]`, `[Estirar]`, `[Ancho]`, `[Alto]`, `[Centrar]`, con cálculo de bounding box rotado.
      - Importación de recursos con nombre por defecto sin extensión (stem) y posicionamiento automático con `contener`.
      - Overlay de selección interactiva en SVG con caja punteada, 4 tiradores de esquina y círculo con cruz central.
      - Modo interactivo en lienzo para alternar entre navegación (pan/zoom) y arrastre directo de la capa activa con el ratón.
      - Botones de empuje rápido (nudge) de posición (±1 cm) y rotación (±5°, 0°).
      - Opciones de visualización conmutables: Cuadrícula, Rótulos (ocultos por defecto en Diseño), Costuras y Mostrar reflejo.
      - Botones de exportación dedicados: "Exportar abanico con diseño (SVG)", "Exportar piezas con diseño…" y "Exportar hoja Carta con diseño".
    - Ejemplos (`docs/ejemplos/disenos/`): proyecto `ejemplo_espejo_12.json` (actualizado a v2) con su carpeta de recursos, 2 motivos SVG tradicionales y 1 imagen PNG de prueba.
    - Etiquetado en git con `f6a-seccion-mitad`.
    - Optimización del arrastre interactivo y renderizado de SVG nativo:
      - Causa raíz del congelamiento: `on_pan_update` llamaba síncronamente a `controlador.empujar_capa_seleccionada()` que regeneraba el SVG completo (con imágenes raster en base64 de varios MB o árboles XML densos) e inmediatamente ejecutaba `_sync_controlador_a_vista()` llamando a `self.update()` de toda la página a 60 Hz. Una ráfaga típica de 300 eventos transmitía entre 36 MB y 582 MB por el canal IPC Flutter <-> Python, saturando la cola de mensajes del motor y bloqueando indefinidamente el bucle de eventos asyncio.
      - Causa raíz del SVG invisible: `svg_abanico.py` e `svg_diseno.py` incrustaban los SVGs importados como `<image href="data:image/svg+xml;base64,...">`. El motor `flutter_svg` de Flutter no soporta archivos SVG incrustados dentro de etiquetas `<image>`, requiriendo elementos nativos (`<g>`, `<path>`, etc.).
      - Solución arquitectónica:
        - Renderizado SVG nativo (`logic/diseno/lienzo.py`, `logic/exportacion/svg_abanico.py`, `logic/exportacion/svg_diseno.py`): extracción limpia de hijos XML con `defusedxml` y `xml.etree.ElementTree`, registro de namespaces estándar sin prefijos espurios (`ns0:`), prefijado sistemático de IDs (`c_{id}_`) para evitar colisiones de gradientes o máscaras, extracción de `viewBox`, escalado preservando aspecto centrado en caja y caché en memoria (`obtener_fragmento_capa`, `CACHE_FRAGMENTOS_CAPA`). Imágenes raster usan vista previa reducida a máx 1600 px en pantalla y resolución nativa al exportar.
        - Arrastre interactivo no bloqueante (`app_flet/vistas/trompo.py`, `app_flet/controlador.py`): `ft.GestureDetector(drag_interval=35)` limitando nativamente la frecuencia de muestreo a ~28 Hz; identidad fija del detector (nunca recreado durante el gesto); durante el arrastre (`on_pan_update`) solo se actualiza la posición en memoria (`actualizar_svg=False`), no se llama a `page.update()` ni a `self.update()`, y se actualizan únicamente los campos numéricos de texto `txt_pos_x` y `txt_pos_y` con guarda `_actualizando_programatico = True`.
        - Recomposición asíncrona al soltar (`on_pan_end`, `on_pan_cancel`, `on_exit` o timeout de seguridad de 2.0 s): 1 sola recomposición en segundo plano con `threading.Thread` y contador incremental (`_id_recomposicion_diseno`) que descarta tareas obsoletas si ocurre un nuevo gesto. Indicador discreto "Actualizando…" durante el proceso.
      - Métricas antes / después (300 micro-eventos de arrastre en pantalla):
        - Tiempo por evento: antes ~15-60 ms (bloqueando el hilo de UI) -> después <0.2 ms (UI fluida a 60 fps).
        - Tráfico IPC Flutter/Python: antes 36 MB a 582 MB transmitidos en ráfaga -> después ~2 KB (solo campos numéricos de posición).
        - Recomposiciones de SVG pesado: antes 300 por ráfaga -> después 1 (al soltar).
        - Llamadas a `page.update()`: antes 300 -> después 0 durante el arrastre.
      - Regla obligatoria para cualquier futuro gesto continuo en Flet:
        - Separar estrictamente la manipulación interactiva de la recomposición pesada:
          1. Durante el gesto (`on_pan_update`, sliders continuos, etc.): limitar frecuencia con `drag_interval`, actualizar solo el modelo en memoria y controles atómicos ligeros (e.g. textos o cajas de selección `control.update()`). NUNCA llamar a `page.update()` ni regenerar estructuras pesadas (SVGs, mallas 3D, HTMLs).
          2. Al soltar (`on_pan_end`, `on_change_end`, o cancelaciones): disparar la recomposición pesada en segundo plano fuera del hilo de UI (`threading.Thread` o `page.run_thread`) con descarte de tareas obsoletas mediante identificador de versión, envolviendo siempre en `try / finally` para garantizar que las banderas (`_arrastrando`, `_ocupado`) se restablezcan en todo momento.
      - Sistema de registro (logging):
        - Registro rotativo en `logs/globos.log` (1 MB × 3 archivos, UTF-8), nivel INFO, capturas no controladas mediante `sys.excepthook`, `threading.excepthook`, `asyncio.get_event_loop().set_exception_handler` y `page.on_error`.
        - Activación de telemetría en pantalla mediante variable de entorno `GLOBOS_DEBUG=1` (`python main.py` o en PowerShell `$env:GLOBOS_DEBUG="1"; python main.py`).
      - Etiquetado en git con `fix-arrastre-capa`.
    - Manipulación interactiva de capas y modos Navegar / Editar (`logic/diseno/gestos_lienzo.py`, `app_flet/vistas/componentes/marco_edicion.py`):
      - Regla fundamental: En modo editar el lienzo muestra base + capas fantasma sin recortar; la composición completa ocurre solo en modo navegar y al exportar.
      - Modos excluyentes:
        - `navegar` (por defecto): Pan y zoom del visor SVG activos; capas compuestas y recortadas en el SVG; marco de edición oculto.
        - `editar`: Pan por arrastre del visor desactivado (`gestos_habilitados=False`), zoom por rueda del ratón (`on_gesture_scroll`) siempre activo. El fondo muestra el abanico base ligero (modo fantasma) y sobre él se superpone el marco de edición (`MarcoEdicion`).
      - Geometría analítica pura (`logic/diseno/gestos_lienzo.py`):
        - `Conversion`: Regla de encaje `preserveAspectRatio meet` con centrado y bandas vacías; métodos `plano_a_px`, `px_a_plano`, `delta_px_a_plano` (con signo invertido $y$ hacia arriba hacia el arco del abanico) y `px_por_cm`.
        - Geometría de manipulación: `mover`, `estirar` (8 tiradores con invarianza exacta de la esquina/borde opuesto para cualquier ángulo de rotación $\theta$, sin voltear y con límite `minimo_cm=1.0`), y `rotar`.
      - Componente Flet `MarcoEdicion`:
        - `ft.Stack` con posicionamiento absoluto (`left`, `top`, `width`, `height`, `rotate`).
        - 1 detector para el cuerpo del marco (`caja_marco`, `mouse_cursor=ft.MouseCursor.MOVE`) para mover la capa.
        - 8 tiradores de redimensionamiento con zona táctil de 18 px (`TAM_TIRADOR_PX=18.0`), caja visual de 10 px y cursores de ratón específicos (`RESIZE_UP_LEFT_DOWN_RIGHT`, `RESIZE_UP_RIGHT_DOWN_LEFT`, `RESIZE_UP_DOWN`, `RESIZE_LEFT_RIGHT`).
        - 1 tirador de rotación superior (`cont_rot`, `mouse_cursor=ft.MouseCursor.PRECISE`).
        - Capas bloqueadas: muestran el contorno del marco pero ocultan los 8 tiradores y el de rotación, impidiendo cualquier arrastre.
      - Flujo de eventos continuo y rendimiento a 60 fps:
        - En cada micro-arrastre (`on_pan_update`), throttle a $\le 60$ Hz (16 ms): se convierte el delta a coordenadas de plano con `Conversion`, se actualiza la geometría en memoria y se llama únicamente a `control.update()` sobre los contenedores afectados del marco (`caja_marco`, tiradores). NUNCA se llama a `page.update()` ni se recompone el SVG.
        - Al soltar (`on_pan_end`, `on_pan_cancel`, `on_exit`): se confirma la geometría en el controlador y los campos numéricos del inspector (`actualizar_campos_geometria` con guarda programática). En modo editar NO se dispara recomposición; la composición completa se realiza únicamente al alternar a modo `navegar` o al exportar.
      - Demo interactiva: `python scripts/demo_marco.py` para probar la sensación y respuesta del marco sin levantar la app completa.
      - Etiquetado en git con `fix-edicion-capa`.
  - F6b: Vectorización y procesado avanzado de plantillas (calcos monocromáticos, plantillas de corte e instrucciones de ensamble).
  - F7: Mapeo de motivos y texturas sobre la malla 3D interactiva en Three.js y exportación de planos de corte multicapa.

## Problemas conocidos
- En la pestaña Hoja de trazo, al cambiar de sección (p. ej. de cono superior con "Piezas separadas" a Pico) el selector de lienzo tarda en refrescarse y muestra el valor de la sección anterior; el usuario decidió no corregirlo ahora.

## Deuda técnica
- `app_flet/vistas/trompo_compat.py`: Capa de proxies creada para compatibilidad con pruebas antiguas; debe eliminarse una vez migradas todas las pruebas a las APIs modulares correspondientes.