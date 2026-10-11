import pytest
import os
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.esquema import EsquemaDiseno
from logic.exportacion.paquete import (
    parsear_ciclo,
    resumen_esquema,
    generar_paquete,
    guardar_paquete,
)


def test_parsear_ciclo_valido():
    c = parsear_ciclo("0, 1, 2E, 1E")
    assert c == [(0, False), (1, False), (2, True), (1, True)]

    # Con mayúsculas y minúsculas y espacios variados
    c2 = parsear_ciclo(" 0 , 1e , 2 , 3E ")
    assert c2 == [(0, False), (1, True), (2, False), (3, True)]


def test_parsear_ciclo_errores():
    with pytest.raises(ValueError, match="no puede estar vacío"):
        parsear_ciclo("")

    with pytest.raises(ValueError, match="no puede estar vacío"):
        parsear_ciclo("   ")

    with pytest.raises(ValueError, match="Elemento inválido en posición 2"):
        parsear_ciclo("0, abc, 2E")

    with pytest.raises(ValueError, match="Elemento inválido en posición 1"):
        parsear_ciclo("E1, 2")


def test_resumen_esquema_tres_ejemplos_usuario():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(100, 20, 2, 1)  # N=20, 2 hileras (num_piramides = 20*2 = 40)
    res = calc.calcular(ent)

    # 1. N=20, Repetición G=5 (4 grupos de 1-2-3-4-5)
    esq_rep = EsquemaDiseno("repeticion", 5)
    lineas_rep = resumen_esquema(esq_rep, ent, res)
    assert len(lineas_rep) == 5
    # En repeticion 20/5 = 4 repeticiones, cada motivo aparece 4 veces
    # superior: 20 piezas total -> 1 por gajo -> 4 por motivo
    # pico: 40 pirámides × 4 = 160 triángulos -> 8 por gajo -> 32 por motivo
    # inferior: 20 piezas total -> 1 por gajo -> 4 por motivo
    assert lineas_rep[0] == "Molde 0: cono superior ×4 · pico ×32 · cono inferior ×4"

    # 2. N=20, Central con espejo G=5 (motivo central 0 sin espejo, vecinos 1 y 2 espejeados)
    esq_cen = EsquemaDiseno("central_espejo", 5)
    lineas_cen = resumen_esquema(esq_cen, ent, res)
    # Ciclo de central_espejo con G=5: m=3 -> [ (2,True), (1,True), (0,False), (1,False), (2,False) ]
    # Motivo 0: 4 gajos sin espejo
    # Motivo 1: 4 en espejo, 4 sin espejo (8 gajos total)
    # Motivo 2: 4 en espejo, 4 sin espejo (8 gajos total)
    assert len(lineas_cen) == 3
    assert lineas_cen[0] == "Molde 0: cono superior ×4 · pico ×32 · cono inferior ×4"
    assert lineas_cen[1] == "Molde 1: cono superior ×8 · pico ×64 · cono inferior ×8 (de ellos 4 en espejo)"
    assert lineas_cen[2] == "Molde 2: cono superior ×8 · pico ×64 · cono inferior ×8 (de ellos 4 en espejo)"

    # 3. N=20, Espejo total G=4 (mitad y mitad en espejo: 0, 1, 1E, 0E)
    esq_esp = EsquemaDiseno("espejo_total", 4)
    lineas_esp = resumen_esquema(esq_esp, ent, res)
    # 20/4 = 5 repeticiones
    # Motivo 0: 5 sin espejo, 5 en espejo (10 gajos total)
    # Motivo 1: 5 sin espejo, 5 en espejo (10 gajos total)
    assert len(lineas_esp) == 2
    assert lineas_esp[0] == "Molde 0: cono superior ×10 · pico ×80 · cono inferior ×10 (de ellos 5 en espejo)"
    assert lineas_esp[1] == "Molde 1: cono superior ×10 · pico ×80 · cono inferior ×10 (de ellos 5 en espejo)"


def test_generar_paquete_y_guardar(tmp_path):
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(380, 30, 2, 1, usar_parametros_avanzados=True, pestana_boca=4)
    res = calc.calcular(ent)
    esq = EsquemaDiseno("repeticion", 5)

    paquete = generar_paquete(res, ent, esq, hoja="carta", escala="auto")
    esperados = {
        "hoja_cono_superior.svg",
        "hoja_pico.svg",
        "hoja_cono_inferior.svg",
        "perfil_armado.svg",
        "conjunto_moldes.svg",
    }
    assert set(paquete.keys()) == esperados

    for nom, svg_content in paquete.items():
        assert svg_content.startswith("<?xml")
        assert "</svg>" in svg_content

    # Guardar en tmp_path
    carpeta_destino = str(tmp_path / "exportados")
    rutas = guardar_paquete(carpeta_destino, paquete, sobrescribir=False)
    assert len(rutas) == 5
    for r in rutas:
        assert os.path.exists(r)
        with open(r, "r", encoding="utf-8") as f:
            assert "</svg>" in f.read()

    # Intentar guardar sin sobrescribir debe lanzar FileExistsError
    with pytest.raises(FileExistsError):
        guardar_paquete(carpeta_destino, paquete, sobrescribir=False)

    # Con sobrescribir=True debe permitirlo
    rutas_re = guardar_paquete(carpeta_destino, paquete, sobrescribir=True)
    assert len(rutas_re) == 5
