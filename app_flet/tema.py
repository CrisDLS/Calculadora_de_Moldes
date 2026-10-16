# app_flet/tema.py
from dataclasses import dataclass
import flet as ft
from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO

@dataclass(frozen=True)
class PaletaTema:
    fondo: str
    panel: str
    texto: str
    texto_secundario: str
    borde: str
    acento: str
    fila_alternada: str
    color_ok: str
    color_aviso: str
    color_error: str
    color_info: str

PALETA_OSCURA = PaletaTema(
    fondo=PANTALLA_OSCURO.fondo_referencia,     # "#1e1e24"
    panel="#282a36",
    texto="#f1f2f6",
    texto_secundario="#a4b0be",
    borde="#3e4153",
    acento="#f48fb1",
    fila_alternada="#252731",
    color_ok="#2ed573",
    color_aviso="#ffa502",
    color_error="#ff4757",
    color_info="#70a1ff",
)

PALETA_CLARA = PaletaTema(
    fondo=PANTALLA_CLARO.fondo_referencia,       # "#f8f9fa"
    panel="#ffffff",
    texto="#2d3436",
    texto_secundario="#636e72",
    borde="#dfe6e9",
    acento="#e84393",
    fila_alternada="#edf2f7",
    color_ok="#10ac84",
    color_aviso="#e67e22",
    color_error="#d63031",
    color_info="#0984e3",
)

def obtener_paleta(modo: ft.ThemeMode) -> PaletaTema:
    if modo == ft.ThemeMode.LIGHT:
        return PALETA_CLARA
    return PALETA_OSCURA

# Temas Material 3 para Flet con ColorScheme explícito
tema_oscuro = ft.Theme(
    color_scheme=ft.ColorScheme(
        surface=PALETA_OSCURA.fondo,
        on_surface=PALETA_OSCURA.texto,
        surface_container=PALETA_OSCURA.panel,
        surface_container_highest=PALETA_OSCURA.panel,
        outline=PALETA_OSCURA.borde,
        primary=PALETA_OSCURA.acento,
        on_primary=PALETA_OSCURA.fondo,
        secondary=PALETA_OSCURA.texto_secundario,
        on_surface_variant=PALETA_OSCURA.texto_secundario,
        error=PALETA_OSCURA.color_error,
    ),
    scaffold_bgcolor=PALETA_OSCURA.fondo,
    card_bgcolor=PALETA_OSCURA.panel,
    divider_color=PALETA_OSCURA.borde,
    use_material3=True,
)

tema_claro = ft.Theme(
    color_scheme=ft.ColorScheme(
        surface=PALETA_CLARA.fondo,
        on_surface=PALETA_CLARA.texto,
        surface_container=PALETA_CLARA.panel,
        surface_container_highest=PALETA_CLARA.panel,
        outline=PALETA_CLARA.borde,
        primary=PALETA_CLARA.acento,
        on_primary="#ffffff",
        secondary=PALETA_CLARA.texto_secundario,
        on_surface_variant=PALETA_CLARA.texto_secundario,
        error=PALETA_CLARA.color_error,
    ),
    scaffold_bgcolor=PALETA_CLARA.fondo,
    card_bgcolor=PALETA_CLARA.panel,
    divider_color=PALETA_CLARA.borde,
    use_material3=True,
)
