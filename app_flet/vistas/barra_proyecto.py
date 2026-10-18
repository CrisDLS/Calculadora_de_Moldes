"""Barra de gestión de proyecto: nuevo, abrir, guardar y guardar como."""

import os
from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo


class BarraProyecto:
    """Gestiona el nombre del proyecto, estado de cambios y botones de archivo."""

    def __init__(
        self,
        paleta,
        controlador,
        file_picker,
        on_mostrar_snackbar: Callable[[str], None],
        on_proyecto_cargado: Callable[[], None],
        on_solicitar_sync: Callable[..., None],
    ):
        self.paleta = paleta
        self.controlador = controlador
        self.file_picker = file_picker
        self.on_mostrar_snackbar = on_mostrar_snackbar
        self.on_proyecto_cargado = on_proyecto_cargado
        self.on_solicitar_sync = on_solicitar_sync

        self._crear_controles()

    def _crear_controles(self) -> None:
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

        self.fila_proyecto = ft.Row(
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
        )

    def construir(self) -> ft.Control:
        return self.fila_proyecto

    def actualizar(self, vm: ViewModelTrompo) -> None:
        self.lbl_nombre_proyecto.value = vm.nombre_proyecto
        self.lbl_estado_proyecto.value = "Sin guardar" if vm.sin_guardar else ""

    def on_proyecto_nuevo(self, e) -> None:
        self.controlador.nuevo()
        self.on_proyecto_cargado()
        self.on_solicitar_sync(reset_zoom=True)
        self.on_mostrar_snackbar("Nuevo proyecto iniciado")

    async def on_proyecto_abrir(self, e) -> None:
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
                self.on_proyecto_cargado()
                self.on_solicitar_sync(reset_zoom=True)
                if self.controlador.recursos_faltantes:
                    faltantes_str = ", ".join(self.controlador.recursos_faltantes)
                    self.on_mostrar_snackbar(f"Proyecto abierto con recursos faltantes: {faltantes_str}")
                else:
                    self.on_mostrar_snackbar(f"Proyecto abierto: {os.path.basename(ruta)}")
            else:
                self.on_mostrar_snackbar(f"Error al abrir: {msg}")

    async def on_proyecto_guardar(self, e) -> None:
        if not self.controlador.ruta_proyecto:
            await self.on_proyecto_guardar_como(e)
            return
        ok, msg = self.controlador.guardar()
        if ok:
            self.on_solicitar_sync()
            self.on_mostrar_snackbar(f"Proyecto guardado: {os.path.basename(self.controlador.ruta_proyecto)}")
        else:
            self.on_mostrar_snackbar(f"Error al guardar: {msg}")

    async def on_proyecto_guardar_como(self, e) -> None:
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
                self.on_solicitar_sync()
                self.on_mostrar_snackbar(f"Proyecto guardado como: {os.path.basename(ruta)}")
            else:
                self.on_mostrar_snackbar(f"Error al guardar: {msg}")
