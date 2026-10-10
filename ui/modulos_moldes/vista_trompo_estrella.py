# ui/modulos_moldes/vista_trompo_estrella.py
import customtkinter as ctk
from configuracion.constantes import (COLOR_ACENTO_MORADO, COLOR_ACENTO_NARANJA, COLOR_AVISO_AVISO,
                                      COLOR_AVISO_AVISO_TEXTO, COLOR_AVISO_ERROR, COLOR_AVISO_INFO,
                                      COLOR_AVISO_OK, COLOR_FILA_ALTERNADA, COLOR_FONDO_APP,
                                      COLOR_INPUT_BORDE, COLOR_INPUT_FONDO, COLOR_TEXTO_BLANCO,
                                      COLOR_TEXTO_GRIS_CLARO, FONT_BOTON, FONT_TEXTO_NORMAL,
                                      FONT_TEXTO_PEQUENO, FONT_TITULO_GRANDE, FONT_TITULO_MEDIANO)
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from ui.modulos_moldes.presentador_trompo_estrella import (ETIQUETAS_RESUMEN_SIMPLE, clasificar_aviso,
                                                           formatear_resumen, leer_entrada)

class VistaTrompoEstrella(ctk.CTkScrollableFrame):
    # Clase de aviso -> (color de fondo, color de texto)
    _COLORES_AVISO = {
        "error": (COLOR_AVISO_ERROR, COLOR_TEXTO_BLANCO),
        "aviso": (COLOR_AVISO_AVISO, COLOR_AVISO_AVISO_TEXTO),
        "ok": (COLOR_AVISO_OK, COLOR_TEXTO_BLANCO),
        "info": (COLOR_AVISO_INFO, COLOR_TEXTO_BLANCO),
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.entradas = {}      # clave del presentador -> CTkEntry
        self.resultado = None   # último BalloonCalculationResult (None si hubo error)

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
        
        # PROPORCIÓN DE COLUMNAS: weight=5 para la izquierda (inputs y resultados) y
        # weight=2 para la derecha (gráfica). Pendiente de decidir en el Paso 7.
        frame_central.grid_columnconfigure(0, weight=5) 
        frame_central.grid_columnconfigure(1, weight=2)

        # === COLUMNA IZQUIERDA ===
        frame_izq = ctk.CTkFrame(frame_central, fg_color="transparent")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # 1. Inputs (Más compactos)
        frame_inputs = ctk.CTkFrame(frame_izq, fg_color="transparent")
        frame_inputs.pack(fill="x")
        frame_inputs.grid_columnconfigure(1, weight=1)

        self.entry_altura = self._crear_input(frame_inputs, 0, "Altura:", "cm", clave="altura")
        self.entry_gajos = self._crear_input(frame_inputs, 1, "Gajos:", "", clave="gajos")
        self.entry_costura = self._crear_input(frame_inputs, 2, "Costura:", "cm", clave="costura")
        self.entry_hileras = self._crear_input(frame_inputs, 3, "Hileras:", "", clave="hileras")

        # 2. Parámetros avanzados (apagado = modo simple: esos campos se ignoran)
        self.switch_avanzado = ctk.CTkSwitch(frame_izq, text="Parámetros avanzados", font=FONT_TEXTO_NORMAL,
                                             text_color=COLOR_TEXTO_BLANCO, progress_color=COLOR_ACENTO_NARANJA,
                                             command=self._alternar_avanzados)
        self.switch_avanzado.pack(anchor="w", pady=(10, 0))
        self.frame_avanzado = ctk.CTkFrame(frame_izq, fg_color="transparent")  # se muestra al activar el interruptor
        self._crear_seccion_avanzada(self.frame_avanzado)

        # 3. Botón Calcular
        self.btn_calcular = ctk.CTkButton(frame_izq, text="Calcular", font=FONT_BOTON, 
                                          fg_color=COLOR_ACENTO_NARANJA, height=40, corner_radius=10,
                                          command=self._calcular)
        self.btn_calcular.pack(pady=(15, 5), fill="x")

        # Mensaje de error de entrada (vacío si todo va bien)
        self.lbl_error = ctk.CTkLabel(frame_izq, text="", text_color=COLOR_AVISO_ERROR, anchor="w",
                                      justify="left", wraplength=360, font=FONT_TEXTO_NORMAL)
        self.lbl_error.pack(fill="x", pady=(0, 10))

        # 4. Tabla Resumen (Compacta y Bordes Blancos)
        self._crear_tabla_resumen(frame_izq)

        # 5. Panel de avisos (color según la clase de aviso)
        self.frame_avisos = ctk.CTkFrame(frame_izq, fg_color="transparent")
        self.frame_avisos.pack(fill="x", pady=(10, 0))
        

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


    def _crear_input(self, master, row, label_text, unidad="", ayuda="", clave=None):
        lbl = ctk.CTkLabel(master, text=label_text, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO, anchor="w")
        lbl.grid(row=row, column=0, sticky="w", pady=5)
        
        # Input más compacto (height=30); `ayuda` es el valor por defecto como texto de ayuda
        entry = ctk.CTkEntry(master, border_width=1, border_color=COLOR_INPUT_BORDE,
                             fg_color=COLOR_INPUT_FONDO, text_color=COLOR_TEXTO_BLANCO,
                             corner_radius=6, height=30, placeholder_text=ayuda)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)

        ctk.CTkLabel(master, text=unidad, width=36, font=FONT_TEXTO_PEQUENO,
                     text_color=COLOR_TEXTO_GRIS_CLARO, anchor="w").grid(row=row, column=2, sticky="w", padx=(6, 0))
        if clave is not None:
            self.entradas[clave] = entry
        return entry

    def _crear_seccion_avanzada(self, master):
        """Campos del modo avanzado. Apagado = modo simple: se ignoran en el cálculo."""
        master.grid_columnconfigure(1, weight=1)
        self._crear_input(master, 0, "Diámetro de boca:", "cm", "11 % de la altura", "diametro_boca")
        self._crear_input(master, 1, "Pestaña:", "cm", "4", "pestana_boca")
        self._crear_input(master, 2, "Diámetro de mecha:", "cm", "50 % de la boca", "diametro_mecha")
        self._crear_input(master, 3, "Peso de mecha:", "g", "sin dato", "masa_mecha_g")
        ctk.CTkLabel(master, text="Estructura y llama", font=FONT_TEXTO_NORMAL,
                     text_color=COLOR_TEXTO_GRIS_CLARO, anchor="w").grid(row=4, column=0, columnspan=3,
                                                                          sticky="w", pady=(10, 0))
        self._crear_input(master, 5, "Alambre:", "mm", "2", "alambre_mm")
        self._crear_input(master, 6, "Varillas:", "pzas", "4", "varillas")
        self._crear_input(master, 7, "Altura de llama:", "cm", "40", "altura_llama")
        self._crear_input(master, 8, "Holgura mínima:", "cm", "10", "holgura_min")

    def _alternar_avanzados(self):
        if self.switch_avanzado.get():
            self.frame_avanzado.pack(fill="x", before=self.btn_calcular, pady=(5, 0))
        else:
            self.frame_avanzado.pack_forget()

    def _calcular(self):
        """Lee los campos, calcula y pinta. Los errores de entrada se muestran en la vista."""
        valores = {clave: entry.get() for clave, entry in self.entradas.items()}
        avanzado = bool(self.switch_avanzado.get())
        try:
            entrada = leer_entrada(valores, avanzado)
            resultado = TrompoEstrellaCalculator().calcular(entrada)
        except ValueError as exc:
            self.resultado = None
            self.lbl_error.configure(text=str(exc))
            self._pintar_resumen([(e, "-") for e in ETIQUETAS_RESUMEN_SIMPLE])
            self._pintar_avisos([])
            return
        self.resultado = resultado
        self.lbl_error.configure(text="")
        self._pintar_resumen(formatear_resumen(resultado))
        self._pintar_avisos(resultado.avisos)

    def evento_guardar_medidas(self):
        print("Guardando...")

    def _crear_tabla_resumen(self, master):
        # BORDE BLANCO SOLICITADO
        self.frame_resumen = ctk.CTkFrame(master, fg_color="transparent", border_width=1, border_color="white", corner_radius=0)
        self.frame_resumen.pack(fill="x")
        self._pintar_resumen([(e, "-") for e in ETIQUETAS_RESUMEN_SIMPLE])

    def _pintar_resumen(self, filas):
        """Reconstruye la tabla resumen con una lista de (etiqueta, valor)."""
        for hijo in self.frame_resumen.winfo_children():
            hijo.destroy()

        # DEFINIMOS ALTURA FIJA PARA LAS FILAS
        ALTURA_FILA = 30

        for i, (titulo, valor) in enumerate(filas):
            bg_color = COLOR_FILA_ALTERNADA if i % 2 != 0 else "transparent"
            
            # Agregamos height y desactivamos propagación
            row_frame = ctk.CTkFrame(self.frame_resumen, fg_color=bg_color, corner_radius=0, height=ALTURA_FILA)
            row_frame.pack(fill="x", padx=1) 
            row_frame.grid_propagate(False) # <--- EL CANDADO: Obliga a respetar la altura fija

            row_frame.grid_columnconfigure(0, weight=2)
            row_frame.grid_columnconfigure(1, weight=1)

            # Labels sin pady, sticky nsew para que se centren solitos en el espacio pequeño
            lbl_izq = ctk.CTkLabel(row_frame, text=titulo, anchor="center", font=("Roboto", 11), text_color=COLOR_TEXTO_BLANCO)
            lbl_izq.grid(row=0, column=0, sticky="nsew", padx=5)
            
            # Divisor vertical
            ctk.CTkFrame(row_frame, width=1, fg_color="white").grid(row=0, column=0, sticky="nse", padx=0)

            lbl_der = ctk.CTkLabel(row_frame, text=valor, anchor="center", font=("Roboto", 11), text_color=COLOR_TEXTO_BLANCO)
            lbl_der.grid(row=0, column=1, sticky="nsew", padx=5)

            # Línea separadora
            if i < len(filas) - 1:
                ctk.CTkFrame(self.frame_resumen, height=1, fg_color="white").pack(fill="x")

    def _pintar_avisos(self, avisos):
        """Un renglón por aviso, con color según su clase (error, aviso, ok, info)."""
        for hijo in self.frame_avisos.winfo_children():
            hijo.destroy()
        for texto in avisos:
            fondo, color_texto = self._COLORES_AVISO[clasificar_aviso(texto)]
            ctk.CTkLabel(self.frame_avisos, text=texto, fg_color=fondo, text_color=color_texto,
                         corner_radius=6, anchor="w", justify="left", wraplength=360,
                         font=("Roboto", 12)).pack(fill="x", pady=3, ipadx=6, ipady=4)

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