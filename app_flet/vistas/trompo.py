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
from app_flet.vistas.pestanas.diseno import PestanaDiseno
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
        self._controlador = ControladorTrompo(estilo_svg=PANTALLA_OSCURO)

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
        self.pestana_diseno = PestanaDiseno(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            debug_mode=self.debug_mode,
            obtener_pagina=lambda: self.obtener_pagina,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda **kwargs: self._sync_controlador_a_vista(self.controlador.get_view_model(), **kwargs),
        )
        self.selector_seccion_diseno = self.pestana_diseno.selector_seccion_diseno
        self.selector_variante_pico_diseno = self.pestana_diseno.selector_variante_pico_diseno
        self.segmento_completo_diseno = self.pestana_diseno.segmento_completo_diseno
        self.segmento_mitad_diseno = self.pestana_diseno.segmento_mitad_diseno
        self.selector_lienzo_diseno = self.pestana_diseno.selector_lienzo_diseno
        self.chk_ver_cuadricula = self.pestana_diseno.chk_ver_cuadricula
        self.chk_ver_rotulos = self.pestana_diseno.chk_ver_rotulos
        self.chk_ver_costuras = self.pestana_diseno.chk_ver_costuras
        self.chk_mostrar_reflejo = self.pestana_diseno.chk_mostrar_reflejo
        self.selector_interaccion_diseno = self.pestana_diseno.selector_interaccion_diseno
        self.barra_herramientas_diseno = self.pestana_diseno.barra_herramientas_diseno
        self.btn_anadir_capa = self.pestana_diseno.btn_anadir_capa
        self.col_lista_capas = self.pestana_diseno.col_lista_capas
        self.txt_nombre_capa = self.pestana_diseno.txt_nombre_capa
        self.txt_pos_x = self.pestana_diseno.txt_pos_x
        self.txt_pos_y = self.pestana_diseno.txt_pos_y
        self.txt_ancho_capa = self.pestana_diseno.txt_ancho_capa
        self.txt_alto_capa = self.pestana_diseno.txt_alto_capa
        self.chk_proporcion = self.pestana_diseno.chk_proporcion
        self.slider_rotacion = self.pestana_diseno.slider_rotacion
        self.lbl_rotacion_val = self.pestana_diseno.lbl_rotacion_val
        self.btn_reflejo_h = self.pestana_diseno.btn_reflejo_h
        self.btn_reflejo_v = self.pestana_diseno.btn_reflejo_v
        self.slider_opacidad = self.pestana_diseno.slider_opacidad
        self.lbl_opacidad_val = self.pestana_diseno.lbl_opacidad_val
        self.btn_ajustar_cubrir = self.pestana_diseno.btn_ajustar_cubrir
        self.btn_ajustar_contener = self.pestana_diseno.btn_ajustar_contener
        self.btn_ajustar_estirar = self.pestana_diseno.btn_ajustar_estirar
        self.btn_ajustar_ancho = self.pestana_diseno.btn_ajustar_ancho
        self.btn_ajustar_alto = self.pestana_diseno.btn_ajustar_alto
        self.btn_centrar_capa = self.pestana_diseno.btn_centrar_capa
        self.btn_nudge_left = self.pestana_diseno.btn_nudge_left
        self.btn_nudge_right = self.pestana_diseno.btn_nudge_right
        self.btn_nudge_up = self.pestana_diseno.btn_nudge_up
        self.btn_nudge_down = self.pestana_diseno.btn_nudge_down
        self.btn_rot_m5 = self.pestana_diseno.btn_rot_m5
        self.btn_rot_p5 = self.pestana_diseno.btn_rot_p5
        self.btn_rot_0 = self.pestana_diseno.btn_rot_0
        self.panel_inspector_capa = self.pestana_diseno.panel_inspector_capa
        self.btn_exportar_abanico = self.pestana_diseno.btn_exportar_abanico
        self.btn_exportar_gajos = self.pestana_diseno.btn_exportar_gajos
        self.btn_exportar_hoja_diseno = self.pestana_diseno.btn_exportar_hoja_diseno
        self.panel_lateral_diseno = self.pestana_diseno.panel_lateral_diseno
        self.lbl_vacio_diseno = self.pestana_diseno.lbl_vacio_diseno
        self.panel_contenido_diseno = self.pestana_diseno.panel_contenido_diseno
        self.container_viewer_diseno = self.pestana_diseno.container_viewer_diseno
        self.img_svg_diseno = self.pestana_diseno.img_svg_diseno
        self.detector_gestos_diseno = self.pestana_diseno.detector_gestos_diseno
        self.btn_zoom_in_diseno = self.pestana_diseno.btn_zoom_in_diseno
        self.btn_zoom_out_diseno = self.pestana_diseno.btn_zoom_out_diseno
        self.btn_ajustar_diseno = self.pestana_diseno.btn_ajustar_diseno
        self.lbl_zoom_diseno_porcentaje = self.pestana_diseno.lbl_zoom_diseno_porcentaje
        self.lbl_instruccion_zoom_diseno = self.pestana_diseno.lbl_instruccion_zoom_diseno
        self.lbl_estado_diseno = self.pestana_diseno.lbl_estado_diseno
        self.barra_zoom_diseno = self.pestana_diseno.barra_zoom_diseno
        self.lbl_debug_diseno = self.pestana_diseno.lbl_debug_diseno
        self.visor_diseno = self.pestana_diseno.visor
        tab_diseno = self.pestana_diseno.construir()

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

    @property
    def controlador(self) -> ControladorTrompo:
        return self._controlador

    @controlador.setter
    def controlador(self, c: ControladorTrompo) -> None:
        self._controlador = c
        if hasattr(self, "pestana_resumen"):
            self.pestana_resumen.controlador = c
        if hasattr(self, "pestana_tablas"):
            self.pestana_tablas.controlador = c
        if hasattr(self, "pestana_moldes2d"):
            self.pestana_moldes2d.controlador = c
        if hasattr(self, "pestana_hoja"):
            self.pestana_hoja.controlador = c
        if hasattr(self, "pestana_vista3d"):
            self.pestana_vista3d.controlador = c
        if hasattr(self, "pestana_diseno"):
            self.pestana_diseno.controlador = c

    def _on_tabs_change(self, e):
        if getattr(self, "arrastrando_capa", False):
            self.pestana_diseno.gestor_visor.finalizar_arrastre_capa()

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

        # 8. Vista 3D y lista de compra (F4)
        self.pestana_vista3d.actualizar(vm)

        # 9. Pestaña Diseño (F6a)
        self.pestana_diseno.actualizar(vm, reset_zoom=reset_zoom)

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
    # --- MÉTODOS DE LA PESTAÑA DISEÑO (Delegados en PestanaDiseno) ---
    # =========================================================================
    @property
    def arrastrando_capa(self) -> bool:
        return self.pestana_diseno.gestor_visor.arrastrando_capa

    @arrastrando_capa.setter
    def arrastrando_capa(self, val: bool) -> None:
        self.pestana_diseno.gestor_visor.arrastrando_capa = val

    @property
    def modo_interaccion_diseno(self) -> str:
        return self.pestana_diseno.gestor_visor.modo_interaccion_diseno

    @modo_interaccion_diseno.setter
    def modo_interaccion_diseno(self, val: str) -> None:
        self.pestana_diseno.gestor_visor.modo_interaccion_diseno = val

    @property
    def telemetria_arrastre_eventos(self) -> int:
        return self.pestana_diseno.gestor_visor.telemetria_arrastre_eventos

    @telemetria_arrastre_eventos.setter
    def telemetria_arrastre_eventos(self, val: int) -> None:
        self.pestana_diseno.gestor_visor.telemetria_arrastre_eventos = val

    def _renderizar_diseno(self, reset_vista: bool = False):
        self.pestana_diseno.gestor_visor.renderizar_diseno(reset_vista=reset_vista)

    def _ajustar_vista_diseno(self):
        self.pestana_diseno.gestor_visor.ajustar_vista()

    def on_cambio_seccion_diseno(self, e):
        self.pestana_diseno.on_cambio_seccion_diseno(e)

    def on_cambio_variante_diseno(self, e):
        self.pestana_diseno.on_cambio_variante_diseno(e)

    def on_cambio_lienzo_diseno(self, e):
        self.pestana_diseno.on_cambio_lienzo_diseno(e)

    async def on_anadir_capa_click(self, e):
        await self.pestana_diseno.inspector.on_anadir_capa_click(e)

    def _empujar_capa(self, dx: float = 0.0, dy: float = 0.0, drot: float = 0.0):
        self.pestana_diseno.inspector._empujar_capa(dx=dx, dy=dy, drot=drot)

    def _fijar_rotacion_0(self):
        self.pestana_diseno.inspector._fijar_rotacion_0()

    async def on_exportar_abanico_click(self, e):
        await self.pestana_diseno.on_exportar_abanico_click(e)

    async def on_exportar_gajos_click(self, e):
        await self.pestana_diseno.on_exportar_gajos_click(e)

    async def on_exportar_hoja_diseno_click(self, e):
        await self.pestana_diseno.on_exportar_hoja_diseno_click(e)

    def obtener_estado_telemetria(self) -> dict:
        return self.pestana_diseno.gestor_visor.obtener_estado_telemetria()

    @property
    def _id_recomposicion_diseno(self) -> int:
        return self.pestana_diseno._id_recomposicion_diseno

    @_id_recomposicion_diseno.setter
    def _id_recomposicion_diseno(self, val: int) -> None:
        self.pestana_diseno._id_recomposicion_diseno = val

    def _on_gesture_diseno_pan_start(self, e):
        self.pestana_diseno.gestor_visor._on_gesture_pan_start(e)

    def _on_gesture_diseno_pan_update(self, e):
        self.pestana_diseno.gestor_visor._on_gesture_pan_update(e)

    def _on_gesture_diseno_pan_end(self, e):
        self.pestana_diseno.gestor_visor._on_gesture_pan_end(e)

    def _on_gesture_diseno_pan_cancel(self, e):
        self.pestana_diseno.gestor_visor._on_gesture_pan_cancel(e)

    def _on_gesture_diseno_exit(self, e):
        self.pestana_diseno.gestor_visor._on_gesture_exit(e)

    def _timeout_arrastre_capa(self):
        self.pestana_diseno.gestor_visor._timeout_arrastre_capa()

    def _finalizar_arrastre_capa(self):
        self.pestana_diseno.gestor_visor.finalizar_arrastre_capa()

    def on_pos_x_change(self, e):
        self.pestana_diseno.inspector.on_pos_x_change(e)

    def on_pos_y_change(self, e):
        self.pestana_diseno.inspector.on_pos_y_change(e)

    def on_ancho_capa_change(self, e):
        self.pestana_diseno.inspector.on_ancho_capa_change(e)

    def on_alto_capa_change(self, e):
        self.pestana_diseno.inspector.on_alto_capa_change(e)

    def on_nombre_capa_change(self, e):
        self.pestana_diseno.inspector.on_nombre_capa_change(e)

    def on_proporcion_change(self, e):
        self.pestana_diseno.inspector.on_proporcion_change(e)

    def on_rotacion_change(self, e):
        self.pestana_diseno.inspector.on_rotacion_change(e)

    def on_opacidad_change(self, e):
        self.pestana_diseno.inspector.on_opacidad_change(e)

    def on_reflejo_h_click(self, e):
        self.pestana_diseno.inspector.on_reflejo_h_click(e)

    def on_reflejo_v_click(self, e):
        self.pestana_diseno.inspector.on_reflejo_v_click(e)

    def on_ajustar_cubrir_click(self, e):
        self.pestana_diseno.inspector.on_ajustar_cubrir_click(e)

    def on_ajustar_contener_click(self, e):
        self.pestana_diseno.inspector.on_ajustar_contener_click(e)

    def on_ajustar_estirar_click(self, e):
        self.pestana_diseno.inspector.on_ajustar_estirar_click(e)

    def on_ajustar_ancho_click(self, e):
        self.pestana_diseno.inspector.on_ajustar_ancho_click(e)

    def on_ajustar_alto_click(self, e):
        self.pestana_diseno.inspector.on_ajustar_alto_click(e)

    def on_centrar_capa_click(self, e):
        self.pestana_diseno.inspector.on_centrar_capa_click(e)

    def on_toggle_ver_cuadricula(self, e):
        self.pestana_diseno.on_toggle_ver_cuadricula(e)

    def on_toggle_ver_rotulos(self, e):
        self.pestana_diseno.on_toggle_ver_rotulos(e)

    def on_toggle_ver_costuras(self, e):
        self.pestana_diseno.on_toggle_ver_costuras(e)

    def on_toggle_mostrar_reflejo(self, e):
        self.pestana_diseno.on_toggle_mostrar_reflejo(e)


