# ui/modulos_moldes/vista_trompo_estrella.py
import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from configuracion.constantes import (COLOR_ACENTO_MORADO, COLOR_ACENTO_NARANJA, COLOR_AVISO_AVISO,
                                      COLOR_AVISO_AVISO_TEXTO, COLOR_AVISO_ERROR, COLOR_AVISO_INFO,
                                      COLOR_AVISO_OK, COLOR_FILA_ALTERNADA, COLOR_FONDO_APP,
                                      COLOR_INPUT_BORDE, COLOR_INPUT_FONDO, COLOR_TEXTO_BLANCO,
                                      COLOR_TEXTO_GRIS_CLARO, FONT_BOTON, FONT_TEXTO_NORMAL,
                                      FONT_TEXTO_PEQUENO, FONT_TITULO_GRANDE, FONT_TITULO_MEDIANO,
                                      COLOR_GRAFICA_FONDO_FIGURA, COLOR_GRAFICA_FONDO_EJES,
                                      COLOR_GRAFICA_TEXTO, COLOR_GRAFICA_LINEAS, COLOR_GRAFICA_PESTANA)
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from presentacion.trompo_estrella import (ETIQUETAS_RESUMEN_SIMPLE, clasificar_aviso,
                                                           formatear_resumen, leer_entrada, formatear_tablas, tabla_a_texto)
