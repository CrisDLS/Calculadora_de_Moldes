from typing import Dict, List, Optional
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput, BalloonCalculationResult
from logic.exportacion.estilos import EstiloSvg, PANTALLA_OSCURO
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.pintura import EsquemaPintura
from logic.exportacion.visor3d import ServidorVisor
from logic.diseno.lienzo import Diseno
from presentacion.trompo_estrella import TablaMolde

from app_flet.controlador.modelos import TarjetaResumen, AvisoFlet, ViewModelTrompo
from app_flet.controlador.entradas import ControladorEntradasMixin
from app_flet.controlador.hoja import ControladorHojaMixin
from app_flet.controlador.diseno import ControladorDisenoMixin
from app_flet.controlador.vista3d import Controlador3DMixin
from app_flet.controlador.proyecto import ControladorProyectoMixin


class ControladorTrompo(
    ControladorEntradasMixin,
    ControladorHojaMixin,
    ControladorDisenoMixin,
    Controlador3DMixin,
    ControladorProyectoMixin,
):
    """Fachada unificada del controlador de la aplicación."""

    def __init__(self, estilo_svg: EstiloSvg = PANTALLA_OSCURO):
        self._init_estado_calculo(estilo_svg)
        self._init_estado_entradas()
        self._init_estado_hoja()
        self._init_estado_diseno_y_3d()

    def _init_estado_calculo(self, estilo_svg: EstiloSvg) -> None:
        self.calculadora = TrompoEstrellaCalculator()
        self.resultado: Optional[BalloonCalculationResult] = None
        self.entrada_actual: Optional[BalloonInput] = None
        self.desactualizado = False
        self.mensaje_error: Optional[str] = None
        self.estilo_svg: EstiloSvg = estilo_svg

        # Tablas y SVGs expuestos
        self.tablas: List[TablaMolde] = []
        self.svg_conjunto: str = ""
        self.svg_superior: str = ""
        self.svg_pico: str = ""
        self.svg_inferior: str = ""
        self.svg_perfil: str = ""
        self.svg_hoja: str = ""
        self.svg_diseno: str = ""

    def _init_estado_entradas(self) -> None:
        self.altura = "950"
        self.gajos = "30"
        self.hileras = "2"
        self.costura = "1"
        self.avanzado = False
        self.boca = ""
        self.pestana = ""
        self.diametro_mecha = ""
        self.peso_mecha = ""
        self.alambre = ""
        self.varillas = ""
        self.altura_llama = ""
        self.holgura = ""

    def _init_estado_hoja(self) -> None:
        self.esquema_modo: str = "repeticion"
        self.esquema_tam_grupo: int = 5
        self.esquema_ciclo_texto: str = "0, 1, 2E, 1E"
        self.hoja_tipo: str = "carta"
        self.hoja_escala: str = "auto"
        self.hoja_pieza: str = "superior"
        self.hoja_lienzo: str = "abanico"
        self.hoja_dibujar: str = "completo"
        self.esquema_pico: EsquemaDisenoPico = EsquemaDisenoPico()
        self.aviso_hoja: Optional[str] = None

        self.config_secciones: Dict[str, ConfigSeccion] = {
            "superior": ConfigSeccion(
                seccion="superior",
                esquema=EsquemaDiseno(modo="repeticion", tam_grupo=5),
                dibujar="completo",
                lienzo="abanico",
                escala="auto",
            ),
            "inferior": ConfigSeccion(
                seccion="inferior",
                esquema=EsquemaDiseno(modo="repeticion", tam_grupo=5),
                dibujar="completo",
                lienzo="abanico",
                escala="auto",
            ),
            "pico": ConfigSeccion(
                seccion="pico",
                esquema_pico=EsquemaDisenoPico(),
                dibujar="completo",
                lienzo="abanico",
                escala="auto",
            ),
        }

    def _init_estado_diseno_y_3d(self) -> None:
        self.disenos: Dict[str, Diseno] = {}
        self.diseno_seccion: str = "superior"
        self.diseno_variante: str = "A"
        self.diseno_lienzo_modo: str = "completo"
        self.diseno_pico_modo: str = "una_cara"
        self.capa_seleccionada_id: Optional[str] = None
        self.mantener_proporcion: bool = True
        self.recursos_faltantes: List[str] = []
        self.diseno_ver_cuadricula: bool = True
        self.diseno_ver_rotulos: bool = False
        self.diseno_ver_costuras: bool = True
        self.diseno_mostrar_reflejo: bool = True

        self.nombre_proyecto: str = "Sin título"
        self.ruta_proyecto: Optional[str] = None
        self.sin_guardar: bool = False

        self.pintura: EsquemaPintura = EsquemaPintura()
        self.pliegos_por_paquete: int = 100
        self.pliego_ancho: float = 50.0
        self.pliego_alto: float = 70.0
        self.servidor_3d: Optional[ServidorVisor] = None


__all__ = [
    "ControladorTrompo",
    "ViewModelTrompo",
    "TarjetaResumen",
    "AvisoFlet",
]
