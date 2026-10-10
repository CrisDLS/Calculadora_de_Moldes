import pytest
from app_flet.controlador import ControladorTrompo

def test_controlador_simple():
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    c.avanzado = False
    
    vm = c.calcular()
    assert vm.mensaje_error is None
    assert len(vm.tarjetas) == 8
    
    tj_dict = {tj.etiqueta: tj.valor for tj in vm.tarjetas}
    assert "Ancho máx. de gajo (cm)" in tj_dict
    assert "Volumen (m³)" in tj_dict
    
    # Test desactualizado
    c.marcar_desactualizado()
    vm2 = c.get_view_model()
    assert vm2.desactualizado is True

def test_controlador_avanzado():
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    c.avanzado = True
    c.boca = "105"
    vm = c.calcular()
    assert vm.mensaje_error is None
    assert len(vm.tarjetas) == 15
    tj_dict = {tj.etiqueta: tj.valor for tj in vm.tarjetas}
    assert "Sí" == tj_dict.get("Viable", "")

def test_controlador_error():
    c = ControladorTrompo()
    c.altura = "abc"
    vm = c.calcular()
    assert vm.mensaje_error is not None
    assert "altura" in vm.mensaje_error.lower()