from ui.modulos_moldes.graficas_trompo_estrella import figura_moldes, figura_perfil
from tkinter import ttk

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
        self.variables = {}     # clave del presentador -> StringVar
        self.resultado = None   # último BalloonCalculationResult (None si hubo error)
        self.datos_desactualizados = False
        
        # Estado de gráfica
        self.figura_actual = None
        self.canvas_widget = None
        self.tipo_grafica_var = ctk.StringVar(value="Moldes")

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
        
        # PROPORCIÓN DE COLUMNAS: weight=3 para la izquierda (inputs y resultados) y
        # weight=2 para la derecha (gráfica). Para que sea un 40%.
        frame_central.grid_columnconfigure(0, weight=3) 
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

        self.seg_btn_grafica = ctk.CTkSegmentedButton(frame_der, values=["Moldes", "Perfil armado"],
                                                      variable=self.tipo_grafica_var,
                                                      command=self._cambiar_grafica)
        self.seg_btn_grafica.pack(fill="x", padx=20, pady=(15, 10))
        
        self.frame_canvas = ctk.CTkFrame(frame_der, fg_color="transparent")
        self.frame_canvas.pack(expand=True, fill="both", padx=10, pady=5)

        btn_guardar_medidas = ctk.CTkButton(frame_der, text="   Guardar Medidas", fg_color="transparent", 
                                            text_color=COLOR_TEXTO_BLANCO, hover_color="#5a3275",
                                            command=self.evento_guardar_medidas)
        btn_guardar_medidas.pack(side="bottom", pady=20)


        # --- Sección Inferior: Tablas Detalladas (CTkTabview) ---
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_changed)
        self.tabview.pack(fill="both", expand=True, pady=(20, 0))
        
        self.nombres_tabs = ["Cono superior", "Pico", "Cono inferior"]
        self.tab_widgets = {}
        
        self._configurar_estilo_treeview()

        for nombre in self.nombres_tabs:
            tab = self.tabview.add(nombre)
            
            lbl_resumen = ctk.CTkLabel(tab, text="", font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO)
            lbl_resumen.pack(pady=(5, 5))
            
            frame_tree = ctk.CTkFrame(tab, fg_color="transparent")
            frame_tree.pack(fill="both", expand=True)
            
            from tkinter import ttk
            scrollbar = ttk.Scrollbar(frame_tree)
            scrollbar.pack(side="right", fill="y")
            
            tree = ttk.Treeview(frame_tree, yscrollcommand=scrollbar.set, style="Dark.Treeview")
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=tree.yview)
            
            lbl_nota = ctk.CTkLabel(tab, text="", font=FONT_TEXTO_PEQUENO, text_color=COLOR_AVISO_INFO)
            lbl_nota.pack(pady=(5, 5))
            
            btn_copiar = ctk.CTkButton(tab, text="Copiar tabla", font=FONT_BOTON,
                                       fg_color=COLOR_ACENTO_MORADO, command=lambda n=nombre: self._copiar_tabla(n))
            btn_copiar.pack(pady=(5, 10))
            
            self.tab_widgets[nombre] = {
                'tree': tree,
                'lbl_resumen': lbl_resumen,
                'lbl_nota': lbl_nota,
                'tabla_data': None
            }

    def _on_tab_changed(self):
        nombre = self.tabview.get()
        if nombre in self.tab_widgets:
            tree = self.tab_widgets[nombre]['tree']
            # Forzar distribución al cambiar de pestaña
            if tree.winfo_width() > 20:
                tree.event_generate("<Configure>", width=tree.winfo_width(), height=tree.winfo_height())


    def _crear_input(self, master, row, label_text, unidad="", ayuda="", clave=None):
        lbl = ctk.CTkLabel(master, text=label_text, font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO, anchor="w")
        lbl.grid(row=row, column=0, sticky="w", pady=5)
        
        var = ctk.StringVar()
        if clave is not None:
            self.variables[clave] = var
            var.trace_add("write", self._on_datos_cambiados)
            
        # Input más compacto (height=30); `ayuda` es el valor por defecto como texto de ayuda
        entry = ctk.CTkEntry(master, border_width=1, border_color=COLOR_INPUT_BORDE,
                             fg_color=COLOR_INPUT_FONDO, text_color=COLOR_TEXTO_BLANCO,
                             corner_radius=6, height=30, placeholder_text=ayuda,
                             textvariable=var)
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

    def _on_datos_cambiados(self, *args):
        if self.datos_desactualizados:
            return # Ya está desactualizado, evitar loops y recálculos gráficos
            
        self.datos_desactualizados = True
        self.resultado = None
        self.lbl_error.configure(text="Cambiaste los datos: pulsa Calcular", text_color=COLOR_AVISO_INFO)
        self._pintar_resumen([(e, "-") for e in ETIQUETAS_RESUMEN_SIMPLE])
        self._pintar_avisos([])
        self._limpiar_tablas()
        self._limpiar_grafica()

    def _alternar_avanzados(self):
        if self.switch_avanzado.get():
            self.frame_avanzado.pack(fill="x", before=self.btn_calcular, pady=(5, 0))
        else:
            self.frame_avanzado.pack_forget()
        
        self.datos_desactualizados = False # reset state and force full clear
        self._on_datos_cambiados()

    def _calcular(self):
        """Lee los campos, calcula y pinta. Los errores de entrada se muestran en la vista."""
        # Temporalmente evitar que el cálculo active el trace por alguna razón (aunque solo leemos)
        valores = {clave: entry.get() for clave, entry in self.entradas.items()}
        avanzado = bool(self.switch_avanzado.get())
        
        self.datos_desactualizados = False # Quitamos bandera de error
        
        try:
            entrada = leer_entrada(valores, avanzado)
            resultado = TrompoEstrellaCalculator().calcular(entrada)
        except ValueError as exc:
            self.resultado = None
            self.lbl_error.configure(text=str(exc), text_color=COLOR_AVISO_ERROR)
            self._pintar_resumen([(e, "-") for e in ETIQUETAS_RESUMEN_SIMPLE])
            self._pintar_avisos([])
            self._limpiar_tablas()
            self._limpiar_grafica()
            return
            
        self.resultado = resultado
        self.lbl_error.configure(text="")
        self._pintar_resumen(formatear_resumen(resultado))
        self._pintar_avisos(resultado.avisos)
        self._pintar_tablas(resultado, entrada)
        self._pintar_grafica()

    def _limpiar_grafica(self):
        if self.figura_actual is not None:
            plt.close(self.figura_actual)
            self.figura_actual = None
        if self.canvas_widget is not None:
            self.canvas_widget.destroy()
            self.canvas_widget = None

    def _pintar_grafica(self):
        self._limpiar_grafica()
        if not self.resultado:
            return
            
        tema = {
            "fondo_figura": COLOR_GRAFICA_FONDO_FIGURA,
            "fondo_grafica": COLOR_GRAFICA_FONDO_EJES,
            "texto": COLOR_GRAFICA_TEXTO,
            "lineas": COLOR_GRAFICA_LINEAS,
            "acento": COLOR_ACENTO_NARANJA,
            "pestana": COLOR_GRAFICA_PESTANA
        }
        
        tipo = self.tipo_grafica_var.get()
        if tipo == "Moldes":
            self.figura_actual = figura_moldes(self.resultado, tema)
        else:
            self.figura_actual = figura_perfil(self.resultado, tema)
            
        canvas = FigureCanvasTkAgg(self.figura_actual, master=self.frame_canvas)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill="both")

    def _cambiar_grafica(self, *args):
        if not self.datos_desactualizados and self.resultado:
            self._pintar_grafica()

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

            row_frame.grid_rowconfigure(0, weight=1)
            row_frame.grid_columnconfigure(0, weight=2)
            row_frame.grid_columnconfigure(1, weight=1)

            # Labels sin pady, sticky nsew para que se centren solitos en el espacio pequeño
            lbl_izq = ctk.CTkLabel(row_frame, text=titulo, anchor="center", font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO)
            lbl_izq.grid(row=0, column=0, sticky="nsew", padx=5)
            
            # Divisor vertical
            ctk.CTkFrame(row_frame, width=1, fg_color="white").grid(row=0, column=0, sticky="nse", padx=0)

            lbl_der = ctk.CTkLabel(row_frame, text=valor, anchor="center", font=FONT_TEXTO_NORMAL, text_color=COLOR_TEXTO_BLANCO)
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
        # We replace this mock function with the actual Tabview integration
        pass

    def _configurar_estilo_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        # Obtenemos la fuente de la interfaz (es una tupla ej: ("Roboto", 14))
        font_str = f"{FONT_TEXTO_NORMAL[0]} {FONT_TEXTO_NORMAL[1]}"
        
        style.configure("Dark.Treeview",
                        background=COLOR_FONDO_APP,
                        foreground=COLOR_TEXTO_BLANCO,
                        fieldbackground=COLOR_FONDO_APP,
                        bordercolor=COLOR_INPUT_BORDE,
                        font=font_str,
                        rowheight=FONT_TEXTO_NORMAL[1] + 10)
        style.map("Dark.Treeview", background=[('selected', COLOR_ACENTO_MORADO)])
        style.configure("Dark.Treeview.Heading",
                        background=COLOR_INPUT_FONDO,
                        foreground=COLOR_TEXTO_BLANCO,
                        font=font_str,
                        relief="flat")
        style.map("Dark.Treeview.Heading", background=[('active', "#5c5c5c")])

    def _limpiar_tablas(self):
        for w in self.tab_widgets.values():
            w['lbl_resumen'].configure(text="")
            w['lbl_nota'].configure(text="")
            w['tabla_data'] = None
            tree = w['tree']
            tree.delete(*tree.get_children())
            tree["columns"] = []
            
            # Quitar binding previo si existe
            tree.unbind("<Configure>")

    def _pintar_tablas(self, resultado, entrada):
        self._limpiar_tablas()
        tablas = formatear_tablas(resultado, entrada)
        for tabla in tablas:
            w = self.tab_widgets[tabla.titulo]
            w['tabla_data'] = tabla
            w['lbl_resumen'].configure(text=tabla.resumen)
            if tabla.nota:
                w['lbl_nota'].configure(text=tabla.nota)
            else:
                w['lbl_nota'].configure(text="")
                
            tree = w['tree']
            tree["columns"] = tabla.encabezados
            tree["show"] = "headings"
            for col in tabla.encabezados:
                tree.heading(col, text=col, anchor="e")
                tree.column(col, anchor="e", width=100)
            
            tree.tag_configure("impar", background=COLOR_FONDO_APP)
            tree.tag_configure("par", background=COLOR_FILA_ALTERNADA)
            
            for i, fila in enumerate(tabla.filas):
                tag = "par" if i % 2 != 0 else "impar"
                tree.insert("", "end", values=fila, tags=(tag,))
                
            def _distribuir_columnas(event, t=tree, n_cols=len(tabla.encabezados)):
                if event.width > 20:
                    ancho = max(20, event.width // n_cols)
                    for c in t["columns"]:
                        t.column(c, width=ancho)
            
            tree.bind("<Configure>", _distribuir_columnas)

    def _copiar_tabla(self, nombre):
        tabla_data = self.tab_widgets[nombre]['tabla_data']
        if tabla_data:
            texto = tabla_a_texto(tabla_data)
            self.clipboard_clear()
            self.clipboard_append(texto)