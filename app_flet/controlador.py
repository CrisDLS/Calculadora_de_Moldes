# app_flet/controlador.py
import os
import warnings
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Union
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput, BalloonCalculationResult, Condiciones
from logic.exportacion.estilos import EstiloSvg, PANTALLA_OSCURO, IMPRESION
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto, svg_hoja
from logic.exportacion.svg_abanico import svg_abanico
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_perfil import svg_perfil
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.paquete import parsear_ciclo, resumen_esquema, generar_paquete, guardar_paquete
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto
from logic.diseno.diseno_pico import EsquemaDisenoPico, ResumenPico, resumen_pico
from presentacion.trompo_estrella import (
    leer_entrada,
    formatear_resumen,
    clasificar_aviso,
    formatear_tablas,
    TablaMolde,
)

from logic.diseno.pintura import EsquemaPintura
from logic.diseno.paleta import ColorPapel, cargar_catalogo, color_por_id
from logic.diseno.compra import ItemCompra, lista_de_compra
from logic.exportacion.escena3d import escena_a_dict
from logic.exportacion.visor3d import ServidorVisor, exportar_visor_autocontenido
from logic.diseno.lienzo import Diseno, CapaDiseno, importar_recurso, ajustar_capa
from logic.exportacion.svg_diseno import svg_gajo, exportar_diseno
from logic.geometria.abanico import pieza_a_geometria_plana
from pathlib import Path

@dataclass
class TarjetaResumen:
    etiqueta: str
    valor: str

@dataclass
class AvisoFlet:
    texto: str
    clase: str  # "ok", "aviso", "error", "info"

from logic.diseno.config_seccion import ConfigSeccion

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


