from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class AsignacionGajo:
    gajo: int
    motivo: int
    espejo: bool

@dataclass
class EsquemaDiseno:
    modo: str
    k: int
    ciclo: Optional[List[Tuple[int, bool]]] = None

    def asignar(self, num_gajos: int) -> List[AsignacionGajo]:
        # Validar divisibilidad
        if self.modo == "repeticion":
            longitud_ciclo = self.k
        elif self.modo == "espejo_total":
            longitud_ciclo = 2 * self.k
        elif self.modo == "personalizado":
            if not self.ciclo:
                raise ValueError("Modo personalizado requiere definir un ciclo.")
            longitud_ciclo = len(self.ciclo)
        else:
            raise ValueError(f"Modo desconocido: {self.modo}")

        if num_gajos % longitud_ciclo != 0:
            sobran = num_gajos % longitud_ciclo
            divisores = [d for d in range(1, num_gajos + 1) if num_gajos % d == 0]
            raise ValueError(
                f"El esquema requiere que el número de gajos ({num_gajos}) sea "
                f"múltiplo de la longitud del ciclo ({longitud_ciclo}). Sobran {sobran} gajo(s). "
                f"Longitudes permitidas para {num_gajos} gajos: {divisores}"
            )

        # Generar ciclo base
        ciclo_base = []
        if self.modo == "repeticion":
            for m in range(self.k):
                ciclo_base.append((m, False))
        elif self.modo == "espejo_total":
            for m in range(self.k):
                ciclo_base.append((m, False))
            for m in reversed(range(self.k)):
                ciclo_base.append((m, True))
        elif self.modo == "personalizado":
            ciclo_base = self.ciclo.copy()

        # Asignar a todos los gajos
        asignaciones = []
        for i in range(num_gajos):
            motivo, espejo = ciclo_base[i % longitud_ciclo]
            asignaciones.append(AsignacionGajo(gajo=i, motivo=motivo, espejo=espejo))

        return asignaciones
