"""
Configuración independiente por sección para el cálculo y trazado de moldes.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union, Tuple
from logic.diseno.esquema import EsquemaDiseno, tiene_simetria_espejo
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.pintura import VariantePico


@dataclass
class ConfigSeccion:
    seccion: str  # "superior" | "inferior" | "pico"
    esquema: Optional[EsquemaDiseno] = None  # Para conos superior e inferior
    esquema_pico: Optional[EsquemaDisenoPico] = None  # Exclusivo para pico
    dibujar: str = "completo"  # "completo" | "mitad" (en pico siempre "completo")
    lienzo: str = "abanico"    # "abanico" | "separadas"
    escala: Union[str, int, float] = "auto"

    def __post_init__(self):
        if self.seccion == "pico":
            self.dibujar = "completo"
            if self.esquema_pico is None:
                self.esquema_pico = EsquemaDisenoPico()
        else:
            if self.esquema is None:
                self.esquema = EsquemaDiseno(modo="repeticion", tam_grupo=5)
            # Validar si el esquema permite mitad
            puede, _ = self.puede_usar_mitad()
            if not puede and self.dibujar == "mitad":
                self.dibujar = "completo"

    def puede_usar_mitad(self) -> Tuple[bool, str]:
        """Determina si la sección actual admite el modo 'mitad' (espejo)."""
        if self.seccion == "pico":
            return False, "En los picos no aplica simetría de espejo (las pirámides se arman con caras cerradas)."
        return tiene_simetria_espejo(self.esquema)

    def copiar_desde(self, otra: "ConfigSeccion") -> None:
        """Copia la configuración desde otra sección, adaptando según paridad de tipo."""
        if self.seccion == "pico":
            if otra.seccion == "pico" and otra.esquema_pico:
                # Copiar configuración de pico
                self.esquema_pico = EsquemaDisenoPico(
                    modo_repeticion=otra.esquema_pico.modo_repeticion,
                    variante_a=VariantePico(**asdict(otra.esquema_pico.variante_a)),
                    usar_variante_b=otra.esquema_pico.usar_variante_b,
                    variante_b=VariantePico(**asdict(otra.esquema_pico.variante_b)),
                    motivos_por_cara=list(otra.esquema_pico.motivos_por_cara),
                )
            self.lienzo = otra.lienzo
            self.escala = otra.escala
            self.dibujar = "completo"
        else:
            if otra.esquema:
                self.esquema = EsquemaDiseno(
                    modo=otra.esquema.modo,
                    tam_grupo=otra.esquema.tam_grupo,
                    ciclo=list(otra.esquema.ciclo) if otra.esquema.ciclo else None,
                )
            self.lienzo = otra.lienzo
            self.escala = otra.escala
            puede, _ = self.puede_usar_mitad()
            self.dibujar = otra.dibujar if (puede and otra.dibujar == "mitad") else "completo"

    def a_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "seccion": self.seccion,
            "dibujar": self.dibujar,
            "lienzo": self.lienzo,
            "escala": self.escala,
        }
        if self.esquema is not None:
            res["esquema"] = {
                "modo": self.esquema.modo,
                "tam_grupo": self.esquema.tam_grupo,
                "ciclo": self.esquema.ciclo,
            }
        if self.esquema_pico is not None:
            res["esquema_pico"] = asdict(self.esquema_pico)
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSeccion":
        sec = data.get("seccion", "superior")
        esq = None
        if data.get("esquema"):
            e_data = data["esquema"]
            ciclo = e_data.get("ciclo")
            if ciclo:
                ciclo = [(c[0], c[1]) for c in ciclo]
            esq = EsquemaDiseno(
                modo=e_data["modo"],
                tam_grupo=e_data.get("tam_grupo", e_data.get("k", 1)),
                ciclo=ciclo,
            )
        
        esq_pico = None
        if data.get("esquema_pico"):
            ep_data = data["esquema_pico"]
            var_a_data = ep_data.get("variante_a", {})
            var_a = VariantePico(**var_a_data) if var_a_data else VariantePico()
            var_b_data = ep_data.get("variante_b", {})
            var_b = VariantePico(**var_b_data) if var_b_data else VariantePico()
            esq_pico = EsquemaDisenoPico(
                modo_repeticion=ep_data.get("modo_repeticion", "todas_a"),
                variante_a=var_a,
                usar_variante_b=ep_data.get("usar_variante_b", False),
                variante_b=var_b,
                motivos_por_cara=ep_data.get("motivos_por_cara", [0, 1, 2, 3]),
            )

        return cls(
            seccion=sec,
            esquema=esq,
            esquema_pico=esq_pico,
            dibujar=data.get("dibujar", "completo"),
            lienzo=data.get("lienzo", "abanico"),
            escala=data.get("escala", "auto"),
        )
