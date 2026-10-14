# Calculadora de Moldes — Globo de Cantoya "Trompo Estrella"

Aplicación de escritorio para el diseño, cálculo geométrico y despiece de moldes de globos de cantoya tradicionales de tipo "trompo estrella" (tradición de Zozocolco y Veracruz, México).

## Características principales
- **Cálculo geométrico exacto**: Obtención de las tres piezas de cada gajo (cono superior, cono inferior y picos) a partir de la altura total de papel, número de gajos, hileras de picos y costura.
- **Modo simple y avanzado**: Estimación de viabilidad, empuje neto (gas ideal), holgura de mecha, aro de alambre y pliegos de papel requeridos.
- **Moldes 2D vectoriales**: Visualización en pantalla y exportación de SVG a escala real con cotas y márgenes de costura.
- **Hojas de trazo y abanicos**: Distribución automática y a escala para impresión en hojas Carta o A4, y trazo en abanico continuo o por mitad simétrica.
- **Diseño gráfico sobre el abanico**: Capas vectoriales (SVG) e imágenes (PNG/JPG) con escalado, rotación, opacidad, reflejos rígidos simétricos, recorte exacto de gajos y exportación de piezas decoradas.
- **Visualizador 3D interactivo**: Previsualización 3D en tiempo real con Three.js (luces solares, controles orbitales, modo día/noche y costuras).
- **Esquemas de pintura y lista de compra**: Asignación de patrones de color para papel china, catálogo personalizable y cálculo de pliegos y paquetes de papel necesarios.

## Requisitos e instalación
1. Python 3.10 o superior (recomendado Python 3.12/3.13).
2. Crear y activar un entorno virtual:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux / macOS:
   source .venv/bin/activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución
Inicia la aplicación con la interfaz en Flet:
```bash
python main.py
```

Para correr las pruebas automatizadas:
```bash
pytest
```

## Estructura del proyecto
- `main.py`: Punto de entrada de la aplicación.
- `app_flet/`: Interfaz de usuario construida con Flet (vistas, tema, controlador reactivo y visor 3D).
- `logic/`: Núcleo de lógica pura (cálculo de moldes, geometría, esquemas de diseño, exportación SVG y modelo 3D).
- `presentacion/`: Capa compartida de formateo de datos y tablas para la UI.
- `datos/`: Catálogo de colores tradicionales de papel china (`colores_papel.json`).
- `tests/`: Batería de pruebas unitarias y de regresión con pytest.

## Calibración y seguridad
> **Nota de calibración física**: Los supuestos físicos del cálculo (temperatura interior de 70 °C, temperatura ambiente de 28 °C, gramaje de papel de 20 g/m² + pegamento, pestaña de boca y holgura mínima de mecha) son estimaciones teóricas que deben calibrarse mediante pruebas prácticas y prototipos controlados.

> **Aviso de seguridad**: Las estimaciones no sustituyen las pruebas; vuela solo en áreas abiertas y conforme a la normativa local.

## Diagnóstico y registros
Los registros de depuración y rendimiento se guardan automáticamente en `logs/globos.log` (rotativo, 1 MB × 3 archivos, UTF-8). Si experimentas algún problema de rendimiento o congelamiento, adjunta este archivo al reportar la incidencia.
