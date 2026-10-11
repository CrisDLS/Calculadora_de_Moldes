# app_flet/vistas/trompo.py
import asyncio
from typing import Optional
import flet as ft
from app_flet.controlador import ControladorTrompo, ViewModelTrompo
from app_flet import tema
from app_flet.vistas.tabla_molde import TablaMoldePersonalizada
from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO
from presentacion.trompo_estrella import tabla_a_texto, TablaMolde

class VistaTrompo(ft.Container):
    def __init__(self, servicio_clipboard=None):
        super().__init__()
        self.expand = True
        self.modo_tema = ft.ThemeMode.DARK
        self.paleta = tema.obtener_paleta(self.modo_tema)
        
        self.servicio_clipboard = servicio_clipboard if servicio_clipboard is not None else ft.Clipboard()
        self.ultimo_mensaje_snackbar: Optional[str] = None
        self.controlador = ControladorTrompo(estilo_svg=PANTALLA_OSCURO)
        
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
            color=self.paleta.texto_secundario
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
            style=ft.ButtonStyle(color=self.paleta.texto, bgcolor=self.paleta.acento)
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
            on_click=self.on_toggle_tema,
        )
        
        self.panel_izquierdo = ft.Container(
            width=300,
            padding=20,
            bgcolor=self.paleta.panel,
            border_radius=10,
            content=ft.Column(
                controls=[
                    ft.Text("Trompo estrella", size=24, weight=ft.FontWeight.BOLD, color=self.paleta.texto),
                    ft.Divider(color=self.paleta.borde),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            controls=[
                                self.txt_altura, self.txt_gajos, self.txt_hileras, self.txt_costura,
                                ft.Divider(color=self.paleta.borde),
                                self.switch_avanzado,
                                self.panel_avanzado,
                                ft.Divider(color=self.paleta.borde),
                                self.btn_calcular,
                                self.lbl_error,
                            ],
                            spacing=10
                        )
                    ),
                    ft.Divider(color=self.paleta.borde),
                    ft.Row(
                        controls=[
                            ft.Text("Tema", size=13, color=self.paleta.texto_secundario),
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
                ft.Divider(color=self.paleta.borde),
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
            content=ft.Text("Calcula para ver las tablas", size=16, color=self.paleta.texto_secundario),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )
        self.lbl_titulo_tabla = ft.Text(size=20, weight=ft.FontWeight.BOLD, color=self.paleta.texto)
        self.lbl_resumen_tabla = ft.Text(size=14, color=self.paleta.texto_secundario)
        self.lbl_nota_tabla = ft.Container(
            content=ft.Text(size=13, color=self.paleta.color_aviso, weight=ft.FontWeight.W_500),
            bgcolor=self.paleta.panel,
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
                ft.Divider(color=self.paleta.borde),
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
                    ft.Divider(color=self.paleta.borde),
                    self.lbl_vacio_tablas,
                    self.panel_contenido_tablas,
                ]
            )
        )

        # 3. Pestaña Moldes 2D
        self.selector_molde = ft.SegmentedButton(
            selected=["0"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="0", label=ft.Text("Las 3 piezas")),
                ft.Segment(value="1", label=ft.Text("Cono superior")),
                ft.Segment(value="2", label=ft.Text("Pico")),
                ft.Segment(value="3", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_pieza_molde
        )
        self.lbl_vacio_moldes = ft.Container(
            content=ft.Text("Calcula para ver los moldes", size=16, color=self.paleta.texto_secundario),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )
        self.img_svg = ft.Image(src="", fit=ft.BoxFit.CONTAIN)
        self.viewer_svg = ft.InteractiveViewer(
            content=self.img_svg,
            min_scale=0.2,
            max_scale=10.0,
            expand=True,
        )
        self.container_viewer_svg = ft.Container(
            content=self.viewer_svg,
            border=ft.Border.all(1, self.paleta.borde),
            border_radius=8,
            expand=True,
            padding=10,
            alignment=ft.Alignment(0, 0),
        )
        self.lbl_instruccion_zoom = ft.Text(
            "Rueda del ratón: zoom · Arrastrar: mover",
            size=11,
            color=self.paleta.texto_secundario,
            text_align=ft.TextAlign.CENTER,
        )
        self.lbl_pie_moldes = ft.Text(
            "La escala y la hoja de trazo en Carta llegarán en F3.",
            size=12,
            color=self.paleta.texto_secundario,
            text_align=ft.TextAlign.CENTER,
        )
        self.panel_contenido_moldes = ft.Column(
            expand=True,
            visible=False,
            controls=[
                self.container_viewer_svg,
                ft.Row([self.lbl_instruccion_zoom], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.lbl_pie_moldes], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=6,
        )

        tab_2d = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row([self.selector_molde], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=self.paleta.borde),
                    self.lbl_vacio_moldes,
                    self.panel_contenido_moldes,
                ]
            )
        )

        # 4. Pestaña Vista 3D
        tab_3d = ft.Container(content=ft.Text("Próximamente en F4", color=self.paleta.texto_secundario), alignment=ft.Alignment(0, 0))
        
        self.tabs = ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Resumen"),
                            ft.Tab(label="Tablas"),
                            ft.Tab(label="Moldes 2D"),
                            ft.Tab(label="Vista 3D")
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[tab_resumen, tab_tablas, tab_2d, tab_3d]
                    )
                ]
            )
        )
        
        self.panel_derecho = ft.Container(
            expand=True,
            padding=10,
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
        page = self.obtener_pagina
        if page:
            page.theme_mode = self.modo_tema
            page.theme = tema.tema_claro
            page.dark_theme = tema.tema_oscuro

        # Regenerar SVG con el nuevo estilo sin recalcular
        self.controlador.cambiar_estilo(estilo)
        self._actualizar_estilos_paleta()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _actualizar_estilos_paleta(self):
        self.panel_izquierdo.bgcolor = self.paleta.panel
        self.btn_calcular.style = ft.ButtonStyle(color=self.paleta.texto, bgcolor=self.paleta.acento)
        self.lbl_error.color = self.paleta.color_error
        self.lbl_desactualizado.color = self.paleta.color_aviso
        self.lbl_subseccion_avanzada.color = self.paleta.texto_secundario
        self.lbl_vacio_tablas.content.color = self.paleta.texto_secundario
        self.lbl_vacio_moldes.content.color = self.paleta.texto_secundario
        self.lbl_titulo_tabla.color = self.paleta.texto
        self.lbl_resumen_tabla.color = self.paleta.texto_secundario
        self.lbl_nota_tabla.bgcolor = self.paleta.panel
        self.lbl_nota_tabla.content.color = self.paleta.color_aviso
        self.container_viewer_svg.border = ft.Border.all(1, self.paleta.borde)
        self.lbl_instruccion_zoom.color = self.paleta.texto_secundario
        self.lbl_pie_moldes.color = self.paleta.texto_secundario
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
        self._renderizar_molde_seleccionado()
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
        self._sync_controlador_a_vista(vm)

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

    def _renderizar_molde_seleccionado(self):
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

        if svg_str:
            self.img_svg.src = svg_str.encode("utf-8")
        else:
            self.img_svg.src = ""

    def _sync_controlador_a_vista(self, vm: ViewModelTrompo):
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
                bg_color = self.paleta.panel
                text_color = self.paleta.texto
                if tj.etiqueta == "Viable":
                    bg_color = self.paleta.color_ok if tj.valor == "Sí" else self.paleta.color_error
                    text_color = "#ffffff"
                    
                card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(tj.etiqueta, size=11, color=self.paleta.texto_secundario),
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
                c = self.paleta.texto
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
        if vm.svg_conjunto and not vm.desactualizado:
            self.lbl_vacio_moldes.visible = False
            self.panel_contenido_moldes.visible = True
            self._renderizar_molde_seleccionado()
        else:
            self.lbl_vacio_moldes.visible = True
            self.panel_contenido_moldes.visible = False

        try:
            self.update()
        except RuntimeError:
            pass
