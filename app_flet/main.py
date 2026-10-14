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
    page.window_min_width = 800
    page.window_min_height = 600
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