import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.pestanas.base import PestanaBase


class PestanaResumen(PestanaBase):
    """Pestaña de resumen de resultados geométricos y avisos clasificados."""

    def __init__(self, paleta):
        self.paleta = paleta
        self.lbl_desactualizado = ft.Text(
            "Cambiaste los datos: pulsa Calcular",
            color=self.paleta.color_aviso,
            visible=False,
        )
        self.grid_tarjetas = ft.ResponsiveRow(run_spacing=10)
        self.col_avisos = ft.Column(spacing=5)
        self.contenedor: ft.ListView = ft.ListView(
            padding=20,
            controls=[
                self.lbl_desactualizado,
                self.grid_tarjetas,
                ft.Divider(color=ft.Colors.OUTLINE),
                self.col_avisos,
            ],
        )

    def construir(self) -> ft.Control:
        return self.contenedor

    def actualizar(self, vm: ViewModelTrompo) -> None:
        self.lbl_desactualizado.visible = vm.desactualizado
        self._actualizar_tarjetas(vm)
        self._actualizar_avisos(vm)

    def _actualizar_tarjetas(self, vm: ViewModelTrompo) -> None:
        self.grid_tarjetas.controls.clear()
        if vm.desactualizado:
            return

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

    def _actualizar_avisos(self, vm: ViewModelTrompo) -> None:
        self.col_avisos.controls.clear()
        if vm.desactualizado:
            return

        for av in vm.avisos:
            c = ft.Colors.ON_SURFACE
            if av.clase == "ok":
                c = self.paleta.color_ok
            elif av.clase == "aviso":
                c = self.paleta.color_aviso
            elif av.clase == "error":
                c = self.paleta.color_error
            elif av.clase == "info":
                c = self.paleta.color_info

            self.col_avisos.controls.append(ft.Text(av.texto, color=c))

    def aplicar_tema(self, paleta) -> None:
        self.paleta = paleta
        self.lbl_desactualizado.color = paleta.color_aviso
