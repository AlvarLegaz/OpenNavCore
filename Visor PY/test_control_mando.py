import pygame
import sys

# =========================================================
# CONFIGURACIÓN DEL MANDO ESM-9101
# =========================================================

ZONA_MUERTA = 0.15

# Botones principales
BOTON_1 = 0
BOTON_2 = 2
BOTON_3 = 3
BOTON_4 = 1

# Sticks
EJE_STICK_IZQ_X = 0
EJE_STICK_IZQ_Y = 1

EJE_STICK_DER_X = 2
EJE_STICK_DER_Y = 3

# Gatillos
EJE_GATILLO_IZQ = 4
EJE_GATILLO_DER = 5

ANCHO = 1000
ALTO = 700


def aplicar_zona_muerta(valor, zona_muerta=ZONA_MUERTA):
    if abs(valor) < zona_muerta:
        return 0.0
    return valor


def leer_eje_seguro(mando, eje):
    """
    Lee un eje evitando error si el mando no tiene ese número de eje.
    """
    if eje < mando.get_numaxes():
        return mando.get_axis(eje)
    return 0.0


def leer_mando(mando):
    """
    Lee el estado completo del mando y devuelve un diccionario.

    Devuelve:
    - 4 botones
    - cruceta
    - stick izquierdo
    - stick derecho
    - gatillo izquierdo
    - gatillo derecho
    """

    pygame.event.pump()

    # -----------------------------
    # BOTONES
    # -----------------------------
    botones = {
        "boton_1": bool(mando.get_button(BOTON_1)),
        "boton_2": bool(mando.get_button(BOTON_2)),
        "boton_3": bool(mando.get_button(BOTON_3)),
        "boton_4": bool(mando.get_button(BOTON_4)),
    }

    # -----------------------------
    # CRUCETA
    # -----------------------------
    if mando.get_numhats() > 0:
        hat = mando.get_hat(0)
    else:
        hat = (0, 0)

    cruceta = {
        "arriba": hat == (0, 1),
        "abajo": hat == (0, -1),
        "izquierda": hat == (-1, 0),
        "derecha": hat == (1, 0),
        "valor": hat,
    }

    # -----------------------------
    # STICK IZQUIERDO
    # -----------------------------
    stick_izq_x = aplicar_zona_muerta(
        leer_eje_seguro(mando, EJE_STICK_IZQ_X)
    )

    stick_izq_y = aplicar_zona_muerta(
        leer_eje_seguro(mando, EJE_STICK_IZQ_Y)
    )

    stick_izquierdo = {
        "x": stick_izq_x,
        "y": stick_izq_y,
        "arriba": stick_izq_y < -ZONA_MUERTA,
        "abajo": stick_izq_y > ZONA_MUERTA,
        "izquierda": stick_izq_x < -ZONA_MUERTA,
        "derecha": stick_izq_x > ZONA_MUERTA,
    }

    # -----------------------------
    # STICK DERECHO
    # -----------------------------
    stick_der_x = aplicar_zona_muerta(
        leer_eje_seguro(mando, EJE_STICK_DER_X)
    )

    stick_der_y = aplicar_zona_muerta(
        leer_eje_seguro(mando, EJE_STICK_DER_Y)
    )

    stick_derecho = {
        "x": stick_der_x,
        "y": stick_der_y,
        "arriba": stick_der_y < -ZONA_MUERTA,
        "abajo": stick_der_y > ZONA_MUERTA,
        "izquierda": stick_der_x < -ZONA_MUERTA,
        "derecha": stick_der_x > ZONA_MUERTA,
    }

    # -----------------------------
    # GATILLOS
    # -----------------------------
    gatillo_izq = leer_eje_seguro(mando, EJE_GATILLO_IZQ)
    gatillo_der = leer_eje_seguro(mando, EJE_GATILLO_DER)

    # Algunos mandos entregan los gatillos de -1 a 1.
    # Los convertimos a 0 - 1 para que sea más cómodo.
    gatillo_izq_norm = (gatillo_izq + 1) / 2
    gatillo_der_norm = (gatillo_der + 1) / 2

    estado = {
        "botones": botones,
        "cruceta": cruceta,
        "stick_izquierdo": stick_izquierdo,
        "stick_derecho": stick_derecho,
        "gatillos": {
            "izquierdo": gatillo_izq_norm,
            "derecho": gatillo_der_norm,
            "izquierdo_raw": gatillo_izq,
            "derecho_raw": gatillo_der,
        },
    }

    return estado


