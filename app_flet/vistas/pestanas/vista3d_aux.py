"""Ayudantes y constructores auxiliares para la pestaña Vista 3D."""

import asyncio
import os
from typing import Callable, List, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from logic.diseno.paleta import ColorPapel, color_por_id
from logic.diseno.pintura import Cara, EsquemaPintura, VariantePico, color_de_cara


def actualizar_vista_previa_2d(
    fila_previa_sup: ft.Row,
    col_previa_picos: ft.Column,
    fila_previa_inf: ft.Row,
    p: EsquemaPintura,
    gajos: int,
    hileras: int,
    catalogo_papel: List[ColorPapel],
) -> None:
    """Actualiza los bloques de color 2D de cono superior, picos y cono inferior."""
    N = int(gajos or 30)
    h = int(hileras or 2)

    fila_previa_sup.controls.clear()
    fila_previa_inf.controls.clear()
    col_previa_picos.controls.clear()

    for k in range(N):
        cara_s = Cara([], "superior", k, None, None, [0, 0, 1], [])
        col_id_s = color_de_cara(p, cara_s, None, N)
        col_hex_s = color_por_id(col_id_s, catalogo_papel).hex

        fila_previa_sup.controls.append(
            ft.Container(
                width=22,
                height=22,
                bgcolor=col_hex_s,
                border_radius=3,
                tooltip=f"Gajo {k+1}: {col_id_s}",
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            )
        )

        cara_i = Cara([], "inferior", k, None, None, [0, 0, -1], [])
        col_id_i = color_de_cara(p, cara_i, None, N)
        col_hex_i = color_por_id(col_id_i, catalogo_papel).hex

        fila_previa_inf.controls.append(
            ft.Container(
                width=22,
                height=22,
                bgcolor=col_hex_i,
                border_radius=3,
                tooltip=f"Gajo {k+1}: {col_id_i}",
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            )
        )

    for j in range(h):
        fila_p = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)
        for k in range(N):
            cara_p = Cara([], "pico", k, j, 0, [1, 0, 0], [])
            col_id_p = color_de_cara(p, cara_p, None, N)
            col_hex_p = color_por_id(col_id_p, catalogo_papel).hex
            fila_p.controls.append(
                ft.Container(
                    width=22,
                    height=22,
                    bgcolor=col_hex_p,
                    border_radius=3,
                    tooltip=f"H{j+1} G{k+1}: {col_id_p}",
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                )
            )
        col_previa_picos.controls.append(fila_p)


def construir_fila_color(
    cid: str,
    opciones: List[ft.DropdownOption],
    catalogo_papel: List[ColorPapel],
    on_change: Callable,
    on_del: Callable,
    permitir_del: bool,
) -> ft.Row:
    """Construye una fila con muestra de color, selector desplegable y botón de eliminar."""
    c_obj = color_por_id(cid, catalogo_papel)
    val_dd = cid if any(o.key == cid for o in opciones) else (opciones[0].key if opciones else cid)
    btn_del = (
        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Quitar color", on_click=on_del)
        if permitir_del
        else ft.Container()
    )
    return ft.Row(
        controls=[
            ft.Container(
                width=22,
                height=22,
                bgcolor=c_obj.hex,
                border_radius=4,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
            ),
            ft.Dropdown(
                options=opciones,
                value=val_dd,
                dense=True,
                width=220,
                on_select=on_change,
            ),
            btn_del,
        ],
        spacing=8,
    )


def construir_item_cara(
    label: str,
    val: str,
    c_idx: int,
    opciones: List[ft.DropdownOption],
    catalogo_papel: List[ColorPapel],
    on_select_color: Callable[[int, str], None],
    w: int = 180,
) -> ft.Row:
    """Construye un control para una cara de pirámide con muestra y dropdown."""
    c_obj = color_por_id(val, catalogo_papel)
    return ft.Row(
        [
            ft.Container(
                width=20,
                height=20,
                bgcolor=c_obj.hex,
                border_radius=4,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
            ),
            ft.Dropdown(
                label=label,
                options=opciones,
                value=val,
                dense=True,
                width=w,
                on_select=lambda e, idx=c_idx: on_select_color(idx, e.control.value),
            ),
        ],
        spacing=6,
    )


