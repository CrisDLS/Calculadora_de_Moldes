# app_flet/vistas/tabla_molde.py
from typing import List, Optional
import flet as ft
from presentacion.trompo_estrella import TablaMolde
from app_flet.tema import PaletaTema

PESOS_COLUMNAS = [7, 10, 10, 10]  # Pesos proporcionales: Paso (0.7), Largo (1.0), Acumulado (1.0), Ancho/2 (1.0)

class TablaMoldePersonalizada(ft.Container):
    def __init__(self, paleta: PaletaTema):
        super().__init__()
        self.paleta = paleta
        self.expand = True
        self.tabla_actual: Optional[TablaMolde] = None

        self.row_encabezados = ft.Row(spacing=0, expand=True)
        self.container_encabezado = ft.Container(
            content=self.row_encabezados,
            bgcolor=self.paleta.panel,
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
            padding=ft.Padding.only(left=10, right=20, top=10, bottom=10),
            border=ft.Border.all(1, self.paleta.borde),
        )

        self.list_filas = ft.ListView(
            spacing=0,
            expand=True,
            padding=ft.Padding.only(right=10),
        )

        self.container_cuerpo = ft.Container(
            content=self.list_filas,
            expand=True,
            border=ft.Border.only(
                left=ft.BorderSide(1, self.paleta.borde),
                right=ft.BorderSide(1, self.paleta.borde),
                bottom=ft.BorderSide(1, self.paleta.borde),
            ),
            border_radius=ft.BorderRadius.only(bottom_left=8, bottom_right=8),
        )

        self.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self.container_encabezado,
                self.container_cuerpo,
            ]
        )

    def cargar_tabla(self, tabla: TablaMolde, paleta: Optional[PaletaTema] = None):
        self.tabla_actual = tabla
        if paleta is not None:
            self.paleta = paleta
        self._construir_ui()
        try:
            res = self.list_filas.scroll_to(offset=0, duration=0)
            if hasattr(res, "close"):
                res.close()
        except Exception:
            pass

    def actualizar_paleta(self, paleta: PaletaTema):
        self.paleta = paleta
        if self.tabla_actual:
            self._construir_ui()

    def _construir_ui(self):
        if not self.tabla_actual:
            self.row_encabezados.controls.clear()
            self.list_filas.controls.clear()
            return

        # 1. Encabezados
        self.container_encabezado.bgcolor = self.paleta.panel
        self.container_encabezado.border = ft.Border.all(1, self.paleta.borde)
        self.container_cuerpo.border = ft.Border.only(
            left=ft.BorderSide(1, self.paleta.borde),
            right=ft.BorderSide(1, self.paleta.borde),
            bottom=ft.BorderSide(1, self.paleta.borde),
        )

        self.row_encabezados.controls = [
            ft.Container(
                expand=peso,
                alignment=ft.Alignment(1, 0),
                content=ft.Text(
                    enc,
                    weight=ft.FontWeight.BOLD,
                    size=13,
                    color=self.paleta.texto,
                    text_align=ft.TextAlign.RIGHT,
                ),
            )
            for enc, peso in zip(self.tabla_actual.encabezados, PESOS_COLUMNAS)
        ]

        # 2. Filas
        filas_controls = []
        for idx, f in enumerate(self.tabla_actual.filas):
            bg = self.paleta.fila_alternada if (idx % 2 == 1) else None
            celdas = [
                ft.Container(
                    expand=peso,
                    alignment=ft.Alignment(1, 0),
                    content=ft.Text(
                        val,
                        size=13,
                        color=self.paleta.texto,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                )
                for val, peso in zip(f, PESOS_COLUMNAS)
            ]
            row = ft.Container(
                content=ft.Row(controls=celdas, spacing=0, expand=True),
                bgcolor=bg,
                padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            )
            filas_controls.append(row)

        self.list_filas.controls = filas_controls
