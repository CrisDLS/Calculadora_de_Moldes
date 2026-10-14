# app_flet/vistas/trompo.py
import os
import time
import asyncio
import webbrowser
from typing import Optional, Tuple
import flet as ft
from app_flet.controlador import ControladorTrompo, ViewModelTrompo
from app_flet import tema
from app_flet.vistas.tabla_molde import TablaMoldePersonalizada
from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO
from logic.exportacion.vista_svg import (
    VistaSvg,
    ajustar,
    adaptar_aspecto,
    zoom,
    desplazar,
    aplicar_viewbox,
    extraer_dimensiones_svg,
)
from presentacion.trompo_estrella import tabla_a_texto, TablaMolde
from logic.exportacion.paquete import generar_paquete, guardar_paquete
from logic.diseno.paleta import ColorPapel, cargar_catalogo, color_por_id, exportar_csv, importar_csv, guardar_color_usuario
from logic.diseno.pintura import EsquemaPintura, VariantePico, color_de_cara
from logic.geometria.malla_trompo import Cara
from logic.exportacion.visor3d import exportar_visor_autocontenido

class VistaTrompo(ft.Container):
    def __init__(self, servicio_clipboard=None, servicio_file_picker=None):
        super().__init__()
        self.expand = True
        self.modo_tema = ft.ThemeMode.DARK
        self.paleta = tema.obtener_paleta(self.modo_tema)
        
        self.servicio_clipboard = servicio_clipboard if servicio_clipboard is not None else ft.Clipboard()
        self.file_picker = servicio_file_picker if servicio_file_picker is not None else ft.FilePicker()
        self.ultimo_mensaje_snackbar: Optional[str] = None
        self.ultimo_tiempo_toggle_tema_ms: float = 0.0
        self.conteo_page_updates: int = 0
        self.controlador = ControladorTrompo(estilo_svg=PANTALLA_OSCURO)

        # Estado de zoom y navegación por viewBox
        self.vista_svg: Optional[VistaSvg] = None
        self.vista_base_svg: Optional[VistaSvg] = None
        self._svg_actual_raw: str = ""
        self._ultimo_render_time: float = 0.0
        self._acum_dx: float = 0.0
        self._acum_dy: float = 0.0
        # Telemetría de rendimiento del visor (últimas 20 muestras)
        self._tiempos_actualizacion: list[float] = []
        self._timestamps_actualizacion: list[float] = []
        
        # --- CAMPOS SIMPLES ---
        self.txt_altura = self._crear_campo("Altura total de papel", "950", "cm")
        self.txt_gajos = self._crear_campo("Cantidad de gajos", "30", "")
        self.txt_hileras = self._crear_campo("Hileras de picos", "2", "")
        self.txt_costura = self._crear_campo("Ancho de costura", "1", "cm")
        
        # --- CAMPOS AVANZADOS ---
        self.switch_avanzado = ft.Switch(label="Parámetros avanzados", on_change=self.on_switch_avanzado)
        self.txt_boca = self._crear_campo("Diámetro de boca", "", "cm", "11% de la altura")
        self.txt_pestana = self._crear_campo("Pestaña boca", "", "cm", "0 cm (Sin pestaña)")
        self.txt_d_mecha = self._crear_campo("Diámetro de mecha", "", "cm", "Calculado")
        self.txt_p_mecha = self._crear_campo("Peso de mecha", "", "g", "Opcional")
        
        # Subsección avanzada
        self.txt_alambre = self._crear_campo("Alambre", "", "mm", "1.5 mm")
        self.txt_varillas = self._crear_campo("Varillas", "", "", "2")
        self.txt_llama = self._crear_campo("Altura de llama", "", "cm", "40.0 cm")
        self.txt_holgura = self._crear_campo("Holgura mín.", "", "cm", "10.0 cm")
        
        self.lbl_subseccion_avanzada = ft.Text(
            "Estructura y seguridad",
            weight=ft.FontWeight.BOLD,
            size=14,
            color=ft.Colors.ON_SURFACE_VARIANT
        )
        self.panel_avanzado = ft.Column(
            visible=False,
            controls=[
                self.txt_boca, self.txt_pestana, self.txt_d_mecha, self.txt_p_mecha,
                self.lbl_subseccion_avanzada,
                self.txt_alambre, self.txt_varillas, self.txt_llama, self.txt_holgura
            ]
        )
        
        self.btn_calcular = ft.FilledButton(
            "Calcular", 
            on_click=self.on_calcular,
            style=ft.ButtonStyle(color=ft.Colors.ON_PRIMARY, bgcolor=ft.Colors.PRIMARY)
        )
        self.lbl_error = ft.Text(color=self.paleta.color_error, visible=False)
        self.lbl_desactualizado = ft.Text(
            "Cambiaste los datos: pulsa Calcular",
            color=self.paleta.color_aviso,
            visible=False
        )
        
        # Botón de alternar tema (sol/luna)
        self.btn_tema = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE,
            tooltip="Cambiar a tema claro",
            icon_color=ft.Colors.ON_SURFACE,
            on_click=self.on_toggle_tema,
        )
        self.lbl_tema = ft.Text("Tema", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.lbl_titulo_app = ft.Text("Trompo estrella", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE)

        # Controles de Proyecto (F3)
        self.lbl_nombre_proyecto = ft.Text(
            "Sin título",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.lbl_estado_proyecto = ft.Text(
            "",
            size=11,
            color=self.paleta.color_aviso,
        )
        self.btn_proyecto_nuevo = ft.IconButton(
            icon=ft.Icons.NOTE_ADD_OUTLINED,
            tooltip="Nuevo proyecto",
            icon_size=18,
            on_click=self.on_proyecto_nuevo,
        )
        self.btn_proyecto_abrir = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            tooltip="Abrir proyecto…",
            icon_size=18,
            on_click=self.on_proyecto_abrir,
        )
        self.btn_proyecto_guardar = ft.IconButton(
            icon=ft.Icons.SAVE_OUTLINED,
            tooltip="Guardar proyecto",
            icon_size=18,
            on_click=self.on_proyecto_guardar,
        )
        self.btn_proyecto_guardar_como = ft.IconButton(
            icon=ft.Icons.SAVE_AS_OUTLINED,
            tooltip="Guardar como…",
            icon_size=18,
            on_click=self.on_proyecto_guardar_como,
        )
        
        self.panel_izquierdo = ft.Container(
            width=300,
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=10,
            content=ft.Column(
                controls=[
                    self.lbl_titulo_app,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            controls=[
                                self.txt_altura, self.txt_gajos, self.txt_hileras, self.txt_costura,
                                ft.Divider(color=ft.Colors.OUTLINE),
                                self.switch_avanzado,
                                self.panel_avanzado,
                                ft.Divider(color=ft.Colors.OUTLINE),
                                self.btn_calcular,
                                self.lbl_error,
                            ],
                            spacing=10
                        )
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    self.lbl_nombre_proyecto,
                                    self.lbl_estado_proyecto,
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    self.btn_proyecto_nuevo,
                                    self.btn_proyecto_abrir,
                                    self.btn_proyecto_guardar,
                                    self.btn_proyecto_guardar_como,
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            self.lbl_tema,
                            self.btn_tema,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ]
            )
        )
        
        # --- ZONA DERECHA: PESTAÑAS ---
        # 1. Pestaña Resumen
        self.grid_tarjetas = ft.ResponsiveRow(run_spacing=10)
        self.col_avisos = ft.Column(spacing=5)
        tab_resumen = ft.ListView(
            padding=20,
            controls=[
                self.lbl_desactualizado,
                self.grid_tarjetas,
                ft.Divider(color=ft.Colors.OUTLINE),
                self.col_avisos
            ]
        )

        # 2. Pestaña Tablas
        self.selector_tabla = ft.SegmentedButton(
            selected=["0"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="0", label=ft.Text("Cono superior")),
                ft.Segment(value="1", label=ft.Text("Pico")),
                ft.Segment(value="2", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_pieza_tabla
        )
        self.lbl_vacio_tablas = ft.Container(
            content=ft.Text("Calcula para ver las tablas", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )
        self.lbl_titulo_tabla = ft.Text(size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE)
        self.lbl_resumen_tabla = ft.Text(size=14, color=ft.Colors.ON_SURFACE_VARIANT)
        self.lbl_nota_tabla = ft.Container(
            content=ft.Text(size=13, color=self.paleta.color_aviso, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=6,
            padding=8,
            visible=False,
        )
        self.btn_copiar_tabla = ft.FilledButton(
            "Copiar tabla",
            icon=ft.Icons.COPY,
            on_click=self.on_copiar_tabla
        )
        
        self.tabla_componente = TablaMoldePersonalizada(self.paleta)
        
        self.panel_contenido_tablas = ft.Column(
            expand=True,
            visible=False,
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(controls=[self.lbl_titulo_tabla, self.lbl_resumen_tabla], expand=True),
                        self.btn_copiar_tabla
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                self.lbl_nota_tabla,
                ft.Divider(color=ft.Colors.OUTLINE),
                self.tabla_componente,
            ],
            spacing=10,
        )

        tab_tablas = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row([self.selector_tabla], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_tablas,
                    self.panel_contenido_tablas,
                ]
            )
        )

        # 3. Pestaña Moldes 2D con zoom vectorial por viewBox
        self.selector_molde = ft.SegmentedButton(
            selected=["0"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="0", label=ft.Text("Las 3 piezas")),
                ft.Segment(value="1", label=ft.Text("Cono superior")),
                ft.Segment(value="2", label=ft.Text("Pico")),
                ft.Segment(value="3", label=ft.Text("Cono inferior")),
                ft.Segment(value="4", label=ft.Text("Perfil armado")),
            ],
            on_change=self.on_cambio_pieza_molde
        )
        self.lbl_vacio_moldes = ft.Container(
            content=ft.Text("Calcula para ver los moldes", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )

        # Dimensiones de la zona medida del visor (excluyendo padding y borde)
        self.zona_ancho: float = 600.0
        self.zona_alto: float = 500.0
        self._padding_container: float = 10.0
        self._border_width: float = 1.0

        self.img_svg = ft.Image(src="", fit=ft.BoxFit.CONTAIN, width=self.zona_ancho, height=self.zona_alto)

        self.detector_gestos = ft.GestureDetector(
            content=self.img_svg,
            expand=True,
            on_scroll=self._on_gesture_scroll,
            on_pan_update=self._on_gesture_pan_update,
            on_double_tap=self._on_gesture_double_tap,
        )

        self.container_viewer_svg = ft.Container(
            content=self.detector_gestos,
            border=ft.Border.all(self._border_width, ft.Colors.OUTLINE),
            border_radius=8,
            expand=True,
            padding=self._padding_container,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment(0, 0),
            on_size_change=self._on_container_size_change,
        )

        # Controles de zoom
        self.btn_zoom_out = ft.IconButton(
            icon=ft.Icons.REMOVE,
            tooltip="Alejar",
            icon_size=18,
            on_click=self._on_btn_zoom_out,
        )
        self.lbl_zoom_porcentaje = ft.Text(
            "100 %",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_500,
        )
        self.btn_zoom_in = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Acercar",
            icon_size=18,
            on_click=self._on_btn_zoom_in,
        )
        self.btn_ajustar = ft.TextButton(
            "Ajustar",
            icon=ft.Icons.FIT_SCREEN,
            on_click=self._on_btn_ajustar,
        )
        self.barra_zoom = ft.Row(
            controls=[
                self.btn_zoom_out,
                self.lbl_zoom_porcentaje,
                self.btn_zoom_in,
                self.btn_ajustar,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        self.lbl_instruccion_zoom = ft.Text(
            "Rueda: zoom al cursor · Arrastrar: mover · Doble clic: ajustar",
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )
        self.lbl_pie_moldes = ft.Text(
            "La escala y la hoja de trazo en Carta llegarán en F3.",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )

        # Depuración con GLOBOS_DEBUG=1
        self.debug_mode = os.environ.get("GLOBOS_DEBUG") == "1"
        self.lbl_debug = ft.Text(
            "",
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
            visible=self.debug_mode,
        )

        self.panel_contenido_moldes = ft.Column(
            expand=True,
            visible=False,
            controls=[
                self.container_viewer_svg,
                self.barra_zoom,
                ft.Row([self.lbl_instruccion_zoom], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.lbl_debug], alignment=ft.MainAxisAlignment.CENTER) if self.debug_mode else ft.Container(),
                ft.Row([self.lbl_pie_moldes], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=4,
        )

        tab_2d = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row([self.selector_molde], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_moldes,
                    self.panel_contenido_moldes,
                ]
            )
        )

        # 4. Pestaña Hoja de trazo (F3)
        self.selector_pieza_hoja = ft.SegmentedButton(
            selected=["superior"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="superior", label=ft.Text("Cono superior")),
                ft.Segment(value="pico", label=ft.Text("Pico")),
                ft.Segment(value="inferior", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_pieza_hoja,
        )
        self.selector_lienzo = ft.SegmentedButton(
            selected=["abanico"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="abanico", label=ft.Text("Abanico (recomendado)")),
                ft.Segment(value="separadas", label=ft.Text("Piezas separadas")),
            ],
            on_change=self.on_cambio_lienzo,
        )
        self.segmento_completo_hoja = ft.Segment(value="completo", label=ft.Text("Completo"))
        self.segmento_mitad_hoja = ft.Segment(value="mitad", label=ft.Text("Mitad (espejo)"))
        self.selector_modo_dibujo = ft.SegmentedButton(
            selected=["completo"],
            allow_multiple_selection=False,
            segments=[
                self.segmento_completo_hoja,
                self.segmento_mitad_hoja,
            ],
            on_change=self.on_cambio_modo_dibujo,
        )
        self.btn_sincronizar_conos = ft.OutlinedButton(
            "Usar la misma en ambos conos",
            icon=ft.Icons.SYNC,
            on_click=self.on_sincronizar_conos,
        )
        self.btn_copiar_config_hoja = ft.PopupMenuButton(
            tooltip="Copiar configuración de otra sección",
            icon=ft.Icons.COPY_ALL,
            items=[
                ft.PopupMenuItem(content=ft.Text("Copiar de Cono superior"), on_click=lambda e: self.on_copiar_config("superior")),
                ft.PopupMenuItem(content=ft.Text("Copiar de Cono inferior"), on_click=lambda e: self.on_copiar_config("inferior")),
            ],
        )

        self.dd_repeticion_pico_hoja = ft.Dropdown(
            label="Repetición del pico",
            value="todas_a",
            options=[
                ft.DropdownOption(key="todas_a", text="Todas iguales (A)"),
                ft.DropdownOption(key="alternar_gajo", text="Alternar por gajo"),
                ft.DropdownOption(key="alternar_hilera", text="Alternar por hilera"),
                ft.DropdownOption(key="ajedrez", text="Ajedrez"),
            ],
            on_select=self.on_cambio_repeticion_pico_hoja,
            dense=True,
            width=200,
        )
        self.lbl_resumen_pico = ft.Text(
            "",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_500,
        )
        self.panel_diseno_pico_hoja = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Diseño del pico", size=13, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            self.dd_repeticion_pico_hoja,
                            self.lbl_resumen_pico,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            padding=8,
            visible=False,
        )
        self.dd_modo_esquema = ft.Dropdown(
            label="Modo de diseño",
            value="repeticion",
            options=[
                ft.DropdownOption(key="repeticion", text="Repetición"),
                ft.DropdownOption(key="central_espejo", text="Central con espejo"),
                ft.DropdownOption(key="espejo_total", text="Espejo total"),
                ft.DropdownOption(key="personalizado", text="Personalizado"),
            ],
            on_select=self.on_cambio_esquema_opciones,
            dense=True,
            width=180,
        )
        self.txt_tam_grupo = ft.TextField(
            label="Grupo (G)",
            value="5",
            width=90,
            dense=True,
            on_change=self.on_cambio_esquema_opciones,
        )
        self.txt_ciclo_personalizado = ft.TextField(
            label="Ciclo personalizado",
            value="0, 1, 2E, 1E",
            expand=True,
            dense=True,
            hint_text="ej. 0, 1, 2E, 1E",
            visible=False,
            on_change=self.on_cambio_esquema_opciones,
        )
        self.dd_hoja = ft.Dropdown(
            label="Hoja",
            value="carta",
            options=[
                ft.DropdownOption(key="carta", text="Carta (215.9 × 279.4 mm)"),
                ft.DropdownOption(key="a4", text="A4 (210 × 297 mm)"),
            ],
            on_select=self.on_cambio_hoja_opciones,
            dense=True,
            width=190,
        )
        self.dd_escala = ft.Dropdown(
            label="Escala",
            value="auto",
            options=[
                ft.DropdownOption(key="auto", text="Auto (ajustar)"),
                ft.DropdownOption(key="10", text="1:10"),
                ft.DropdownOption(key="15", text="1:15"),
                ft.DropdownOption(key="20", text="1:20"),
                ft.DropdownOption(key="25", text="1:25"),
                ft.DropdownOption(key="30", text="1:30"),
            ],
            on_select=self.on_cambio_hoja_opciones,
            dense=True,
            width=140,
        )
        self.btn_exportar_hoja = ft.FilledButton(
            "Exportar hoja (SVG)",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.on_exportar_hoja,
        )
        self.btn_exportar_paquete = ft.OutlinedButton(
            "Exportar paquete…",
            icon=ft.Icons.FOLDER_ZIP,
            on_click=self.on_exportar_paquete,
        )
        self.lbl_error_esquema = ft.Text(
            "",
            color=self.paleta.color_error,
            size=13,
            weight=ft.FontWeight.W_500,
            visible=False,
        )
        self.lbl_aviso_hoja = ft.Container(
            content=ft.Text("", size=12, color=self.paleta.color_aviso, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=6,
            padding=6,
            visible=False,
        )
        self.col_resumen_esquema = ft.Column(spacing=2)

        # Visor de la hoja (papel blanco con sombra suave)
        self.zona_ancho_hoja: float = 600.0
        self.zona_alto_hoja: float = 500.0
        self.vista_svg_hoja: Optional[VistaSvg] = None
        self.vista_base_svg_hoja: Optional[VistaSvg] = None
        self._svg_hoja_raw: str = ""

        self.img_svg_hoja = ft.Image(src="", fit=ft.BoxFit.CONTAIN, width=self.zona_ancho_hoja, height=self.zona_alto_hoja)
        self.detector_gestos_hoja = ft.GestureDetector(
            content=self.img_svg_hoja,
            expand=True,
            on_scroll=self._on_gesture_hoja_scroll,
            on_pan_update=self._on_gesture_hoja_pan_update,
            on_double_tap=self._on_gesture_hoja_double_tap,
        )
        self.container_viewer_hoja = ft.Container(
            content=self.detector_gestos_hoja,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=4,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color="#00000022"),
            expand=True,
            padding=self._padding_container,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment(0, 0),
            on_size_change=self._on_container_hoja_size_change,
        )
        self.btn_zoom_out_hoja = ft.IconButton(
            icon=ft.Icons.REMOVE,
            tooltip="Alejar",
            icon_size=18,
            on_click=self._on_btn_zoom_out_hoja,
        )
        self.lbl_zoom_hoja_porcentaje = ft.Text(
            "100 %",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_500,
        )
        self.btn_zoom_in_hoja = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Acercar",
            icon_size=18,
            on_click=self._on_btn_zoom_in_hoja,
        )
        self.btn_ajustar_hoja = ft.TextButton(
            "Ajustar",
            icon=ft.Icons.FIT_SCREEN,
            on_click=self._on_btn_ajustar_hoja,
        )
        self.barra_zoom_hoja = ft.Row(
            controls=[
                self.btn_zoom_out_hoja,
                self.lbl_zoom_hoja_porcentaje,
                self.btn_zoom_in_hoja,
                self.btn_ajustar_hoja,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )
        self.lbl_vacio_hoja = ft.Container(
            content=ft.Text("Calcula para ver la hoja de trazo", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )
        self.panel_contenido_hoja = ft.Column(
            expand=True,
            visible=False,
            controls=[
                self.container_viewer_hoja,
                self.barra_zoom_hoja,
                ft.Row([self.lbl_instruccion_zoom], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=4,
        )

        tab_hoja = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row(
                        controls=[
                            self.selector_pieza_hoja,
                            self.selector_lienzo,
                            self.selector_modo_dibujo,
                            self.btn_sincronizar_conos,
                            self.btn_copiar_config_hoja,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=10,
                    ),
                    self.panel_diseno_pico_hoja,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            self.dd_modo_esquema,
                            self.txt_tam_grupo,
                            self.txt_ciclo_personalizado,
                            self.dd_hoja,
                            self.dd_escala,
                            self.btn_exportar_hoja,
                            self.btn_exportar_paquete,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        wrap=True,
                        spacing=8,
                    ),
                    self.lbl_error_esquema,
                    self.lbl_aviso_hoja,
                    ft.ExpansionTile(
                        title=ft.Text("Resumen de piezas del esquema", size=13, weight=ft.FontWeight.BOLD),
                        expanded=False,
                        dense=True,
                        controls=[
                            ft.Container(
                                padding=8,
                                content=self.col_resumen_esquema,
                            )
                        ],
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_hoja,
                    self.panel_contenido_hoja,
                ],
                spacing=6,
            ),
        )

        # 5. Pestaña Vista 3D (F4)
        self.catalogo_papel = cargar_catalogo()
        self.filtro_marca_actual = "todas"

        # Controles de Cono Superior
        self.dd_modo_sup = ft.Dropdown(
            label="Modo de caras",
            value="liso",
            options=[
                ft.DropdownOption(key="liso", text="Liso (1 color)"),
                ft.DropdownOption(key="alternado", text="Alternado por gajo"),
                ft.DropdownOption(key="bloques", text="Bloques de G gajos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=200,
        )
        self.txt_tam_bloque_sup = ft.TextField(
            label="Tamaño bloque (G)",
            value="5",
            width=140,
            dense=True,
            visible=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.col_colores_sup = ft.Column(spacing=6)
        self.btn_agregar_color_sup = ft.TextButton("Agregar color al ciclo", icon=ft.Icons.ADD, on_click=self.on_agregar_color_sup)

        # Controles de Cono Inferior
        self.chk_mismo_esquema_inf = ft.Checkbox(
            label="Usar el mismo esquema en el cono inferior",
            value=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.dd_modo_inf = ft.Dropdown(
            label="Modo de caras",
            value="liso",
            options=[
                ft.DropdownOption(key="liso", text="Liso (1 color)"),
                ft.DropdownOption(key="alternado", text="Alternado por gajo"),
                ft.DropdownOption(key="bloques", text="Bloques de G gajos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=200,
        )
        self.txt_tam_bloque_inf = ft.TextField(
            label="Tamaño bloque (G)",
            value="5",
            width=140,
            dense=True,
            visible=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.col_colores_inf = ft.Column(spacing=6)
        self.btn_agregar_color_inf = ft.TextButton("Agregar color al ciclo", icon=ft.Icons.ADD, on_click=self.on_agregar_color_inf)
        self.container_controles_inf = ft.Column(
            controls=[
                ft.Row([self.dd_modo_inf, self.txt_tam_bloque_inf], spacing=10),
                self.col_colores_inf,
                self.btn_agregar_color_inf,
            ],
            spacing=6,
        )

        # Controles de Picos (Variantes A y B)
        self.dd_modo_caras_var_a = ft.Dropdown(
            label="Modo de caras (Variante A)",
            value="igual",
            options=[
                ft.DropdownOption(key="igual", text="Igual en las 4 caras"),
                ft.DropdownOption(key="alternado", text="Alternando 2 colores"),
                ft.DropdownOption(key="cuatro", text="4 colores distintos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=220,
        )
        self.col_colores_var_a = ft.Row(wrap=True, spacing=10)

        self.chk_usar_var_b = ft.Checkbox(
            label="Usar Variante B",
            value=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.dd_repeticion_picos = ft.Dropdown(
            label="Repetición entre pirámides",
            value="todas_a",
            options=[
                ft.DropdownOption(key="todas_a", text="Todas A"),
                ft.DropdownOption(key="alternar_gajo", text="Alternar por gajo (A, B)"),
                ft.DropdownOption(key="alternar_hilera", text="Alternar por hilera (A, B)"),
                ft.DropdownOption(key="ajedrez", text="Ajedrez (A, B)"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=240,
        )
        self.dd_modo_caras_var_b = ft.Dropdown(
            label="Modo de caras (Variante B)",
            value="igual",
            options=[
                ft.DropdownOption(key="igual", text="Igual en las 4 caras"),
                ft.DropdownOption(key="alternado", text="Alternando 2 colores"),
                ft.DropdownOption(key="cuatro", text="4 colores distintos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=220,
        )
        self.col_colores_var_b = ft.Row(wrap=True, spacing=10)
        self.panel_variante_b = ft.Column(
            visible=False,
            controls=[
                self.dd_modo_caras_var_b,
                self.col_colores_var_b,
            ],
            spacing=6,
        )

        # Filtro de marca y gestión de catálogo CSV
        self.dd_filtro_marca = ft.Dropdown(
            label="Filtrar por marca",
            value="todas",
            options=[ft.DropdownOption(key="todas", text="Todas las marcas")],
            on_select=self.on_cambio_filtro_marca,
            dense=True,
            width=180,
        )
        self.btn_agregar_color_catalogo = ft.OutlinedButton(
            "Nuevo color…",
            icon=ft.Icons.COLOR_LENS,
            on_click=self.on_dialogo_agregar_color,
        )
        self.btn_importar_csv = ft.OutlinedButton(
            "Importar CSV…",
            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
            on_click=self.on_importar_catalogo_csv,
        )
        self.btn_exportar_csv = ft.OutlinedButton(
            "Exportar CSV…",
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            on_click=self.on_exportar_catalogo_csv,
        )

        # Vista previa interactiva de patrones (2D canvas/stripes)
        self.fila_previa_sup = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)
        self.col_previa_picos = ft.Column(spacing=2)
        self.fila_previa_inf = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)

        # Sliders y configuración de compra
        self.txt_pliego_ancho = ft.TextField(
            label="Ancho pliego (cm)",
            value="50",
            width=140,
            dense=True,
            on_change=self.on_cambio_tam_pliego,
        )
        self.txt_pliego_alto = ft.TextField(
            label="Alto pliego (cm)",
            value="70",
            width=140,
            dense=True,
            on_change=self.on_cambio_tam_pliego,
        )
        self.txt_pliegos_paquete = ft.TextField(
            label="Pliegos por paquete",
            value="100",
            width=160,
            dense=True,
            on_change=self.on_cambio_pliegos_paquete,
        )
        self.lbl_aviso_colores = ft.Text(
            "Colores en pantalla aproximados: compara con tu pliego",
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            italic=True,
        )

        self.btn_abrir_visor_3d = ft.FilledButton(
            "Abrir visor 3D en navegador",
            icon=ft.Icons.OPEN_IN_BROWSER,
            on_click=self.on_abrir_visor_3d,
        )
        self.btn_exportar_visor_3d = ft.OutlinedButton(
            "Exportar visor 3D (.html)…",
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            on_click=self.on_exportar_visor_3d,
        )
        self.btn_copiar_compra = ft.FilledButton(
            "Copiar lista de compra",
            icon=ft.Icons.COPY,
            on_click=self.on_copiar_lista_compra,
        )

        self.tabla_compra = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Color", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Superior", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Pico", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Inferior", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Total piezas", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Área (m²)", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Pliegos", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Paquetes", weight=ft.FontWeight.BOLD), numeric=True),
            ],
            rows=[],
            heading_row_height=36,
            data_row_min_height=32,
            data_row_max_height=36,
            column_spacing=16,
        )

        self.lbl_vacio_3d = ft.Container(
            content=ft.Text("Calcula para ver la vista 3D y lista de compra", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )

        self.panel_contenido_3d = ft.Column(
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Patrones y colores del globo", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                self.dd_filtro_marca,
                                self.btn_agregar_color_catalogo,
                                self.btn_importar_csv,
                                self.btn_exportar_csv,
                            ],
                            spacing=6,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                self.lbl_aviso_colores,
                ft.Divider(color=ft.Colors.OUTLINE),

                # Sección Cono Superior
                ft.Text("1. Cono Superior", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_modo_sup, self.txt_tam_bloque_sup], spacing=10),
                self.col_colores_sup,
                self.btn_agregar_color_sup,
                ft.Divider(color=ft.Colors.OUTLINE),

                # Sección Cono Inferior
                ft.Text("2. Cono Inferior", size=14, weight=ft.FontWeight.BOLD),
                self.chk_mismo_esquema_inf,
                self.container_controles_inf,
                ft.Divider(color=ft.Colors.OUTLINE),

                # Sección Picos
                ft.Text("3. Picos (Pirámides)", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_repeticion_picos, self.chk_usar_var_b], spacing=10),
                ft.Text("Variante A:", weight=ft.FontWeight.BOLD, size=12),
                self.dd_modo_caras_var_a,
                self.col_colores_var_a,
                self.panel_variante_b,
                ft.Divider(color=ft.Colors.OUTLINE),

                # Vista Previa 2D
                ft.Text("Vista previa del patrón desplegado (por gajo)", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Cono Superior:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.fila_previa_sup, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Text("Hileras de Picos:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.col_previa_picos, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Text("Cono Inferior:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.fila_previa_inf, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Divider(color=ft.Colors.OUTLINE),

                # Lanzadores 3D
                ft.Text("Visor 3D interactivo (three.js)", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Abre el modelo 3D en tu navegador local con luces realistas, rotación orbital, azimut/elevación y modos día/noche.", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row(
                    controls=[self.btn_abrir_visor_3d, self.btn_exportar_visor_3d],
                    spacing=10,
                ),
                ft.Divider(color=ft.Colors.OUTLINE),

                # Lista de Compra
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Lista de compra de papel china", size=14, weight=ft.FontWeight.BOLD),
                                ft.Row(
                                    controls=[
                                        self.txt_pliego_ancho,
                                        self.txt_pliego_alto,
                                        self.txt_pliegos_paquete,
                                    ],
                                    spacing=10,
                                ),
                                self.lbl_aviso_colores,
                            ],
                            spacing=4,
                        ),
                        self.btn_copiar_compra,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=self.tabla_compra,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=8,
                ),
            ],
            spacing=8,
        )

        tab_3d = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    self.lbl_vacio_3d,
                    self.panel_contenido_3d,
                ],
            ),
        )

        # --- 5. PESTAÑA DISEÑO (F6a) ---
        self.selector_seccion_diseno = ft.SegmentedButton(
            selected=["superior"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="superior", label=ft.Text("Cono superior")),
                ft.Segment(value="pico", label=ft.Text("Pico")),
                ft.Segment(value="inferior", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_seccion_diseno,
        )
        self.selector_variante_pico_diseno = ft.SegmentedButton(
            selected=["A"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="A", label=ft.Text("Variante A")),
                ft.Segment(value="B", label=ft.Text("Variante B")),
            ],
            visible=False,
            on_change=self.on_cambio_variante_diseno,
        )
        self.segmento_completo_diseno = ft.Segment(value="completo", label=ft.Text("Lienzo completo"))
        self.segmento_mitad_diseno = ft.Segment(value="mitad", label=ft.Text("Mitad (espejo)"))
        self.selector_lienzo_diseno = ft.SegmentedButton(
            selected=["completo"],
            allow_multiple_selection=False,
            segments=[
                self.segmento_completo_diseno,
                self.segmento_mitad_diseno,
            ],
            on_change=self.on_cambio_lienzo_diseno,
        )

        # Visor interactivo del diseño
        self.zona_ancho_diseno: float = 600.0
        self.zona_alto_diseno: float = 500.0
        self.vista_svg_diseno: Optional[VistaSvg] = None
        self.vista_base_svg_diseno: Optional[VistaSvg] = None
        self._svg_diseno_raw: str = ""

        self.img_svg_diseno = ft.Image(src="", fit=ft.BoxFit.CONTAIN, width=self.zona_ancho_diseno, height=self.zona_alto_diseno)
        self.detector_gestos_diseno = ft.GestureDetector(
            content=self.img_svg_diseno,
            expand=True,
            on_scroll=self._on_gesture_diseno_scroll,
            on_pan_update=self._on_gesture_diseno_pan_update,
            on_double_tap=self._on_gesture_diseno_double_tap,
        )
        self.container_viewer_diseno = ft.Container(
            content=self.detector_gestos_diseno,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=4,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color="#00000022"),
            expand=True,
            padding=self._padding_container,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment(0, 0),
            on_size_change=self._on_container_diseno_size_change,
        )
        self.btn_zoom_out_diseno = ft.IconButton(
            icon=ft.Icons.REMOVE,
            tooltip="Alejar",
            icon_size=18,
            on_click=self._on_btn_zoom_out_diseno,
        )
        self.lbl_zoom_diseno_porcentaje = ft.Text(
            "100 %",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_500,
        )
        self.btn_zoom_in_diseno = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Acercar",
            icon_size=18,
            on_click=self._on_btn_zoom_in_diseno,
        )
        self.btn_ajustar_diseno = ft.TextButton(
            "Ajustar",
            icon=ft.Icons.FIT_SCREEN,
            on_click=self._on_btn_ajustar_diseno,
        )
        self.barra_zoom_diseno = ft.Row(
            controls=[
                self.btn_zoom_out_diseno,
                self.lbl_zoom_diseno_porcentaje,
                self.btn_zoom_in_diseno,
                self.btn_ajustar_diseno,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        # Barra superior de herramientas del visor de diseño
        self.chk_ver_cuadricula = ft.Checkbox(
            label="Cuadrícula",
            value=True,
            on_change=self.on_toggle_ver_cuadricula,
        )
        self.chk_ver_rotulos = ft.Checkbox(
            label="Rótulos",
            value=False,
            on_change=self.on_toggle_ver_rotulos,
        )
        self.chk_ver_costuras = ft.Checkbox(
            label="Costuras",
            value=True,
            on_change=self.on_toggle_ver_costuras,
        )
        self.chk_mostrar_reflejo = ft.Checkbox(
            label="Mostrar reflejo",
            value=True,
            on_change=self.on_toggle_mostrar_reflejo,
        )
        self.modo_interaccion_diseno = "navegar"
        self.selector_interaccion_diseno = ft.SegmentedButton(
            selected=["navegar"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="navegar", label=ft.Text("Navegar"), icon=ft.Icon(ft.Icons.PAN_TOOL, size=16)),
                ft.Segment(value="mover", label=ft.Text("Mover capa"), icon=ft.Icon(ft.Icons.TOUCH_APP, size=16)),
            ],
            on_change=self.on_cambio_modo_interaccion,
        )
        self.barra_herramientas_diseno = ft.Row(
            controls=[
                ft.Row([self.chk_ver_cuadricula, self.chk_ver_rotulos, self.chk_ver_costuras, self.chk_mostrar_reflejo], spacing=4),
                self.selector_interaccion_diseno,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

        # Panel lateral de capas
        self.btn_anadir_capa = ft.FilledButton(
            "Añadir capa…",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            on_click=self.on_anadir_capa_click,
        )
        self.col_lista_capas = ft.Column(spacing=4)

        # Inspector de capa seleccionada
        self.txt_nombre_capa = ft.TextField(label="Nombre", dense=True, on_change=self.on_nombre_capa_change)
        self.txt_pos_x = ft.TextField(label="Posición X (cm)", dense=True, width=120, on_change=self.on_pos_x_change)
        self.txt_pos_y = ft.TextField(label="Posición Y (cm)", dense=True, width=120, on_change=self.on_pos_y_change)
        self.txt_ancho_capa = ft.TextField(label="Ancho (cm)", dense=True, width=120, on_change=self.on_ancho_capa_change)
        self.txt_alto_capa = ft.TextField(label="Alto (cm)", dense=True, width=120, on_change=self.on_alto_capa_change)
        self.chk_proporcion = ft.Checkbox(label="Mantener proporción", value=True, on_change=self.on_proporcion_change)
        self.slider_rotacion = ft.Slider(min=-180, max=180, divisions=72, label="{value}°", on_change=self.on_rotacion_change)
        self.lbl_rotacion_val = ft.Text("0°", size=12)
        self.btn_reflejo_h = ft.IconButton(icon=ft.Icons.FLIP, tooltip="Reflejo horizontal", on_click=self.on_reflejo_h_click)
        self.btn_reflejo_v = ft.IconButton(icon=ft.Icons.FLIP_CAMERA_ANDROID, tooltip="Reflejo vertical", on_click=self.on_reflejo_v_click)
        self.slider_opacidad = ft.Slider(min=0.0, max=1.0, divisions=20, label="{value}", on_change=self.on_opacidad_change)
        self.lbl_opacidad_val = ft.Text("100%", size=12)

        # Botones de ajuste rápido (6 modos)
        self.btn_ajustar_cubrir = ft.TextButton("Cubrir", icon=ft.Icons.ZOOM_OUT_MAP, on_click=self.on_ajustar_cubrir_click, tooltip="Escala conservando proporción para cubrir la ventana")
        self.btn_ajustar_contener = ft.TextButton("Contener", icon=ft.Icons.FIT_SCREEN, on_click=self.on_ajustar_contener_click, tooltip="Escala conservando proporción para caber completo")
        self.btn_ajustar_estirar = ft.TextButton("Estirar", icon=ft.Icons.OPEN_IN_FULL, on_click=self.on_ajustar_estirar_click, tooltip="Llena la ventana estirando ancho y alto")
        self.btn_ajustar_ancho = ft.TextButton("Ancho", icon=ft.Icons.SWAP_HORIZ, on_click=self.on_ajustar_ancho_click, tooltip="Ajusta al ancho del abanico")
        self.btn_ajustar_alto = ft.TextButton("Alto", icon=ft.Icons.SWAP_VERT, on_click=self.on_ajustar_alto_click, tooltip="Ajusta al alto del abanico")
        self.btn_centrar_capa = ft.TextButton("Centrar", icon=ft.Icons.CENTER_FOCUS_STRONG, on_click=self.on_centrar_capa_click, tooltip="Centra la capa en el abanico")

        # Botones de empuje rápido (nudge)
        self.btn_nudge_left = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=18, tooltip="Mover izq. (-1 cm)", on_click=lambda e: self._empujar_capa(dx=-1.0))
        self.btn_nudge_right = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, icon_size=18, tooltip="Mover der. (+1 cm)", on_click=lambda e: self._empujar_capa(dx=1.0))
        self.btn_nudge_up = ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_size=18, tooltip="Mover arriba (+1 cm)", on_click=lambda e: self._empujar_capa(dy=1.0))
        self.btn_nudge_down = ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_size=18, tooltip="Mover abajo (-1 cm)", on_click=lambda e: self._empujar_capa(dy=-1.0))

        self.btn_rot_m5 = ft.TextButton("-5°", on_click=lambda e: self._empujar_capa(drot=-5.0), tooltip="Girar 5° contra reloj")
        self.btn_rot_p5 = ft.TextButton("+5°", on_click=lambda e: self._empujar_capa(drot=5.0), tooltip="Girar 5° a favor de reloj")
        self.btn_rot_0 = ft.TextButton("0°", on_click=lambda e: self._fijar_rotacion_0(), tooltip="Restablecer rotación a 0°")

        self.panel_inspector_capa = ft.Column(
            visible=False,
            spacing=8,
            controls=[
                ft.Text("Propiedades de la capa", weight=ft.FontWeight.BOLD, size=14),
                self.txt_nombre_capa,
                ft.Row([self.txt_pos_x, self.txt_pos_y], spacing=8),
                ft.Row(
                    controls=[
                        ft.Text("Mover (1 cm):", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                        self.btn_nudge_left,
                        self.btn_nudge_down,
                        self.btn_nudge_up,
                        self.btn_nudge_right,
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row([self.txt_ancho_capa, self.txt_alto_capa], spacing=8),
                self.chk_proporcion,
                ft.Text("Ajuste rápido al abanico:", size=12, weight=ft.FontWeight.W_500),
                ft.Row([self.btn_ajustar_cubrir, self.btn_ajustar_contener, self.btn_ajustar_estirar], wrap=True, spacing=4),
                ft.Row([self.btn_ajustar_ancho, self.btn_ajustar_alto, self.btn_centrar_capa], wrap=True, spacing=4),
                ft.Text("Rotación:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row([self.slider_rotacion, self.lbl_rotacion_val], spacing=4),
                ft.Row([self.btn_rot_m5, self.btn_rot_0, self.btn_rot_p5], spacing=4),
                ft.Row([self.btn_reflejo_h, self.btn_reflejo_v], spacing=8),
                ft.Text("Opacidad:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row([self.slider_opacidad, self.lbl_opacidad_val], spacing=4),
            ],
        )

        self.btn_exportar_abanico = ft.FilledButton("Exportar abanico con diseño (SVG)", icon=ft.Icons.FILE_DOWNLOAD, on_click=self.on_exportar_abanico_click)
        self.btn_exportar_gajos = ft.FilledButton("Exportar piezas con diseño…", icon=ft.Icons.FOLDER_OPEN, on_click=self.on_exportar_gajos_click)
        self.btn_exportar_hoja_diseno = ft.FilledButton("Exportar hoja Carta con diseño", icon=ft.Icons.IMAGE, on_click=self.on_exportar_hoja_diseno_click)

        self.panel_lateral_diseno = ft.Container(
            width=340,
            padding=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            content=ft.ListView(
                spacing=10,
                controls=[
                    ft.Text("Sección y Lienzo", size=14, weight=ft.FontWeight.BOLD),
                    self.selector_seccion_diseno,
                    self.selector_variante_pico_diseno,
                    self.selector_lienzo_diseno,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            ft.Text("Capas de diseño", size=14, weight=ft.FontWeight.BOLD),
                            self.btn_anadir_capa,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.col_lista_capas,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.panel_inspector_capa,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Text("Exportación", size=14, weight=ft.FontWeight.BOLD),
                    self.btn_exportar_abanico,
                    self.btn_exportar_gajos,
                    self.btn_exportar_hoja_diseno,
                ],
            ),
        )

        self.lbl_vacio_diseno = ft.Container(
            content=ft.Text("Calcula para editar el diseño", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )

        self.panel_contenido_diseno = ft.Row(
            expand=True,
            visible=False,
            controls=[
                self.panel_lateral_diseno,
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE),
                ft.Column(
                    expand=True,
                    controls=[
                        self.barra_herramientas_diseno,
                        self.container_viewer_diseno,
                        self.barra_zoom_diseno,
                        ft.Row([self.lbl_instruccion_zoom], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=4,
                ),
            ],
            spacing=10,
        )

        tab_diseno = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    self.lbl_vacio_diseno,
                    self.panel_contenido_diseno,
                ],
            ),
        )

        # Tabs generales (6 pestañas)
        self.tabs = ft.Tabs(
            selected_index=0,
            length=6,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Resumen", icon=ft.Icons.DASHBOARD_OUTLINED),
                            ft.Tab(label="Tablas de moldes", icon=ft.Icons.TABLE_CHART_OUTLINED),
                            ft.Tab(label="Moldes 2D", icon=ft.Icons.IMAGE_OUTLINED),
                            ft.Tab(label="Hoja de trazo", icon=ft.Icons.DESCRIPTION_OUTLINED),
                            ft.Tab(label="Diseño", icon=ft.Icons.BRUSH_OUTLINED),
                            ft.Tab(label="Vista 3D", icon=ft.Icons.VIEW_IN_AR_OUTLINED),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[tab_resumen, tab_tablas, tab_2d, tab_hoja, tab_diseno, tab_3d],
                    ),
                ],
            ),
        )


        self.panel_derecho = ft.Container(
            expand=True,
            content=self.tabs
        )
        
        self.content = ft.Row(
            expand=True,
            controls=[self.panel_izquierdo, self.panel_derecho],
            spacing=0
        )
        
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _crear_campo(self, label: str, default_val: str, unidad: str, hint: str = "") -> ft.TextField:
        txt = ft.TextField(
            label=label,
            value=default_val,
            suffix=ft.Text(unidad) if unidad else None,
            hint_text=hint if hint else None,
            on_change=self.on_change_input,
            dense=True
        )
        return txt

    @property
    def obtener_pagina(self) -> Optional[ft.Page]:
        try:
            return self.page
        except RuntimeError:
            return None

    def on_toggle_tema(self, e):
        t0 = time.perf_counter()
        if self.modo_tema == ft.ThemeMode.DARK:
            self.modo_tema = ft.ThemeMode.LIGHT
            self.btn_tema.icon = ft.Icons.DARK_MODE
            self.btn_tema.tooltip = "Cambiar a tema oscuro"
            estilo = PANTALLA_CLARO
        else:
            self.modo_tema = ft.ThemeMode.DARK
            self.btn_tema.icon = ft.Icons.LIGHT_MODE
            self.btn_tema.tooltip = "Cambiar a tema claro"
            estilo = PANTALLA_OSCURO

        self.paleta = tema.obtener_paleta(self.modo_tema)

        # Regenerar SVG con el nuevo estilo sin recalcular el modelo
        self.controlador.cambiar_estilo(estilo)
        self._actualizar_estilos_paleta()

        # Sincronizar datos a la vista difiriendo update()
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, diferir_update=True)

        page = self.obtener_pagina
        if page:
            page.theme_animation_style = ft.AnimationStyle.no_animation()
            page.theme_mode = self.modo_tema
            page.theme = tema.tema_claro
            page.dark_theme = tema.tema_oscuro
            self.conteo_page_updates += 1
            page.update()
        else:
            try:
                self.update()
            except RuntimeError:
                pass

        t1 = time.perf_counter()
        self.ultimo_tiempo_toggle_tema_ms = (t1 - t0) * 1000.0

    def _actualizar_estilos_paleta(self):
        self.lbl_error.color = self.paleta.color_error
        self.lbl_desactualizado.color = self.paleta.color_aviso
        self.lbl_nota_tabla.content.color = self.paleta.color_aviso
        self.tabla_componente.actualizar_paleta(self.paleta)

    def on_change_input(self, e):
        self._leer_vista_a_controlador()
        self.controlador.marcar_desactualizado()
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm)

    def on_switch_avanzado(self, e):
        self.panel_avanzado.visible = self.switch_avanzado.value
        self._leer_vista_a_controlador()
        self.controlador.marcar_desactualizado()
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm)

    def on_cambio_pieza_tabla(self, e):
        self._renderizar_tabla_seleccionada()
        try:
            self.update()
        except RuntimeError:
            pass

    def on_cambio_pieza_molde(self, e):
        sel_molde = self.selector_molde.selected[0] if self.selector_molde.selected else "0"
        if sel_molde == "4":
            self.lbl_vacio_moldes.content.value = "Calcula para ver el perfil"
        else:
            self.lbl_vacio_moldes.content.value = "Calcula para ver los moldes"

        self._renderizar_molde_seleccionado(reset_vista=True)
        try:
            self.update()
        except RuntimeError:
            pass

    def on_copiar_tabla(self, e):
        idx = int(self.selector_tabla.selected[0]) if self.selector_tabla.selected else 0
        if not (self.controlador.tablas and idx < len(self.controlador.tablas)):
            self._mostrar_snackbar("No se pudo copiar")
            return

        tabla = self.controlador.tablas[idx]
        texto = tabla_a_texto(tabla)

        # Usar servicio inyectado
        copia_exitosa = False
        page = self.obtener_pagina
        try:
            # Asegurar registro del servicio si hay página y es ft.Service
            if page and isinstance(self.servicio_clipboard, ft.Service):
                if self.servicio_clipboard not in page.services:
                    page.services.append(self.servicio_clipboard)

            if hasattr(self.servicio_clipboard, "set"):
                res = self.servicio_clipboard.set(texto)
                if asyncio.iscoroutine(res):
                    if page:
                        page.run_task(self.servicio_clipboard.set, texto)
                    else:
                        asyncio.run(res)
                copia_exitosa = True
        except Exception:
            copia_exitosa = False

        if copia_exitosa:
            self._mostrar_snackbar("Tabla copiada al portapapeles")
        else:
            self._mostrar_snackbar("No se pudo copiar")

    def _mostrar_snackbar(self, mensaje: str):
        self.ultimo_mensaje_snackbar = mensaje
        page = self.obtener_pagina
        if page:
            try:
                snack = ft.SnackBar(ft.Text(mensaje), open=True)
                page.overlay.append(snack)
                page.update()
            except Exception:
                pass

    def _leer_vista_a_controlador(self):
        self.controlador.altura = self.txt_altura.value
        self.controlador.gajos = self.txt_gajos.value
        self.controlador.hileras = self.txt_hileras.value
        self.controlador.costura = self.txt_costura.value
        self.controlador.avanzado = self.switch_avanzado.value
        
        self.controlador.boca = self.txt_boca.value
        self.controlador.pestana = self.txt_pestana.value
        self.controlador.diametro_mecha = self.txt_d_mecha.value
        self.controlador.peso_mecha = self.txt_p_mecha.value
        self.controlador.alambre = self.txt_alambre.value
        self.controlador.varillas = self.txt_varillas.value
        self.controlador.altura_llama = self.txt_llama.value
        self.controlador.holgura = self.txt_holgura.value

    def on_calcular(self, e):
        self._leer_vista_a_controlador()
        vm = self.controlador.calcular()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def _renderizar_tabla_seleccionada(self):
        if not self.controlador.tablas:
            return
        idx = int(self.selector_tabla.selected[0]) if self.selector_tabla.selected else 0
        if idx >= len(self.controlador.tablas):
            return
        tabla: TablaMolde = self.controlador.tablas[idx]

        self.lbl_titulo_tabla.value = tabla.titulo
        self.lbl_resumen_tabla.value = tabla.resumen

        if tabla.nota:
            self.lbl_nota_tabla.content.value = f"Nota: {tabla.nota}"
            self.lbl_nota_tabla.visible = True
        else:
            self.lbl_nota_tabla.visible = False

        self.tabla_componente.cargar_tabla(tabla, self.paleta)

    def _porcentaje_zoom(self) -> float:
        if not self.vista_base_svg or not self.vista_svg or self.vista_svg.ancho <= 0:
            return 100.0
        return (self.vista_base_svg.ancho / self.vista_svg.ancho) * 100.0

    def _limites_zoom(self) -> Tuple[float, float]:
        if not self.vista_base_svg:
            return (1.0, 1000.0)
        # Máximo 40x de acercamiento, mínimo que encaje la vista base
        ancho_min = self.vista_base_svg.ancho / 40.0
        ancho_max = self.vista_base_svg.ancho * 1.5
        return (ancho_min, ancho_max)

    def _on_container_size_change(self, e):
        # Medir tamaño real del contenedor descontando padding y borde
        w_raw = getattr(e, "width", 0.0) or 0.0
        h_raw = getattr(e, "height", 0.0) or 0.0
        if w_raw <= 0 or h_raw <= 0:
            return

        descuento_w = 2.0 * (self._padding_container + self._border_width)
        descuento_h = 2.0 * (self._padding_container + self._border_width)
        w_util = max(50.0, w_raw - descuento_w)
        h_util = max(50.0, h_raw - descuento_h)

        if abs(w_util - self.zona_ancho) < 0.5 and abs(h_util - self.zona_alto) < 0.5:
            return

        self.zona_ancho = w_util
        self.zona_alto = h_util
        self.img_svg.width = self.zona_ancho
        self.img_svg.height = self.zona_alto

        aspecto_zona = self.zona_ancho / self.zona_alto

        if self._svg_actual_raw:
            w_nat, h_nat = extraer_dimensiones_svg(self._svg_actual_raw)
            self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            if self.vista_svg:
                self.vista_svg = adaptar_aspecto(self.vista_svg, aspecto_zona)
            else:
                self.vista_svg = self.vista_base_svg
            self._actualizar_imagen_zoom(force=True)

    def _renderizar_molde_seleccionado(self, reset_vista: bool = False):
        vm = self.controlador.get_view_model()
        sel = self.selector_molde.selected[0] if self.selector_molde.selected else "0"
        svg_str = ""
        if sel == "0":
            svg_str = vm.svg_conjunto
        elif sel == "1":
            svg_str = vm.svg_superior
        elif sel == "2":
            svg_str = vm.svg_pico
        elif sel == "3":
            svg_str = vm.svg_inferior
        elif sel == "4":
            svg_str = vm.svg_perfil

        self._svg_actual_raw = svg_str

        if not svg_str:
            self.img_svg.src = ""
            return

        aspecto_zona = self.zona_ancho / self.zona_alto if self.zona_alto > 0 else 1.0
        w_nat, h_nat = extraer_dimensiones_svg(svg_str)
        if reset_vista or not self.vista_svg or not self.vista_base_svg:
            self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            self.vista_svg = self.vista_base_svg

        svg_con_viewbox = aplicar_viewbox(svg_str, self.vista_svg)
        self.img_svg.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_porcentaje.value = f"{self._porcentaje_zoom():.0f} %"
        self._actualizar_debug()

    def _actualizar_debug(self):
        if not self.debug_mode or not self.vista_svg:
            return
        z_str = f"zona {self.zona_ancho:.0f}×{self.zona_alto:.0f} px"
        img_str = f"imagen {self.img_svg.width:.0f}×{self.img_svg.height:.0f}"
        v_str = f"vista {self.vista_svg.x:.1f},{self.vista_svg.y:.1f},{self.vista_svg.ancho:.1f},{self.vista_svg.alto:.1f}"
        zoom_str = f"zoom {self._porcentaje_zoom():.0f} %"

        media_ms = (sum(self._tiempos_actualizacion) / len(self._tiempos_actualizacion)) if self._tiempos_actualizacion else 0.0
        now = time.perf_counter()
        # Actualizaciones en el último segundo
        recientes = [t for t in self._timestamps_actualizacion if now - t <= 1.0]
        fps = len(recientes)
        telem_str = f"{media_ms:.1f} ms/act (media 20) · {fps} act/s"

        self.lbl_debug.value = f"{z_str} · {img_str} · {v_str} · {zoom_str} · {telem_str}"
        try:
            self.lbl_debug.update()
        except Exception:
            pass

    def _actualizar_imagen_zoom(self, force: bool = False, t_inicio_evento: Optional[float] = None):
        if not self._svg_actual_raw or not self.vista_svg:
            return
        now = time.perf_counter()
        if not force and (now - self._ultimo_render_time < (1.0 / 30.0)):
            return
        self._ultimo_render_time = now

        svg_con_viewbox = aplicar_viewbox(self._svg_actual_raw, self.vista_svg)
        self.img_svg.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_porcentaje.value = f"{self._porcentaje_zoom():.0f} %"

        # Registrar telemetría si se pasó t_inicio_evento o medir el coste del renderizado
        t_ref = t_inicio_evento if t_inicio_evento is not None else now
        try:
            self.img_svg.update()
            self.lbl_zoom_porcentaje.update()
        except Exception:
            pass

        t_fin = time.perf_counter()
        dt_ms = (t_fin - t_ref) * 1000.0
        self._tiempos_actualizacion.append(dt_ms)
        if len(self._tiempos_actualizacion) > 20:
            self._tiempos_actualizacion.pop(0)
        self._timestamps_actualizacion.append(t_fin)
        if len(self._timestamps_actualizacion) > 50:
            self._timestamps_actualizacion.pop(0)

        self._actualizar_debug()

    def _on_gesture_scroll(self, e: ft.ScrollEvent):
        t_inicio = time.perf_counter()
        if not self.vista_svg:
            return
        # Rueda del ratón: scroll_delta.y < 0 acerca (zoom in), > 0 aleja (zoom out)
        delta_y = getattr(e, "scroll_delta", None)
        factor = 1.15
        if delta_y and hasattr(delta_y, "y"):
            if delta_y.y > 0:
                factor = 1.0 / 1.15
            elif delta_y.y < 0:
                factor = 1.15

        fx = 0.5
        fy = 0.5
        local_pos = getattr(e, "local_position", None)
        if local_pos and hasattr(local_pos, "x") and hasattr(local_pos, "y"):
            if self.zona_ancho > 0 and self.zona_alto > 0:
                fx = max(0.01, min(0.99, local_pos.x / self.zona_ancho))
                fy = max(0.01, min(0.99, local_pos.y / self.zona_alto))

        self.vista_svg = zoom(
            self.vista_svg,
            factor=factor,
            fx=fx,
            fy=fy,
            limites=self._limites_zoom()
        )
        self._actualizar_imagen_zoom(t_inicio_evento=t_inicio)

    def _on_gesture_pan_update(self, e: ft.DragUpdateEvent):
        t_inicio = time.perf_counter()
        if not self.vista_svg or not self.vista_base_svg:
            return
        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if delta and hasattr(delta, "x") and hasattr(delta, "y"):
            w_control = max(50.0, self.zona_ancho)
            h_control = max(50.0, self.zona_alto)
            dx = delta.x * (self.vista_svg.ancho / w_control)
            dy = delta.y * (self.vista_svg.alto / h_control)
            limites_cont = (self.vista_base_svg.ancho, self.vista_base_svg.alto)
            self.vista_svg = desplazar(self.vista_svg, dx=dx, dy=dy, limites_contenido=limites_cont)
            self._actualizar_imagen_zoom(t_inicio_evento=t_inicio)

    def _on_gesture_double_tap(self, e):
        self._ajustar_vista()

    def _on_btn_zoom_in(self, e):
        if not self.vista_svg:
            return
        self.vista_svg = zoom(self.vista_svg, factor=1.25, fx=0.5, fy=0.5, limites=self._limites_zoom())
        self._actualizar_imagen_zoom(force=True)

    def _on_btn_zoom_out(self, e):
        if not self.vista_svg:
            return
        self.vista_svg = zoom(self.vista_svg, factor=1.0 / 1.25, fx=0.5, fy=0.5, limites=self._limites_zoom())
        self._actualizar_imagen_zoom(force=True)

    def _on_btn_ajustar(self, e):
        self._ajustar_vista()

    def _ajustar_vista(self):
        if not self._svg_actual_raw:
            return
        w_nat, h_nat = extraer_dimensiones_svg(self._svg_actual_raw)
        aspecto_zona = self.zona_ancho / self.zona_alto if self.zona_alto > 0 else 1.0
        self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
        self.vista_svg = self.vista_base_svg
        self._actualizar_imagen_zoom(force=True)

    def _sync_controlador_a_vista(self, vm: ViewModelTrompo, diferir_update: bool = False, reset_zoom: bool = False):
        # 1. Error
        if vm.mensaje_error:
            self.lbl_error.value = vm.mensaje_error
            self.lbl_error.visible = True
        else:
            self.lbl_error.visible = False
            
        # 2. Desactualizado
        self.lbl_desactualizado.visible = vm.desactualizado
        
        # 3. Tarjetas de resumen
        self.grid_tarjetas.controls.clear()
        if not vm.desactualizado:
            for tj in vm.tarjetas:
                bg_color = ft.Colors.SURFACE_CONTAINER
                text_color = ft.Colors.ON_SURFACE
                if tj.etiqueta == "Viable":
                    bg_color = self.paleta.color_ok if tj.valor == "Sí" else self.paleta.color_error
                    text_color = ft.Colors.WHITE
                    
                card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(tj.etiqueta, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(tj.valor, size=18, weight=ft.FontWeight.BOLD, color=text_color),
                        ],
                        spacing=2,
                    ),
                    bgcolor=bg_color,
                    padding=10,
                    border_radius=8,
                    col={"sm": 6, "md": 4, "lg": 3},
                )
                self.grid_tarjetas.controls.append(card)
                
        # 4. Avisos
        self.col_avisos.controls.clear()
        if not vm.desactualizado:
            for av in vm.avisos:
                c = ft.Colors.ON_SURFACE
                if av.clase == "ok": c = self.paleta.color_ok
                elif av.clase == "aviso": c = self.paleta.color_aviso
                elif av.clase == "error": c = self.paleta.color_error
                elif av.clase == "info": c = self.paleta.color_info
                
                self.col_avisos.controls.append(
                    ft.Text(av.texto, color=c)
                )

        # 5. Tablas
        if vm.tablas and not vm.desactualizado:
            self.lbl_vacio_tablas.visible = False
            self.panel_contenido_tablas.visible = True
            self._renderizar_tabla_seleccionada()
        else:
            self.lbl_vacio_tablas.visible = True
            self.panel_contenido_tablas.visible = False

        # 6. Moldes 2D
        sel_molde = self.selector_molde.selected[0] if self.selector_molde.selected else "0"
        if sel_molde == "4":
            self.lbl_vacio_moldes.content.value = "Calcula para ver el perfil"
        else:
            self.lbl_vacio_moldes.content.value = "Calcula para ver los moldes"

        if vm.svg_conjunto and not vm.desactualizado:
            self.lbl_vacio_moldes.visible = False
            self.panel_contenido_moldes.visible = True
            self._renderizar_molde_seleccionado(reset_vista=reset_zoom)
        else:
            self.lbl_vacio_moldes.visible = True
            self.panel_contenido_moldes.visible = False

        # 7. Hoja de trazo (F3 y F5)
        sel_hoja = self.selector_pieza_hoja.selected[0] if self.selector_pieza_hoja.selected else "superior"
        self.panel_diseno_pico_hoja.visible = (sel_hoja == "pico")
        self.btn_sincronizar_conos.visible = (sel_hoja != "pico")
        cfg_hoja = vm.config_secciones.get(sel_hoja)
        if cfg_hoja:
            puede_h, mot_h = cfg_hoja.puede_usar_mitad()
            self.segmento_mitad_hoja.disabled = not puede_h
            self.segmento_mitad_hoja.tooltip = mot_h if not puede_h else "Trazo sobre papel doblado en simetría"
            self.selector_modo_dibujo.selected = [cfg_hoja.dibujar]
            self.selector_lienzo.selected = [cfg_hoja.lienzo]

        # Actualizar estado de mitad en diseño
        self.segmento_mitad_diseno.disabled = not vm.puede_usar_mitad
        self.segmento_mitad_diseno.tooltip = vm.motivo_no_mitad if not vm.puede_usar_mitad else "Diseño sobre mitad con reflejo simétrico"
        self.selector_lienzo_diseno.selected = [vm.diseno_lienzo_modo]

        if vm.resumen_pico_linea:
            self.lbl_resumen_pico.value = vm.resumen_pico_linea

        if vm.esquema_error:
            self.lbl_error_esquema.value = vm.esquema_error
            self.lbl_error_esquema.visible = True
        else:
            self.lbl_error_esquema.visible = False

        if vm.aviso_hoja:
            self.lbl_aviso_hoja.content.value = vm.aviso_hoja
            self.lbl_aviso_hoja.visible = True
        else:
            self.lbl_aviso_hoja.visible = False

        self.col_resumen_esquema.controls.clear()
        for linea in vm.resumen_esquema:
            self.col_resumen_esquema.controls.append(
                ft.Text(f"• {linea}", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
            )

        if vm.svg_hoja and not vm.desactualizado and not vm.esquema_error:
            self.lbl_vacio_hoja.visible = False
            self.panel_contenido_hoja.visible = True
            self._renderizar_hoja(reset_vista=reset_zoom)
        else:
            if vm.esquema_error:
                self.lbl_vacio_hoja.content.value = "Corrige el esquema para generar la hoja"
            elif vm.desactualizado:
                self.lbl_vacio_hoja.content.value = "Pulsa Calcular para actualizar la hoja"
            else:
                self.lbl_vacio_hoja.content.value = "Calcula para ver la hoja de trazo"
            self.lbl_vacio_hoja.visible = True
            self.panel_contenido_hoja.visible = False

        # 8. Vista 3D y lista de compra (F4)
        if vm.items_compra and not vm.desactualizado:
            self.lbl_vacio_3d.visible = False
            self.panel_contenido_3d.visible = True
            self.txt_pliegos_paquete.value = str(self.controlador.pliegos_por_paquete)
            self._actualizar_dropdowns_patrones()

            # Actualizar filas de tabla de compra
            self.tabla_compra.rows.clear()
            for it in vm.items_compra:
                nombre_txt = it.color.nombre
                if it.color.marca or it.color.codigo:
                    extra = f"{it.color.marca} {it.color.codigo}".strip()
                    nombre_txt = f"{it.color.nombre} [{extra}]"
                self.tabla_compra.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(nombre_txt)),
                            ft.DataCell(ft.Text(str(it.piezas_superior))),
                            ft.DataCell(ft.Text(str(it.piezas_pico))),
                            ft.DataCell(ft.Text(str(it.piezas_inferior))),
                            ft.DataCell(ft.Text(str(it.piezas_totales), weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(f"{it.area_m2:.2f}")),
                            ft.DataCell(ft.Text(str(it.pliegos), weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(str(it.paquetes), weight=ft.FontWeight.BOLD)),
                        ]
                    )
                )
        else:
            self.lbl_vacio_3d.visible = True
            self.panel_contenido_3d.visible = False

        # 9. Pestaña Diseño (F6a)
        self.chk_ver_cuadricula.value = vm.diseno_ver_cuadricula
        self.chk_ver_rotulos.value = vm.diseno_ver_rotulos
        self.chk_ver_costuras.value = vm.diseno_ver_costuras
        self.chk_mostrar_reflejo.value = vm.diseno_mostrar_reflejo
        self.chk_mostrar_reflejo.visible = (vm.diseno_lienzo_modo == "mitad")

        if vm.svg_diseno and not vm.desactualizado:
            self.lbl_vacio_diseno.visible = False
            self.panel_contenido_diseno.visible = True
            self._renderizar_diseno(reset_vista=reset_zoom)
        else:
            self.lbl_vacio_diseno.visible = True
            self.panel_contenido_diseno.visible = False

        self._actualizar_panel_capas_y_inspector(vm)

        # 10. Proyecto (F3)
        self.lbl_nombre_proyecto.value = vm.nombre_proyecto
        self.lbl_estado_proyecto.value = "Sin guardar" if vm.sin_guardar else ""
        self._actualizar_titulo_ventana(diferir_update=diferir_update)

        if not diferir_update:
            try:
                self.update()
            except RuntimeError:
                pass

    def did_mount(self):
        page = self.obtener_pagina
        if page:
            if hasattr(self, "file_picker") and self.file_picker not in page.services:
                page.services.append(self.file_picker)
                page.update()
            self._actualizar_titulo_ventana()

    def _actualizar_titulo_ventana(self, diferir_update: bool = False):
        page = self.obtener_pagina
        if page:
            ast = " *" if self.controlador.sin_guardar else ""
            nom = self.controlador.nombre_proyecto
            page.title = f"Calculadora de moldes — {nom}{ast}"
            if not diferir_update:
                try:
                    page.update()
                except Exception:
                    pass

    def _cargar_entradas_desde_controlador(self):
        self.txt_altura.value = str(self.controlador.altura)
        self.txt_gajos.value = str(self.controlador.gajos)
        self.txt_hileras.value = str(self.controlador.hileras)
        self.txt_costura.value = str(self.controlador.costura)
        self.switch_avanzado.value = bool(self.controlador.avanzado)
        self.panel_avanzado.visible = bool(self.controlador.avanzado)

        self.txt_boca.value = str(self.controlador.boca or "")
        self.txt_pestana.value = str(self.controlador.pestana or "")
        self.txt_d_mecha.value = str(self.controlador.diametro_mecha or "")
        self.txt_p_mecha.value = str(self.controlador.peso_mecha or "")
        self.txt_alambre.value = str(self.controlador.alambre or "")
        self.txt_varillas.value = str(self.controlador.varillas or "")
        self.txt_llama.value = str(self.controlador.altura_llama or "")
        self.txt_holgura.value = str(self.controlador.holgura or "")

        self.dd_modo_esquema.value = self.controlador.esquema_modo
        self.txt_tam_grupo.value = str(self.controlador.esquema_tam_grupo)
        self.txt_ciclo_personalizado.value = self.controlador.esquema_ciclo_texto
        self.txt_ciclo_personalizado.visible = (self.controlador.esquema_modo == "personalizado")
        self.txt_tam_grupo.visible = (self.controlador.esquema_modo != "personalizado")

        self.dd_hoja.value = self.controlador.hoja_tipo
        self.dd_escala.value = str(self.controlador.hoja_escala)
        self.selector_pieza_hoja.selected = [self.controlador.hoja_pieza]
        self.selector_lienzo.selected = [self.controlador.hoja_lienzo]
        self.selector_modo_dibujo.selected = [self.controlador.hoja_dibujar]
        self.dd_repeticion_pico_hoja.value = self.controlador.esquema_pico.modo_repeticion

        self.txt_pliegos_paquete.value = str(self.controlador.pliegos_por_paquete)
        self.txt_pliego_ancho.value = str(self.controlador.pliego_ancho)
        self.txt_pliego_alto.value = str(self.controlador.pliego_alto)

    def on_proyecto_nuevo(self, e):
        self.controlador.nuevo()
        self._cargar_entradas_desde_controlador()
        self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=True)
        self._mostrar_snackbar("Nuevo proyecto iniciado")

    async def on_proyecto_abrir(self, e):
        archivos = await self.file_picker.pick_files(
            dialog_title="Abrir proyecto",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            allow_multiple=False,
        )
        if archivos and len(archivos) > 0 and archivos[0].path:
            ruta = archivos[0].path
            ok, msg = self.controlador.abrir(ruta)
            if ok:
                self._cargar_entradas_desde_controlador()
                self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=True)
                self._mostrar_snackbar(f"Proyecto abierto: {os.path.basename(ruta)}")
            else:
                self._mostrar_snackbar(f"Error al abrir: {msg}")

    async def on_proyecto_guardar(self, e):
        if not self.controlador.ruta_proyecto:
            await self.on_proyecto_guardar_como(e)
            return
        ok, msg = self.controlador.guardar()
        if ok:
            self._sync_controlador_a_vista(self.controlador.get_view_model())
            self._mostrar_snackbar(f"Proyecto guardado: {os.path.basename(self.controlador.ruta_proyecto)}")
        else:
            self._mostrar_snackbar(f"Error al guardar: {msg}")

    async def on_proyecto_guardar_como(self, e):
        nombre_def = f"{self.controlador.nombre_proyecto}.json"
        ruta = await self.file_picker.save_file(
            dialog_title="Guardar proyecto como",
            file_name=nombre_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
        )
        if ruta:
            ok, msg = self.controlador.guardar(ruta)
            if ok:
                self._sync_controlador_a_vista(self.controlador.get_view_model())
                self._mostrar_snackbar(f"Proyecto guardado como: {os.path.basename(ruta)}")
            else:
                self._mostrar_snackbar(f"Error al guardar: {msg}")

    def on_cambio_pieza_hoja(self, e):
        sel = self.selector_pieza_hoja.selected[0] if self.selector_pieza_hoja.selected else "superior"
        self.controlador.actualizar_opciones_hoja(pieza=sel)
        self.panel_diseno_pico_hoja.visible = (sel == "pico")
        cfg = self.controlador.obtener_config_seccion(sel)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
            else:
                self.txt_ciclo_personalizado.value = ""
            self.txt_ciclo_personalizado.visible = (cfg.esquema.modo == "personalizado")
            self.txt_tam_grupo.visible = (cfg.esquema.modo != "personalizado")
        self.dd_escala.value = str(cfg.escala)
        self.selector_lienzo.selected = [cfg.lienzo]
        self.selector_modo_dibujo.selected = [cfg.dibujar]
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def on_sincronizar_conos(self, e):
        origen = self.controlador.hoja_pieza
        if origen not in ("superior", "inferior"):
            origen = "superior"
        self.controlador.sincronizar_conos(origen)
        cfg = self.controlador.obtener_config_seccion(self.controlador.hoja_pieza)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)
        self._mostrar_snackbar("Configuración sincronizada en ambos conos")

    def on_copiar_config(self, origen: str):
        destino = self.controlador.hoja_pieza
        self.controlador.copiar_configuracion_seccion(origen, destino)
        cfg = self.controlador.obtener_config_seccion(destino)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
        self.dd_escala.value = str(cfg.escala)
        self.selector_lienzo.selected = [cfg.lienzo]
        self.selector_modo_dibujo.selected = [cfg.dibujar]
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)
        self._mostrar_snackbar(f"Configuración copiada desde {origen}")

    def on_cambio_lienzo(self, e):
        sel = self.selector_lienzo.selected[0] if self.selector_lienzo.selected else "abanico"
        self.controlador.actualizar_opciones_hoja(lienzo=sel)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def on_cambio_modo_dibujo(self, e):
        sel = self.selector_modo_dibujo.selected[0] if self.selector_modo_dibujo.selected else "completo"
        self.controlador.actualizar_opciones_hoja(dibujar=sel)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def on_cambio_repeticion_pico_hoja(self, e):
        rep = self.dd_repeticion_pico_hoja.value or "todas_a"
        self.controlador.actualizar_esquema_pico(modo_repeticion=rep)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def on_cambio_esquema_opciones(self, e):
        modo = self.dd_modo_esquema.value or "repeticion"
        self.txt_ciclo_personalizado.visible = (modo == "personalizado")
        self.txt_tam_grupo.visible = (modo != "personalizado")
        tam_g = 5
        try:
            tam_g = int(self.txt_tam_grupo.value or "5")
        except ValueError:
            pass
        ciclo = self.txt_ciclo_personalizado.value or ""
        self.controlador.actualizar_esquema(modo=modo, tam_grupo=tam_g, ciclo_texto=ciclo)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def on_cambio_hoja_opciones(self, e):
        hoja = self.dd_hoja.value or "carta"
        escala = self.dd_escala.value or "auto"
        self.controlador.actualizar_opciones_hoja(tipo=hoja, escala=escala)
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    async def on_exportar_hoja(self, e):
        if not self.controlador.svg_hoja:
            self._mostrar_snackbar("No hay hoja de trazo para exportar")
            return
        nombre_def = f"hoja_{self.controlador.hoja_pieza}_{self.controlador.esquema_modo}.svg"
        ruta = await self.file_picker.save_file(
            dialog_title="Exportar hoja de trazo",
            file_name=nombre_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["svg"],
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(self.controlador.svg_hoja)
                self._mostrar_snackbar(f"Hoja exportada: {os.path.basename(ruta)}")
            except Exception as err:
                self._mostrar_snackbar(f"Error al exportar hoja: {err}")

    async def on_exportar_paquete(self, e):
        if not (self.controlador.resultado and self.controlador.entrada_actual):
            self._mostrar_snackbar("Calcula el modelo antes de exportar el paquete")
            return
        carpeta = await self.file_picker.get_directory_path(
            dialog_title="Seleccionar carpeta para paquete de exportación"
        )
        if carpeta:
            try:
                archivos_dict = generar_paquete(
                    self.controlador.resultado,
                    self.controlador.entrada_actual,
                    esquema=self.controlador._construir_esquema(),
                    hoja=self.controlador.hoja_tipo,
                    escala=self.controlador.hoja_escala,
                )
                archivos_escritos = guardar_paquete(carpeta, archivos_dict, sobrescribir=True)
                self._mostrar_snackbar(f"Paquete exportado: {len(archivos_escritos)} archivos guardados")
            except Exception as err:
                self._mostrar_snackbar(f"Error al exportar paquete: {err}")

    def _opciones_colores_filtradas(self) -> list:
        marca = self.filtro_marca_actual
        cols = self.catalogo_papel
        if marca != "todas":
            cols = [c for c in cols if (c.marca or "").strip().lower() == marca.lower()]
        
        opciones = []
        for c in cols:
            texto = c.nombre
            if c.marca or c.codigo:
                extra = f"{c.marca} {c.codigo}".strip()
                texto = f"{c.nombre} [{extra}]"
            opciones.append(ft.DropdownOption(key=c.id, text=texto))
        return opciones

    def _actualizar_dropdowns_patrones(self):
        opciones = self._opciones_colores_filtradas()
        p = self.controlador.pintura

        # 1. Cono superior
        self.dd_modo_sup.value = p.modo_superior
        self.txt_tam_bloque_sup.visible = (p.modo_superior == "bloques")
        self.txt_tam_bloque_sup.value = str(p.tam_bloque_superior)
        
        self.col_colores_sup.controls.clear()
        for idx, cid in enumerate(p.colores_superior):
            def make_change_sup(i):
                return lambda e: self.on_cambio_color_ciclo_sup(i, e.control.value)
            def make_del_sup(i):
                return lambda e: self.on_eliminar_color_ciclo_sup(i)

            c_obj = color_por_id(cid, self.catalogo_papel)
            row = ft.Row(
                controls=[
                    ft.Container(width=22, height=22, bgcolor=c_obj.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                    ft.Dropdown(
                        options=opciones,
                        value=cid if any(o.key == cid for o in opciones) else (opciones[0].key if opciones else cid),
                        dense=True,
                        width=220,
                        on_select=make_change_sup(idx),
                    ),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Quitar color", on_click=make_del_sup(idx)) if len(p.colores_superior) > 1 else ft.Container(),
                ],
                spacing=8,
            )
            self.col_colores_sup.controls.append(row)
        self.btn_agregar_color_sup.visible = (len(p.colores_superior) < 6 and p.modo_superior != "liso")

        # 2. Cono inferior
        self.chk_mismo_esquema_inf.value = p.mismo_esquema_inferior
        self.container_controles_inf.visible = not p.mismo_esquema_inferior
        self.dd_modo_inf.value = p.modo_inferior
        self.txt_tam_bloque_inf.visible = (p.modo_inferior == "bloques")
        self.txt_tam_bloque_inf.value = str(p.tam_bloque_inferior)

        self.col_colores_inf.controls.clear()
        for idx, cid in enumerate(p.colores_inferior):
            def make_change_inf(i):
                return lambda e: self.on_cambio_color_ciclo_inf(i, e.control.value)
            def make_del_inf(i):
                return lambda e: self.on_eliminar_color_ciclo_inf(i)

            c_obj = color_por_id(cid, self.catalogo_papel)
            row = ft.Row(
                controls=[
                    ft.Container(width=22, height=22, bgcolor=c_obj.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                    ft.Dropdown(
                        options=opciones,
                        value=cid if any(o.key == cid for o in opciones) else (opciones[0].key if opciones else cid),
                        dense=True,
                        width=220,
                        on_select=make_change_inf(idx),
                    ),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Quitar color", on_click=make_del_inf(idx)) if len(p.colores_inferior) > 1 else ft.Container(),
                ],
                spacing=8,
            )
            self.col_colores_inf.controls.append(row)
        self.btn_agregar_color_inf.visible = (len(p.colores_inferior) < 6 and p.modo_inferior != "liso")

        # 3. Picos
        self.dd_repeticion_picos.value = p.repeticion_picos
        self.chk_usar_var_b.value = p.usar_variante_b
        self.panel_variante_b.visible = p.usar_variante_b

        # Variante A
        self.dd_modo_caras_var_a.value = p.variante_a.modo_caras
        self._construir_controles_variante(self.col_colores_var_a, p.variante_a, "A", opciones)

        # Variante B
        self.dd_modo_caras_var_b.value = p.variante_b.modo_caras
        self._construir_controles_variante(self.col_colores_var_b, p.variante_b, "B", opciones)

        # 4. Actualizar vista previa 2D
        self._actualizar_vista_previa_2d()

    def _construir_controles_variante(self, container_row: ft.Row, variante: VariantePico, nombre_var: str, opciones: list):
        container_row.controls.clear()
        modo = variante.modo_caras

        def make_change(cara_idx):
            return lambda e: self.on_cambio_color_variante(nombre_var, cara_idx, e.control.value)

        if modo == "igual":
            c_obj = color_por_id(variante.color_0, self.catalogo_papel)
            container_row.controls.append(
                ft.Row([
                    ft.Container(width=20, height=20, bgcolor=c_obj.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                    ft.Dropdown(label="Color (4 caras)", options=opciones, value=variante.color_0, dense=True, width=220, on_select=make_change(0))
                ], spacing=6)
            )
        elif modo == "alternado":
            c0 = color_por_id(variante.color_0, self.catalogo_papel)
            c1 = color_por_id(variante.color_1, self.catalogo_papel)
            container_row.controls.extend([
                ft.Row([
                    ft.Container(width=20, height=20, bgcolor=c0.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                    ft.Dropdown(label="Caras 0 y 2", options=opciones, value=variante.color_0, dense=True, width=180, on_select=make_change(0))
                ], spacing=6),
                ft.Row([
                    ft.Container(width=20, height=20, bgcolor=c1.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                    ft.Dropdown(label="Caras 1 y 3", options=opciones, value=variante.color_1, dense=True, width=180, on_select=make_change(1))
                ], spacing=6),
            ])
        elif modo == "cuatro":
            colores_var = [variante.color_0, variante.color_1, variante.color_2, variante.color_3]
            for idx, c_val in enumerate(colores_var):
                c_obj = color_por_id(c_val, self.catalogo_papel)
                container_row.controls.append(
                    ft.Row([
                        ft.Container(width=20, height=20, bgcolor=c_obj.hex, border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE)),
                        ft.Dropdown(label=f"Cara {idx}", options=opciones, value=c_val, dense=True, width=150, on_select=make_change(idx))
                    ], spacing=6)
                )

    def _actualizar_vista_previa_2d(self):
        vm = self.controlador.get_view_model()
        p = self.controlador.pintura
        N = int(self.controlador.gajos or 30)
        hileras = int(self.controlador.hileras or 2)

        self.fila_previa_sup.controls.clear()
        self.fila_previa_inf.controls.clear()
        self.col_previa_picos.controls.clear()

        # Cono superior e inferior
        for k in range(N):
            cara_s = Cara([], "superior", k, None, None, [0, 0, 1], [])
            col_id_s = color_de_cara(p, cara_s, None, N)
            col_hex_s = color_por_id(col_id_s, self.catalogo_papel).hex

            self.fila_previa_sup.controls.append(
                ft.Container(width=22, height=22, bgcolor=col_hex_s, border_radius=3, tooltip=f"Gajo {k+1}: {col_id_s}", border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT))
            )

            cara_i = Cara([], "inferior", k, None, None, [0, 0, -1], [])
            col_id_i = color_de_cara(p, cara_i, None, N)
            col_hex_i = color_por_id(col_id_i, self.catalogo_papel).hex

            self.fila_previa_inf.controls.append(
                ft.Container(width=22, height=22, bgcolor=col_hex_i, border_radius=3, tooltip=f"Gajo {k+1}: {col_id_i}", border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT))
            )

        # Picos (cuadrícula de hileras × gajos)
        for j in range(hileras):
            fila_p = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)
            for k in range(N):
                # Usar color de cara 0 como representativo de la pirámide
                cara_p = Cara([], "pico", k, j, 0, [1, 0, 0], [])
                col_id_p = color_de_cara(p, cara_p, None, N)
                col_hex_p = color_por_id(col_id_p, self.catalogo_papel).hex
                fila_p.controls.append(
                    ft.Container(width=22, height=22, bgcolor=col_hex_p, border_radius=3, tooltip=f"H{j+1} G{k+1}: {col_id_p}", border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT))
                )
            self.col_previa_picos.controls.append(fila_p)

    def on_cambio_patron_ui(self, e):
        p = self.controlador.pintura
        p.modo_superior = self.dd_modo_sup.value or "liso"
        try:
            p.tam_bloque_superior = max(1, int(self.txt_tam_bloque_sup.value or 5))
        except ValueError:
            p.tam_bloque_superior = 5

        p.mismo_esquema_inferior = bool(self.chk_mismo_esquema_inf.value)
        p.modo_inferior = self.dd_modo_inf.value or "liso"
        try:
            p.tam_bloque_inferior = max(1, int(self.txt_tam_bloque_inf.value or 5))
        except ValueError:
            p.tam_bloque_inferior = 5

        p.repeticion_picos = self.dd_repeticion_picos.value or "todas_a"
        p.usar_variante_b = bool(self.chk_usar_var_b.value)

        p.variante_a.modo_caras = self.dd_modo_caras_var_a.value or "igual"
        p.variante_b.modo_caras = self.dd_modo_caras_var_b.value or "igual"

        self.controlador.actualizar_pintura(pintura_completa=p)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_color_ciclo_sup(self, idx: int, cid: str):
        p = self.controlador.pintura
        if idx < len(p.colores_superior):
            p.colores_superior[idx] = cid
            p.color_superior = p.colores_superior[0]
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_agregar_color_sup(self, e):
        p = self.controlador.pintura
        if len(p.colores_superior) < 6:
            p.colores_superior.append("blanco")
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_eliminar_color_ciclo_sup(self, idx: int):
        p = self.controlador.pintura
        if len(p.colores_superior) > 1 and idx < len(p.colores_superior):
            p.colores_superior.pop(idx)
            p.color_superior = p.colores_superior[0]
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_color_ciclo_inf(self, idx: int, cid: str):
        p = self.controlador.pintura
        if idx < len(p.colores_inferior):
            p.colores_inferior[idx] = cid
            p.color_inferior = p.colores_inferior[0]
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_agregar_color_inf(self, e):
        p = self.controlador.pintura
        if len(p.colores_inferior) < 6:
            p.colores_inferior.append("blanco")
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_eliminar_color_ciclo_inf(self, idx: int):
        p = self.controlador.pintura
        if len(p.colores_inferior) > 1 and idx < len(p.colores_inferior):
            p.colores_inferior.pop(idx)
            p.color_inferior = p.colores_inferior[0]
            self.controlador.actualizar_pintura(pintura_completa=p)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_color_variante(self, nombre_var: str, cara_idx: int, cid: str):
        p = self.controlador.pintura
        var = p.variante_a if nombre_var == "A" else p.variante_b
        if cara_idx == 0: var.color_0 = cid
        elif cara_idx == 1: var.color_1 = cid
        elif cara_idx == 2: var.color_2 = cid
        elif cara_idx == 3: var.color_3 = cid

        if nombre_var == "A":
            p.color_pico = var.color_0

        self.controlador.actualizar_pintura(pintura_completa=p)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_filtro_marca(self, e):
        self.filtro_marca_actual = self.dd_filtro_marca.value or "todas"
        self._actualizar_dropdowns_patrones()
        self.update()

    def on_cambio_pliegos_paquete(self, e):
        try:
            val = max(1, int(self.txt_pliegos_paquete.value or 100))
        except ValueError:
            val = 100
        self.controlador.pliegos_por_paquete = val
        self.controlador.sin_guardar = True
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_tam_pliego(self, e):
        try:
            ancho = float(self.txt_pliego_ancho.value or 50)
            alto = float(self.txt_pliego_alto.value or 70)
        except ValueError:
            return
        if ancho > 0 and alto > 0:
            self.controlador.pliego_ancho = ancho
            self.controlador.pliego_alto = alto
            self.controlador.sin_guardar = True
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    async def on_dialogo_agregar_color(self, e):
        txt_nom = ft.TextField(label="Nombre del color", dense=True)
        txt_marca = ft.TextField(label="Marca (opcional)", dense=True)
        txt_codigo = ft.TextField(label="Código de fábrica (opcional)", dense=True)
        txt_hex = ft.TextField(label="HEX (ej. #e91e63)", dense=True)
        txt_notas = ft.TextField(label="Notas", dense=True)
        chk_calib = ft.Checkbox(label="Calibrado (exacto)", value=False)

        def guardar_nuevo_color(dialog_event):
            nom = txt_nom.value.strip()
            hex_val = txt_hex.value.strip()
            if not nom or not hex_val:
                self._mostrar_snackbar("Nombre y código HEX son obligatorios.")
                return
            if not hex_val.startswith("#"):
                hex_val = "#" + hex_val
            try:
                col = ColorPapel(
                    id=nom.lower().replace(" ", "_"),
                    nombre=nom,
                    hex=hex_val,
                    aproximado=not chk_calib.value,
                    marca=txt_marca.value.strip(),
                    codigo=txt_codigo.value.strip(),
                    notas=txt_notas.value.strip()
                )
                guardar_color_usuario(col)
                self.catalogo_papel = cargar_catalogo()
                self._actualizar_marcas_disponibles()
                self._actualizar_dropdowns_patrones()
                dialog.open = False
                self.page.update()
                self._mostrar_snackbar(f"Color '{nom}' agregado con éxito.")
            except Exception as err:
                self._mostrar_snackbar(f"Error al guardar: {err}")

        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo color de papel"),
            content=ft.Column([txt_nom, txt_marca, txt_codigo, txt_hex, txt_notas, chk_calib], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dialog, "open", False) or self.page.update()),
                ft.FilledButton("Guardar", on_click=guardar_nuevo_color),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _actualizar_marcas_disponibles(self):
        marcas = sorted(list(set(c.marca.strip() for c in self.catalogo_papel if c.marca.strip())))
        opts = [ft.DropdownOption(key="todas", text="Todas las marcas")]
        for m in marcas:
            opts.append(ft.DropdownOption(key=m, text=m))
        self.dd_filtro_marca.options = opts

    async def on_importar_catalogo_csv(self, e):
        archivos = await self.file_picker.pick_files(
            dialog_title="Importar catálogo de colores CSV",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"],
            allow_multiple=False,
        )
        if archivos and len(archivos) > 0 and archivos[0].path:
            ruta = archivos[0].path
            try:
                importados, errores = importar_csv(ruta)
                self.catalogo_papel = cargar_catalogo()
                self._actualizar_marcas_disponibles()
                self._actualizar_dropdowns_patrones()
                msg = f"{len(importados)} colores importados."
                if errores:
                    msg += f" ({len(errores)} filas omitidas: {errores[0]})"
                self._mostrar_snackbar(msg)
                self._sync_controlador_a_vista(self.controlador.get_view_model())
            except Exception as err:
                self._mostrar_snackbar(f"Error al importar CSV: {err}")

    async def on_exportar_catalogo_csv(self, e):
        ruta = await self.file_picker.save_file(
            dialog_title="Exportar catálogo de colores CSV",
            file_name="catalogo_colores_papel.csv",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"],
        )
        if ruta:
            try:
                exportar_csv(ruta, self.catalogo_papel)
                self._mostrar_snackbar(f"Catálogo exportado: {os.path.basename(ruta)}")
            except Exception as err:
                self._mostrar_snackbar(f"Error al exportar CSV: {err}")

    def on_abrir_visor_3d(self, e):
        servidor = self.controlador.obtener_servidor_3d()
        if servidor and servidor.url:
            webbrowser.open(servidor.url)
            self._mostrar_snackbar(f"Abriendo visor 3D en {servidor.url}")
        else:
            self._mostrar_snackbar("No se pudo iniciar el servidor 3D local")

    async def on_exportar_visor_3d(self, e):
        if not (self.controlador.resultado and self.controlador.entrada_actual):
            self._mostrar_snackbar("Calcula el modelo antes de exportar el visor 3D")
            return
        nombre_def = f"{self.controlador.nombre_proyecto}_visor3d.html"
        ruta = await self.file_picker.save_file(
            dialog_title="Exportar visor 3D autocontenido",
            file_name=nombre_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["html"],
        )
        if ruta:
            try:
                self.controlador.exportar_visor_3d(ruta)
                self._mostrar_snackbar(f"Visor 3D exportado: {os.path.basename(ruta)}")
            except Exception as err:
                self._mostrar_snackbar(f"Error al exportar visor 3D: {err}")

    def on_copiar_lista_compra(self, e):
        vm = self.controlador.get_view_model()
        if not vm.items_compra:
            self._mostrar_snackbar("No hay datos en la lista de compra")
            return

        lineas = ["Color\tMarca\tCódigo\tSuperior\tPico\tInferior\tTotal piezas\tÁrea (m²)\tPliegos\tPaquetes"]
        for it in vm.items_compra:
            m = it.color.marca or "-"
            c = it.color.codigo or "-"
            lineas.append(
                f"{it.color.nombre}\t{m}\t{c}\t{it.piezas_superior}\t{it.piezas_pico}\t{it.piezas_inferior}\t{it.piezas_totales}\t{it.area_m2:.2f}\t{it.pliegos}\t{it.paquetes}"
            )
        texto = "\n".join(lineas)

        copia_exitosa = False
        page = self.obtener_pagina
        try:
            if page and isinstance(self.servicio_clipboard, ft.Service):
                if self.servicio_clipboard not in page.services:
                    page.services.append(self.servicio_clipboard)

            if hasattr(self.servicio_clipboard, "set"):
                res = self.servicio_clipboard.set(texto)
                if asyncio.iscoroutine(res):
                    if page:
                        page.run_task(self.servicio_clipboard.set, texto)
                    else:
                        asyncio.run(res)
                copia_exitosa = True
        except Exception:
            copia_exitosa = False

        if copia_exitosa:
            self._mostrar_snackbar("Lista de compra copiada al portapapeles")
        else:
            self._mostrar_snackbar("No se pudo copiar la lista")

    def _porcentaje_zoom_hoja(self) -> float:
        if not self.vista_base_svg_hoja or not self.vista_svg_hoja or self.vista_svg_hoja.ancho <= 0:
            return 100.0
        return (self.vista_base_svg_hoja.ancho / self.vista_svg_hoja.ancho) * 100.0

    def _limites_zoom_hoja(self) -> Tuple[float, float]:
        if not self.vista_base_svg_hoja:
            return (1.0, 1000.0)
        ancho_min = self.vista_base_svg_hoja.ancho / 40.0
        ancho_max = self.vista_base_svg_hoja.ancho * 1.5
        return (ancho_min, ancho_max)

    def _on_container_hoja_size_change(self, e):
        w_raw = getattr(e, "width", 0.0) or 0.0
        h_raw = getattr(e, "height", 0.0) or 0.0
        if w_raw <= 0 or h_raw <= 0:
            return

        descuento_w = 2.0 * (self._padding_container + 1.0)
        descuento_h = 2.0 * (self._padding_container + 1.0)
        w_util = max(50.0, w_raw - descuento_w)
        h_util = max(50.0, h_raw - descuento_h)

        if abs(w_util - self.zona_ancho_hoja) < 0.5 and abs(h_util - self.zona_alto_hoja) < 0.5:
            return

        self.zona_ancho_hoja = w_util
        self.zona_alto_hoja = h_util
        self.img_svg_hoja.width = self.zona_ancho_hoja
        self.img_svg_hoja.height = self.zona_alto_hoja

        aspecto_zona = self.zona_ancho_hoja / self.zona_alto_hoja

        if self._svg_hoja_raw:
            w_nat, h_nat = extraer_dimensiones_svg(self._svg_hoja_raw)
            self.vista_base_svg_hoja = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            if self.vista_svg_hoja:
                self.vista_svg_hoja = adaptar_aspecto(self.vista_svg_hoja, aspecto_zona)
            else:
                self.vista_svg_hoja = self.vista_base_svg_hoja
            self._actualizar_imagen_hoja_zoom(force=True)

    def _renderizar_hoja(self, reset_vista: bool = False):
        vm = self.controlador.get_view_model()
        svg_str = vm.svg_hoja
        self._svg_hoja_raw = svg_str

        if not svg_str:
            self.img_svg_hoja.src = ""
            return

        aspecto_zona = self.zona_ancho_hoja / self.zona_alto_hoja if self.zona_alto_hoja > 0 else 1.0
        w_nat, h_nat = extraer_dimensiones_svg(svg_str)
        if reset_vista or not self.vista_svg_hoja or not self.vista_base_svg_hoja:
            self.vista_base_svg_hoja = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            self.vista_svg_hoja = self.vista_base_svg_hoja

        svg_con_viewbox = aplicar_viewbox(svg_str, self.vista_svg_hoja)
        self.img_svg_hoja.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_hoja_porcentaje.value = f"{self._porcentaje_zoom_hoja():.0f} %"

    def _actualizar_imagen_hoja_zoom(self, force: bool = False):
        if not self._svg_hoja_raw or not self.vista_svg_hoja:
            return
        svg_con_viewbox = aplicar_viewbox(self._svg_hoja_raw, self.vista_svg_hoja)
        self.img_svg_hoja.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_hoja_porcentaje.value = f"{self._porcentaje_zoom_hoja():.0f} %"
        try:
            self.img_svg_hoja.update()
            self.lbl_zoom_hoja_porcentaje.update()
        except Exception:
            pass

    def _on_gesture_hoja_scroll(self, e: ft.ScrollEvent):
        if not self.vista_svg_hoja:
            return
        delta_y = getattr(e, "scroll_delta", None)
        factor = 1.15
        if delta_y and hasattr(delta_y, "y"):
            if delta_y.y > 0:
                factor = 1.0 / 1.15
            elif delta_y.y < 0:
                factor = 1.15

        fx = 0.5
        fy = 0.5
        local_pos = getattr(e, "local_position", None)
        if local_pos and hasattr(local_pos, "x") and hasattr(local_pos, "y"):
            if self.zona_ancho_hoja > 0 and self.zona_alto_hoja > 0:
                fx = max(0.01, min(0.99, local_pos.x / self.zona_ancho_hoja))
                fy = max(0.01, min(0.99, local_pos.y / self.zona_alto_hoja))

        self.vista_svg_hoja = zoom(
            self.vista_svg_hoja,
            factor=factor,
            fx=fx,
            fy=fy,
            limites=self._limites_zoom_hoja()
        )
        self._actualizar_imagen_hoja_zoom()

    def _on_gesture_hoja_pan_update(self, e: ft.DragUpdateEvent):
        if not self.vista_svg_hoja or not self.vista_base_svg_hoja:
            return
        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if delta and hasattr(delta, "x") and hasattr(delta, "y"):
            w_control = max(50.0, self.zona_ancho_hoja)
            h_control = max(50.0, self.zona_alto_hoja)
            dx = delta.x * (self.vista_svg_hoja.ancho / w_control)
            dy = delta.y * (self.vista_svg_hoja.alto / h_control)
            limites_cont = (self.vista_base_svg_hoja.ancho, self.vista_base_svg_hoja.alto)
            self.vista_svg_hoja = desplazar(self.vista_svg_hoja, dx=dx, dy=dy, limites_contenido=limites_cont)
            self._actualizar_imagen_hoja_zoom()

    def _on_gesture_hoja_double_tap(self, e):
        self._ajustar_vista_hoja()

    def _on_btn_zoom_in_hoja(self, e):
        if not self.vista_svg_hoja:
            return
        self.vista_svg_hoja = zoom(self.vista_svg_hoja, factor=1.25, fx=0.5, fy=0.5, limites=self._limites_zoom_hoja())
        self._actualizar_imagen_hoja_zoom(force=True)

    def _on_btn_zoom_out_hoja(self, e):
        if not self.vista_svg_hoja:
            return
        self.vista_svg_hoja = zoom(self.vista_svg_hoja, factor=1.0 / 1.25, fx=0.5, fy=0.5, limites=self._limites_zoom_hoja())
        self._actualizar_imagen_hoja_zoom(force=True)

    def _on_btn_ajustar_hoja(self, e):
        self._ajustar_vista_hoja()

    def _ajustar_vista_hoja(self):
        if not self._svg_hoja_raw:
            return
        w_nat, h_nat = extraer_dimensiones_svg(self._svg_hoja_raw)
        aspecto_zona = self.zona_ancho_hoja / self.zona_alto_hoja if self.zona_alto_hoja > 0 else 1.0
        self.vista_base_svg_hoja = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
        self.vista_svg_hoja = self.vista_base_svg_hoja
        self._actualizar_imagen_hoja_zoom(force=True)

    # =========================================================================
    # --- MÉTODOS DE LA PESTAÑA DISEÑO (F6a) ---
    # =========================================================================
    def _porcentaje_zoom_diseno(self) -> float:
        if not self.vista_base_svg_diseno or not self.vista_svg_diseno or self.vista_svg_diseno.ancho <= 0:
            return 100.0
        return (self.vista_base_svg_diseno.ancho / self.vista_svg_diseno.ancho) * 100.0

    def _limites_zoom_diseno(self) -> Tuple[float, float]:
        if not self.vista_base_svg_diseno:
            return (1.0, 1000.0)
        ancho_min = self.vista_base_svg_diseno.ancho / 40.0
        ancho_max = self.vista_base_svg_diseno.ancho * 1.5
        return (ancho_min, ancho_max)

    def _on_container_diseno_size_change(self, e):
        w_raw = getattr(e, "width", 0.0) or 0.0
        h_raw = getattr(e, "height", 0.0) or 0.0
        if w_raw <= 0 or h_raw <= 0:
            return

        descuento_w = 2.0 * (self._padding_container + self._border_width)
        descuento_h = 2.0 * (self._padding_container + self._border_width)
        w_util = max(50.0, w_raw - descuento_w)
        h_util = max(50.0, h_raw - descuento_h)

        if abs(w_util - self.zona_ancho_diseno) < 0.5 and abs(h_util - self.zona_alto_diseno) < 0.5:
            return

        self.zona_ancho_diseno = w_util
        self.zona_alto_diseno = h_util
        self.img_svg_diseno.width = self.zona_ancho_diseno
        self.img_svg_diseno.height = self.zona_alto_diseno

        aspecto_zona = self.zona_ancho_diseno / self.zona_alto_diseno
        if self._svg_diseno_raw:
            w_nat, h_nat = extraer_dimensiones_svg(self._svg_diseno_raw)
            self.vista_base_svg_diseno = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            if self.vista_svg_diseno:
                self.vista_svg_diseno = adaptar_aspecto(self.vista_svg_diseno, aspecto_zona)
            else:
                self.vista_svg_diseno = self.vista_base_svg_diseno
            self._actualizar_imagen_diseno_zoom(force=True)

    def _renderizar_diseno(self, reset_vista: bool = False):
        if not self.controlador.svg_diseno:
            self.img_svg_diseno.src = ""
            return
        self._svg_diseno_raw = self.controlador.svg_diseno
        aspecto_zona = self.zona_ancho_diseno / self.zona_alto_diseno if self.zona_alto_diseno > 0 else 1.0
        w_nat, h_nat = extraer_dimensiones_svg(self._svg_diseno_raw)

        if reset_vista or not self.vista_svg_diseno or not self.vista_base_svg_diseno:
            self.vista_base_svg_diseno = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
            self.vista_svg_diseno = self.vista_base_svg_diseno

        self._actualizar_imagen_diseno()

    def _actualizar_imagen_diseno(self):
        if not self._svg_diseno_raw or not self.vista_svg_diseno:
            return
        svg_con_viewbox = aplicar_viewbox(self._svg_diseno_raw, self.vista_svg_diseno)
        self.img_svg_diseno.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_diseno_porcentaje.value = f"{self._porcentaje_zoom_diseno():.0f} %"

    def _actualizar_imagen_diseno_zoom(self, force: bool = False):
        if not self._svg_diseno_raw or not self.vista_svg_diseno:
            return
        svg_con_viewbox = aplicar_viewbox(self._svg_diseno_raw, self.vista_svg_diseno)
        self.img_svg_diseno.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_diseno_porcentaje.value = f"{self._porcentaje_zoom_diseno():.0f} %"
        try:
            self.img_svg_diseno.update()
            self.lbl_zoom_diseno_porcentaje.update()
        except Exception:
            pass

    def _on_gesture_diseno_scroll(self, e: ft.ScrollEvent):
        if not self.vista_svg_diseno:
            return
        delta_y = getattr(e, "scroll_delta", None)
        factor = 1.15
        if delta_y and hasattr(delta_y, "y"):
            if delta_y.y > 0:
                factor = 1.0 / 1.15
            elif delta_y.y < 0:
                factor = 1.15

        fx = 0.5
        fy = 0.5
        local_pos = getattr(e, "local_position", None)
        if local_pos and hasattr(local_pos, "x") and hasattr(local_pos, "y"):
            if self.zona_ancho_diseno > 0 and self.zona_alto_diseno > 0:
                fx = max(0.01, min(0.99, local_pos.x / self.zona_ancho_diseno))
                fy = max(0.01, min(0.99, local_pos.y / self.zona_alto_diseno))

        self.vista_svg_diseno = zoom(
            self.vista_svg_diseno,
            factor=factor,
            fx=fx,
            fy=fy,
            limites=self._limites_zoom_diseno()
        )
        self._actualizar_imagen_diseno_zoom()

    def _on_gesture_diseno_pan_update(self, e: ft.DragUpdateEvent):
        if not self.vista_svg_diseno or not self.vista_base_svg_diseno:
            return
        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if not (delta and hasattr(delta, "x") and hasattr(delta, "y")):
            return

        capa_sel = self.controlador.obtener_capa_seleccionada()
        if (
            self.modo_interaccion_diseno == "mover"
            and capa_sel
            and not capa_sel.bloqueada
        ):
            w_control = max(50.0, self.zona_ancho_diseno)
            h_control = max(50.0, self.zona_alto_diseno)
            dx_mm = delta.x * (self.vista_svg_diseno.ancho / w_control)
            dy_mm = delta.y * (self.vista_svg_diseno.alto / h_control)
            vent = self.controlador.ventana_lienzo()
            w_cm = max(1.0, vent[2] - vent[0])
            factor_escala = self.vista_base_svg_diseno.ancho / w_cm
            if factor_escala <= 0:
                factor_escala = 1.0
            dx_cm = dx_mm / factor_escala
            dy_cm = dy_mm / factor_escala
            self.controlador.empujar_capa_seleccionada(dx=dx_cm, dy=dy_cm)
            self._sync_controlador_a_vista(self.controlador.get_view_model())
        else:
            w_control = max(50.0, self.zona_ancho_diseno)
            h_control = max(50.0, self.zona_alto_diseno)
            dx = delta.x * (self.vista_svg_diseno.ancho / w_control)
            dy = delta.y * (self.vista_svg_diseno.alto / h_control)
            limites_cont = (self.vista_base_svg_diseno.ancho, self.vista_base_svg_diseno.alto)
            self.vista_svg_diseno = desplazar(self.vista_svg_diseno, dx=dx, dy=dy, limites_contenido=limites_cont)
            self._actualizar_imagen_diseno_zoom()

    def _on_gesture_diseno_double_tap(self, e):
        self._ajustar_vista_diseno()

    def _on_btn_zoom_in_diseno(self, e):
        if not self.vista_svg_diseno:
            return
        self.vista_svg_diseno = zoom(self.vista_svg_diseno, factor=1.25, fx=0.5, fy=0.5, limites=self._limites_zoom_diseno())
        self._actualizar_imagen_diseno_zoom(force=True)

    def _on_btn_zoom_out_diseno(self, e):
        if not self.vista_svg_diseno:
            return
        self.vista_svg_diseno = zoom(self.vista_svg_diseno, factor=1.0 / 1.25, fx=0.5, fy=0.5, limites=self._limites_zoom_diseno())
        self._actualizar_imagen_diseno_zoom(force=True)

    def _on_btn_ajustar_diseno(self, e):
        self._ajustar_vista_diseno()

    def _ajustar_vista_diseno(self):
        if not self._svg_diseno_raw:
            return
        w_nat, h_nat = extraer_dimensiones_svg(self._svg_diseno_raw)
        aspecto_zona = self.zona_ancho_diseno / self.zona_alto_diseno if self.zona_alto_diseno > 0 else 1.0
        self.vista_base_svg_diseno = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=0.04)
        self.vista_svg_diseno = self.vista_base_svg_diseno
        self._actualizar_imagen_diseno_zoom(force=True)

    def on_cambio_seccion_diseno(self, e):
        sel = self.selector_seccion_diseno.selected[0] if self.selector_seccion_diseno.selected else "superior"
        self.selector_variante_pico_diseno.visible = (sel == "pico")
        var = self.selector_variante_pico_diseno.selected[0] if self.selector_variante_pico_diseno.selected else "A"
        self.controlador.cambiar_diseno_seccion(sel, var)
        self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=True)

    def on_cambio_variante_diseno(self, e):
        sel = self.selector_seccion_diseno.selected[0] if self.selector_seccion_diseno.selected else "pico"
        var = self.selector_variante_pico_diseno.selected[0] if self.selector_variante_pico_diseno.selected else "A"
        self.controlador.cambiar_diseno_seccion(sel, var)
        self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=True)

    def on_cambio_lienzo_diseno(self, e):
        modo = self.selector_lienzo_diseno.selected[0] if self.selector_lienzo_diseno.selected else "completo"
        self.controlador.cambiar_diseno_lienzo_modo(modo)
        self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=True)

    async def on_anadir_capa_click(self, e):
        archivos = await self.file_picker.pick_files(
            dialog_title="Seleccionar imagen o SVG para diseño",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png", "jpg", "jpeg", "webp", "svg"],
            allow_multiple=False,
        )
        if archivos and len(archivos) > 0 and archivos[0].path:
            ruta = archivos[0].path
            try:
                self.controlador.anadir_capa(ruta)
                self._sync_controlador_a_vista(self.controlador.get_view_model())
                self._mostrar_snackbar(f"Capa añadida: {os.path.basename(ruta)}")
            except Exception as ex:
                self._mostrar_snackbar(f"Error al añadir capa: {ex}")

    def _actualizar_panel_capas_y_inspector(self, vm: ViewModelTrompo):
        self.col_lista_capas.controls.clear()
        capa_activa = self.controlador.obtener_capa_seleccionada()

        for c in vm.capas_diseno:
            es_sel = (c.id == vm.capa_seleccionada_id)
            c_id = c.id

            def make_select(cid):
                return lambda e: self._seleccionar_capa(cid)

            def make_move(cid, delta):
                return lambda e: self._mover_capa(cid, delta)

            def make_toggle_vis(cid, vis):
                return lambda e: self._toggle_visibilidad_capa(cid, vis)

            def make_toggle_lock(cid, lock):
                return lambda e: self._toggle_bloqueo_capa(cid, lock)

            def make_delete(cid):
                return lambda e: self._eliminar_capa(cid)

            btn_vis = ft.IconButton(
                icon=ft.Icons.VISIBILITY if c.visible else ft.Icons.VISIBILITY_OFF,
                icon_size=16,
                tooltip="Visibilidad",
                on_click=make_toggle_vis(c_id, not c.visible),
            )
            btn_lock = ft.IconButton(
                icon=ft.Icons.LOCK if c.bloqueada else ft.Icons.LOCK_OPEN,
                icon_size=16,
                tooltip="Bloquear",
                on_click=make_toggle_lock(c_id, not c.bloqueada),
            )
            btn_up = ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD,
                icon_size=16,
                tooltip="Subir orden",
                on_click=make_move(c_id, -1),
            )
            btn_down = ft.IconButton(
                icon=ft.Icons.ARROW_DOWNWARD,
                icon_size=16,
                tooltip="Bajar orden",
                on_click=make_move(c_id, 1),
            )
            btn_del = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=16,
                icon_color=ft.Colors.ERROR,
                tooltip="Eliminar",
                on_click=make_delete(c_id),
            )

            tipo_icono = ft.Icons.DRAW if c.tipo == "svg" else ft.Icons.IMAGE
            fila_capa = ft.Container(
                padding=6,
                border_radius=6,
                bgcolor=ft.Colors.PRIMARY_CONTAINER if es_sel else ft.Colors.SURFACE_CONTAINER,
                border=ft.Border.all(1, ft.Colors.PRIMARY if es_sel else ft.Colors.OUTLINE_VARIANT),
                on_click=make_select(c_id),
                content=ft.Row(
                    controls=[
                        ft.Icon(tipo_icono, size=18),
                        ft.Text(c.nombre, size=13, weight=ft.FontWeight.BOLD if es_sel else ft.FontWeight.NORMAL, expand=True),
                        btn_vis,
                        btn_lock,
                        btn_up,
                        btn_down,
                        btn_del,
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
            self.col_lista_capas.controls.append(fila_capa)

        # Actualizar inspector
        if capa_activa:
            self.panel_inspector_capa.visible = True
            self.txt_nombre_capa.value = capa_activa.nombre
            self.txt_pos_x.value = f"{capa_activa.x:.2f}"
            self.txt_pos_y.value = f"{capa_activa.y:.2f}"
            self.txt_ancho_capa.value = f"{capa_activa.ancho:.2f}"
            self.txt_alto_capa.value = f"{capa_activa.alto:.2f}"
            self.chk_proporcion.value = self.controlador.mantener_proporcion
            self.slider_rotacion.value = float(capa_activa.rotacion)
            self.lbl_rotacion_val.value = f"{capa_activa.rotacion:.0f}°"
            self.slider_opacidad.value = float(capa_activa.opacidad)
            self.lbl_opacidad_val.value = f"{int(capa_activa.opacidad * 100)}%"
        else:
            self.panel_inspector_capa.visible = False

    def _seleccionar_capa(self, cid: str):
        self.controlador.capa_seleccionada_id = cid
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _mover_capa(self, cid: str, delta: int):
        self.controlador.mover_capa(cid, delta)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _toggle_visibilidad_capa(self, cid: str, vis: bool):
        self.controlador.capa_seleccionada_id = cid
        self.controlador.modificar_capa_seleccionada(visible=vis)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _toggle_bloqueo_capa(self, cid: str, lock: bool):
        for c in self.controlador.obtener_diseno_activo().capas:
            if c.id == cid:
                c.bloqueada = lock
                self.controlador.sin_guardar = True
                break
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _eliminar_capa(self, cid: str):
        self.controlador.eliminar_capa(cid)
        self._sync_controlador_a_vista(self.controlador.get_view_model())
        self._mostrar_snackbar("Capa eliminada")

    def on_nombre_capa_change(self, e):
        self.controlador.modificar_capa_seleccionada(nombre=self.txt_nombre_capa.value)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_pos_x_change(self, e):
        try:
            val = float(self.txt_pos_x.value or 0.0)
            self.controlador.modificar_capa_seleccionada(x=val)
            self._sync_controlador_a_vista(self.controlador.get_view_model())
        except ValueError:
            pass

    def on_pos_y_change(self, e):
        try:
            val = float(self.txt_pos_y.value or 0.0)
            self.controlador.modificar_capa_seleccionada(y=val)
            self._sync_controlador_a_vista(self.controlador.get_view_model())
        except ValueError:
            pass

    def on_ancho_capa_change(self, e):
        try:
            val = max(0.1, float(self.txt_ancho_capa.value or 1.0))
            capa = self.controlador.obtener_capa_seleccionada()
            if capa:
                if self.controlador.mantener_proporcion and capa.ancho_natural > 0:
                    alto_prop = val * (capa.alto_natural / capa.ancho_natural)
                    self.controlador.modificar_capa_seleccionada(ancho=val, alto=alto_prop)
                else:
                    self.controlador.modificar_capa_seleccionada(ancho=val)
                self._sync_controlador_a_vista(self.controlador.get_view_model())
        except ValueError:
            pass

    def on_alto_capa_change(self, e):
        try:
            val = max(0.1, float(self.txt_alto_capa.value or 1.0))
            capa = self.controlador.obtener_capa_seleccionada()
            if capa:
                if self.controlador.mantener_proporcion and capa.alto_natural > 0:
                    ancho_prop = val * (capa.ancho_natural / capa.alto_natural)
                    self.controlador.modificar_capa_seleccionada(ancho=ancho_prop, alto=val)
                else:
                    self.controlador.modificar_capa_seleccionada(alto=val)
                self._sync_controlador_a_vista(self.controlador.get_view_model())
        except ValueError:
            pass

    def on_proporcion_change(self, e):
        self.controlador.mantener_proporcion = bool(self.chk_proporcion.value)

    def on_rotacion_change(self, e):
        val = float(self.slider_rotacion.value or 0.0)
        self.lbl_rotacion_val.value = f"{val:.0f}°"
        self.controlador.modificar_capa_seleccionada(rotacion=val)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_reflejo_h_click(self, e):
        capa = self.controlador.obtener_capa_seleccionada()
        if capa:
            self.controlador.modificar_capa_seleccionada(reflejo_h=not capa.reflejo_h)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_reflejo_v_click(self, e):
        capa = self.controlador.obtener_capa_seleccionada()
        if capa:
            self.controlador.modificar_capa_seleccionada(reflejo_v=not capa.reflejo_v)
            self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_opacidad_change(self, e):
        val = float(self.slider_opacidad.value or 1.0)
        self.lbl_opacidad_val.value = f"{int(val * 100)}%"
        self.controlador.modificar_capa_seleccionada(opacidad=val)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_ajustar_cubrir_click(self, e):
        self.controlador.ajustar_capa_cubrir()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_ajustar_contener_click(self, e):
        self.controlador.ajustar_capa_contener()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_ajustar_estirar_click(self, e):
        self.controlador.ajustar_capa_estirar()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_ajustar_ancho_click(self, e):
        self.controlador.ajustar_capa_ancho()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_ajustar_alto_click(self, e):
        self.controlador.ajustar_capa_alto()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_centrar_capa_click(self, e):
        self.controlador.centrar_capa_seleccionada()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _empujar_capa(self, dx: float = 0.0, dy: float = 0.0, drot: float = 0.0):
        self.controlador.empujar_capa_seleccionada(dx=dx, dy=dy, drot=drot)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _fijar_rotacion_0(self):
        self.controlador.modificar_capa_seleccionada(rotacion=0.0)
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_toggle_ver_cuadricula(self, e):
        self.controlador.cambiar_diseno_ver_cuadricula(bool(self.chk_ver_cuadricula.value))
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_toggle_ver_rotulos(self, e):
        self.controlador.cambiar_diseno_ver_rotulos(bool(self.chk_ver_rotulos.value))
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_toggle_ver_costuras(self, e):
        self.controlador.cambiar_diseno_ver_costuras(bool(self.chk_ver_costuras.value))
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_toggle_mostrar_reflejo(self, e):
        self.controlador.cambiar_diseno_mostrar_reflejo(bool(self.chk_mostrar_reflejo.value))
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def on_cambio_modo_interaccion(self, e):
        sel = self.selector_interaccion_diseno.selected
        self.modo_interaccion_diseno = sel[0] if sel else "navegar"

    async def on_exportar_abanico_click(self, e):
        nom_def = f"abanico_{self.controlador.diseno_seccion}.svg"
        ruta = await self.file_picker.save_file(
            dialog_title="Guardar abanico con diseño (SVG)",
            file_name=nom_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["svg"],
        )
        if ruta:
            try:
                self.controlador.exportar_abanico_diseno(ruta)
                self._mostrar_snackbar(f"Abanico guardado: {os.path.basename(ruta)}")
            except Exception as ex:
                self._mostrar_snackbar(f"Error al exportar abanico: {ex}")

    async def on_exportar_gajos_click(self, e):
        carpeta = await self.file_picker.get_directory_path(dialog_title="Seleccionar carpeta para exportar gajos")
        if carpeta:
            try:
                archs = self.controlador.exportar_gajos_diseno(carpeta)
                self._mostrar_snackbar(f"{len(archs)} gajos exportados en {os.path.basename(carpeta)}")
            except Exception as ex:
                self._mostrar_snackbar(f"Error al exportar gajos: {ex}")

    async def on_exportar_hoja_diseno_click(self, e):
        nom_def = f"hoja_carta_diseno_{self.controlador.diseno_seccion}.svg"
        ruta = await self.file_picker.save_file(
            dialog_title="Guardar hoja Carta con diseño",
            file_name=nom_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["svg"],
        )
        if ruta:
            try:
                self.controlador.exportar_hoja_diseno(ruta)
                self._mostrar_snackbar(f"Hoja decorada guardada: {os.path.basename(ruta)}")
            except Exception as ex:
                self._mostrar_snackbar(f"Error al exportar hoja decorada: {ex}")

