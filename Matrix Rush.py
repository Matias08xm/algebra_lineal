import numpy as np
import random
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import threading
import time

# Configuración inicial
DIM = 7
PUNTAJE_ENEMIGO = 10
PUNTAJE_ALIADO = -30
PUNTAJE_MULTI = 50

# Vectores de unos para la multiplicación tradicional (P * I * Q)
P = np.ones((1, DIM), dtype=int)
Q = np.ones((DIM, 1), dtype=int)

# Variables de estado global del juego
class EstadoJuego:
    def __init__(self):
        self.puntos = 0
        self.multiplicador_global = 1
        self.duracion_multi = 0
        self.tiempo_restante = 60
        self.juego_activo = True
        self.E = self.inicializar_tablero()

    def inicializar_tablero(self):
        # Inicializamos todo el tablero lleno de aliados
        tablero = np.full((DIM, DIM), PUNTAJE_ALIADO, dtype=int)

        # Decidimos cuántos enemigos colocar (entre 12 y 18)
        n_enemigos = random.randint(12, 18)

        # Obtenemos todas las celdas disponibles
        celdas = [(f, c) for f in range(DIM) for c in range(DIM)]
        random.shuffle(celdas)

        # Colocamos un único multiplicador en la primera celda
        f_m, c_m = celdas[0]
        tablero[f_m, c_m] = PUNTAJE_MULTI

        # Colocamos los enemigos en las celdas restantes
        for i in range(1, min(n_enemigos + 1, len(celdas))):
            f_e, c_e = celdas[i]
            tablero[f_e, c_e] = PUNTAJE_ENEMIGO

        return tablero

    def reiniciar_tablero(self):
        self.E = self.inicializar_tablero()

estado = EstadoJuego()

# Elementos de la interfaz de usuario
output_tablero = widgets.Output()
output_mates = widgets.Output()
label_marcador = widgets.HTML()

# Indicador de tiempo simple en HTML para evitar bugs de rendimiento
label_tiempo = widgets.HTML()

# Botón para volver a spawnear enemigos
btn_respawn = widgets.Button(description="🔄 Respawn Enemigos", button_style='primary', layout=widgets.Layout(margin='10px 0'))

def formatear_matriz_html(matriz, titulo):
    """Genera una representación HTML elegante de una matriz NumPy"""
    html = f"<div style='margin: 10px; font-family: monospace;'><strong>{titulo}:</strong><br>"
    html += "<table style='border-left: 2px solid black; border-right: 2px solid black; border-collapse: collapse; margin-top: 5px;'>"
    for fila in matriz:
        html += "<tr>"
        for val in fila:
            color = "black"
            if val > 0: color = "green"
            elif val < 0: color = "red"
            html += f"<td style='padding: 4px 10px; text-align: right; color: {color};'>{val}</td>"
        html += "</tr>"
    html += "</table></div>"
    return html

def actualizar_marcador():
    multi_txt = f"<span style='color: gold; font-weight: bold;'>X2 ({estado.duracion_multi} turnos)</span>" if estado.duracion_multi > 0 else "X1"
    estado_txt = "<span style='color: #2ecc71;'>ACTIVO</span>" if estado.juego_activo else "<span style='color: #e74c3c; font-weight: bold;'>¡TIEMPO TERMINADO!</span>"
    label_marcador.value = f"""
    <div style='background-color: #2c3e50; color: white; padding: 15px; border-radius: 8px; font-family: sans-serif;'>
        <h2 style='margin: 0;'>🎮 MATRIX RUSH INTERACTIVO</h2>
        <p style='font-size: 16px; margin: 5px 0 0 0;'>
            <strong>Puntos Totales:</strong> <span style='font-size: 20px; color: #2ecc71;'>{estado.puntos}</span> |
            <strong>Multiplicador:</strong> {multi_txt} |
            <strong>Estado:</strong> {estado_txt}
        </p>
    </div>
    """

def actualizar_reloj_html():
    color_tiempo = "#e74c3c" if estado.tiempo_restante <= 15 else "#2c3e50"
    label_tiempo.value = f"""
    <div style='background-color: {color_tiempo}; color: white; padding: 10px 20px; border-radius: 8px; font-family: sans-serif; font-size: 18px; font-weight: bold; text-align: center;'>
        ⏱️ Tiempo restante: {estado.tiempo_restante}s
    </div>
    """

