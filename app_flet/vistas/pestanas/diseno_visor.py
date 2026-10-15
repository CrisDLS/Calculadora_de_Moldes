"""Gestión del visor SVG de diseño: renderizado, zoom, paneo, telemetría y recomposición."""

import logging
import threading
import time
from typing import Callable, Optional, Tuple
import flet as ft
from app_flet.vistas.componentes.visor_svg import VisorSvg
from logic.exportacion.vista_svg import (
    VistaSvg,
    adaptar_aspecto,
    ajustar,
    aplicar_viewbox,
    desplazar,
    extraer_dimensiones_svg,
    zoom,
)

logger = logging.getLogger("globos")


class VisorDisenoGestor:
    """Controla el visor interactivo de diseño, gestos y recomposición asíncrona."""

    def __init__(
        self,
        controlador,
        inspector,
        debug_mode: bool = False,
        obtener_pagina: Optional[Callable[[], Optional[ft.Page]]] = None,
        on_solicitar_sync: Optional[Callable[..., None]] = None,
    ):
        self.controlador = controlador
        self.inspector = inspector
        self.debug_mode = debug_mode
        self._obtener_pagina = obtener_pagina
        self.on_solicitar_sync = on_solicitar_sync

        self.modo_interaccion_diseno: str = "navegar"
        self._svg_diseno_raw: str = ""

        # Visor compartido
        self.visor = VisorSvg(
            papel_blanco=True,
            drag_interval=35,
            margen_ajuste=0.04,
            on_custom_pan_start=self._on_gesture_pan_start,
            on_custom_pan_update=self._on_gesture_pan_update,
            on_custom_pan_end=self._on_gesture_pan_end,
            on_custom_pan_cancel=self._on_gesture_pan_cancel,
            on_custom_exit=self._on_gesture_exit,
        )
        self.container_viewer = self.visor.container_viewer_svg
        self.img_svg = self.visor.img_svg
        self.detector_gestos = self.visor.detector_gestos
        self.btn_zoom_in = self.visor.btn_zoom_in
        self.btn_zoom_out = self.visor.btn_zoom_out
        self.btn_ajustar = self.visor.btn_ajustar
        self.lbl_zoom_porcentaje = self.visor.lbl_zoom_porcentaje
        self.lbl_instruccion_zoom = self.visor.lbl_instruccion_zoom

        self.lbl_estado_diseno = ft.Text(
            "",
            size=11,
            color=ft.Colors.PRIMARY,
            weight=ft.FontWeight.W_500,
            italic=True,
        )
        self.barra_zoom = ft.Row(
            controls=[
                self.btn_zoom_out,
                self.lbl_zoom_porcentaje,
                self.btn_zoom_in,
                self.btn_ajustar,
                self.lbl_estado_diseno,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        # Telemetría de arrastre y recomposición
        self.telemetria_arrastre_eventos: int = 0
        self.telemetria_arrastre_inicio_ts: float = 0.0
        self.telemetria_eventos_por_segundo: float = 0.0
        self.telemetria_ms_ultima_recomposicion: float = 0.0
        self.telemetria_recomposiciones_pendientes: int = 0
        self.telemetria_recomposiciones_descartadas: int = 0
        self.arrastrando_capa: bool = False
        self._id_recomposicion_diseno: int = 0
        self._timer_seguridad_arrastre: Optional[threading.Timer] = None

        self.lbl_debug_diseno = ft.Text(
            "",
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
            visible=self.debug_mode,
        )

    @property
    def vista_svg(self) -> Optional[VistaSvg]:
        return self.visor.vista_svg

    @vista_svg.setter
    def vista_svg(self, val: Optional[VistaSvg]) -> None:
        self.visor.vista_svg = val

    @property
    def vista_base_svg(self) -> Optional[VistaSvg]:
        return self.visor.vista_base_svg

    @vista_base_svg.setter
    def vista_base_svg(self, val: Optional[VistaSvg]) -> None:
        self.visor.vista_base_svg = val

    @property
    def zona_ancho(self) -> float:
        return self.visor.zona_ancho

    @zona_ancho.setter
    def zona_ancho(self, val: float) -> None:
        self.visor.zona_ancho = val

    @property
    def zona_alto(self) -> float:
        return self.visor.zona_alto

    @zona_alto.setter
    def zona_alto(self, val: float) -> None:
        self.visor.zona_alto = val

    def _porcentaje_zoom_diseno(self) -> float:
        return self.visor.porcentaje_zoom()

    def _limites_zoom_diseno(self) -> Tuple[float, float]:
        if not self.vista_base_svg:
            return (1.0, 1000.0)
        ancho_min = self.vista_base_svg.ancho / 40.0
        ancho_max = self.vista_base_svg.ancho * 1.5
        return (ancho_min, ancho_max)

    def _on_container_diseno_size_change(self, e) -> None:
        self.visor._on_container_size_change(e)

    def renderizar_diseno(self, reset_vista: bool = False) -> None:
        if not self.controlador.svg_diseno:
            self.img_svg.src = ""
            return
        self._svg_diseno_raw = self.controlador.svg_diseno
        self.visor.cargar_svg(self._svg_diseno_raw, reset_vista=reset_vista)

    def _actualizar_imagen_diseno(self) -> None:
        self.visor.actualizar_imagen()

    def _actualizar_imagen_diseno_zoom(self, force: bool = False) -> None:
        self.visor.actualizar_imagen_zoom(force=force)

    def _on_gesture_pan_start(self, e) -> None:
        if self.modo_interaccion_diseno == "mover":
            capa = self.controlador.obtener_capa_seleccionada()
            if capa and not capa.bloqueada:
                self.arrastrando_capa = True
                self.telemetria_arrastre_eventos = 0
                self.telemetria_arrastre_inicio_ts = time.time()
                self._reiniciar_timer_seguridad_arrastre()
                try:
                    logger.info(f"Inicio de arrastre de capa '{capa.nombre}' (id={capa.id})")
                except Exception:
                    pass

    def _on_gesture_pan_update(self, e: ft.DragUpdateEvent) -> None:
        if not self.vista_svg or not self.vista_base_svg:
            return
        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if not (delta and hasattr(delta, "x") and hasattr(delta, "y")):
            return

        capa_sel = self.controlador.obtener_capa_seleccionada()
        if self.modo_interaccion_diseno == "mover" and capa_sel and not capa_sel.bloqueada:
            self.arrastrando_capa = True
            self.telemetria_arrastre_eventos += 1
            dt = time.time() - getattr(self, "telemetria_arrastre_inicio_ts", time.time())
            if dt > 0.05:
                self.telemetria_eventos_por_segundo = self.telemetria_arrastre_eventos / dt
            self._reiniciar_timer_seguridad_arrastre()

            w_control = max(50.0, self.zona_ancho)
            h_control = max(50.0, self.zona_alto)
            dx_mm = delta.x * (self.vista_svg.ancho / w_control)
            dy_mm = delta.y * (self.vista_svg.alto / h_control)
            vent = self.controlador.ventana_lienzo()
            w_cm = max(1.0, vent[2] - vent[0])
            factor_escala = self.vista_base_svg.ancho / w_cm
            if factor_escala <= 0:
                factor_escala = 1.0
            dx_cm = dx_mm / factor_escala
            dy_cm = dy_mm / factor_escala

            self.controlador.empujar_capa_seleccionada(dx=dx_cm, dy=dy_cm, actualizar_svg=False)

            capa_act = self.controlador.obtener_capa_seleccionada()
            if capa_act:
                self.inspector._actualizando_programatico = True
                try:
                    self.inspector.txt_pos_x.value = f"{capa_act.x:.2f}"
                    self.inspector.txt_pos_y.value = f"{capa_act.y:.2f}"
                    self.inspector.txt_pos_x.update()
                    self.inspector.txt_pos_y.update()
                except Exception:
                    pass
                finally:
                    self.inspector._actualizando_programatico = False

            if self.debug_mode:
                self._actualizar_debug_diseno()
        else:
            w_control = max(50.0, self.zona_ancho)
            h_control = max(50.0, self.zona_alto)
            dx = delta.x * (self.vista_svg.ancho / w_control)
            dy = delta.y * (self.vista_svg.alto / h_control)
            limites_cont = (self.vista_base_svg.ancho, self.vista_base_svg.alto)
            self.vista_svg = desplazar(self.vista_svg, dx=dx, dy=dy, limites_contenido=limites_cont)
            self._actualizar_imagen_diseno_zoom()

    def _on_gesture_pan_end(self, e) -> None:
        self.finalizar_arrastre_capa()

    def _on_gesture_pan_cancel(self, e) -> None:
        self.finalizar_arrastre_capa()

    def _on_gesture_exit(self, e) -> None:
        if getattr(self, "arrastrando_capa", False):
            self.finalizar_arrastre_capa()

    def _reiniciar_timer_seguridad_arrastre(self) -> None:
        if self._timer_seguridad_arrastre:
            try:
                self._timer_seguridad_arrastre.cancel()
            except Exception:
                pass
        self._timer_seguridad_arrastre = threading.Timer(2.0, self._timeout_arrastre_capa)
        self._timer_seguridad_arrastre.daemon = True
        self._timer_seguridad_arrastre.start()

    def _timeout_arrastre_capa(self) -> None:
        if getattr(self, "arrastrando_capa", False):
            try:
                logger.warning("Arrastre de capa finalizado por timeout de seguridad (2.0s)")
            except Exception:
                pass
            self.finalizar_arrastre_capa()

    def finalizar_arrastre_capa(self) -> None:
        if self._timer_seguridad_arrastre:
            try:
                self._timer_seguridad_arrastre.cancel()
            except Exception:
                pass
            self._timer_seguridad_arrastre = None

        if not getattr(self, "arrastrando_capa", False):
            return

        self.arrastrando_capa = False
        self._id_recomposicion_diseno += 1
        current_id = self._id_recomposicion_diseno
        self.telemetria_recomposiciones_pendientes += 1

        try:
            self.lbl_estado_diseno.value = "Actualizando…"
            self.lbl_estado_diseno.update()
        except Exception:
            pass

        def worker():
            t0 = time.time()
            try:
                self.controlador.actualizar_svg_diseno()
            except Exception as err:
                try:
                    logger.error(f"Error al recomponer SVG de diseño: {err}", exc_info=True)
                except Exception:
                    pass
            finally:
                ms = (time.time() - t0) * 1000.0
                self.telemetria_ms_ultima_recomposicion = ms
                self._aplicar_recomposicion_diseno(current_id)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _aplicar_recomposicion_diseno(self, req_id: int) -> None:
        self.telemetria_recomposiciones_pendientes = max(0, self.telemetria_recomposiciones_pendientes - 1)
        if req_id != self._id_recomposicion_diseno:
            self.telemetria_recomposiciones_descartadas += 1
            return

        def sync_ui():
            try:
                self.lbl_estado_diseno.value = ""
                self.lbl_estado_diseno.update()
            except Exception:
                pass
            if self.on_solicitar_sync:
                try:
                    self.on_solicitar_sync()
                except Exception as ex:
                    try:
                        logger.error(f"Error al sincronizar vista tras recomposición: {ex}")
                    except Exception:
                        pass

        pagina = self._obtener_pagina() if self._obtener_pagina else None
        if pagina:
            try:
                pagina.run_thread(sync_ui)
            except Exception:
                sync_ui()
        else:
            sync_ui()

    def ajustar_vista(self) -> None:
        self.visor.ajustar()

    def obtener_estado_telemetria(self) -> dict:
        return {
            "arrastrando": getattr(self, "arrastrando_capa", False),
            "modo": getattr(self, "modo_interaccion_diseno", "navegar"),
            "eventos_arrastre": getattr(self, "telemetria_arrastre_eventos", 0),
            "pendientes": getattr(self, "telemetria_recomposiciones_pendientes", 0),
            "descartadas": getattr(self, "telemetria_recomposiciones_descartadas", 0),
        }

    def _actualizar_debug_diseno(self) -> None:
        if not self.debug_mode:
            return
        self.lbl_debug_diseno.value = (
            f"arrastre: {self.telemetria_eventos_por_segundo:.1f} ev/s · "
            f"última recomp: {self.telemetria_ms_ultima_recomposicion:.1f} ms · "
            f"pendientes: {self.telemetria_recomposiciones_pendientes} · "
            f"descartadas: {self.telemetria_recomposiciones_descartadas}"
        )
        try:
            self.lbl_debug_diseno.update()
        except Exception:
            pass
