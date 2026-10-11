# app_flet/controlador.py
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.models import BalloonInput, BalloonCalculationResult
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto
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

class ControladorTrompo:
    def __init__(self):
        self.calculadora = TrompoEstrellaCalculator()
        self.resultado: Optional[BalloonCalculationResult] = None
        self.entrada_actual: Optional[BalloonInput] = None
        self.desactualizado = False
        self.mensaje_error: Optional[str] = None
        
        # Tablas y SVGs expuestos
        self.tablas: List[TablaMolde] = []
        self.svg_conjunto: str = ""
        self.svg_superior: str = ""
        self.svg_pico: str = ""
        self.svg_inferior: str = ""

        # Estado de los campos
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

    def marcar_desactualizado(self):
        if self.resultado is not None:
            self.desactualizado = True
            self._vaciar_datos_calculados()

    def _vaciar_datos_calculados(self):
        self.tablas = []
        self.svg_conjunto = ""
        self.svg_superior = ""
        self.svg_pico = ""
        self.svg_inferior = ""

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
            self.svg_conjunto = svg_conjunto(self.resultado, self.entrada_actual, escala=10.0)
            self.svg_superior = svg_pieza(self.resultado, self.entrada_actual, "superior", escala=10.0)
            self.svg_pico = svg_pieza(self.resultado, self.entrada_actual, "pico", escala=10.0)
            self.svg_inferior = svg_pieza(self.resultado, self.entrada_actual, "inferior", escala=10.0)
        except ValueError as e:
            self.mensaje_error = str(e)

        return self.get_view_model()

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
        )
