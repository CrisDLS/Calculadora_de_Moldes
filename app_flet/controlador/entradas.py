from typing import Any, List, Optional
from logic.exportacion.estilos import EstiloSvg
from logic.exportacion.svg_moldes import svg_pieza, svg_conjunto
from logic.geometria.perfil import perfil_armado
from logic.exportacion.svg_perfil import svg_perfil
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.paquete import resumen_esquema
from logic.diseno.diseno_pico import resumen_pico
from logic.diseno.compra import ItemCompra, lista_de_compra
from logic.diseno.paleta import cargar_catalogo
from logic.diseno.config_seccion import ConfigSeccion
from logic.models import Condiciones
from presentacion.trompo_estrella import (
    leer_entrada,
    formatear_resumen,
    clasificar_aviso,
    formatear_tablas,
)
from app_flet.controlador.modelos import TarjetaResumen, AvisoFlet, ViewModelTrompo


class ControladorEntradasMixin:
    """Mixin para gestión de entradas, cálculo de geometría y armado de view-model."""

    def marcar_desactualizado(self) -> None:
        self.sin_guardar = True
        if self.resultado is not None:
            self.desactualizado = True
            self._vaciar_datos_calculados()

    def marcar_cambio_diseno(self) -> None:
        self.sin_guardar = True
        self._generar_svg_hoja()

    def actualizar_campo(self, campo: str, valor: Any) -> None:
        if hasattr(self, campo):
            setattr(self, campo, valor)
            self.marcar_desactualizado()

    def _vaciar_datos_calculados(self) -> None:
        self.tablas = []
        self.svg_conjunto = ""
        self.svg_superior = ""
        self.svg_pico = ""
        self.svg_inferior = ""
        self.svg_perfil = ""
        self.svg_hoja = ""
        self.aviso_hoja = None

    def _generar_svgs(self) -> None:
        if self.resultado and self.entrada_actual:
            self.svg_conjunto = svg_conjunto(self.resultado, self.entrada_actual, escala=10.0, estilo=self.estilo_svg)
            self.svg_superior = svg_pieza(self.resultado, self.entrada_actual, "superior", escala=10.0, estilo=self.estilo_svg)
            self.svg_pico = svg_pieza(self.resultado, self.entrada_actual, "pico", escala=10.0, estilo=self.estilo_svg)
            self.svg_inferior = svg_pieza(self.resultado, self.entrada_actual, "inferior", escala=10.0, estilo=self.estilo_svg)
            perf = perfil_armado(self.entrada_actual, self.resultado, mostrar_picos_al_borde=True)
            self.svg_perfil = svg_perfil(perf, estilo=self.estilo_svg, escala=10.0)
            self._generar_svg_hoja()

    def cambiar_estilo(self, estilo: EstiloSvg) -> ViewModelTrompo:
        self.estilo_svg = estilo
        if self.resultado and self.entrada_actual and not self.desactualizado:
            self._generar_svgs()
        return self.get_view_model()

    def limpiar(self) -> None:
        self.resultado = None
        self.entrada_actual = None
        self.desactualizado = False
        self.mensaje_error = None
        self._vaciar_datos_calculados()

    def _recoger_diccionario_entradas(self) -> dict:
        datos = {
            "altura": self.altura,
            "gajos": self.gajos,
            "hileras": self.hileras,
            "costura": self.costura,
        }
        if self.avanzado:
            if self.boca:
                datos["diametro_boca"] = self.boca
            if self.pestana:
                datos["pestana_boca"] = self.pestana
            if self.diametro_mecha:
                datos["diametro_mecha"] = self.diametro_mecha
            if self.peso_mecha:
                datos["masa_mecha_g"] = self.peso_mecha
            if self.alambre:
                datos["alambre_mm"] = self.alambre
            if self.varillas:
                datos["varillas"] = self.varillas
            if self.altura_llama:
                datos["altura_llama"] = self.altura_llama
            if self.holgura:
                datos["holgura_min"] = self.holgura
        return datos

    def calcular(self) -> ViewModelTrompo:
        self.limpiar()
        datos = self._recoger_diccionario_entradas()

        try:
            self.entrada_actual = leer_entrada(datos, self.avanzado)
            self.resultado = self.calculadora.calcular(self.entrada_actual)
            self.tablas = formatear_tablas(self.resultado, self.entrada_actual)
            self._generar_svgs()
            self._actualizar_svg_diseno()
            self._actualizar_servidor_3d()
            self.sin_guardar = True
        except ValueError as e:
            self.mensaje_error = str(e)

        return self.get_view_model()

    def _preparar_tarjetas_y_avisos(self) -> tuple[List[TarjetaResumen], List[AvisoFlet]]:
        tarjetas: List[TarjetaResumen] = []
        avisos: List[AvisoFlet] = []
        if self.resultado and self.entrada_actual and not self.desactualizado:
            resumen_lista = formatear_resumen(self.resultado)
            for k, v in resumen_lista:
                tarjetas.append(TarjetaResumen(etiqueta=k, valor=v))
            for aviso in self.resultado.avisos:
                clase = clasificar_aviso(aviso)
                avisos.append(AvisoFlet(texto=aviso, clase=clase))
        return tarjetas, avisos

    def _derivar_datos_esquema_y_compra(self) -> tuple[Optional[str], List[str], List[ItemCompra]]:
        esquema_err: Optional[str] = None
        res_esq: List[str] = []
        items_compra: List[ItemCompra] = []
        try:
            sec_esq = self.hoja_pieza if self.hoja_pieza != "pico" else "superior"
            esq = self._construir_esquema(sec_esq)
            if self.resultado and self.entrada_actual and not self.desactualizado:
                if self.hoja_pieza != "pico":
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
            if self.hoja_pieza != "pico":
                esquema_err = str(e)
        return esquema_err, res_esq, items_compra

    def _derivar_resumen_pico(self) -> Optional[str]:
        if self.resultado and self.entrada_actual and not self.desactualizado:
            try:
                rp = resumen_pico(self.esquema_pico, self.entrada_actual, self.resultado)
                return f"{rp.total_piramides} pirámides ({rp.piramides_a} tipo A, {rp.piramides_b} tipo B) · {rp.total_triangulos} triángulos en total"
            except Exception:
                return None
        return None

    def get_view_model(self) -> ViewModelTrompo:
        tarjetas, avisos = self._preparar_tarjetas_y_avisos()
        esquema_err, res_esq, items_compra = self._derivar_datos_esquema_y_compra()
        res_pico_str = self._derivar_resumen_pico()

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
            diseno_lienzo_modo=self.diseno_pico_modo if self.diseno_seccion == "pico" else cfg_diseno.dibujar,
            mantener_proporcion=self.mantener_proporcion,
            recursos_faltantes=list(self.recursos_faltantes),
            diseno_ver_cuadricula=self.diseno_ver_cuadricula,
            diseno_ver_rotulos=self.diseno_ver_rotulos,
            diseno_ver_costuras=self.diseno_ver_costuras,
            diseno_mostrar_reflejo=self.diseno_mostrar_reflejo,
            config_secciones={k: ConfigSeccion.from_dict(v.a_dict()) for k, v in self.config_secciones.items()},
            puede_usar_mitad=puede_mitad,
            motivo_no_mitad=motivo_no,
            mostrar_diseno_3d=getattr(self, "mostrar_diseno_3d", True),
            hay_diseno_visible=self.hay_capas_visibles_diseno() if hasattr(self, "hay_capas_visibles_diseno") else False,
        )
