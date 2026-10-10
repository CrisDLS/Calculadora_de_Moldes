import pytest
import matplotlib
matplotlib.use("Agg")
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from ui.modulos_moldes.graficas_trompo_estrella import figura_moldes, figura_perfil

@pytest.fixture
def calc_resultado_avanzado():
    e = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    return TrompoEstrellaCalculator().calcular(e)

@pytest.fixture
def calc_resultado_simple():
    e = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=False)
    return TrompoEstrellaCalculator().calcular(e)

@pytest.fixture
def tema_test():
    return {
        "fondo_figura": "#000000",
        "fondo_grafica": "#111111",
        "texto": "#ffffff",
        "lineas": "#aaaaaa",
        "acento": "#ff00ff",
        "pestana": "#ff9900"
    }

def test_figura_moldes(calc_resultado_avanzado, calc_resultado_simple, tema_test):
    # Avanzado (tiene pestaña)
    fig_av = figura_moldes(calc_resultado_avanzado, tema_test)
    assert len(fig_av.axes) == 3
    
    # 17 + 12 + 25 puntos marcados?
    # En plt, cada plot de puntos o líneas es una Line2D, fill_between es PolyCollection.
    # En cono inferior, ax3
    ax3 = fig_av.axes[2]
    # Comprobar que hay un PolyCollection para la pestaña en avanzado
    assert len(ax3.collections) == 1
    
    # Simple (sin pestaña)
    fig_sim = figura_moldes(calc_resultado_simple, tema_test)
    assert len(fig_sim.axes) == 3
    assert len(fig_sim.axes[2].collections) == 0

def test_figura_perfil(calc_resultado_simple, tema_test):
    fig = figura_perfil(calc_resultado_simple, tema_test)
    assert len(fig.axes) == 1
    # Verifica que renderiza bien sin errores
    assert len(fig.axes[0].lines) > 0
def test_resultados_desactualizados():
    import customtkinter as ctk
    from ui.modulos_moldes.vista_trompo_estrella import VistaTrompoEstrella
    
    root = ctk.CTk()
    v = VistaTrompoEstrella(root)
    
    v.entradas['altura'].insert(0, '950')
    v.entradas['gajos'].insert(0, '30')
    v.entradas['hileras'].insert(0, '2')
    v.entradas['costura'].insert(0, '1')
    
    v._calcular()
    assert v.resultado is not None
    assert v.datos_desactualizados is False
    assert v.canvas_widget is not None
    assert v.figura_actual is not None
    
    # Simular cambio en el campo "altura"
    v.variables['altura'].set('900')
    
    assert v.datos_desactualizados is True
    assert v.resultado is None
    assert v.lbl_error.cget("text") == "Cambiaste los datos: pulsa Calcular"
    
    # Comprobar si se limpia
    assert v.canvas_widget is None
    assert v.figura_actual is None
    assert len(v.tab_widgets["Cono superior"]['tree'].get_children()) == 0
