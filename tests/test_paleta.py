import pytest
from logic.diseno.paleta import ColorPapel, cargar_catalogo, guardar_color_usuario, color_por_id

def test_color_papel_hex_valido():
    c = ColorPapel("rojo", "Rojo", "#ff0000", True)
    assert c.id == "rojo"
    assert c.hex == "#ff0000"

    with pytest.raises(ValueError, match="Código HEX inválido"):
        ColorPapel("malo", "Malo", "ff0000")

    with pytest.raises(ValueError, match="Código HEX inválido"):
        ColorPapel("malo2", "Malo", "#fff")

def test_cargar_catalogo_base():
    cat = cargar_catalogo()
    assert len(cat) >= 20
    ids = [c.id for c in cat]
    assert "blanco" in ids
    assert "negro" in ids
    assert "rosa_mexicano" in ids

def test_color_por_id():
    c = color_por_id("blanco")
    assert c.id == "blanco"
    assert c.hex == "#ffffff"

    # Inexistente devuelve blanco
    c_def = color_por_id("no_existe")
    assert c_def.id == "blanco"

def test_guardar_color_usuario(tmp_path):
    ruta_user = tmp_path / "colores_user.json"
    nuevo = ColorPapel("morado_personalizado", "Morado Mio", "#5500aa", False)
    guardar_color_usuario(nuevo, str(ruta_user))

    cat = cargar_catalogo(str(ruta_user))
    assert any(c.id == "morado_personalizado" for c in cat)
    c_rec = color_por_id("morado_personalizado", cat)
    assert c_rec.hex == "#5500aa"

    # Sobrescribir color base
    blanco_mod = ColorPapel("blanco", "Blanco Hueso", "#fafafa", True)
    guardar_color_usuario(blanco_mod, str(ruta_user))
    cat2 = cargar_catalogo(str(ruta_user))
    c_b = color_por_id("blanco", cat2)
    assert c_b.hex == "#fafafa"
    assert c_b.nombre == "Blanco Hueso"
