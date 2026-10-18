"""Vista principal del Trompo Estrella (Compositor de la interfaz en Flet)."""

import time
from typing import Optional
import flet as ft
from app_flet import tema
from app_flet.controlador import ControladorTrompo, ViewModelTrompo
from app_flet.vistas.barra_proyecto import BarraProyecto
from app_flet.vistas.panel_entradas import PanelEntradas
from app_flet.vistas.pestanas.diseno import PestanaDiseno
from app_flet.vistas.pestanas.hoja import PestanaHoja
from app_flet.vistas.pestanas.moldes2d import PestanaMoldes2D
from app_flet.vistas.pestanas.resumen import PestanaResumen
from app_flet.vistas.pestanas.tablas import PestanaTablas
from app_flet.vistas.pestanas.vista3d import PestanaVista3D
from app_flet.vistas.trompo_compat import VistaTrompoCompat
from logic.exportacion.estilos import PANTALLA_CLARO, PANTALLA_OSCURO


class VistaTrompo(VistaTrompoCompat, ft.Container):
    """Compositor principal: coordina panel lateral, barra de proyecto y pestañas."""

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

        self._crear_componentes()
        self._conectar_proxies()
        self._construir_layout()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    @property
    def controlador(self) -> ControladorTrompo:
        return self._controlador

    @controlador.setter
    def controlador(self, c: ControladorTrompo) -> None:
        self._controlador = c
        if hasattr(self, "panel_entradas"): self.panel_entradas.controlador = c
        if hasattr(self, "barra_proyecto"): self.barra_proyecto.controlador = c
        if hasattr(self, "pestana_resumen"): self.pestana_resumen.controlador = c
        if hasattr(self, "pestana_tablas"): self.pestana_tablas.controlador = c
        if hasattr(self, "pestana_moldes2d"): self.pestana_moldes2d.controlador = c
        if hasattr(self, "pestana_hoja"): self.pestana_hoja.controlador = c
        if hasattr(self, "pestana_vista3d"): self.pestana_vista3d.controlador = c
        if hasattr(self, "pestana_diseno"): self.pestana_diseno.controlador = c

    @property
    def obtener_pagina(self) -> Optional[ft.Page]:
        try:
            return self.page
        except RuntimeError:
            return None

    def _crear_componentes(self) -> None:
        self.barra_proyecto = BarraProyecto(
            paleta=self.paleta,
            controlador=self.controlador,
            file_picker=self.file_picker,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_proyecto_cargado=self._cargar_entradas_desde_controlador,
            on_solicitar_sync=lambda *a, **kw: self._sync_controlador_a_vista(self.controlador.get_view_model(), *a, **kw),
        )
        self.panel_entradas = PanelEntradas(
            paleta=self.paleta,
            controlador=self.controlador,
            barra_proyecto=self.barra_proyecto,
            on_toggle_tema=self.on_toggle_tema,
            on_solicitar_sync=lambda *a, **kw: self._sync_controlador_a_vista(self.controlador.get_view_model(), *a, **kw),
            on_antes_de_calcular=self._antes_de_calcular,
        )
        self.pestana_resumen = PestanaResumen(self.paleta)
        self.pestana_tablas = PestanaTablas(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_clipboard=self.servicio_clipboard,
            on_mostrar_snackbar=self._mostrar_snackbar,
            obtener_pagina=lambda: self.obtener_pagina,
        )
        self.pestana_moldes2d = PestanaMoldes2D(self.paleta, self.controlador)
        self.pestana_hoja = PestanaHoja(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda *a, **kw: self._sync_controlador_a_vista(self.controlador.get_view_model(), *a, **kw),
        )
        self.pestana_vista3d = PestanaVista3D(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            servicio_clipboard=self.servicio_clipboard,
            obtener_pagina=lambda: self.obtener_pagina,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda *a, **kw: self._sync_controlador_a_vista(self.controlador.get_view_model(), *a, **kw),
        )
        self.pestana_diseno = PestanaDiseno(
            paleta=self.paleta,
            controlador=self.controlador,
            servicio_file_picker=self.file_picker,
            debug_mode=bool(getattr(self, "debug_mode", False)),
            obtener_pagina=lambda: self.obtener_pagina,
            on_mostrar_snackbar=self._mostrar_snackbar,
            on_solicitar_sync=lambda *a, **kw: self._sync_controlador_a_vista(self.controlador.get_view_model(), *a, **kw),
        )

    def _construir_layout(self) -> None:
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
                        controls=[
                            self.pestana_resumen.construir(),
                            self.pestana_tablas.construir(),
                            self.pestana_moldes2d.construir(),
                            self.pestana_hoja.construir(),
                            self.pestana_diseno.construir(),
                            self.pestana_vista3d.construir(),
                        ],
                    ),
                ],
            ),
        )
        self.panel_derecho = ft.Container(expand=True, content=self.tabs)
        self.content = ft.Row(
            expand=True,
            controls=[self.panel_izquierdo, self.panel_derecho],
            spacing=0,
        )

    def _sync_controlador_a_vista(self, vm: ViewModelTrompo, diferir_update: bool = False, reset_zoom: bool = False):
        if vm.mensaje_error:
            self.lbl_error.value = vm.mensaje_error
            self.lbl_error.visible = True
        else:
            self.lbl_error.visible = False

        self.pestana_resumen.actualizar(vm)
        self.pestana_tablas.actualizar(vm)
        self.pestana_moldes2d.actualizar(vm, reset_zoom=reset_zoom)
        self.pestana_hoja.actualizar(vm, reset_zoom=reset_zoom)
        self.pestana_vista3d.actualizar(vm)
        self.pestana_diseno.actualizar(vm, reset_zoom=reset_zoom)

        self.barra_proyecto.actualizar(vm)
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
        self.controlador.cambiar_estilo(estilo)
        self.panel_entradas.aplicar_tema(self.paleta)
        self.pestana_resumen.aplicar_tema(self.paleta)
        self.pestana_tablas.aplicar_tema(self.paleta)

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

        self.ultimo_tiempo_toggle_tema_ms = (time.perf_counter() - t0) * 1000.0

    def _antes_de_calcular(self) -> None:
        if getattr(self, "arrastrando_capa", False):
            self._finalizar_arrastre_capa()

    def _on_tabs_change(self, e):
        if getattr(self, "arrastrando_capa", False):
            self.pestana_diseno.gestor_visor.finalizar_arrastre_capa()
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _cargar_entradas_desde_controlador(self):
        self.panel_entradas.cargar_desde_controlador()
        self.dd_hoja.value = self.controlador.hoja_tipo
        self.dd_escala.value = str(self.controlador.hoja_escala)
        self.selector_pieza_hoja.selected = [self.controlador.hoja_pieza]
        self.selector_lienzo.selected = [self.controlador.hoja_lienzo]
        self.selector_modo_dibujo.selected = [self.controlador.hoja_dibujar]
        self.dd_repeticion_pico_hoja.value = self.controlador.esquema_pico.modo_repeticion
        self.txt_pliegos_paquete.value = str(self.controlador.pliegos_por_paquete)
        self.txt_pliego_ancho.value = str(self.controlador.pliego_ancho)
        self.txt_pliego_alto.value = str(self.controlador.pliego_alto)

    def _leer_vista_a_controlador(self):
        self.panel_entradas.leer_vista_a_controlador()
