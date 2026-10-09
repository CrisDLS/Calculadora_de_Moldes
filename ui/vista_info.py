# ui/vista_info.py
import customtkinter as ctk
from configuracion.constantes import *

class VistaInfo(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Encabezado
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill="x", pady=(20, 10))
        # TODO: Icono información
        ctk.CTkLabel(frame_header, text="[i]", font=("Arial", 40), text_color=COLOR_ACENTO_NARANJA).pack(side="left", padx=(0,10))
        ctk.CTkLabel(frame_header, text="Mas Información", font=FONT_TITULO_GRANDE, text_color=COLOR_TEXTO_BLANCO).pack(side="left")
        
        ctk.CTkFrame(self, height=2, fg_color=COLOR_TEXTO_GRIS_CLARO).pack(fill="x", pady=(0, 30))

        # Estado Vacío
        frame_vacio = ctk.CTkFrame(self, fg_color="transparent")
        frame_vacio.pack(expand=True)
        
        lbl_mensaje = ctk.CTkLabel(frame_vacio, text="🛠️En Construcción 🛠️", 
                                   font=FONT_TITULO_MEDIANO, text_color=COLOR_SELECCION_SIDEBAR)
        lbl_mensaje.pack()