def procesar_turno(f, c):
    if not estado.juego_activo:
        return

    # Guardar multiplicador previo para la demostración visual del turno actual
    mult_aplicado = 2 if estado.duracion_multi > 0 else 1

    # Actualizar estado del multiplicador
    if estado.duracion_multi > 0:
        estado.duracion_multi -= 1
        estado.multiplicador_global = 2
    else:
        estado.multiplicador_global = 1

    # 1. Matriz de Acción (A)
    A = np.zeros((DIM, DIM), dtype=int)
    A[f, c] = 1

    # 2. Producto de Hadamard (I = E ∘ A)
    I = estado.E * A

    # 3. Multiplicación Tradicional (P * I * Q)
    PI = np.dot(P, I)
    S_matriz = np.dot(PI, Q)
    S = S_matriz[0, 0]

    # 4. Lógicas según el valor matemático (S)
    puntos_accion = 0
    mensaje_resultado = ""
    if S == PUNTAJE_ENEMIGO:
        puntos_accion = S * mult_aplicado
        estado.puntos += puntos_accion
        if mult_aplicado == 2:
            mensaje_resultado = f"<h3 style='color: #2ecc71;'>🎯 ¡Enemigo eliminado! +20 pts (Multiplicador X2 Aplicado)</h3>"
        else:
            mensaje_resultado = f"<h3 style='color: #2ecc71;'>🎯 ¡Enemigo eliminado! +10 pts</h3>"
    elif S == PUNTAJE_ALIADO:
        puntos_accion = S
        estado.puntos += puntos_accion
        mensaje_resultado = f"<h3 style='color: #e74c3c;'>💀 ¡Aliado dañado! {puntos_accion} pts</h3>"
    elif S == PUNTAJE_MULTI:
        puntos_accion = S
        estado.puntos += puntos_accion
        estado.duracion_multi = 3
        mensaje_resultado = f"<h3 style='color: #f1c40f;'>⚡ ¡Multiplicador Activado! +50 pts y X2 por 3 turnos.</h3>"
    else:
        mensaje_resultado = "<h3 style='color: #95a5a6;'>💨 Fallaste, celda vacía (0).</h3>"

    # 5. Actualización del tablero usando resta de matrices (E_nuevo = E - I)
    estado.E = estado.E - I

    # Si la celda clickeada queda vacía (0), la rellenamos con un aliado para mantener el tablero lleno
    if estado.E[f, c] == 0:
         estado.E[f, c] = PUNTAJE_ALIADO

    # Mostrar demostración matemática con el cálculo de multiplicación detallado con el x2 si aplica
    with output_mates:
        clear_output(wait=True)

        if S == PUNTAJE_ENEMIGO and mult_aplicado == 2:
            # Forzar la visualización directa del +20 en la ecuación de S
            calculo_final_str = f"<strong>[ {puntos_accion} ]</strong> <span style='font-size: 13px; color: #2ecc71;'>(Base {S} × Multiplicador 2)</span>"
        elif S == PUNTAJE_MULTI:
            calculo_final_str = f"<strong>[ +{puntos_accion} ]</strong> <span style='font-size: 13px; color: #f1c40f;'>(Multiplicador Activado)</span>"
        else:
            signo = "+" if puntos_accion > 0 else ""
            color_puntos = "#2ecc71" if puntos_accion > 0 else "#e74c3c"
            calculo_final_str = f"<strong style='color: {color_puntos};'>{signo}{puntos_accion} pts</strong>"

        html_complet = f"""
        <div style='background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 8px;'>
            <h3 style='margin-top: 0;'>🧮 Demostración Matemática del Clic en ({f}, {c}):</h3>
            {mensaje_resultado}
            <div style='display: flex; flex-wrap: wrap;'>
                {formatear_matriz_html(A, "1. Matriz de Acción (A)")}
                {formatear_matriz_html(I, "2. Prod. Hadamard (I = E ∘ A)")}
            </div>
            <div style='margin-top: 15px; font-family: sans-serif;'>
                <strong>3. Multiplicación Tradicional (S = P × I × Q):</strong><br>
                <span style='font-family: monospace;'>Vector P (1x7) × Matriz I (7x7) × Vector Q (7x1) = {calculo_final_str}</span>
            </div>
            <div style='display: flex; flex-wrap: wrap; margin-top: 15px;'>
                {formatear_matriz_html(estado.E + I - I, "Tablero Anterior (E)")}
                {formatear_matriz_html(estado.E, "4. Tablero Nuevo (E_nuevo = E - I)")}
            </div>
        </div>
        """
        display(HTML(html_complet))

    actualizar_marcador()
    dibujar_tablero()

