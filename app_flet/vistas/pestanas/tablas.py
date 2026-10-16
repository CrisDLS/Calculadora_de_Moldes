import asyncio
from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.pestanas.base import PestanaBase
from app_flet.vistas.tabla_molde import TablaMoldePersonalizada
from presentacion.trompo_estrella import tabla_a_texto, TablaMolde


class PestanaTablas(PestanaBase):
    """Pestaña de tablas numéricas de corte de moldes."""

    def __init__(
        self,
        paleta,
        controlador,
        servicio_clipboard=None,
        on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
        obtener_pagina: Optional[Callable[[], Optional[ft.Page]]] = None,
    ):
        self.paleta = paleta
        self.controlador = controlador
        self.servicio_clipboard = servicio_clipboard if servicio_clipboard is not None else ft.Clipboard()
        self.on_mostrar_snackbar = on_mostrar_snackbar
        self.obtener_pagina = obtener_pagina or (lambda: None)

        self.selector_tabla = ft.SegmentedButton(
            selected=["0"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="0", label=ft.Text("Cono superior")),
                ft.Segment(value="1", label=ft.Text("Pico")),
                ft.Segment(value="2", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_pieza_tabla,
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
            on_click=self.on_copiar_tabla,
        )

        self.tabla_componente = TablaMoldePersonalizada(self.paleta)

        self.panel_contenido_tablas = ft.Column(
            expand=True,
            visible=False,
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(controls=[self.lbl_titulo_tabla, self.lbl_resumen_tabla], expand=True),
                        self.btn_copiar_tabla,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.lbl_nota_tabla,
                ft.Divider(color=ft.Colors.OUTLINE),
                self.tabla_componente,
            ],
            spacing=10,
        )

        self.contenedor = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row([self.selector_tabla], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_tablas,
                    self.panel_contenido_tablas,
                ],
            ),
        )

    def construir(self) -> ft.Control:
        return self.contenedor

    def actualizar(self, vm: ViewModelTrompo) -> None:
        if vm.tablas and not vm.desactualizado:
            self.lbl_vacio_tablas.visible = False
            self.panel_contenido_tablas.visible = True
            self.renderizar_tabla_seleccionada()
        else:
            self.lbl_vacio_tablas.visible = True
            self.panel_contenido_tablas.visible = False

    def renderizar_tabla_seleccionada(self) -> None:
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

    def on_cambio_pieza_tabla(self, e) -> None:
        self.renderizar_tabla_seleccionada()
        try:
            self.contenedor.update()
        except RuntimeError:
            pass

    def on_copiar_tabla(self, e) -> None:
        idx = int(self.selector_tabla.selected[0]) if self.selector_tabla.selected else 0
        if not (self.controlador.tablas and idx < len(self.controlador.tablas)):
            if self.on_mostrar_snackbar:
                self.on_mostrar_snackbar("No se pudo copiar")
            return

        tabla = self.controlador.tablas[idx]
        texto = tabla_a_texto(tabla)

        copia_exitosa = False
        page = self.obtener_pagina()
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

        if self.on_mostrar_snackbar:
            msg = "Tabla copiada al portapapeles" if copia_exitosa else "No se pudo copiar"
            self.on_mostrar_snackbar(msg)

    def aplicar_tema(self, paleta) -> None:
        self.paleta = paleta
        self.lbl_nota_tabla.content.color = self.paleta.color_aviso
        self.tabla_componente.actualizar_paleta(self.paleta)
