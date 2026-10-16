"""Panel lateral izquierdo de entradas de parámetros y control de cálculo."""

from typing import Callable, Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo


class PanelEntradas:
    """Gestiona los campos de entrada geométricos, parámetros avanzados y botón de cálculo."""

    def __init__(
        self,
        paleta,
        controlador,
        barra_proyecto,
        on_toggle_tema: Callable,
        on_solicitar_sync: Callable[..., None],
        on_antes_de_calcular: Optional[Callable[[], None]] = None,
    ):
        self.paleta = paleta
        self.controlador = controlador
        self.barra_proyecto = barra_proyecto
        self.on_toggle_tema = on_toggle_tema
        self.on_solicitar_sync = on_solicitar_sync
        self.on_antes_de_calcular = on_antes_de_calcular

        self._crear_controles()
        self._construir_layout()

    def _crear_campo(self, label: str, default_val: str, unidad: str, hint: str = "") -> ft.TextField:
        return ft.TextField(
            label=label,
            value=default_val,
            suffix=ft.Text(unidad) if unidad else None,
            hint_text=hint if hint else None,
            on_change=self.on_change_input,
            dense=True,
        )

    def _crear_controles(self) -> None:
        self.lbl_titulo_app = ft.Text("Trompo estrella", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE)

        # Campos simples
        self.txt_altura = self._crear_campo("Altura total de papel", "950", "cm")
        self.txt_gajos = self._crear_campo("Cantidad de gajos", "30", "")
        self.txt_hileras = self._crear_campo("Hileras de picos", "2", "")
        self.txt_costura = self._crear_campo("Ancho de costura", "1", "cm")

        # Campos avanzados
        self.switch_avanzado = ft.Switch(label="Parámetros avanzados", on_change=self.on_switch_avanzado)
        self.txt_boca = self._crear_campo("Diámetro de boca", "", "cm", "11% de la altura")
        self.txt_pestana = self._crear_campo("Pestaña boca", "", "cm", "0 cm (Sin pestaña)")
        self.txt_d_mecha = self._crear_campo("Diámetro de mecha", "", "cm", "Calculado")
        self.txt_p_mecha = self._crear_campo("Peso de mecha", "", "g", "Opcional")

        self.txt_alambre = self._crear_campo("Alambre", "", "mm", "1.5 mm")
        self.txt_varillas = self._crear_campo("Varillas", "", "", "2")
        self.txt_llama = self._crear_campo("Altura de llama", "", "cm", "40.0 cm")
        self.txt_holgura = self._crear_campo("Holgura mín.", "", "cm", "10.0 cm")

        self.lbl_subseccion_avanzada = ft.Text(
            "Estructura y seguridad",
            weight=ft.FontWeight.BOLD,
            size=14,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.panel_avanzado = ft.Column(
            visible=False,
            controls=[
                self.txt_boca,
                self.txt_pestana,
                self.txt_d_mecha,
                self.txt_p_mecha,
                self.lbl_subseccion_avanzada,
                self.txt_alambre,
                self.txt_varillas,
                self.txt_llama,
                self.txt_holgura,
            ],
        )

        self.btn_calcular = ft.FilledButton(
            "Calcular",
            on_click=self.on_calcular,
            style=ft.ButtonStyle(color=ft.Colors.ON_PRIMARY, bgcolor=ft.Colors.PRIMARY),
        )
        self.lbl_error = ft.Text(color=self.paleta.color_error, visible=False)
        self.lbl_desactualizado = ft.Text(
            "Cambiaste los datos: pulsa Calcular",
            color=self.paleta.color_aviso,
            visible=False,
        )

        self.btn_tema = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE,
            tooltip="Cambiar a tema claro",
            icon_color=ft.Colors.ON_SURFACE,
            on_click=self.on_toggle_tema,
        )
        self.lbl_tema = ft.Text("Tema", size=13, color=ft.Colors.ON_SURFACE_VARIANT)

    def _construir_layout(self) -> None:
        self.panel_izquierdo = ft.Container(
            width=300,
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=10,
            content=ft.Column(
                controls=[
                    self.lbl_titulo_app,
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            controls=[
                                self.txt_altura,
                                self.txt_gajos,
                                self.txt_hileras,
                                self.txt_costura,
                                ft.Divider(color=ft.Colors.OUTLINE),
                                self.switch_avanzado,
                                self.panel_avanzado,
                                ft.Divider(color=ft.Colors.OUTLINE),
                                self.btn_calcular,
                                self.lbl_error,
                            ],
                            spacing=10,
                        ),
                    ),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    self.barra_proyecto.construir(),
                    ft.Divider(color=ft.Colors.OUTLINE),
                    ft.Row(
                        controls=[
                            self.lbl_tema,
                            self.btn_tema,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ]
            ),
        )

    def construir(self) -> ft.Control:
        return self.panel_izquierdo

    def aplicar_tema(self, paleta) -> None:
        self.paleta = paleta
        self.lbl_error.color = paleta.color_error

    def leer_vista_a_controlador(self) -> None:
        self.controlador.altura = self.txt_altura.value
        self.controlador.gajos = self.txt_gajos.value
        self.controlador.hileras = self.txt_hileras.value
        self.controlador.costura = self.txt_costura.value
        self.controlador.avanzado = self.switch_avanzado.value

        self.controlador.boca = self.txt_boca.value
        self.controlador.pestana = self.txt_pestana.value
        self.controlador.diametro_mecha = self.txt_d_mecha.value
        self.controlador.peso_mecha = self.txt_p_mecha.value
        self.controlador.alambre = self.txt_alambre.value
        self.controlador.varillas = self.txt_varillas.value
        self.controlador.altura_llama = self.txt_llama.value
        self.controlador.holgura = self.txt_holgura.value

    def cargar_desde_controlador(self) -> None:
        self.txt_altura.value = str(self.controlador.altura)
        self.txt_gajos.value = str(self.controlador.gajos)
        self.txt_hileras.value = str(self.controlador.hileras)
        self.txt_costura.value = str(self.controlador.costura)
        self.switch_avanzado.value = bool(self.controlador.avanzado)
        self.panel_avanzado.visible = bool(self.controlador.avanzado)

        self.txt_boca.value = str(self.controlador.boca or "")
        self.txt_pestana.value = str(self.controlador.pestana or "")
        self.txt_d_mecha.value = str(self.controlador.diametro_mecha or "")
        self.txt_p_mecha.value = str(self.controlador.peso_mecha or "")
        self.txt_alambre.value = str(self.controlador.alambre or "")
        self.txt_varillas.value = str(self.controlador.varillas or "")
        self.txt_llama.value = str(self.controlador.altura_llama or "")
        self.txt_holgura.value = str(self.controlador.holgura or "")

    def on_change_input(self, e) -> None:
        self.leer_vista_a_controlador()
        self.controlador.marcar_desactualizado()
        self.on_solicitar_sync()

    def on_switch_avanzado(self, e) -> None:
        self.panel_avanzado.visible = self.switch_avanzado.value
        self.leer_vista_a_controlador()
        self.controlador.marcar_desactualizado()
        self.on_solicitar_sync()

    def on_calcular(self, e) -> None:
        if self.on_antes_de_calcular:
            self.on_antes_de_calcular()
        self.leer_vista_a_controlador()
        vm = self.controlador.calcular()
        self.on_solicitar_sync(reset_zoom=True)
