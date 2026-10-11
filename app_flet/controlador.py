# app_flet/controlador.py
import os
import warnings
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Union
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput, BalloonCalculationResult, Condiciones
from logic.exportacion.estilos import EstiloSvg, PANTALLA_OSCURO, IMPRESION
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto, svg_hoja
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_perfil import svg_perfil
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.paquete import parsear_ciclo, resumen_esquema, generar_paquete, guardar_paquete
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto
from presentacion.trompo_estrella import (
    leer_entrada,
    formatear_resumen,
    clasificar_aviso,
    formatear_tablas,
    TablaMolde,
)

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
    # Proyecto
    nombre_proyecto: str = "Sin título"
    ruta_proyecto: Optional[str] = None
    sin_guardar: bool = False

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

        # Estado de diseño / hoja de trazo (F3)
        self.esquema_modo: str = "repeticion"
        self.esquema_tam_grupo: int = 5
        self.esquema_ciclo_texto: str = "0, 1, 2E, 1E"
        self.hoja_tipo: str = "carta"
        self.hoja_escala: str = "auto"
        self.hoja_pieza: str = "superior"  # "superior", "pico", "inferior"

        self.aviso_hoja: Optional[str] = None

        # Estado del proyecto
        self.nombre_proyecto: str = "Sin título"
        self.ruta_proyecto: Optional[str] = None
        self.sin_guardar: bool = False

    def marcar_desactualizado(self):
        if self.resultado is not None:
            self.desactualizado = True
            self.sin_guardar = True
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
        self.marcar_cambio_diseno()

    def actualizar_opciones_hoja(
        self,
        pieza: Optional[str] = None,
        tipo: Optional[str] = None,
        escala: Optional[str] = None,
    ):
        if pieza is not None:
            self.hoja_pieza = pieza
        if tipo is not None:
            self.hoja_tipo = tipo
        if escala is not None:
            self.hoja_escala = escala
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

    def _construir_esquema(self) -> EsquemaDiseno:
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
            esq = self._construir_esquema()
            escala_val = "auto" if str(self.hoja_escala).lower() == "auto" else float(self.hoja_escala)

            with warnings.catch_warnings(record=True) as w_list:
                warnings.simplefilter("always")
                self.svg_hoja = svg_hoja(
                    resultado=self.resultado,
                    entrada=self.entrada_actual,
                    seccion=self.hoja_pieza,
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
        except ValueError as e:
            self.mensaje_error = str(e)

        return self.get_view_model()

    # --- Métodos de Proyecto (F3) ---
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

        self.nombre_proyecto = "Sin título"
        self.ruta_proyecto = None
        self.sin_guardar = False

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

        try:
            esq = self._construir_esquema()
        except Exception:
            esq = None

        return Proyecto(
            version=1,
            nombre=self.nombre_proyecto,
            entrada=ent,
            condiciones=Condiciones(),
            esquema=esq,
            notas="",
            hoja=self.hoja_tipo,
            escala=self.hoja_escala,
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

        if proy.esquema:
            self.esquema_modo = proy.esquema.modo
            self.esquema_tam_grupo = proy.esquema.tam_grupo
            if proy.esquema.ciclo:
                self.esquema_ciclo_texto = ", ".join(
                    f"{m}{'E' if esp else ''}" for m, esp in proy.esquema.ciclo
                )

        self.hoja_tipo = proy.hoja or "carta"
        self.hoja_escala = str(proy.escala) if proy.escala is not None else "auto"

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

        # Derivar estado del esquema
        esquema_err = None
        res_esq = []
        try:
            esq = self._construir_esquema()
            if self.resultado and self.entrada_actual and not self.desactualizado:
                res_esq = resumen_esquema(esq, self.entrada_actual, self.resultado)
        except Exception as e:
            esquema_err = str(e)

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
            nombre_proyecto=self.nombre_proyecto,
            ruta_proyecto=self.ruta_proyecto,
            sin_guardar=self.sin_guardar,
        )
