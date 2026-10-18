# app_flet/main.py
import asyncio
import flet as ft
from app_flet.vistas.trompo import VistaTrompo
from app_flet import tema
from logic.registro import inicializar_registro, registrar_excepcion_asyncio, MonitorLatido, logger

def main(page: ft.Page):
    inicializar_registro()
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(registrar_excepcion_asyncio)
    except RuntimeError:
        pass

    page.on_error = lambda e: logger.error(f"Error en Flet Page: {e.data if hasattr(e, 'data') else e}")

    page.title = "Calculadora de moldes"
    page.theme = tema.tema_oscuro
    page.theme_mode = ft.ThemeMode.DARK

    # Configuración de tamaño de ventana con API Flet 1.0.4 (ft.Window)
    if hasattr(page, "window") and page.window is not None:
        page.window.min_width = 1100
        page.window.min_height = 700
        page.window.width = 1200
        page.window.height = 760

    page.window_min_width = 1100
    page.window_min_height = 700
    page.window_width = 1200
    page.window_height = 760
    page.padding = 0
    
    vista = VistaTrompo()
    page.add(vista)

    # Iniciar monitor de latido conectado al estado de la vista
    latido = MonitorLatido(
        intervalo_s=1.0,
        umbral_alerta_s=2.0,
        obtener_estado_fn=getattr(vista, "obtener_estado_telemetria", None),
        obtener_pagina_fn=lambda: page,
    )
    latido.iniciar()