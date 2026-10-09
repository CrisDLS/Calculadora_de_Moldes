# widgets/sidebar.py
import customtkinter as ctk
from configuracion.constantes import *


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, comando_navegacion, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO_SIDEBAR, width=250, corner_radius=0, **kwargs)
        self.comando_navegacion = comando_navegacion
        
        # Estado inicial
        self.es_expandido = True 

        # Evitamos que el frame se encoja automáticamente al contenido
        self.grid_propagate(False)

        # --- Botón Hamburguesa (Ahora es un Botón funcional) ---
        self.btn_menu = ctk.CTkButton(self, text="☰", font=("Arial", 26), 
                                      fg_color="transparent", 
                                      text_color=COLOR_ACENTO_NARANJA,
                                      width=40,
                                      hover_color=COLOR_SELECCION_SIDEBAR,
                                      command=self.alternar_sidebar) # <--- Vinculamos la función
        # Lo alineamos a la izquierda (w)
        self.btn_menu.pack(pady=(20, 40), padx=15, anchor="w")

        # Lista para guardar referencias a los botones y poder cambiar su texto luego
        self.botones_menu = []

        # --- Botones de Navegación ---
        self.btn_inicio = self._crear_boton_menu("Inicio", "inicio")
        self.btn_moldes = self._crear_boton_menu("Moldes", "moldes")
        self.btn_guardados = self._crear_boton_menu("Guardados", "guardados")
        self.btn_info = self._crear_boton_menu("Mas\nInfomacion", "info")

        self.seleccionar_boton("inicio")

        # --- Botón Inferior ---
        # Guardamos el texto original en un atributo custom para usarlo luego
        self.btn_info = ctk.CTkButton(self, text="Mas\ninfromación", anchor="w", fg_color="transparent",
                                      text_color=COLOR_TEXTO_BLANCO, hover=False, font=FONT_TEXTO_NORMAL)
        self.btn_info.texto_original = "Mas\ninfromación" # Hack para guardar el texto
        self.btn_info.pack(side="bottom", fill="x", pady=20, padx=10)

    def _crear_boton_menu(self, texto, nombre_vista):
        # Nota: Cuando tengas iconos, agrégalos aquí con el parámetro image=tu_imagen
        btn = ctk.CTkButton(self, text=f"   {texto}", anchor="w", 
                            fg_color="transparent", 
                            text_color=COLOR_TEXTO_BLANCO,
                            font=FONT_TEXTO_NORMAL,
                            height=50,
                            corner_radius=10,
                            hover_color=COLOR_SELECCION_SIDEBAR,
                            command=lambda v=nombre_vista: self.navegar(v))
        
        # Guardamos el texto original dentro del objeto botón para recordarlo
        btn.texto_original = f"   {texto}"
        
        btn.pack(pady=5, padx=10, fill="x")
        self.botones_menu.append(btn) # Lo agregamos a la lista
        return btn

    def navegar(self, vista):
        self.seleccionar_boton(vista)
        if self.comando_navegacion:
            self.comando_navegacion(vista)

    def seleccionar_boton(self, nombre_vista):
        # Reseteamos colores
        self.btn_inicio.configure(fg_color="transparent")
        self.btn_moldes.configure(fg_color="transparent")
        self.btn_guardados.configure(fg_color="transparent")

        # Resaltamos
        if nombre_vista == "inicio":
            self.btn_inicio.configure(fg_color=COLOR_SELECCION_SIDEBAR)
        elif nombre_vista == "moldes":
            self.btn_moldes.configure(fg_color=COLOR_SELECCION_SIDEBAR)
        elif nombre_vista == "guardados":
            self.btn_guardados.configure(fg_color=COLOR_SELECCION_SIDEBAR)

    def alternar_sidebar(self):
        if self.es_expandido:
            # --- COLAPSAR ---
            self.configure(width=70) # Reducir ancho del sidebar
            
            # Ocultar texto de los botones de navegación
            for btn in self.botones_menu:
                btn.configure(text="") 
            
            # Ocultar texto del botón info
            self.btn_info.configure(text="")
            
            self.es_expandido = False
        else:
            # --- EXPANDIR ---
            self.configure(width=250) # Restaurar ancho original
            
            # Restaurar texto de los botones
            for btn in self.botones_menu:
                btn.configure(text=btn.texto_original)
            
            # Restaurar texto info
            self.btn_info.configure(text=self.btn_info.texto_original)
            
            self.es_expandido = True