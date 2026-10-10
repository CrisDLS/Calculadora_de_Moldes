# app_flet/main.py
import flet as ft
from app_flet.vistas.trompo import VistaTrompo
from app_flet import tema

def main(page: ft.Page):
    page.title = "Calculadora de moldes"
    page.theme = tema.tema_oscuro
    page.theme_mode = ft.ThemeMode.DARK
    page.window_min_width = 800
    page.window_min_height = 600
    page.padding = 0
    
    vista = VistaTrompo()
    page.add(vista)

if __name__ == "__main__":
    ft.app(target=main)
