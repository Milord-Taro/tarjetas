#!/usr/bin/env python3
"""Genera la ilustración de línea del edificio que va de fondo en la tarjeta.

La geometría se define una sola vez acá, en 3D, y se emite en dos formatos:
  · assets/marcas/topp-create/edificio-linea.svg  → la usa la tarjeta web
  · assets/marcas/topp-create/edificio-linea.png  → la usa la imagen de WhatsApp

Es un axonométrico isométrico de un volumen moderno de dos plantas con losas en
voladizo, terraza y ritmo de montantes.

Las caras se pintan rellenas del color de fondo y en orden de profundidad
(algoritmo del pintor) antes de trazar sus aristas. Sin eso el dibujo queda como
una caja de alambre donde todas las líneas se cruzan entre sí y no se lee nada.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SALIDA_DIR = ROOT / "assets" / "marcas" / "topp-create"

COLOR_LINEA = "#24292D"
COLOR_RELLENO = "#F4F1EC"   # el crema de la tarjeta: las caras tapan sin verse
PNG_ANCHO = 1600
SUPERMUESTREO = 4           # se dibuja a 4x y se reduce, para que la línea quede suave

GRUESO_ESTRUCTURA = 0.070
GRUESO_DETALLE = 0.032


def proyectar(punto):
    """Isométrico: +x baja hacia la derecha, +z baja hacia la izquierda, +y sube."""
    x, y, z = punto
    return ((x - z) * math.cos(math.radians(30)), (x + z) * 0.5 - y)


def centroide(poligono):
    return (
        sum(p[0] for p in poligono) / len(poligono),
        sum(p[1] for p in poligono) / len(poligono),
        sum(p[2] for p in poligono) / len(poligono),
    )


def profundidad(poligono):
    """Con la cámara sobre (1,1,1), lo que tiene mayor x+y+z está más adelante."""
    x, y, z = centroide(poligono)
    return x + y + z


def caras_visibles(x0, x1, y0, y1, z0, z1):
    """Las tres caras de un prisma que miran a la cámara: superior, derecha e izquierda."""
    return [
        [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)],
        [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
    ]


def montantes_cara_x(x, y0, y1, z0, z1, cantidad):
    paso = (z1 - z0) / (cantidad + 1)
    return [[(x, y0, z0 + paso * i), (x, y1, z0 + paso * i)] for i in range(1, cantidad + 1)]


def montantes_cara_z(z, y0, y1, x0, x1, cantidad):
    paso = (x1 - x0) / (cantidad + 1)
    return [[(x0 + paso * i, y0, z), (x0 + paso * i, y1, z)] for i in range(1, cantidad + 1)]


def volumen(x0, x1, y0, y1, z0, z1, montantes=None):
    """Un cuerpo: sus caras visibles + los montantes que van sobre ellas."""
    detalle = []
    if montantes:
        cant_x, cant_z, margen = montantes
        detalle += montantes_cara_x(x1, y0 + margen, y1 - margen, z0, z1, cant_x)
        detalle += montantes_cara_z(z1, y0 + margen, y1 - margen, x0, x1, cant_z)
    return {"caras": caras_visibles(x0, x1, y0, y1, z0, z1), "detalle": detalle}


def construir_edificio():
    """Cuerpos ordenados de atrás hacia adelante (se pintan en ese orden)."""
    cuerpos = [
        # Zócalo / plataforma.
        volumen(-0.7, 10.7, -0.35, 0, -0.7, 7.9),
        # Planta baja, retranqueada para que se lea el voladizo de la losa.
        volumen(0.5, 9.5, 0, 3.0, 0.5, 7.4, montantes=(5, 6, 0.16)),
        # Losa de entrepiso en voladizo.
        volumen(0, 10, 3.0, 3.32, 0, 7.9),
        # Volumen superior: más corto, deja terraza a la derecha.
        volumen(0.5, 6.4, 3.32, 6.2, 0.5, 7.4, montantes=(5, 4, 0.18)),
        # Losa de cubierta, también en voladizo.
        volumen(0, 6.9, 6.2, 6.52, 0, 7.9),
    ]

    # Baranda de la terraza: va delante de todo, sobre la losa de entrepiso.
    y_baranda = 3.32
    alto = 0.95
    baranda = [
        [(6.9, y_baranda + alto, 7.9), (10, y_baranda + alto, 7.9), (10, y_baranda + alto, 0)],
    ]
    for i in range(1, 6):
        x = 6.9 + (10 - 6.9) * i / 6
        baranda.append([(x, y_baranda, 7.9), (x, y_baranda + alto, 7.9)])
    for i in range(1, 8):
        z = 7.9 - 7.9 * i / 8
        baranda.append([(10, y_baranda, z), (10, y_baranda + alto, z)])
    # Parantes de arranque y esquina: sin ellos el pasamanos termina en el aire.
    for extremo in [(6.9, 7.9), (10, 7.9), (10, 0)]:
        x, z = extremo
        baranda.append([(x, y_baranda, z), (x, y_baranda + alto, z)])
    cuerpos.append({"caras": [], "detalle": baranda})

    return cuerpos


# ── Salida ───────────────────────────────────────────────────────────────────

def aplanar(cuerpos):
    """Proyecta todo y devuelve la lista de operaciones de dibujo, ya en orden."""
    operaciones = []
    for cuerpo in cuerpos:
        for cara in sorted(cuerpo["caras"], key=profundidad):
            operaciones.append(("cara", [proyectar(p) for p in cara]))
        for trazo in cuerpo["detalle"]:
            operaciones.append(("detalle", [proyectar(p) for p in trazo]))
    return operaciones


def limites(operaciones):
    puntos = [p for _, poli in operaciones for p in poli]
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    return min(xs), min(ys), max(xs), max(ys)


def escribir_svg(operaciones, ruta, margen=0.35):
    x0, y0, x1, y1 = limites(operaciones)
    ancho = (x1 - x0) + 2 * margen
    alto = (y1 - y0) + 2 * margen

    def puntos(poli):
        return " ".join(f"{p[0] - x0 + margen:.3f},{p[1] - y0 + margen:.3f}" for p in poli)

    lineas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho:.3f} {alto:.3f}" '
        f'stroke="{COLOR_LINEA}" stroke-linecap="round" stroke-linejoin="round">',
    ]
    for tipo, poli in operaciones:
        if tipo == "cara":
            lineas.append(
                f'  <polygon points="{puntos(poli)}" fill="{COLOR_RELLENO}" '
                f'stroke-width="{GRUESO_ESTRUCTURA}"/>'
            )
        else:
            lineas.append(
                f'  <polyline points="{puntos(poli)}" fill="none" '
                f'stroke-width="{GRUESO_DETALLE}" opacity="0.6"/>'
            )
    lineas.append("</svg>")

    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ancho, alto


def escribir_png(operaciones, ruta, ancho_svg, alto_svg, margen=0.35):
    x0, y0, _, _ = limites(operaciones)
    escala = PNG_ANCHO * SUPERMUESTREO / ancho_svg
    ancho_px = int(ancho_svg * escala)
    alto_px = int(alto_svg * escala)

    def rgb(color):
        return tuple(int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    img = Image.new("RGBA", (ancho_px, alto_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for tipo, poli in operaciones:
        puntos = [((p[0] - x0 + margen) * escala, (p[1] - y0 + margen) * escala) for p in poli]
        if tipo == "cara":
            draw.polygon(puntos, fill=rgb(COLOR_RELLENO) + (255,))
            draw.line(puntos + [puntos[0]], fill=rgb(COLOR_LINEA) + (255,),
                      width=max(1, int(GRUESO_ESTRUCTURA * escala)), joint="curve")
        else:
            draw.line(puntos, fill=rgb(COLOR_LINEA) + (155,),
                      width=max(1, int(GRUESO_DETALLE * escala)), joint="curve")

    img = img.resize((PNG_ANCHO, int(alto_px / SUPERMUESTREO)), Image.LANCZOS)
    img.save(ruta)
    return img.size


def main():
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    operaciones = aplanar(construir_edificio())

    ruta_svg = SALIDA_DIR / "edificio-linea.svg"
    ancho, alto = escribir_svg(operaciones, ruta_svg)
    print(f"• {ruta_svg.relative_to(ROOT)}  (viewBox {ancho:.2f} x {alto:.2f})")

    ruta_png = SALIDA_DIR / "edificio-linea.png"
    tamano = escribir_png(operaciones, ruta_png, ancho, alto)
    print(f"• {ruta_png.relative_to(ROOT)}  ({tamano[0]}x{tamano[1]})")


if __name__ == "__main__":
    main()
