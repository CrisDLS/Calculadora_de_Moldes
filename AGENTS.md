# Calculadora de moldes — globo de cantoya "trompo estrella"

## Objetivo
Dadas altura, gajos, hileras de picos y costura, calcular las TRES piezas planas de
cada gajo (cono superior, pico, cono inferior) para cortar el molde de un globo de
papel china que se eleva con aire caliente (tradición de Veracruz). Cualquier medida
que el usuario ponga debe validarse como viable o explicar por qué no.

## Estructura real del repositorio
- `main.py` → app CustomTkinter (`App`): sidebar + `content_frame` + vistas con carga perezosa.
- `logic/` → `interfaces.py` (`BalloonCalculator`), `models.py` (`BalloonInput`,
  `BalloonCalculationResult`, `SectionResult`, `Point2D`), `utils.py`.
- `ui/` → vistas (`vista_inicio`, `vista_moldes`, `vista_guardados`, `vista_diseñar`, `vista_info`)
  y `ui/modulos_moldes/vista_trompo_estrella.py`.
- `widgets/` (p. ej. `sidebar_2`), `configuracion/constantes.py` (colores), `utils/`, `recursos/`.
- `referencia/trompo_estrella.py` → prototipo autocontenido con la lógica CORRECTA y validada
  (copiarlo al repo en esa carpeta; no forma parte de la app, es la referencia a portar).

## Reglas de arquitectura
- `logic/` NUNCA importa `customtkinter`, `flet` ni `tkinter`, y NUNCA imprime ni lee consola:
  `calcular()` devuelve objetos. Nuevos tipos de globo implementan `BalloonCalculator`.
- La UI solo recoge entradas, llama a `calcular()` y muestra resultados; no contiene fórmulas.
- Tareas largas (dibujar moldes, exportar PDF/DXF) reciben un callback `on_progress(fraccion, texto)`
  y se ejecutan fuera del hilo de la interfaz.
- Tarea 1: portar `referencia/trompo_estrella.py` a `logic/` sin cambiar resultados (tests primero).
  Reemplazar la clase vieja `TrompoEstrellaCalculator`.
- Tarea 2 (después, en una rama aparte): evaluar migrar la UI de CustomTkinter a Flet. Fijar la
  versión de Flet en `requirements.txt` y comprobar la API contra la documentación de esa versión.
- Renombrar `requiremets.txt` a `requirements.txt`.

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
pico = triángulo, uno por gajo y por hilera. Prototipo mínimo recomendado: ~380 cm de papel.

## Reglas para el agente
- Antes de cambiar una fórmula, di cuál y por qué; no toques las constantes sin avisar.
- Todo parámetro nuevo va como campo con valor por defecto, no número mágico.
- Escribe tests con los valores de referencia y corre pruebas tras cada cambio.
- Responde en español.