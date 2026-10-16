"""Componente interactivo del marco de edición y 8 tiradores en Flet.

Superpone sobre el visor SVG una capa de controles ligeros (ft.Stack) con:
- Grupo de edición único (ft.Stack) que agrupa imagen fantasma, marco y tiradores
  con coordenadas relativas al grupo: mover la capa actualiza un solo control.
- Posicionamiento absoluto respecto al inicio del gesto (nunca pierde distancia).
- Planificador "el último gana" a <= 60 Hz con volcado inmediato al soltar.
- 8 tiradores táctiles (>= 28 px de zona activa) y tirador de rotación superior.
"""

from dataclasses import replace
import logging
import math
import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import flet as ft

from logic.diseno.gestos_lienzo import (
    Conversion,
    centro_capa,
    estirar,
    mover,
    rotar,
    tiradores,
)
from logic.diseno.lienzo import CapaDiseno, obtener_fragmento_capa
from logic.registro import inicializar_registro

logger = logging.getLogger("globos")

TAM_TIRADOR_PX = 28.0
TAM_ROT_PX = 28.0
INTERVALO_FRAME_S = 1.0 / 60.0
THROTTLE_S = INTERVALO_FRAME_S


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
        self._capa_inicial: Optional[CapaDiseno] = None
        self._puntero_inicial_px: Tuple[float, float] = (0.0, 0.0)
        self._tiene_puntero_global_inicial: bool = False
        self._puntero_virtual_px: Tuple[float, float] = (0.0, 0.0)

        self._capa_pendiente: Optional[CapaDiseno] = None
        self._hay_pendiente: bool = False
        self._ultima_aplicacion_ts: float = 0.0
        self._timer_pendiente: Optional[threading.Timer] = None
        self._lock_pendiente = threading.Lock()

        self._clave_preview_actual: Optional[Tuple] = None
        self._pad_grupo_x: float = 36.0
        self._pad_grupo_y: float = 52.0

        self.telemetria_eventos_arrastre: int = 0
        self.telemetria_aplicaciones: int = 0
        self.telemetria_latencia_ms: float = 0.0
        self.telemetria_eventos_sec: float = 0.0
        self._inicio_arrastre_ts: float = 0.0

        self._crear_controles()

    def _crear_controles(self) -> None:
        """Inicializa el grupo de edición único y sus controles hijos relativos."""
        self._crear_marco_y_cuerpo()
        self._crear_tiradores()

        ids_tiradores = ["tl", "tr", "br", "bl", "t", "b", "r", "l"]
        self.stack = ft.Stack(
            controls=[
                self.caja_marco,
                *[self.tiradores_controles[tid] for tid in ids_tiradores],
                self.cont_rot,
            ],
            visible=False,
            clip_behavior=ft.ClipBehavior.NONE,
        )
        self.grupo_edicion = self.stack

    def _crear_marco_y_cuerpo(self) -> None:
        """Crea el contenedor del marco y su detector de gestos para mover."""
        self.img_preview = ft.Image(
            src="",
            fit=ft.BoxFit.FILL,
            opacity=0.85,
            visible=False,
        )
        self.detector_cuerpo = ft.GestureDetector(
            content=ft.Container(content=self.img_preview),
            drag_interval=16,
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_start=self._on_cuerpo_pan_start,
            on_pan_update=self._on_cuerpo_pan_update,
            on_pan_end=self._on_cuerpo_pan_end,
            on_pan_cancel=self._on_cuerpo_pan_cancel,
        )
        self.caja_marco = ft.Container(
            border=ft.Border.all(1.5, ft.Colors.BLUE_ACCENT),
            bgcolor="#2196F318",
            visible=False,
            content=self.detector_cuerpo,
        )

    def _crear_tiradores(self) -> None:
        """Crea los 8 tiradores de redimensionado (>=28 px) y el tirador de rotación."""
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
        for t_id in ["tl", "tr", "br", "bl", "t", "b", "r", "l"]:
            caja_visual = ft.Container(
                width=10,
                height=10,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1.5, ft.Colors.BLUE_ACCENT),
                border_radius=2,
            )
            caja_hitbox = ft.Container(
                width=TAM_TIRADOR_PX,
                height=TAM_TIRADOR_PX,
                alignment=ft.Alignment.CENTER,
                content=caja_visual,
            )
            det = ft.GestureDetector(
                content=caja_hitbox,
                drag_interval=16,
                mouse_cursor=cursores.get(t_id, ft.MouseCursor.BASIC),
                on_pan_start=lambda e, tid=t_id: self._on_tirador_pan_start(tid, e),
                on_pan_update=lambda e, tid=t_id: self._on_tirador_pan_update(tid, e),
                on_pan_end=lambda e, tid=t_id: self._on_tirador_pan_end(tid, e),
                on_pan_cancel=lambda e, tid=t_id: self._on_tirador_pan_cancel(tid, e),
            )
            self.detectores_tiradores[t_id] = det
            self.tiradores_controles[t_id] = ft.Container(
                width=TAM_TIRADOR_PX,
                height=TAM_TIRADOR_PX,
                content=det,
                visible=False,
            )

        caja_rot_visual = ft.Container(
            width=12,
            height=12,
            shape=ft.BoxShape.CIRCLE,
            bgcolor=ft.Colors.BLUE_ACCENT,
            border=ft.Border.all(1.5, ft.Colors.WHITE),
        )
        caja_rot_hitbox = ft.Container(
            width=TAM_ROT_PX,
            height=TAM_ROT_PX,
            alignment=ft.Alignment.CENTER,
            content=caja_rot_visual,
        )
        self.detector_rot = ft.GestureDetector(
            content=caja_rot_hitbox,
            drag_interval=16,
            mouse_cursor=ft.MouseCursor.PRECISE,
            on_pan_start=self._on_rot_pan_start,
            on_pan_update=self._on_rot_pan_update,
            on_pan_end=self._on_rot_pan_end,
            on_pan_cancel=self._on_rot_pan_cancel,
        )
        self.cont_rot = ft.Container(
            width=TAM_ROT_PX,
            height=TAM_ROT_PX,
            content=self.detector_rot,
            visible=False,
        )

    def mostrar(
        self,
        capa: CapaDiseno,
        conversion: Conversion,
        carpeta_recursos: Optional[Path] = None,
        mantener_proporcion: bool = False,
    ) -> None:
        """Activa y posiciona el marco de edición sobre la capa especificada."""
        self._cancelar_tarea_pendiente()
        self.capa_activa = capa
        self.conversion = conversion
        self.carpeta_recursos = carpeta_recursos
        self.mantener_proporcion = mantener_proporcion
        self.stack.visible = True
        self.grupo_edicion.visible = True

        self._actualizar_previsualizacion_imagen()
        self._posicionar_marco_y_tiradores()
        self._registrar_estado_fantasma("entrar_editar")
        try:
            self.stack.update()
        except Exception:
            pass
        self.actualizar_controles_locales()

    def ocultar(self) -> None:
        """Oculta el marco y desactiva la interacción."""
        self._cancelar_tarea_pendiente()
        self._arrastrando = False
        self._tirador_activo = None
        self._capa_inicial = None
        self._capa_pendiente = None
        self._hay_pendiente = False
        self.capa_activa = None
        self.stack.visible = False
        self.grupo_edicion.visible = False
        self.caja_marco.visible = False
        self.img_preview.visible = False
        for c in self.tiradores_controles.values():
            c.visible = False
        self.cont_rot.visible = False
        try:
            self.stack.update()
        except Exception:
            pass
        self.actualizar_controles_locales()

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
            self.grupo_edicion.visible = True
            self._actualizar_previsualizacion_imagen()
            self._posicionar_marco_y_tiradores()
            self._registrar_estado_fantasma("actualizar_capa")
            self.actualizar_controles_locales()

    def _actualizar_previsualizacion_imagen(self) -> None:
        """Configura la imagen o SVG autónomo fantasma dentro del marco con caché de src."""
        if not self.capa_activa or not self.carpeta_recursos:
            self.img_preview.visible = False
            self._clave_preview_actual = None
            return

        c = self.capa_activa
        ruta_img = self.carpeta_recursos / c.archivo
        if not ruta_img.exists() or not ruta_img.is_file():
            self.img_preview.visible = False
            self._clave_preview_actual = None
            return

        self.img_preview.opacity = max(0.15, min(1.0, float(c.opacidad) * 0.85))
        self.img_preview.visible = True

        clave = (c.id, c.archivo, str(self.carpeta_recursos), c.tipo, bool(c.reflejo_h), bool(c.reflejo_v))
        if self._clave_preview_actual == clave and self.img_preview.src:
            return

        if c.tipo == "svg":
            contenido_frag, vb = obtener_fragmento_capa(c, self.carpeta_recursos, vista_previa=True)
            if not contenido_frag:
                self.img_preview.visible = False
                self._clave_preview_actual = None
                return
            vx, vy, vw, vh = vb if (vb and len(vb) == 4 and vb[2] > 0 and vb[3] > 0) else (0.0, 0.0, 100.0, 100.0)
            cx_vb, cy_vb = vx + vw / 2.0, vy + vh / 2.0
            transforms_vb = []
            if c.reflejo_h:
                transforms_vb.append(f"translate({cx_vb:.4f} {cy_vb:.4f}) scale(-1 1) translate({-cx_vb:.4f} {-cy_vb:.4f})")
            if c.reflejo_v:
                transforms_vb.append(f"translate({cx_vb:.4f} {cy_vb:.4f}) scale(1 -1) translate({-cx_vb:.4f} {-cy_vb:.4f})")
            cuerpo_svg = f'<g transform="{" ".join(transforms_vb)}">\n{contenido_frag}\n</g>' if transforms_vb else contenido_frag
            svg_autonomo = (
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="none">\n{cuerpo_svg}\n</svg>'
            )
            self.img_preview.src = svg_autonomo.encode("utf-8")
        else:
            self.img_preview.src = ruta_img.read_bytes()
        self._clave_preview_actual = clave

    def _posicionar_solo_grupo(self) -> None:
        """Actualiza únicamente left/top del grupo de edición al mover la capa."""
        if not self.capa_activa or not self.conversion:
            return
        c, conv = self.capa_activa, self.conversion
        cx, cy = centro_capa(c)
        px_cx, py_cy = conv.plano_a_px(cx, cy)
        w_px = max(1.0, c.ancho * conv.px_por_cm)
        h_px = max(1.0, c.alto * conv.px_por_cm)
        self.grupo_edicion.left = (px_cx - w_px / 2.0) - self._pad_grupo_x
        self.grupo_edicion.top = (py_cy - h_px / 2.0) - self._pad_grupo_y

    def _posicionar_marco_y_tiradores(self) -> None:
        """Calcula y aplica las coordenadas del grupo y las relativas del marco y 8 tiradores."""
        if not self.capa_activa or not self.conversion:
            return
        c, conv = self.capa_activa, self.conversion
        cx, cy = centro_capa(c)
        px_cx, py_cy = conv.plano_a_px(cx, cy)
        w_px = max(1.0, c.ancho * conv.px_por_cm)
        h_px = max(1.0, c.alto * conv.px_por_cm)

        extra_rot = max(0.0, 0.5 * math.hypot(w_px, h_px) - 0.5 * min(w_px, h_px)) if abs(c.rotacion) > 1e-4 else 0.0
        dist_rot_cm = max(1.8, 28.0 / max(0.1, conv.px_por_cm))
        pad_x = max(36.0, TAM_TIRADOR_PX) + extra_rot
        pad_y = max(52.0, dist_rot_cm * conv.px_por_cm + TAM_ROT_PX) + extra_rot
        self._pad_grupo_x, self._pad_grupo_y = pad_x, pad_y

        ox, oy = (px_cx - w_px / 2.0) - pad_x, (py_cy - h_px / 2.0) - pad_y
        self.grupo_edicion.left = ox
        self.grupo_edicion.top = oy
        self.grupo_edicion.width = w_px + 2.0 * pad_x
        self.grupo_edicion.height = h_px + 2.0 * pad_y
        self.grupo_edicion.visible = True

        self.caja_marco.left = pad_x
        self.caja_marco.top = pad_y
        self.caja_marco.width = w_px
        self.caja_marco.height = h_px
        self.img_preview.width = w_px
        self.img_preview.height = h_px
        self.caja_marco.rotate = ft.Rotate(angle=-math.radians(c.rotacion))
        self.caja_marco.visible = True

        bloqueada = bool(c.bloqueada)
        tirs_plano = tiradores(c, incluir_rotacion=True, dist_rot_cm=dist_rot_cm)
        medio_h = TAM_TIRADOR_PX / 2.0
        for t_id, cont in self.tiradores_controles.items():
            if t_id in tirs_plano and not bloqueada:
                t_px_x, t_px_y = conv.plano_a_px(*tirs_plano[t_id])
                cont.left = (t_px_x - medio_h) - ox
                cont.top = (t_px_y - medio_h) - oy
                cont.visible = True
            else:
                cont.visible = False

        if "rot" in tirs_plano and not bloqueada:
            r_px_x, r_px_y = conv.plano_a_px(*tirs_plano["rot"])
            self.cont_rot.left = (r_px_x - TAM_ROT_PX / 2.0) - ox
            self.cont_rot.top = (r_px_y - TAM_ROT_PX / 2.0) - oy
            self.cont_rot.visible = True
        else:
            self.cont_rot.visible = False

    def _registrar_estado_fantasma(self, evento: str) -> None:
        """Escribe en logs/globos.log (INFO) las métricas de la zona, encuadre, marco y capa fantasma."""
        try:
            inicializar_registro()
            c, conv = self.capa_activa, self.conversion
            v = conv.vista if conv else None
            zona_str = f"({conv.zona_w:.1f}x{conv.zona_h:.1f})" if conv else "None"
            enc_str = f"({v.x:.1f},{v.y:.1f},{v.ancho:.1f},{v.alto:.1f})" if v else "None"
            g, m, f = self.grupo_edicion, self.caja_marco, self.img_preview
            src_val = f.src
            abs_left = (g.left or 0.0) + (m.left or 0.0)
            abs_top = (g.top or 0.0) + (m.top or 0.0)
            logger.info(
                f"[{evento}] zona={zona_str} encuadre={enc_str} | capa={c.nombre if c else 'None'} | "
                f"grupo: left={g.left} top={g.top} | "
                f"marco: left={abs_left} top={abs_top} width={m.width} height={m.height} visible={m.visible} | "
                f"fantasma: left={abs_left} top={abs_top} width={f.width} height={f.height} "
                f"opacity={f.opacity} visible={f.visible} src_tipo={type(src_val).__name__} src_len={len(src_val) if src_val else 0}"
            )
        except Exception:
            pass

    def actualizar_solo_grupo(self) -> None:
        """Actualiza un único control (el grupo de edición) cuando se mueve la capa."""
        try:
            self.grupo_edicion.update()
        except Exception:
            pass

    def actualizar_controles_locales(self) -> None:
        """Actualiza el grupo de edición tras estirar, rotar o mostrar."""
        try:
            self.grupo_edicion.update()
        except Exception:
            pass

    def _iniciar_gesto(self, tirador: str, e) -> None:
        """Captura la geometría inicial de la capa y la posición inicial del puntero."""
        self._cancelar_tarea_pendiente()
        self._arrastrando = True
        self._tirador_activo = tirador
        self._capa_inicial = replace(self.capa_activa) if self.capa_activa else None
        self._capa_pendiente = None
        self._hay_pendiente = False
        self._inicio_arrastre_ts = time.perf_counter()
        self._ultima_aplicacion_ts = 0.0
        self.telemetria_eventos_arrastre = 0
        self.telemetria_aplicaciones = 0

        pos = getattr(e, "global_position", None) if e is not None else None
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            self._puntero_inicial_px = (float(pos.x), float(pos.y))
            self._tiene_puntero_global_inicial = True
        else:
            self._puntero_inicial_px = (0.0, 0.0)
            self._tiene_puntero_global_inicial = False
        self._puntero_virtual_px = self._puntero_inicial_px

    def _obtener_desplazamiento_desde_inicio_px(self, e) -> Optional[Tuple[float, float]]:
        """Calcula (puntero_ahora - puntero_al_empezar) en píxeles usando posición absoluta."""
        pos = getattr(e, "global_position", None)
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            px_ahora, py_ahora = float(pos.x), float(pos.y)
            if not self._tiene_puntero_global_inicial:
                delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
                if delta is not None and hasattr(delta, "x") and hasattr(delta, "y"):
                    self._puntero_inicial_px = (px_ahora - float(delta.x), py_ahora - float(delta.y))
                else:
                    self._puntero_inicial_px = (px_ahora, py_ahora)
                self._tiene_puntero_global_inicial = True
            return (px_ahora - self._puntero_inicial_px[0], py_ahora - self._puntero_inicial_px[1])

        delta = getattr(e, "local_delta", None) or getattr(e, "global_delta", None)
        if delta is not None and hasattr(delta, "x") and hasattr(delta, "y"):
            self._puntero_virtual_px = (
                self._puntero_virtual_px[0] + float(delta.x),
                self._puntero_virtual_px[1] + float(delta.y),
            )
            return (
                self._puntero_virtual_px[0] - self._puntero_inicial_px[0],
                self._puntero_virtual_px[1] - self._puntero_inicial_px[1],
            )
        return None

    def _programar_o_aplicar_pendiente(self, ahora: float) -> None:
        """Aplica inmediatamente si transcurrió >= 1/60s o deja programado el último estado."""
        with self._lock_pendiente:
            transcurrido = ahora - self._ultima_aplicacion_ts
            if transcurrido >= INTERVALO_FRAME_S:
                if self._timer_pendiente is not None:
                    self._timer_pendiente.cancel()
                    self._timer_pendiente = None
                self._aplicar_pendiente_sin_lock(ahora)
            elif self._timer_pendiente is None:
                restante = max(0.001, INTERVALO_FRAME_S - transcurrido)
                t = threading.Timer(restante, self._tick_timer_pendiente)
                t.daemon = True
                self._timer_pendiente = t
                t.start()

    def _tick_timer_pendiente(self) -> None:
        """Callback del temporizador de cola: aplica la última posición guardada."""
        with self._lock_pendiente:
            self._timer_pendiente = None
            if not self._arrastrando or not self._hay_pendiente:
                return
            self._aplicar_pendiente_sin_lock(time.perf_counter())

    def _aplicar_pendiente_sin_lock(self, ahora: float) -> None:
        """Envía al árbol visual la última posición pendiente (1 solo control al mover)."""
        if not self._hay_pendiente or self._capa_pendiente is None:
            return
        self.capa_activa = self._capa_pendiente
        self._hay_pendiente = False
        self._ultima_aplicacion_ts = ahora
        self.telemetria_aplicaciones += 1

        if self._tirador_activo == "cuerpo":
            self._posicionar_solo_grupo()
            self.actualizar_solo_grupo()
        else:
            self._posicionar_marco_y_tiradores()
            self.actualizar_controles_locales()

    def _cancelar_tarea_pendiente(self) -> None:
        """Detiene el temporizador pendiente si existe."""
        with self._lock_pendiente:
            if self._timer_pendiente is not None:
                self._timer_pendiente.cancel()
                self._timer_pendiente = None

    def _on_cuerpo_pan_start(self, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._iniciar_gesto("cuerpo", e)

    def _on_cuerpo_pan_update(self, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if self._capa_inicial is None:
            self._capa_inicial = replace(self.capa_activa)
        try:
            desp_px = self._obtener_desplazamiento_desde_inicio_px(e)
            if desp_px is None:
                return
            dx_px, dy_px = desp_px
            dx_cm, dy_cm = self.conversion.delta_px_a_plano(dx_px, dy_px)
            nueva_capa = mover(self._capa_inicial, (dx_cm, dy_cm))
            self.capa_activa = nueva_capa
            self._capa_pendiente = nueva_capa
            self._hay_pendiente = True
            self.on_cambio_geometria(nueva_capa, False)
            self._programar_o_aplicar_pendiente(t0)
            self._registrar_telemetria("cuerpo", dx_px, dy_px, dx_cm, dy_cm, (time.perf_counter() - t0) * 1000.0)
        except Exception as err:
            logger.exception(f"Error en arrastre del cuerpo: {err}")

    def _on_cuerpo_pan_end(self, e) -> None:
        self._finalizar_gesto(e)

    def _on_cuerpo_pan_cancel(self, e) -> None:
        self._finalizar_gesto(e)

    def _on_cuerpo_exit(self, e) -> None:
        if self._arrastrando:
            self._finalizar_gesto(e)

    def _on_tirador_pan_start(self, t_id: str, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._iniciar_gesto(t_id, e)

    def _on_tirador_pan_update(self, t_id: str, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if self._capa_inicial is None:
            self._capa_inicial = replace(self.capa_activa)
        try:
            desp_px = self._obtener_desplazamiento_desde_inicio_px(e)
            if desp_px is None:
                return
            dx_px, dy_px = desp_px
            dx_cm, dy_cm = self.conversion.delta_px_a_plano(dx_px, dy_px)
            nueva_capa = estirar(
                self._capa_inicial,
                tirador=t_id,
                delta_plano=(dx_cm, dy_cm),
                mantener_proporcion=self.mantener_proporcion,
                minimo_cm=1.0,
            )
            self.capa_activa = nueva_capa
            self._capa_pendiente = nueva_capa
            self._hay_pendiente = True
            self.on_cambio_geometria(nueva_capa, False)
            self._programar_o_aplicar_pendiente(t0)
            self._registrar_telemetria(t_id, dx_px, dy_px, dx_cm, dy_cm, (time.perf_counter() - t0) * 1000.0)
        except Exception as err:
            logger.exception(f"Error en estiramiento con tirador {t_id}: {err}")

    def _on_tirador_pan_end(self, t_id: str, e) -> None:
        self._finalizar_gesto(e)

    def _on_tirador_pan_cancel(self, t_id: str, e) -> None:
        self._finalizar_gesto(e)

    def _on_tirador_exit(self, t_id: str, e) -> None:
        if self._arrastrando and self._tirador_activo == t_id:
            self._finalizar_gesto(e)

    def _on_rot_pan_start(self, e) -> None:
        if not self.capa_activa or self.capa_activa.bloqueada:
            return
        self._iniciar_gesto("rot", e)

    def _on_rot_pan_update(self, e: ft.DragUpdateEvent) -> None:
        t0 = time.perf_counter()
        if not self._arrastrando or not self.capa_activa or not self.conversion:
            return
        if self._capa_inicial is None:
            self._capa_inicial = replace(self.capa_activa)
        try:
            pos = getattr(e, "global_position", None) or getattr(e, "local_position", None)
            if not (pos and hasattr(pos, "x") and hasattr(pos, "y")):
                return
            if getattr(e, "global_position", None) is not None and self._tiene_puntero_global_inicial:
                dist_rot_cm = max(1.8, 28.0 / max(0.1, self.conversion.px_por_cm))
                tirs_ini = tiradores(self._capa_inicial, incluir_rotacion=True, dist_rot_cm=dist_rot_cm)
                rx0_px, ry0_px = self.conversion.plano_a_px(*tirs_ini["rot"])
                px_zona = rx0_px + (float(pos.x) - self._puntero_inicial_px[0])
                py_zona = ry0_px + (float(pos.y) - self._puntero_inicial_px[1])
                px_cm, py_cm = self.conversion.px_a_plano(px_zona, py_zona)
            else:
                px_cm, py_cm = self.conversion.px_a_plano(float(pos.x), float(pos.y))

            nueva_capa = rotar(self._capa_inicial, (px_cm, py_cm))
            self.capa_activa = nueva_capa
            self._capa_pendiente = nueva_capa
            self._hay_pendiente = True
            self.on_cambio_geometria(nueva_capa, False)
            self._programar_o_aplicar_pendiente(t0)
        except Exception as err:
            logger.exception(f"Error en rotación de capa: {err}")

    def _on_rot_pan_end(self, e) -> None:
        self._finalizar_gesto(e)

    def _on_rot_pan_cancel(self, e) -> None:
        self._finalizar_gesto(e)

    def _on_rot_exit(self, e) -> None:
        if self._arrastrando and self._tirador_activo == "rot":
            self._finalizar_gesto(e)

    def _finalizar_gesto(self, e=None) -> None:
        """Detiene la tarea programada, aplica la última posición pendiente y confirma la geometría."""
        self._cancelar_tarea_pendiente()
        if not self._arrastrando:
            return
        pos_fin = getattr(e, "global_position", None) if e is not None else None
        if (
            pos_fin is not None
            and hasattr(pos_fin, "x")
            and hasattr(pos_fin, "y")
            and self._tiene_puntero_global_inicial
            and self._capa_inicial is not None
            and self.conversion is not None
        ):
            try:
                dx_px = float(pos_fin.x) - self._puntero_inicial_px[0]
                dy_px = float(pos_fin.y) - self._puntero_inicial_px[1]
                dx_cm, dy_cm = self.conversion.delta_px_a_plano(dx_px, dy_px)
                nueva_fin = None
                if self._tirador_activo == "cuerpo":
                    nueva_fin = mover(self._capa_inicial, (dx_cm, dy_cm))
                elif self._tirador_activo in self.tiradores_controles:
                    nueva_fin = estirar(
                        self._capa_inicial,
                        tirador=self._tirador_activo,
                        delta_plano=(dx_cm, dy_cm),
                        mantener_proporcion=self.mantener_proporcion,
                        minimo_cm=1.0,
                    )
                if nueva_fin is not None and nueva_fin != self.capa_activa:
                    self.capa_activa = nueva_fin
                    self._capa_pendiente = nueva_fin
                    self._hay_pendiente = True
            except Exception:
                pass
        with self._lock_pendiente:
            if self._hay_pendiente:
                self._aplicar_pendiente_sin_lock(time.perf_counter())
        tid = self._tirador_activo or "cuerpo"
        dur = time.perf_counter() - self._inicio_arrastre_ts
        logger.info(
            f"Gesto finalizado: tirador={tid}, eventos={self.telemetria_eventos_arrastre}, "
            f"aplicaciones={self.telemetria_aplicaciones}, duracion={dur:.3f}s"
        )
        self._arrastrando = False
        self._tirador_activo = None
        self._capa_inicial = None
        if self.capa_activa:
            self.on_cambio_geometria(self.capa_activa, True)

    def _registrar_telemetria(
        self, tirador: str, dx_px: float, dy_px: float, dx_cm: float, dy_cm: float, dt_ms: float
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
            logger.info(
                f"[GESTO] tirador={tirador:2s} | dx_px={dx_px:+5.1f} dy_px={dy_px:+5.1f} | "
                f"dx_cm={dx_cm:+6.2f} dy_cm={dy_cm:+6.2f} | "
                f"marco: x={c.x:5.1f} y={c.y:5.1f} w={c.ancho:5.1f} h={c.alto:5.1f} rot={c.rotacion:5.1f}° | "
                f"t_proc={dt_ms:4.1f}ms ({self.telemetria_eventos_sec:4.1f} ev/s)"
            )
