import json
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Union, Set
from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno
from logic.diseno.pintura import EsquemaPintura, VariantePico
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.lienzo import Diseno

from logic.diseno.config_seccion import ConfigSeccion

@dataclass
class Proyecto:
    version: int
    nombre: str
    entrada: BalloonInput
    condiciones: Condiciones
    esquema: Optional[EsquemaDiseno] = None
    notas: str = ""
    hoja: str = "carta"
    escala: Union[str, int, float] = "auto"
    pintura: Optional[EsquemaPintura] = None
    pliegos_por_paquete: int = 100
    esquema_pico: Optional[EsquemaDisenoPico] = None
    disenos: Dict[str, Diseno] = field(default_factory=dict)
    config_secciones: Dict[str, ConfigSeccion] = field(default_factory=dict)
    recursos_faltantes: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Asegurar que siempre existan las 3 configuraciones de sección
        if not self.config_secciones:
            self.config_secciones = {
                "superior": ConfigSeccion(
                    seccion="superior",
                    esquema=self.esquema or EsquemaDiseno(modo="repeticion", tam_grupo=5),
                    dibujar="completo",
                    lienzo="abanico",
                    escala=self.escala,
                ),
                "inferior": ConfigSeccion(
                    seccion="inferior",
                    esquema=self.esquema or EsquemaDiseno(modo="repeticion", tam_grupo=5),
                    dibujar="completo",
                    lienzo="abanico",
                    escala=self.escala,
                ),
                "pico": ConfigSeccion(
                    seccion="pico",
                    esquema_pico=self.esquema_pico or EsquemaDisenoPico(),
                    dibujar="completo",
                    lienzo="abanico",
                    escala=self.escala,
                ),
            }
        else:
            if "superior" not in self.config_secciones:
                self.config_secciones["superior"] = ConfigSeccion(seccion="superior", esquema=self.esquema)
            if "inferior" not in self.config_secciones:
                self.config_secciones["inferior"] = ConfigSeccion(seccion="inferior", esquema=self.esquema)
            if "pico" not in self.config_secciones:
                self.config_secciones["pico"] = ConfigSeccion(seccion="pico", esquema_pico=self.esquema_pico)

        # Sincronizar campos legados si existen
        if self.esquema is not None and self.config_secciones.get("superior") and self.config_secciones["superior"].esquema:
            self.esquema = self.config_secciones["superior"].esquema
        if self.esquema_pico is not None and self.config_secciones.get("pico") and self.config_secciones["pico"].esquema_pico:
            self.esquema_pico = self.config_secciones["pico"].esquema_pico

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proyecto":
        data = _migrar_proyecto(data)
        
        # Validar campos requeridos
        for req in ["version", "nombre", "entrada"]:
            if req not in data:
                raise ValueError(f"Falta el campo requerido: {req}")
        
        ent = BalloonInput(**data["entrada"])
        cond = Condiciones(**data.get("condiciones", {}))
        
        esq = None
        if data.get("esquema"):
            e_data = data["esquema"]
            ciclo = e_data.get("ciclo")
            if ciclo:
                ciclo = [(c[0], c[1]) for c in ciclo]
            esq = EsquemaDiseno(e_data["modo"], e_data.get("tam_grupo", e_data.get("k", 1)), ciclo)
            
        pintura = None
        if data.get("pintura"):
            p_data = data["pintura"]
            col_motivos = {}
            for k, v in p_data.get("colores_motivos", {}).items():
                col_motivos[int(k)] = v
            
            var_a_data = p_data.get("variante_a", {})
            var_a = VariantePico(**var_a_data) if var_a_data else VariantePico()

            var_b_data = p_data.get("variante_b", {})
            var_b = VariantePico(**var_b_data) if var_b_data else VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo")

            pintura = EsquemaPintura(
                modo_superior=p_data.get("modo_superior", "liso"),
                colores_superior=p_data.get("colores_superior", [p_data.get("color_superior", "blanco")]),
                tam_bloque_superior=p_data.get("tam_bloque_superior", 5),
                mismo_esquema_inferior=p_data.get("mismo_esquema_inferior", False),
                modo_inferior=p_data.get("modo_inferior", "liso"),
                colores_inferior=p_data.get("colores_inferior", [p_data.get("color_inferior", "blanco")]),
                tam_bloque_inferior=p_data.get("tam_bloque_inferior", 5),
                variante_a=var_a,
                usar_variante_b=p_data.get("usar_variante_b", False),
                variante_b=var_b,
                repeticion_picos=p_data.get("repeticion_picos", "todas_a"),
                color_superior=p_data.get("color_superior", "blanco"),
                color_pico=p_data.get("color_pico", "amarillo"),
                color_inferior=p_data.get("color_inferior", "blanco"),
                colores_motivos=col_motivos,
                colores_caras_especificas=p_data.get("colores_caras_especificas", {})
            )

        esq_pico = None
        if data.get("esquema_pico"):
            ep_data = data["esquema_pico"]
            var_a_data = ep_data.get("variante_a", {})
            var_a = VariantePico(**var_a_data) if var_a_data else VariantePico()
            var_b_data = ep_data.get("variante_b", {})
            var_b = VariantePico(**var_b_data) if var_b_data else VariantePico(color_0="rojo", color_1="rojo", color_2="rojo", color_3="rojo")
            esq_pico = EsquemaDisenoPico(
                modo_repeticion=ep_data.get("modo_repeticion", "todas_a"),
                variante_a=var_a,
                usar_variante_b=ep_data.get("usar_variante_b", False),
                variante_b=var_b,
                motivos_por_cara=ep_data.get("motivos_por_cara", [0, 1, 2, 3])
            )

        disenos = {}
        if data.get("disenos"):
            raw_disenos = data["disenos"]
            if isinstance(raw_disenos, dict):
                for k, v in raw_disenos.items():
                    disenos[k] = Diseno.from_dict(v)
            elif isinstance(raw_disenos, list):
                for d in raw_disenos:
                    obj = Diseno.from_dict(d)
                    clave = f"{obj.seccion}_{obj.variante}" if obj.seccion == "pico" else obj.seccion
                    disenos[clave] = obj

        # Parsear config_secciones (v2)
        configs = {}
        if data.get("config_secciones"):
            for sec_k, sec_v in data["config_secciones"].items():
                configs[sec_k] = ConfigSeccion.from_dict(sec_v)

        return cls(
            version=data["version"],
            nombre=data["nombre"],
            entrada=ent,
            condiciones=cond,
            esquema=esq,
            notas=data.get("notas", ""),
            hoja=data.get("hoja", "carta"),
            escala=data.get("escala", "auto"),
            pintura=pintura,
            pliegos_por_paquete=data.get("pliegos_por_paquete", 100),
            esquema_pico=esq_pico,
            disenos=disenos,
            config_secciones=configs,
        )

