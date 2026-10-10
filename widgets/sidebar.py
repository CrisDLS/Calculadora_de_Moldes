# widgets/sidebar.py
import customtkinter as ctk
from configuracion.constantes import (COLOR_ACENTO_NARANJA, COLOR_FONDO_SIDEBAR, COLOR_SELECCION_SIDEBAR,
                                      COLOR_TEXTO_BLANCO, FONT_TEXTO_NORMAL)
from utils.gestor_imagenes import GestorImagenes

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, comando_navegacion, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO_SIDEBAR, width=250, corner_radius=0, **kwargs)
        self.comando_navegacion = comando_navegacion
        self.es_expandido = True 
        self.grid_propagate(False)

        # 1. Instanciamos el Gestor
        self.gestor = GestorImagenes()

        # 2. DEFINICIÓN: Solo Texto y Clave. La imagen la pedimos después.
        self.menu_items = [
            ("Inicio", "inicio"),
            ("Moldes", "moldes"),
            ("Guardados", "guardados"),
            ("🎨 Diseñar", "diseñar"),
            ("Más Información", "info")
        ]

        self.botones = {}

        # --- Botón Hamburguesa ---
        self.btn_menu = ctk.CTkButton(self, text="☰", font=("Arial", 26), width=40, 
                                      fg_color="transparent", text_color=COLOR_ACENTO_NARANJA,
                                      hover_color=COLOR_SELECCION_SIDEBAR, anchor="w",
                                      command=self.alternar_sidebar)
        self.btn_menu.pack(pady=(20, 40), padx=15, anchor="w")

        # --- Generación de Botones ---
        for texto, clave in self.menu_items:
            # PEDIMOS LA IMAGEN AL GESTOR (Tipo Sidebar)
            icono = self.gestor.obtener_imagen(clave, tipo="sidebar")
            
            btn = self._crear_boton_generico(f"   {texto}", clave, icono)
            self.botones[clave] = btn
            btn.pack(pady=5, padx=10, fill="x")

        self.espaciador = ctk.CTkFrame(self, fg_color="transparent")
        self.espaciador.pack(expand=True, fill="y")

        """# --- Botón Info ---
        icono_info = self.gestor.obtener_imagen("info", tipo="sidebar")
        self.btn_info = self._crear_boton_generico("Mas\nInformación", "info", icono_info)
        self.botones["info"] = self.btn_info
        self.btn_info.pack(side="bottom", fill="x", pady=20, padx=10)

        self.seleccionar_boton("inicio")"""

    def _crear_boton_generico(self, texto, clave, icono):
        btn = ctk.CTkButton(
            self, text=texto, image=icono, compound="left", anchor="w", 
            fg_color="transparent", text_color=COLOR_TEXTO_BLANCO,
            font=FONT_TEXTO_NORMAL, height=50, corner_radius=10,
            hover_color=COLOR_SELECCION_SIDEBAR,
            # AL NAVEGAR: También pasamos la imagen
            command=lambda v=clave: self.navegar(v)
        )
        btn.texto_original = texto
        return btn

    def navegar(self, vista):
        self.seleccionar_boton(vista)
        if self.comando_navegacion:
            # El título principal cambie su icono,
            icono_header = self.gestor.obtener_imagen(vista, tipo="header")
            
            # Enviamos el nombre de la vista Y su icono grande correspondiente
            self.comando_navegacion(vista, icono_header)

    def seleccionar_boton(self, vista_seleccionada):
        # 1. Limpiamos TODOS los botones 
        for btn in self.botones.values():
            btn.configure(fg_color="transparent")
        
        # 2. Iluminamos SOLO el seleccionado
        if vista_seleccionada in self.botones:
            self.botones[vista_seleccionada].configure(fg_color=COLOR_SELECCION_SIDEBAR)

    def alternar_sidebar(self):
        if self.es_expandido:
            # --- COLAPSAR ---
            self.configure(width=60)
            for btn in self.botones.values(): # Recorre botones principales e info
                btn.configure(text="") 
            self.es_expandido = False
        else:
            # --- EXPANDIR ---
            self.configure(width=180)
            for btn in self.botones.values():
                btn.configure(text=btn.texto_original) # Recupera el texto guardado
            self.es_expandido = True