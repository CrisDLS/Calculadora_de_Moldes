"""Pestaña de Diseño gráfico y motivos sobre el abanico (F6a)."""

import os
from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.pestanas.base import PestanaBase
from app_flet.vistas.pestanas.diseno_inspector import PanelCapasInspector
from app_flet.vistas.pestanas.diseno_visor import VisorDisenoGestor


class PestanaDiseno(PestanaBase):
    """Pestaña de composición visual, capas de motivos y exportación decorada."""

    def __init__(
        self,
        paleta,
        controlador,
        servicio_file_picker=None,
        debug_mode: bool = False,
        obtener_pagina: Optional[Callable[[], Optional[ft.Page]]] = None,
        on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
        on_solicitar_sync: Optional[Callable[..., None]] = None,
    ):
        self.paleta = paleta
        self._controlador = controlador
        self.file_picker = servicio_file_picker if servicio_file_picker is not None else ft.FilePicker()
        self.debug_mode = debug_mode
        self._obtener_pagina = obtener_pagina
        self.on_mostrar_snackbar = on_mostrar_snackbar or (lambda msg: None)
        self.on_solicitar_sync = on_solicitar_sync or (lambda **kwargs: None)

        self._crear_subcomponentes()
        self._crear_selectores_y_herramientas()
        self._crear_botones_exportacion()
        self._construir_layout()

    @property
    def controlador(self):
        return self._controlador

    @controlador.setter
    def controlador(self, c) -> None:
        self._controlador = c
        if hasattr(self, "inspector"):
            self.inspector.controlador = c
        if hasattr(self, "gestor_visor"):
            self.gestor_visor.controlador = c

    @property
    def _id_recomposicion_diseno(self) -> int:
        return self.gestor_visor._id_recomposicion_diseno

    @_id_recomposicion_diseno.setter
    def _id_recomposicion_diseno(self, val: int) -> None:
        self.gestor_visor._id_recomposicion_diseno = val


    def _crear_subcomponentes(self) -> None:
        self.inspector = PanelCapasInspector(
            controlador=self.controlador,
            file_picker=self.file_picker,
            on_solicitar_sync=self._al_solicitar_sync_inspector,
            on_mostrar_snackbar=self.on_mostrar_snackbar,
            obtener_pagina=self._obtener_pagina,
        )
        self.gestor_visor = VisorDisenoGestor(
            controlador=self.controlador,
            inspector=self.inspector,
            debug_mode=self.debug_mode,
            obtener_pagina=self._obtener_pagina,
            on_solicitar_sync=self._al_solicitar_sync_visor,
        )

        # Proxies para compatibilidad con accesos directos
        self.panel_inspector_capa = self.inspector.panel_inspector_capa
        self.col_lista_capas = self.inspector.col_lista_capas
        self.btn_anadir_capa = self.inspector.btn_anadir_capa
        self.txt_nombre_capa = self.inspector.txt_nombre_capa
        self.txt_pos_x = self.inspector.txt_pos_x
        self.txt_pos_y = self.inspector.txt_pos_y
        self.txt_ancho_capa = self.inspector.txt_ancho_capa
        self.txt_alto_capa = self.inspector.txt_alto_capa
        self.chk_proporcion = self.inspector.chk_proporcion
        self.slider_rotacion = self.inspector.slider_rotacion
        self.lbl_rotacion_val = self.inspector.lbl_rotacion_val
        self.btn_reflejo_h = self.inspector.btn_reflejo_h
        self.btn_reflejo_v = self.inspector.btn_reflejo_v
        self.slider_opacidad = self.inspector.slider_opacidad
        self.lbl_opacidad_val = self.inspector.lbl_opacidad_val
        self.btn_ajustar_cubrir = self.inspector.btn_ajustar_cubrir
        self.btn_ajustar_contener = self.inspector.btn_ajustar_contener
        self.btn_ajustar_estirar = self.inspector.btn_ajustar_estirar
        self.btn_ajustar_ancho = self.inspector.btn_ajustar_ancho
        self.btn_ajustar_alto = self.inspector.btn_ajustar_alto
        self.btn_centrar_capa = self.inspector.btn_centrar_capa
        self.btn_nudge_left = self.inspector.btn_nudge_left
        self.btn_nudge_right = self.inspector.btn_nudge_right
        self.btn_nudge_up = self.inspector.btn_nudge_up
        self.btn_nudge_down = self.inspector.btn_nudge_down
        self.btn_rot_m5 = self.inspector.btn_rot_m5
        self.btn_rot_p5 = self.inspector.btn_rot_p5
        self.btn_rot_0 = self.inspector.btn_rot_0

        self.visor = self.gestor_visor.visor
        self.container_viewer_diseno = self.gestor_visor.container_viewer
        self.img_svg_diseno = self.gestor_visor.img_svg
        self.detector_gestos_diseno = self.gestor_visor.detector_gestos
        self.btn_zoom_in_diseno = self.gestor_visor.btn_zoom_in
        self.btn_zoom_out_diseno = self.gestor_visor.btn_zoom_out
        self.btn_ajustar_diseno = self.gestor_visor.btn_ajustar
        self.lbl_zoom_diseno_porcentaje = self.gestor_visor.lbl_zoom_porcentaje
        self.lbl_instruccion_zoom_diseno = self.gestor_visor.lbl_instruccion_zoom
        self.lbl_estado_diseno = self.gestor_visor.lbl_estado_diseno
        self.barra_zoom_diseno = self.gestor_visor.barra_zoom
        self.lbl_debug_diseno = self.gestor_visor.lbl_debug_diseno

    def _al_solicitar_sync_inspector(self) -> None:
        self.on_solicitar_sync()

    def _al_solicitar_sync_visor(self) -> None:
        self.on_solicitar_sync()

    def _crear_selectores_y_herramientas(self) -> None:
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
        self.segmento_una_cara_pico = ft.Segment(value="una_cara", label=ft.Text("Una cara"))
        self.segmento_completo_pico = ft.Segment(value="completo", label=ft.Text("Lienzo completo"))
        self.selector_lienzo_diseno = ft.SegmentedButton(
            selected=["completo"],
            allow_multiple_selection=False,
            segments=[
                self.segmento_completo_diseno,
                self.segmento_mitad_diseno,
            ],
            on_change=self.on_cambio_lienzo_diseno,
        )

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

        self.selector_interaccion_diseno = ft.SegmentedButton(
            selected=["navegar"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="navegar", label=ft.Text("Navegar"), icon=ft.Icon(ft.Icons.PAN_TOOL, size=16)),
                ft.Segment(value="editar", label=ft.Text("Editar"), icon=ft.Icon(ft.Icons.HIGHLIGHT_ALT, size=16)),
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

    def _crear_botones_exportacion(self) -> None:
        self.btn_exportar_abanico = ft.FilledButton("Exportar abanico con diseño (SVG)", icon=ft.Icons.FILE_DOWNLOAD, on_click=self.on_exportar_abanico_click)
        self.btn_exportar_gajos = ft.FilledButton("Exportar piezas con diseño…", icon=ft.Icons.FOLDER_OPEN, on_click=self.on_exportar_gajos_click)
        self.btn_exportar_hoja_diseno = ft.FilledButton("Exportar hoja Carta con diseño", icon=ft.Icons.IMAGE, on_click=self.on_exportar_hoja_diseno_click)

    def _construir_layout(self) -> None:
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
                        ft.Row([self.lbl_instruccion_zoom_diseno], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([self.lbl_debug_diseno], alignment=ft.MainAxisAlignment.CENTER) if self.debug_mode else ft.Container(),
                    ],
                    spacing=4,
                ),
            ],
            spacing=10,
        )

        self.tab_diseno = ft.Container(
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

    def construir(self) -> ft.Control:
        return self.tab_diseno

    def actualizar(self, vm: ViewModelTrompo, reset_zoom: bool = False) -> None:
        """Actualiza la vista con el estado del ViewModel."""
        sec = self.controlador.diseno_seccion
        self.selector_seccion_diseno.selected = [sec]
        self.selector_variante_pico_diseno.visible = (sec == "pico")
        self.selector_variante_pico_diseno.selected = [self.controlador.diseno_variante]
        self.selector_lienzo_diseno.visible = True

        if sec == "pico":
            self.selector_lienzo_diseno.segments = [
                self.segmento_una_cara_pico,
                self.segmento_completo_pico,
            ]
        else:
            self.selector_lienzo_diseno.segments = [
                self.segmento_completo_diseno,
                self.segmento_mitad_diseno,
            ]
            self.segmento_mitad_diseno.disabled = not vm.puede_usar_mitad
            self.segmento_mitad_diseno.tooltip = vm.motivo_no_mitad if not vm.puede_usar_mitad else "Diseño sobre mitad con reflejo simétrico"

        self.selector_lienzo_diseno.selected = [vm.diseno_lienzo_modo]

        self.chk_ver_cuadricula.value = vm.diseno_ver_cuadricula
        self.chk_ver_rotulos.value = vm.diseno_ver_rotulos
        self.chk_ver_costuras.value = vm.diseno_ver_costuras
        self.chk_mostrar_reflejo.value = vm.diseno_mostrar_reflejo
        self.chk_mostrar_reflejo.visible = (vm.diseno_lienzo_modo == "mitad")

        if vm.svg_diseno and not vm.desactualizado:
            self.lbl_vacio_diseno.visible = False
            self.panel_contenido_diseno.visible = True
            if self.gestor_visor.modo_interaccion_diseno == "editar":
                self.controlador.actualizar_svg_diseno(modo_fantasma=True)
            self.gestor_visor.renderizar_diseno(reset_vista=reset_zoom)
        else:
            self.lbl_vacio_diseno.visible = True
            self.panel_contenido_diseno.visible = False

        self.inspector.actualizar(vm)

        # Sincronización del modo de interacción y del marco superpuesto
        capa_sel = self.controlador.obtener_capa_seleccionada()
        if self.gestor_visor.modo_interaccion_diseno == "editar":
            if not capa_sel or capa_sel.bloqueada:
                self.gestor_visor.cambiar_modo_interaccion("navegar")
                self.selector_interaccion_diseno.selected = ["navegar"]
            else:
                conv = self.gestor_visor.obtener_conversion()
                carp = self.controlador.obtener_carpeta_recursos_activa()
                if conv:
                    self.gestor_visor.marco_edicion.actualizar(
                        capa_sel, conv, carp, mantener_proporcion=self.controlador.mantener_proporcion
                    )
        else:
            self.selector_interaccion_diseno.selected = ["navegar"]

    def on_cambio_seccion_diseno(self, e) -> None:
        sel = self.selector_seccion_diseno.selected[0] if self.selector_seccion_diseno.selected else "superior"
        self.selector_variante_pico_diseno.visible = (sel == "pico")
        self.selector_lienzo_diseno.visible = True
        var = self.selector_variante_pico_diseno.selected[0] if self.selector_variante_pico_diseno.selected else "A"
        self.controlador.cambiar_diseno_seccion(sel, var)
        self.on_solicitar_sync(reset_zoom=True)

    def on_cambio_variante_diseno(self, e) -> None:
        sel = self.selector_seccion_diseno.selected[0] if self.selector_seccion_diseno.selected else "pico"
        var = self.selector_variante_pico_diseno.selected[0] if self.selector_variante_pico_diseno.selected else "A"
        self.controlador.cambiar_diseno_seccion(sel, var)
        self.on_solicitar_sync(reset_zoom=True)

    def on_cambio_lienzo_diseno(self, e) -> None:
        if self.controlador.diseno_seccion == "pico":
            modo = self.selector_lienzo_diseno.selected[0] if self.selector_lienzo_diseno.selected else "una_cara"
        else:
            modo = self.selector_lienzo_diseno.selected[0] if self.selector_lienzo_diseno.selected else "completo"
        self.controlador.cambiar_diseno_lienzo_modo(modo)
        self.on_solicitar_sync(reset_zoom=True)

    def on_toggle_ver_cuadricula(self, e) -> None:
        self.controlador.cambiar_diseno_ver_cuadricula(bool(self.chk_ver_cuadricula.value))
        self.on_solicitar_sync()

    def on_toggle_ver_rotulos(self, e) -> None:
        self.controlador.cambiar_diseno_ver_rotulos(bool(self.chk_ver_rotulos.value))
        self.on_solicitar_sync()

    def on_toggle_ver_costuras(self, e) -> None:
        self.controlador.cambiar_diseno_ver_costuras(bool(self.chk_ver_costuras.value))
        self.on_solicitar_sync()

    def on_toggle_mostrar_reflejo(self, e) -> None:
        self.controlador.cambiar_diseno_mostrar_reflejo(bool(self.chk_mostrar_reflejo.value))
        self.on_solicitar_sync()

    def on_cambio_modo_interaccion(self, e) -> None:
        sel = self.selector_interaccion_diseno.selected
        modo = list(sel)[0] if sel else "navegar"
        exito = self.gestor_visor.cambiar_modo_interaccion(modo)
        if not exito:
            self.selector_interaccion_diseno.selected = ["navegar"]
            try:
                self.selector_interaccion_diseno.update()
            except Exception:
                pass

    def cambiar_modo_interaccion(self, modo: str) -> bool:
        """Cambia programáticamente el modo de interacción entre navegar y editar."""
        self.selector_interaccion_diseno.selected = [modo]
        return self.gestor_visor.cambiar_modo_interaccion(modo)

    async def on_exportar_abanico_click(self, e) -> None:
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
                self.on_mostrar_snackbar(f"Abanico guardado: {os.path.basename(ruta)}")
            except Exception as ex:
                self.on_mostrar_snackbar(f"Error al exportar abanico: {ex}")

    async def on_exportar_gajos_click(self, e) -> None:
        carpeta = await self.file_picker.get_directory_path(dialog_title="Seleccionar carpeta para exportar gajos")
        if carpeta:
            try:
                archs = self.controlador.exportar_gajos_diseno(carpeta)
                self.on_mostrar_snackbar(f"{len(archs)} gajos exportados en {os.path.basename(carpeta)}")
            except Exception as ex:
                self.on_mostrar_snackbar(f"Error al exportar gajos: {ex}")

    async def on_exportar_hoja_diseno_click(self, e) -> None:
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
                self.on_mostrar_snackbar(f"Hoja decorada guardada: {os.path.basename(ruta)}")
            except Exception as ex:
                self.on_mostrar_snackbar(f"Error al exportar hoja decorada: {ex}")
