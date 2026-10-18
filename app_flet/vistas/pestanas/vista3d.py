import asyncio
import webbrowser
from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo
from app_flet.vistas.pestanas.base import PestanaBase
from app_flet.vistas.pestanas.dialogos_catalogo import (
    dialogo_agregar_color,
    importar_colores_dialogo,
    exportar_colores_dialogo,
)
from app_flet.vistas.pestanas.vista3d_aux import (
    actualizar_vista_previa_2d,
    construir_fila_color,
    construir_item_cara,
    copiar_lista_compra_portapapeles,
    exportar_visor_3d_archivo,
    poblar_tabla_compra,
)
from logic.diseno.paleta import ColorPapel, cargar_catalogo, color_por_id
from logic.diseno.pintura import VariantePico


class PestanaVista3D(PestanaBase):
    """Pestaña de patrones de pintura, vista 3D interactiva y lista de compra."""

    def __init__(
        self,
        paleta,
        controlador,
        servicio_file_picker=None,
        servicio_clipboard=None,
        obtener_pagina: Optional[Callable[[], Optional[ft.Page]]] = None,
        on_mostrar_snackbar: Optional[Callable[[str], None]] = None,
        on_solicitar_sync: Optional[Callable[[], None]] = None,
    ):
        self.paleta = paleta
        self.controlador = controlador
        self.file_picker = servicio_file_picker if servicio_file_picker is not None else ft.FilePicker()
        self.servicio_clipboard = servicio_clipboard
        self._obtener_pagina = obtener_pagina
        self.on_mostrar_snackbar = on_mostrar_snackbar
        self.on_solicitar_sync = on_solicitar_sync

        self.catalogo_papel = cargar_catalogo()
        self.filtro_marca_actual = "todas"

        self._crear_controles_cono_superior()
        self._crear_controles_cono_inferior()
        self._crear_controles_picos()
        self._crear_controles_catalogo()
        self._crear_controles_compra_y_visor()
        self._construir_panel_contenido_3d()
        self._montar_contenedor()

    @property
    def pagina(self) -> Optional[ft.Page]:
        return self._obtener_pagina() if self._obtener_pagina else None

    def _crear_controles_cono_superior(self) -> None:
        self.dd_modo_sup = ft.Dropdown(
            label="Modo de caras",
            value="liso",
            options=[
                ft.DropdownOption(key="liso", text="Liso (1 color)"),
                ft.DropdownOption(key="alternado", text="Alternado por gajo"),
                ft.DropdownOption(key="bloques", text="Bloques de G gajos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=200,
        )
        self.txt_tam_bloque_sup = ft.TextField(
            label="Tamaño bloque (G)",
            value="5",
            width=140,
            dense=True,
            visible=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.col_colores_sup = ft.Column(spacing=6)
        self.btn_agregar_color_sup = ft.TextButton("Agregar color al ciclo", icon=ft.Icons.ADD, on_click=self.on_agregar_color_sup)

    def _crear_controles_cono_inferior(self) -> None:
        self.chk_mismo_esquema_inf = ft.Checkbox(
            label="Usar el mismo esquema en el cono inferior",
            value=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.dd_modo_inf = ft.Dropdown(
            label="Modo de caras",
            value="liso",
            options=[
                ft.DropdownOption(key="liso", text="Liso (1 color)"),
                ft.DropdownOption(key="alternado", text="Alternado por gajo"),
                ft.DropdownOption(key="bloques", text="Bloques de G gajos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=200,
        )
        self.txt_tam_bloque_inf = ft.TextField(
            label="Tamaño bloque (G)",
            value="5",
            width=140,
            dense=True,
            visible=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.col_colores_inf = ft.Column(spacing=6)
        self.btn_agregar_color_inf = ft.TextButton("Agregar color al ciclo", icon=ft.Icons.ADD, on_click=self.on_agregar_color_inf)
        self.container_controles_inf = ft.Column(
            controls=[
                ft.Row([self.dd_modo_inf, self.txt_tam_bloque_inf], spacing=10),
                self.col_colores_inf,
                self.btn_agregar_color_inf,
            ],
            spacing=6,
        )

    def _crear_controles_picos(self) -> None:
        self.dd_modo_caras_var_a = ft.Dropdown(
            label="Modo de caras (Variante A)",
            value="igual",
            options=[
                ft.DropdownOption(key="igual", text="Igual en las 4 caras"),
                ft.DropdownOption(key="alternado", text="Alternando 2 colores"),
                ft.DropdownOption(key="cuatro", text="4 colores distintos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=220,
        )
        self.col_colores_var_a = ft.Row(wrap=True, spacing=10)
        self.chk_usar_var_b = ft.Checkbox(
            label="Usar Variante B",
            value=False,
            on_change=self.on_cambio_patron_ui,
        )
        self.dd_repeticion_picos = ft.Dropdown(
            label="Repetición entre pirámides",
            value="todas_a",
            options=[
                ft.DropdownOption(key="todas_a", text="Todas A"),
                ft.DropdownOption(key="alternar_gajo", text="Alternar por gajo (A, B)"),
                ft.DropdownOption(key="alternar_hilera", text="Alternar por hilera (A, B)"),
                ft.DropdownOption(key="ajedrez", text="Ajedrez (A, B)"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=240,
        )
        self.dd_modo_caras_var_b = ft.Dropdown(
            label="Modo de caras (Variante B)",
            value="igual",
            options=[
                ft.DropdownOption(key="igual", text="Igual en las 4 caras"),
                ft.DropdownOption(key="alternado", text="Alternando 2 colores"),
                ft.DropdownOption(key="cuatro", text="4 colores distintos"),
            ],
            on_select=self.on_cambio_patron_ui,
            dense=True,
            width=220,
        )
        self.col_colores_var_b = ft.Row(wrap=True, spacing=10)
        self.panel_variante_b = ft.Column(
            visible=False,
            controls=[
                self.dd_modo_caras_var_b,
                self.col_colores_var_b,
            ],
            spacing=6,
        )

    def _crear_controles_catalogo(self) -> None:
        self.dd_filtro_marca = ft.Dropdown(
            label="Filtrar por marca",
            value="todas",
            options=[ft.DropdownOption(key="todas", text="Todas las marcas")],
            on_select=self.on_cambio_filtro_marca,
            dense=True,
            width=180,
        )
        self.btn_agregar_color_catalogo = ft.OutlinedButton(
            "Nuevo color…",
            icon=ft.Icons.COLOR_LENS,
            on_click=self.on_dialogo_agregar_color,
        )
        self.btn_importar_csv = ft.OutlinedButton(
            "Importar CSV…",
            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
            on_click=self.on_importar_catalogo_csv,
        )
        self.btn_exportar_csv = ft.OutlinedButton(
            "Exportar CSV…",
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            on_click=self.on_exportar_catalogo_csv,
        )

    def _crear_controles_compra_y_visor(self) -> None:
        self.fila_previa_sup = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)
        self.col_previa_picos = ft.Column(spacing=2)
        self.fila_previa_inf = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=2)

        self.txt_pliego_ancho = ft.TextField(
            label="Ancho pliego (cm)",
            value="50",
            width=140,
            dense=True,
            on_change=self.on_cambio_tam_pliego,
        )
        self.txt_pliego_alto = ft.TextField(
            label="Alto pliego (cm)",
            value="70",
            width=140,
            dense=True,
            on_change=self.on_cambio_tam_pliego,
        )
        self.txt_pliegos_paquete = ft.TextField(
            label="Pliegos por paquete",
            value="100",
            width=160,
            dense=True,
            on_change=self.on_cambio_pliegos_paquete,
        )
        self.lbl_aviso_colores = ft.Text(
            "Colores en pantalla aproximados: compara con tu pliego",
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            italic=True,
        )
        self.btn_abrir_visor_3d = ft.FilledButton(
            "Abrir visor 3D en navegador",
            icon=ft.Icons.OPEN_IN_BROWSER,
            on_click=self.on_abrir_visor_3d,
        )
        self.btn_exportar_visor_3d = ft.OutlinedButton(
            "Exportar visor 3D (.html)…",
            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
            on_click=self.on_exportar_visor_3d,
        )
        self.sw_mostrar_diseno_3d = ft.Switch(
            label="Mostrar diseño en 3D",
            value=True,
            disabled=True,
            tooltip="Muestra el diseño gráfico sobre las caras en el visor 3D",
            on_change=self.on_toggle_mostrar_diseno_3d,
        )
        self.btn_copiar_compra = ft.FilledButton(
            "Copiar lista de compra",
            icon=ft.Icons.COPY,
            on_click=self.on_copiar_lista_compra,
        )
        self.tabla_compra = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Color", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Superior", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Pico", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Inferior", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Total piezas", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Área (m²)", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Pliegos", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Paquetes", weight=ft.FontWeight.BOLD), numeric=True),
            ],
            rows=[],
            heading_row_height=36,
            data_row_min_height=32,
            data_row_max_height=36,
            column_spacing=16,
        )
        self.lbl_vacio_3d = ft.Container(
            content=ft.Text("Calcula para ver la vista 3D y lista de compra", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            alignment=ft.Alignment(0, 0),
            expand=True,
            visible=True,
        )

    def _construir_panel_contenido_3d(self) -> None:
        self.panel_contenido_3d = ft.Column(
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Patrones y colores del globo", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                self.dd_filtro_marca,
                                self.btn_agregar_color_catalogo,
                                self.btn_importar_csv,
                                self.btn_exportar_csv,
                            ],
                            spacing=6,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                self.lbl_aviso_colores,
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Text("1. Cono Superior", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_modo_sup, self.txt_tam_bloque_sup], spacing=10),
                self.col_colores_sup,
                self.btn_agregar_color_sup,
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Text("2. Cono Inferior", size=14, weight=ft.FontWeight.BOLD),
                self.chk_mismo_esquema_inf,
                self.container_controles_inf,
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Text("3. Picos (Pirámides)", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_repeticion_picos, self.chk_usar_var_b], spacing=10),
                ft.Text("Variante A:", weight=ft.FontWeight.BOLD, size=12),
                self.dd_modo_caras_var_a,
                self.col_colores_var_a,
                self.panel_variante_b,
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Text("Vista previa del patrón desplegado (por gajo)", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Cono Superior:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.fila_previa_sup, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Text("Hileras de Picos:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.col_previa_picos, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Text("Cono Inferior:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(content=self.fila_previa_inf, padding=4, bgcolor=ft.Colors.SURFACE_CONTAINER, border_radius=6),
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Text("Visor 3D interactivo (three.js)", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Abre el modelo 3D en tu navegador local con luces realistas, rotación orbital, azimut/elevación y modos día/noche.", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row(
                    controls=[self.btn_abrir_visor_3d, self.btn_exportar_visor_3d, self.sw_mostrar_diseno_3d],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=ft.Colors.OUTLINE),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Lista de compra de papel china", size=14, weight=ft.FontWeight.BOLD),
                                ft.Row(controls=[self.txt_pliego_ancho, self.txt_pliego_alto, self.txt_pliegos_paquete], spacing=10),
                                self.lbl_aviso_colores,
                            ],
                            spacing=4,
                        ),
                        self.btn_copiar_compra,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=self.tabla_compra,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=8,
                ),
            ],
            spacing=8,
        )

    def _montar_contenedor(self) -> None:
        self.contenedor = ft.Container(
            padding=15,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    self.lbl_vacio_3d,
                    self.panel_contenido_3d,
                ],
            ),
        )

    def construir(self) -> ft.Control:
        return self.contenedor

    def actualizar(self, vm: ViewModelTrompo) -> None:
        if vm.items_compra and not vm.desactualizado:
            self.lbl_vacio_3d.visible = False
            self.panel_contenido_3d.visible = True
            self.txt_pliegos_paquete.value = str(self.controlador.pliegos_por_paquete)
            self._actualizar_dropdowns_patrones()
            self.sw_mostrar_diseno_3d.value = vm.mostrar_diseno_3d
            self.sw_mostrar_diseno_3d.disabled = not vm.hay_diseno_visible

            poblar_tabla_compra(self.tabla_compra, vm.items_compra)
        else:
            self.lbl_vacio_3d.visible = True
            self.panel_contenido_3d.visible = False

    def _opciones_colores_filtradas(self) -> list:
        marca = self.filtro_marca_actual
        cols = self.catalogo_papel
        if marca != "todas":
            cols = [c for c in cols if (c.marca or "").strip().lower() == marca.lower()]

        opciones = []
        for c in cols:
            texto = c.nombre
            if c.marca or c.codigo:
                extra = f"{c.marca} {c.codigo}".strip()
                texto = f"{c.nombre} [{extra}]"
            opciones.append(ft.DropdownOption(key=c.id, text=texto))
        return opciones

    def _actualizar_dropdowns_patrones(self) -> None:
        opciones = self._opciones_colores_filtradas()
        p = self.controlador.pintura

        self.dd_modo_sup.value = p.modo_superior
        self.txt_tam_bloque_sup.visible = (p.modo_superior == "bloques")
        self.txt_tam_bloque_sup.value = str(p.tam_bloque_superior)


        self.col_colores_sup.controls.clear()
        for idx, cid in enumerate(p.colores_superior):
            self.col_colores_sup.controls.append(
                construir_fila_color(
                    cid,
                    opciones,
                    self.catalogo_papel,
                    lambda e, i=idx: self.on_cambio_color_ciclo_sup(i, e.control.value),
                    lambda e, i=idx: self.on_eliminar_color_ciclo_sup(i),
                    len(p.colores_superior) > 1,
                )
            )
        self.btn_agregar_color_sup.visible = (len(p.colores_superior) < 6 and p.modo_superior != "liso")

        self.chk_mismo_esquema_inf.value = p.mismo_esquema_inferior
        self.container_controles_inf.visible = not p.mismo_esquema_inferior
        self.dd_modo_inf.value = p.modo_inferior
        self.txt_tam_bloque_inf.visible = (p.modo_inferior == "bloques")
        self.txt_tam_bloque_inf.value = str(p.tam_bloque_inferior)

        self.col_colores_inf.controls.clear()
        for idx, cid in enumerate(p.colores_inferior):
            self.col_colores_inf.controls.append(
                construir_fila_color(
                    cid,
                    opciones,
                    self.catalogo_papel,
                    lambda e, i=idx: self.on_cambio_color_ciclo_inf(i, e.control.value),
                    lambda e, i=idx: self.on_eliminar_color_ciclo_inf(i),
                    len(p.colores_inferior) > 1,
                )
            )
        self.btn_agregar_color_inf.visible = (len(p.colores_inferior) < 6 and p.modo_inferior != "liso")

        self.dd_repeticion_picos.value = p.repeticion_picos
        self.chk_usar_var_b.value = p.usar_variante_b
        self.panel_variante_b.visible = p.usar_variante_b

        self.dd_modo_caras_var_a.value = p.variante_a.modo_caras
        self._construir_controles_variante(self.col_colores_var_a, p.variante_a, "A", opciones)

        self.dd_modo_caras_var_b.value = p.variante_b.modo_caras
        self._construir_controles_variante(self.col_colores_var_b, p.variante_b, "B", opciones)

        self._actualizar_vista_previa_2d()

    def _construir_controles_variante(self, container_row: ft.Row, variante: VariantePico, nombre_var: str, opciones: list) -> None:
        container_row.controls.clear()
        modo = variante.modo_caras

        def _item(label: str, val: str, c_idx: int, w: int = 180) -> ft.Row:
            return construir_item_cara(
                label,
                val,
                c_idx,
                opciones,
                self.catalogo_papel,
                lambda idx, cid: self.on_cambio_color_variante(nombre_var, idx, cid),
                w,
            )

        if modo == "igual":
            container_row.controls.append(_item("Color (4 caras)", variante.color_0, 0, 220))
        elif modo == "alternado":
            container_row.controls.extend([
                _item("Caras 0 y 2", variante.color_0, 0, 180),
                _item("Caras 1 y 3", variante.color_1, 1, 180),
            ])
        elif modo == "cuatro":
            for idx, c_val in enumerate([variante.color_0, variante.color_1, variante.color_2, variante.color_3]):
                container_row.controls.append(_item(f"Cara {idx}", c_val, idx, 150))

    def _actualizar_vista_previa_2d(self) -> None:
        actualizar_vista_previa_2d(
            self.fila_previa_sup,
            self.col_previa_picos,
            self.fila_previa_inf,
            self.controlador.pintura,
            int(self.controlador.gajos or 30),
            int(self.controlador.hileras or 2),
            self.catalogo_papel,
        )

    def on_cambio_patron_ui(self, e) -> None:
        p = self.controlador.pintura
        p.modo_superior = self.dd_modo_sup.value or "liso"
        try:
            p.tam_bloque_superior = max(1, int(self.txt_tam_bloque_sup.value or 5))
        except ValueError:
            p.tam_bloque_superior = 5

        p.mismo_esquema_inferior = bool(self.chk_mismo_esquema_inf.value)
        p.modo_inferior = self.dd_modo_inf.value or "liso"
        try:
            p.tam_bloque_inferior = max(1, int(self.txt_tam_bloque_inf.value or 5))
        except ValueError:
            p.tam_bloque_inferior = 5

        p.repeticion_picos = self.dd_repeticion_picos.value or "todas_a"
        p.usar_variante_b = bool(self.chk_usar_var_b.value)

        p.variante_a.modo_caras = self.dd_modo_caras_var_a.value or "igual"
        p.variante_b.modo_caras = self.dd_modo_caras_var_b.value or "igual"

        self.controlador.actualizar_pintura(pintura_completa=p)
        if self.on_solicitar_sync:
            self.on_solicitar_sync()

    def _modificar_ciclo(self, seccion: str, accion: str, idx: int = 0, cid: str = "") -> None:
        p = self.controlador.pintura
        cols = p.colores_superior if seccion == "sup" else p.colores_inferior
        if accion == "cambio" and idx < len(cols):
            cols[idx] = cid
            if seccion == "sup": p.color_superior = cols[0]
            else: p.color_inferior = cols[0]
        elif accion == "agregar" and len(cols) < 6:
            cols.append("blanco")
        elif accion == "eliminar" and len(cols) > 1 and idx < len(cols):
            cols.pop(idx)
            if seccion == "sup": p.color_superior = cols[0]
            else: p.color_inferior = cols[0]
        self.controlador.actualizar_pintura(pintura_completa=p)
        if self.on_solicitar_sync:
            self.on_solicitar_sync()

    def on_cambio_color_ciclo_sup(self, idx: int, cid: str) -> None:
        self._modificar_ciclo("sup", "cambio", idx, cid)

    def on_agregar_color_sup(self, e) -> None:
        self._modificar_ciclo("sup", "agregar")

    def on_eliminar_color_ciclo_sup(self, idx: int) -> None:
        self._modificar_ciclo("sup", "eliminar", idx)

    def on_cambio_color_ciclo_inf(self, idx: int, cid: str) -> None:
        self._modificar_ciclo("inf", "cambio", idx, cid)

    def on_agregar_color_inf(self, e) -> None:
        self._modificar_ciclo("inf", "agregar")

    def on_eliminar_color_ciclo_inf(self, idx: int) -> None:
        self._modificar_ciclo("inf", "eliminar", idx)

    def on_cambio_color_variante(self, nombre_var: str, cara_idx: int, cid: str) -> None:
        p = self.controlador.pintura
        var = p.variante_a if nombre_var == "A" else p.variante_b
        if cara_idx == 0: var.color_0 = cid
        elif cara_idx == 1: var.color_1 = cid
        elif cara_idx == 2: var.color_2 = cid
        elif cara_idx == 3: var.color_3 = cid

        if nombre_var == "A":
            p.color_pico = var.color_0

        self.controlador.actualizar_pintura(pintura_completa=p)
        if self.on_solicitar_sync:
            self.on_solicitar_sync()

    def on_cambio_filtro_marca(self, e) -> None:
        self.filtro_marca_actual = self.dd_filtro_marca.value or "todas"
        self._actualizar_dropdowns_patrones()
        page = self.pagina
        if page:
            page.update()

    def on_cambio_pliegos_paquete(self, e) -> None:
        try:
            val = max(1, int(self.txt_pliegos_paquete.value or 100))
        except ValueError:
            val = 100
        self.controlador.pliegos_por_paquete = val
        self.controlador.sin_guardar = True
        if self.on_solicitar_sync:
            self.on_solicitar_sync()

    def on_cambio_tam_pliego(self, e) -> None:
        try:
            ancho = float(self.txt_pliego_ancho.value or 50)
            alto = float(self.txt_pliego_alto.value or 70)
        except ValueError:
            return
        if ancho > 0 and alto > 0:
            self.controlador.pliego_ancho = ancho
            self.controlador.pliego_alto = alto
            self.controlador.sin_guardar = True
            if self.on_solicitar_sync:
                self.on_solicitar_sync()

    async def on_dialogo_agregar_color(self, e) -> None:
        def on_color_guardado(col: ColorPapel):
            self.catalogo_papel = cargar_catalogo()
            self._actualizar_marcas_disponibles()
            self._actualizar_dropdowns_patrones()

        await dialogo_agregar_color(
            page=self.pagina,
            on_color_guardado=on_color_guardado,
            on_mostrar_snackbar=self.on_mostrar_snackbar,
        )

    def _actualizar_marcas_disponibles(self) -> None:
        marcas = sorted(list(set(c.marca.strip() for c in self.catalogo_papel if c.marca.strip())))
        opts = [ft.DropdownOption(key="todas", text="Todas las marcas")]
        for m in marcas:
            opts.append(ft.DropdownOption(key=m, text=m))
        self.dd_filtro_marca.options = opts

    async def on_importar_catalogo_csv(self, e) -> None:
        def on_act():
            self.catalogo_papel = cargar_catalogo()
            self._actualizar_marcas_disponibles()
            self._actualizar_dropdowns_patrones()
            if self.on_solicitar_sync:
                self.on_solicitar_sync()

        await importar_colores_dialogo(
            file_picker=self.file_picker,
            on_catalogo_actualizado=on_act,
            on_mostrar_snackbar=self.on_mostrar_snackbar,
        )

    async def on_exportar_catalogo_csv(self, e) -> None:
        await exportar_colores_dialogo(
            file_picker=self.file_picker,
            catalogo=self.catalogo_papel,
            on_mostrar_snackbar=self.on_mostrar_snackbar,
        )

    def on_abrir_visor_3d(self, e) -> None:
        servidor = self.controlador.obtener_servidor_3d()
        if servidor and servidor.url:
            webbrowser.open(servidor.url)
            if self.on_mostrar_snackbar:
                self.on_mostrar_snackbar(f"Abriendo visor 3D en {servidor.url}")
        else:
            if self.on_mostrar_snackbar:
                self.on_mostrar_snackbar("No se pudo iniciar el servidor 3D local")

    async def on_exportar_visor_3d(self, e) -> None:
        await exportar_visor_3d_archivo(
            self.controlador,
            self.file_picker,
            self.on_mostrar_snackbar,
        )

    def on_copiar_lista_compra(self, e) -> None:
        copiar_lista_compra_portapapeles(
            self.controlador.get_view_model(),
            self.servicio_clipboard,
            self.pagina,
            self.on_mostrar_snackbar,
        )

    def on_toggle_mostrar_diseno_3d(self, e) -> None:
        val = bool(self.sw_mostrar_diseno_3d.value)
        self.controlador.cambiar_mostrar_diseno_3d(val)
        if self.on_solicitar_sync:
            self.on_solicitar_sync()
