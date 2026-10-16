from logic.models import BalloonInput, Condiciones
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.pintura import VariantePico
from logic.diseno.diseno_pico import EsquemaDisenoPico, resumen_pico
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto

def test_conteo_piramides_y_triangulos_modos_repeticion():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    # 1. todas_a
    esq_todas = EsquemaDisenoPico(modo_repeticion="todas_a", usar_variante_b=True)
    r_todas = resumen_pico(esq_todas, inp, res)
    assert r_todas.total_piramides == 60
    assert r_todas.piramides_a == 60
    assert r_todas.piramides_b == 0
    assert r_todas.total_triangulos == 240
    assert r_todas.triangulos_a == 240
    assert r_todas.triangulos_b == 0

    # 2. alternar_gajo (30 gajos -> 15 gajos pares x 2 hileras = 30 A, 15 impares x 2 = 30 B)
    esq_gajo = EsquemaDisenoPico(modo_repeticion="alternar_gajo", usar_variante_b=True)
    r_gajo = resumen_pico(esq_gajo, inp, res)
    assert r_gajo.piramides_a == 30
    assert r_gajo.piramides_b == 30
    assert r_gajo.triangulos_a == 120
    assert r_gajo.triangulos_b == 120

    # 3. alternar_hilera (2 hileras -> hilera 0: 30 A, hilera 1: 30 B)
    esq_hilera = EsquemaDisenoPico(modo_repeticion="alternar_hilera", usar_variante_b=True)
    r_hilera = resumen_pico(esq_hilera, inp, res)
    assert r_hilera.piramides_a == 30
    assert r_hilera.piramides_b == 30
    assert r_hilera.triangulos_a == 120
    assert r_hilera.triangulos_b == 120

    # 4. ajedrez (30 x 2 = 60 -> 30 A y 30 B)
    esq_ajedrez = EsquemaDisenoPico(modo_repeticion="ajedrez", usar_variante_b=True)
    r_ajedrez = resumen_pico(esq_ajedrez, inp, res)
    assert r_ajedrez.piramides_a == 30
    assert r_ajedrez.piramides_b == 30
    assert r_ajedrez.triangulos_a == 120
    assert r_ajedrez.triangulos_b == 120

def test_conteo_colores_en_resumen():
    calc = TrompoEstrellaCalculator()
    inp = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(inp)

    var_a = VariantePico(modo_caras="igual", color_0="azul_rey")
    var_b = VariantePico(modo_caras="alternado", color_0="blanco", color_1="rojo")
    esq = EsquemaDisenoPico(
        modo_repeticion="alternar_gajo",
        usar_variante_b=True,
        variante_a=var_a,
        variante_b=var_b
    )

    r = resumen_pico(esq, inp, res)
    # Variante A (30 pirámides x 4 caras = 120 triángulos azul_rey)
    assert r.conteo_colores["azul_rey"] == 120
    # Variante B (30 pirámides: caras 0 y 2 blanco = 60, caras 1 y 3 rojo = 60)
    assert r.conteo_colores["blanco"] == 60
    assert r.conteo_colores["rojo"] == 60
    assert sum(r.conteo_colores.values()) == 240

def test_serializacion_deserializacion_proyecto_con_esquema_pico(tmp_path):
    inp = BalloonInput(950.0, 30, 2, 1.0)
    cond = Condiciones()
    var_a = VariantePico(modo_caras="igual", color_0="amarillo")
    var_b = VariantePico(modo_caras="cuatro", color_0="rojo", color_1="verde", color_2="azul", color_3="blanco")
    esq_pico = EsquemaDisenoPico(
        modo_repeticion="ajedrez",
        usar_variante_b=True,
        variante_a=var_a,
        variante_b=var_b,
        motivos_por_cara=[0, 1, 2, 3]
    )

    p = Proyecto(
        version=1,
        nombre="Globo Picos",
        entrada=inp,
        condiciones=cond,
        esquema=None,
        notas="Prueba pico",
        esquema_pico=esq_pico
    )

    ruta = tmp_path / "proy_pico.json"
    guardar_proyecto(p, str(ruta))

    p_cargado = cargar_proyecto(str(ruta))
    assert p_cargado.esquema_pico is not None
    assert p_cargado.esquema_pico.modo_repeticion == "ajedrez"
    assert p_cargado.esquema_pico.usar_variante_b is True
    assert p_cargado.esquema_pico.variante_a.color_0 == "amarillo"
    assert p_cargado.esquema_pico.variante_b.modo_caras == "cuatro"
    assert p_cargado.esquema_pico.variante_b.color_1 == "verde"
    assert p_cargado.esquema_pico.motivos_por_cara == [0, 1, 2, 3]
