#!/usr/bin/env python3
"""Demo interactiva independiente para probar el marco de edición y 8 tiradores.

Permite probar la sensación del marco de manipulación directa táctil en Flet
sin tener que levantar toda la aplicación:
- Abanico base de cono superior (950/30/2/1, grupo de 5 gajos).
- Capa de ejemplo vectorial (mosaico_geometrico.svg).
- Modos excluyentes: 'Navegar' (pan/zoom) vs 'Editar' (marco y 8 tiradores a 60 fps).
- Telemetría en tiempo real del último gesto.
"""

import math
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import flet as ft

from app_flet.vistas.componentes.marco_edicion import MarcoEdicion
from app_flet.vistas.componentes.visor_svg import VisorSvg
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.gestos_lienzo import Conversion
from logic.diseno.lienzo import CapaDiseno, Diseno, cargar_recurso_seguro
from logic.exportacion.svg_abanico import (
    calcular_parametros_proyeccion_abanico,
    svg_abanico,
)
from logic.models import BalloonInput


def main(page: ft.Page) -> None:
    page.title = "Demo: Marco de Edición y Tiradores"
    page.window.width = 900
    page.window.height = 700
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT

    # 1. Geometría base del globo
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )
    calc = TrompoEstrellaCalculator()
    resultado = calc.calcular(entrada)
    esquema = EsquemaDiseno(modo="repeticion", tam_grupo=5)

    # 2. Carpeta de recursos temporal y capa de ejemplo
    rec_dir = RAIZ / "guardados" / "_demo_recursos"
    rec_dir.mkdir(parents=True, exist_ok=True)
    ej_svg = RAIZ / "docs" / "ejemplos" / "disenos" / "mosaico_geometrico.svg"
    dest_svg = rec_dir / "mosaico_geometrico.svg"
    if ej_svg.exists() and not dest_svg.exists():
        shutil.copy(ej_svg, dest_svg)

    rec_info = cargar_recurso_seguro(dest_svg)
    capa = CapaDiseno(
        id="capa-demo",
        nombre="Mosaico Geométrico",
        archivo="mosaico_geometrico.svg",
        tipo="svg",
        x=0.0,
        y=150.0,
        ancho=40.0,
        alto=40.0,
        ancho_natural=rec_info.ancho_px,
        alto_natural=rec_info.alto_px,
        rotacion=0.0,
        opacidad=1.0,
    )
    diseno = Diseno(capas=[capa])

    # 3. Componentes visuales
    visor = VisorSvg(
        papel_blanco=True,
        drag_interval=16,
        margen_ajuste=0.04,
    )

    lbl_debug = ft.Text(
        "Modo: Navegar · Arrastra con ratón para mover lienzo, rueda para zoom.",
        size=11,
        color=ft.Colors.BLUE_GREY_800,
        weight=ft.FontWeight.W_500,
    )

    def on_cambio_geometria(capa_actualizada: CapaDiseno, finalizado: bool) -> None:
        nonlocal capa
        capa = capa_actualizada
        c = capa
        ult = getattr(marco, "_ultimo_evento_desc", "cuerpo")
        lat = marco.telemetria_latencia_ms
        ev_s = marco.telemetria_eventos_sec
        lbl_debug.value = (
            f"[GESTO {ult}] x={c.x:.1f} y={c.y:.1f} w={c.ancho:.1f} h={c.alto:.1f} "
            f"rot={c.rotacion:.1f}° | lat={lat:.1f}ms ({ev_s:.0f} ev/s) | "
            f"{'CONFIRMADO (soltado)' if finalizado else 'en curso...'}"
        )
        try:
            lbl_debug.update()
        except Exception:
            pass

    marco = MarcoEdicion(
        on_cambio_geometria=on_cambio_geometria,
        debug_mode=True,
    )

    stack_visor = ft.Stack(
        controls=[
            visor.detector_gestos,
            marco.stack,
        ],
        expand=True,
    )
    visor.container_viewer_svg.content = stack_visor

    def obtener_conversion() -> Conversion:
        geom = calcular_parametros_proyeccion_abanico(
            resultado=resultado,
            entrada=entrada,
            seccion="superior",
            esquema=esquema,
            hoja="carta",
            escala="auto",
        )
        w_z = visor.ancho_zona
        h_z = visor.alto_zona
        return Conversion(
            vista=visor.vista_svg,
            zona_px=(w_z, h_z),
            cx_page=geom["cx_page"],
            cy_page=geom["cy_page"],
            y_mid_cm=geom["y_mid_cm"],
            factor_escala=geom["factor"],
            y_arriba=True,
        )

    def generar_svg(fantasma: bool) -> str:
        return svg_abanico(
            resultado=resultado,
            entrada=entrada,
            seccion="superior",
            esquema=esquema,
            hoja="carta",
            escala="auto",
            diseno=diseno,
            carpeta_recursos=rec_dir,
            modo_fantasma=fantasma,
        )

    def actualizar_visor(fantasma: bool) -> None:
        raw_svg = generar_svg(fantasma)
        visor.cargar_svg(raw_svg, reset_vista=False)

    def al_cambiar_tamano(e: ft.ContainerResizeEvent) -> None:
        visor._on_container_size_change(e)
        if marco.stack.visible and capa:
            conv = obtener_conversion()
            marco.actualizar(capa, conv, rec_dir)

    visor.container_viewer_svg.on_size_change = al_cambiar_tamano

    def al_cambiar_modo(e) -> None:
        modo = sel_modo.selected[0] if sel_modo.selected else "navegar"
        if modo == "editar":
            visor.gestos_habilitados = False
            actualizar_visor(fantasma=True)
            conv = obtener_conversion()
            marco.mostrar(capa, conv, rec_dir, mantener_proporcion=chk_prop.value)
            lbl_debug.value = "Modo: EDITAR · Arrastra el marco para mover, esquinas/lados para estirar."
        else:
            visor.gestos_habilitados = True
            marco.ocultar()
            actualizar_visor(fantasma=False)
            lbl_debug.value = "Modo: NAVEGAR · Arrastra para desplazar el lienzo, rueda para zoom."
        lbl_debug.update()

    sel_modo = ft.SegmentedButton(
        segments=[
            ft.Segment(value="navegar", label=ft.Text("Navegar"), icon=ft.Icons.PAN_TOOL),
            ft.Segment(value="editar", label=ft.Text("Editar capa"), icon=ft.Icons.CROP),
        ],
        selected=["navegar"],
        on_change=al_cambiar_modo,
    )

    def al_cambiar_prop(e) -> None:
        marco.mantener_proporcion = chk_prop.value

    chk_prop = ft.Checkbox(
        label="Mantener proporción",
        value=False,
        on_change=al_cambiar_prop,
    )

    btn_reset = ft.FilledTonalButton(
        "Ajustar vista",
        icon=ft.Icons.FIT_SCREEN,
        on_click=lambda _: visor.ajustar_vista(),
    )

    barra_controles = ft.Row(
        controls=[
            ft.Text("Herramienta:", weight=ft.FontWeight.BOLD),
            sel_modo,
            chk_prop,
            btn_reset,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )

    page.add(
        barra_controles,
        ft.Container(
            content=visor.container_viewer_svg,
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
        ),
        lbl_debug,
    )

    # Carga inicial
    actualizar_visor(fantasma=False)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
