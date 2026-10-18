import warnings
from typing import Optional, Union
from logic.exportacion.estilos import IMPRESION
from logic.exportacion.svg_moldes import svg_hoja
from logic.exportacion.svg_abanico import svg_abanico
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.paquete import parsear_ciclo
from logic.diseno.config_seccion import ConfigSeccion


class ControladorHojaMixin:
    """Mixin para gestión de esquemas, opciones de hoja de trazo y configuración por sección."""

    def obtener_config_seccion(self, seccion: Optional[str] = None) -> ConfigSeccion:
        sec = seccion or getattr(self, "diseno_seccion", "superior")
        if sec not in self.config_secciones:
            self.config_secciones[sec] = ConfigSeccion(seccion=sec)
        return self.config_secciones[sec]

    def _construir_esquema(self, seccion: Optional[str] = None) -> EsquemaDiseno:
        if seccion is not None and seccion != self.hoja_pieza:
            cfg = self.config_secciones.get(seccion)
            if cfg and cfg.esquema:
                return cfg.esquema
        if self.esquema_modo == "personalizado":
            ciclo = parsear_ciclo(self.esquema_ciclo_texto)
            return EsquemaDiseno("personalizado", len(ciclo), ciclo=ciclo)
        return EsquemaDiseno(self.esquema_modo, int(self.esquema_tam_grupo))

    def actualizar_esquema(
        self,
        modo: Optional[str] = None,
        tam_grupo: Optional[int] = None,
        ciclo_texto: Optional[str] = None,
    ) -> None:
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
    ) -> None:
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
                cfg.dibujar = dibujar
                if dibujar == "mitad":
                    cfg.diseno_modo = "mitad"
                    cfg.espejo = True
                    self.diseno_pico_modo = "mitad"
                else:
                    cfg.diseno_modo = "una_cara"
                    cfg.espejo = False
                    self.diseno_pico_modo = "una_cara"
                self.hoja_dibujar = dibujar
                if getattr(self, "diseno_seccion", None) == "pico":
                    self.diseno_lienzo_modo = cfg.diseno_modo
            else:
                puede, _ = cfg.puede_usar_mitad()
                if dibujar == "mitad" and not puede:
                    cfg.dibujar = "completo"
                    self.hoja_dibujar = "completo"
                else:
                    cfg.dibujar = dibujar
                    self.hoja_dibujar = dibujar
        self.marcar_cambio_diseno()

    def actualizar_esquema_pico(self, modo_repeticion: Optional[str] = None) -> None:
        if modo_repeticion is not None:
            self.esquema_pico.modo_repeticion = modo_repeticion
            self.esquema_pico.usar_variante_b = (modo_repeticion != "todas_a")
            if "pico" in self.config_secciones and self.config_secciones["pico"].esquema_pico:
                self.config_secciones["pico"].esquema_pico.modo_repeticion = modo_repeticion
                self.config_secciones["pico"].esquema_pico.usar_variante_b = (modo_repeticion != "todas_a")
        self.marcar_cambio_diseno()

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
        if getattr(self, "diseno_seccion", None) == seccion:
            self.diseno_lienzo_modo = cfg.dibujar
        self.sin_guardar = True
        self._generar_svg_hoja()
        self._actualizar_svg_diseno()

    def cambiar_dibujar_seccion(self, seccion: str, dibujar: str) -> None:
        cfg = self.obtener_config_seccion(seccion)
        if cfg.seccion == "pico":
            cfg.dibujar = dibujar
            if dibujar == "mitad":
                cfg.diseno_modo = "mitad"
                cfg.espejo = True
                self.diseno_pico_modo = "mitad"
            else:
                cfg.diseno_modo = "una_cara"
                cfg.espejo = False
                self.diseno_pico_modo = "una_cara"
            if getattr(self, "diseno_seccion", None) == "pico":
                self.diseno_lienzo_modo = cfg.diseno_modo
        else:
            puede, _ = cfg.puede_usar_mitad()
            if dibujar == "mitad" and not puede:
                cfg.dibujar = "completo"
            else:
                cfg.dibujar = dibujar
            if getattr(self, "diseno_seccion", None) == seccion:
                self.diseno_lienzo_modo = cfg.dibujar
        if self.hoja_pieza == seccion:
            self.hoja_dibujar = cfg.dibujar
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
        if getattr(self, "diseno_seccion", None) == destino:
            self.diseno_lienzo_modo = self.config_secciones[destino].dibujar
        self.sin_guardar = True
        self._generar_svg_hoja()
        self._actualizar_svg_diseno()

    def sincronizar_conos(self, origen: str = "superior") -> None:
        destino = "inferior" if origen == "superior" else "superior"
        self.copiar_configuracion_seccion(origen, destino)

    def _generar_svg_hoja(self) -> None:
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
