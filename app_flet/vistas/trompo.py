# app_flet/vistas/trompo.py
import os
import time
import asyncio
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

class VistaTrompo(ft.Container):
    def __init__(self, servicio_clipboard=None):
        super().__init__()
        self.expand = True
        self.modo_tema = ft.ThemeMode.DARK
        self.paleta = tema.obtener_paleta(self.modo_tema)
        
        self.servicio_clipboard = servicio_clipboard if servicio_clipboard is not None else ft.Clipboard()
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

        # 4. Pestaña Vista 3D
        tab_3d = ft.Container(
            content=ft.Text("3D llegará en F4", color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
        )

        # Tabs generales
        self.tabs = ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Resumen", icon=ft.Icons.DASHBOARD_OUTLINED),
                            ft.Tab(label="Tablas de moldes", icon=ft.Icons.TABLE_CHART_OUTLINED),
                            ft.Tab(label="Moldes 2D", icon=ft.Icons.IMAGE_OUTLINED),
                            ft.Tab(label="Vista 3D", icon=ft.Icons.VIEW_IN_AR_OUTLINED),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[tab_resumen, tab_tablas, tab_2d, tab_3d],
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
        self.controlador.marcar_desactualizado()
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm)

    def on_switch_avanzado(self, e):
        self.panel_avanzado.visible = self.switch_avanzado.value
        self.controlador.marcar_desactualizado()
        try:
            self.update()
        except RuntimeError:
            pass

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
        self.lbl_debug.value = f"{z_str} · {img_str} · {v_str} · {zoom_str}"
        try:
            self.lbl_debug.update()
        except Exception:
            pass

    def _actualizar_imagen_zoom(self, force: bool = False):
        if not self._svg_actual_raw or not self.vista_svg:
            return
        now = time.perf_counter()
        if not force and (now - self._ultimo_render_time < (1.0 / 30.0)):
            return
        self._ultimo_render_time = now

        svg_con_viewbox = aplicar_viewbox(self._svg_actual_raw, self.vista_svg)
        self.img_svg.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_porcentaje.value = f"{self._porcentaje_zoom():.0f} %"
        self._actualizar_debug()
        try:
            self.img_svg.update()
            self.lbl_zoom_porcentaje.update()
        except Exception:
            pass

    def _on_gesture_scroll(self, e: ft.ScrollEvent):
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
        self._actualizar_imagen_zoom()

    def _on_gesture_pan_update(self, e: ft.DragUpdateEvent):
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
            self._actualizar_imagen_zoom()

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

        if not diferir_update:
            try:
                self.update()
            except RuntimeError:
                pass
