from logic.models import BalloonInput, Condiciones
from logic.diseno.esquema import EsquemaDiseno, tiene_simetria_espejo
from logic.diseno.diseno_pico import EsquemaDisenoPico
from logic.diseno.config_seccion import ConfigSeccion
from logic.proyecto.modelo import Proyecto, guardar_proyecto, cargar_proyecto
from logic.exportacion.paquete import generar_paquete
from logic.calculators.trompo_estrella import TrompoEstrellaCalculator
from app_flet.controlador import ControladorTrompo


def test_independencia_secciones():
    ctrl = ControladorTrompo()
    ctrl.altura = "950"
    ctrl.gajos = "30"
    ctrl.hileras = "2"
    ctrl.costura = "1"
    ctrl.calcular()

    # 1. Modificar superior no altera inferior ni pico
    ctrl.cambiar_esquema_seccion("superior", "central_espejo", 5)
    ctrl.cambiar_dibujar_seccion("superior", "mitad")
    ctrl.cambiar_lienzo_seccion("superior", "separadas")
    ctrl.cambiar_escala_seccion("superior", "15")

    cfg_inf = ctrl.obtener_config_seccion("inferior")
    cfg_pico = ctrl.obtener_config_seccion("pico")

    assert cfg_inf.esquema.modo == "repeticion"
    assert cfg_inf.dibujar == "completo"
    assert cfg_inf.lienzo == "abanico"
    assert cfg_inf.escala == "auto"

    assert cfg_pico.dibujar == "completo"
    assert cfg_pico.lienzo == "abanico"

    # 2. Modificar inferior no altera superior ni pico
    ctrl.cambiar_esquema_seccion("inferior", "espejo_total", 6)
    ctrl.cambiar_dibujar_seccion("inferior", "mitad")

    cfg_sup = ctrl.obtener_config_seccion("superior")
    assert cfg_sup.esquema.modo == "central_espejo"
    assert cfg_sup.esquema.tam_grupo == 5
    assert cfg_sup.dibujar == "mitad"
    assert cfg_sup.lienzo == "separadas"
    assert cfg_sup.escala == "15"

    # 3. Modificar pico no altera conos
    ctrl.actualizar_esquema_pico(modo_repeticion="ajedrez")
    cfg_pico = ctrl.obtener_config_seccion("pico")
    assert cfg_pico.esquema_pico.modo_repeticion == "ajedrez"
    assert ctrl.obtener_config_seccion("superior").esquema.modo == "central_espejo"
    assert ctrl.obtener_config_seccion("inferior").esquema.modo == "espejo_total"


def test_mitad_desactivado_sin_espejo_y_en_pico():
    # Repetición: no admite mitad
    cfg_rep = ConfigSeccion(seccion="superior", esquema=EsquemaDiseno("repeticion", 5))
    puede, motivo = cfg_rep.puede_usar_mitad()
    assert puede is False
    assert "repetición" in motivo.lower()

    # Si se intenta forzar 'mitad', se revierte a 'completo'
    cfg_rep.dibujar = "mitad"
    cfg_rep.__post_init__()
    assert cfg_rep.dibujar == "completo"

    # Pico: admite mitad (espejo) sobre la cara
    cfg_pico = ConfigSeccion(seccion="pico", dibujar="mitad")
    puede_pico, motivo_pico = cfg_pico.puede_usar_mitad()
    assert puede_pico is True
    assert cfg_pico.dibujar == "mitad"
    assert "simetría" in motivo_pico.lower()

    # Central espejo y espejo total: admiten mitad
    cfg_central = ConfigSeccion(seccion="superior", esquema=EsquemaDiseno("central_espejo", 5))
    puede_c, _ = cfg_central.puede_usar_mitad()
    assert puede_c is True

    cfg_total = ConfigSeccion(seccion="inferior", esquema=EsquemaDiseno("espejo_total", 4))
    puede_t, _ = cfg_total.puede_usar_mitad()
    assert puede_t is True


def test_ciclo_personalizado_simetrico_y_no_simetrico():
    # Simétrico par: 0, 1, 1E, 0E
    esq_sim_par = EsquemaDiseno("personalizado", 4, ciclo=[(0, False), (1, False), (1, True), (0, True)])
    puede, _ = tiene_simetria_espejo(esq_sim_par)
    assert puede is True

    # Simétrico impar con centro neutro: 0, 1, 2, 1E, 0E
    esq_sim_impar = EsquemaDiseno("personalizado", 5, ciclo=[(0, False), (1, False), (2, False), (1, True), (0, True)])
    puede_imp, _ = tiene_simetria_espejo(esq_sim_impar)
    assert puede_imp is True

    # Asimétrico: 0, 1, 2
    esq_asim = EsquemaDiseno("personalizado", 3, ciclo=[(0, False), (1, False), (2, False)])
    puede_asim, motivo = tiene_simetria_espejo(esq_asim)
    assert puede_asim is False
    assert "no es simétrico" in motivo.lower()


