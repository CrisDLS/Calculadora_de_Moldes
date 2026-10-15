from typing import Optional
from logic.diseno.pintura import EsquemaPintura
from logic.exportacion.escena3d import escena_a_dict
from logic.exportacion.visor3d import ServidorVisor, exportar_visor_autocontenido


class Controlador3DMixin:
    """Mixin para gestión del visor 3D (three.js), servidor local y esquemas de pintura."""

    def obtener_servidor_3d(self) -> ServidorVisor:
        if self.servidor_3d is None:
            self.servidor_3d = ServidorVisor()
            self.servidor_3d.iniciar()
        self._actualizar_servidor_3d()
        return self.servidor_3d

    def _actualizar_servidor_3d(self) -> None:
        if self.servidor_3d and self.resultado and self.entrada_actual:
            try:
                esq = self._construir_esquema()
                escena = escena_a_dict(
                    self.entrada_actual,
                    self.resultado,
                    esquema_pintura=self.pintura,
                    esquema_diseno=esq,
                )
                self.servidor_3d.actualizar_datos_escena(escena)
            except Exception:
                pass

    def exportar_visor_3d(self, ruta: str) -> None:
        if not (self.resultado and self.entrada_actual):
            raise ValueError("Calcula el modelo antes de exportar el visor 3D")
        esq = self._construir_esquema()
        escena = escena_a_dict(
            self.entrada_actual,
            self.resultado,
            esquema_pintura=self.pintura,
            esquema_diseno=esq,
        )
        exportar_visor_autocontenido(escena, ruta)

    def actualizar_pintura(
        self,
        color_sup: Optional[str] = None,
        color_pic: Optional[str] = None,
        color_inf: Optional[str] = None,
        pintura_completa: Optional[EsquemaPintura] = None,
    ) -> None:
        if pintura_completa is not None:
            self.pintura = pintura_completa
        else:
            if color_sup is not None:
                self.pintura.color_superior = color_sup
                if self.pintura.colores_superior:
                    self.pintura.colores_superior[0] = color_sup
                else:
                    self.pintura.colores_superior = [color_sup]
            if color_pic is not None:
                self.pintura.color_pico = color_pic
                self.pintura.variante_a.color_0 = color_pic
            if color_inf is not None:
                self.pintura.color_inferior = color_inf
                if self.pintura.colores_inferior:
                    self.pintura.colores_inferior[0] = color_inf
                else:
                    self.pintura.colores_inferior = [color_inf]
        self.sin_guardar = True
        self._actualizar_servidor_3d()
