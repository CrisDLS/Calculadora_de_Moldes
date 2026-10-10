# App.py
import customtkinter as ctk
import os
import sys
from configuracion.constantes import COLOR_FONDO_APP
from widgets.sidebar import Sidebar
from ui.vista_inicio import VistaInicio
from ui.vista_moldes import VistaMoldes
from ui.vista_guardados import VistaGuardados
from ui.vista_disenar import VistaDiseñar
from ui.vista_info import VistaInfo
from ui.modulos_moldes.vista_trompo_estrella import VistaTrompoEstrella

# Configuración global de CTk
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") # No importa mucho porque usamos colores personalizados

# --- FUNCIÓN HELPER PARA RUTAS (Indispensable para el .ico en el .exe) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mi Proyecto Globos")
        self.geometry("1024x700")
        self.minsize(800, 500)
        self.configure(fg_color=COLOR_FONDO_APP)
        ruta_icono = resource_path(os.path.join("recursos", "GloboTE.ico"))
        if os.path.exists(ruta_icono):
            self.iconbitmap(ruta_icono)
        else:
            print(f"⚠️ Advertencia: No se encontró el icono en {ruta_icono}")

        # Configuración del layout principal (Grid 1x2)
        self.grid_columnconfigure(0, weight=0) # Sidebar fija
        self.grid_columnconfigure(1, weight=1) # Contenido expandible
        self.grid_rowconfigure(0, weight=1)

        # --- Inicializar Sidebar ---
        self.sidebar = Sidebar(self, comando_navegacion=self.cambiar_vista)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # --- Área de Contenido Principal ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Diccionario para guardar las instancias de las vistas
        self.vistas = {}

        # Inicializar y mostrar la vista por defecto (Moldes, según tu flujo de imágenes)
        self.cambiar_vista("inicio")


    def cambiar_vista(self, nombre_vista, icono_header=None):
        # 1. Limpiar el content_frame actual
        for widget in self.content_frame.winfo_children():
            widget.pack_forget() # O grid_forget(), dependiendo de cómo se inserten

        # 2. Obtener o crear la vista solicitada
        vista = self.vistas.get(nombre_vista)
        
        if vista is None:
            # Lazy loading: Solo creamos la vista si no existe
            if nombre_vista == "inicio":
                vista = VistaInicio(self.content_frame, call_moldes=lambda: self.cambiar_vista("moldes"))
            elif nombre_vista == "moldes":
                # Pasamos un callback específico para cuando se hace click en "Trompo Estrella"
                vista = VistaMoldes(self.content_frame, callback_trompo_estrella=lambda: self.cambiar_vista("trompo_estrella"))
            elif nombre_vista == "guardados":
                vista = VistaGuardados(self.content_frame)
            elif nombre_vista == "diseñar":
                vista = VistaDiseñar(self.content_frame)
            elif nombre_vista == "info":
                vista = VistaInfo(self.content_frame)
            elif nombre_vista == "trompo_estrella":
                vista = VistaTrompoEstrella(self.content_frame)
                # Hack visual: si estamos en trompo estrella, marcamos "Moldes" en el sidebar
                self.sidebar.seleccionar_boton("moldes") 
            
            self.vistas[nombre_vista] = vista

        # 3. Mostrar la nueva vista
        if vista:
            # Usamos pack(fill="both", expand=True) para que la vista ocupe todo el content_frame
            vista.pack(fill="both", expand=True)
            
            # Actualizar selección del sidebar si no es una sub-vista como trompo_estrella
            if nombre_vista != "trompo_estrella":
                 self.sidebar.seleccionar_boton(nombre_vista)


if __name__ == "__main__":
    app = App()
    app.mainloop()