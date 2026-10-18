from dataclasses import dataclass, field
from typing import Dict, List, Optional
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.lienzo import CapaDiseno, Diseno
from logic.diseno.pintura import EsquemaPintura
from logic.diseno.compra import ItemCompra
from presentacion.trompo_estrella import TablaMolde


@dataclass
class TarjetaResumen:
    etiqueta: str
    valor: str


@dataclass
class AvisoFlet:
    texto: str
    clase: str  # "ok", "aviso", "error", "info"


@dataclass
class ViewModelTrompo:
    tarjetas: List[TarjetaResumen]
    avisos: List[AvisoFlet]
    mensaje_error: Optional[str]
    desactualizado: bool
    tablas: List[TablaMolde] = field(default_factory=list)
    svg_conjunto: str = ""
    svg_superior: str = ""
    svg_pico: str = ""
    svg_inferior: str = ""
    svg_perfil: str = ""
    # Hoja de trazo y esquema
    svg_hoja: str = ""
    esquema_error: Optional[str] = None
    resumen_esquema: List[str] = field(default_factory=list)
    aviso_hoja: Optional[str] = None
    resumen_pico_linea: Optional[str] = None
    esquema_pico: Optional[EsquemaDisenoPico] = None
    # Proyecto
    nombre_proyecto: str = "Sin título"
    ruta_proyecto: Optional[str] = None
    sin_guardar: bool = False
    # Vista 3D y lista de compra (F4)
    items_compra: List[ItemCompra] = field(default_factory=list)
    pintura: Optional[EsquemaPintura] = None
    url_visor_3d: str = ""
    # Diseño sobre el abanico (F6a)
    svg_diseno: str = ""
    diseno_activo: Optional[Diseno] = None
    capas_diseno: List[CapaDiseno] = field(default_factory=list)
    capa_seleccionada_id: Optional[str] = None
    diseno_seccion: str = "superior"
    diseno_variante: str = "A"
    diseno_lienzo_modo: str = "completo"
    mantener_proporcion: bool = True
    recursos_faltantes: List[str] = field(default_factory=list)
    diseno_ver_cuadricula: bool = True
    diseno_ver_rotulos: bool = False
    diseno_ver_costuras: bool = True
    diseno_mostrar_reflejo: bool = True
    # Configuración independiente por sección (Parte 1)
    config_secciones: Dict[str, ConfigSeccion] = field(default_factory=dict)
    puede_usar_mitad: bool = True
    motivo_no_mitad: str = ""
    # Control de visualización de texturas en visor 3D
    mostrar_diseno_3d: bool = True
    hay_diseno_visible: bool = False
