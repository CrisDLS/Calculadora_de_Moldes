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

def test_controlador_tablas_y_svg_simple_y_desactualizado():
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    c.avanzado = False

    vm = c.calcular()
    assert vm.mensaje_error is None

    # Tablas expuestas en controlador y view model
    assert len(c.tablas) == 3
    assert len(vm.tablas) == 3
    t_sup, t_pic, t_inf = c.tablas
    assert len(t_sup.filas) == 17
    assert len(t_pic.filas) == 12
    assert len(t_inf.filas) == 25
    # En modo simple, cono inferior no lleva nota de pestaña
    assert t_inf.nota is None

    # SVGs expuestos en controlador y view model
    assert "<svg" in c.svg_conjunto
    assert "<svg" in c.svg_superior
    assert "<svg" in c.svg_pico
    assert "<svg" in c.svg_inferior
    assert vm.svg_conjunto == c.svg_conjunto
    assert vm.svg_superior == c.svg_superior

    # Al marcar desactualizado, se vacían
    c.marcar_desactualizado()
    assert c.tablas == []
    assert c.svg_conjunto == ""
    assert c.svg_superior == ""
    assert c.svg_pico == ""
    assert c.svg_inferior == ""

    vm_des = c.get_view_model()
    assert vm_des.desactualizado is True
    assert vm_des.tablas == []
    assert vm_des.svg_conjunto == ""

def test_controlador_tablas_avanzado_con_nota():
    c = ControladorTrompo()
    c.altura = "950"
    c.gajos = "30"
    c.hileras = "2"
    c.costura = "1"
    c.avanzado = True
    c.pestana = "4"
    c.boca = "105"

    vm = c.calcular()
    assert vm.mensaje_error is None
    assert len(c.tablas) == 3
    t_inf = c.tablas[2]
    assert t_inf.nota is not None
    assert "pestaña de 4.00 cm" in t_inf.nota

    # Al limpiar, se vacían
    c.limpiar()
    assert c.tablas == []
    assert c.svg_conjunto == ""
    assert c.svg_superior == ""

def test_controlador_cambiar_estilo():
    from logic.exportacion.estilos import PANTALLA_OSCURO, PANTALLA_CLARO
    c = ControladorTrompo()
    assert c.estilo_svg == PANTALLA_OSCURO

    c.calcular()
    res_orig = c.resultado
    assert PANTALLA_OSCURO.contorno in c.svg_conjunto

    # Cambiar estilo sin recalcular
    vm = c.cambiar_estilo(PANTALLA_CLARO)
    assert c.estilo_svg == PANTALLA_CLARO
    assert c.resultado is res_orig  # No recalcula
    assert PANTALLA_CLARO.contorno in c.svg_conjunto
    assert vm.svg_conjunto == c.svg_conjunto
