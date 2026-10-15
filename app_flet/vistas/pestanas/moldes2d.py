import os
from typing import Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.componentes.visor_svg import VisorSvg
from app_flet.vistas.pestanas.base import PestanaBase


class PestanaMoldes2D(PestanaBase):
    """Pestaña de visualización de moldes planos 2D y perfil armado proyectado."""

    def __init__(self, paleta, controlador):
        self.paleta = paleta
        self.controlador = controlador
        self._svg_actual_raw: str = ""

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
            on_change=self.on_cambio_pieza_molde,
        )
        self.lbl_vacio_moldes = ft.Container(
            content=ft.Text("Calcula para ver los moldes", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )

        self.visor_moldes = VisorSvg(papel_blanco=False, margen_ajuste=0.04)
        self.container_viewer_svg = self.visor_moldes.container_viewer_svg
        self.img_svg = self.visor_moldes.img_svg
        self.detector_gestos = self.visor_moldes.detector_gestos
        self.barra_zoom = self.visor_moldes.barra_zoom
        self.lbl_zoom_porcentaje = self.visor_moldes.lbl_zoom_porcentaje
        self.btn_zoom_in = self.visor_moldes.btn_zoom_in
        self.btn_zoom_out = self.visor_moldes.btn_zoom_out
        self.btn_ajustar = self.visor_moldes.btn_ajustar
        self.lbl_instruccion_zoom = self.visor_moldes.lbl_instruccion_zoom
        self.lbl_debug = self.visor_moldes.lbl_debug
        self.debug_mode = self.visor_moldes.debug_mode
        self._padding_container = self.visor_moldes._padding_container
        self._border_width = self.visor_moldes._border_width

        self.lbl_pie_moldes = ft.Text(
            "La escala y la hoja de trazo en Carta llegarán en F3.",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
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

        self.contenedor = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row([self.selector_molde], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_moldes,
                    self.panel_contenido_moldes,
                ],
            ),
        )

    def construir(self) -> ft.Control:
        return self.contenedor

    def actualizar(self, vm: ViewModelTrompo, reset_zoom: bool = False) -> None:
        sel_molde = self.selector_molde.selected[0] if self.selector_molde.selected else "0"
        if sel_molde == "4":
            self.lbl_vacio_moldes.content.value = "Calcula para ver el perfil"
        else:
            self.lbl_vacio_moldes.content.value = "Calcula para ver los moldes"

        if vm.svg_conjunto and not vm.desactualizado:
            self.lbl_vacio_moldes.visible = False
            self.panel_contenido_moldes.visible = True
            self.renderizar_molde_seleccionado(reset_vista=reset_zoom)
        else:
            self.lbl_vacio_moldes.visible = True
            self.panel_contenido_moldes.visible = False

    def renderizar_molde_seleccionado(self, reset_vista: bool = False) -> None:
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
        self.visor_moldes.cargar_svg(svg_str, reset_vista=reset_vista)

    def on_cambio_pieza_molde(self, e) -> None:
        sel_molde = self.selector_molde.selected[0] if self.selector_molde.selected else "0"
        if sel_molde == "4":
            self.lbl_vacio_moldes.content.value = "Calcula para ver el perfil"
        else:
            self.lbl_vacio_moldes.content.value = "Calcula para ver los moldes"

        self.renderizar_molde_seleccionado(reset_vista=True)
        try:
            self.contenedor.update()
        except RuntimeError:
            pass
