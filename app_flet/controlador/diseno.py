import warnings
from pathlib import Path
from typing import List, Optional, Tuple
from logic.diseno.lienzo import Diseno, CapaDiseno, importar_recurso, ajustar_capa
from logic.exportacion.svg_abanico import svg_abanico
from logic.exportacion.svg_diseno import exportar_diseno
from logic.exportacion.estilos import IMPRESION


class ControladorDisenoMixin:
    """Mixin para diseño de motivos sobre el abanico, manipulación de capas y exportación."""

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
        actualizar_svg: bool = True,
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
        if actualizar_svg:
            self._actualizar_svg_diseno()

    def actualizar_geometria_capa_seleccionada(
        self,
        x: float,
        y: float,
        ancho: float,
        alto: float,
        rotacion: Optional[float] = None,
        actualizar_svg: bool = True,
    ) -> None:
        """Actualiza la geometría completa de la capa seleccionada."""
        capa = self.obtener_capa_seleccionada()
        if not capa or capa.bloqueada:
            return
        capa.x = round(float(x), 4)
        capa.y = round(float(y), 4)
        capa.ancho = round(float(ancho), 4)
        capa.alto = round(float(alto), 4)
        if rotacion is not None:
            capa.rotacion = round(float(rotacion), 2)
        self.sin_guardar = True
        if actualizar_svg:
            self._actualizar_svg_diseno()

    def obtener_conversion_diseno(
        self,
        zona_px: Tuple[float, float],
        vista_svg,
    ):
        """Construye la instancia de Conversion matemática plano <-> px para la vista actual."""
        if not self.resultado or not self.entrada_actual or not vista_svg:
            return None
        from logic.exportacion.svg_abanico import calcular_parametros_proyeccion_abanico
        from logic.diseno.gestos_lienzo import Conversion

        sec = self.diseno_seccion
        cfg = self.obtener_config_seccion(sec)
        esq = cfg.esquema if (cfg and cfg.esquema) else self._construir_esquema(sec)
        geom = calcular_parametros_proyeccion_abanico(
            resultado=self.resultado,
            entrada=self.entrada_actual,
            seccion=sec,
            esquema=esq,
            hoja=self.hoja_tipo,
            dibujar=cfg.dibujar,
            mostrar_reflejo=self.diseno_mostrar_reflejo,
        )
        return Conversion(
            vista=vista_svg,
            zona_px=zona_px,
            y_arriba=True,
            factor_escala=geom["factor"],
            cx_vista=geom["cx_page"],
            cy_vista=geom["cy_page"],
            y_mid_plano=geom["y_mid_cm"],
        )

    def actualizar_svg_diseno(self, modo_fantasma: bool = False) -> None:
        """Fuerza la regeneración del SVG de diseño."""
        self._actualizar_svg_diseno(modo_fantasma=modo_fantasma)

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

    def _actualizar_svg_diseno(self, modo_fantasma: bool = False) -> None:
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
            overlay = None if modo_fantasma else (capa_sel if (capa_sel and not capa_sel.bloqueada) else None)
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
                modo_fantasma=modo_fantasma,
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
