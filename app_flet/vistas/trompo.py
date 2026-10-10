# app_flet/vistas/trompo.py
import flet as ft
from app_flet.controlador import ControladorTrompo, ViewModelTrompo
from app_flet import tema

class VistaTrompo(ft.Container):
    def __init__(self):
        super().__init__()
        self.controlador = ControladorTrompo()
        self.expand = True
        
        # --- CAMPOS SIMPLES ---
        self.txt_altura = self._crear_campo("Altura total de papel", "950", "cm")
        self.txt_gajos = self._crear_campo("Cantidad de gajos", "30", "")
        self.txt_hileras = self._crear_campo("Hileras de picos", "2", "")
        self.txt_costura = self._crear_campo("Ancho de costura", "1", "cm")
        
        # --- CAMPOS AVANZADOS ---
        self.switch_avanzado = ft.Switch(label="Parámetros avanzados", on_change=self.on_switch_avanzado)
        self.txt_boca = self._crear_campo("Diámetro de boca", "", "cm", "11% de la altura")
        self.txt_pestana = self._crear_campo("Pestaña boca", "", "cm", "0 cm (Sin pestaña)")
        self.txt_d_mecha = self._crear_campo("Diámetro de mecha", "", "cm", "Calculado")
        self.txt_p_mecha = self._crear_campo("Peso de mecha", "", "g", "Opcional")
        
        # Subsección avanzada
        self.txt_alambre = self._crear_campo("Alambre", "", "mm", "1.5 mm")
        self.txt_varillas = self._crear_campo("Varillas", "", "", "2")
        self.txt_llama = self._crear_campo("Altura de llama", "", "cm", "40.0 cm")
        self.txt_holgura = self._crear_campo("Holgura mín.", "", "cm", "10.0 cm")
        
        self.panel_avanzado = ft.Column(
            visible=False,
            controls=[
                self.txt_boca, self.txt_pestana, self.txt_d_mecha, self.txt_p_mecha,
                ft.Text("Estructura y seguridad", weight=ft.FontWeight.BOLD, size=14, color=tema.COLOR_TEXTO_SECUNDARIO),
                self.txt_alambre, self.txt_varillas, self.txt_llama, self.txt_holgura
            ]
        )
        
        self.btn_calcular = ft.FilledButton(
            "Calcular", 
            on_click=self.on_calcular, 
            style=ft.ButtonStyle(color=tema.COLOR_TEXTO, bgcolor=tema.COLOR_ACENTO)
        )
        self.lbl_error = ft.Text(color=tema.COLOR_ERROR, visible=False)
        self.lbl_desactualizado = ft.Text("Cambiaste los datos: pulsa Calcular", color=tema.COLOR_AVISO, visible=False)
        
        panel_izquierdo = ft.Container(
            width=300,
            padding=20,
            bgcolor=tema.COLOR_FONDO_SECUNDARIO,
            border_radius=10,
            content=ft.ListView(
                controls=[
                    ft.Text("Trompo estrella", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.txt_altura, self.txt_gajos, self.txt_hileras, self.txt_costura,
                    ft.Divider(),
                    self.switch_avanzado,
                    self.panel_avanzado,
                    ft.Divider(),
                    self.btn_calcular,
                    self.lbl_error,
                ],
                spacing=10
            )
        )
        
        # --- ZONA DERECHA ---
        self.grid_tarjetas = ft.ResponsiveRow(run_spacing=10)
        self.col_avisos = ft.Column(spacing=5)
        
        tab_resumen = ft.ListView(
            padding=20,
            controls=[
                self.lbl_desactualizado,
                self.grid_tarjetas,
                ft.Divider(),
                self.col_avisos
            ]
        )
        tab_tablas = ft.Container(content=ft.Text("Próximamente"), alignment=ft.Alignment(0, 0))
        tab_2d = ft.Container(content=ft.Text("Próximamente"), alignment=ft.Alignment(0, 0))
        tab_3d = ft.Container(content=ft.Text("Próximamente"), alignment=ft.Alignment(0, 0))
        
        self.tabs = ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Resumen"),
                            ft.Tab(label="Tablas"),
                            ft.Tab(label="Moldes 2D"),
                            ft.Tab(label="Vista 3D")
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[tab_resumen, tab_tablas, tab_2d, tab_3d]
                    )
                ]
            )
        )
        
        panel_derecho = ft.Container(
            expand=True,
            padding=10,
            content=self.tabs
        )
        
        self.content = ft.Row(
            expand=True,
            controls=[panel_izquierdo, panel_derecho],
            spacing=0
        )
        
        self._sync_controlador_a_vista(self.controlador.get_view_model())

    def _crear_campo(self, label: str, default_val: str, unidad: str, hint: str = "") -> ft.TextField:
        txt = ft.TextField(
            label=label,
            value=default_val,
            suffix=ft.Text(unidad) if unidad else None,
            hint_text=hint if hint else None,
            on_change=self.on_change_input,
            dense=True
        )
        return txt

    def on_change_input(self, e):
        self.controlador.marcar_desactualizado()
        vm = self.controlador.get_view_model()
        self._sync_controlador_a_vista(vm)

    def on_switch_avanzado(self, e):
        self.panel_avanzado.visible = self.switch_avanzado.value
        self.controlador.marcar_desactualizado()
        try:
            self.update()
        except RuntimeError:
            pass

    def _leer_vista_a_controlador(self):
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

    def on_calcular(self, e):
        self._leer_vista_a_controlador()
        vm = self.controlador.calcular()
        self._sync_controlador_a_vista(vm)

    def _sync_controlador_a_vista(self, vm: ViewModelTrompo):
        # Mensaje de error
        if vm.mensaje_error:
            self.lbl_error.value = vm.mensaje_error
            self.lbl_error.visible = True
        else:
            self.lbl_error.visible = False
            self.lbl_error.value = ""

        # Estado desactualizado
        if vm.desactualizado:
            self.lbl_desactualizado.visible = True
            self.grid_tarjetas.controls.clear()
            self.col_avisos.controls.clear()
        else:
            self.lbl_desactualizado.visible = False
            self.grid_tarjetas.controls.clear()
            self.col_avisos.controls.clear()
            
            # Construir tarjetas
            for tj in vm.tarjetas:
                bg_color = tema.COLOR_FONDO_SECUNDARIO
                text_color = tema.COLOR_TEXTO
                if tj.etiqueta == "Viable":
                    bg_color = tema.COLOR_OK if tj.valor == "Sí" else tema.COLOR_ERROR
                    text_color = ft.Colors.WHITE
                    
                card = ft.Container(
                    bgcolor=bg_color,
                    padding=15,
                    border_radius=8,
                    col={"sm": 12, "md": 6, "lg": 4, "xl": 3},
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(tj.etiqueta, size=12, color=tema.COLOR_TEXTO_SECUNDARIO if text_color != ft.Colors.WHITE else text_color),
                            ft.Text(tj.valor, size=18, weight=ft.FontWeight.BOLD, color=text_color)
                        ]
                    )
                )
                self.grid_tarjetas.controls.append(card)
                
            # Construir avisos
            colores = {
                "ok": tema.COLOR_OK,
                "aviso": tema.COLOR_AVISO,
                "error": tema.COLOR_ERROR,
                "info": tema.COLOR_INFO
            }
            for av in vm.avisos:
                c = colores.get(av.clase, tema.COLOR_TEXTO)
                self.col_avisos.controls.append(
                    ft.Text(av.texto, color=c)
                )
        try:
            self.update()
        except RuntimeError:
            pass