def _migrar_proyecto(data: Dict[str, Any]) -> Dict[str, Any]:
    v = data.get("version")
    if v is None:
        raise ValueError("JSON corrupto o sin versión.")
    
    if v == 1:
        # Migración v1 -> v2: Esquemas y lienzos independientes por sección
        esq_global = data.get("esquema")
        esq_pico = data.get("esquema_pico")
        hoja_dibujar = data.get("hoja_dibujar", "completo")
        hoja_lienzo = data.get("hoja_lienzo", "abanico")
        escala = data.get("escala", "auto")

        cfg_sup = {
            "seccion": "superior",
            "esquema": esq_global,
            "dibujar": hoja_dibujar,
            "lienzo": hoja_lienzo,
            "escala": escala,
        }
        cfg_inf = {
            "seccion": "inferior",
            "esquema": esq_global,
            "dibujar": hoja_dibujar,
            "lienzo": hoja_lienzo,
            "escala": escala,
        }
        cfg_pico = {
            "seccion": "pico",
            "esquema_pico": esq_pico,
            "dibujar": "completo",
            "lienzo": hoja_lienzo,
            "escala": escala,
        }

        data["config_secciones"] = {
            "superior": cfg_sup,
            "inferior": cfg_inf,
            "pico": cfg_pico,
        }
        data["version"] = 2
        return data

    if v > 2:
        raise ValueError(f"Versión de proyecto desconocida: {v}")
    
    return data

