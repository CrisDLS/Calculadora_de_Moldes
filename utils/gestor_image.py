# utils/gestor_imagenes.py

import customtkinter as ctk
from PIL import Image
import os
import sys

class GestorImagenes:
    def __init__(self):
        # CONFIGURACIÓN DE IMÁGENES (Tu diccionario adaptado)
        # Clave: {Archivo, Tamaño Sidebar, Tamaño Header}
        self.config_imagenes = {
            "inicio":     {"file": "inicio.png", "sidebar": (30, 30), "header": (45, 40)},
            "moldes":     {"file": "moldes.png", "sidebar": (30, 30), "header": (40, 45)},
            "guardados":  {"file": "guardados.png", "sidebar": (30, 30), "header": (40, 40)},
            "info":       {"file": "info.png", "sidebar": (30, 30), "header": (40, 40)},
            # Agrega aquí tus otros modos...

            "globo_central": {"file": "GloboTE.png", "sidebar": (200, 200), "header": (200, 200)},
        }
        
        # Cache para no cargar la misma imagen dos veces si no es necesario
        self._cache_imagenes = {}

    def _resource_path(self, relative_path):
        """La función estrella: maneja rutas para desarrollo y .exe"""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            # Subimos niveles para salir de 'utils' y llegar a la raíz
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_path, "recursos", relative_path)

    def obtener_imagen(self, clave, tipo="sidebar"):
        """
        clave: 'inicio', 'moldes', etc.
        tipo: 'sidebar' o 'header'
        """
        if clave not in self.config_imagenes:
            return None

        datos = self.config_imagenes[clave]
        nombre_archivo = datos["file"]
        
        # Seleccionamos el tamaño según lo que pidas
        size = datos["sidebar"] if tipo == "sidebar" else datos["header"]
        
        # Identificador único para el cache (ej: "inicio_sidebar")
        cache_key = f"{clave}_{tipo}"

        # Si ya la cargamos antes, la devolvemos directo (Optimización)
        if cache_key in self._cache_imagenes:
            return self._cache_imagenes[cache_key]

        # Si no, la cargamos
        full_path = self._resource_path(nombre_archivo)
        try:
            img_pil = Image.open(full_path)
            imagen_ctk = ctk.CTkImage(
                light_image=img_pil,
                dark_image=img_pil,
                size=size
            )
            # Guardamos en cache y retornamos
            self._cache_imagenes[cache_key] = imagen_ctk
            return imagen_ctk

        except FileNotFoundError:
            print(f"⚠️ Error: No se encontró {full_path}")
            return None