def test_proyecto_ida_y_vuelta_con_secciones(tmp_path):
    ent = BalloonInput(950, 30, 2, 1)
    cond = Condiciones()
    cfg_sup = ConfigSeccion("superior", esquema=EsquemaDiseno("repeticion", 5), dibujar="completo", lienzo="abanico", escala="auto")
    cfg_inf = ConfigSeccion("inferior", esquema=EsquemaDiseno("central_espejo", 5), dibujar="mitad", lienzo="abanico", escala="15")
    cfg_pic = ConfigSeccion("pico", esquema_pico=EsquemaDisenoPico(modo_repeticion="ajedrez"), dibujar="completo", lienzo="separadas", escala="20")

    p = Proyecto(
        version=2,
        nombre="Proyecto MultiSeccion",
        entrada=ent,
        condiciones=cond,
        config_secciones={
            "superior": cfg_sup,
            "inferior": cfg_inf,
            "pico": cfg_pic,
        }
    )

    ruta = tmp_path / "multi.json"
    guardar_proyecto(p, str(ruta))

    p2 = cargar_proyecto(str(ruta))
    assert p2.version == 2
    assert p2.config_secciones["superior"].esquema.modo == "repeticion"
    assert p2.config_secciones["superior"].dibujar == "completo"
    assert p2.config_secciones["inferior"].esquema.modo == "central_espejo"
    assert p2.config_secciones["inferior"].dibujar == "mitad"
    assert str(p2.config_secciones["inferior"].escala) == "15"
    assert p2.config_secciones["pico"].esquema_pico.modo_repeticion == "ajedrez"
    assert p2.config_secciones["pico"].lienzo == "separadas"


def test_migracion_proyecto_v1(tmp_path):
    ruta = tmp_path / "v1_viejo.json"
    contenido = {
        "version": 1,
        "nombre": "Globo Antiguo",
        "entrada": {"altura_cuerpo": 950, "num_gajos": 30, "num_hileras_picos": 2, "ancho_costura": 1},
        "esquema": {"modo": "central_espejo", "tam_grupo": 5},
        "hoja": "carta",
        "escala": "20",
        "hoja_dibujar": "mitad",
        "hoja_lienzo": "abanico",
    }
    import json
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido, f)

    p = cargar_proyecto(str(ruta))
    assert p.version == 2
    # El esquema global se migró a superior e inferior
    assert p.config_secciones["superior"].esquema.modo == "central_espejo"
    assert p.config_secciones["superior"].dibujar == "mitad"
    assert p.config_secciones["inferior"].esquema.modo == "central_espejo"
    assert p.config_secciones["inferior"].dibujar == "mitad"
    # Pico queda completo
    assert p.config_secciones["pico"].dibujar == "completo"


def test_generar_paquete_con_secciones_distintas():
    ent = BalloonInput(950, 30, 2, 1)
    calc = TrompoEstrellaCalculator()
    res = calc.calcular(ent)

    cfg_sup = ConfigSeccion("superior", esquema=EsquemaDiseno("repeticion", 5), dibujar="completo", lienzo="abanico", escala="auto")
    cfg_inf = ConfigSeccion("inferior", esquema=EsquemaDiseno("central_espejo", 5), dibujar="mitad", lienzo="abanico", escala="30")
    cfg_pic = ConfigSeccion("pico", esquema_pico=EsquemaDisenoPico(), dibujar="completo", lienzo="abanico", escala="auto")

    archivos = generar_paquete(
        resultado=res,
        entrada=ent,
        hoja="carta",
        config_secciones={"superior": cfg_sup, "inferior": cfg_inf, "pico": cfg_pic},
    )

    # Las hojas se generaron
    assert "hoja_abanico_superior.svg" in archivos
    assert "hoja_abanico_inferior.svg" in archivos
    assert "hoja_abanico_pico.svg" in archivos

    svg_sup = archivos["hoja_abanico_superior.svg"]
    svg_inf = archivos["hoja_abanico_inferior.svg"]

    # Cono superior completo vs inferior mitad producen SVGs distintos
    assert svg_sup != svg_inf
    assert "Abanico completo" in svg_sup
    assert "Medio abanico (espejo)" in svg_inf
    assert "1:30" in svg_inf


def test_sincronizar_y_copiar_configuracion():
    ctrl = ControladorTrompo()
    ctrl.altura = "950"
    ctrl.gajos = "30"
    ctrl.hileras = "2"
    ctrl.costura = "1"
    ctrl.calcular()

    # Configurar cono superior
    ctrl.cambiar_esquema_seccion("superior", "central_espejo", 5)
    ctrl.cambiar_dibujar_seccion("superior", "mitad")
    ctrl.cambiar_escala_seccion("superior", "20")

    # Sincronizar conos
    ctrl.sincronizar_conos("superior")

    cfg_inf = ctrl.obtener_config_seccion("inferior")
    assert cfg_inf.esquema.modo == "central_espejo"
    assert cfg_inf.esquema.tam_grupo == 5
    assert cfg_inf.dibujar == "mitad"
    assert str(cfg_inf.escala) == "20"
