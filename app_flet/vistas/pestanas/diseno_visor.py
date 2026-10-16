"""Gestión del visor SVG de diseño: renderizado, zoom, paneo, telemetría y marco de edición."""

import logging
import threading
import time
from typing import Callable, Optional, Tuple
import flet as ft
from app_flet.vistas.componentes.marco_edicion import MarcoEdicion
from app_flet.vistas.componentes.visor_svg import VisorSvg
from logic.exportacion.vista_svg import (
    VistaSvg,
    adaptar_aspecto,
    ajustar,
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

        self._inicializar_visor_y_marco()
        self._inicializar_telemetria()

    def _inicializar_visor_y_marco(self) -> None:
        """Inicializa VisorSvg, MarcoEdicion y sus contenedores."""
        self.visor = VisorSvg(
            papel_blanco=True,
            drag_interval=16,
            margen_ajuste=0.04,
            on_custom_pan_start=self._on_gesture_pan_start,
            on_custom_pan_update=self._on_gesture_pan_update,
            on_custom_pan_end=self._on_gesture_pan_end,
            on_custom_pan_cancel=self._on_gesture_pan_cancel,
            on_custom_exit=self._on_gesture_exit,
        )
        self.img_svg = self.visor.img_svg
        self.detector_gestos = self.visor.detector_gestos
        self.btn_zoom_in = self.visor.btn_zoom_in
        self.btn_zoom_out = self.visor.btn_zoom_out
        self.btn_ajustar = self.visor.btn_ajustar
        self.lbl_zoom_porcentaje = self.visor.lbl_zoom_porcentaje
        self.lbl_instruccion_zoom = self.visor.lbl_instruccion_zoom

        self.marco_edicion = MarcoEdicion(
            on_cambio_geometria=self._al_cambiar_geometria_marco,
            debug_mode=self.debug_mode,
        )

        self.stack_visor = ft.Stack(
            controls=[
                self.visor.detector_gestos,
                self.marco_edicion.stack,
            ],
            expand=True,
        )
        self.visor.container_viewer_svg.content = self.stack_visor
        self.container_viewer = self.visor.container_viewer_svg

        self._on_size_change_original = self.visor.container_viewer_svg.on_size_change
        self.visor.container_viewer_svg.on_size_change = self._on_container_diseno_size_change

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

    def _inicializar_telemetria(self) -> None:
        """Inicializa métricas de rendimiento y depuración."""
        self.telemetria_arrastre_eventos: int = 0
        self.telemetria_eventos_por_segundo: float = 0.0
        self.telemetria_ms_ultima_recomposicion: float = 0.0
        self.telemetria_recomposiciones_pendientes: int = 0
        self.telemetria_recomposiciones_descartadas: int = 0
        self._id_recomposicion_diseno: int = 0
        self._timer_debounce_recomposicion: Optional[threading.Timer] = None

        self.lbl_debug_diseno = ft.Text(
            "",
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
            visible=self.debug_mode,
        )

    @property
    def arrastrando_capa(self) -> bool:
        return getattr(self.marco_edicion, "_arrastrando", False)

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

    def obtener_conversion(self):
        """Obtiene la conversión matemática actual entre pantalla (px) y plano (cm)."""
        if not self.vista_svg:
            return None
        return self.controlador.obtener_conversion_diseno(
            (self.zona_ancho, self.zona_alto), self.vista_svg
        )

    def _on_container_diseno_size_change(self, e) -> None:
        """Adapta la vista y reposiciona el marco ante cambios de tamaño de ventana."""
        self.visor.on_container_size_change(e)
        if self.modo_interaccion_diseno == "editar":
            capa = self.controlador.obtener_capa_seleccionada()
            conv = self.obtener_conversion()
            if capa and conv:
                carp = self.controlador.obtener_carpeta_recursos_activa()
                self.marco_edicion.actualizar(capa, conv, carp)

    def renderizar_diseno(self, reset_vista: bool = False) -> None:
        if not self.controlador.svg_diseno:
            self.img_svg.src = ""
            return
        self._svg_diseno_raw = self.controlador.svg_diseno
        self.visor.cargar_svg(self._svg_diseno_raw, reset_vista=reset_vista)

    # ==========================================================================
    # Modos Excluyentes: Navegar vs Editar
    # ==========================================================================

    def cambiar_modo_interaccion(self, modo: str) -> bool:
        """Cambia entre modo navegar (pan/zoom) y modo editar (marco/tiradores)."""
        if modo == "editar":
            capa = self.controlador.obtener_capa_seleccionada()
            if not capa or capa.bloqueada:
                self.lbl_estado_diseno.value = "Selecciona una capa no bloqueada para editar"
                try:
                    self.lbl_estado_diseno.update()
                except Exception:
                    pass
                return False

            self.modo_interaccion_diseno = "editar"
            # En modo editar, el visor SVG queda desactivado
            self.visor.gestos_habilitados = False

            # Cargar SVG ligero en modo fantasma
            self.controlador.actualizar_svg_diseno(modo_fantasma=True)
            self.renderizar_diseno(reset_vista=False)

            # Mostrar marco de edición superpuesto
            conv = self.obtener_conversion()
            carp = self.controlador.obtener_carpeta_recursos_activa()
            if conv:
                self.marco_edicion.mostrar(
                    capa, conv, carp, mantener_proporcion=self.controlador.mantener_proporcion
                )

            if self.controlador.diseno_lienzo_modo == "mitad":
                self.lbl_estado_diseno.value = (
                    "Modo Editar: arrastra el marco o sus tiradores · El reflejo se muestra al volver a Navegar"
                )
            else:
                self.lbl_estado_diseno.value = "Modo Editar: arrastra el marco o sus tiradores"
            try:
                self.lbl_estado_diseno.update()
            except Exception:
                pass
            return True

        else:  # "navegar"
            self.modo_interaccion_diseno = "navegar"
            # En modo navegar, reactivar gestos normales del visor
            self.visor.gestos_habilitados = True
            self.marco_edicion.ocultar()

            # Regenerar SVG completo con capas decoradas normales
            self.controlador.actualizar_svg_diseno(modo_fantasma=False)
            self.renderizar_diseno(reset_vista=False)

            self.lbl_estado_diseno.value = ""
            try:
                self.lbl_estado_diseno.update()
            except Exception:
                pass
            return True

    def _al_cambiar_geometria_marco(self, capa, finalizado: bool) -> None:
        """Callback invocado por MarcoEdicion ante micro-arrastres o al soltar."""
        # 1. Actualizar campos del inspector inmediatamente sin recargar SVG
        self.inspector.actualizar_campos_geometria(
            capa.x, capa.y, capa.ancho, capa.alto, capa.rotacion
        )
        if self.debug_mode:
            self.telemetria_arrastre_eventos = self.marco_edicion.telemetria_eventos_arrastre
            self.telemetria_eventos_por_segundo = self.marco_edicion.telemetria_eventos_sec
            self._actualizar_debug_diseno()

        # 2. Al soltar: confirmar en el controlador; en modo editar NO se recompone
        if finalizado:
            self.controlador.actualizar_geometria_capa_seleccionada(
                x=capa.x,
                y=capa.y,
                ancho=capa.ancho,
                alto=capa.alto,
                rotacion=capa.rotacion,
                actualizar_svg=False,
            )
            if self.modo_interaccion_diseno != "editar":
                self._programar_recomposicion_debounced()

    def _programar_recomposicion_debounced(self) -> None:
        """Programa la recomposición en segundo plano con debounce de 100 ms."""
        if self._timer_debounce_recomposicion:
            try:
                self._timer_debounce_recomposicion.cancel()
            except Exception:
                pass

        self._id_recomposicion_diseno += 1
        req_id = self._id_recomposicion_diseno

        def worker():
            t0 = time.time()
            try:
                # Si sigue en modo editar, actualiza el SVG ligero de fondo
                fantasma = self.modo_interaccion_diseno == "editar"
                self.controlador.actualizar_svg_diseno(modo_fantasma=fantasma)
            except Exception as err:
                try:
                    logger.error(f"Error al recomponer SVG de diseño: {err}", exc_info=True)
                except Exception:
                    pass
            finally:
                ms = (time.time() - t0) * 1000.0
                self.telemetria_ms_ultima_recomposicion = ms
                self._aplicar_recomposicion_diseno(req_id)

        self._timer_debounce_recomposicion = threading.Timer(0.100, worker)
        self._timer_debounce_recomposicion.daemon = True
        self._timer_debounce_recomposicion.start()

    def _aplicar_recomposicion_diseno(self, req_id: int) -> None:
        if req_id != self._id_recomposicion_diseno:
            self.telemetria_recomposiciones_descartadas += 1
            return

        def sync_ui():
            self.renderizar_diseno(reset_vista=False)
            if self.on_solicitar_sync:
                try:
                    self.on_solicitar_sync()
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

    # Callbacks de gestos del visor delegados (modo navegar)
    def _on_gesture_pan_start(self, e) -> None:
        pass

    def _on_gesture_pan_update(self, e) -> bool:
        # En modo navegar, retorna False para que VisorSvg haga su paneo normal
        return False

    def _on_gesture_pan_end(self, e) -> None:
        pass

    def _on_gesture_pan_cancel(self, e) -> None:
        pass

    def _on_gesture_exit(self, e) -> None:
        pass

    def ajustar_vista(self) -> None:
        self.visor.ajustar_vista()
        if self.modo_interaccion_diseno == "editar":
            conv = self.obtener_conversion()
            capa = self.controlador.obtener_capa_seleccionada()
            if conv and capa:
                self.marco_edicion.actualizar(capa, conv)

    def obtener_estado_telemetria(self) -> dict:
        return {
            "arrastrando": self.arrastrando_capa,
            "modo": self.modo_interaccion_diseno,
            "eventos_arrastre": self.telemetria_arrastre_eventos,
            "pendientes": self.telemetria_recomposiciones_pendientes,
            "descartadas": self.telemetria_recomposiciones_descartadas,
        }

    def _actualizar_debug_diseno(self) -> None:
        if not self.debug_mode:
            return
        m = self.marco_edicion
        lat = m.telemetria_latencia_ms
        ev_s = m.telemetria_eventos_sec
        v = self.visor.vista_svg
        enc = f"vBox:{v.x:.0f},{v.y:.0f},{v.ancho:.0f},{v.alto:.0f}" if v else "vBox:-"
        zona = f"zona:{self.visor.ancho_zona:.0f}x{self.visor.alto_zona:.0f}"
        ult = getattr(m, "_ultimo_evento_desc", "ninguno")
        self.lbl_debug_diseno.value = (
            f"modo:{self.modo_interaccion_diseno} · {ult} · {zona} · {enc} · {ev_s:.0f} ev/s ({lat:.1f} ms)"
        )
        try:
            self.lbl_debug_diseno.update()
        except Exception:
            pass
