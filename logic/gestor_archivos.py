import json
import os
from datetime import datetime

# Definimos dónde se guardarán los archivos
# Esto busca la ruta base del proyecto y añade la carpeta 'guardados'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_GUARDADOS = os.path.join(BASE_DIR, "guardados")

class GestorArchivos:
    def __init__(self):
        self._verificar_directorio()

    def _verificar_directorio(self):
        """Crea la carpeta 'guardados' si no existe."""
        if not os.path.exists(CARPETA_GUARDADOS):
            os.makedirs(CARPETA_GUARDADOS)

    def guardar_globo(self, datos_globo, nombre_archivo):
        """
        Guarda el diccionario del globo en un archivo JSON.
        nombre_archivo: string (ej. "mi_globo_01")
        """
        if not nombre_archivo.endswith('.json'):
            nombre_archivo += '.json'
            
        ruta_completa = os.path.join(CARPETA_GUARDADOS, nombre_archivo)
        
        # Agregamos fecha de modificación automática
        datos_globo['ultima_modificacion'] = datetime.now().isoformat()

        try:
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                json.dump(datos_globo, f, indent=4, ensure_ascii=False)
            return True, f"Guardado exitosamente en: {ruta_completa}"
        except Exception as e:
            return False, f"Error al guardar: {str(e)}"

    def cargar_globo(self, nombre_archivo):
        """Lee un JSON y devuelve el diccionario."""
        ruta_completa = os.path.join(CARPETA_GUARDADOS, nombre_archivo)
        
        if not os.path.exists(ruta_completa):
            return None, "El archivo no existe"

        try:
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, "Cargado correctamente"
        except Exception as e:
            return None, f"Error al leer archivo: {str(e)}"

    def listar_archivos(self):
        """Devuelve una lista de todos los globos guardados."""
        archivos = []
        if os.path.exists(CARPETA_GUARDADOS):
            for f in os.listdir(CARPETA_GUARDADOS):
                if f.endswith('.json'):
                    archivos.append(f)
        return archivos