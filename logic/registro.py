import sys
import time
import logging
import threading
import asyncio
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, Callable

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "globos.log"

logger = logging.getLogger("globos")


def inicializar_registro() -> logging.Logger:
    """Configura logging rotativo a logs/globos.log (1 MB x 3, UTF-8) en nivel INFO."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Evitar duplicar handlers si se llama varias veces
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=1024 * 1024,  # 1 MB
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Hooks de excepciones no controladas
    def _sys_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Excepción no controlada en hilo principal:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = _sys_excepthook

    if hasattr(threading, "excepthook"):
        def _threading_excepthook(args):
            logger.error(f"Excepción no controlada en hilo {args.thread.name}:", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        threading.excepthook = _threading_excepthook

    return logger


def registrar_excepcion_asyncio(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]):
    """Manejador de excepciones no controladas en asyncio."""
    msg = context.get("message", "Excepción no controlada en bucle asyncio")
    exc = context.get("exception")
    if exc:
        logger.error(f"{msg}:", exc_info=exc)
    else:
        logger.error(f"{msg}: {context}")


class MonitorLatido:
    """Monitor de latido (heartbeat) que vigila la capacidad de respuesta del bucle de UI."""
    def __init__(
        self,
        intervalo_s: float = 1.0,
        umbral_alerta_s: float = 2.0,
        obtener_estado_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        obtener_pagina_fn: Optional[Callable[[], Any]] = None,
    ):
        self.intervalo_s = intervalo_s
        self.umbral_alerta_s = umbral_alerta_s
        self.obtener_estado_fn = obtener_estado_fn
        self.obtener_pagina_fn = obtener_pagina_fn
        self.ultimo_latido_ts = time.time()
        self._activo = False
        self._hilo: Optional[threading.Thread] = None

    def registrar_latido(self):
        """Marca de tiempo que actualiza el hilo de la UI cuando está viva."""
        self.ultimo_latido_ts = time.time()

    def iniciar(self):
        if self._activo:
            return
        self._activo = True
        self.ultimo_latido_ts = time.time()
        self._hilo = threading.Thread(target=self._bucle_monitor, name="MonitorLatido", daemon=True)
        self._hilo.start()

    def detener(self):
        self._activo = False

    def _bucle_monitor(self):
        while self._activo:
            time.sleep(self.intervalo_s)
            ahora = time.time()

            # Intentar programar latido en bucle de UI si hay página disponible
            if self.obtener_pagina_fn:
                try:
                    page = self.obtener_pagina_fn()
                    if page and hasattr(page, "run_thread"):
                        page.run_thread(self.registrar_latido)
                except Exception:
                    pass

            delta = ahora - self.ultimo_latido_ts
            if delta > self.umbral_alerta_s:
                estado_str = ""
                if self.obtener_estado_fn:
                    try:
                        st = self.obtener_estado_fn()
                        estado_str = f" · Banderas: {st}"
                    except Exception as e:
                        estado_str = f" · Error obteniendo estado: {e}"
                logger.warning(f"interfaz sin responder {delta:.1f} s{estado_str}")
