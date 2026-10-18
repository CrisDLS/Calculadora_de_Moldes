"""Panel lateral de capas e inspector de propiedades de la capa en la pestaña Diseño."""

from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo


class PanelCapasInspector:
    """Gestiona la lista de capas y el inspector de propiedades de la capa seleccionada."""

    def __init__(
        self,
        controlador,
        file_picker,
        on_solicitar_sync: Callable[..., None],
        on_mostrar_snackbar: Callable[[str], None],
        obtener_pagina: Optional[Callable[[], Optional[ft.Page]]] = None,
    ):
        self.controlador = controlador
        self.file_picker = file_picker
        self.on_solicitar_sync = on_solicitar_sync
        self.on_mostrar_snackbar = on_mostrar_snackbar
        self._obtener_pagina = obtener_pagina
        self._actualizando_programatico: bool = False

        self._crear_controles()

    @property
    def pagina(self) -> Optional[ft.Page]:
        return self._obtener_pagina() if self._obtener_pagina else None

    def _crear_controles(self) -> None:
        # Panel lateral de capas
        self.btn_anadir_capa = ft.FilledButton(
            "Añadir capa…",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            on_click=self.on_anadir_capa_click,
        )
        self.col_lista_capas = ft.Column(spacing=4)

        # Inspector de capa seleccionada
        self.txt_nombre_capa = ft.TextField(label="Nombre", dense=True, on_change=self.on_nombre_capa_change)
        self.txt_pos_x = ft.TextField(label="Posición X (cm)", dense=True, width=120, on_change=self.on_pos_x_change)
        self.txt_pos_y = ft.TextField(label="Posición Y (cm)", dense=True, width=120, on_change=self.on_pos_y_change)
        self.txt_ancho_capa = ft.TextField(label="Ancho (cm)", dense=True, width=120, on_change=self.on_ancho_capa_change)
        self.txt_alto_capa = ft.TextField(label="Alto (cm)", dense=True, width=120, on_change=self.on_alto_capa_change)
        self.chk_proporcion = ft.Checkbox(label="Mantener proporción", value=True, on_change=self.on_proporcion_change)
        self.slider_rotacion = ft.Slider(min=-180, max=180, divisions=72, label="{value}°", on_change=self.on_rotacion_change)
        self.lbl_rotacion_val = ft.Text("0°", size=12)
        self.btn_reflejo_h = ft.IconButton(icon=ft.Icons.FLIP, tooltip="Reflejo horizontal", on_click=self.on_reflejo_h_click)
        self.btn_reflejo_v = ft.IconButton(icon=ft.Icons.FLIP_CAMERA_ANDROID, tooltip="Reflejo vertical", on_click=self.on_reflejo_v_click)
        self.slider_opacidad = ft.Slider(min=0.0, max=1.0, divisions=20, label="{value}", on_change=self.on_opacidad_change)
        self.lbl_opacidad_val = ft.Text("100%", size=12)

        # Botones de ajuste rápido (6 modos)
        self.btn_ajustar_cubrir = ft.TextButton("Cubrir", icon=ft.Icons.ZOOM_OUT_MAP, on_click=self.on_ajustar_cubrir_click, tooltip="Escala conservando proporción para cubrir la ventana")
        self.btn_ajustar_contener = ft.TextButton("Contener", icon=ft.Icons.FIT_SCREEN, on_click=self.on_ajustar_contener_click, tooltip="Escala conservando proporción para caber completo")
        self.btn_ajustar_estirar = ft.TextButton("Estirar", icon=ft.Icons.OPEN_IN_FULL, on_click=self.on_ajustar_estirar_click, tooltip="Llena la ventana estirando ancho y alto")
        self.btn_ajustar_ancho = ft.TextButton("Ancho", icon=ft.Icons.SWAP_HORIZ, on_click=self.on_ajustar_ancho_click, tooltip="Ajusta al ancho del abanico")
        self.btn_ajustar_alto = ft.TextButton("Alto", icon=ft.Icons.SWAP_VERT, on_click=self.on_ajustar_alto_click, tooltip="Ajusta al alto del abanico")
        self.btn_centrar_capa = ft.TextButton("Centrar", icon=ft.Icons.CENTER_FOCUS_STRONG, on_click=self.on_centrar_capa_click, tooltip="Centra la capa en el abanico")

        # Botones de empuje rápido (nudge)
        self.btn_nudge_left = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=18, tooltip="Mover izq. (-1 cm)", on_click=lambda e: self._empujar_capa(dx=-1.0))
        self.btn_nudge_right = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, icon_size=18, tooltip="Mover der. (+1 cm)", on_click=lambda e: self._empujar_capa(dx=1.0))
        self.btn_nudge_up = ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_size=18, tooltip="Mover arriba (+1 cm)", on_click=lambda e: self._empujar_capa(dy=1.0))
        self.btn_nudge_down = ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_size=18, tooltip="Mover abajo (-1 cm)", on_click=lambda e: self._empujar_capa(dy=-1.0))

        self.btn_rot_m5 = ft.TextButton("-5°", on_click=lambda e: self._empujar_capa(drot=-5.0), tooltip="Girar 5° contra reloj")
        self.btn_rot_p5 = ft.TextButton("+5°", on_click=lambda e: self._empujar_capa(drot=5.0), tooltip="Girar 5° a favor de reloj")
        self.btn_rot_0 = ft.TextButton("0°", on_click=lambda e: self._fijar_rotacion_0(), tooltip="Restablecer rotación a 0°")

        self.panel_inspector_capa = ft.Column(
            visible=False,
            spacing=8,
            controls=[
                ft.Text("Propiedades de la capa", weight=ft.FontWeight.BOLD, size=14),
                self.txt_nombre_capa,
                ft.Row([self.txt_pos_x, self.txt_pos_y], spacing=8),
                ft.Row(
                    controls=[
                        ft.Text("Mover (1 cm):", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                        self.btn_nudge_left,
                        self.btn_nudge_down,
                        self.btn_nudge_up,
                        self.btn_nudge_right,
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row([self.txt_ancho_capa, self.txt_alto_capa], spacing=8),
                self.chk_proporcion,
                ft.Text("Ajuste rápido al abanico:", size=12, weight=ft.FontWeight.W_500),
                ft.Row([self.btn_ajustar_cubrir, self.btn_ajustar_contener, self.btn_ajustar_estirar], wrap=True, spacing=4),
                ft.Row([self.btn_ajustar_ancho, self.btn_ajustar_alto, self.btn_centrar_capa], wrap=True, spacing=4),
                ft.Text("Rotación:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row([self.slider_rotacion, self.lbl_rotacion_val], spacing=4),
                ft.Row([self.btn_rot_m5, self.btn_rot_0, self.btn_rot_p5], spacing=4),
                ft.Row([self.btn_reflejo_h, self.btn_reflejo_v], spacing=8),
                ft.Text("Opacidad:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row([self.slider_opacidad, self.lbl_opacidad_val], spacing=4),
            ],
        )

    def actualizar(self, vm: ViewModelTrompo) -> None:
        """Actualiza la lista de capas y el inspector con el estado actual."""
        self.col_lista_capas.controls.clear()
        capa_activa = self.controlador.obtener_capa_seleccionada()
        faltantes = getattr(vm, "recursos_faltantes", []) or []

        if faltantes:
            self.col_lista_capas.controls.append(
                ft.Container(
                    padding=8,
                    border_radius=6,
                    bgcolor=ft.Colors.ERROR_CONTAINER,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.ERROR, size=18),
                            ft.Text(
                                f"Archivos faltantes: {', '.join(faltantes)}",
                                size=11,
                                color=ft.Colors.ON_ERROR_CONTAINER,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        for c in vm.capas_diseno:
            es_sel = (c.id == vm.capa_seleccionada_id)
            es_faltante = c.archivo in faltantes
            self.col_lista_capas.controls.append(self._crear_fila_capa(c, es_sel, es_faltante))

        if capa_activa:
            self.panel_inspector_capa.visible = True
            self.txt_nombre_capa.value = capa_activa.nombre
            self.txt_pos_x.value = f"{capa_activa.x:.2f}"
            self.txt_pos_y.value = f"{capa_activa.y:.2f}"
            self.txt_ancho_capa.value = f"{capa_activa.ancho:.2f}"
            self.txt_alto_capa.value = f"{capa_activa.alto:.2f}"
            self.chk_proporcion.value = self.controlador.mantener_proporcion
            self.slider_rotacion.value = float(capa_activa.rotacion)
            self.lbl_rotacion_val.value = f"{capa_activa.rotacion:.0f}°"
            self.slider_opacidad.value = float(capa_activa.opacidad)
            self.lbl_opacidad_val.value = f"{int(capa_activa.opacidad * 100)}%"
        else:
            self.panel_inspector_capa.visible = False

    def _crear_fila_capa(self, c, es_sel: bool, es_faltante: bool) -> ft.Container:
        """Crea el contenedor de control para una capa en la lista lateral."""
        c_id = c.id
        btn_vis = ft.IconButton(
            icon=ft.Icons.VISIBILITY if c.visible else ft.Icons.VISIBILITY_OFF,
            icon_size=16, tooltip="Visibilidad",
            on_click=lambda e, cid=c_id, v=not c.visible: self._toggle_visibilidad_capa(cid, v),
        )
        btn_lock = ft.IconButton(
            icon=ft.Icons.LOCK if c.bloqueada else ft.Icons.LOCK_OPEN,
            icon_size=16, tooltip="Bloquear",
            on_click=lambda e, cid=c_id, l=not c.bloqueada: self._toggle_bloqueo_capa(cid, l),
        )
        btn_up = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD, icon_size=16, tooltip="Subir orden",
            on_click=lambda e, cid=c_id: self._mover_capa(cid, -1),
        )
        btn_down = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD, icon_size=16, tooltip="Bajar orden",
            on_click=lambda e, cid=c_id: self._mover_capa(cid, 1),
        )
        btn_del = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.ERROR, tooltip="Eliminar",
            on_click=lambda e, cid=c_id: self._eliminar_capa(cid),
        )

        if es_faltante:
            ctrl_icono = ft.Icon(
                ft.Icons.WARNING_AMBER_ROUNDED,
                size=18,
                color=ft.Colors.ERROR,
                tooltip=f"Archivo faltante: {c.archivo}",
            )
            ctrl_texto = ft.Column(
                [
                    ft.Text(c.nombre, size=13, weight=ft.FontWeight.BOLD if es_sel else ft.FontWeight.NORMAL, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"Falta: {c.archivo}", size=10, color=ft.Colors.ERROR, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                ],
                spacing=1,
                expand=True,
            )
            borde = ft.Border.all(1, ft.Colors.ERROR)
        else:
            tipo_icono = ft.Icons.DRAW if c.tipo == "svg" else ft.Icons.IMAGE
            ctrl_icono = ft.Icon(tipo_icono, size=18)
            ctrl_texto = ft.Text(c.nombre, size=13, weight=ft.FontWeight.BOLD if es_sel else ft.FontWeight.NORMAL, expand=True)
            borde = ft.Border.all(1, ft.Colors.PRIMARY if es_sel else ft.Colors.OUTLINE_VARIANT)

        return ft.Container(
            padding=6,
            border_radius=6,
            bgcolor=ft.Colors.PRIMARY_CONTAINER if es_sel else ft.Colors.SURFACE_CONTAINER,
            border=borde,
            on_click=lambda e, cid=c_id: self._seleccionar_capa(cid),
            content=ft.Row(
                controls=[
                    ctrl_icono,
                    ctrl_texto,
                    btn_vis,
                    btn_lock,
                    btn_up,
                    btn_down,
                    btn_del,
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

        if capa_activa:
            self.panel_inspector_capa.visible = True
            self.txt_nombre_capa.value = capa_activa.nombre
            self.txt_pos_x.value = f"{capa_activa.x:.2f}"
            self.txt_pos_y.value = f"{capa_activa.y:.2f}"
            self.txt_ancho_capa.value = f"{capa_activa.ancho:.2f}"
            self.txt_alto_capa.value = f"{capa_activa.alto:.2f}"
            self.chk_proporcion.value = self.controlador.mantener_proporcion
            self.slider_rotacion.value = float(capa_activa.rotacion)
            self.lbl_rotacion_val.value = f"{capa_activa.rotacion:.0f}°"
            self.slider_opacidad.value = float(capa_activa.opacidad)
            self.lbl_opacidad_val.value = f"{int(capa_activa.opacidad * 100)}%"
        else:
            self.panel_inspector_capa.visible = False

    def actualizar_campos_geometria(
        self,
        x: float,
        y: float,
        ancho: float,
        alto: float,
        rotacion: Optional[float] = None,
        actualizar_ui: bool = True,
    ) -> None:
        """Actualiza los campos de texto del inspector sin disparar eventos on_change."""
        self._actualizando_programatico = True
        try:
            vx = f"{x:.2f}"
            vy = f"{y:.2f}"
            vw = f"{ancho:.2f}"
            vh = f"{alto:.2f}"
            c_x = self.txt_pos_x.value != vx
            c_y = self.txt_pos_y.value != vy
            c_w = self.txt_ancho_capa.value != vw
            c_h = self.txt_alto_capa.value != vh
            self.txt_pos_x.value = vx
            self.txt_pos_y.value = vy
            self.txt_ancho_capa.value = vw
            self.txt_alto_capa.value = vh
            c_r = False
            if rotacion is not None:
                vr = float(rotacion)
                vlr = f"{rotacion:.0f}°"
                c_r = (self.slider_rotacion.value != vr) or (self.lbl_rotacion_val.value != vlr)
                self.slider_rotacion.value = vr
                self.lbl_rotacion_val.value = vlr
            if actualizar_ui:
                if c_x:
                    self.txt_pos_x.update()
                if c_y:
                    self.txt_pos_y.update()
                if c_w:
                    self.txt_ancho_capa.update()
                if c_h:
                    self.txt_alto_capa.update()
                if c_r:
                    self.slider_rotacion.update()
                    self.lbl_rotacion_val.update()
        except Exception:
            pass
        finally:
            self._actualizando_programatico = False

    async def on_anadir_capa_click(self, e) -> None:
        archivos = await self.file_picker.pick_files(
            dialog_title="Seleccionar imagen o SVG para diseño",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png", "jpg", "jpeg", "webp", "svg"],
            allow_multiple=False,
        )
        if archivos and len(archivos) > 0 and archivos[0].path:
            ruta = archivos[0].path
            try:
                import os
                self.controlador.anadir_capa(ruta)
                self.on_solicitar_sync()
                self.on_mostrar_snackbar(f"Capa añadida: {os.path.basename(ruta)}")
            except Exception as ex:
                self.on_mostrar_snackbar(f"Error al añadir capa: {ex}")

    def _seleccionar_capa(self, cid: str) -> None:
        self.controlador.capa_seleccionada_id = cid
        self.on_solicitar_sync()

    def _mover_capa(self, cid: str, delta: int) -> None:
        self.controlador.mover_capa(cid, delta)
        self.on_solicitar_sync()

    def _toggle_visibilidad_capa(self, cid: str, vis: bool) -> None:
        self.controlador.capa_seleccionada_id = cid
        self.controlador.modificar_capa_seleccionada(visible=vis)
        self.on_solicitar_sync()

    def _toggle_bloqueo_capa(self, cid: str, lock: bool) -> None:
        for c in self.controlador.obtener_diseno_activo().capas:
            if c.id == cid:
                c.bloqueada = lock
                self.controlador.sin_guardar = True
                break
        self.on_solicitar_sync()

    def _eliminar_capa(self, cid: str) -> None:
        self.controlador.eliminar_capa(cid)
        self.on_solicitar_sync()
        self.on_mostrar_snackbar("Capa eliminada")

    def on_nombre_capa_change(self, e) -> None:
        self.controlador.modificar_capa_seleccionada(nombre=self.txt_nombre_capa.value)
        self.on_solicitar_sync()

    def on_pos_x_change(self, e) -> None:
        if self._actualizando_programatico:
            return
        try:
            val = float(self.txt_pos_x.value or 0.0)
            self.controlador.modificar_capa_seleccionada(x=val)
            self.on_solicitar_sync()
        except ValueError:
            pass

    def on_pos_y_change(self, e) -> None:
        if self._actualizando_programatico:
            return
        try:
            val = float(self.txt_pos_y.value or 0.0)
            self.controlador.modificar_capa_seleccionada(y=val)
            self.on_solicitar_sync()
        except ValueError:
            pass

    def on_ancho_capa_change(self, e) -> None:
        try:
            val = max(0.1, float(self.txt_ancho_capa.value or 1.0))
            capa = self.controlador.obtener_capa_seleccionada()
            if capa:
                if self.controlador.mantener_proporcion and capa.ancho_natural > 0:
                    alto_prop = val * (capa.alto_natural / capa.ancho_natural)
                    self.controlador.modificar_capa_seleccionada(ancho=val, alto=alto_prop)
                else:
                    self.controlador.modificar_capa_seleccionada(ancho=val)
                self.on_solicitar_sync()
        except ValueError:
            pass

    def on_alto_capa_change(self, e) -> None:
        try:
            val = max(0.1, float(self.txt_alto_capa.value or 1.0))
            capa = self.controlador.obtener_capa_seleccionada()
            if capa:
                if self.controlador.mantener_proporcion and capa.alto_natural > 0:
                    ancho_prop = val * (capa.ancho_natural / capa.alto_natural)
                    self.controlador.modificar_capa_seleccionada(ancho=ancho_prop, alto=val)
                else:
                    self.controlador.modificar_capa_seleccionada(alto=val)
                self.on_solicitar_sync()
        except ValueError:
            pass

    def on_proporcion_change(self, e) -> None:
        self.controlador.mantener_proporcion = bool(self.chk_proporcion.value)

    def on_rotacion_change(self, e) -> None:
        val = float(self.slider_rotacion.value or 0.0)
        self.lbl_rotacion_val.value = f"{val:.0f}°"
        self.controlador.modificar_capa_seleccionada(rotacion=val)
        self.on_solicitar_sync()

    def on_reflejo_h_click(self, e) -> None:
        capa = self.controlador.obtener_capa_seleccionada()
        if capa:
            self.controlador.modificar_capa_seleccionada(reflejo_h=not capa.reflejo_h)
            self.on_solicitar_sync()

    def on_reflejo_v_click(self, e) -> None:
        capa = self.controlador.obtener_capa_seleccionada()
        if capa:
            self.controlador.modificar_capa_seleccionada(reflejo_v=not capa.reflejo_v)
            self.on_solicitar_sync()

    def on_opacidad_change(self, e) -> None:
        val = float(self.slider_opacidad.value or 1.0)
        self.lbl_opacidad_val.value = f"{int(val * 100)}%"
        self.controlador.modificar_capa_seleccionada(opacidad=val)
        self.on_solicitar_sync()

    def on_ajustar_cubrir_click(self, e) -> None:
        self.controlador.ajustar_capa_cubrir()
        self.on_solicitar_sync()

    def on_ajustar_contener_click(self, e) -> None:
        self.controlador.ajustar_capa_contener()
        self.on_solicitar_sync()

    def on_ajustar_estirar_click(self, e) -> None:
        self.controlador.ajustar_capa_estirar()
        self.on_solicitar_sync()

    def on_ajustar_ancho_click(self, e) -> None:
        self.controlador.ajustar_capa_ancho()
        self.on_solicitar_sync()

    def on_ajustar_alto_click(self, e) -> None:
        self.controlador.ajustar_capa_alto()
        self.on_solicitar_sync()

    def on_centrar_capa_click(self, e) -> None:
        self.controlador.centrar_capa_seleccionada()
        self.on_solicitar_sync()

    def _empujar_capa(self, dx: float = 0.0, dy: float = 0.0, drot: float = 0.0) -> None:
        self.controlador.empujar_capa_seleccionada(dx=dx, dy=dy, drot=drot)
        self.on_solicitar_sync()

    def _fijar_rotacion_0(self) -> None:
        self.controlador.modificar_capa_seleccionada(rotacion=0.0)
        self.on_solicitar_sync()
