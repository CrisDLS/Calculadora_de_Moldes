"""Pruebas del controlador para F3: esquema de diseño, hoja de trazo y proyectos."""

import os
import pytest
from app_flet.controlador import ControladorTrompo
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO, IMPRESION


def test_controlador_esquema_y_hoja_defecto():
    ctrl = ControladorTrompo()
    vm = ctrl.calcular()
    assert vm.mensaje_error is None
    assert vm.svg_hoja != ""
    assert vm.esquema_error is None
    assert len(vm.resumen_esquema) > 0
    # Por defecto: repeticion, grupo 5, carta, auto, superior
    assert ctrl.esquema_modo == "repeticion"
    assert ctrl.esquema_tam_grupo == 5
    assert ctrl.hoja_tipo == "carta"
    assert ctrl.hoja_escala == "auto"
    assert ctrl.hoja_pieza == "superior"


def test_controlador_cambio_opciones_hoja_no_recalcula_modelo():
    ctrl = ControladorTrompo()
    ctrl.calcular()
    res1 = ctrl.resultado

    # Cambiar pieza de hoja
    ctrl.actualizar_opciones_hoja(pieza="pico")
    assert ctrl.resultado is res1  # Mismo objeto de resultado, no recalculó
    assert ctrl.hoja_pieza == "pico"
    assert ctrl.svg_hoja != ""

    # Cambiar hoja y escala
    ctrl.actualizar_opciones_hoja(tipo="a4", escala="20")
    assert ctrl.resultado is res1
    assert ctrl.hoja_tipo == "a4"
    assert ctrl.hoja_escala == "20"
    assert ctrl.svg_hoja != ""


def test_controlador_esquema_error_y_personalizado():
    ctrl = ControladorTrompo()
    ctrl.calcular()

    # Esquema inválido: central con espejo pero tamaño de grupo par
    ctrl.actualizar_esquema(modo="central_espejo", tam_grupo=4)
    vm = ctrl.get_view_model()
    assert vm.esquema_error is not None
    assert "impar" in vm.esquema_error
    assert vm.svg_hoja == ""

    # Esquema personalizado válido (longitud 5 divide a 30)
    ctrl.actualizar_esquema(modo="personalizado", ciclo_texto="0, 1, 2, 1E, 0")
    vm = ctrl.get_view_model()
    assert vm.esquema_error is None
    assert vm.svg_hoja != ""

    # Esquema personalizado inválido
    ctrl.actualizar_esquema(modo="personalizado", ciclo_texto="0, 1X, invalid")
    vm = ctrl.get_view_model()
    assert vm.esquema_error is not None
    assert "Formato" in vm.esquema_error
    assert vm.svg_hoja == ""


def test_controlador_proyecto_ciclo_vida(tmp_path):
    ctrl = ControladorTrompo()
    ctrl.altura = "900"
    ctrl.gajos = "24"
    ctrl.hileras = "3"
    ctrl.costura = "1.5"
    ctrl.actualizar_esquema(modo="espejo_total", tam_grupo=4)
    ctrl.actualizar_opciones_hoja(tipo="a4", escala="15", pieza="inferior")
    ctrl.calcular()

    # Exportar a proyecto
    proy = ctrl.a_proyecto()
    assert proy.entrada.altura_cuerpo == 900.0
    assert proy.entrada.num_gajos == 24
    assert proy.esquema.modo == "espejo_total"
    assert proy.esquema.tam_grupo == 4
    assert proy.hoja == "a4"
    assert proy.escala == "15"

    # Guardar en archivo
    archivo_json = str(tmp_path / "test_globo.json")
    ok, msg = ctrl.guardar(archivo_json)
    assert ok is True
    assert ctrl.sin_guardar is False
    assert ctrl.nombre_proyecto == "test_globo"
    assert ctrl.ruta_proyecto == archivo_json

    # Modificar valor -> sin_guardar pasa a True
    ctrl.actualizar_campo("altura", "920")
    assert ctrl.sin_guardar is True

    # Nuevo proyecto
    ctrl.nuevo()
    assert ctrl.nombre_proyecto == "Sin título"
    assert ctrl.ruta_proyecto is None
    assert ctrl.sin_guardar is False
    assert ctrl.altura == "950"

    # Abrir archivo previamente guardado
    ok_abrir, msg_abrir = ctrl.abrir(archivo_json)
    assert ok_abrir is True
    assert ctrl.altura == "900.0" or ctrl.altura == "900"
    assert ctrl.gajos == "24"
    assert ctrl.esquema_modo == "espejo_total"
    assert ctrl.esquema_tam_grupo == 4
    assert ctrl.hoja_tipo == "a4"
    assert ctrl.hoja_escala == "15"
    assert ctrl.sin_guardar is False
    assert ctrl.resultado is not None
