# app_flet/vistas/trompo.py
import os
import time
import asyncio
import threading
import webbrowser
from typing import Optional, Tuple
import flet as ft
from app_flet.controlador import ControladorTrompo, ViewModelTrompo
from app_flet import tema
from app_flet.vistas.tabla_molde import TablaMoldePersonalizada
from app_flet.vistas.componentes.visor_svg import VisorSvg
from app_flet.vistas.pestanas.resumen import PestanaResumen
from app_flet.vistas.pestanas.tablas import PestanaTablas
from app_flet.vistas.pestanas.moldes2d import PestanaMoldes2D
from app_flet.vistas.pestanas.hoja import PestanaHoja
from app_flet.vistas.pestanas.vista3d import PestanaVista3D
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
from logic.diseno.pintura import VariantePico, color_de_cara
from logic.geometria.malla_trompo import Cara
from logic.registro import logger

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
        self.pestana_resumen = PestanaResumen(self.paleta)
        self.lbl_desactualizado = self.pestana_resumen.lbl_desactualizado
        self.grid_tarjetas = self.pestana_resumen.grid_tarjetas
        self.col_avisos = self.pestana_resumen.col_avisos
        tab_resumen = self.pestana_resumen.construir()

        # 2. Pestaña Tablas
        self.pestana_tablas = PestanaTablas(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_clipboard=self.servicio_clipboard,
            on_mostrar_snackbar=self._mostrar_snackbar,
            obtener_pagina=lambda: self.obtener_pagina,
        )
        self.selector_tabla = self.pestana_tablas.selector_tabla
        self.lbl_vacio_tablas = self.pestana_tablas.lbl_vacio_tablas
        self.lbl_titulo_tabla = self.pestana_tablas.lbl_titulo_tabla
        self.lbl_resumen_tabla = self.pestana_tablas.lbl_resumen_tabla
        self.lbl_nota_tabla = self.pestana_tablas.lbl_nota_tabla
        self.btn_copiar_tabla = self.pestana_tablas.btn_copiar_tabla
        self.tabla_componente = self.pestana_tablas.tabla_componente
        self.panel_contenido_tablas = self.pestana_tablas.panel_contenido_tablas
        tab_tablas = self.pestana_tablas.construir()

        # 3. Pestaña Moldes 2D con zoom vectorial por viewBox
        self.pestana_moldes2d = PestanaMoldes2D(self.paleta, self.controlador)
        self.selector_molde = self.pestana_moldes2d.selector_molde
        self.lbl_vacio_moldes = self.pestana_moldes2d.lbl_vacio_moldes
        self.panel_contenido_moldes = self.pestana_moldes2d.panel_contenido_moldes
        self.visor_moldes = self.pestana_moldes2d.visor_moldes
        self.container_viewer_svg = self.pestana_moldes2d.container_viewer_svg
        self.img_svg = self.pestana_moldes2d.img_svg
        self.detector_gestos = self.pestana_moldes2d.detector_gestos
        self.barra_zoom = self.pestana_moldes2d.barra_zoom
        self.lbl_zoom_porcentaje = self.pestana_moldes2d.lbl_zoom_porcentaje
        self.btn_zoom_in = self.pestana_moldes2d.btn_zoom_in
        self.btn_zoom_out = self.pestana_moldes2d.btn_zoom_out
        self.btn_ajustar = self.pestana_moldes2d.btn_ajustar
        self.lbl_instruccion_zoom = self.pestana_moldes2d.lbl_instruccion_zoom
        self.lbl_debug = self.pestana_moldes2d.lbl_debug
        self.debug_mode = self.pestana_moldes2d.debug_mode
        self._padding_container = self.pestana_moldes2d._padding_container
        self._border_width = self.pestana_moldes2d._border_width
        self.lbl_pie_moldes = self.pestana_moldes2d.lbl_pie_moldes
        tab_2d = self.pestana_moldes2d.construir()

        # 4. Pestaña Hoja de trazo (F3)
        self.pestana_hoja = PestanaHoja(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda reset_zoom: self._sync_controlador_a_vista(self.controlador.get_view_model(), reset_zoom=reset_zoom),
        )
        self.selector_pieza_hoja = self.pestana_hoja.selector_pieza_hoja
        self.selector_lienzo = self.pestana_hoja.selector_lienzo
        self.segmento_completo_hoja = self.pestana_hoja.segmento_completo_hoja
        self.segmento_mitad_hoja = self.pestana_hoja.segmento_mitad_hoja
        self.selector_modo_dibujo = self.pestana_hoja.selector_modo_dibujo
        self.btn_sincronizar_conos = self.pestana_hoja.btn_sincronizar_conos
        self.btn_copiar_config_hoja = self.pestana_hoja.btn_copiar_config_hoja
        self.dd_repeticion_pico_hoja = self.pestana_hoja.dd_repeticion_pico_hoja
        self.lbl_resumen_pico = self.pestana_hoja.lbl_resumen_pico
        self.panel_diseno_pico_hoja = self.pestana_hoja.panel_diseno_pico_hoja
        self.dd_modo_esquema = self.pestana_hoja.dd_modo_esquema
        self.txt_tam_grupo = self.pestana_hoja.txt_tam_grupo
        self.txt_ciclo_personalizado = self.pestana_hoja.txt_ciclo_personalizado
        self.dd_hoja = self.pestana_hoja.dd_hoja
        self.dd_escala = self.pestana_hoja.dd_escala
        self.btn_exportar_hoja = self.pestana_hoja.btn_exportar_hoja
        self.btn_exportar_paquete = self.pestana_hoja.btn_exportar_paquete
        self.lbl_error_esquema = self.pestana_hoja.lbl_error_esquema
        self.lbl_aviso_hoja = self.pestana_hoja.lbl_aviso_hoja
        self.col_resumen_esquema = self.pestana_hoja.col_resumen_esquema
        self.visor_hoja = self.pestana_hoja.visor_hoja
        self.container_viewer_hoja = self.pestana_hoja.container_viewer_hoja
        self.img_svg_hoja = self.pestana_hoja.img_svg_hoja
        self.detector_gestos_hoja = self.pestana_hoja.detector_gestos_hoja
        self.barra_zoom_hoja = self.pestana_hoja.barra_zoom_hoja
        self.lbl_zoom_hoja_porcentaje = self.pestana_hoja.lbl_zoom_hoja_porcentaje
        self.btn_zoom_in_hoja = self.pestana_hoja.btn_zoom_in_hoja
        self.btn_zoom_out_hoja = self.pestana_hoja.btn_zoom_out_hoja
        self.btn_ajustar_hoja = self.pestana_hoja.btn_ajustar_hoja
        self.lbl_instruccion_zoom_hoja = self.pestana_hoja.lbl_instruccion_zoom_hoja
        self.lbl_debug_hoja = self.pestana_hoja.lbl_debug_hoja
        self.lbl_vacio_hoja = self.pestana_hoja.lbl_vacio_hoja
        self.panel_contenido_hoja = self.pestana_hoja.panel_contenido_hoja
        tab_hoja = self.pestana_hoja.construir()

        # 5. Pestaña Vista 3D (F4)
        self.pestana_vista3d = PestanaVista3D(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            servicio_clipboard=self.servicio_clipboard,
            obtener_pagina=lambda: self.obtener_pagina,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda: self._sync_controlador_a_vista(self.controlador.get_view_model()),
        )
        self.catalogo_papel = self.pestana_vista3d.catalogo_papel
        self.dd_modo_sup = self.pestana_vista3d.dd_modo_sup
        self.txt_tam_bloque_sup = self.pestana_vista3d.txt_tam_bloque_sup
        self.col_colores_sup = self.pestana_vista3d.col_colores_sup
        self.btn_agregar_color_sup = self.pestana_vista3d.btn_agregar_color_sup
        self.chk_mismo_esquema_inf = self.pestana_vista3d.chk_mismo_esquema_inf
        self.dd_modo_inf = self.pestana_vista3d.dd_modo_inf
        self.txt_tam_bloque_inf = self.pestana_vista3d.txt_tam_bloque_inf
        self.col_colores_inf = self.pestana_vista3d.col_colores_inf
        self.btn_agregar_color_inf = self.pestana_vista3d.btn_agregar_color_inf
        self.container_controles_inf = self.pestana_vista3d.container_controles_inf
        self.dd_modo_caras_var_a = self.pestana_vista3d.dd_modo_caras_var_a
        self.col_colores_var_a = self.pestana_vista3d.col_colores_var_a
        self.chk_usar_var_b = self.pestana_vista3d.chk_usar_var_b
        self.dd_repeticion_picos = self.pestana_vista3d.dd_repeticion_picos
        self.dd_modo_caras_var_b = self.pestana_vista3d.dd_modo_caras_var_b
        self.col_colores_var_b = self.pestana_vista3d.col_colores_var_b
        self.panel_variante_b = self.pestana_vista3d.panel_variante_b
        self.dd_filtro_marca = self.pestana_vista3d.dd_filtro_marca
        self.btn_agregar_color_catalogo = self.pestana_vista3d.btn_agregar_color_catalogo
        self.btn_importar_csv = self.pestana_vista3d.btn_importar_csv
        self.btn_exportar_csv = self.pestana_vista3d.btn_exportar_csv
        self.fila_previa_sup = self.pestana_vista3d.fila_previa_sup
        self.col_previa_picos = self.pestana_vista3d.col_previa_picos
        self.fila_previa_inf = self.pestana_vista3d.fila_previa_inf
        self.txt_pliego_ancho = self.pestana_vista3d.txt_pliego_ancho
        self.txt_pliego_alto = self.pestana_vista3d.txt_pliego_alto
        self.txt_pliegos_paquete = self.pestana_vista3d.txt_pliegos_paquete
        self.lbl_aviso_colores = self.pestana_vista3d.lbl_aviso_colores
        self.btn_abrir_visor_3d = self.pestana_vista3d.btn_abrir_visor_3d
        self.btn_exportar_visor_3d = self.pestana_vista3d.btn_exportar_visor_3d
        self.btn_copiar_compra = self.pestana_vista3d.btn_copiar_compra
        self.tabla_compra = self.pestana_vista3d.tabla_compra
        self.lbl_vacio_3d = self.pestana_vista3d.lbl_vacio_3d
        self.panel_contenido_3d = self.pestana_vista3d.panel_contenido_3d
        tab_3d = self.pestana_vista3d.construir()

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

        # Visor interactivo del diseño (compartido)
        self.visor_diseno = VisorSvg(
            papel_blanco=True,
            drag_interval=35,
            margen_ajuste=0.04,
            on_custom_pan_start=self._on_gesture_diseno_pan_start,
            on_custom_pan_update=self._on_gesture_diseno_pan_update,
            on_custom_pan_end=self._on_gesture_diseno_pan_end,
            on_custom_pan_cancel=self._on_gesture_diseno_pan_cancel,
            on_custom_exit=self._on_gesture_diseno_exit,
        )
        self.container_viewer_diseno = self.visor_diseno.container_viewer_svg
        self.img_svg_diseno = self.visor_diseno.img_svg
        self.detector_gestos_diseno = self.visor_diseno.detector_gestos
        self.btn_zoom_in_diseno = self.visor_diseno.btn_zoom_in
        self.btn_zoom_out_diseno = self.visor_diseno.btn_zoom_out
        self.btn_ajustar_diseno = self.visor_diseno.btn_ajustar
        self.lbl_zoom_diseno_porcentaje = self.visor_diseno.lbl_zoom_porcentaje
        self.lbl_instruccion_zoom_diseno = self.visor_diseno.lbl_instruccion_zoom
        self.lbl_debug_diseno = self.visor_diseno.lbl_debug
        self._svg_diseno_raw: str = ""

        self.lbl_estado_diseno = ft.Text(
            "",
            size=11,
            color=ft.Colors.PRIMARY,
            weight=ft.FontWeight.W_500,
            italic=True,
        )
        self.barra_zoom_diseno = ft.Row(
            controls=[
                self.btn_zoom_out_diseno,
                self.lbl_zoom_diseno_porcentaje,
                self.btn_zoom_in_diseno,
                self.btn_ajustar_diseno,
                self.lbl_estado_diseno,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        # Telemetría de arrastre y recomposición de diseño
        self.telemetria_arrastre_eventos: int = 0
        self.telemetria_arrastre_inicio_ts: float = 0.0
        self.telemetria_eventos_por_segundo: float = 0.0
        self.telemetria_ms_ultima_recomposicion: float = 0.0
        self.telemetria_recomposiciones_pendientes: int = 0
        self.telemetria_recomposiciones_descartadas: int = 0
        self.arrastrando_capa: bool = False
        self._id_recomposicion_diseno: int = 0
        self._recomponiendo_diseno: bool = False
        self._timer_seguridad_arrastre: Optional[threading.Timer] = None
        self._actualizando_programatico: bool = False
        self.lbl_debug_diseno = ft.Text(
            "",
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
            visible=self.debug_mode,
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
                        ft.Row([self.lbl_debug_diseno], alignment=ft.MainAxisAlignment.CENTER) if self.debug_mode else ft.Container(),
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
            on_change=self._on_tabs_change,
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
        self.pestana_resumen.aplicar_tema(self.paleta)
        self.pestana_tablas.aplicar_tema(self.paleta)

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
        self.pestana_tablas.on_cambio_pieza_tabla(e)

    def on_copiar_tabla(self, e):
        self.pestana_tablas.on_copiar_tabla(e)

    def on_cambio_pieza_molde(self, e):
        self.pestana_moldes2d.on_cambio_pieza_molde(e)

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
        if getattr(self, "arrastrando_capa", False):
            self._finalizar_arrastre_capa()
        self._leer_vista_a_controlador()
        vm = self.controlador.calcular()
        self._sync_controlador_a_vista(vm, reset_zoom=True)

    def _renderizar_tabla_seleccionada(self):
        self.pestana_tablas.renderizar_tabla_seleccionada()

    def _porcentaje_zoom(self) -> float:
        if not self.vista_base_svg or not self.vista_svg or self.vista_svg.ancho <= 0:
            return 100.0
        return (self.vista_base_svg.ancho / self.vista_svg.ancho) * 100.0

    # Propiedades delegadas al componente VisorSvg
    @property
    def vista_svg(self) -> Optional[VistaSvg]:
        return self.visor_moldes.vista_svg if hasattr(self, "visor_moldes") else None

    @vista_svg.setter
    def vista_svg(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_moldes"):
            self.visor_moldes.vista_svg = val

    @property
    def _svg_actual_raw(self) -> str:
        return self.pestana_moldes2d._svg_actual_raw if hasattr(self, "pestana_moldes2d") else ""

    @_svg_actual_raw.setter
    def _svg_actual_raw(self, val: str) -> None:
        if hasattr(self, "pestana_moldes2d"):
            self.pestana_moldes2d._svg_actual_raw = val

    @property
    def vista_base_svg(self) -> Optional[VistaSvg]:
        return self.visor_moldes.vista_base_svg if hasattr(self, "visor_moldes") else None

    @vista_base_svg.setter
    def vista_base_svg(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_moldes"):
            self.visor_moldes.vista_base_svg = val

    @property
    def zona_ancho(self) -> float:
        return self.visor_moldes.zona_ancho if hasattr(self, "visor_moldes") else 600.0

    @zona_ancho.setter
    def zona_ancho(self, val: float) -> None:
        if hasattr(self, "visor_moldes"):
            self.visor_moldes.zona_ancho = val

    @property
    def zona_alto(self) -> float:
        return self.visor_moldes.zona_alto if hasattr(self, "visor_moldes") else 500.0

    @zona_alto.setter
    def zona_alto(self, val: float) -> None:
        if hasattr(self, "visor_moldes"):
            self.visor_moldes.zona_alto = val

    @property
    def vista_svg_hoja(self) -> Optional[VistaSvg]:
        return self.visor_hoja.vista_svg if hasattr(self, "visor_hoja") else None

    @vista_svg_hoja.setter
    def vista_svg_hoja(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_hoja"):
            self.visor_hoja.vista_svg = val

    @property
    def vista_base_svg_hoja(self) -> Optional[VistaSvg]:
        return self.visor_hoja.vista_base_svg if hasattr(self, "visor_hoja") else None

    @vista_base_svg_hoja.setter
    def vista_base_svg_hoja(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_hoja"):
            self.visor_hoja.vista_base_svg = val

    @property
    def zona_ancho_hoja(self) -> float:
        return self.visor_hoja.zona_ancho if hasattr(self, "visor_hoja") else 600.0

    @zona_ancho_hoja.setter
    def zona_ancho_hoja(self, val: float) -> None:
        if hasattr(self, "visor_hoja"):
            self.visor_hoja.zona_ancho = val

    @property
    def zona_alto_hoja(self) -> float:
        return self.visor_hoja.zona_alto if hasattr(self, "visor_hoja") else 500.0

    @zona_alto_hoja.setter
    def zona_alto_hoja(self, val: float) -> None:
        if hasattr(self, "visor_hoja"):
            self.visor_hoja.zona_alto = val

    @property
    def _svg_hoja_raw(self) -> str:
        return self.pestana_hoja._svg_hoja_raw if hasattr(self, "pestana_hoja") else ""

    @_svg_hoja_raw.setter
    def _svg_hoja_raw(self, val: str) -> None:
        if hasattr(self, "pestana_hoja"):
            self.pestana_hoja._svg_hoja_raw = val

    @property
    def vista_svg_diseno(self) -> Optional[VistaSvg]:
        return self.visor_diseno.vista_svg if hasattr(self, "visor_diseno") else None

    @vista_svg_diseno.setter
    def vista_svg_diseno(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_diseno"):
            self.visor_diseno.vista_svg = val

    @property
    def vista_base_svg_diseno(self) -> Optional[VistaSvg]:
        return self.visor_diseno.vista_base_svg if hasattr(self, "visor_diseno") else None

    @vista_base_svg_diseno.setter
    def vista_base_svg_diseno(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_diseno"):
            self.visor_diseno.vista_base_svg = val

    @property
    def zona_ancho_diseno(self) -> float:
        return self.visor_diseno.zona_ancho if hasattr(self, "visor_diseno") else 600.0

    @zona_ancho_diseno.setter
    def zona_ancho_diseno(self, val: float) -> None:
        if hasattr(self, "visor_diseno"):
            self.visor_diseno.zona_ancho = val

    @property
    def zona_alto_diseno(self) -> float:
        return self.visor_diseno.zona_alto if hasattr(self, "visor_diseno") else 500.0

    @zona_alto_diseno.setter
    def zona_alto_diseno(self, val: float) -> None:
        if hasattr(self, "visor_diseno"):
            self.visor_diseno.zona_alto = val

    def _limites_zoom(self) -> Tuple[float, float]:
        return self.visor_moldes.limites_zoom()

    def _on_container_size_change(self, e):
        self.visor_moldes.on_container_size_change(e)

    def _renderizar_molde_seleccionado(self, reset_vista: bool = False):
        self.pestana_moldes2d.renderizar_molde_seleccionado(reset_vista=reset_vista)

    def _actualizar_debug(self):
        self.visor_moldes.actualizar_debug()

    def _actualizar_imagen_zoom(self, force: bool = False, t_inicio_evento: Optional[float] = None):
        self.visor_moldes.actualizar_imagen_zoom(force=force, t_inicio_evento=t_inicio_evento)

    def _on_gesture_scroll(self, e: ft.ScrollEvent):
        self.visor_moldes.on_gesture_scroll(e)

    def _on_gesture_pan_update(self, e: ft.DragUpdateEvent):
        self.visor_moldes.on_gesture_pan_update(e)

    def _on_gesture_double_tap(self, e):
        self.visor_moldes.ajustar_vista()

    def _on_btn_zoom_in(self, e):
        self.visor_moldes.zoom_in()

    def _on_btn_zoom_out(self, e):
        self.visor_moldes.zoom_out()

    def _on_btn_ajustar(self, e):
        self.visor_moldes.ajustar_vista()

    def _ajustar_vista(self):
        self.visor_moldes.ajustar_vista()

    def _porcentaje_zoom(self) -> float:
        return self.visor_moldes.porcentaje_zoom()

    def _sync_controlador_a_vista(self, vm: ViewModelTrompo, diferir_update: bool = False, reset_zoom: bool = False):
        # 1. Error
        if vm.mensaje_error:
            self.lbl_error.value = vm.mensaje_error
            self.lbl_error.visible = True
        else:
            self.lbl_error.visible = False
            
        # 2, 3 y 4. Resumen (desactualizado, tarjetas, avisos)
        self.pestana_resumen.actualizar(vm)

        # 5. Tablas
        self.pestana_tablas.actualizar(vm)

        # 6. Moldes 2D
        self.pestana_moldes2d.actualizar(vm, reset_zoom=reset_zoom)

        # 7. Hoja de trazo (F3 y F5)
        self.pestana_hoja.actualizar(vm, reset_zoom=reset_zoom)

        # Actualizar estado de mitad en diseño
        self.segmento_mitad_diseno.disabled = not vm.puede_usar_mitad
        self.segmento_mitad_diseno.tooltip = vm.motivo_no_mitad if not vm.puede_usar_mitad else "Diseño sobre mitad con reflejo simétrico"
        self.selector_lienzo_diseno.selected = [vm.diseno_lienzo_modo]

        # 8. Vista 3D y lista de compra (F4)
        self.pestana_vista3d.actualizar(vm)

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
        self.pestana_hoja.on_cambio_pieza_hoja(e)

    def on_sincronizar_conos(self, e):
        self.pestana_hoja.on_sincronizar_conos(e)

    def on_copiar_config(self, origen: str):
        self.pestana_hoja.on_copiar_config(origen)

    def on_cambio_lienzo(self, e):
        self.pestana_hoja.on_cambio_lienzo(e)

    def on_cambio_modo_dibujo(self, e):
        self.pestana_hoja.on_cambio_modo_dibujo(e)

    def on_cambio_repeticion_pico_hoja(self, e):
        self.pestana_hoja.on_cambio_repeticion_pico_hoja(e)

    def on_cambio_esquema_opciones(self, e):
        self.pestana_hoja.on_cambio_esquema_opciones(e)

    def on_cambio_hoja_opciones(self, e):
        self.pestana_hoja.on_cambio_hoja_opciones(e)

    async def on_exportar_hoja(self, e):
        await self.pestana_hoja.on_exportar_hoja(e)

    async def on_exportar_paquete(self, e):
        await self.pestana_hoja.on_exportar_paquete(e)

    @property
    def filtro_marca_actual(self) -> str:
        return self.pestana_vista3d.filtro_marca_actual if hasattr(self, "pestana_vista3d") else "todas"

    @filtro_marca_actual.setter
    def filtro_marca_actual(self, val: str) -> None:
        if hasattr(self, "pestana_vista3d"):
            self.pestana_vista3d.filtro_marca_actual = val

    def _opciones_colores_filtradas(self) -> list:
        return self.pestana_vista3d._opciones_colores_filtradas()

    def _actualizar_dropdowns_patrones(self):
        self.pestana_vista3d._actualizar_dropdowns_patrones()

    def _actualizar_vista_previa_2d(self):
        self.pestana_vista3d._actualizar_vista_previa_2d()

    def on_cambio_patron_ui(self, e):
        self.pestana_vista3d.on_cambio_patron_ui(e)

    def on_cambio_color_ciclo_sup(self, idx: int, cid: str):
        self.pestana_vista3d.on_cambio_color_ciclo_sup(idx, cid)

    def on_agregar_color_sup(self, e):
        self.pestana_vista3d.on_agregar_color_sup(e)

    def on_eliminar_color_ciclo_sup(self, idx: int):
        self.pestana_vista3d.on_eliminar_color_ciclo_sup(idx)

    def on_cambio_color_ciclo_inf(self, idx: int, cid: str):
        self.pestana_vista3d.on_cambio_color_ciclo_inf(idx, cid)

    def on_agregar_color_inf(self, e):
        self.pestana_vista3d.on_agregar_color_inf(e)

    def on_eliminar_color_ciclo_inf(self, idx: int):
        self.pestana_vista3d.on_eliminar_color_ciclo_inf(idx)

    def on_cambio_color_variante(self, nombre_var: str, cara_idx: int, cid: str):
        self.pestana_vista3d.on_cambio_color_variante(nombre_var, cara_idx, cid)

    def on_cambio_filtro_marca(self, e):
        self.pestana_vista3d.on_cambio_filtro_marca(e)

    def on_cambio_pliegos_paquete(self, e):
        self.pestana_vista3d.on_cambio_pliegos_paquete(e)

    def on_cambio_tam_pliego(self, e):
        self.pestana_vista3d.on_cambio_tam_pliego(e)

    async def on_dialogo_agregar_color(self, e):
        await self.pestana_vista3d.on_dialogo_agregar_color(e)

    async def on_importar_catalogo_csv(self, e):
        await self.pestana_vista3d.on_importar_catalogo_csv(e)

    async def on_exportar_catalogo_csv(self, e):
        await self.pestana_vista3d.on_exportar_catalogo_csv(e)

    def on_abrir_visor_3d(self, e):
        self.pestana_vista3d.on_abrir_visor_3d(e)

    async def on_exportar_visor_3d(self, e):
        await self.pestana_vista3d.on_exportar_visor_3d(e)

    def on_copiar_lista_compra(self, e):
        self.pestana_vista3d.on_copiar_lista_compra(e)

    def _renderizar_hoja(self, reset_vista: bool = False):
        self.pestana_hoja.renderizar_hoja(reset_vista=reset_vista)

    def _ajustar_vista_hoja(self):
        self.visor_hoja.ajustar()


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

    def _on_gesture_diseno_pan_start(self, e):
        if self.modo_interaccion_diseno == "mover":
            capa = self.controlador.obtener_capa_seleccionada()
            if capa and not capa.bloqueada:
                self.arrastrando_capa = True
                self.telemetria_arrastre_eventos = 0
                self.telemetria_arrastre_inicio_ts = time.time()
                self._reiniciar_timer_seguridad_arrastre()
                try:
                    logger.info(f"Inicio de arrastre de capa '{capa.nombre}' (id={capa.id})")
                except Exception:
                    pass

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
            self.arrastrando_capa = True
            self.telemetria_arrastre_eventos += 1
            dt = time.time() - getattr(self, "telemetria_arrastre_inicio_ts", time.time())
            if dt > 0.05:
                self.telemetria_eventos_por_segundo = self.telemetria_arrastre_eventos / dt
            self._reiniciar_timer_seguridad_arrastre()

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

            # 1. Modificar posición en memoria sin regenerar el SVG pesado
            self.controlador.empujar_capa_seleccionada(dx=dx_cm, dy=dy_cm, actualizar_svg=False)

            # 2. Actualizar solo los campos numéricos X/Y en el inspector
            capa_act = self.controlador.obtener_capa_seleccionada()
            if capa_act:
                self._actualizando_programatico = True
                try:
                    self.txt_pos_x.value = f"{capa_act.x:.2f}"
                    self.txt_pos_y.value = f"{capa_act.y:.2f}"
                    self.txt_pos_x.update()
                    self.txt_pos_y.update()
                except Exception:
                    pass
                finally:
                    self._actualizando_programatico = False

            if self.debug_mode:
                self._actualizar_debug_diseno()
        else:
            w_control = max(50.0, self.zona_ancho_diseno)
            h_control = max(50.0, self.zona_alto_diseno)
            dx = delta.x * (self.vista_svg_diseno.ancho / w_control)
            dy = delta.y * (self.vista_svg_diseno.alto / h_control)
            limites_cont = (self.vista_base_svg_diseno.ancho, self.vista_base_svg_diseno.alto)
            self.vista_svg_diseno = desplazar(self.vista_svg_diseno, dx=dx, dy=dy, limites_contenido=limites_cont)
            self._actualizar_imagen_diseno_zoom()

    def _on_gesture_diseno_pan_end(self, e):
        self._finalizar_arrastre_capa()

    def _on_gesture_diseno_pan_cancel(self, e):
        self._finalizar_arrastre_capa()

    def _on_gesture_diseno_exit(self, e):
        if getattr(self, "arrastrando_capa", False):
            self._finalizar_arrastre_capa()

    def _reiniciar_timer_seguridad_arrastre(self):
        if self._timer_seguridad_arrastre:
            try:
                self._timer_seguridad_arrastre.cancel()
            except Exception:
                pass
        self._timer_seguridad_arrastre = threading.Timer(2.0, self._timeout_arrastre_capa)
        self._timer_seguridad_arrastre.daemon = True
        self._timer_seguridad_arrastre.start()

    def _timeout_arrastre_capa(self):
        if getattr(self, "arrastrando_capa", False):
            try:
                logger.warning("Arrastre de capa finalizado por timeout de seguridad (2.0s)")
            except Exception:
                pass
            self._finalizar_arrastre_capa()

    def _finalizar_arrastre_capa(self):
        if self._timer_seguridad_arrastre:
            try:
                self._timer_seguridad_arrastre.cancel()
            except Exception:
                pass
            self._timer_seguridad_arrastre = None

        if not getattr(self, "arrastrando_capa", False):
            return

        self.arrastrando_capa = False
        self._id_recomposicion_diseno += 1
        current_id = self._id_recomposicion_diseno
        self.telemetria_recomposiciones_pendientes += 1

        try:
            self.lbl_estado_diseno.value = "Actualizando…"
            self.lbl_estado_diseno.update()
        except Exception:
            pass

        def worker():
            t0 = time.time()
            try:
                self.controlador.actualizar_svg_diseno()
            except Exception as err:
                try:
                    logger.error(f"Error al recomponer SVG de diseño: {err}", exc_info=True)
                except Exception:
                    pass
            finally:
                ms = (time.time() - t0) * 1000.0
                self.telemetria_ms_ultima_recomposicion = ms
                self._aplicar_recomposicion_diseno(current_id)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _aplicar_recomposicion_diseno(self, req_id: int):
        self.telemetria_recomposiciones_pendientes = max(0, self.telemetria_recomposiciones_pendientes - 1)
        if req_id != self._id_recomposicion_diseno:
            self.telemetria_recomposiciones_descartadas += 1
            return

        def sync_ui():
            try:
                self.lbl_estado_diseno.value = ""
                self.lbl_estado_diseno.update()
            except Exception:
                pass
            try:
                self._sync_controlador_a_vista(self.controlador.get_view_model())
            except Exception as ex:
                try:
                    logger.error(f"Error al sincronizar vista tras recomposición: {ex}")
                except Exception:
                    pass

        page = self.obtener_pagina
        if page:
            try:
                page.run_thread(sync_ui)
            except Exception:
                sync_ui()
        else:
            sync_ui()

    def _on_tabs_change(self, e):
        if getattr(self, "arrastrando_capa", False):
            self._finalizar_arrastre_capa()

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
        if getattr(self, "_actualizando_programatico", False):
            return
        try:
            val = float(self.txt_pos_x.value or 0.0)
            self.controlador.modificar_capa_seleccionada(x=val)
            self._sync_controlador_a_vista(self.controlador.get_view_model())
        except ValueError:
            pass

    def on_pos_y_change(self, e):
        if getattr(self, "_actualizando_programatico", False):
            return
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

    def obtener_estado_telemetria(self) -> dict:
        return {
            "arrastrando": getattr(self, "arrastrando_capa", False),
            "modo": getattr(self, "modo_interaccion_diseno", "navegar"),
            "eventos_arrastre": getattr(self, "telemetria_arrastre_eventos", 0),
            "pendientes": getattr(self, "telemetria_recomposiciones_pendientes", 0),
            "descartadas": getattr(self, "telemetria_recomposiciones_descartadas", 0),
        }

    def _actualizar_debug_diseno(self):
        if not self.debug_mode:
            return
        self.lbl_debug_diseno.value = (
            f"arrastre: {self.telemetria_eventos_por_segundo:.1f} ev/s · "
            f"última recomp: {self.telemetria_ms_ultima_recomposicion:.1f} ms · "
            f"pendientes: {self.telemetria_recomposiciones_pendientes} · "
            f"descartadas: {self.telemetria_recomposiciones_descartadas}"
        )
        try:
            self.lbl_debug_diseno.update()
        except Exception:
            pass


