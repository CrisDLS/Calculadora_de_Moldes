# app_flet/main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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


