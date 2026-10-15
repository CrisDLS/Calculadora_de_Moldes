"""Componente interactivo del marco de edición y 8 tiradores en Flet.

Superpone sobre el visor SVG una capa de controles ligeros (ft.Stack) con:
- Marco semitransparente con borde azul para mover la capa.
- 8 tiradores táctiles (4 esquinas y 4 laterales) para estirar con invarianza opuesta.
- Tirador de rotación superior.
- Previsualización nativa a 60 fps sin recomposición del SVG completo.
"""

import logging
import math
import os
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple, Union

import flet as ft
from logic.diseno.gestos_lienzo import (
    Conversion,
    centro_capa,
    esquinas_capa,
    estirar,
    mover,
    rotar,
    tiradores,
)
from logic.diseno.lienzo import CapaDiseno

logger = logging.getLogger("globos")

TAM_TIRADOR_PX = 18.0
TAM_ROT_PX = 20.0
THROTTLE_S = 0.016  # <= 60 Hz


class MarcoEdicion:
    """Marco interactivo con 8 tiradores para manipulación táctil directa de una capa."""

    def __init__(
        self,
        on_cambio_geometria: Optional[Callable[[CapaDiseno, bool], None]] = None,
        debug_mode: bool = False,
    ):
        self.on_cambio_geometria = on_cambio_geometria or (lambda c, f: None)
        self.debug_mode = debug_mode or (os.environ.get("GLOBOS_DEBUG") == "1")

        self.capa_activa: Optional[CapaDiseno] = None
        self.conversion: Optional[Conversion] = None
        self.carpeta_recursos: Optional[Path] = None
        self.mantener_proporcion: bool = False

        self._arrastrando: bool = False
        self._tirador_activo: Optional[str] = None
        self._ultimo_evento_ts: float = 0.0

        self.telemetria_eventos_arrastre: int = 0
        self.telemetria_latencia_ms: float = 0.0
        self.telemetria_eventos_sec: float = 0.0
        self._inicio_arrastre_ts: float = 0.0

        self._crear_controles()

    def _crear_controles(self) -> None:
        """Inicializa los controles visuales del marco y tiradores."""
        self._crear_marco_y_cuerpo()
        self._crear_tiradores()

        ids_tiradores = ["tl", "tr", "br", "bl", "t", "b", "r", "l"]
        self.stack = ft.Stack(
            controls=[
                self.detector_cuerpo,
                *[self.detectores_tiradores[tid] for tid in ids_tiradores],
                self.detector_rot,
            ],
            visible=False,
            expand=True,
        )

    def _crear_marco_y_cuerpo(self) -> None:
        """Crea el contenedor del marco y su detector de gestos para mover."""
        self.img_preview = ft.Image(
            src="",
            fit=ft.BoxFit.FILL,
            opacity=0.8,
            visible=False,
            expand=True,
        )

        self.caja_marco = ft.Container(
            border=ft.Border.all(1.5, ft.Colors.BLUE_ACCENT),
            bgcolor="#2196F318",
            visible=False,
            content=self.img_preview,
        )

        self.detector_cuerpo = ft.GestureDetector(
            content=self.caja_marco,
            drag_interval=16,
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_start=self._on_cuerpo_pan_start,
            on_pan_update=self._on_cuerpo_pan_update,
            on_pan_end=self._on_cuerpo_pan_end,
            on_pan_cancel=self._on_cuerpo_pan_cancel,
            on_exit=self._on_cuerpo_exit,
        )

    def _crear_tiradores(self) -> None:
        """Crea los 8 tiradores de redimensionado y el tirador de rotación."""
        self.tiradores_controles: Dict[str, ft.Container] = {}
        self.detectores_tiradores: Dict[str, ft.GestureDetector] = {}

        cursores = {
            "tl": ft.MouseCursor.RESIZE_UP_LEFT_DOWN_RIGHT,
            "br": ft.MouseCursor.RESIZE_UP_LEFT_DOWN_RIGHT,
            "tr": ft.MouseCursor.RESIZE_UP_RIGHT_DOWN_LEFT,
            "bl": ft.MouseCursor.RESIZE_UP_RIGHT_DOWN_LEFT,
            "t": ft.MouseCursor.RESIZE_UP_DOWN,
            "b": ft.MouseCursor.RESIZE_UP_DOWN,
            "r": ft.MouseCursor.RESIZE_LEFT_RIGHT,
            "l": ft.MouseCursor.RESIZE_LEFT_RIGHT,
        }

        ids_tiradores = ["tl", "tr", "br", "bl", "t", "b", "r", "l"]
        for t_id in ids_tiradores:
            caja_visual = ft.Container(
                width=10,
                height=10,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1.5, ft.Colors.BLUE_ACCENT),
                border_radius=2,
            )
            cont = ft.Container(
                width=TAM_TIRADOR_PX,
                height=TAM_TIRADOR_PX,
                alignment=ft.Alignment.CENTER,
                content=caja_visual,
                visible=False,
            )
            self.tiradores_controles[t_id] = cont

            det = ft.GestureDetector(
                content=cont,
                drag_interval=16,
                mouse_cursor=cursores.get(t_id, ft.MouseCursor.BASIC),
                on_pan_start=lambda e, tid=t_id: self._on_tirador_pan_start(tid, e),
                on_pan_update=lambda e, tid=t_id: self._on_tirador_pan_update(tid, e),
                on_pan_end=lambda e, tid=t_id: self._on_tirador_pan_end(tid, e),
                on_pan_cancel=lambda e, tid=t_id: self._on_tirador_pan_cancel(tid, e),
                on_exit=lambda e, tid=t_id: self._on_tirador_exit(tid, e),
            )
            self.detectores_tiradores[t_id] = det

        caja_rot_visual = ft.Container(
            width=12,
            height=12,
            shape=ft.BoxShape.CIRCLE,
            bgcolor=ft.Colors.BLUE_ACCENT,
            border=ft.Border.all(1.5, ft.Colors.WHITE),
        )
        self.cont_rot = ft.Container(
            width=TAM_ROT_PX,
            height=TAM_ROT_PX,
            alignment=ft.Alignment.CENTER,
            content=caja_rot_visual,
            visible=False,
        )
        self.detector_rot = ft.GestureDetector(
            content=self.cont_rot,
            drag_interval=16,
            mouse_cursor=ft.MouseCursor.PRECISE,
            on_pan_start=self._on_rot_pan_start,
            on_pan_update=self._on_rot_pan_update,
            on_pan_end=self._on_rot_pan_end,
            on_pan_cancel=self._on_rot_pan_cancel,
            on_exit=self._on_rot_exit,
        )

    def mostrar(
        self,
        capa: CapaDiseno,
        conversion: Conversion,
        carpeta_recursos: Optional[Path] = None,
        mantener_proporcion: bool = False,
    ) -> None:
        """Activa y posiciona el marco de edición sobre la capa especificada."""
        self.capa_activa = capa
        self.conversion = conversion
        self.carpeta_recursos = carpeta_recursos
        self.mantener_proporcion = mantener_proporcion
        self.stack.visible = True

        self._actualizar_previsualizacion_imagen()
        self._posicionar_marco_y_tiradores()

    def ocultar(self) -> None:
        """Oculta el marco y desactiva la interacción."""
        self._arrastrando = False
        self._tirador_activo = None
        self.capa_activa = None
        self.stack.visible = False
        self.caja_marco.visible = False
        for c in self.tiradores_controles.values():
            c.visible = False
        self.cont_rot.visible = False

    def actualizar(
        self,
        capa: CapaDiseno,
        conversion: Conversion,
        carpeta_recursos: Optional[Path] = None,
        mantener_proporcion: Optional[bool] = None,
    ) -> None:
        """Actualiza la geometría y posición del marco con una nueva conversión."""
        self.capa_activa = capa
        self.conversion = conversion
        if carpeta_recursos is not None:
            self.carpeta_recursos = carpeta_recursos
        if mantener_proporcion is not None:
            self.mantener_proporcion = mantener_proporcion

        if self.stack.visible and self.capa_activa and self.conversion:
            self._posicionar_marco_y_tiradores()

    def _actualizar_previsualizacion_imagen(self) -> None:
        """Configura la imagen fantasma dentro del marco para previsualización."""
        if not self.capa_activa or not self.carpeta_recursos:
            self.img_preview.visible = False
            return

        ruta_img = self.carpeta_recursos / self.capa_activa.archivo
        if ruta_img.exists() and self.capa_activa.tipo != "svg":
            self.img_preview.src = str(ruta_img)
            self.img_preview.visible = True
        else:
            self.img_preview.visible = False

    def _posicionar_marco_y_tiradores(self) -> None:
        """Calcula y aplica las coordenadas en píxeles del marco y de los 8 tiradores."""
        if not self.capa_activa or not self.conversion:
            return

        c = self.capa_activa
        conv = self.conversion

        cx, cy = centro_capa(c)
        px_cx, py_cy = conv.plano_a_px(cx, cy)
        w_px = max(1.0, c.ancho * conv.px_por_cm)
        h_px = max(1.0, c.alto * conv.px_por_cm)

        # Contenedor del marco
        self.caja_marco.left = px_cx - w_px / 2.0
        self.caja_marco.top = py_cy - h_px / 2.0
        self.caja_marco.width = w_px
        self.caja_marco.height = h_px
        # En pantalla antihorario es rotación negativa:
        rad_pantalla = -math.radians(c.rotacion)
        self.caja_marco.rotate = ft.Rotate(angle=rad_pantalla)
        self.caja_marco.visible = True

        # Posicionamiento exacto de los tiradores en el plano (ocultos si capa bloqueada)
        bloqueada = bool(c.bloqueada)
        tirs_plano = tiradores(c, incluir_rotacion=True, dist_rot_cm=1.8)
        medio_h = TAM_TIRADOR_PX / 2.0

        for t_id, cont in self.tiradores_controles.items():
            if t_id in tirs_plano and not bloqueada:
                tx_cm, ty_cm = tirs_plano[t_id]
                t_px_x, t_px_y = conv.plano_a_px(tx_cm, ty_cm)
                cont.left = t_px_x - medio_h
                cont.top = t_px_y - medio_h
                cont.visible = True
            else:
                cont.visible = False

        # Tirador de rotación
        if "rot" in tirs_plano and not bloqueada:
            rx_cm, ry_cm = tirs_plano["rot"]
            r_px_x, r_px_y = conv.plano_a_px(rx_cm, ry_cm)
            self.cont_rot.left = r_px_x - TAM_ROT_PX / 2.0
            self.cont_rot.top = r_px_y - TAM_ROT_PX / 2.0
            self.cont_rot.visible = True
        else:
            self.cont_rot.visible = False

    def actualizar_controles_locales(self) -> None:
        """Actualiza atómicamente solo los controles del marco en pantalla."""
        try:
            self.caja_marco.update()
            for cont in self.tiradores_controles.values():
                cont.update()
            self.cont_rot.update()
        except Exception:
            pass

    # ==========================================================================
    # Manejadores de Gestos: Cuerpo del Marco (Mover)
    # ==========================================================================

    def _on_cuerpo_pan_start(self, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._arrastrando = True
        self._tirador_activo = "cuerpo"
        self._inicio_arrastre_ts = time.perf_counter()
        self.telemetria_eventos_arrastre = 0

    def _on_cuerpo_pan_update(self, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if t0 - self._ultimo_evento_ts < THROTTLE_S:
            return
        self._ultimo_evento_ts = t0

        try:
            delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
            if not (delta and hasattr(delta, "x") and hasattr(delta, "y")):
                return

            dx_cm, dy_cm = self.conversion.delta_px_a_plano(delta.x, delta.y)
            self.capa_activa = mover(self.capa_activa, (dx_cm, dy_cm))
            self._posicionar_marco_y_tiradores()
            self.actualizar_controles_locales()

            self._registrar_telemetria(
                "cuerpo", delta.x, delta.y, dx_cm, dy_cm, (time.perf_counter() - t0) * 1000.0
            )
            self.on_cambio_geometria(self.capa_activa, False)
        except Exception as err:
            logger.exception(f"Error en arrastre del cuerpo: {err}")

    def _on_cuerpo_pan_end(self, e) -> None:
        self._finalizar_gesto()

    def _on_cuerpo_pan_cancel(self, e) -> None:
        self._finalizar_gesto()

    def _on_cuerpo_exit(self, e) -> None:
        if self._arrastrando:
            self._finalizar_gesto()

    # ==========================================================================
    # Manejadores de Gestos: 8 Tiradores (Estirar)
    # ==========================================================================

    def _on_tirador_pan_start(self, t_id: str, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._arrastrando = True
        self._tirador_activo = t_id
        self._inicio_arrastre_ts = time.perf_counter()
        self.telemetria_eventos_arrastre = 0

    def _on_tirador_pan_update(self, t_id: str, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if t0 - self._ultimo_evento_ts < THROTTLE_S:
            return
        self._ultimo_evento_ts = t0

        try:
            delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
            if not (delta and hasattr(delta, "x") and hasattr(delta, "y")):
                return

            dx_cm, dy_cm = self.conversion.delta_px_a_plano(delta.x, delta.y)
            self.capa_activa = estirar(
                self.capa_activa,
                tirador=t_id,
                delta_plano=(dx_cm, dy_cm),
                mantener_proporcion=self.mantener_proporcion,
                minimo_cm=1.0,
            )
            self._posicionar_marco_y_tiradores()
            self.actualizar_controles_locales()

            self._registrar_telemetria(
                t_id, delta.x, delta.y, dx_cm, dy_cm, (time.perf_counter() - t0) * 1000.0
            )
            self.on_cambio_geometria(self.capa_activa, False)
        except Exception as err:
            logger.exception(f"Error en estiramiento con tirador {t_id}: {err}")

    def _on_tirador_pan_end(self, t_id: str, e) -> None:
        self._finalizar_gesto()

    def _on_tirador_pan_cancel(self, t_id: str, e) -> None:
        self._finalizar_gesto()

    def _on_tirador_exit(self, t_id: str, e) -> None:
        if self._arrastrando and self._tirador_activo == t_id:
            self._finalizar_gesto()

    # ==========================================================================
    # Manejadores de Gestos: Rotación
    # ==========================================================================

    def _on_rot_pan_start(self, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._arrastrando = True
        self._tirador_activo = "rot"
        self._inicio_arrastre_ts = time.perf_counter()
        self.telemetria_eventos_arrastre = 0

    def _on_rot_pan_update(self, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if t0 - self._ultimo_evento_ts < THROTTLE_S:
            return
        self._ultimo_evento_ts = t0

        try:
            pos = getattr(e, "global_position", None) or getattr(e, "local_position", None)
            if not (pos and hasattr(pos, "x") and hasattr(pos, "y")):
                return

            px_cm, py_cm = self.conversion.px_a_plano(pos.x, pos.y)
            self.capa_activa = rotar(self.capa_activa, (px_cm, py_cm))
            self._posicionar_marco_y_tiradores()
            self.actualizar_controles_locales()

            self.on_cambio_geometria(self.capa_activa, False)
        except Exception as err:
            logger.exception(f"Error en rotación de capa: {err}")

    def _on_rot_pan_end(self, e) -> None:
        self._finalizar_gesto()

    def _on_rot_pan_cancel(self, e) -> None:
        self._finalizar_gesto()

    def _on_rot_exit(self, e) -> None:
        if self._arrastrando and self._tirador_activo == "rot":
            self._finalizar_gesto()

    # ==========================================================================
    # Finalización Segura y Telemetría
    # ==========================================================================

    def _finalizar_gesto(self) -> None:
        """Restaura las banderas de estado y notifica la confirmación de la geometría."""
        if not self._arrastrando:
            return
        tid = self._tirador_activo or "cuerpo"
        dur = time.perf_counter() - self._inicio_arrastre_ts
        logger.info(
            f"Gesto finalizado: tirador={tid}, eventos={self.telemetria_eventos_arrastre}, "
            f"duracion={dur:.3f}s"
        )
        self._arrastrando = False
        self._tirador_activo = None
        if self.capa_activa:
            self.on_cambio_geometria(self.capa_activa, True)

    def _registrar_telemetria(
        self,
        tirador: str,
        dx_px: float,
        dy_px: float,
        dx_cm: float,
        dy_cm: float,
        dt_ms: float,
    ) -> None:
        """Registra telemetría de rendimiento y frecuencia de actualización."""
        self.telemetria_eventos_arrastre += 1
        self.telemetria_latencia_ms = dt_ms
        self._ultimo_evento_desc = f"{tirador}: dx={dx_px:+.1f},dy={dy_px:+.1f}"
        dur = time.perf_counter() - self._inicio_arrastre_ts
        if dur > 0.05:
            self.telemetria_eventos_sec = self.telemetria_eventos_arrastre / dur

        if self.debug_mode and self.capa_activa:
            c = self.capa_activa
            msg = (
                f"[GESTO] tirador={tirador:2s} | "
                f"dx_px={dx_px:+5.1f} dy_px={dy_px:+5.1f} | "
                f"dx_cm={dx_cm:+6.2f} dy_cm={dy_cm:+6.2f} | "
                f"marco: x={c.x:5.1f} y={c.y:5.1f} w={c.ancho:5.1f} h={c.alto:5.1f} rot={c.rotacion:5.1f}° | "
                f"t_proc={dt_ms:4.1f}ms ({self.telemetria_eventos_sec:4.1f} ev/s)"
            )
            logger.info(msg)
