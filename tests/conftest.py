"""Configuración global de pruebas para pytest."""
import os
import hashlib
from pathlib import Path
import pytest


def _calcular_hash_guardados(carpeta: Path) -> str:
    """Calcula hash SHA-256 canónico del contenido de una carpeta."""
    if not carpeta.exists():
        return ""
    files = sorted([f for f in carpeta.rglob("*") if f.is_file()])
    h = hashlib.sha256()
    for f in files:
        rel = f.relative_to(carpeta).as_posix()
        fhash = hashlib.sha256(f.read_bytes()).hexdigest()
        h.update(f"{rel}:{fhash}\n".encode())
    return h.hexdigest()


@pytest.fixture(scope="session", autouse=True)
def aislar_globos_datos_y_proteger_guardados(tmp_path_factory):
    """
    Aisla la carpeta de datos de usuario en un directorio temporal para toda la sesión de pruebas.
    Actúa como guardia verificando que la carpeta guardados/ no sea modificada ni creada.
    """
    temp_datos = tmp_path_factory.mktemp("globos_datos_sesion")
    orig_env = os.environ.get("GLOBOS_DATOS")
    os.environ["GLOBOS_DATOS"] = str(temp_datos)

    carp = Path("guardados")
    existe_inicial = carp.exists()
    hash_inicial = _calcular_hash_guardados(carp) if existe_inicial else None
    archivos_inicial = len([f for f in carp.rglob("*") if f.is_file()]) if existe_inicial else 0

    yield temp_datos

    # Restaurar variable de entorno
    if orig_env is not None:
        os.environ["GLOBOS_DATOS"] = orig_env
    else:
        os.environ.pop("GLOBOS_DATOS", None)

    # GUARDIA: verificar que guardados/ no fue modificado
    if not existe_inicial:
        assert not carp.exists(), "La carpeta guardados/ no existía y fue creada durante la sesión de pruebas!"
    else:
        assert carp.exists(), "La carpeta guardados/ fue eliminada durante la sesión de pruebas!"
        hash_final = _calcular_hash_guardados(carp)
        archivos_final = len([f for f in carp.rglob("*") if f.is_file()])
        assert hash_final == hash_inicial, (
            f"GUARDIA: La carpeta guardados/ fue modificada durante la sesión de pruebas!\n"
            f"Archivos antes: {archivos_inicial}, después: {archivos_final}\n"
            f"Hash antes: {hash_inicial}\n"
            f"Hash después: {hash_final}"
        )