def dibujar_texto(pantalla, texto, x, y, fuente, color=(255, 255, 255)):
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, (x, y))


def dibujar_boton(pantalla, x, y, texto, activo, fuente, ancho=110, alto=50):
    color = (0, 180, 0) if activo else (70, 70, 70)

    pygame.draw.rect(
        pantalla,
        color,
        (x, y, ancho, alto),
        border_radius=10
    )

    pygame.draw.rect(
        pantalla,
        (255, 255, 255),
        (x, y, ancho, alto),
        2,
        border_radius=10
    )

    etiqueta = fuente.render(texto, True, (255, 255, 255))
    rect = etiqueta.get_rect(center=(x + ancho // 2, y + alto // 2))
    pantalla.blit(etiqueta, rect)


def dibujar_barra_eje(pantalla, x, y, ancho, alto, valor, titulo, fuente):
    """
    Barra horizontal para valores de -1.0 a 1.0
    """

    centro = x + ancho // 2

    dibujar_texto(
        pantalla,
        f"{titulo}: {valor:.2f}",
        x,
        y - 32,
        fuente
    )

    pygame.draw.rect(
        pantalla,
        (60, 60, 60),
        (x, y, ancho, alto),
        border_radius=8
    )

    pygame.draw.rect(
        pantalla,
        (255, 255, 255),
        (x, y, ancho, alto),
        2,
        border_radius=8
    )

    pygame.draw.line(
        pantalla,
        (255, 255, 255),
        (centro, y),
        (centro, y + alto),
        2
    )

    longitud = int((ancho // 2) * valor)

    if longitud >= 0:
        rect_barra = (centro, y + 5, longitud, alto - 10)
    else:
        rect_barra = (centro + longitud, y + 5, abs(longitud), alto - 10)

    pygame.draw.rect(
        pantalla,
        (0, 150, 255),
        rect_barra,
        border_radius=6
    )


def dibujar_barra_gatillo(pantalla, x, y, ancho, alto, valor, titulo, fuente):
    """
    Barra horizontal para gatillos.
    Valor de 0.0 a 1.0.
    """

    valor = max(0.0, min(1.0, valor))

    dibujar_texto(
        pantalla,
        f"{titulo}: {valor:.2f}",
        x,
        y - 32,
        fuente
    )

    pygame.draw.rect(
        pantalla,
        (60, 60, 60),
        (x, y, ancho, alto),
        border_radius=8
    )

    pygame.draw.rect(
        pantalla,
        (255, 255, 255),
        (x, y, ancho, alto),
        2,
        border_radius=8
    )

    longitud = int(ancho * valor)

    pygame.draw.rect(
        pantalla,
        (0, 150, 255),
        (x + 5, y + 5, max(0, longitud - 10), alto - 10),
        border_radius=6
    )


def dibujar_cruceta(pantalla, estado_cruceta, fuente):
    x = 80
    y = 360

    ancho_boton = 95
    alto_boton = 42

    dibujar_texto(pantalla, "CRUCETA", x + 55, y - 45, fuente)

    dibujar_boton(
        pantalla,
        x + ancho_boton,
        y,
        "ARR",
        estado_cruceta["arriba"],
        fuente,
        ancho_boton,
        alto_boton
    )

    dibujar_boton(
        pantalla,
        x + ancho_boton,
        y + alto_boton * 2,
        "ABA",
        estado_cruceta["abajo"],
        fuente,
        ancho_boton,
        alto_boton
    )

    dibujar_boton(
        pantalla,
        x,
        y + alto_boton,
        "IZQ",
        estado_cruceta["izquierda"],
        fuente,
        ancho_boton,
        alto_boton
    )

    dibujar_boton(
        pantalla,
        x + ancho_boton * 2,
        y + alto_boton,
        "DER",
        estado_cruceta["derecha"],
        fuente,
        ancho_boton,
        alto_boton
    )


def dibujar_interfaz(pantalla, estado, fuente, fuente_grande, nombre_mando, num_ejes):
    pantalla.fill((25, 25, 25))

    dibujar_texto(
        pantalla,
        "Monitor visual de mando ESM-9101",
        30,
        25,
        fuente_grande
    )

    dibujar_texto(
        pantalla,
        f"Mando detectado: {nombre_mando} | Ejes detectados: {num_ejes}",
        30,
        70,
        fuente
    )

    # -----------------------------
    # BOTONES
    # -----------------------------
    dibujar_texto(pantalla, "BOTONES", 100, 125, fuente)

    dibujar_boton(
        pantalla,
        60,
        170,
        "B1",
        estado["botones"]["boton_1"],
        fuente
    )

    dibujar_boton(
        pantalla,
        190,
        170,
        "B2",
        estado["botones"]["boton_2"],
        fuente
    )

    dibujar_boton(
        pantalla,
        60,
        235,
        "B3",
        estado["botones"]["boton_3"],
        fuente
    )

    dibujar_boton(
        pantalla,
        190,
        235,
        "B4",
        estado["botones"]["boton_4"],
        fuente
    )

    # -----------------------------
    # CRUCETA
    # -----------------------------
    dibujar_cruceta(pantalla, estado["cruceta"], fuente)

    # -----------------------------
    # STICK IZQUIERDO
    # -----------------------------
    dibujar_texto(pantalla, "STICK IZQUIERDO", 430, 125, fuente)

    dibujar_barra_eje(
        pantalla,
        400,
        190,
        260,
        32,
        estado["stick_izquierdo"]["x"],
        "Izq X",
        fuente
    )

    dibujar_barra_eje(
        pantalla,
        400,
        280,
        260,
        32,
        estado["stick_izquierdo"]["y"],
        "Izq Y",
        fuente
    )

    dibujar_texto(
        pantalla,
        f"A:{estado['stick_izquierdo']['arriba']} "
        f"B:{estado['stick_izquierdo']['abajo']} "
        f"I:{estado['stick_izquierdo']['izquierda']} "
        f"D:{estado['stick_izquierdo']['derecha']}",
        400,
        335,
        fuente
    )

    # -----------------------------
    # STICK DERECHO
    # -----------------------------
    dibujar_texto(pantalla, "STICK DERECHO", 720, 125, fuente)

    dibujar_barra_eje(
        pantalla,
        700,
        190,
        260,
        32,
        estado["stick_derecho"]["x"],
        "Der X",
        fuente
    )

    dibujar_barra_eje(
        pantalla,
        700,
        280,
        260,
        32,
        estado["stick_derecho"]["y"],
        "Der Y",
        fuente
    )

    dibujar_texto(
        pantalla,
        f"A:{estado['stick_derecho']['arriba']} "
        f"B:{estado['stick_derecho']['abajo']} "
        f"I:{estado['stick_derecho']['izquierda']} "
        f"D:{estado['stick_derecho']['derecha']}",
        700,
        335,
        fuente
    )

    # -----------------------------
    # GATILLOS
    # -----------------------------
    dibujar_texto(pantalla, "GATILLOS", 430, 430, fuente)

    dibujar_barra_gatillo(
        pantalla,
        400,
        500,
        260,
        32,
        estado["gatillos"]["izquierdo"],
        "Gatillo izquierdo",
        fuente
    )

    dibujar_barra_gatillo(
        pantalla,
        700,
        500,
        260,
        32,
        estado["gatillos"]["derecho"],
        "Gatillo derecho",
        fuente
    )

    dibujar_texto(
        pantalla,
        f"Raw gatillos: IZQ {estado['gatillos']['izquierdo_raw']:.2f} | "
        f"DER {estado['gatillos']['derecho_raw']:.2f}",
        400,
        560,
        fuente
    )

    dibujar_texto(
        pantalla,
        f"Valor cruceta: {estado['cruceta']['valor']}",
        60,
        555,
        fuente
    )

    dibujar_texto(
        pantalla,
        "Pulsa ESC o cierra la ventana para salir",
        30,
        650,
        fuente
    )


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No se ha detectado ningún mando.")
        sys.exit()

    mando = pygame.joystick.Joystick(0)
    mando.init()

    nombre_mando = mando.get_name()
    num_ejes = mando.get_numaxes()

    print("Mando detectado:", nombre_mando)
    print("Ejes detectados:", num_ejes)
    print("Botones detectados:", mando.get_numbuttons())
    print("Crucetas detectadas:", mando.get_numhats())

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Monitor visual de mando ESM-9101")

    fuente = pygame.font.SysFont("Arial", 20)
    fuente_grande = pygame.font.SysFont("Arial", 32, bold=True)

    reloj = pygame.time.Clock()
    ejecutando = True

    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False

        estado = leer_mando(mando)

        dibujar_interfaz(
            pantalla=pantalla,
            estado=estado,
            fuente=fuente,
            fuente_grande=fuente_grande,
            nombre_mando=nombre_mando,
            num_ejes=num_ejes
        )

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()