async def exportar_visor_3d_archivo(
    controlador,
    file_picker,
    on_mostrar_snackbar: Optional[Callable[[str], None]],
) -> None:
    """Abre diálogo para exportar el archivo HTML del visor 3D."""
    if not (controlador.resultado and controlador.entrada_actual):
        if on_mostrar_snackbar:
            on_mostrar_snackbar("Calcula el modelo antes de exportar el visor 3D")
        return
    nombre_def = f"{controlador.nombre_proyecto}_visor3d.html"
    ruta = await file_picker.save_file(
        dialog_title="Exportar visor 3D autocontenido",
        file_name=nombre_def,
        file_type=ft.FilePickerFileType.CUSTOM,
        allowed_extensions=["html"],
    )
    if ruta:
        try:
            controlador.exportar_visor_3d(ruta)
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Visor 3D exportado: {os.path.basename(ruta)}")
        except Exception as err:
            if on_mostrar_snackbar:
                on_mostrar_snackbar(f"Error al exportar visor 3D: {err}")


def copiar_lista_compra_portapapeles(
    vm: ViewModelTrompo,
    servicio_clipboard,
    pagina: Optional[ft.Page],
    on_mostrar_snackbar: Optional[Callable[[str], None]],
) -> None:
    """Copia la lista de compra en formato TSV al portapapeles."""
    if not vm.items_compra:
        if on_mostrar_snackbar:
            on_mostrar_snackbar("No hay datos en la lista de compra")
        return

    lineas = ["Color\tMarca\tCódigo\tSuperior\tPico\tInferior\tTotal piezas\tÁrea (m²)\tPliegos\tPaquetes"]
    for it in vm.items_compra:
        m = it.color.marca or "-"
        c = it.color.codigo or "-"
        lineas.append(
            f"{it.color.nombre}\t{m}\t{c}\t{it.piezas_superior}\t{it.piezas_pico}\t{it.piezas_inferior}\t"
            f"{it.piezas_totales}\t{it.area_m2:.2f}\t{it.pliegos}\t{it.paquetes}"
        )
    texto = "\n".join(lineas)

    copia_exitosa = False
    try:
        if pagina and isinstance(servicio_clipboard, ft.Service):
            if servicio_clipboard not in pagina.services:
                pagina.services.append(servicio_clipboard)

        if hasattr(servicio_clipboard, "set"):
            res = servicio_clipboard.set(texto)
            if asyncio.iscoroutine(res):
                if pagina:
                    pagina.run_task(servicio_clipboard.set, texto)
                else:
                    asyncio.run(res)
            copia_exitosa = True
    except Exception:
        copia_exitosa = False

    if copia_exitosa:
        if on_mostrar_snackbar:
            on_mostrar_snackbar("Lista de compra copiada al portapapeles")
    else:
        if on_mostrar_snackbar:
            on_mostrar_snackbar("No se pudo copiar la lista")


def poblar_tabla_compra(tabla: ft.DataTable, items_compra: list) -> None:
    """Llena las filas de la tabla de compra con los ítems calculados."""
    tabla.rows.clear()
    for it in items_compra:
        nombre_txt = it.color.nombre
        if it.color.marca or it.color.codigo:
            extra = f"{it.color.marca} {it.color.codigo}".strip()
            nombre_txt = f"{it.color.nombre} [{extra}]"
        tabla.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(nombre_txt)),
                    ft.DataCell(ft.Text(str(it.piezas_superior))),
                    ft.DataCell(ft.Text(str(it.piezas_pico))),
                    ft.DataCell(ft.Text(str(it.piezas_inferior))),
                    ft.DataCell(ft.Text(str(it.piezas_totales), weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(f"{it.area_m2:.2f}")),
                    ft.DataCell(ft.Text(str(it.pliegos), weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str(it.paquetes), weight=ft.FontWeight.BOLD)),
                ]
            )
        )
