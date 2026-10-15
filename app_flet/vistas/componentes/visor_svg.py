"""
Componente reutilizable de visualización SVG con zoom y paneo por viewBox.
"""

import os
import time
from typing import Callable, List, Optional, Tuple
import flet as ft

from logic.exportacion.vista_svg import (
    VistaSvg,
    adaptar_aspecto,
    ajustar,
    aplicar_viewbox,
    desplazar,
    extraer_dimensiones_svg,
    zoom,
)


class VisorSvg:
    """
    Control interactivo para visualizar y explorar gráficos SVG.
    Soporta zoom relativo al cursor, arrastre para desplazamiento,
    ajuste automático a la zona útil y telemetría de rendimiento.
    """

    def __init__(
        self,
        papel_blanco: bool = False,
        drag_interval: Optional[int] = None,
        margen_ajuste: float = 0.04,
        on_custom_pan_start: Optional[Callable] = None,
        on_custom_pan_update: Optional[Callable] = None,
        on_custom_pan_end: Optional[Callable] = None,
        on_custom_pan_cancel: Optional[Callable] = None,
        on_custom_exit: Optional[Callable] = None,
        on_cambio_vista: Optional[Callable[[VistaSvg], None]] = None,
    ):
        self.papel_blanco = papel_blanco
        self.drag_interval = drag_interval
        self.margen_ajuste = margen_ajuste
        self.on_custom_pan_start = on_custom_pan_start
        self.on_custom_pan_update = on_custom_pan_update
        self.on_custom_pan_end = on_custom_pan_end
        self.on_custom_pan_cancel = on_custom_pan_cancel
        self.on_custom_exit = on_custom_exit
        self.on_cambio_vista = on_cambio_vista

        self.zona_ancho: float = 600.0
        self.zona_alto: float = 500.0
        self._padding_container: float = 10.0
        self._border_width: float = 1.0

        self.vista_svg: Optional[VistaSvg] = None
        self.vista_base_svg: Optional[VistaSvg] = None
        self.svg_actual_raw: str = ""

        # Telemetría de depuración
        self.debug_mode = os.environ.get("GLOBOS_DEBUG") == "1"
        self._tiempos_actualizacion: List[float] = []
        self._timestamps_actualizacion: List[float] = []
        self._ultimo_render_time: float = 0.0

        # Controles internos de la UI
        self._crear_controles()

    def _crear_controles(self) -> None:
        self._crear_visor()
        self._crear_barra_herramientas()

    def _crear_visor(self) -> None:
        self.img_svg = ft.Image(
            src="",
            fit=ft.BoxFit.CONTAIN,
            width=self.zona_ancho,
            height=self.zona_alto,
        )

        detector_kwargs = {
            "content": self.img_svg,
            "expand": True,
            "on_scroll": self.on_gesture_scroll,
            "on_pan_start": self.on_gesture_pan_start,
            "on_pan_update": self.on_gesture_pan_update,
            "on_pan_end": self.on_gesture_pan_end,
            "on_pan_cancel": self.on_gesture_pan_cancel,
            "on_exit": self.on_gesture_exit,
            "on_double_tap": self.on_gesture_double_tap,
        }
        if self.drag_interval is not None:
            detector_kwargs["drag_interval"] = self.drag_interval

        self.detector_gestos = ft.GestureDetector(**detector_kwargs)

        if self.papel_blanco:
            self.container_viewer_svg = ft.Container(
                content=self.detector_gestos,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=4,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color="#00000022"),
                expand=True,
                padding=self._padding_container,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                alignment=ft.Alignment(0, 0),
                on_size_change=self.on_container_size_change,
            )
        else:
            self.container_viewer_svg = ft.Container(
                content=self.detector_gestos,
                border=ft.Border.all(self._border_width, ft.Colors.OUTLINE),
                border_radius=8,
                expand=True,
                padding=self._padding_container,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                alignment=ft.Alignment(0, 0),
                on_size_change=self.on_container_size_change,
            )

    def _crear_barra_herramientas(self) -> None:
        self.btn_zoom_out = ft.IconButton(
            icon=ft.Icons.REMOVE,
            tooltip="Alejar",
            icon_size=18,
            on_click=self.on_btn_zoom_out,
        )
        self.lbl_zoom_porcentaje = ft.Text(
            "100 %",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_500,
        )
        self.btn_zoom_in = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Acercar",
            icon_size=18,
            on_click=self.on_btn_zoom_in,
        )
        self.btn_ajustar = ft.TextButton(
            "Ajustar",
            icon=ft.Icons.FIT_SCREEN,
            on_click=self.on_btn_ajustar,
        )

        self.barra_zoom = ft.Row(
            controls=[
                self.btn_zoom_out,
                self.lbl_zoom_porcentaje,
                self.btn_zoom_in,
                self.btn_ajustar,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        self.lbl_instruccion_zoom = ft.Text(
            "Rueda: zoom al cursor · Arrastrar: mover · Doble clic: ajustar",
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )

        self.lbl_debug = ft.Text(
            "",
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
            visible=self.debug_mode,
        )

    def cargar_svg(self, svg_str: str, reset_vista: bool = False, force: bool = False) -> None:
        """Carga un nuevo string SVG y actualiza la vista."""
        self.svg_actual_raw = svg_str
        if not svg_str:
            self.img_svg.src = ""
            return

        aspecto_zona = self.zona_ancho / self.zona_alto if self.zona_alto > 0 else 1.0
        w_nat, h_nat = extraer_dimensiones_svg(svg_str)

        if reset_vista or not self.vista_svg or not self.vista_base_svg:
            self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=self.margen_ajuste)
            self.vista_svg = self.vista_base_svg

        self.actualizar_imagen_zoom(force=force)

    def limpiar(self) -> None:
        """Limpia el contenido del visor."""
        self.svg_actual_raw = ""
        self.img_svg.src = ""
        self.vista_svg = None
        self.vista_base_svg = None

    def porcentaje_zoom(self) -> float:
        """Calcula el porcentaje de zoom actual respecto a la vista base."""
        if not self.vista_svg or not self.vista_base_svg or self.vista_svg.ancho <= 0:
            return 100.0
        return (self.vista_base_svg.ancho / self.vista_svg.ancho) * 100.0

    def limites_zoom(self) -> Tuple[float, float]:
        """Calcula los límites mínimo y máximo de zoom."""
        if not self.vista_base_svg:
            return 0.1, 10.0
        return self.vista_base_svg.ancho * 0.1, self.vista_base_svg.ancho * 10.0

    def ajustar_vista(self) -> None:
        """Reajusta el zoom y centrado a la vista base."""
        if not self.svg_actual_raw:
            return
        w_nat, h_nat = extraer_dimensiones_svg(self.svg_actual_raw)
        aspecto_zona = self.zona_ancho / self.zona_alto if self.zona_alto > 0 else 1.0
        self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=self.margen_ajuste)
        self.vista_svg = self.vista_base_svg
        self.actualizar_imagen_zoom(force=True)

    def zoom_in(self) -> None:
        """Aumenta el zoom un 25% hacia el centro."""
        if not self.vista_svg:
            return
        self.vista_svg = zoom(self.vista_svg, factor=1.25, fx=0.5, fy=0.5, limites=self.limites_zoom())
        self.actualizar_imagen_zoom(force=True)

    def zoom_out(self) -> None:
        """Disminuye el zoom un 25% hacia el centro."""
        if not self.vista_svg:
            return
        self.vista_svg = zoom(self.vista_svg, factor=1.0 / 1.25, fx=0.5, fy=0.5, limites=self.limites_zoom())
        self.actualizar_imagen_zoom(force=True)

    def actualizar_imagen_zoom(self, force: bool = False, t_inicio_evento: Optional[float] = None) -> None:
        """Aplica el viewBox actual al SVG y actualiza la imagen."""
        if not self.svg_actual_raw or not self.vista_svg:
            return

        now = time.perf_counter()
        if not force and (now - self._ultimo_render_time < (1.0 / 30.0)):
            return
        self._ultimo_render_time = now

        svg_con_viewbox = aplicar_viewbox(self.svg_actual_raw, self.vista_svg)
        self.img_svg.src = svg_con_viewbox.encode("utf-8")
        self.lbl_zoom_porcentaje.value = f"{self.porcentaje_zoom():.0f} %"

        t_ref = t_inicio_evento if t_inicio_evento is not None else now
        try:
            self.img_svg.update()
            self.lbl_zoom_porcentaje.update()
        except Exception:
            pass

        t_fin = time.perf_counter()
        dt_ms = (t_fin - t_ref) * 1000.0
        self._tiempos_actualizacion.append(dt_ms)
        if len(self._tiempos_actualizacion) > 20:
            self._tiempos_actualizacion.pop(0)
        self._timestamps_actualizacion.append(t_fin)
        if len(self._timestamps_actualizacion) > 50:
            self._timestamps_actualizacion.pop(0)

        self.actualizar_debug()
        if self.on_cambio_vista:
            self.on_cambio_vista(self.vista_svg)

    def actualizar_debug(self) -> None:
        """Actualiza la etiqueta de telemetría si GLOBOS_DEBUG=1."""
        if not self.debug_mode or not self.vista_svg:
            return
        z_str = f"zona {self.zona_ancho:.0f}×{self.zona_alto:.0f} px"
        img_str = f"imagen {self.img_svg.width:.0f}×{self.img_svg.height:.0f}"
        v_str = f"vista {self.vista_svg.x:.1f},{self.vista_svg.y:.1f},{self.vista_svg.ancho:.1f},{self.vista_svg.alto:.1f}"
        zoom_str = f"zoom {self.porcentaje_zoom():.0f} %"

        media_ms = (sum(self._tiempos_actualizacion) / len(self._tiempos_actualizacion)) if self._tiempos_actualizacion else 0.0
        now = time.perf_counter()
        recientes = [t for t in self._timestamps_actualizacion if now - t <= 1.0]
        fps = len(recientes)
        telem_str = f"{media_ms:.1f} ms/act (media 20) · {fps} act/s"

        self.lbl_debug.value = f"{z_str} · {img_str} · {v_str} · {zoom_str} · {telem_str}"
        try:
            self.lbl_debug.update()
        except Exception:
            pass

    def on_container_size_change(self, e) -> None:
        """Adapta la vista al cambiar el tamaño del contenedor."""
        w_raw = getattr(e, "width", 0.0) or 0.0
        h_raw = getattr(e, "height", 0.0) or 0.0
        if w_raw <= 0 or h_raw <= 0:
            return

        descuento_w = 2.0 * (self._padding_container + self._border_width)
        descuento_h = 2.0 * (self._padding_container + self._border_width)
        w_util = max(50.0, w_raw - descuento_w)
        h_util = max(50.0, h_raw - descuento_h)

        if abs(w_util - self.zona_ancho) < 0.5 and abs(h_util - self.zona_alto) < 0.5:
            return

        self.zona_ancho = w_util
        self.zona_alto = h_util
        self.img_svg.width = self.zona_ancho
        self.img_svg.height = self.zona_alto

        aspecto_zona = self.zona_ancho / self.zona_alto
        if self.svg_actual_raw:
            w_nat, h_nat = extraer_dimensiones_svg(self.svg_actual_raw)
            self.vista_base_svg = ajustar(w_nat, h_nat, aspecto_zona=aspecto_zona, margen=self.margen_ajuste)
            if self.vista_svg:
                self.vista_svg = adaptar_aspecto(self.vista_svg, aspecto_zona)
            else:
                self.vista_svg = self.vista_base_svg
            self.actualizar_imagen_zoom(force=True)

    def on_gesture_scroll(self, e: ft.ScrollEvent) -> None:
        """Zoom centrado en el cursor mediante la rueda del ratón."""
        if not self.vista_svg:
            return
        delta_y = getattr(e, "scroll_delta", None)
        factor = 1.15
        if delta_y and hasattr(delta_y, "y"):
            if delta_y.y > 0:
                factor = 1.0 / 1.15
            elif delta_y.y < 0:
                factor = 1.15

        fx = 0.5
        fy = 0.5
        local_pos = getattr(e, "local_position", None)
        if local_pos and hasattr(local_pos, "x") and hasattr(local_pos, "y"):
            if self.zona_ancho > 0 and self.zona_alto > 0:
                fx = max(0.01, min(0.99, local_pos.x / self.zona_ancho))
                fy = max(0.01, min(0.99, local_pos.y / self.zona_alto))

        self.vista_svg = zoom(self.vista_svg, factor=factor, fx=fx, fy=fy, limites=self.limites_zoom())
        self.actualizar_imagen_zoom()

    def on_gesture_pan_start(self, e) -> None:
        if self.on_custom_pan_start:
            self.on_custom_pan_start(e)

    def on_gesture_pan_update(self, e: ft.DragUpdateEvent) -> None:
        """Arrastre para desplazar el lienzo o delegado a callback personalizado."""
        if self.on_custom_pan_update:
            consumido = self.on_custom_pan_update(e)
            if consumido:
                return

        if not self.vista_svg or not self.vista_base_svg:
            return
        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if not (delta and hasattr(delta, "x") and hasattr(delta, "y")):
            return

        w_control = max(50.0, self.zona_ancho)
        h_control = max(50.0, self.zona_alto)
        dx = delta.x * (self.vista_svg.ancho / w_control)
        dy = delta.y * (self.vista_svg.alto / h_control)
        limites_cont = (self.vista_base_svg.ancho, self.vista_base_svg.alto)
        self.vista_svg = desplazar(self.vista_svg, dx=dx, dy=dy, limites_contenido=limites_cont)
        self.actualizar_imagen_zoom()

    def on_gesture_pan_end(self, e) -> None:
        if self.on_custom_pan_end:
            self.on_custom_pan_end(e)

    def on_gesture_pan_cancel(self, e) -> None:
        if self.on_custom_pan_cancel:
            self.on_custom_pan_cancel(e)

    def on_gesture_exit(self, e) -> None:
        if self.on_custom_exit:
            self.on_custom_exit(e)

    def on_gesture_double_tap(self, e) -> None:
        self.ajustar_vista()

    def on_btn_zoom_in(self, e) -> None:
        self.zoom_in()

    def on_btn_zoom_out(self, e) -> None:
        self.zoom_out()

    def on_btn_ajustar(self, e) -> None:
        self.ajustar_vista()
