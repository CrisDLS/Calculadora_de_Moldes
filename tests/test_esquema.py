import pytest
from logic.diseno.esquema import EsquemaDiseno, AsignacionGajo

def test_esquema_repeticion():
    # N=20, repeticion, G=5 → 5 motivos, 4 repeticiones, ningún espejo
    eq = EsquemaDiseno(modo="repeticion", tam_grupo=5)
    assert eq.motivos_a_dibujar == 5
    assert eq.repeticiones(20) == 4
    
    asig = eq.asignar(20)
    assert len(asig) == 20
    
    res = eq.resumen_motivos(asig)
    for i in range(5):
        assert res[i] == (4, 0, 4) # total, en_espejo, sin_espejo
        
    # motivo i va en gajos i, i+5, i+10, i+15
    for i in range(5):
        for j in range(4):
            g = i + j * 5
            assert asig[g].motivo == i
            assert asig[g].espejo is False

def test_esquema_central_espejo():
    # N=20, central_espejo, G=5 → 3 motivos
    # ciclo [(2,True), (1,True), (0,False), (1,False), (2,False)]
    eq = EsquemaDiseno(modo="central_espejo", tam_grupo=5)
    assert eq.motivos_a_dibujar == 3
    assert eq.repeticiones(20) == 4
    
    asig = eq.asignar(20)
    assert len(asig) == 20
    
    res = eq.resumen_motivos(asig)
    assert res[0] == (4, 0, 4)
    assert res[1] == (8, 4, 4)
    assert res[2] == (8, 4, 4)
    
    ciclo = eq._generar_ciclo()
    assert ciclo == [(2, True), (1, True), (0, False), (1, False), (2, False)]
    
    # Invariante de simetría: al revés invertimos espejo salvo el 0
    c_rev = list(reversed(ciclo))
    c_sym = []
    for m, e in c_rev:
        if m == 0:
            c_sym.append((m, e))
        else:
            c_sym.append((m, not e))
    assert c_sym == ciclo

def test_esquema_espejo_total():
    # N=20, espejo_total, G=4 → 2 motivos, 5 repeticiones
    # ciclo [(0,False), (1,False), (1,True), (0,True)]
    eq = EsquemaDiseno(modo="espejo_total", tam_grupo=4)
    assert eq.motivos_a_dibujar == 2
    assert eq.repeticiones(20) == 5
    
    asig = eq.asignar(20)
    res = eq.resumen_motivos(asig)
    assert res[0] == (10, 5, 5)
    assert res[1] == (10, 5, 5)
    
    ciclo = eq._generar_ciclo()
    assert ciclo == [(0, False), (1, False), (1, True), (0, True)]
    
    # Invariante
    c_rev = list(reversed(ciclo))
    c_sym = [(m, not e) for m, e in c_rev]
    assert c_sym == ciclo

def test_esquema_central_espejo_g1():
    eq = EsquemaDiseno("central_espejo", 1)
    assert eq.motivos_a_dibujar == 1
    assert eq._generar_ciclo() == [(0, False)]

def test_esquema_errores_paridad():
    with pytest.raises(ValueError, match="impar"):
        eq = EsquemaDiseno("central_espejo", 4)
        eq._generar_ciclo()
        
    with pytest.raises(ValueError, match="par"):
        eq = EsquemaDiseno("espejo_total", 5)
        eq._generar_ciclo()

def test_esquema_errores_divisibilidad():
    # N=16 con G=5
    eq1 = EsquemaDiseno("repeticion", 5)
    with pytest.raises(ValueError) as exc1:
        eq1.asignar(16)
    assert "Sobran 1" in str(exc1.value)
    
    # N=20 con G=3 central_espejo
    eq2 = EsquemaDiseno("central_espejo", 3)
    with pytest.raises(ValueError) as exc2:
        eq2.asignar(20)
    assert "Sobran 2" in str(exc2.value)
    assert "[1, 5]" in str(exc2.value)

def test_esquema_personalizado():
    ciclo = [(0, False), (1, True), (0, True)]
    eq = EsquemaDiseno(modo="personalizado", tam_grupo=3, ciclo=ciclo)
    asig = eq.asignar(6)
    assert len(asig) == 6
    assert asig[0].motivo == 0 and asig[0].espejo is False
    assert asig[1].motivo == 1 and asig[1].espejo is True
    assert asig[2].motivo == 0 and asig[2].espejo is True
    
    res = eq.resumen_motivos(asig)
    assert res[0] == (4, 2, 2)
    assert res[1] == (2, 2, 0)
