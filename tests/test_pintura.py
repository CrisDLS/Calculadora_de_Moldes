from logic.geometria.malla_trompo import Cara
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, color_de_cara

def test_color_de_cara_defaults():
    pintura = EsquemaPintura(color_superior="rojo", color_pico="verde_bandera", color_inferior="azul_rey")
    cara_sup = Cara([0, 1, 2], "superior", 0, None, None, [0, 0, 1], [])
    cara_pic = Cara([0, 1, 2], "pico", 0, 0, 0, [1, 0, 0], [])
    cara_inf = Cara([0, 1, 2, 3], "inferior", 0, None, None, [0, 0, -1], [])

    assert color_de_cara(pintura, cara_sup) == "rojo"
    assert color_de_cara(pintura, cara_pic) == "verde_bandera"
    assert color_de_cara(pintura, cara_inf) == "azul_rey"

def test_color_de_cara_por_motivo():
    esq_diseno = EsquemaDiseno("repeticion", 2)
    pintura = EsquemaPintura(
        color_superior="blanco",
        colores_motivos={
            0: {"superior": "rojo", "pico": "negro"},
            1: {"superior": "azul_rey", "pico": "blanco"},
        }
    )
    cara_gajo0 = Cara([0, 1, 2], "superior", 0, None, None, [0, 0, 1], [])
    cara_gajo1 = Cara([0, 1, 2], "superior", 1, None, None, [0, 0, 1], [])

    assert color_de_cara(pintura, cara_gajo0, esq_diseno, 20) == "rojo"
    assert color_de_cara(pintura, cara_gajo1, esq_diseno, 20) == "azul_rey"

def test_color_de_cara_especifica_prioridad():
    pintura = EsquemaPintura(
        color_superior="blanco",
        colores_caras_especificas={"superior_5": "dorado"}
    )
    cara_esp = Cara([0, 1, 2], "superior", 5, None, None, [0, 0, 1], [])
    cara_otra = Cara([0, 1, 2], "superior", 6, None, None, [0, 0, 1], [])

    assert color_de_cara(pintura, cara_esp) == "dorado"
    assert color_de_cara(pintura, cara_otra) == "blanco"
