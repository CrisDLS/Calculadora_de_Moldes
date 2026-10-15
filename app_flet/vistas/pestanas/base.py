from abc import ABC, abstractmethod
from typing import Optional
import flet as ft
from app_flet.controlador.modelos import ViewModelTrompo


class PestanaBase(ABC):
    """Contrato base para las pestañas de la interfaz de trompo estrella."""

    @abstractmethod
    def construir(self) -> ft.Control:
        """Construye y devuelve el control raíz de la pestaña."""
        pass

    @abstractmethod
    def actualizar(self, vm: ViewModelTrompo) -> None:
        """Actualiza los controles de la pestaña con los datos del view-model."""
        pass

    def aplicar_tema(self, paleta) -> None:
        """Aplica la paleta de colores activa a los controles temáticos de la pestaña."""
        pass

    def al_mostrar(self) -> None:
        """Hook opcional llamado cuando la pestaña se vuelve visible."""
        pass