class ControladorTrompo:
    def __init__(self, estilo_svg: EstiloSvg = PANTALLA_OSCURO):
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

        # Estado de diseño sobre el abanico (F6a)
        self.disenos: Dict[str, Diseno] = {}
        self.diseno_seccion: str = "superior"
        self.diseno_variante: str = "A"
        self.diseno_lienzo_modo: str = "completo"
        self.capa_seleccionada_id: Optional[str] = None
        self.mantener_proporcion: bool = True
        self.recursos_faltantes: List[str] = []
        self.diseno_ver_cuadricula: bool = True
        self.diseno_ver_rotulos: bool = False
        self.diseno_ver_costuras: bool = True
        self.diseno_mostrar_reflejo: bool = True

        # Estado de los campos de entrada
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

        # Estado de diseño / hoja de trazo (F3 y F5)
        self.esquema_modo: str = "repeticion"
        self.esquema_tam_grupo: int = 5
        self.esquema_ciclo_texto: str = "0, 1, 2E, 1E"
        self.hoja_tipo: str = "carta"
        self.hoja_escala: str = "auto"
        self.hoja_pieza: str = "superior"  # "superior", "pico", "inferior"
        self.hoja_lienzo: str = "abanico"   # "abanico" | "separadas"
        self.hoja_dibujar: str = "completo" # "completo" | "mitad"
        self.esquema_pico: EsquemaDisenoPico = EsquemaDisenoPico()

        # Configuración independiente por sección (Parte 1)
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

        self.aviso_hoja: Optional[str] = None

        # Estado del proyecto
        self.nombre_proyecto: str = "Sin título"
        self.ruta_proyecto: Optional[str] = None
        self.sin_guardar: bool = False

        # Estado de pintura y visor 3D (F4)
        self.pintura: EsquemaPintura = EsquemaPintura()
        self.pliegos_por_paquete: int = 100
        self.pliego_ancho: float = 50.0
        self.pliego_alto: float = 70.0
        self.servidor_3d: Optional[ServidorVisor] = None

    def obtener_servidor_3d(self) -> ServidorVisor:
        if self.servidor_3d is None:
            self.servidor_3d = ServidorVisor()
            self.servidor_3d.iniciar()
        self._actualizar_servidor_3d()
        return self.servidor_3d

    def _actualizar_servidor_3d(self):
        if self.servidor_3d and self.resultado and self.entrada_actual:
            try:
                esq = self._construir_esquema()
                escena = escena_a_dict(
                    self.entrada_actual,
                    self.resultado,
                    esquema_pintura=self.pintura,
                    esquema_diseno=esq
                )
                self.servidor_3d.actualizar_datos_escena(escena)
            except Exception:
                pass

    def exportar_visor_3d(self, ruta: str) -> None:
        if not (self.resultado and self.entrada_actual):
            raise ValueError("Calcula el modelo antes de exportar el visor 3D")
        esq = self._construir_esquema()
        escena = escena_a_dict(
            self.entrada_actual,
            self.resultado,
            esquema_pintura=self.pintura,
            esquema_diseno=esq
        )
        exportar_visor_autocontenido(escena, ruta)

    def actualizar_pintura(
        self,
        color_sup: Optional[str] = None,
        color_pic: Optional[str] = None,
        color_inf: Optional[str] = None,
        pintura_completa: Optional[EsquemaPintura] = None,
    ):
        if pintura_completa is not None:
            self.pintura = pintura_completa
        else:
            if color_sup is not None:
                self.pintura.color_superior = color_sup
                if self.pintura.colores_superior:
                    self.pintura.colores_superior[0] = color_sup
                else:
                    self.pintura.colores_superior = [color_sup]
            if color_pic is not None:
                self.pintura.color_pico = color_pic
                self.pintura.variante_a.color_0 = color_pic
            if color_inf is not None:
                self.pintura.color_inferior = color_inf
                if self.pintura.colores_inferior:
                    self.pintura.colores_inferior[0] = color_inf
                else:
                    self.pintura.colores_inferior = [color_inf]
        self.sin_guardar = True
        self._actualizar_servidor_3d()

    def marcar_desactualizado(self):
        self.sin_guardar = True
        if self.resultado is not None:
            self.desactualizado = True
            self._vaciar_datos_calculados()

    def marcar_cambio_diseno(self):
        self.sin_guardar = True
        self._generar_svg_hoja()

    def actualizar_campo(self, campo: str, valor: Any):
        if hasattr(self, campo):
            setattr(self, campo, valor)
            self.marcar_desactualizado()

    def actualizar_esquema(
        self,
        modo: Optional[str] = None,
        tam_grupo: Optional[int] = None,
        ciclo_texto: Optional[str] = None,
    ):
        if modo is not None:
            self.esquema_modo = modo
        if tam_grupo is not None:
            self.esquema_tam_grupo = tam_grupo
        if ciclo_texto is not None:
            self.esquema_ciclo_texto = ciclo_texto

        sec = self.hoja_pieza if self.hoja_pieza != "pico" else "superior"
        cfg = self.obtener_config_seccion(sec)
        if self.esquema_modo == "personalizado":
            try:
                ciclo = parsear_ciclo(self.esquema_ciclo_texto)
                cfg.esquema = EsquemaDiseno("personalizado", len(ciclo), ciclo=ciclo)
            except Exception:
                cfg.esquema = EsquemaDiseno("personalizado", 1, ciclo=None)
        else:
            try:
                cfg.esquema = EsquemaDiseno(self.esquema_modo, int(self.esquema_tam_grupo))
            except Exception:
                cfg.esquema = None
        puede, _ = cfg.puede_usar_mitad()
        if not puede and cfg.dibujar == "mitad":
            cfg.dibujar = "completo"
            self.hoja_dibujar = "completo"
        self.marcar_cambio_diseno()

    def actualizar_opciones_hoja(
        self,
        pieza: Optional[str] = None,
        tipo: Optional[str] = None,
        escala: Optional[str] = None,
        lienzo: Optional[str] = None,
        dibujar: Optional[str] = None,
    ):
        if pieza is not None:
            self.hoja_pieza = pieza
            cfg = self.obtener_config_seccion(pieza)
            if cfg.esquema:
                self.esquema_modo = cfg.esquema.modo
                self.esquema_tam_grupo = cfg.esquema.tam_grupo
                if cfg.esquema.ciclo:
                    self.esquema_ciclo_texto = ", ".join(f"{m}{'E' if e else ''}" for m, e in cfg.esquema.ciclo)
            self.hoja_lienzo = cfg.lienzo
            self.hoja_dibujar = cfg.dibujar
            self.hoja_escala = str(cfg.escala)
        if tipo is not None:
            self.hoja_tipo = tipo

        sec = self.hoja_pieza
        cfg = self.obtener_config_seccion(sec)
        if escala is not None:
            self.hoja_escala = escala
            cfg.escala = escala
        if lienzo is not None:
            self.hoja_lienzo = lienzo
            cfg.lienzo = lienzo
        if dibujar is not None:
            if sec == "pico":
                cfg.dibujar = "completo"
                self.hoja_dibujar = "completo"
            else:
                puede, _ = cfg.puede_usar_mitad()
                if dibujar == "mitad" and not puede:
                    cfg.dibujar = "completo"
                    self.hoja_dibujar = "completo"
                else:
                    cfg.dibujar = dibujar
                    self.hoja_dibujar = dibujar
        self.marcar_cambio_diseno()

    def actualizar_esquema_pico(self, modo_repeticion: Optional[str] = None):
        if modo_repeticion is not None:
            self.esquema_pico.modo_repeticion = modo_repeticion
            self.esquema_pico.usar_variante_b = (modo_repeticion != "todas_a")
            if "pico" in self.config_secciones and self.config_secciones["pico"].esquema_pico:
                self.config_secciones["pico"].esquema_pico.modo_repeticion = modo_repeticion
                self.config_secciones["pico"].esquema_pico.usar_variante_b = (modo_repeticion != "todas_a")
        self.marcar_cambio_diseno()

    def _vaciar_datos_calculados(self):
        self.tablas = []
        self.svg_conjunto = ""
        self.svg_superior = ""
        self.svg_pico = ""
        self.svg_inferior = ""
        self.svg_perfil = ""
        self.svg_hoja = ""
        self.aviso_hoja = None

    def _generar_svgs(self):
        if self.resultado and self.entrada_actual:
            self.svg_conjunto = svg_conjunto(self.resultado, self.entrada_actual, escala=10.0, estilo=self.estilo_svg)
            self.svg_superior = svg_pieza(self.resultado, self.entrada_actual, "superior", escala=10.0, estilo=self.estilo_svg)
            self.svg_pico = svg_pieza(self.resultado, self.entrada_actual, "pico", escala=10.0, estilo=self.estilo_svg)
            self.svg_inferior = svg_pieza(self.resultado, self.entrada_actual, "inferior", escala=10.0, estilo=self.estilo_svg)
            perf = perfil_armado(self.entrada_actual, self.resultado, mostrar_picos_al_borde=True)
            self.svg_perfil = svg_perfil(perf, estilo=self.estilo_svg, escala=10.0)
            self._generar_svg_hoja()

    def _construir_esquema(self, seccion: Optional[str] = None) -> EsquemaDiseno:
        if seccion is not None and seccion != self.hoja_pieza:
            cfg = self.config_secciones.get(seccion)
            if cfg and cfg.esquema:
                return cfg.esquema
        if self.esquema_modo == "personalizado":
            ciclo = parsear_ciclo(self.esquema_ciclo_texto)
            return EsquemaDiseno("personalizado", len(ciclo), ciclo=ciclo)
        else:
            return EsquemaDiseno(self.esquema_modo, int(self.esquema_tam_grupo))

    def _generar_svg_hoja(self):
        self.aviso_hoja = None
        if not (self.resultado and self.entrada_actual and not self.desactualizado):
            self.svg_hoja = ""
            return

        try:
            sec = self.hoja_pieza
            cfg = self.obtener_config_seccion(sec)
            esq = cfg.esquema if (cfg and cfg.esquema) else self._construir_esquema(sec)
            escala_val = "auto" if str(cfg.escala).lower() == "auto" else float(cfg.escala)
            dibujar_val = cfg.dibujar

            with warnings.catch_warnings(record=True) as w_list:
                warnings.simplefilter("always")
                if cfg.lienzo == "abanico":
                    self.svg_hoja = svg_abanico(
                        resultado=self.resultado,
                        entrada=self.entrada_actual,
                        seccion=sec,
                        esquema=esq,
                        escala=escala_val,
                        hoja=self.hoja_tipo,
                        estilo=IMPRESION,
                        dibujar=dibujar_val,
                    )
                else:
                    self.svg_hoja = svg_hoja(
                        resultado=self.resultado,
                        entrada=self.entrada_actual,
                        seccion=sec,
                        esquema=esq,
                        escala=escala_val,
                        hoja=self.hoja_tipo,
                        estilo=IMPRESION,
                    )
                if w_list:
                    self.aviso_hoja = str(w_list[-1].message)
        except Exception:
            self.svg_hoja = ""

    def cambiar_estilo(self, estilo: EstiloSvg) -> ViewModelTrompo:
        self.estilo_svg = estilo
        if self.resultado and self.entrada_actual and not self.desactualizado:
            self._generar_svgs()
        return self.get_view_model()

    def limpiar(self):
        self.resultado = None
        self.entrada_actual = None
        self.desactualizado = False
        self.mensaje_error = None
        self._vaciar_datos_calculados()

    def calcular(self) -> ViewModelTrompo:
        self.limpiar()
        
        datos = {
            "altura": self.altura,
            "gajos": self.gajos,
            "hileras": self.hileras,
            "costura": self.costura
        }
        
        if self.avanzado:
            if self.boca: datos["diametro_boca"] = self.boca
            if self.pestana: datos["pestana_boca"] = self.pestana
            if self.diametro_mecha: datos["diametro_mecha"] = self.diametro_mecha
            if self.peso_mecha: datos["masa_mecha_g"] = self.peso_mecha
            if self.alambre: datos["alambre_mm"] = self.alambre
            if self.varillas: datos["varillas"] = self.varillas
            if self.altura_llama: datos["altura_llama"] = self.altura_llama
            if self.holgura: datos["holgura_min"] = self.holgura

        try:
            self.entrada_actual = leer_entrada(datos, self.avanzado)
            self.resultado = self.calculadora.calcular(self.entrada_actual)
            
            # Generar tablas y SVGs
            self.tablas = formatear_tablas(self.resultado, self.entrada_actual)
            self._generar_svgs()
            self._actualizar_svg_diseno()
            self._actualizar_servidor_3d()
            self.sin_guardar = True
        except ValueError as e:
            self.mensaje_error = str(e)

        return self.get_view_model()

    # --- Métodos de Proyecto (F3 y Parte 1) ---
    def nuevo(self):
        self.limpiar()
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

        self.esquema_modo = "repeticion"
        self.esquema_tam_grupo = 5
        self.esquema_ciclo_texto = "0, 1, 2E, 1E"
        self.hoja_tipo = "carta"
        self.hoja_escala = "auto"
        self.hoja_pieza = "superior"
        self.hoja_lienzo = "abanico"
        self.hoja_dibujar = "completo"
        self.esquema_pico = EsquemaDisenoPico()

        self.config_secciones = {
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

        self.disenos = {}
        self.capa_seleccionada_id = None
        self.svg_diseno = ""
        self.recursos_faltantes = []

        self.nombre_proyecto = "Sin título"
        self.ruta_proyecto = None
        self.sin_guardar = False

    def obtener_config_seccion(self, seccion: Optional[str] = None) -> ConfigSeccion:
        sec = seccion or self.diseno_seccion
        if sec not in self.config_secciones:
            self.config_secciones[sec] = ConfigSeccion(seccion=sec)
        return self.config_secciones[sec]

    def cambiar_seccion_hoja(self, seccion: str) -> None:
        self.hoja_pieza = seccion
        cfg = self.obtener_config_seccion(seccion)
        if cfg.esquema:
            self.esquema_modo = cfg.esquema.modo
            self.esquema_tam_grupo = cfg.esquema.tam_grupo
            if cfg.esquema.ciclo:
                self.esquema_ciclo_texto = ", ".join(f"{m}{'E' if e else ''}" for m, e in cfg.esquema.ciclo)
        self.hoja_lienzo = cfg.lienzo
        self.hoja_dibujar = cfg.dibujar
        self.hoja_escala = str(cfg.escala)
        self._generar_svg_hoja()

    def cambiar_esquema_seccion(self, seccion: str, modo: str, tam_grupo: int, ciclo_texto: str = "") -> None:
        cfg = self.obtener_config_seccion(seccion)
        if cfg.seccion == "pico":
            return
        if modo == "personalizado":
            ciclo = parsear_ciclo(ciclo_texto)
            cfg.esquema = EsquemaDiseno("personalizado", len(ciclo), ciclo=ciclo)
        else:
            cfg.esquema = EsquemaDiseno(modo, int(tam_grupo))
        puede, _ = cfg.puede_usar_mitad()
        if not puede and cfg.dibujar == "mitad":
            cfg.dibujar = "completo"
        if self.hoja_pieza == seccion:
            self.esquema_modo = modo
            self.esquema_tam_grupo = tam_grupo
            if ciclo_texto:
                self.esquema_ciclo_texto = ciclo_texto
            self.hoja_dibujar = cfg.dibujar
        if self.diseno_seccion == seccion:
            self.diseno_lienzo_modo = cfg.dibujar
        self.sin_guardar = True
        self._generar_svg_hoja()
        self._actualizar_svg_diseno()

    def cambiar_dibujar_seccion(self, seccion: str, dibujar: str) -> None:
        cfg = self.obtener_config_seccion(seccion)
        if cfg.seccion == "pico":
            cfg.dibujar = "completo"
        else:
            puede, _ = cfg.puede_usar_mitad()
            if dibujar == "mitad" and not puede:
                cfg.dibujar = "completo"
            else:
                cfg.dibujar = dibujar
        if self.hoja_pieza == seccion:
            self.hoja_dibujar = cfg.dibujar
        if self.diseno_seccion == seccion:
            self.diseno_lienzo_modo = cfg.dibujar
        self.sin_guardar = True
        self._generar_svg_hoja()
        self._actualizar_svg_diseno()

    def cambiar_lienzo_seccion(self, seccion: str, lienzo: str) -> None:
        cfg = self.obtener_config_seccion(seccion)
        cfg.lienzo = lienzo
        if self.hoja_pieza == seccion:
            self.hoja_lienzo = lienzo
        self.sin_guardar = True
        self._generar_svg_hoja()

    def cambiar_escala_seccion(self, seccion: str, escala: Union[str, int, float]) -> None:
        cfg = self.obtener_config_seccion(seccion)
        cfg.escala = escala
        if self.hoja_pieza == seccion:
            self.hoja_escala = str(escala)
        self.sin_guardar = True
        self._generar_svg_hoja()

    def copiar_configuracion_seccion(self, origen: str, destino: str) -> None:
        if origen not in self.config_secciones or destino not in self.config_secciones:
            return
        self.config_secciones[destino].copiar_desde(self.config_secciones[origen])
        if self.hoja_pieza == destino:
            self.cambiar_seccion_hoja(destino)
        if self.diseno_seccion == destino:
            self.diseno_lienzo_modo = self.config_secciones[destino].dibujar
        self.sin_guardar = True
        self._generar_svg_hoja()
        self._actualizar_svg_diseno()

    def sincronizar_conos(self, origen: str = "superior") -> None:
        destino = "inferior" if origen == "superior" else "superior"
        self.copiar_configuracion_seccion(origen, destino)

    def a_proyecto(self) -> Proyecto:
        datos = {
            "altura": self.altura,
            "gajos": self.gajos,
            "hileras": self.hileras,
            "costura": self.costura
        }
        if self.avanzado:
            if self.boca: datos["diametro_boca"] = self.boca
            if self.pestana: datos["pestana_boca"] = self.pestana
            if self.diametro_mecha: datos["diametro_mecha"] = self.diametro_mecha
            if self.peso_mecha: datos["masa_mecha_g"] = self.peso_mecha
            if self.alambre: datos["alambre_mm"] = self.alambre
            if self.varillas: datos["varillas"] = self.varillas
            if self.altura_llama: datos["altura_llama"] = self.altura_llama
            if self.holgura: datos["holgura_min"] = self.holgura

        try:
            ent = leer_entrada(datos, self.avanzado)
        except Exception:
            ent = BalloonInput(float(self.altura or 950), int(self.gajos or 30), int(self.hileras or 2), float(self.costura or 1))

        esq_sup = self.obtener_config_seccion("superior").esquema

        configs_a_guardar = {}
        for k, v in self.config_secciones.items():
            configs_a_guardar[k] = ConfigSeccion.from_dict(v.a_dict())

        return Proyecto(
            version=2,
            nombre=self.nombre_proyecto,
            entrada=ent,
            condiciones=Condiciones(pliego_cm=(float(self.pliego_ancho), float(self.pliego_alto))),
            esquema=esq_sup,
            notas="",
            hoja=self.hoja_tipo,
            escala=self.hoja_escala,
            pintura=self.pintura,
            pliegos_por_paquete=self.pliegos_por_paquete,
            esquema_pico=self.config_secciones["pico"].esquema_pico,
            disenos=self.disenos,
            config_secciones=configs_a_guardar,
        )

    def desde_proyecto(self, proy: Proyecto, ruta: Optional[str] = None):
        self.limpiar()
        ent = proy.entrada
        self.altura = str(ent.altura_cuerpo)
        self.gajos = str(ent.num_gajos)
        self.hileras = str(ent.num_hileras_picos)
        self.costura = str(ent.ancho_costura)
        self.avanzado = bool(ent.usar_parametros_avanzados)

        self.boca = str(ent.diametro_boca) if ent.diametro_boca is not None else ""
        self.pestana = str(ent.pestana_boca) if ent.pestana_boca else ""
        self.diametro_mecha = str(ent.diametro_mecha) if ent.diametro_mecha is not None else ""
        self.peso_mecha = str(ent.masa_mecha_g) if ent.masa_mecha_g is not None else ""
        self.alambre = str(ent.alambre_mm) if ent.alambre_mm is not None else ""
        self.varillas = str(ent.varillas) if ent.varillas is not None else ""
        self.altura_llama = str(ent.altura_llama) if ent.altura_llama is not None else ""
        self.holgura = str(ent.holgura_min) if ent.holgura_min is not None else ""

        # Restaurar config_secciones
        if getattr(proy, "config_secciones", None):
            self.config_secciones = {}
            for k, v in proy.config_secciones.items():
                if isinstance(v, ConfigSeccion):
                    self.config_secciones[k] = ConfigSeccion.from_dict(v.a_dict())
                elif isinstance(v, dict):
                    self.config_secciones[k] = ConfigSeccion.from_dict(v)

            cfg_sup = self.config_secciones.get("superior")
            if cfg_sup and cfg_sup.esquema:
                self.esquema_modo = cfg_sup.esquema.modo
                self.esquema_tam_grupo = cfg_sup.esquema.tam_grupo
                if cfg_sup.esquema.ciclo:
                    self.esquema_ciclo_texto = ", ".join(f"{m}{'E' if e else ''}" for m, e in cfg_sup.esquema.ciclo)
                self.hoja_dibujar = cfg_sup.dibujar
                self.hoja_lienzo = cfg_sup.lienzo
        elif proy.esquema:
            self.esquema_modo = proy.esquema.modo
            self.esquema_tam_grupo = proy.esquema.tam_grupo
            if proy.esquema.ciclo:
                self.esquema_ciclo_texto = ", ".join(
                    f"{m}{'E' if esp else ''}" for m, esp in proy.esquema.ciclo
                )

        self.hoja_tipo = proy.hoja or "carta"
        self.hoja_escala = str(proy.escala) if proy.escala is not None else "auto"

        if proy.pintura:
            self.pintura = proy.pintura
        else:
            self.pintura = EsquemaPintura()

        self.pliegos_por_paquete = getattr(proy, "pliegos_por_paquete", 100) or 100
        if proy.condiciones and proy.condiciones.pliego_cm:
            self.pliego_ancho = float(proy.condiciones.pliego_cm[0])
            self.pliego_alto = float(proy.condiciones.pliego_cm[1])

        if getattr(proy, "esquema_pico", None):
            self.esquema_pico = proy.esquema_pico
        else:
            self.esquema_pico = EsquemaDisenoPico()

        self.disenos = proy.disenos.copy() if getattr(proy, "disenos", None) else {}
        self.recursos_faltantes = list(getattr(proy, "recursos_faltantes", []))

        self.nombre_proyecto = proy.nombre
        self.ruta_proyecto = ruta
        self.sin_guardar = False

        # Recalcular automáticamente
        self.calcular()
        self.sin_guardar = False

    def guardar(self, ruta: Optional[str] = None) -> Tuple[bool, str]:
        destino = ruta or self.ruta_proyecto
        if not destino:
            return False, "No se ha especificado ruta para guardar"
        try:
            nombre = os.path.splitext(os.path.basename(destino))[0]
            self.nombre_proyecto = nombre
            proy = self.a_proyecto()
            guardar_proyecto(proy, destino)
            self.ruta_proyecto = destino
            self.sin_guardar = False
            return True, destino
        except Exception as e:
            return False, str(e)

    def abrir(self, ruta: str) -> Tuple[bool, str]:
        try:
            proy = cargar_proyecto(ruta)
            self.desde_proyecto(proy, ruta)
            return True, ruta
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error al abrir archivo: {e}"

    def get_view_model(self) -> ViewModelTrompo:
        tarjetas = []
        avisos = []
        
        if self.resultado and self.entrada_actual and not self.desactualizado:
            resumen_lista = formatear_resumen(self.resultado)
            for k, v in resumen_lista:
                tarjetas.append(TarjetaResumen(etiqueta=k, valor=v))
                
            for aviso in self.resultado.avisos:
                clase = clasificar_aviso(aviso)
                avisos.append(AvisoFlet(texto=aviso, clase=clase))

        # Derivar estado del esquema y lista de compra
        esquema_err = None
        res_esq = []
        items_compra = []
        try:
            esq = self._construir_esquema()
            if self.resultado and self.entrada_actual and not self.desactualizado:
                res_esq = resumen_esquema(esq, self.entrada_actual, self.resultado)
                items_compra = lista_de_compra(
                    entrada=self.entrada_actual,
                    resultado=self.resultado,
                    esquema_pintura=self.pintura,
                    esquema_diseno=esq,
                    condiciones=Condiciones(pliego_cm=(float(self.pliego_ancho), float(self.pliego_alto))),
                    catalogo=cargar_catalogo(),
                    pliegos_por_paquete=self.pliegos_por_paquete,
                )
        except Exception as e:
            esquema_err = str(e)

        res_pico_str = None
        if self.resultado and self.entrada_actual and not self.desactualizado:
            try:
                rp = resumen_pico(self.esquema_pico, self.entrada_actual, self.resultado)
                res_pico_str = f"{rp.total_piramides} pirámides ({rp.piramides_a} tipo A, {rp.piramides_b} tipo B) · {rp.total_triangulos} triángulos en total"
            except Exception:
                pass

        url_3d = self.servidor_3d.url if self.servidor_3d else ""
        dis_activo = self.obtener_diseno_activo() if not self.desactualizado else None
        capas_dis = list(dis_activo.capas) if dis_activo else []

        cfg_diseno = self.obtener_config_seccion(self.diseno_seccion)
        puede_mitad, motivo_no = cfg_diseno.puede_usar_mitad()

        return ViewModelTrompo(
            tarjetas=tarjetas,
            avisos=avisos,
            mensaje_error=self.mensaje_error,
            desactualizado=self.desactualizado,
            tablas=list(self.tablas) if not self.desactualizado else [],
            svg_conjunto=self.svg_conjunto if not self.desactualizado else "",
            svg_superior=self.svg_superior if not self.desactualizado else "",
            svg_pico=self.svg_pico if not self.desactualizado else "",
            svg_inferior=self.svg_inferior if not self.desactualizado else "",
            svg_perfil=self.svg_perfil if not self.desactualizado else "",
            svg_hoja=self.svg_hoja if not self.desactualizado and not esquema_err else "",
            esquema_error=esquema_err,
            resumen_esquema=res_esq,
            aviso_hoja=self.aviso_hoja,
            resumen_pico_linea=res_pico_str,
            esquema_pico=self.esquema_pico,
            nombre_proyecto=self.nombre_proyecto,
            ruta_proyecto=self.ruta_proyecto,
            sin_guardar=self.sin_guardar,
            items_compra=items_compra if not self.desactualizado else [],
            pintura=self.pintura,
            url_visor_3d=url_3d,
            svg_diseno=self.svg_diseno if not self.desactualizado else "",
            diseno_activo=dis_activo,
            capas_diseno=capas_dis,
            capa_seleccionada_id=self.capa_seleccionada_id,
            diseno_seccion=self.diseno_seccion,
            diseno_variante=self.diseno_variante,
            diseno_lienzo_modo=cfg_diseno.dibujar,
            mantener_proporcion=self.mantener_proporcion,
            recursos_faltantes=list(self.recursos_faltantes),
            diseno_ver_cuadricula=self.diseno_ver_cuadricula,
            diseno_ver_rotulos=self.diseno_ver_rotulos,
            diseno_ver_costuras=self.diseno_ver_costuras,
            diseno_mostrar_reflejo=self.diseno_mostrar_reflejo,
            config_secciones={k: ConfigSeccion.from_dict(v.a_dict()) for k, v in self.config_secciones.items()},
            puede_usar_mitad=puede_mitad,
            motivo_no_mitad=motivo_no,
        )

    # --- Métodos de Diseño sobre el abanico (F6a) ---
    def clave_diseno_activo(self) -> str:
        return f"pico_{self.diseno_variante}" if self.diseno_seccion == "pico" else self.diseno_seccion

    def obtener_diseno_activo(self) -> Diseno:
        clave = self.clave_diseno_activo()
        if clave not in self.disenos:
            self.disenos[clave] = Diseno(seccion=self.diseno_seccion, variante=self.diseno_variante, capas=[])
        return self.disenos[clave]

    def obtener_carpeta_recursos_activa(self) -> Path:
        if self.ruta_proyecto:
            p = Path(self.ruta_proyecto)
            d = p.parent / f"{p.stem}_recursos"
        else:
            d = Path("guardados") / "recursos_temp"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def ventana_lienzo(self) -> Tuple[float, float, float, float]:
        """Calcula la caja envolvente del lienzo (min_x, min_y, max_x, max_y) en cm."""
        if not self.resultado or not self.entrada_actual:
            return (-50.0, 0.0, 50.0, 100.0)
        from logic.geometria.abanico import pieza_a_geometria_plana, abanico
        sec = self.diseno_seccion
        pz = pieza_a_geometria_plana(self.resultado, self.entrada_actual, sec)
        cfg = self.obtener_config_seccion(sec)
        tam_g = 4 if sec == "pico" else (cfg.esquema.tam_grupo if cfg.esquema else 5)
        ab = abanico(pz, n=tam_g, centrado=True)
        if cfg.dibujar == "mitad":
            min_x = 0.0
            max_x = ab.caja_max_x
        else:
            min_x = ab.caja_min_x
            max_x = ab.caja_max_x
        return (min_x, ab.caja_min_y, max_x, ab.caja_max_y)

    def anadir_capa(self, ruta_archivo: str) -> CapaDiseno:
        carp = self.obtener_carpeta_recursos_activa()
        ventana = self.ventana_lienzo()
        capa = importar_recurso(ruta_archivo, carp, ventana=ventana)
        diseno = self.obtener_diseno_activo()
        diseno.capas.append(capa)
        self.capa_seleccionada_id = capa.id
        self.sin_guardar = True
        self._actualizar_svg_diseno()
        return capa

    def eliminar_capa(self, id_capa: str) -> None:
        diseno = self.obtener_diseno_activo()
        diseno.capas = [c for c in diseno.capas if c.id != id_capa]
        if self.capa_seleccionada_id == id_capa:
            self.capa_seleccionada_id = diseno.capas[0].id if diseno.capas else None
        self.sin_guardar = True
        self._actualizar_svg_diseno()

    def mover_capa(self, id_capa: str, direccion: int) -> None:
        diseno = self.obtener_diseno_activo()
        for i, c in enumerate(diseno.capas):
            if c.id == id_capa:
                nuevo_idx = i + direccion
                if 0 <= nuevo_idx < len(diseno.capas):
                    diseno.capas[i], diseno.capas[nuevo_idx] = diseno.capas[nuevo_idx], diseno.capas[i]
                    self.sin_guardar = True
                    self._actualizar_svg_diseno()
                break

    def obtener_capa_seleccionada(self) -> Optional[CapaDiseno]:
        if not self.capa_seleccionada_id:
            diseno = self.obtener_diseno_activo()
            return diseno.capas[0] if diseno.capas else None
        for c in self.obtener_diseno_activo().capas:
            if c.id == self.capa_seleccionada_id:
                return c
        return None

    def modificar_capa_seleccionada(self, **kwargs) -> None:
        capa = self.obtener_capa_seleccionada()
        if not capa or capa.bloqueada:
            return
        for k, v in kwargs.items():
            if hasattr(capa, k):
                setattr(capa, k, v)
        self.sin_guardar = True
        self._actualizar_svg_diseno()

    def ajustar_capa_seleccionada(self, modo: str) -> None:
        capa = self.obtener_capa_seleccionada()
        if not capa or capa.bloqueada:
            return
        ventana = self.ventana_lienzo()
        capa_ajustada = ajustar_capa(capa, ventana, modo)
        capa.x = capa_ajustada.x
        capa.y = capa_ajustada.y
        capa.ancho = capa_ajustada.ancho
        capa.alto = capa_ajustada.alto
        self.sin_guardar = True
        self._actualizar_svg_diseno()

    def ajustar_capa_cubrir(self) -> None:
        self.ajustar_capa_seleccionada("cubrir")

    def ajustar_capa_contener(self) -> None:
        self.ajustar_capa_seleccionada("contener")

    def ajustar_capa_estirar(self) -> None:
        self.ajustar_capa_seleccionada("estirar")

    def ajustar_capa_ancho(self) -> None:
        self.ajustar_capa_seleccionada("ancho")

    def ajustar_capa_alto(self) -> None:
        self.ajustar_capa_seleccionada("alto")

    def centrar_capa_seleccionada(self) -> None:
        self.ajustar_capa_seleccionada("centrar")

    def empujar_capa_seleccionada(
        self,
        dx: float = 0.0,
        dy: float = 0.0,
        dw: float = 0.0,
        dh: float = 0.0,
        drot: float = 0.0,
    ) -> None:
        capa = self.obtener_capa_seleccionada()
        if not capa or capa.bloqueada:
            return
        capa.x = round(capa.x + dx, 2)
        capa.y = round(capa.y + dy, 2)
        if dw != 0 or dh != 0:
            if self.mantener_proporcion and capa.ancho_natural > 0 and capa.alto_natural > 0:
                prop = capa.alto_natural / capa.ancho_natural
                nuevo_w = max(0.5, capa.ancho + dw)
                capa.ancho = round(nuevo_w, 2)
                capa.alto = round(nuevo_w * prop, 2)
            else:
                capa.ancho = round(max(0.5, capa.ancho + dw), 2)
                capa.alto = round(max(0.5, capa.alto + dh), 2)
        if drot != 0:
            nueva_rot = (capa.rotacion + drot) % 360
            if nueva_rot > 180:
                nueva_rot -= 360
            capa.rotacion = round(nueva_rot, 1)
        self.sin_guardar = True
        self._actualizar_svg_diseno()

    def cambiar_diseno_ver_cuadricula(self, val: bool) -> None:
        self.diseno_ver_cuadricula = val
        self._actualizar_svg_diseno()

    def cambiar_diseno_ver_rotulos(self, val: bool) -> None:
        self.diseno_ver_rotulos = val
        self._actualizar_svg_diseno()

    def cambiar_diseno_ver_costuras(self, val: bool) -> None:
        self.diseno_ver_costuras = val
        self._actualizar_svg_diseno()

    def cambiar_diseno_mostrar_reflejo(self, val: bool) -> None:
        self.diseno_mostrar_reflejo = val
        self._actualizar_svg_diseno()

    def cambiar_diseno_seccion(self, seccion: str, variante: str = "A") -> None:
        self.diseno_seccion = seccion
        self.diseno_variante = variante
        cfg = self.obtener_config_seccion(seccion)
        self.diseno_lienzo_modo = cfg.dibujar
        dis = self.obtener_diseno_activo()
        self.capa_seleccionada_id = dis.capas[0].id if dis.capas else None
        self._actualizar_svg_diseno()

    def cambiar_diseno_lienzo_modo(self, modo: str) -> None:
        cfg = self.obtener_config_seccion(self.diseno_seccion)
        if cfg.seccion == "pico":
            cfg.dibujar = "completo"
        else:
            puede, _ = cfg.puede_usar_mitad()
            cfg.dibujar = modo if (puede or modo == "completo") else "completo"
        self.diseno_lienzo_modo = cfg.dibujar
        self.sin_guardar = True
        self._actualizar_svg_diseno()

    def _actualizar_svg_diseno(self) -> None:
        if not self.resultado or not self.entrada_actual:
            self.svg_diseno = ""
            return
        try:
            sec = self.diseno_seccion
            cfg = self.obtener_config_seccion(sec)
            esq = cfg.esquema if (cfg and cfg.esquema) else self._construir_esquema(sec)
            dis = self.obtener_diseno_activo()
            carp = self.obtener_carpeta_recursos_activa()
            capa_sel = self.obtener_capa_seleccionada()
            overlay = capa_sel if (capa_sel and not capa_sel.bloqueada) else None
            self.svg_diseno = svg_abanico(
                resultado=self.resultado,
                entrada=self.entrada_actual,
                seccion=sec,
                esquema=esq,
                estilo=self.estilo_svg,
                hoja=self.hoja_tipo,
                dibujar=cfg.dibujar,
                diseno=dis,
                carpeta_recursos=carp,
                mostrar_reflejo=self.diseno_mostrar_reflejo,
                ver_cuadricula=self.diseno_ver_cuadricula,
                ver_rotulos=self.diseno_ver_rotulos,
                ver_costuras=self.diseno_ver_costuras,
                overlay_capa_activa=overlay,
            )
        except Exception as e:
            warnings.warn(f"Error generando SVG de diseño: {e}")
            self.svg_diseno = ""

    def exportar_gajos_diseno(self, carpeta_destino: str) -> List[Path]:
        if not self.resultado or not self.entrada_actual:
            return []
        sec = self.diseno_seccion
        cfg = self.obtener_config_seccion(sec)
        esq = cfg.esquema if (cfg and cfg.esquema) else self._construir_esquema(sec)
        dis = self.obtener_diseno_activo()
        carp_rec = self.obtener_carpeta_recursos_activa()
        return exportar_diseno(
            carpeta=carpeta_destino,
            resultado=self.resultado,
            entrada=self.entrada_actual,
            esquema=esq,
            diseno=dis,
            carpeta_recursos=carp_rec,
            seccion=sec,
            formato_hoja=self.hoja_tipo,
            dibujar=cfg.dibujar,
        )

    def exportar_hoja_diseno(self, ruta_destino: str) -> None:
        if not self.resultado or not self.entrada_actual:
            return
        sec = self.diseno_seccion
        cfg = self.obtener_config_seccion(sec)
        esq = cfg.esquema if (cfg and cfg.esquema) else self._construir_esquema(sec)
        dis = self.obtener_diseno_activo()
        carp_rec = self.obtener_carpeta_recursos_activa()
        svg_txt = svg_abanico(
            resultado=self.resultado,
            entrada=self.entrada_actual,
            seccion=sec,
            esquema=esq,
            estilo=IMPRESION,
            hoja=self.hoja_tipo,
            dibujar=cfg.dibujar,
            diseno=dis,
            carpeta_recursos=carp_rec,
            mostrar_reflejo=self.diseno_mostrar_reflejo,
            ver_cuadricula=self.diseno_ver_cuadricula,
            ver_rotulos=self.diseno_ver_rotulos,
            ver_costuras=self.diseno_ver_costuras,
        )
        with open(ruta_destino, "w", encoding="utf-8") as f:
            f.write(svg_txt)

    def exportar_abanico_diseno(self, ruta_destino: str) -> None:
        self.exportar_hoja_diseno(ruta_destino)

