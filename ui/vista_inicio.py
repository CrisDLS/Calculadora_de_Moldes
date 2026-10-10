# ui/vista_inicio.py
import customtkinter as ctk
from configuracion.constantes import (COLOR_ACENTO_NARANJA, COLOR_TEXTO_BLANCO, COLOR_TEXTO_GRIS_CLARO,
                                      FONT_BOTON, FONT_TEXTO_NORMAL, FONT_TITULO_GRANDE, FONT_TITULO_MEDIANO)
from utils.gestor_imagenes import GestorImagenes

class VistaInicio(ctk.CTkFrame):
    def __init__(self, master, call_moldes, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.call_moldes = call_moldes

        # Instanciamos la imagen
        gestor = GestorImagenes()

        # Título Principal
        lbl_titulo = ctk.CTkLabel(self, text="¡Crea tu Globo de Catonlla\nPerfecto!", 
                                  font=FONT_TITULO_GRANDE, text_color=COLOR_TEXTO_BLANCO, justify="center")
        lbl_titulo.pack(pady=(50, 30))

        # 3. CARGAR LA IMAGEN
        # Pedimos la imagen con la clave que pusimos en el diccionario.
        # Usamos tipo="header" porque ahí configuramos el tamaño grande (200x200)
        imagen_globo = gestor.obtener_imagen("globo_central", tipo="header")

        # TODO: Aquí va la imagen central colorida del globo (Imagen 5)
        lbl_img_central = ctk.CTkLabel(
            self,
            text= "",
            image=imagen_globo,
            fg_color="transparent",
        )
        lbl_img_central.pack(pady=20)

        # Botón de Acción Principal
        btn_nuevo = ctk.CTkButton(self, text="Calcular Nuevo Molde", font=FONT_BOTON,
                                  fg_color=COLOR_ACENTO_NARANJA, height=50, corner_radius=25, command=self.call_moldes)
        btn_nuevo.pack(pady=30)

        # Separador
        ctk.CTkFrame(self, height=2, fg_color=COLOR_TEXTO_GRIS_CLARO).pack(fill="x", pady=30)

        # Sección Inferior (Instrucciones y Nota)
        frame_info = ctk.CTkFrame(self, fg_color="transparent")
        frame_info.pack(fill="x", padx=20)
        frame_info.grid_columnconfigure(0, weight=1)
        frame_info.grid_columnconfigure(1, weight=1)

        # Como Empezar
        lbl_como = ctk.CTkLabel(frame_info, text="Como Empezar?", font=FONT_TITULO_MEDIANO, text_color=COLOR_TEXTO_BLANCO, anchor="w")
        lbl_como.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        instrucciones = "1.Selecciona el tipo de molde\n2.Introduce las dimensiones deseadas\n3.Obtén el calculo"
        lbl_inst = ctk.CTkLabel(frame_info, text=instrucciones, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO, anchor="w", justify="left")
        lbl_inst.grid(row=1, column=0, sticky="w")

        # Nota
        lbl_nota_titulo = ctk.CTkLabel(frame_info, text="Nota:", font=FONT_TITULO_MEDIANO, text_color=COLOR_TEXTO_BLANCO, anchor="w")
        lbl_nota_titulo.grid(row=0, column=1, sticky="w", pady=(0, 10))

        nota = "Si guardas tus medidas podras\nver tu globo en 3d"
        lbl_nota = ctk.CTkLabel(frame_info, text=nota, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO, anchor="w", justify="left")
        lbl_nota.grid(row=1, column=1, sticky="w")