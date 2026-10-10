from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

@dataclass
class AsignacionGajo:
    gajo: int
    motivo: int
    espejo: bool

@dataclass
class EsquemaDiseno:
    modo: str
    tam_grupo: int
    ciclo: Optional[List[Tuple[int, bool]]] = None

    def _generar_ciclo(self) -> List[Tuple[int, bool]]:
        if self.modo == "repeticion":
            return [(m, False) for m in range(self.tam_grupo)]
        elif self.modo == "central_espejo":
            if self.tam_grupo % 2 == 0:
                raise ValueError(f"El modo 'central_espejo' requiere un tamaño de grupo impar, pero se dio {self.tam_grupo}.")
            m = (self.tam_grupo + 1) // 2
            ciclo = []
            for i in range(m - 1, 0, -1):
                ciclo.append((i, True))
            ciclo.append((0, False))
            for i in range(1, m):
                ciclo.append((i, False))
            return ciclo
        elif self.modo == "espejo_total":
            if self.tam_grupo % 2 != 0:
                raise ValueError(f"El modo 'espejo_total' requiere un tamaño de grupo par, pero se dio {self.tam_grupo}.")
            m = self.tam_grupo // 2
            ciclo = []
            for i in range(m):
                ciclo.append((i, False))
            for i in range(m - 1, -1, -1):
                ciclo.append((i, True))
            return ciclo
        elif self.modo == "personalizado":
            if not self.ciclo:
                raise ValueError("Modo personalizado requiere definir un ciclo.")
            return self.ciclo.copy()
        else:
            raise ValueError(f"Modo desconocido: {self.modo}")

    @property
    def motivos_a_dibujar(self) -> int:
        c = self._generar_ciclo()
        return len(set(motivo for motivo, _ in c))

    def repeticiones(self, num_gajos: int) -> int:
        c = self._generar_ciclo()
        longitud_ciclo = len(c)
        if num_gajos % longitud_ciclo != 0:
            sobran = num_gajos % longitud_ciclo
            divisores = [d for d in range(1, num_gajos + 1) if num_gajos % d == 0]
            
            # Filtrar divisores por paridad según modo si es necesario para dar mejor feedback
            divs_filtrados = []
            for d in divisores:
                if self.modo == "central_espejo" and d % 2 == 0: continue
                if self.modo == "espejo_total" and d % 2 != 0: continue
                divs_filtrados.append(d)
                
            msg_divs = str(divs_filtrados) if divs_filtrados else "ninguno compatible con este modo"
            raise ValueError(
                f"El esquema requiere que el número de gajos ({num_gajos}) sea "
                f"múltiplo del tamaño de grupo ({longitud_ciclo}). Sobran {sobran} gajo(s). "
                f"Tamaños de grupo permitidos para {num_gajos} gajos en modo {self.modo}: {msg_divs}"
            )
        return num_gajos // longitud_ciclo

    def asignar(self, num_gajos: int) -> List[AsignacionGajo]:
        ciclo_base = self._generar_ciclo()
        reps = self.repeticiones(num_gajos) # Lanza ValueError si no divide
        
        longitud_ciclo = len(ciclo_base)
        asignaciones = []
        for i in range(num_gajos):
            motivo, espejo = ciclo_base[i % longitud_ciclo]
            asignaciones.append(AsignacionGajo(gajo=i, motivo=motivo, espejo=espejo))

        return asignaciones

    def resumen_motivos(self, asignaciones: List[AsignacionGajo]) -> Dict[int, Tuple[int, int, int]]:
        resumen = {}
        for a in asignaciones:
            if a.motivo not in resumen:
                resumen[a.motivo] = {"total": 0, "en_espejo": 0, "sin_espejo": 0}
            resumen[a.motivo]["total"] += 1
            if a.espejo:
                resumen[a.motivo]["en_espejo"] += 1
            else:
                resumen[a.motivo]["sin_espejo"] += 1
                
        # Transformar a tuplas (total, en_espejo, sin_espejo)
        return {m: (v["total"], v["en_espejo"], v["sin_espejo"]) for m, v in resumen.items()}
