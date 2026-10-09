"""
3. Interfaces
Esto define la "regla" que todas las calculadoras deben seguir. 
Permite que el resto del programa no dependa de "TrompoEstrella", sino de "BalloonCalculator".
"""
from abc import ABC, abstractmethod
from logic.models import BalloonInput, BalloonCalculationResult

class BalloonCalculator(ABC):
    
    @abstractmethod
    def calcular(self, entrada: BalloonInput) -> BalloonCalculationResult:
        """
        Recibe los parámetros de entrada y devuelve el resultado completo
        con dimensiones y coordenadas.
        """
        pass