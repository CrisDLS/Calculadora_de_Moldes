from logic.diseno.paleta import (
    ColorPapel,
    importar_csv,
    exportar_csv,
)
from logic.diseno.compra import lista_de_compra
from logic.models import BalloonInput
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from logic.diseno.pintura import EsquemaPintura

def test_exportar_e_importar_csv_basico(tmp_path):
    colores = [
        ColorPapel("azul_rey", "Azul Rey", "#1976d2", aproximado=True, marca="Estrella", codigo="AR-01", notas="Prueba"),
        ColorPapel("verde_menta", "Verde Menta", "#a8e6cf", aproximado=False, marca="Pingüino", codigo="VM-99", notas="Calibrado exacto"),
    ]
    csv_file = str(tmp_path / "colores.csv")
    exportar_csv(csv_file, colores)

    user_dest = str(tmp_path / "user_colores.json")
    importados, errores = importar_csv(csv_file, ruta_usuario_destino=user_dest)

    assert len(errores) == 0
    assert len(importados) == 2
    assert importados[0].hex == "#1976d2"
    assert importados[0].marca == "Estrella"
    assert importados[0].codigo == "AR-01"
    assert importados[0].aproximado is True

    assert importados[1].hex == "#a8e6cf"
    assert importados[1].aproximado is False  # Calibrado

def test_importar_csv_delimitador_punto_y_coma_y_bom(tmp_path):
    contenido_csv = (
        "\ufeffnombre;marca;codigo;hex;calibrado;notas\n"
        "Amarillo Oro;Colibrí;AO-10;#ffd700;si;Muy brillante\n"
        "Rosa Pastel;Colibrí;RP-20;ffb6c1;no;Tono suave\n"
    )
    csv_file = tmp_path / "colores_puntoycoma.csv"
    csv_file.write_text(contenido_csv, encoding="utf-8-sig")

    user_dest = str(tmp_path / "user_colores.json")
    importados, errores = importar_csv(str(csv_file), ruta_usuario_destino=user_dest)

    assert len(errores) == 0
    assert len(importados) == 2
    assert importados[0].hex == "#ffd700"
    assert importados[0].aproximado is False
    assert importados[1].hex == "#ffb6c1"
    assert importados[1].aproximado is True

def test_importar_csv_tolerancia_a_filas_invalidas(tmp_path):
    contenido_csv = (
        "nombre,marca,codigo,hex,calibrado,notas\n"
        "Color Valido,Marca A,01,#112233,no,Ok\n"
        ",Marca B,02,#223344,no,Sin nombre\n"
        "Color Hex Mal,Marca C,03,NOT_A_HEX,no,Invalido\n"
        "Color Valido 2,Marca D,04,#445566,si,Ok\n"
    )
    csv_file = tmp_path / "colores_con_errores.csv"
    csv_file.write_text(contenido_csv, encoding="utf-8")

    user_dest = str(tmp_path / "user_colores.json")
    importados, errores = importar_csv(str(csv_file), ruta_usuario_destino=user_dest)

    assert len(importados) == 2
    assert len(errores) == 2
    assert "Fila 3" in errores[0]
    assert "Fila 4" in errores[1]

def test_lista_compra_paquetes():
    calc = TrompoEstrellaCalculator()
    ent = BalloonInput(950.0, 30, 2, 1.0)
    res = calc.calcular(ent)
    p = EsquemaPintura(color_superior="blanco", color_pico="amarillo", color_inferior="blanco")

    # Pliegos por paquete = 100
    items_100 = lista_de_compra(ent, res, p, pliegos_por_paquete=100)
    for it in items_100:
        assert it.paquetes == (it.pliegos + 99) // 100

    # Pliegos por paquete = 50
    items_50 = lista_de_compra(ent, res, p, pliegos_por_paquete=50)
    for it in items_50:
        assert it.paquetes == (it.pliegos + 49) // 50
