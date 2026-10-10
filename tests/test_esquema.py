import pytest
from logic.diseno.esquema import EsquemaDiseno, AsignacionGajo

def test_esquema_repeticion():
    eq = EsquemaDiseno(modo="repeticion", k=4)
    asig = eq.asignar(16)
    assert len(asig) == 16
    for i in range(16):
        assert asig[i].gajo == i
        assert asig[i].motivo == i % 4
        assert asig[i].espejo is False

def test_esquema_espejo_total():
    eq = EsquemaDiseno(modo="espejo_total", k=4)
    asig = eq.asignar(16)
    assert len(asig) == 16
    # Ciclo de 8: 0,1,2,3 (False), 3,2,1,0 (True)
    esperado = [
        (0, False), (1, False), (2, False), (3, False),
        (3, True),  (2, True),  (1, True),  (0, True)
    ]
    for i in range(16):
        m_esp, e_esp = esperado[i % 8]
        assert asig[i].motivo == m_esp
        assert asig[i].espejo == e_esp

def test_esquema_personalizado():
    ciclo = [(0, False), (1, True), (0, True)]
    eq = EsquemaDiseno(modo="personalizado", k=3, ciclo=ciclo)
    asig = eq.asignar(6)
    assert len(asig) == 6
    assert asig[0].motivo == 0 and asig[0].espejo is False
    assert asig[1].motivo == 1 and asig[1].espejo is True
    assert asig[2].motivo == 0 and asig[2].espejo is True
    assert asig[3].motivo == 0 and asig[3].espejo is False

def test_esquema_no_divisible():
    eq = EsquemaDiseno(modo="repeticion", k=3)
    with pytest.raises(ValueError) as exc:
        eq.asignar(10)
    msg = str(exc.value)
    assert "Sobran 1" in msg
    assert "1, 2, 5, 10" in msg

def test_esquema_personalizado_sin_ciclo():
    eq = EsquemaDiseno(modo="personalizado", k=3)
    with pytest.raises(ValueError, match="Modo personalizado requiere definir un ciclo"):
        eq.asignar(6)
