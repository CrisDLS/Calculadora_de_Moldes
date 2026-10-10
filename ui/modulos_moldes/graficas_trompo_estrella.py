import math
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from logic.models import BalloonCalculationResult

def _puntos_x_y(puntos, invertido=False):
    x = [p.ancho_medio for p in puntos]
    if invertido:
        x = [-v for v in x]
    y = [p.largo_acumulado for p in puntos]
    return x, y

def _configurar_ejes(ax, tema, titulo, limite_y_inf=0):
    ax.set_facecolor(tema["fondo_grafica"])
    ax.spines['bottom'].set_color(tema["lineas"])
    ax.spines['top'].set_color(tema["lineas"])
    ax.spines['left'].set_color(tema["lineas"])
    ax.spines['right'].set_color(tema["lineas"])
    ax.tick_params(colors=tema["texto"])
    ax.set_title(titulo, color=tema["texto"], pad=10, fontsize=10)
    ax.set_xlabel("cm", color=tema["texto"], fontsize=8)
    ax.set_ylabel("cm", color=tema["texto"], fontsize=8)

def figura_moldes(resultado: BalloonCalculationResult, tema: dict) -> Figure:
    fig = Figure(figsize=(8, 4), facecolor=tema["fondo_figura"])
    
    # 3 subplots para las 3 piezas
    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)
    
    # Cantidad real de piezas, gajos = resultado.seccion_superior.puntos... no, usar recomendados
    gajos = resultado.gajos_min_70cm
    hileras = round(resultado.altura_picos / resultado.ancho_max_gajo)
    
    piezas = [
        (ax1, resultado.seccion_superior, f"Cono Superior\n({gajos} piezas)"),
        (ax2, resultado.seccion_picos, f"Pico\n({gajos * hileras} piezas)"),
        (ax3, resultado.seccion_inferior, f"Cono Inferior\n({gajos} piezas)")
    ]
    
    color_linea = tema["acento"]
    color_pestana = tema.get("pestana", "#ff9900")
    
    for idx, (ax, seccion, titulo) in enumerate(piezas):
        xr, y = _puntos_x_y(seccion.puntos)
        xl, _ = _puntos_x_y(seccion.puntos, invertido=True)
        
        # Modo avanzado: pestaña en el cono inferior
        if idx == 2 and resultado.boca is not None and resultado.boca.pestana > 0:
            if len(y) > 1:
                y0, y1 = y[0], y[1]
                xl0, xr0 = xl[0], xr[0]
                ax.fill_between([xl0, xr0], y0, y1, color=color_pestana, alpha=0.5)
                ax.text(0, (y0 + y1)/2, "Pestaña", color=tema["texto"], fontsize=6, ha="center", va="center")
        
        # Dibuja contorno izquierdo y derecho
        ax.plot(xl, y, color=color_linea, lw=1.5)
        ax.plot(xr, y, color=color_linea, lw=1.5)
        
        # Tapa arriba y abajo
        ax.plot([xl[0], xr[0]], [y[0], y[0]], color=color_linea, lw=1.5)
        ax.plot([xl[-1], xr[-1]], [y[-1], y[-1]], color=color_linea, lw=1.5)
        
        # Marcar puntos
        ax.plot(xr, y, 'o', color=color_linea, markersize=3)
        ax.plot(xl, y, 'o', color=color_linea, markersize=3)
        
        _configurar_ejes(ax, tema, titulo)
        ax.set_aspect('equal')
        
        # Rotular dimensiones
        largo_total = seccion.puntos[-1].largo_acumulado
        ancho_max = max(xr) * 2
        ax.text(0, y[-1] + largo_total*0.05, f"Alto:\n{largo_total:.1f}", color=tema["texto"], fontsize=7, ha="center")
        ax.text(max(xr), y[len(y)//2], f" Ancho máx:\n {ancho_max:.1f}", color=tema["texto"], fontsize=7, ha="left")

    fig.tight_layout()
    return fig

def figura_perfil(resultado: BalloonCalculationResult, tema: dict) -> Figure:
    fig = Figure(figsize=(4, 6), facecolor=tema["fondo_figura"])
    ax = fig.add_subplot(111)
    
    r = resultado.diametro_globo / 2
    rb = resultado.diametro_boquilla_calculado / 2 if resultado.diametro_boquilla_calculado else r * 0.11
    
    h_inf = resultado.altura_cuerpo_base - math.sqrt(resultado.seccion_superior.puntos[-1].largo_acumulado**2 - r**2)
    largo_picos = resultado.altura_picos
    
    y = [0, h_inf, h_inf + largo_picos, resultado.altura_total_real]
    xr = [rb, r, r, 0]
    xl = [-x for x in xr]
    
    ax.plot(xr, y, color=tema["acento"], lw=2)
    ax.plot(xl, y, color=tema["acento"], lw=2)
    ax.plot([xl[0], xr[0]], [y[0], y[0]], color=tema["acento"], lw=2)
    
    _configurar_ejes(ax, tema, "Perfil armado\n(aproximado)")
    ax.set_aspect('equal')
    
    ax.text(0, -resultado.altura_total_real*0.05, f"Boca: {rb*2:.1f} cm", color=tema["texto"], fontsize=8, ha="center", va="top")
    ax.text(r, h_inf + largo_picos/2, f" Diámetro máx:\n {r*2:.1f} cm", color=tema["texto"], fontsize=8, ha="left")
    ax.text(0, resultado.altura_total_real*1.05, f"Alto total: {resultado.altura_total_real:.1f} cm", color=tema["texto"], fontsize=8, ha="center")
    
    fig.tight_layout()
    return fig
