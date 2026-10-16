import os
from typing import Callable, List, Optional
import flet as ft
from logic.diseno.paleta import (
    ColorPapel,
    guardar_color_usuario,
    importar_csv,
    exportar_csv,
)


async def dialogo_agregar_color(
    page: Optional[ft.Page],
    on_color_guardado: Callable[[ColorPapel], None],
    on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
) -> None:
    """Abre un diálogo modal para registrar un nuevo color de papel china."""
    if not page:
        return
    txt_nom = ft.TextField(label="Nombre del color", dense=True)
    txt_marca = ft.TextField(label="Marca (opcional)", dense=True)
    txt_codigo = ft.TextField(label="Código de fábrica (opcional)", dense=True)
    txt_hex = ft.TextField(label="HEX (ej. #e91e63)", dense=True)
    txt_notas = ft.TextField(label="Notas", dense=True)
    chk_calib = ft.Checkbox(label="Calibrado (exacto)", value=False)

    def guardar(e):
        nom = txt_nom.value.strip()
        hex_val = txt_hex.value.strip()
        if not nom or not hex_val:
            if on_mostrar_snackbar:
                on_mostrar_snackbar("Nombre y código HEX son obligatorios.")
            return
        if not hex_val.startswith("#"):
            hex_val = "#" + hex_val
        try:
            col = ColorPapel(
                id=nom.lower().replace(" ", "_"),
                nombre=nom,
                hex=hex_val,
                aproximado=not chk_calib.value,
                marca=txt_marca.value.strip(),
                codigo=txt_codigo.value.strip(),
                notas=txt_notas.value.strip(),
            )
            guardar_color_usuario(col)
            dialog.open = False
            page.update()
            on_color_guardado(col)
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Color '{nom}' agregado con éxito.")
        except Exception as err:
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Error al guardar: {err}")

    dialog = ft.AlertDialog(
        title=ft.Text("Nuevo color de papel"),
        content=ft.Column([txt_nom, txt_marca, txt_codigo, txt_hex, txt_notas, chk_calib], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda ev: setattr(dialog, "open", False) or page.update()),
            ft.FilledButton("Guardar", on_click=guardar),
        ],
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()


async def importar_colores_dialogo(
    file_picker: ft.FilePicker,
    on_catalogo_actualizado: Callable[[], None],
    on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
) -> None:
    """Abre el explorador de archivos para importar colores desde un CSV."""
    archivos = await file_picker.pick_files(
        dialog_title="Importar catálogo de colores CSV",
        file_type=ft.FilePickerFileType.CUSTOM,
        allowed_extensions=["csv"],
        allow_multiple=False,
    )
    if archivos and len(archivos) > 0 and archivos[0].path:
        ruta = archivos[0].path
        try:
            importados, errores = importar_csv(ruta)
            on_catalogo_actualizado()
            msg = f"{len(importados)} colores importados."
            if errores:
                msg += f" ({len(errores)} filas omitidas: {errores[0]})"
            if on_mostrar_snackbar:
                on_mostrar_snackbar(msg)
        except Exception as err:
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Error al importar CSV: {err}")


async def exportar_colores_dialogo(
    file_picker: ft.FilePicker,
    catalogo: List[ColorPapel],
    on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
) -> None:
    """Abre el explorador de archivos para exportar el catálogo a CSV."""
    ruta = await file_picker.save_file(
        dialog_title="Exportar catálogo de colores CSV",
        file_name="catalogo_colores_papel.csv",
        file_type=ft.FilePickerFileType.CUSTOM,
        allowed_extensions=["csv"],
    )
    if ruta:
        try:
            exportar_csv(ruta, catalogo)
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Catálogo exportado: {os.path.basename(ruta)}")
        except Exception as err:
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Error al exportar CSV: {err}")
