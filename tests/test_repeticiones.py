"""Pruebas para repeticiones_por_cara en conos y picos."""

import pytest
from logic.models import BalloonInput
from logic.diseno.config_seccion import ConfigSeccion
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.diseno_pico import EsquemaDisenoPico, repeticiones_por_cara


def test_repeticiones_conos_30_gajos() -> None:
    """Verifica la suma y desglose de repeticiones de conos con N=30."""
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )

    # 1. Modo repetición (G=5) -> 5 motivos de 6 caras completas cada uno
    cfg_rep = ConfigSeccion(
        seccion="superior",
        esquema=EsquemaDiseno(modo="repeticion", tam_grupo=5),
    )
    res_rep = repeticiones_por_cara("superior", entrada, cfg_rep)
    assert sum(res_rep.values()) == 30
    assert len(res_rep) == 5
    for m in range(5):
        assert res_rep[(None, m)] == 6

    # 2. Modo central_espejo (G=5) -> central: 6, laterales 1 y 2: 12 cada uno
    cfg_cen = ConfigSeccion(
        seccion="superior",
        esquema=EsquemaDiseno(modo="central_espejo", tam_grupo=5),
    )
    res_cen = repeticiones_por_cara("superior", entrada, cfg_cen)
    assert sum(res_cen.values()) == 30
    assert res_cen[(None, 0)] == 6
    assert res_cen[(None, 1)] == 12
    assert res_cen[(None, 2)] == 12

    # 3. Modo espejo_total (G=6) -> 3 motivos de 10 caras completas cada uno
    cfg_esp = ConfigSeccion(
        seccion="superior",
        esquema=EsquemaDiseno(modo="espejo_total", tam_grupo=6),
    )
    res_esp = repeticiones_por_cara("superior", entrada, cfg_esp)
    assert sum(res_esp.values()) == 30
    assert len(res_esp) == 3
    for m in range(3):
        assert res_esp[(None, m)] == 10

    # 4. Modo mitad en cono inferior con central_espejo -> mitad + espejo = 1 cara
    cfg_inf_mitad = ConfigSeccion(
        seccion="inferior",
        esquema=EsquemaDiseno(modo="central_espejo", tam_grupo=5),
        dibujar="mitad",
    )
    res_inf_mitad = repeticiones_por_cara("inferior", entrada, cfg_inf_mitad)
    assert sum(res_inf_mitad.values()) == 30
    assert res_inf_mitad[(None, 0)] == 6
    assert res_inf_mitad[(None, 1)] == 12
    assert res_inf_mitad[(None, 2)] == 12


def test_repeticiones_pico_una_cara_y_mitad() -> None:
    """Verifica A + B = 240 caras en pico (una_cara y mitad) con N=30, H=2 en todos los repartos."""
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )

    modos_reparto = [
        ("todas_a", False, 240, 0),
        ("alternar_gajo", True, 120, 120),
        ("alternar_hilera", True, 120, 120),
        ("ajedrez", True, 120, 120),
    ]

    for modo_diseno in ("una_cara", "mitad"):
        for modo_rep, usar_b, exp_a, exp_b in modos_reparto:
            esq_pico = EsquemaDisenoPico(
                modo_repeticion=modo_rep,
                usar_variante_b=usar_b,
            )
            cfg = ConfigSeccion(
                seccion="pico",
                esquema_pico=esq_pico,
                diseno_modo=modo_diseno,
            )
            res = repeticiones_por_cara("pico", entrada, cfg)

            cant_a = res.get(("A", 0), 0)
            cant_b = res.get(("B", 0), 0)
            assert cant_a + cant_b == 240, f"Fallo en {modo_diseno} con {modo_rep}: suma={cant_a + cant_b}"
            assert cant_a == exp_a, f"Fallo en A con {modo_diseno} y {modo_rep}: obtuve {cant_a}, esperaba {exp_a}"
            assert cant_b == exp_b, f"Fallo en B con {modo_diseno} y {modo_rep}: obtuve {cant_b}, esperaba {exp_b}"


def test_repeticiones_pico_completo() -> None:
    """Verifica que en modo completo cada cara k aparezca una vez por pirámide (60 en total por k)."""
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=2,
        ancho_costura=1.0,
    )

    # 1. Todas A en completo: cada k aparece 60 veces en A y 0 en B
    cfg_todas_a = ConfigSeccion(
        seccion="pico",
        esquema_pico=EsquemaDisenoPico(modo_repeticion="todas_a", usar_variante_b=False),
        diseno_modo="completo",
    )
    res_a = repeticiones_por_cara("pico", entrada, cfg_todas_a)
    for k in range(4):
        tot_k = res_a.get(("A", k), 0) + res_a.get(("B", k), 0)
        assert tot_k == 60, f"Cara {k} debería sumar 60 en total, dio {tot_k}"
        assert res_a[("A", k)] == 60
        assert res_a.get(("B", k), 0) == 0

    # 2. Alternar hilera en completo: cada k aparece 30 en A y 30 en B -> 60 en total
    cfg_alt = ConfigSeccion(
        seccion="pico",
        esquema_pico=EsquemaDisenoPico(modo_repeticion="alternar_hilera", usar_variante_b=True),
        diseno_modo="completo",
    )
    res_alt = repeticiones_por_cara("pico", entrada, cfg_alt)
    for k in range(4):
        tot_k = res_alt.get(("A", k), 0) + res_alt.get(("B", k), 0)
        assert tot_k == 60, f"Cara {k} debería sumar 60 en total, dio {tot_k}"
        assert res_alt[("A", k)] == 30
        assert res_alt[("B", k)] == 30


def test_repeticiones_pico_hileras_impares() -> None:
    """Verifica caso con 3 hileras y alternar_hilera: A=240, B=120 caras (una_cara)."""
    entrada = BalloonInput(
        altura_cuerpo=950.0,
        num_gajos=30,
        num_hileras_picos=3,
        ancho_costura=1.0,
    )
    esq_pico = EsquemaDisenoPico(
        modo_repeticion="alternar_hilera",
        usar_variante_b=True,
    )
    cfg = ConfigSeccion(
        seccion="pico",
        esquema_pico=esq_pico,
        diseno_modo="una_cara",
    )
    res = repeticiones_por_cara("pico", entrada, cfg)
    assert res[("A", 0)] == 240
    assert res[("B", 0)] == 120
    assert res[("A", 0)] + res[("B", 0)] == 360
