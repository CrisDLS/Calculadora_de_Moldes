import os
from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.componentes.visor_svg import VisorSvg
from app_flet.vistas.pestanas.base import PestanaBase
from logic.exportacion.paquete import generar_paquete, guardar_paquete


class PestanaHoja(PestanaBase):
    """Pestaña de hoja de trazo a escala (piezas separadas y abanico) con cotas."""

    def __init__(
        self,
        paleta,
        controlador,
        servicio_file_picker=None,
        on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
        on_solicitar_sync: Optional[Callable[[bool], None]] = None,
    ):
        self.paleta = paleta
        self.controlador = controlador
        self.file_picker = servicio_file_picker if servicio_file_picker is not None else ft.FilePicker()
        self.on_mostrar_snackbar = on_mostrar_snackbar
        self.on_solicitar_sync = on_solicitar_sync
        self._svg_hoja_raw: str = ""

        self._crear_selectores_superiores()
        self._crear_panel_pico()
        self._crear_panel_parametros_hoja()
        self._crear_visor_hoja()
        self._montar_contenedor()

    def _crear_selectores_superiores(self) -> None:
        self.selector_pieza_hoja = ft.SegmentedButton(
            selected=["superior"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="superior", label=ft.Text("Cono superior")),
                ft.Segment(value="pico", label=ft.Text("Pico")),
                ft.Segment(value="inferior", label=ft.Text("Cono inferior")),
            ],
            on_change=self.on_cambio_pieza_hoja,
        )
        self.selector_lienzo = ft.SegmentedButton(
            selected=["abanico"],
            allow_multiple_selection=False,
            segments=[
                ft.Segment(value="abanico", label=ft.Text("Abanico (recomendado)")),
                ft.Segment(value="separadas", label=ft.Text("Piezas separadas")),
            ],
            on_change=self.on_cambio_lienzo,
        )
        self.segmento_completo_hoja = ft.Segment(value="completo", label=ft.Text("Completo"))
        self.segmento_mitad_hoja = ft.Segment(value="mitad", label=ft.Text("Mitad (espejo)"))
        self.selector_modo_dibujo = ft.SegmentedButton(
            selected=["completo"],
            allow_multiple_selection=False,
            segments=[
                self.segmento_completo_hoja,
                self.segmento_mitad_hoja,
            ],
            on_change=self.on_cambio_modo_dibujo,
        )
        self.btn_sincronizar_conos = ft.OutlinedButton(
            "Usar la misma en ambos conos",
            icon=ft.Icons.SYNC,
            on_click=self.on_sincronizar_conos,
        )
        self.btn_copiar_config_hoja = ft.PopupMenuButton(
            tooltip="Copiar configuración de otra sección",
            icon=ft.Icons.COPY_ALL,
            items=[
                ft.PopupMenuItem(content=ft.Text("Copiar de Cono superior"), on_click=lambda e: self.on_copiar_config("superior")),
                ft.PopupMenuItem(content=ft.Text("Copiar de Cono inferior"), on_click=lambda e: self.on_copiar_config("inferior")),
            ],
        )

    def _crear_panel_pico(self) -> None:
        self.dd_repeticion_pico_hoja = ft.Dropdown(
            label="Repetición del pico",
            value="todas_a",
            options=[
                ft.DropdownOption(key="todas_a", text="Todas iguales (A)"),
                ft.DropdownOption(key="alternar_gajo", text="Alternar por gajo"),
                ft.DropdownOption(key="alternar_hilera", text="Alternar por hilera"),
                ft.DropdownOption(key="ajedrez", text="Ajedrez"),
            ],
            on_select=self.on_cambio_repeticion_pico_hoja,
            dense=True,
            width=200,
        )
        self.lbl_resumen_pico = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500)
        self.panel_diseno_pico_hoja = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Diseño del pico", size=13, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[self.dd_repeticion_pico_hoja, self.lbl_resumen_pico],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            padding=8,
            visible=False,
        )

    def _crear_panel_parametros_hoja(self) -> None:
        self.dd_modo_esquema = ft.Dropdown(
            label="Modo de diseño",
            value="repeticion",
            options=[
                ft.DropdownOption(key="repeticion", text="Repetición"),
                ft.DropdownOption(key="central_espejo", text="Central con espejo"),
                ft.DropdownOption(key="espejo_total", text="Espejo total"),
                ft.DropdownOption(key="personalizado", text="Personalizado"),
            ],
            on_select=self.on_cambio_esquema_opciones,
            dense=True,
            width=180,
        )
        self.txt_tam_grupo = ft.TextField(
            label="Grupo (G)",
            value="5",
            width=90,
            dense=True,
            on_change=self.on_cambio_esquema_opciones,
        )
        self.txt_ciclo_personalizado = ft.TextField(
            label="Ciclo personalizado",
            value="0, 1, 2E, 1E",
            expand=True,
            dense=True,
            hint_text="ej. 0, 1, 2E, 1E",
            visible=False,
            on_change=self.on_cambio_esquema_opciones,
        )
        self.dd_hoja = ft.Dropdown(
            label="Hoja",
            value="carta",
            options=[
                ft.DropdownOption(key="carta", text="Carta (215.9 × 279.4 mm)"),
                ft.DropdownOption(key="a4", text="A4 (210 × 297 mm)"),
            ],
            on_select=self.on_cambio_hoja_opciones,
            dense=True,
            width=190,
        )
        self.dd_escala = ft.Dropdown(
            label="Escala",
            value="auto",
            options=[
                ft.DropdownOption(key="auto", text="Auto (ajustar)"),
                ft.DropdownOption(key="10", text="1:10"),
                ft.DropdownOption(key="15", text="1:15"),
                ft.DropdownOption(key="20", text="1:20"),
                ft.DropdownOption(key="25", text="1:25"),
                ft.DropdownOption(key="30", text="1:30"),
            ],
            on_select=self.on_cambio_hoja_opciones,
            dense=True,
            width=140,
        )
        self.btn_exportar_hoja = ft.FilledButton("Exportar hoja (SVG)", icon=ft.Icons.DOWNLOAD, on_click=self.on_exportar_hoja)
        self.btn_exportar_paquete = ft.OutlinedButton("Exportar paquete…", icon=ft.Icons.FOLDER_ZIP, on_click=self.on_exportar_paquete)
        self.lbl_error_esquema = ft.Text("", color=self.paleta.color_error, size=13, weight=ft.FontWeight.W_500, visible=False)
        self.lbl_aviso_hoja = ft.Container(
            content=ft.Text("", size=12, color=self.paleta.color_aviso, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=6,
            padding=6,
            visible=False,
        )
        self.col_resumen_esquema = ft.Column(spacing=2)

    def _crear_visor_hoja(self) -> None:
        self.visor_hoja = VisorSvg(papel_blanco=True, margen_ajuste=0.02)
        self.container_viewer_hoja = self.visor_hoja.container_viewer_svg
        self.img_svg_hoja = self.visor_hoja.img_svg
        self.detector_gestos_hoja = self.visor_hoja.detector_gestos
        self.barra_zoom_hoja = self.visor_hoja.barra_zoom
        self.lbl_zoom_hoja_porcentaje = self.visor_hoja.lbl_zoom_porcentaje
        self.btn_zoom_in_hoja = self.visor_hoja.btn_zoom_in
        self.btn_zoom_out_hoja = self.visor_hoja.btn_zoom_out
        self.btn_ajustar_hoja = self.visor_hoja.btn_ajustar
        self.lbl_instruccion_zoom_hoja = self.visor_hoja.lbl_instruccion_zoom
        self.lbl_debug_hoja = self.visor_hoja.lbl_debug
        self.lbl_vacio_hoja = ft.Container(
            content=ft.Text("Calcula para ver la hoja de trazo", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )
        self.panel_contenido_hoja = ft.Column(
            expand=True,
            visible=False,
            controls=[
                self.container_viewer_hoja,
                self.barra_zoom_hoja,
                ft.Row([self.lbl_instruccion_zoom_hoja], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=4,
        )

    def _montar_contenedor(self) -> None:
        self.contenedor = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.Row(
                        controls=[
                            self.selector_pieza_hoja,
                            self.selector_lienzo,
                            self.selector_modo_dibujo,
                            self.btn_sincronizar_conos,
                            self.btn_copiar_config_hoja,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=10,
                    ),
                    self.panel_diseno_pico_hoja,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            self.dd_modo_esquema,
                            self.txt_tam_grupo,
                            self.txt_ciclo_personalizado,
                            self.dd_hoja,
                            self.dd_escala,
                            self.btn_exportar_hoja,
                            self.btn_exportar_paquete,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        wrap=True,
                        spacing=8,
                    ),
                    self.lbl_error_esquema,
                    self.lbl_aviso_hoja,
                    ft.ExpansionTile(
                        title=ft.Text("Resumen de piezas del esquema", size=13, weight=ft.FontWeight.BOLD),
                        expanded=False,
                        dense=True,
                        controls=[ft.Container(padding=8, content=self.col_resumen_esquema)],
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.lbl_vacio_hoja,
                    self.panel_contenido_hoja,
                ],
                spacing=6,
            ),
        )

    def construir(self) -> ft.Control:
        return self.contenedor

    def actualizar(self, vm: ViewModelTrompo, reset_zoom: bool = False) -> None:
        sel_hoja = self.selector_pieza_hoja.selected[0] if self.selector_pieza_hoja.selected else "superior"
        self.panel_diseno_pico_hoja.visible = (sel_hoja == "pico")
        self.btn_sincronizar_conos.visible = (sel_hoja != "pico")
        cfg_hoja = vm.config_secciones.get(sel_hoja)
        if cfg_hoja:
            puede_h, mot_h = cfg_hoja.puede_usar_mitad()
            self.segmento_mitad_hoja.disabled = not puede_h
            self.segmento_mitad_hoja.tooltip = mot_h if not puede_h else "Trazo sobre papel doblado en simetría"
            self.selector_modo_dibujo.selected = [cfg_hoja.dibujar]
            self.selector_lienzo.selected = [cfg_hoja.lienzo]

        if vm.resumen_pico_linea:
            self.lbl_resumen_pico.value = vm.resumen_pico_linea

        self.lbl_error_esquema.value = vm.esquema_error or ""
        self.lbl_error_esquema.visible = bool(vm.esquema_error)

        if vm.aviso_hoja:
            self.lbl_aviso_hoja.content.value = vm.aviso_hoja
            self.lbl_aviso_hoja.visible = True
        else:
            self.lbl_aviso_hoja.visible = False

        self.col_resumen_esquema.controls.clear()
        for linea in vm.resumen_esquema:
            self.col_resumen_esquema.controls.append(ft.Text(f"• {linea}", size=12, color=ft.Colors.ON_SURFACE_VARIANT))

        if vm.svg_hoja and not vm.desactualizado and not vm.esquema_error:
            self.lbl_vacio_hoja.visible = False
            self.panel_contenido_hoja.visible = True
            self.renderizar_hoja(reset_vista=reset_zoom)
        else:
            if vm.esquema_error:
                self.lbl_vacio_hoja.content.value = "Corrige el esquema para generar la hoja"
            elif vm.desactualizado:
                self.lbl_vacio_hoja.content.value = "Pulsa Calcular para actualizar la hoja"
            else:
                self.lbl_vacio_hoja.content.value = "Calcula para ver la hoja de trazo"
            self.lbl_vacio_hoja.visible = True
            self.panel_contenido_hoja.visible = False

    def renderizar_hoja(self, reset_vista: bool = False) -> None:
        vm = self.controlador.get_view_model()
        self._svg_hoja_raw = vm.svg_hoja
        self.visor_hoja.cargar_svg(vm.svg_hoja, reset_vista=reset_vista)

    def on_cambio_pieza_hoja(self, e) -> None:
        sel = self.selector_pieza_hoja.selected[0] if self.selector_pieza_hoja.selected else "superior"
        self.controlador.actualizar_opciones_hoja(pieza=sel)
        self.panel_diseno_pico_hoja.visible = (sel == "pico")
        cfg = self.controlador.obtener_config_seccion(sel)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
            else:
                self.txt_ciclo_personalizado.value = ""
            self.txt_ciclo_personalizado.visible = (cfg.esquema.modo == "personalizado")
            self.txt_tam_grupo.visible = (cfg.esquema.modo != "personalizado")
        self.dd_escala.value = str(cfg.escala)
        self.selector_lienzo.selected = [cfg.lienzo]
        self.selector_modo_dibujo.selected = [cfg.dibujar]
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    def on_sincronizar_conos(self, e) -> None:
        origen = self.controlador.hoja_pieza
        if origen not in ("superior", "inferior"):
            origen = "superior"
        self.controlador.sincronizar_conos(origen)
        cfg = self.controlador.obtener_config_seccion(self.controlador.hoja_pieza)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)
        if self.on_mostrar_snackbar:
            self.on_mostrar_snackbar("Configuración sincronizada en ambos conos")

    def on_copiar_config(self, origen: str) -> None:
        destino = self.controlador.hoja_pieza
        self.controlador.copiar_configuracion_seccion(origen, destino)
        cfg = self.controlador.obtener_config_seccion(destino)
        if cfg.esquema:
            self.dd_modo_esquema.value = cfg.esquema.modo
            self.txt_tam_grupo.value = str(cfg.esquema.tam_grupo)
            if cfg.esquema.ciclo:
                self.txt_ciclo_personalizado.value = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in cfg.esquema.ciclo)
        self.dd_escala.value = str(cfg.escala)
        self.selector_lienzo.selected = [cfg.lienzo]
        self.selector_modo_dibujo.selected = [cfg.dibujar]
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)
        if self.on_mostrar_snackbar:
            self.on_mostrar_snackbar(f"Configuración copiada desde {origen}")

    def on_cambio_lienzo(self, e) -> None:
        sel = self.selector_lienzo.selected[0] if self.selector_lienzo.selected else "abanico"
        self.controlador.actualizar_opciones_hoja(lienzo=sel)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    def on_cambio_modo_dibujo(self, e) -> None:
        sel = self.selector_modo_dibujo.selected[0] if self.selector_modo_dibujo.selected else "completo"
        self.controlador.actualizar_opciones_hoja(dibujar=sel)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    def on_cambio_repeticion_pico_hoja(self, e) -> None:
        rep = self.dd_repeticion_pico_hoja.value or "todas_a"
        self.controlador.actualizar_esquema_pico(modo_repeticion=rep)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    def on_cambio_esquema_opciones(self, e) -> None:
        modo = self.dd_modo_esquema.value or "repeticion"
        self.txt_ciclo_personalizado.visible = (modo == "personalizado")
        self.txt_tam_grupo.visible = (modo != "personalizado")
        tam_g = 5
        try:
            tam_g = int(self.txt_tam_grupo.value or "5")
        except ValueError:
            pass
        ciclo = self.txt_ciclo_personalizado.value or ""
        self.controlador.actualizar_esquema(modo=modo, tam_grupo=tam_g, ciclo_texto=ciclo)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    def on_cambio_hoja_opciones(self, e) -> None:
        hoja = self.dd_hoja.value or "carta"
        escala = self.dd_escala.value or "auto"
        self.controlador.actualizar_opciones_hoja(tipo=hoja, escala=escala)
        if self.on_solicitar_sync:
            self.on_solicitar_sync(True)

    async def on_exportar_hoja(self, e) -> None:
        if not self.controlador.svg_hoja:
            if self.on_mostrar_snackbar:
                self.on_mostrar_snackbar("No hay hoja de trazo para exportar")
            return
        nombre_def = f"hoja_{self.controlador.hoja_pieza}_{self.controlador.esquema_modo}.svg"
        ruta = await self.file_picker.save_file(
            dialog_title="Exportar hoja de trazo",
            file_name=nombre_def,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["svg"],
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(self.controlador.svg_hoja)
                if self.on_mostrar_snackbar:
                    self.on_mostrar_snackbar(f"Hoja exportada: {os.path.basename(ruta)}")
            except Exception as err:
                if self.on_mostrar_snackbar:
                    self.on_mostrar_snackbar(f"Error al exportar hoja: {err}")

    async def on_exportar_paquete(self, e) -> None:
        if not (self.controlador.resultado and self.controlador.entrada_actual):
            if self.on_mostrar_snackbar:
                self.on_mostrar_snackbar("Calcula el modelo antes de exportar el paquete")
            return
        carpeta = await self.file_picker.get_directory_path(
            dialog_title="Seleccionar carpeta para paquete de exportación"
        )
        if carpeta:
            try:
                archivos_dict = generar_paquete(
                    self.controlador.resultado,
                    self.controlador.entrada_actual,
                    esquema=self.controlador._construir_esquema(),
                    hoja=self.controlador.hoja_tipo,
                    escala=self.controlador.hoja_escala,
                )
                archivos_escritos = guardar_paquete(carpeta, archivos_dict, sobrescribir=True)
                if self.on_mostrar_snackbar:
                    self.on_mostrar_snackbar(f"Paquete exportado: {len(archivos_escritos)} archivos guardados")
            except Exception as err:
                if self.on_mostrar_snackbar:
                    self.on_mostrar_snackbar(f"Error al exportar paquete: {err}")
