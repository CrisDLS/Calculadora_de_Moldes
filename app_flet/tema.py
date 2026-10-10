# app_flet/tema.py
import flet as ft

COLOR_FONDO = ft.Colors.BLUE_GREY_900
COLOR_FONDO_SECUNDARIO = ft.Colors.BLUE_GREY_800
COLOR_ACENTO = ft.Colors.PINK_400
COLOR_TEXTO = ft.Colors.WHITE
COLOR_TEXTO_SECUNDARIO = ft.Colors.BLUE_GREY_200

# Colores semánticos para viabilidad y avisos
COLOR_INFO = ft.Colors.BLUE_400
COLOR_OK = ft.Colors.GREEN_400
COLOR_AVISO = ft.Colors.AMBER_500
COLOR_ERROR = ft.Colors.RED_400

tema_oscuro = ft.Theme(
    color_scheme_seed=COLOR_ACENTO,
    color_scheme=ft.ColorScheme(
        primary=COLOR_ACENTO,
        surface=COLOR_FONDO,
        surface_container=COLOR_FONDO_SECUNDARIO,
        on_surface=COLOR_TEXTO,
        on_primary=COLOR_TEXTO,
    ),
    visual_density=ft.VisualDensity.COMFORTABLE,
)
