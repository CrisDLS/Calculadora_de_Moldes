"""Capa de compatibilidad y delegación de proxies para VistaTrompo.

Permite mantener la compatibilidad hacia atrás con los tests históricos y de snapshots
que acceden a controles internos a través de la instancia de VistaTrompo.
"""

from typing import Optional
from logic.exportacion.vista_svg import VistaSvg


class VistaTrompoCompat:
    """Mixin que conecta controles hijos y métodos delegados como atributos directos."""

    def _conectar_proxies(self) -> None:
        self._conectar_proxies_entradas()
        self._conectar_proxies_resumen_tablas()
        self._conectar_proxies_moldes_hoja()
        self._conectar_proxies_vista3d()
        self._conectar_proxies_diseno()

    def _conectar_proxies_entradas(self) -> None:
        pe = self.panel_entradas
        self.panel_izquierdo = pe.panel_izquierdo
        self.txt_altura, self.txt_gajos = pe.txt_altura, pe.txt_gajos
        self.txt_hileras, self.txt_costura = pe.txt_hileras, pe.txt_costura
        self.switch_avanzado, self.panel_avanzado = pe.switch_avanzado, pe.panel_avanzado
        self.txt_boca, self.txt_pestana = pe.txt_boca, pe.txt_pestana
        self.txt_d_mecha, self.txt_p_mecha = pe.txt_d_mecha, pe.txt_p_mecha
        self.txt_alambre, self.txt_varillas = pe.txt_alambre, pe.txt_varillas
        self.txt_llama, self.txt_holgura = pe.txt_llama, pe.txt_holgura
        self.btn_calcular, self.lbl_error = pe.btn_calcular, pe.lbl_error
        self.btn_tema, self.lbl_tema, self.lbl_titulo_app = pe.btn_tema, pe.lbl_tema, pe.lbl_titulo_app

        bp = self.barra_proyecto
        self.lbl_nombre_proyecto = bp.lbl_nombre_proyecto
        self.lbl_estado_proyecto = bp.lbl_estado_proyecto
        self.btn_proyecto_nuevo = bp.btn_proyecto_nuevo
        self.btn_proyecto_abrir = bp.btn_proyecto_abrir
        self.btn_proyecto_guardar = bp.btn_proyecto_guardar
        self.btn_proyecto_guardar_como = bp.btn_proyecto_guardar_como

    def _conectar_proxies_resumen_tablas(self) -> None:
        self.grid_tarjetas = self.pestana_resumen.grid_tarjetas
        self.col_avisos = self.pestana_resumen.col_avisos
        self.lbl_desactualizado = self.pestana_resumen.lbl_desactualizado
        self.selector_tabla = self.pestana_tablas.selector_tabla
        self.lbl_vacio_tablas = self.pestana_tablas.lbl_vacio_tablas
        self.lbl_titulo_tabla = self.pestana_tablas.lbl_titulo_tabla
        self.lbl_resumen_tabla = self.pestana_tablas.lbl_resumen_tabla
        self.lbl_nota_tabla = self.pestana_tablas.lbl_nota_tabla
        self.btn_copiar_tabla = self.pestana_tablas.btn_copiar_tabla
        self.tabla_componente = self.pestana_tablas.tabla_componente
        self.panel_contenido_tablas = self.pestana_tablas.panel_contenido_tablas

    def _conectar_proxies_moldes_hoja(self) -> None:
        m2 = self.pestana_moldes2d
        self.selector_molde = m2.selector_molde
        self.lbl_vacio_moldes = m2.lbl_vacio_moldes
        self.panel_contenido_moldes = m2.panel_contenido_moldes
        self.visor_moldes = m2.visor_moldes
        self.container_viewer_svg = m2.container_viewer_svg
        self.img_svg = m2.img_svg
        self.detector_gestos = m2.detector_gestos
        self.barra_zoom = m2.barra_zoom
        self.lbl_instruccion_zoom = m2.lbl_instruccion_zoom
        self.lbl_zoom_porcentaje = m2.lbl_zoom_porcentaje
        self.btn_zoom_in = m2.btn_zoom_in
        self.btn_zoom_out = m2.btn_zoom_out
        self.btn_ajustar = m2.btn_ajustar
        self.lbl_debug = m2.lbl_debug

        h = self.pestana_hoja
        self.dd_hoja, self.dd_escala = h.dd_hoja, h.dd_escala
        self.selector_pieza_hoja = h.selector_pieza_hoja
        self.selector_lienzo, self.selector_modo_dibujo = h.selector_lienzo, h.selector_modo_dibujo
        self.dd_repeticion_pico_hoja = h.dd_repeticion_pico_hoja
        self.dd_modo_esquema = h.dd_modo_esquema
        self.txt_tam_grupo = h.txt_tam_grupo
        self.txt_ciclo_personalizado = h.txt_ciclo_personalizado
        self.btn_exportar_paquete = h.btn_exportar_paquete
        self.col_resumen_esquema = h.col_resumen_esquema
        self.lbl_resumen_esquema = h.col_resumen_esquema
        self.lbl_error_esquema = h.lbl_error_esquema
        self.lbl_resumen_pico = h.lbl_resumen_pico
        self.lbl_resumen_pico_hoja = h.lbl_resumen_pico
        self.lbl_vacio_hoja = h.lbl_vacio_hoja
        self.panel_contenido_hoja = h.panel_contenido_hoja
        self.visor_hoja = h.visor_hoja
        self.container_viewer_hoja = h.container_viewer_hoja
        self.img_svg_hoja = h.img_svg_hoja
        self.detector_gestos_hoja = h.detector_gestos_hoja
        self.barra_zoom_hoja = h.barra_zoom_hoja
        self.lbl_zoom_hoja_porcentaje = h.lbl_zoom_hoja_porcentaje
        self.btn_zoom_in_hoja = h.btn_zoom_in_hoja
        self.btn_zoom_out_hoja = h.btn_zoom_out_hoja
        self.btn_ajustar_hoja = h.btn_ajustar_hoja
        self.panel_diseno_pico_hoja = h.panel_diseno_pico_hoja

    def _conectar_proxies_vista3d(self) -> None:
        v3 = self.pestana_vista3d
        self.dd_filtro_marca = v3.dd_filtro_marca
        self.btn_agregar_color_catalogo = v3.btn_agregar_color_catalogo
        self.btn_importar_csv = v3.btn_importar_csv
        self.btn_exportar_csv = v3.btn_exportar_csv
        self.dd_modo_sup = v3.dd_modo_sup
        self.txt_tam_bloque_sup = v3.txt_tam_bloque_sup
        self.col_colores_sup = v3.col_colores_sup
        self.btn_agregar_color_sup = v3.btn_agregar_color_sup
        self.chk_mismo_esquema_inf = v3.chk_mismo_esquema_inf
        self.dd_modo_inf = v3.dd_modo_inf
        self.txt_tam_bloque_inf = v3.txt_tam_bloque_inf
        self.col_colores_inf = v3.col_colores_inf
        self.btn_agregar_color_inf = v3.btn_agregar_color_inf
        self.dd_repeticion_picos = v3.dd_repeticion_picos
        self.chk_usar_var_b = v3.chk_usar_var_b
        self.dd_modo_caras_var_a = v3.dd_modo_caras_var_a
        self.col_colores_var_a = v3.col_colores_var_a
        self.dd_modo_caras_var_b = v3.dd_modo_caras_var_b
        self.col_colores_var_b = v3.col_colores_var_b
        self.panel_variante_b = v3.panel_variante_b
        self.fila_previa_sup = v3.fila_previa_sup
        self.col_previa_picos = v3.col_previa_picos
        self.fila_previa_inf = v3.fila_previa_inf
        self.txt_pliego_ancho = v3.txt_pliego_ancho
        self.txt_pliego_alto = v3.txt_pliego_alto
        self.txt_pliegos_paquete = v3.txt_pliegos_paquete
        self.lbl_aviso_colores = v3.lbl_aviso_colores
        self.btn_abrir_visor_3d = v3.btn_abrir_visor_3d
        self.btn_exportar_visor_3d = v3.btn_exportar_visor_3d
        self.sw_mostrar_diseno_3d = v3.sw_mostrar_diseno_3d
        self.btn_copiar_compra = v3.btn_copiar_compra
        self.tabla_compra = v3.tabla_compra
        self.lbl_vacio_3d = v3.lbl_vacio_3d
        self.panel_contenido_3d = v3.panel_contenido_3d

    def _conectar_proxies_diseno(self) -> None:
        d = self.pestana_diseno
        self.selector_seccion_diseno = d.selector_seccion_diseno
        self.selector_variante_pico_diseno = d.selector_variante_pico_diseno
        self.segmento_completo_diseno = d.segmento_completo_diseno
        self.segmento_mitad_diseno = d.segmento_mitad_diseno
        self.selector_lienzo_diseno = d.selector_lienzo_diseno
        self.chk_ver_cuadricula = d.chk_ver_cuadricula
        self.chk_ver_rotulos = d.chk_ver_rotulos
        self.chk_ver_costuras = d.chk_ver_costuras
        self.chk_mostrar_reflejo = d.chk_mostrar_reflejo
        self.selector_interaccion_diseno = d.selector_interaccion_diseno
        self.barra_herramientas_diseno = d.barra_herramientas_diseno
        self.btn_anadir_capa = d.btn_anadir_capa
        self.col_lista_capas = d.col_lista_capas
        self.txt_nombre_capa = d.txt_nombre_capa
        self.txt_pos_x = d.txt_pos_x
        self.txt_pos_y = d.txt_pos_y
        self.txt_ancho_capa = d.txt_ancho_capa
        self.txt_alto_capa = d.txt_alto_capa
        self.chk_proporcion = d.chk_proporcion
        self.slider_rotacion = d.slider_rotacion
        self.lbl_rotacion_val = d.lbl_rotacion_val
        self.btn_reflejo_h = d.btn_reflejo_h
        self.btn_reflejo_v = d.btn_reflejo_v
        self.slider_opacidad = d.slider_opacidad
        self.lbl_opacidad_val = d.lbl_opacidad_val
        self.btn_ajustar_cubrir = d.btn_ajustar_cubrir
        self.btn_ajustar_contener = d.btn_ajustar_contener
        self.btn_ajustar_estirar = d.btn_ajustar_estirar
        self.btn_ajustar_ancho = d.btn_ajustar_ancho
        self.btn_ajustar_alto = d.btn_ajustar_alto
        self.btn_centrar_capa = d.btn_centrar_capa
        self.btn_nudge_left = d.btn_nudge_left
        self.btn_nudge_right = d.btn_nudge_right
        self.btn_nudge_up = d.btn_nudge_up
        self.btn_nudge_down = d.btn_nudge_down
        self.btn_rot_m5 = d.btn_rot_m5
        self.btn_rot_p5 = d.btn_rot_p5
        self.btn_rot_0 = d.btn_rot_0
        self.panel_inspector_capa = d.panel_inspector_capa
        self.btn_exportar_abanico = d.btn_exportar_abanico
        self.btn_exportar_gajos = d.btn_exportar_gajos
        self.btn_exportar_hoja_diseno = d.btn_exportar_hoja_diseno
        self.panel_lateral_diseno = d.panel_lateral_diseno
        self.lbl_vacio_diseno = d.lbl_vacio_diseno
        self.panel_contenido_diseno = d.panel_contenido_diseno
        self.container_viewer_diseno = d.container_viewer_diseno
        self.img_svg_diseno = d.img_svg_diseno
        self.detector_gestos_diseno = d.detector_gestos_diseno
        self.btn_zoom_in_diseno = d.btn_zoom_in_diseno
        self.btn_zoom_out_diseno = d.btn_zoom_out_diseno
        self.btn_ajustar_diseno = d.btn_ajustar_diseno
        self.lbl_zoom_diseno_porcentaje = d.lbl_zoom_diseno_porcentaje
        self.lbl_instruccion_zoom_diseno = d.lbl_instruccion_zoom_diseno
        self.lbl_estado_diseno = d.lbl_estado_diseno
        self.barra_zoom_diseno = d.barra_zoom_diseno
        self.lbl_debug_diseno = d.lbl_debug_diseno
        self.visor_diseno = d.visor

    # Proxies de métodos
    def on_calcular(self, e): self.panel_entradas.on_calcular(e)
    def on_change_input(self, e): self.panel_entradas.on_change_input(e)
    def on_switch_avanzado(self, e): self.panel_entradas.on_switch_avanzado(e)
    def on_proyecto_nuevo(self, e): self.barra_proyecto.on_proyecto_nuevo(e)
    async def on_proyecto_abrir(self, e): await self.barra_proyecto.on_proyecto_abrir(e)
    async def on_proyecto_guardar(self, e): await self.barra_proyecto.on_proyecto_guardar(e)
    async def on_proyecto_guardar_como(self, e): await self.barra_proyecto.on_proyecto_guardar_como(e)
    def on_cambio_pieza_tabla(self, e): self.pestana_tablas.on_cambio_pieza_tabla(e)
    def on_copiar_tabla(self, e): self.pestana_tablas.on_copiar_tabla(e)
    def on_cambio_pieza_molde(self, e): self.pestana_moldes2d.on_cambio_pieza_molde(e)
    def on_cambio_pieza_hoja(self, e): self.pestana_hoja.on_cambio_pieza_hoja(e)
    def on_cambio_esquema_opciones(self, e): self.pestana_hoja.on_cambio_esquema_opciones(e)
    def on_cambio_hoja_opciones(self, e): self.pestana_hoja.on_cambio_hoja_opciones(e)
    async def on_exportar_hoja(self, e): await self.pestana_hoja.on_exportar_hoja(e)
    async def on_exportar_paquete(self, e): await self.pestana_hoja.on_exportar_paquete(e)
    def on_copiar_lista_compra(self, e): self.pestana_vista3d.on_copiar_lista_compra(e)
    def on_cambio_patron_ui(self, e): self.pestana_vista3d.on_cambio_patron_ui(e)
    def on_cambio_color_ciclo_sup(self, idx: int, cid: str) -> None: self.pestana_vista3d.on_cambio_color_ciclo_sup(idx, cid)
    def on_agregar_color_sup(self, e) -> None: self.pestana_vista3d.on_agregar_color_sup(e)
    def on_eliminar_color_ciclo_sup(self, idx: int) -> None: self.pestana_vista3d.on_eliminar_color_ciclo_sup(idx)
    def on_cambio_color_ciclo_inf(self, idx: int, cid: str) -> None: self.pestana_vista3d.on_cambio_color_ciclo_inf(idx, cid)
    def on_agregar_color_inf(self, e) -> None: self.pestana_vista3d.on_agregar_color_inf(e)
    def on_eliminar_color_ciclo_inf(self, idx: int) -> None: self.pestana_vista3d.on_eliminar_color_ciclo_inf(idx)
    def on_cambio_color_variante(self, nombre_var: str, cara_idx: int, cid: str) -> None: self.pestana_vista3d.on_cambio_color_variante(nombre_var, cara_idx, cid)
    async def on_abrir_visor_3d(self, e): await self.pestana_vista3d.on_abrir_visor_3d(e)
    async def on_exportar_visor_3d(self, e): await self.pestana_vista3d.on_exportar_visor_3d(e)
    def on_cambio_seccion_diseno(self, e): self.pestana_diseno.on_cambio_seccion_diseno(e)
    def on_cambio_variante_diseno(self, e): self.pestana_diseno.on_cambio_variante_diseno(e)
    def on_cambio_lienzo_diseno(self, e): self.pestana_diseno.on_cambio_lienzo_diseno(e)
    async def on_anadir_capa_click(self, e): await self.pestana_diseno.inspector.on_anadir_capa_click(e)
    def _empujar_capa(self, dx: float = 0.0, dy: float = 0.0, drot: float = 0.0): self.pestana_diseno.inspector._empujar_capa(dx=dx, dy=dy, drot=drot)
    def _fijar_rotacion_0(self): self.pestana_diseno.inspector._fijar_rotacion_0()
    async def on_exportar_abanico_click(self, e): await self.pestana_diseno.on_exportar_abanico_click(e)
    async def on_exportar_gajos_click(self, e): await self.pestana_diseno.on_exportar_gajos_click(e)
    async def on_exportar_hoja_diseno_click(self, e): await self.pestana_diseno.on_exportar_hoja_diseno_click(e)
    def on_pos_x_change(self, e): self.pestana_diseno.inspector.on_pos_x_change(e)
    def on_pos_y_change(self, e): self.pestana_diseno.inspector.on_pos_y_change(e)
    def on_ancho_capa_change(self, e): self.pestana_diseno.inspector.on_ancho_capa_change(e)
    def on_alto_capa_change(self, e): self.pestana_diseno.inspector.on_alto_capa_change(e)
    def on_nombre_capa_change(self, e): self.pestana_diseno.inspector.on_nombre_capa_change(e)
    def on_proporcion_change(self, e): self.pestana_diseno.inspector.on_proporcion_change(e)
    def on_rotacion_change(self, e): self.pestana_diseno.inspector.on_rotacion_change(e)
    def on_opacidad_change(self, e): self.pestana_diseno.inspector.on_opacidad_change(e)
    def on_reflejo_h_click(self, e): self.pestana_diseno.inspector.on_reflejo_h_click(e)
    def on_reflejo_v_click(self, e): self.pestana_diseno.inspector.on_reflejo_v_click(e)
    def on_ajustar_cubrir_click(self, e): self.pestana_diseno.inspector.on_ajustar_cubrir_click(e)
    def on_ajustar_contener_click(self, e): self.pestana_diseno.inspector.on_ajustar_contener_click(e)
    def on_ajustar_estirar_click(self, e): self.pestana_diseno.inspector.on_ajustar_estirar_click(e)
    def on_ajustar_ancho_click(self, e): self.pestana_diseno.inspector.on_ajustar_ancho_click(e)
    def on_ajustar_alto_click(self, e): self.pestana_diseno.inspector.on_ajustar_alto_click(e)
    def on_centrar_capa_click(self, e): self.pestana_diseno.inspector.on_centrar_capa_click(e)
    def on_toggle_ver_cuadricula(self, e): self.pestana_diseno.on_toggle_ver_cuadricula(e)
    def on_toggle_ver_rotulos(self, e): self.pestana_diseno.on_toggle_ver_rotulos(e)
    def on_toggle_ver_costuras(self, e): self.pestana_diseno.on_toggle_ver_costuras(e)
    def on_toggle_mostrar_reflejo(self, e): self.pestana_diseno.on_toggle_mostrar_reflejo(e)

    # Telemetría y gestos
    def obtener_estado_telemetria(self) -> dict: return self.pestana_diseno.gestor_visor.obtener_estado_telemetria()
    @property
    def _id_recomposicion_diseno(self) -> int: return self.pestana_diseno._id_recomposicion_diseno
    @_id_recomposicion_diseno.setter
    def _id_recomposicion_diseno(self, val: int) -> None: self.pestana_diseno._id_recomposicion_diseno = val
    @property
    def arrastrando_capa(self) -> bool: return self.pestana_diseno.gestor_visor.arrastrando_capa
    @arrastrando_capa.setter
    def arrastrando_capa(self, val: bool) -> None: self.pestana_diseno.gestor_visor.arrastrando_capa = val
    @property
    def modo_interaccion_diseno(self) -> str: return self.pestana_diseno.gestor_visor.modo_interaccion_diseno
    @modo_interaccion_diseno.setter
    def modo_interaccion_diseno(self, val: str) -> None: self.pestana_diseno.gestor_visor.modo_interaccion_diseno = val
    @property
    def telemetria_arrastre_eventos(self) -> int: return self.pestana_diseno.gestor_visor.telemetria_arrastre_eventos
    @telemetria_arrastre_eventos.setter
    def telemetria_arrastre_eventos(self, val: int) -> None: self.pestana_diseno.gestor_visor.telemetria_arrastre_eventos = val
    def _on_gesture_diseno_pan_start(self, e): self.pestana_diseno.gestor_visor._on_gesture_pan_start(e)
    def _on_gesture_diseno_pan_update(self, e): self.pestana_diseno.gestor_visor._on_gesture_pan_update(e)
    def _on_gesture_diseno_pan_end(self, e): self.pestana_diseno.gestor_visor._on_gesture_pan_end(e)
    def _on_gesture_diseno_pan_cancel(self, e): self.pestana_diseno.gestor_visor._on_gesture_pan_cancel(e)
    def _on_gesture_diseno_exit(self, e): self.pestana_diseno.gestor_visor._on_gesture_exit(e)
    def _timeout_arrastre_capa(self): self.pestana_diseno.gestor_visor._timeout_arrastre_capa()
    def _finalizar_arrastre_capa(self): self.pestana_diseno.gestor_visor.finalizar_arrastre_capa()

    # Visores Moldes y Hoja
    def _on_btn_zoom_in(self, e): self.visor_moldes.on_btn_zoom_in(e)
    def _on_btn_zoom_out(self, e): self.visor_moldes.on_btn_zoom_out(e)
    def _on_btn_ajustar(self, e): self.visor_moldes.on_btn_ajustar(e)
    def _on_gesture_double_tap(self, e): self.visor_moldes.on_gesture_double_tap(e)
    def _on_gesture_scroll(self, e): self.visor_moldes.on_gesture_scroll(e)
    def _on_gesture_pan_start(self, e): self.visor_moldes.on_gesture_pan_start(e)
    def _on_gesture_pan_update(self, e): self.visor_moldes.on_gesture_pan_update(e)
    def _on_gesture_pan_end(self, e): self.visor_moldes.on_gesture_pan_end(e)
    def _on_container_size_change(self, e): self.visor_moldes.on_container_size_change(e)
    def _on_container_size_change_hoja(self, e): self.visor_hoja.on_container_size_change(e)
    def _on_container_size_change_diseno(self, e): self.visor_diseno.on_container_size_change(e)

    @property
    def vista_svg(self) -> Optional[VistaSvg]: return self.visor_moldes.vista_svg if hasattr(self, "visor_moldes") else None
    @vista_svg.setter
    def vista_svg(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_moldes"): self.visor_moldes.vista_svg = val
    @property
    def vista_base_svg(self) -> Optional[VistaSvg]: return self.visor_moldes.vista_base_svg if hasattr(self, "visor_moldes") else None
    @vista_base_svg.setter
    def vista_base_svg(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_moldes"): self.visor_moldes.vista_base_svg = val
    @property
    def zona_ancho(self) -> float: return self.visor_moldes.zona_ancho if hasattr(self, "visor_moldes") else 600.0
    @zona_ancho.setter
    def zona_ancho(self, val: float) -> None:
        if hasattr(self, "visor_moldes"): self.visor_moldes.zona_ancho = val
    @property
    def zona_alto(self) -> float: return self.visor_moldes.zona_alto if hasattr(self, "visor_moldes") else 500.0
    @zona_alto.setter
    def zona_alto(self, val: float) -> None:
        if hasattr(self, "visor_moldes"): self.visor_moldes.zona_alto = val
    @property
    def _svg_actual_raw(self) -> str: return self.pestana_moldes2d._svg_actual_raw if hasattr(self, "pestana_moldes2d") else ""
    @_svg_actual_raw.setter
    def _svg_actual_raw(self, val: str) -> None:
        if hasattr(self, "pestana_moldes2d"): self.pestana_moldes2d._svg_actual_raw = val
    @property
    def vista_svg_hoja(self) -> Optional[VistaSvg]: return self.visor_hoja.vista_svg if hasattr(self, "visor_hoja") else None
    @vista_svg_hoja.setter
    def vista_svg_hoja(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_hoja"): self.visor_hoja.vista_svg = val
    @property
    def vista_base_svg_hoja(self) -> Optional[VistaSvg]: return self.visor_hoja.vista_base_svg if hasattr(self, "visor_hoja") else None
    @vista_base_svg_hoja.setter
    def vista_base_svg_hoja(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_hoja"): self.visor_hoja.vista_base_svg = val
    @property
    def zona_ancho_hoja(self) -> float: return self.visor_hoja.zona_ancho if hasattr(self, "visor_hoja") else 600.0
    @zona_ancho_hoja.setter
    def zona_ancho_hoja(self, val: float) -> None:
        if hasattr(self, "visor_hoja"): self.visor_hoja.zona_ancho = val
    @property
    def zona_alto_hoja(self) -> float: return self.visor_hoja.zona_alto if hasattr(self, "visor_hoja") else 500.0
    @zona_alto_hoja.setter
    def zona_alto_hoja(self, val: float) -> None:
        if hasattr(self, "visor_hoja"): self.visor_hoja.zona_alto = val
    @property
    def _svg_hoja_raw(self) -> str: return self.pestana_hoja._svg_hoja_raw if hasattr(self, "pestana_hoja") else ""
    @_svg_hoja_raw.setter
    def _svg_hoja_raw(self, val: str) -> None:
        if hasattr(self, "pestana_hoja"): self.pestana_hoja._svg_hoja_raw = val
    @property
    def vista_svg_diseno(self) -> Optional[VistaSvg]: return self.visor_diseno.vista_svg if hasattr(self, "visor_diseno") else None
    @vista_svg_diseno.setter
    def vista_svg_diseno(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_diseno"): self.visor_diseno.vista_svg = val
    @property
    def vista_base_svg_diseno(self) -> Optional[VistaSvg]: return self.visor_diseno.vista_base_svg if hasattr(self, "visor_diseno") else None
    @vista_base_svg_diseno.setter
    def vista_base_svg_diseno(self, val: Optional[VistaSvg]) -> None:
        if hasattr(self, "visor_diseno"): self.visor_diseno.vista_base_svg = val
    @property
    def zona_ancho_diseno(self) -> float: return self.visor_diseno.zona_ancho if hasattr(self, "visor_diseno") else 600.0
    @zona_ancho_diseno.setter
    def zona_ancho_diseno(self, val: float) -> None:
        if hasattr(self, "visor_diseno"): self.visor_diseno.zona_ancho = val
    @property
    def zona_alto_diseno(self) -> float: return self.visor_diseno.zona_alto if hasattr(self, "visor_diseno") else 500.0
    @zona_alto_diseno.setter
    def zona_alto_diseno(self, val: float) -> None:
        if hasattr(self, "visor_diseno"): self.visor_diseno.zona_alto = val
