# ui/modulos_moldes/vista_trompo_estrella.py
import customtkinter as ctk
from configuracion.constantes import (COLOR_ACENTO_MORADO, COLOR_ACENTO_NARANJA, COLOR_FILA_ALTERNADA,
                                      COLOR_FONDO_APP, COLOR_INPUT_BORDE, COLOR_INPUT_FONDO,
                                      COLOR_TEXTO_BLANCO, COLOR_TEXTO_GRIS_CLARO, FONT_BOTON,
                                      FONT_TEXTO_NORMAL, FONT_TITULO_GRANDE, FONT_TITULO_MEDIANO)

class VistaTrompoEstrella(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # --- Encabezado ---
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill="x", pady=(10, 15))
        
        lbl_placeholder_img_titulo = ctk.CTkLabel(frame_header, text="[IMG]", text_color=COLOR_TEXTO_GRIS_CLARO)
        lbl_placeholder_img_titulo.pack(side="left", padx=(0, 20))

        lbl_titulo = ctk.CTkLabel(frame_header, text="Trompo Estrella", font=FONT_TITULO_GRANDE, text_color=COLOR_TEXTO_BLANCO)
        lbl_titulo.pack(side="left")
        
        ctk.CTkFrame(self, height=2, fg_color=COLOR_TEXTO_GRIS_CLARO).pack(fill="x", pady=(0, 15))

        # --- Sección Central (Layout Ajustado) ---
        frame_central = ctk.CTkFrame(self, fg_color="transparent")
        frame_central.pack(fill="x", expand=True)
        
        # AJUSTE DE PROPORCIÓN: 
        # weight=2 para la izquierda (antes 1) y weight=5 para la derecha.
        # Esto hace que la derecha sea mucho más ancha y comprime la izquierda.
        frame_central.grid_columnconfigure(0, weight=5) 
        frame_central.grid_columnconfigure(1, weight=2)

        # === COLUMNA IZQUIERDA ===
        frame_izq = ctk.CTkFrame(frame_central, fg_color="transparent")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # 1. Inputs (Más compactos)
        frame_inputs = ctk.CTkFrame(frame_izq, fg_color="transparent")
        frame_inputs.pack(fill="x")
        frame_inputs.grid_columnconfigure(1, weight=1)

        self.entry_altura = self._crear_input(frame_inputs, 0, "Altura:")
        self.entry_gajos = self._crear_input(frame_inputs, 1, "Gajos:")
        self.entry_costura = self._crear_input(frame_inputs, 2, "Costura:")
        self.entry_hileras = self._crear_input(frame_inputs, 3, "Hileras:")

        # 2. Botón Calcular
        btn_calcular = ctk.CTkButton(frame_izq, text="Calcular", font=FONT_BOTON, 
                                     fg_color=COLOR_ACENTO_NARANJA, height=40, corner_radius=10)
        btn_calcular.pack(pady=(15, 20), fill="x")

        # 3. Tabla Resumen (Compacta y Bordes Blancos)
        self._crear_tabla_resumen(frame_izq)
        

        # === COLUMNA DERECHA (Gráfica - Ahora tiene más espacio) ===
        frame_der = ctk.CTkFrame(frame_central, fg_color=COLOR_ACENTO_MORADO, corner_radius=20, height=380)
        frame_der.grid(row=0, column=1, sticky="nsew")
        frame_der.pack_propagate(False)

        lbl_graf = ctk.CTkLabel(frame_der, text="Graficación de\nmedidas", font=FONT_TITULO_MEDIANO, text_color=COLOR_TEXTO_BLANCO)
        lbl_graf.pack(expand=True)

        btn_guardar_medidas = ctk.CTkButton(frame_der, text="   Guardar Medidas", fg_color="transparent", 
                                            text_color=COLOR_TEXTO_BLANCO, hover_color="#5a3275",
                                            command=self.evento_guardar_medidas)
        btn_guardar_medidas.pack(side="bottom", pady=20)


        # --- Sección Inferior: Tablas Detalladas (Redondeadas) ---
        self._crear_tabla_detallada(self, "Cono Superior")
        self._crear_tabla_detallada(self, "Pico")
        self._crear_tabla_detallada(self, "Cono Inferior")


    def _crear_input(self, master, row, label_text):
        lbl = ctk.CTkLabel(master, text=label_text, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO, anchor="w")
        lbl.grid(row=row, column=0, sticky="w", pady=5)
        
        # Input más compacto (height=30)
        entry = ctk.CTkEntry(master, border_width=1, border_color=COLOR_INPUT_BORDE,
                             fg_color=COLOR_INPUT_FONDO, text_color=COLOR_TEXTO_BLANCO,
                             corner_radius=6, height=30)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        return entry

    def evento_guardar_medidas(self):
        print("Guardando...")

    def _crear_tabla_resumen(self, master):
        # BORDE BLANCO SOLICITADO
        frame_tabla = ctk.CTkFrame(master, fg_color="transparent", border_width=1, border_color="white", corner_radius=0)
        frame_tabla.pack(fill="x")
        
        titulos = ["Diámetro de la Boca", "Ancho Max.", "Gajos mín. recomendados", "Gajos máx. recomendados"] 
        
        # DEFINIMOS ALTURA FIJA PARA LAS FILAS
        ALTURA_FILA = 30

        for i, titulo in enumerate(titulos):
            bg_color = COLOR_FILA_ALTERNADA if i % 2 != 0 else "transparent"
            
            # Agregamos height y desactivamos propagación
            row_frame = ctk.CTkFrame(frame_tabla, fg_color=bg_color, corner_radius=0, height=ALTURA_FILA)
            row_frame.pack(fill="x", padx=1) 
            row_frame.grid_propagate(False) # <--- EL CANDADO: Obliga a respetar los 22px

            row_frame.grid_columnconfigure(0, weight=2)
            row_frame.grid_columnconfigure(1, weight=1)

            # Labels sin pady, sticky nsew para que se centren solitos en el espacio pequeño
            lbl_izq = ctk.CTkLabel(row_frame, text=titulo, anchor="center", font=("Roboto", 11), text_color=COLOR_TEXTO_BLANCO)
            lbl_izq.grid(row=0, column=0, sticky="nsew", padx=5)
            
            # Divisor vertical
            ctk.CTkFrame(row_frame, width=1, fg_color="white").grid(row=0, column=0, sticky="nse", padx=0)

            lbl_der = ctk.CTkLabel(row_frame, text="-", anchor="center", font=("Roboto", 11), text_color=COLOR_TEXTO_BLANCO)
            lbl_der.grid(row=0, column=1, sticky="nsew", padx=5)

            # Línea separadora
            if i < len(titulos) - 1:
                ctk.CTkFrame(frame_tabla, height=1, fg_color="white").pack(fill="x")

    def _crear_tabla_detallada(self, master, titulo_tabla):
        ctk.CTkLabel(master, text=titulo_tabla, font=FONT_TITULO_MEDIANO, text_color=COLOR_TEXTO_BLANCO).pack(pady=(20, 5))

        # --- ESTRUCTURA REDONDEADA ---
        outer_frame = ctk.CTkFrame(master, fg_color="white", corner_radius=15)
        outer_frame.pack(fill="x")

        inner_frame = ctk.CTkFrame(outer_frame, fg_color=COLOR_FONDO_APP, corner_radius=15)
        inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # --- HEADERS ---
        # Altura fija para el encabezado también
        header_frame = ctk.CTkFrame(inner_frame, fg_color="transparent", corner_radius=10, height=25)
        header_frame.pack(fill="x", pady=(2,0))
        header_frame.grid_propagate(False) # Bloqueamos altura del header

        headers = ["Paso", "Largo", "Acum.", "Ancho/2"]
        for i, h in enumerate(headers):
            header_frame.grid_columnconfigure(i, weight=1)
            # Quitamos pady vertical, dejamos que se centre solo
            ctk.CTkLabel(header_frame, text=h, font=("Roboto", 11, "bold"), text_color=COLOR_TEXTO_BLANCO).grid(row=0, column=i, sticky="nsew")
            
            # Divisor Header
            if i > 0:
                 ctk.CTkFrame(header_frame, width=1, height=15, fg_color="white").grid(row=0, column=i, sticky="w")

        ctk.CTkFrame(inner_frame, height=1, fg_color="white").pack(fill="x")

        # --- BODY ---
        body_container = ctk.CTkFrame(inner_frame, fg_color="transparent", corner_radius=0)
        body_container.pack(fill="x", pady=(0, 5))

        # ALTURA FILA DATOS
        ALTURA_FILA_DATOS = 20 # Puedes bajarlo a 18 si quieres más comprimido

        for row_idx in range(1, 11): 
            bg_color = "transparent" if row_idx % 2 != 0 else COLOR_FILA_ALTERNADA
            
            # 1. Fijamos height
            row_frame = ctk.CTkFrame(body_container, fg_color=bg_color, corner_radius=0, height=ALTURA_FILA_DATOS)
            row_frame.pack(fill="x")
            
            # 2. IMPORTANTE: Bloqueamos la propagación para que respete el height=20
            row_frame.grid_propagate(False)
            
            for col_idx in range(4):
                row_frame.grid_columnconfigure(col_idx, weight=1)
                texto = f"{row_idx}" if col_idx == 0 else ""
                
                # 3. Label sin pady, usando sticky="nsew" ocupa todo el alto disponible (que son 20px)
                lbl = ctk.CTkLabel(row_frame, text=texto, font=("Roboto", 11), text_color=COLOR_TEXTO_BLANCO)
                lbl.grid(row=0, column=col_idx, sticky="nsew")
                
                # Divisor vertical sutil
                if col_idx > 0:
                      ctk.CTkFrame(row_frame, width=1, fg_color="white").grid(row=0, column=col_idx, sticky="nsw")
            
            # Línea separadora
            if row_idx < 10:
                ctk.CTkFrame(body_container, height=1, fg_color="#555555").pack(fill="x")