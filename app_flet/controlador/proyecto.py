import os
from typing import Optional, Tuple
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.pintura import EsquemaPintura
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto
from presentacion.trompo_estrella import leer_entrada


class ControladorProyectoMixin:
    """Mixin para gestión del ciclo de vida y persistencia de proyectos en disco."""

    def nuevo(self) -> None:
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

    def a_proyecto(self) -> Proyecto:
        datos = self._recoger_diccionario_entradas()
        try:
            ent = leer_entrada(datos, self.avanzado)
        except Exception:
            ent = BalloonInput(
                float(self.altura or 950),
                int(self.gajos or 30),
                int(self.hileras or 2),
                float(self.costura or 1),
            )

        esq_sup = self.obtener_config_seccion("superior").esquema
        configs_a_guardar = {
            k: ConfigSeccion.from_dict(v.a_dict()) for k, v in self.config_secciones.items()
        }

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

    def _restaurar_entradas_proyecto(self, ent: BalloonInput) -> None:
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

    def _restaurar_secciones_proyecto(self, proy: Proyecto) -> None:
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
                self.esquema_ciclo_texto = ", ".join(f"{m}{'E' if esp else ''}" for m, esp in proy.esquema.ciclo)

    def desde_proyecto(self, proy: Proyecto, ruta: Optional[str] = None) -> None:
        self.limpiar()
        self._restaurar_entradas_proyecto(proy.entrada)
        self._restaurar_secciones_proyecto(proy)

        self.hoja_tipo = proy.hoja or "carta"
        self.hoja_escala = str(proy.escala) if proy.escala is not None else "auto"
        self.pintura = proy.pintura if proy.pintura else EsquemaPintura()
        self.pliegos_por_paquete = getattr(proy, "pliegos_por_paquete", 100) or 100

        if proy.condiciones and proy.condiciones.pliego_cm:
            self.pliego_ancho = float(proy.condiciones.pliego_cm[0])
            self.pliego_alto = float(proy.condiciones.pliego_cm[1])

        self.esquema_pico = getattr(proy, "esquema_pico", None) or EsquemaDisenoPico()
        self.disenos = proy.disenos.copy() if getattr(proy, "disenos", None) else {}
        self.recursos_faltantes = list(getattr(proy, "recursos_faltantes", []))

        self.nombre_proyecto = proy.nombre
        self.ruta_proyecto = ruta
        self.sin_guardar = False

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