def al_hacer_click(b):
    f = b.row
    c = b.col
    procesar_turno(f, c)

def al_hacer_respawn(b):
    if not estado.juego_activo:
        return
    estado.reiniciar_tablero()
    actualizar_marcador()
    dibujar_tablero()
    with output_mates:
        clear_output(wait=True)
        display(HTML("<h3 style='color: #2980b9;'>🔄 ¡Enemigos regenerados en el tablero!</h3>"))

btn_respawn.on_click(al_hacer_respawn)

def dibujar_tablero():
    with output_tablero:
        clear_output(wait=True)
        grid_items = []
        for i in range(DIM):
            for j in range(DIM):
                val = estado.E[i, j]
                if val == PUNTAJE_ENEMIGO:
                    label, style, color = "E", "warning", "#f39c12"
                elif val == PUNTAJE_ALIADO:
                    label, style, color = "A", "danger", "#e74c3c"
                elif val == PUNTAJE_MULTI:
                    label, style, color = "M", "success", "#2ecc71"
                else:
                    label, style, color = ".", "", "#bdc3c7"

                btn = widgets.Button(
                    description=label,
                    layout=widgets.Layout(width='45px', height='45px', margin='2px'),
                    button_style=style,
                    disabled=not estado.juego_activo
                )
                btn.row = i
                btn.col = j
                btn.on_click(al_hacer_click)
                grid_items.append(btn)

        # Crear Grid de 7x7 botones
        grid = widgets.GridBox(
            grid_items,
            layout=widgets.Layout(grid_template_columns="repeat(7, 49px)")
        )

        # Leyenda de iconos
        leyenda = widgets.HTML("""
        <div style='margin-top: 10px; font-family: sans-serif; font-size: 13px;'>
            <span style='color: #f39c12; font-weight: bold;'>E</span> = Enemigo (+10) |
            <span style='color: #e74c3c; font-weight: bold;'>A</span> = Aliado (-30) |
            <span style='color: #2ecc71; font-weight: bold;'>M</span> = Multiplicador (+50 y combo X2)
        </div>
        """)

        display(widgets.VBox([grid, leyenda]))

# Función para el hilo del temporizador
def funcion_temporizador():
    while estado.tiempo_restante > 0:
        time.sleep(1)
        estado.tiempo_restante -= 1
        actualizar_reloj_html()

    estado.juego_activo = False
    btn_respawn.disabled = True
    actualizar_marcador()
    dibujar_tablero()
    with output_mates:
        clear_output(wait=True)
        display(HTML(f"""
        <div style='background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 8px; text-align: center;'>
            <h2 style='color: #721c24; margin-top: 0;'>⏱️ ¡Fin del Tiempo!</h2>
            <p style='font-size: 18px;'>Puntuación Final conseguida: <strong style='font-size: 24px; color: #2ecc71;'>{estado.puntos} pts</strong></p>
        </div>
        """
        ))

# Reiniciamos las variables de control
estado = EstadoJuego()
actualizar_reloj_html()
btn_respawn.disabled = False

# Inicialización y renderizado de la UI
actualizar_marcador()
dibujar_tablero()

# Mostrar elementos en VBox
display(widgets.VBox([
    label_marcador,
    widgets.HBox([label_tiempo, btn_respawn], layout=widgets.Layout(justify_content='space-between', align_items='center', margin='10px 0')),
    widgets.HBox([
        widgets.VBox([widgets.HTML("<h3>Tablero de Juego</h3>"), output_tablero], layout=widgets.Layout(margin='0 20px 0 0')),
        widgets.VBox([widgets.HTML("<h3>Panel Matemático</h3>"), output_mates])
    ])
]))

# Iniciar hilo del temporizador
hilo_temp = threading.Thread(target=funcion_temporizador)
hilo_temp.start()
