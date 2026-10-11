import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

def _directorio_assets() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "app_flet", "assets", "visor3d")

class _ManejadorVisor(BaseHTTPRequestHandler):
    servidor_ref: Any = None

    def log_message(self, format, *args):
        # Silenciar logs en consola
        pass

    def do_GET(self):
        if self.path == "/api/escena":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            datos = self.servidor_ref.obtener_datos_escena() if self.servidor_ref else {}
            payload = json.dumps(datos, ensure_ascii=False).encode("utf-8")
            self.wfile.write(payload)
            return

        # Servir archivos estáticos de assets/visor3d
        base_dir = _directorio_assets()
        ruta_rel = self.path.lstrip("/").split("?")[0]
        if not ruta_rel or ruta_rel == "":
            ruta_rel = "visor.html"
            
        ruta_archivo = os.path.normpath(os.path.join(base_dir, ruta_rel))
        # Seguridad: evitar escapar de base_dir
        if not ruta_archivo.startswith(base_dir) or not os.path.exists(ruta_archivo) or os.path.isdir(ruta_archivo):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        ext = os.path.splitext(ruta_archivo)[1].lower()
        mimes = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }
        content_type = mimes.get(ext, "application/octet-stream")

        try:
            with open(ruta_archivo, "rb") as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except Exception:
            self.send_response(500)
            self.end_headers()

class ServidorVisor:
    def __init__(self, host: str = "127.0.0.1", puerto: int = 0):
        self.host = host
        self.puerto_solicitado = puerto
        self.puerto_real: int = 0
        self._servidor: Optional[HTTPServer] = None
        self._hilo: Optional[threading.Thread] = None
        self._datos_escena: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def actualizar_datos_escena(self, datos: Dict[str, Any]) -> None:
        with self._lock:
            self._datos_escena = datos

    def obtener_datos_escena(self) -> Dict[str, Any]:
        with self._lock:
            return self._datos_escena

    def iniciar(self) -> int:
        if self._servidor is not None:
            return self.puerto_real

        class HandlerConRef(_ManejadorVisor):
            pass
        HandlerConRef.servidor_ref = self

        self._servidor = HTTPServer((self.host, self.puerto_solicitado), HandlerConRef)
        self.puerto_real = self._servidor.server_port

        self._hilo = threading.Thread(target=self._servidor.serve_forever, daemon=True)
        self._hilo.start()
        return self.puerto_real

    @property
    def url(self) -> str:
        if self.puerto_real == 0:
            return ""
        return f"http://{self.host}:{self.puerto_real}/"

    def detener(self) -> None:
        if self._servidor:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._servidor = None
            self.puerto_real = 0

def exportar_visor_autocontenido(datos_escena: Dict[str, Any], ruta_salida_html: str) -> None:
    """Genera un archivo HTML autocontenido (three.js, controles y datos embebidos).
    
    Funciona 100 % fuera de línea al hacer doble clic en el explorador de archivos.
    """
    assets = _directorio_assets()
    with open(os.path.join(assets, "vendor", "three.min.js"), "r", encoding="utf-8") as f:
        three_js = f.read()
    with open(os.path.join(assets, "vendor", "OrbitControls.js"), "r", encoding="utf-8") as f:
        orbit_js = f.read()
    with open(os.path.join(assets, "visor.js"), "r", encoding="utf-8") as f:
        visor_js = f.read()
    with open(os.path.join(assets, "visor.html"), "r", encoding="utf-8") as f:
        html = f.read()

    # Reemplazar scripts externos por embebidos
    script_bundle = f"""
  <script>{three_js}</script>
  <script>{orbit_js}</script>
  <script>
    window.__DATOS_ESCENA_3D__ = {json.dumps(datos_escena, ensure_ascii=False)};
  </script>
  <script>{visor_js}</script>
"""
    # Reemplazar las etiquetas <script src=...> del final
    tags_a_reemplazar = """  <script src="/vendor/three.min.js"></script>
  <script src="/vendor/OrbitControls.js"></script>
  <script src="/visor.js"></script>"""
    
    if tags_a_reemplazar in html:
        html_autocontenido = html.replace(tags_a_reemplazar, script_bundle)
    else:
        # Fallback reemplazo genérico
        html_autocontenido = html.replace("</body>", f"{script_bundle}</body>")

    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida_html)), exist_ok=True)
    with open(ruta_salida_html, "w", encoding="utf-8") as f:
        f.write(html_autocontenido)
