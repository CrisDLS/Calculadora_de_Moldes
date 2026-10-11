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
    fila_alternada="#f1f2f6",
    color_ok="#10ac84",
    color_aviso="#e67e22",
    color_error="#d63031",
    color_info="#0984e3",
)

def obtener_paleta(modo: ft.ThemeMode) -> PaletaTema:
    if modo == ft.ThemeMode.LIGHT:
        return PALETA_CLARA
    return PALETA_OSCURA

# Temas Material 3 para Flet
tema_oscuro = ft.Theme(
    color_scheme_seed=PALETA_OSCURA.acento,
    scaffold_bgcolor=PALETA_OSCURA.fondo,
    use_material3=True,
)

tema_claro = ft.Theme(
    color_scheme_seed=PALETA_CLARA.acento,
    scaffold_bgcolor=PALETA_CLARA.fondo,
    use_material3=True,
)
