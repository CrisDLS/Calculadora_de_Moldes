# ui/vista_moldes.py
import customtkinter as ctk
from configuracion.constantes import *
from utils.gestor_image import GestorImagenes

class VistaMoldes(ctk.CTkFrame):
    def __init__(self, master, callback_trompo_estrella, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.callback_trompo_estrella = callback_trompo_estrella

        # Instanciamos la imagen
        gestor = GestorImagenes()

        # Encabezado con icono de avión (placeholder)
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill="x", pady=(20, 10))
        
        # Cargamos la imagen
        image_molde = gestor.obtener_imagen("moldes", tipo= "header")

        # TODO: Icono avión rojo
        img_encabezado = ctk.CTkLabel(
            frame_header,
            text="",
            image=image_molde,
            fg_color="transparent",
        )
        img_encabezado.pack(side="left")

        ctk.CTkLabel(frame_header, text="   Escoge tu preferido", font=FONT_TITULO_MEDIANO, text_color=COLOR_TEXTO_BLANCO).pack(side="left")
        
        ctk.CTkFrame(self, height=2, fg_color=COLOR_TEXTO_GRIS_CLARO).pack(fill="x", pady=(0, 30))

        # Grid de Tarjetas (2 filas, 3 columnas)
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=20)
        
        moldes = [
            ("Trompo Estrella", True), ("Modelado", False), ("Piao", False),
            ("Bagda", False), ("Careca", False), ("Barrica", False)
        ]

        for i, (nombre, es_activo) in enumerate(moldes):
            row = i // 3
            col = i % 3
            grid_frame.grid_rowconfigure(row, weight=1)
            grid_frame.grid_columnconfigure(col, weight=1)

            cmd = self.callback_trompo_estrella if es_activo else None
            card = self._crear_tarjeta(grid_frame, nombre, comando=cmd)
            
            # AGREGAMOS PADX Y PADY AQUÍ:
            # padx=15: Espacio a los lados (total 30px entre tarjetas)
            # pady=15: Espacio arriba y abajo
            card.grid(row=row, column=col, sticky="nsew", padx=15, pady=15)

    def _crear_tarjeta(self, master, texto, comando=None):
        # 1. CONTENEDOR PRINCIPAL (Invisible)
        # Este frame solo sirve para agrupar las dos mitades, no tiene color.
        card_container = ctk.CTkFrame(master, fg_color="transparent")
        
        # Función para manejar el clic en cualquier parte
        def al_hacer_clic(event):
            if comando:
                comando()

        if comando:
            card_container.configure(cursor="hand2")
            card_container.bind("<Button-1>", al_hacer_clic)

        # --- PARTE SUPERIOR (Morada - Imagen) ---
        # corner_radius=20 redondea todo, pero luego lo "parchamos" abajo
        top_frame = ctk.CTkFrame(card_container, fg_color=COLOR_ACENTO_MORADO, corner_radius=20, width=0) # width=0 deja que se expanda
        top_frame.pack(side="top", fill="both", expand=True, pady=(0, 0)) # Spacing 0 es clave

        # TRUCO: Parche cuadrado morado en la parte inferior para quitar la curvatura de abajo
        patch_top = ctk.CTkFrame(top_frame, fg_color=COLOR_ACENTO_MORADO, corner_radius=0, height=10)
        patch_top.pack(side="bottom", fill="x")

        # Imagen/Texto dentro de la parte morada
        lbl_img = ctk.CTkLabel(top_frame, text=f"[SILUETA\n{texto.upper()}]", text_color="black")
        lbl_img.pack(expand=True, pady=20) # Usamos pack normal aquí

        # --- PARTE INFERIOR (Naranja - Título) ---
        bottom_frame = ctk.CTkFrame(card_container, fg_color=COLOR_ACENTO_NARANJA, corner_radius=20, height=50)
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 0))

        # TRUCO: Parche cuadrado naranja en la parte superior para quitar la curvatura de arriba
        # Usamos place para asegurar que quede "pegado" al borde superior del frame naranja
        patch_bottom = ctk.CTkFrame(bottom_frame, fg_color=COLOR_ACENTO_NARANJA, corner_radius=0, height=10)
        patch_bottom.place(relx=0, rely=0, relwidth=1)

        # Texto del título
        lbl_texto = ctk.CTkLabel(bottom_frame, text=texto, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO)
        lbl_texto.place(relx=0.5, rely=0.5, anchor="center")

        # --- VINCULACIÓN DE EVENTOS (Para que todo sea clicable) ---
        if comando:
            # Vinculamos todos los elementos visibles al clic
            top_frame.bind("<Button-1>", al_hacer_clic)
            patch_top.bind("<Button-1>", al_hacer_clic)
            lbl_img.bind("<Button-1>", al_hacer_clic)
            bottom_frame.bind("<Button-1>", al_hacer_clic)
            patch_bottom.bind("<Button-1>", al_hacer_clic)
            lbl_texto.bind("<Button-1>", al_hacer_clic)

        return card_container