def obtener_carpeta_recursos(ruta_proyecto: Union[str, Path]) -> Path:
    p = Path(ruta_proyecto)
    return p.parent / f"{p.stem}_recursos"

def copiar_recursos_proyecto(ruta_origen: Union[str, Path], ruta_destino: Union[str, Path]) -> None:
    carp_origen = obtener_carpeta_recursos(ruta_origen)
    carp_destino = obtener_carpeta_recursos(ruta_destino)
    if carp_origen.exists() and carp_origen.is_dir():
        carp_destino.mkdir(parents=True, exist_ok=True)
        for item in carp_origen.iterdir():
            if item.is_file():
                shutil.copy2(item, carp_destino / item.name)

def guardar_proyecto(proyecto: Proyecto, ruta: str, ruta_anterior: Optional[str] = None) -> None:
    if ruta_anterior and Path(ruta_anterior).resolve() != Path(ruta).resolve():
        copiar_recursos_proyecto(ruta_anterior, ruta)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(asdict(proyecto), f, indent=4, ensure_ascii=False)

def cargar_proyecto(ruta: str) -> Proyecto:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError("El archivo no es un JSON válido.") from e
    
    proyecto = Proyecto.from_dict(data)
    carp_recursos = obtener_carpeta_recursos(ruta)
    faltantes = []
    for diseno in proyecto.disenos.values():
        for capa in diseno.capas:
            archivo_recurso = carp_recursos / capa.archivo
            if not archivo_recurso.exists():
                faltantes.append(capa.archivo)
    proyecto.recursos_faltantes = faltantes
    return proyecto


def obtener_archivos_referenciados_por_proyectos(
    carpeta_proyectos: Union[str, Path],
    proyecto_actual: Optional[Proyecto] = None,
) -> Set[str]:
    """Obtiene el conjunto de nombres de archivo de recursos referenciados por todos los proyectos en disco y en memoria."""
    referenciados: Set[str] = set()

    # Proyectos guardados en carpeta_proyectos (por ejemplo guardados/)
    base = Path(carpeta_proyectos)
    if base.exists():
        for f in base.rglob("*.json"):
            # Ignorar archivos en papelera o temporales internos
            if "_papelera" in f.parts:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue
                disenos = data.get("disenos", {})
                for sec_diseno in disenos.values():
                    if isinstance(sec_diseno, dict):
                        for c in sec_diseno.get("capas", []):
                            arch = c.get("archivo")
                            if arch:
                                referenciados.add(arch)
            except Exception:
                pass

    # Proyecto actualmente cargado en memoria
    if proyecto_actual:
        for diseno in proyecto_actual.disenos.values():
            for capa in diseno.capas:
                if capa.archivo:
                    referenciados.add(capa.archivo)

    return referenciados


def recursos_sin_uso(
    carpeta_recursos: Union[str, Path],
    archivos_referenciados: Set[str],
) -> List[Path]:
    """Retorna la lista de rutas de archivos en carpeta_recursos que no están referenciados por ningún proyecto."""
    carp = Path(carpeta_recursos)
    if not carp.exists() or not carp.is_dir():
        return []

    sin_uso: List[Path] = []
    for item in carp.iterdir():
        # Excluir subcarpetas (como _papelera), archivos ocultos y archivos .json de proyecto
        if item.is_file() and not item.name.startswith(".") and not item.name.endswith(".json"):
            if item.name not in archivos_referenciados:
                sin_uso.append(item)

    return sorted(sin_uso, key=lambda p: p.name)


def mover_a_papelera(
    archivos: List[Path],
    carpeta_recursos: Union[str, Path],
    subdirectorio_fecha: Optional[str] = None,
) -> Path:
    """Mueve archivos sin uso a <carpeta_recursos>/_papelera/<fecha_hora>/ sin borrar nada permanentemente."""
    carp_base = Path(carpeta_recursos)
    fecha_str = subdirectorio_fecha or datetime.now().strftime("%Y%m%d_%H%M%S")
    destino_papelera = carp_base / "_papelera" / fecha_str
    destino_papelera.mkdir(parents=True, exist_ok=True)

    for arch in archivos:
        if arch.exists() and arch.is_file():
            shutil.move(str(arch), str(destino_papelera / arch.name))

    return destino_papelera

