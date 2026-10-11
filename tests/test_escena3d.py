import pytest
import json
import math
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.pintura import EsquemaPintura
from logic.exportacion.escena3d import escena_a_dict

def test_escena_a_dict_estructura_y_serializacion():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    res = calc.calcular(inp)
    
    pintura = EsquemaPintura(color_superior="rojo", color_pico="amarillo", color_inferior="negro")
    escena = escena_a_dict(inp, res, pintura)
    
    # Debe ser 100% serializable a JSON
    json_str = json.dumps(escena)
    assert len(json_str) > 0
    
    # Claves requeridas
    assert "metadata" in escena
    assert "vertices" in escena
    assert "caras" in escena
    assert "anillos" in escena
    assert "texturas" in escena
    assert escena["texturas"] == {}
    
    # Triángulos exclusivamente
    for c in escena["caras"]:
        assert len(c["indices"]) == 3
        assert len(c["normal"]) == 3
        # Normal debe tener norma ~ 1.0
        norm = math.hypot(*c["normal"])
        assert norm == pytest.approx(1.0, abs=1e-3)
        assert c["color"].startswith("#")

    # z de la boca debe estar en z = 0
    idx_boca = escena["anillos"]["boca"]
    for idx in idx_boca:
        v = escena["vertices"][idx]
        assert v[2] == pytest.approx(0.0, abs=1e-4)

    # Cantidad total de caras triangulares:
    # 30 sup (triángulos) + 30 inf (cuadriláteros divididos en 2 = 60) + 30 * 2 hileras * 4 caras pirámide (240 triángulos) = 330 triángulos
    assert len(escena["caras"]) == 30 + 60 + 240
