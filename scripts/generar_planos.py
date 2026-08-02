#!/usr/bin/env python3
"""Genera prototipos de plano arquitectónico para usar de fondo en la tarjeta.

Cada prototipo se define con primitivas de dibujo técnico (muros de doble línea
con vanos, arcos de puerta, ejes con globo, cotas, achurados, vegetación) y se
emite en dos formatos, igual que la ilustración del edificio:
  · assets/marcas/topp-create/fondo-plano-<id>.svg  → la tarjeta web
  · assets/marcas/topp-create/fondo-plano-<id>.png  → la imagen para WhatsApp

El lienzo es vertical (2:3) para que encaje en el rectángulo de la tarjeta.
Como el dibujo va al 6-8% de opacidad detrás del contenido, el criterio es que
la mancha quede pareja: sin zonas vacías grandes ni nudos de líneas.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SALIDA_DIR = ROOT / "assets" / "marcas" / "topp-create"

COLOR_LINEA = "#24292D"
ANCHO, ALTO = 1000, 1500
PNG_ANCHO = 1000
SUPERMUESTREO = 3

# Jerarquía de trazo del dibujo técnico: corte, elemento, detalle, auxiliar.
G_CORTE = 5.0
G_ELEMENTO = 2.6
G_DETALLE = 1.5
G_AUXILIAR = 1.0


class Dibujo:
    """Acumula polilíneas con su grosor. Nada se dibuja hasta emitir."""

    def __init__(self):
        self.trazos = []

    def linea(self, p1, p2, grosor=G_ELEMENTO):
        self.trazos.append(([p1, p2], grosor))

    def poli(self, puntos, grosor=G_ELEMENTO, cerrar=False):
        puntos = list(puntos)
        if cerrar:
            puntos = puntos + [puntos[0]]
        self.trazos.append((puntos, grosor))

    def rect(self, x0, y0, x1, y1, grosor=G_ELEMENTO):
        self.poli([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], grosor, cerrar=True)

    def arco(self, cx, cy, radio, desde, hasta, grosor=G_DETALLE, pasos=36):
        puntos = [
            (cx + radio * math.cos(math.radians(desde + (hasta - desde) * i / pasos)),
             cy + radio * math.sin(math.radians(desde + (hasta - desde) * i / pasos)))
            for i in range(pasos + 1)
        ]
        self.poli(puntos, grosor)

    def circulo(self, cx, cy, radio, grosor=G_DETALLE):
        self.arco(cx, cy, radio, 0, 360, grosor)


# ── Primitivas de dibujo técnico ─────────────────────────────────────────────

def muro(d, p1, p2, espesor, huecos=(), grosor=G_CORTE):
    """Muro de doble línea entre dos puntos, con vanos (puertas/ventanas).

    Los huecos se dan como fracciones (desde, hasta) del largo del muro; en cada
    vano se cierran las dos caras con una jamba, que es como se representa el
    corte del muro en planta.
    """
    (x1, y1), (x2, y2) = p1, p2
    largo = math.hypot(x2 - x1, y2 - y1)
    if largo == 0:
        return
    ux, uy = (x2 - x1) / largo, (y2 - y1) / largo
    nx, ny = -uy * espesor / 2, ux * espesor / 2

    tramos = []
    cursor = 0.0
    for desde, hasta in sorted(huecos):
        if desde > cursor:
            tramos.append((cursor, desde))
        cursor = max(cursor, hasta)
    if cursor < 1:
        tramos.append((cursor, 1.0))

    for desde, hasta in tramos:
        ax, ay = x1 + ux * largo * desde, y1 + uy * largo * desde
        bx, by = x1 + ux * largo * hasta, y1 + uy * largo * hasta
        d.linea((ax + nx, ay + ny), (bx + nx, by + ny), grosor)
        d.linea((ax - nx, ay - ny), (bx - nx, by - ny), grosor)
        # Jambas en los extremos de cada tramo.
        d.linea((ax + nx, ay + ny), (ax - nx, ay - ny), grosor)
        d.linea((bx + nx, by + ny), (bx - nx, by - ny), grosor)


def puerta(d, x, y, radio, orientacion=0, sentido=1):
    """Hoja + barrido de apertura, la convención de puerta en planta."""
    ang = orientacion
    hx, hy = x + radio * math.cos(math.radians(ang)), y + radio * math.sin(math.radians(ang))
    d.linea((x, y), (hx, hy), G_DETALLE)
    d.arco(x, y, radio, ang, ang + 90 * sentido, G_AUXILIAR)


def ventana(d, p1, p2, espesor):
    """Vano de ventana: las dos caras del muro más el vidrio al centro."""
    (x1, y1), (x2, y2) = p1, p2
    largo = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / largo, (y2 - y1) / largo
    nx, ny = -uy * espesor / 2, ux * espesor / 2
    for factor in (1, -1, 0):
        d.linea(
            (x1 + nx * factor, y1 + ny * factor),
            (x2 + nx * factor, y2 + ny * factor),
            G_DETALLE if factor else G_AUXILIAR,
        )


def eje(d, p1, p2, etiqueta_radio=26):
    """Eje estructural: línea de trazo y punto con globo en un extremo."""
    (x1, y1), (x2, y2) = p1, p2
    largo = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / largo, (y2 - y1) / largo
    patron = [18, 6, 4, 6]
    pos = 0.0
    indice = 0
    while pos < largo:
        tramo = patron[indice % len(patron)]
        if indice % 2 == 0:
            fin = min(pos + tramo, largo)
            d.linea((x1 + ux * pos, y1 + uy * pos), (x1 + ux * fin, y1 + uy * fin), G_AUXILIAR)
        pos += tramo
        indice += 1
    d.circulo(x1 - ux * etiqueta_radio, y1 - uy * etiqueta_radio, etiqueta_radio, G_DETALLE)


def cota(d, p1, p2, marca=9):
    """Línea de cota con los extremos en aspa, como en plano de obra."""
    (x1, y1), (x2, y2) = p1, p2
    d.linea(p1, p2, G_AUXILIAR)
    largo = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / largo, (y2 - y1) / largo
    for px, py in (p1, p2):
        d.linea((px - (ux + uy) * marca, py - (uy - ux) * marca),
                (px + (ux + uy) * marca, py + (uy - ux) * marca), G_AUXILIAR)


def achurado(d, poligono, angulo=45, paso=16, grosor=G_AUXILIAR):
    """Achurado clipeado contra el polígono, por intersección de rectas."""
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    diagonal = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    dx, dy = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
    nx, ny = -dy, dx

    desplazamiento = -diagonal
    while desplazamiento <= diagonal:
        ox, oy = cx + nx * desplazamiento, cy + ny * desplazamiento
        cortes = []
        for i in range(len(poligono)):
            ax, ay = poligono[i]
            bx, by = poligono[(i + 1) % len(poligono)]
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            t_arista = ((ox - ax) * dy - (oy - ay) * dx) / -den
            if 0 <= t_arista <= 1:
                px, py = ax + ex * t_arista, ay + ey * t_arista
                cortes.append((px - ox) * dx + (py - oy) * dy)
        cortes.sort()
        for i in range(0, len(cortes) - 1, 2):
            t0, t1 = cortes[i], cortes[i + 1]
            d.linea((ox + dx * t0, oy + dy * t0), (ox + dx * t1, oy + dy * t1), grosor)
        desplazamiento += paso


def arbol(d, cx, cy, radio, radios=12):
    """Vegetación en planta: copa y radios, como en plano de implantación."""
    d.circulo(cx, cy, radio, G_DETALLE)
    d.circulo(cx, cy, radio * 0.16, G_AUXILIAR)
    for i in range(radios):
        ang = math.radians(360 * i / radios)
        d.linea(
            (cx + radio * 0.2 * math.cos(ang), cy + radio * 0.2 * math.sin(ang)),
            (cx + radio * 0.95 * math.cos(ang), cy + radio * 0.95 * math.sin(ang)),
            G_AUXILIAR,
        )


def escalera(d, x0, y0, x1, y1, peldanos=12, sentido="v"):
    d.rect(x0, y0, x1, y1, G_ELEMENTO)
    for i in range(1, peldanos):
        if sentido == "v":
            y = y0 + (y1 - y0) * i / peldanos
            d.linea((x0, y), (x1, y), G_DETALLE)
        else:
            x = x0 + (x1 - x0) * i / peldanos
            d.linea((x, y0), (x, y1), G_DETALLE)
    # Flecha de subida.
    if sentido == "v":
        xm = (x0 + x1) / 2
        d.linea((xm, y1 - 12), (xm, y0 + 12), G_AUXILIAR)
        d.poli([(xm - 8, y0 + 26), (xm, y0 + 12), (xm + 8, y0 + 26)], G_AUXILIAR)


# ── Prototipos ───────────────────────────────────────────────────────────────

def prototipo_planta_vivienda():
    """P1 · Planta de vivienda: muros cortados, vanos, mobiliario y terraza."""
    d = Dibujo()
    e = 20  # espesor de muro
    x0, y0, x1, y1 = 90, 150, 910, 1230

    # Envolvente con vanos de ventana.
    muro(d, (x0, y0), (x1, y0), e, huecos=[(0.18, 0.34), (0.60, 0.78)])
    muro(d, (x0, y1), (x1, y1), e, huecos=[(0.22, 0.40), (0.66, 0.80)])
    muro(d, (x0, y0), (x0, y1), e, huecos=[(0.30, 0.46), (0.68, 0.84)])
    muro(d, (x1, y0), (x1, y1), e, huecos=[(0.12, 0.26), (0.55, 0.72)])
    for p1, p2 in [
        ((x0 + 0.18 * (x1 - x0), y0), (x0 + 0.34 * (x1 - x0), y0)),
        ((x0 + 0.60 * (x1 - x0), y0), (x0 + 0.78 * (x1 - x0), y0)),
        ((x0, y0 + 0.30 * (y1 - y0)), (x0, y0 + 0.46 * (y1 - y0))),
        ((x1, y0 + 0.55 * (y1 - y0)), (x1, y0 + 0.72 * (y1 - y0))),
    ]:
        ventana(d, p1, p2, e)

    # Particiones interiores, con puertas.
    muro(d, (x0, 560), (620, 560), e, huecos=[(0.45, 0.62)])
    muro(d, (620, y0), (620, y1), e, huecos=[(0.30, 0.44), (0.72, 0.86)])
    muro(d, (x0, 880), (620, 880), e, huecos=[(0.20, 0.36)])
    muro(d, (330, 880), (330, y1), e, huecos=[(0.40, 0.56)])

    puerta(d, 620 - 118, 560, 100, orientacion=0, sentido=-1)
    puerta(d, 620, y0 + 0.30 * (y1 - y0), 100, orientacion=90)
    puerta(d, 620, y0 + 0.72 * (y1 - y0), 100, orientacion=90)
    puerta(d, 216, 880, 92, orientacion=0)
    puerta(d, 330, 880 + 0.40 * (y1 - 880), 92, orientacion=90, sentido=-1)

    # Núcleo húmedo achurado + escalera.
    achurado(d, [(640, 200), (890, 200), (890, 330), (640, 330)], 45, 20)
    escalera(d, 660, 380, 870, 700, peldanos=13)

    # Mobiliario: cama, sofá, mesa con sillas.
    d.rect(150, 640, 400, 830, G_DETALLE)
    d.linea((150, 690), (400, 690), G_AUXILIAR)
    d.rect(430, 950, 590, 1180, G_DETALLE)
    d.circulo(200, 1050, 78, G_DETALLE)
    for i in range(6):
        ang = math.radians(60 * i)
        d.circulo(200 + 118 * math.cos(ang), 1050 + 118 * math.sin(ang), 26, G_AUXILIAR)
    d.rect(660, 780, 880, 1000, G_DETALLE)
    d.linea((660, 890), (880, 890), G_AUXILIAR)

    # Terraza exterior con despiece.
    d.rect(x0, y1 + 30, x1, 1400, G_DETALLE)
    for i in range(1, 8):
        x = x0 + (x1 - x0) * i / 8
        d.linea((x, y1 + 30), (x, 1400), G_AUXILIAR)

    # Cotas exteriores.
    cota(d, (x0, 100), (620, 100))
    cota(d, (620, 100), (x1, 100))
    cota(d, (50, y0), (50, 560))
    cota(d, (50, 560), (50, y1))
    return d


def prototipo_implantacion():
    """P2 · Planta de implantación: huella, circulaciones, agua y vegetación."""
    d = Dibujo()

    # Curvas de nivel de fondo.
    for i, desfase in enumerate(range(0, 5)):
        puntos = [
            (x, 260 + desfase * 90 + 70 * math.sin(x / 190 + desfase * 0.7))
            for x in range(-40, 1041, 20)
        ]
        d.poli(puntos, G_AUXILIAR)

    # Huella del edificio: dos volúmenes desfasados.
    d.rect(150, 430, 640, 830, G_CORTE)
    d.rect(400, 700, 880, 1090, G_CORTE)
    achurado(d, [(150, 430), (640, 430), (640, 830), (150, 830)], 45, 34, G_AUXILIAR)
    for x in range(190, 641, 60):
        d.linea((x, 430), (x, 830), G_AUXILIAR)
    for y in range(740, 1091, 58):
        d.linea((400, y), (880, y), G_AUXILIAR)

    # Circulación y accesos.
    d.poli([(60, 1290), (300, 1290), (300, 1140), (700, 1140)], G_ELEMENTO)
    d.poli([(60, 1330), (340, 1330), (340, 1180), (700, 1180)], G_ELEMENTO)
    d.linea((520, 1090), (520, 1140), G_DETALLE)
    d.linea((600, 1090), (600, 1140), G_DETALLE)

    # Espejo de agua.
    d.rect(660, 470, 900, 660, G_ELEMENTO)
    achurado(d, [(660, 470), (900, 470), (900, 660), (660, 660)], 0, 18, G_AUXILIAR)

    # Vegetación.
    for cx, cy, r in [(120, 300, 62), (300, 210, 48), (830, 260, 70),
                      (110, 700, 54), (930, 900, 58), (200, 1050, 66),
                      (760, 1290, 74), (450, 1350, 50)]:
        arbol(d, cx, cy, r)

    # Plaza pavimentada, para que la mancha no quede hueca abajo a la izquierda.
    d.rect(70, 900, 330, 1120, G_ELEMENTO)
    for i in range(1, 5):
        d.linea((70, 900 + 220 * i / 5), (330, 900 + 220 * i / 5), G_AUXILIAR)
    for i in range(1, 5):
        d.linea((70 + 260 * i / 5, 900), (70 + 260 * i / 5, 1120), G_AUXILIAR)

    # Norte.
    d.circulo(880, 140, 46, G_DETALLE)
    d.poli([(880, 100), (862, 186), (880, 168), (898, 186)], G_ELEMENTO, cerrar=True)
    return d


def prototipo_reticula():
    """P3 · Retícula estructural: ejes con globo, columnas, vigas y cotas."""
    d = Dibujo()
    xs = [140, 300, 460, 620, 780, 920]
    ys = [230, 400, 570, 740, 910, 1080, 1250]

    for x in xs:
        eje(d, (x, 190), (x, 1310))
    for y in ys:
        eje(d, (100, y), (960, y))

    # Vigas: doble línea entre ejes.
    for y in ys:
        for desfase in (-6, 6):
            d.linea((xs[0], y + desfase), (xs[-1], y + desfase), G_DETALLE)
    for x in xs:
        for desfase in (-6, 6):
            d.linea((x + desfase, ys[0]), (x + desfase, ys[-1]), G_DETALLE)

    # Columnas en los cruces.
    for x in xs:
        for y in ys:
            d.rect(x - 15, y - 15, x + 15, y + 15, G_CORTE)

    # Un par de losas achuradas, para romper la regularidad.
    achurado(d, [(300, 400), (460, 400), (460, 570), (300, 570)], 45, 22, G_AUXILIAR)
    achurado(d, [(620, 910), (780, 910), (780, 1080), (620, 1080)], 45, 22, G_AUXILIAR)

    # Cadena de cotas arriba y a la izquierda.
    for i in range(len(xs) - 1):
        cota(d, (xs[i], 120), (xs[i + 1], 120))
    for i in range(len(ys) - 1):
        cota(d, (60, ys[i]), (60, ys[i + 1]))
    return d


def prototipo_alzado():
    """P4 · Alzado y sección: forjados, ritmo de huecos y terreno."""
    d = Dibujo()
    x0, x1 = 110, 890
    niveles = [1180, 990, 800, 610, 420, 260]

    # Terreno con achurado.
    d.linea((40, 1180), (960, 1180), G_CORTE)
    achurado(d, [(40, 1180), (960, 1180), (960, 1290), (40, 1290)], 60, 22, G_AUXILIAR)

    # Forjados: cada losa en corte, con voladizo alterno.
    for i, y in enumerate(niveles):
        vuelo = 30 if i % 2 else 0
        d.rect(x0 - vuelo, y - 16, x1 + vuelo, y, G_CORTE)

    # Envolvente y ritmo de montantes por planta.
    for i in range(len(niveles) - 1):
        base, techo = niveles[i], niveles[i + 1]
        d.linea((x0, base - 16), (x0, techo), G_ELEMENTO)
        d.linea((x1, base - 16), (x1, techo), G_ELEMENTO)
        for j in range(1, 10):
            x = x0 + (x1 - x0) * j / 10
            d.linea((x, base - 16), (x, techo), G_AUXILIAR)
        # Antepecho.
        d.linea((x0, base - 70), (x1, base - 70), G_DETALLE)

    # Mitad izquierda en sección: se ve el interior.
    corte = 420
    d.linea((corte, niveles[0]), (corte, niveles[-1]), G_DETALLE)
    for i in range(len(niveles) - 1):
        base, techo = niveles[i], niveles[i + 1]
        achurado(d, [(x0, base - 16), (corte, base - 16), (corte, base - 6), (x0, base - 6)],
                 45, 14, G_AUXILIAR)
        d.linea((x0 + 60, base - 16), (x0 + 60, techo), G_AUXILIAR)

    # Cotas de nivel a la derecha.
    for y in niveles:
        d.linea((x1 + 60, y), (x1 + 100, y), G_AUXILIAR)
        d.poli([(x1 + 68, y - 12), (x1 + 84, y), (x1 + 68, y + 12)], G_AUXILIAR, cerrar=True)
    d.linea((x1 + 84, niveles[0]), (x1 + 84, niveles[-1]), G_AUXILIAR)

    # Cubierta plana con antepecho, en línea con el resto del lenguaje.
    d.rect(x0 - 40, niveles[-1] - 84, x1 + 40, niveles[-1] - 68, G_CORTE)
    d.linea((x0 - 40, niveles[-1] - 68), (x0 - 40, niveles[-1] - 16), G_ELEMENTO)
    d.linea((x1 + 40, niveles[-1] - 68), (x1 + 40, niveles[-1] - 16), G_ELEMENTO)
    return d


PROTOTIPOS = {
    "planta": ("Planta de vivienda", prototipo_planta_vivienda),
    "implantacion": ("Planta de implantación", prototipo_implantacion),
    "reticula": ("Retícula estructural", prototipo_reticula),
    "alzado": ("Alzado y sección", prototipo_alzado),
}


# ── Salida ───────────────────────────────────────────────────────────────────

def escribir_svg(dibujo, ruta):
    lineas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" fill="none" '
        f'stroke="{COLOR_LINEA}" stroke-linecap="round" stroke-linejoin="round">'
    ]
    for puntos, grosor in dibujo.trazos:
        d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(puntos))
        lineas.append(f'  <path d="{d}" stroke-width="{grosor}"/>')
    lineas.append("</svg>")
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def rasterizar(dibujo, ancho=PNG_ANCHO):
    escala = ancho * SUPERMUESTREO / ANCHO
    img = Image.new("RGBA", (int(ANCHO * escala), int(ALTO * escala)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = tuple(int(COLOR_LINEA.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
    for puntos, grosor in dibujo.trazos:
        escalados = [(x * escala, y * escala) for x, y in puntos]
        if len(escalados) < 2:
            continue
        draw.line(escalados, fill=color, width=max(1, int(grosor * escala)), joint="curve")
    return img.resize((ancho, int(ALTO / ANCHO * ancho)), Image.LANCZOS)


def main():
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    for clave, (titulo, constructor) in PROTOTIPOS.items():
        dibujo = constructor()
        escribir_svg(dibujo, SALIDA_DIR / f"fondo-plano-{clave}.svg")
        rasterizar(dibujo).save(SALIDA_DIR / f"fondo-plano-{clave}.png")
        print(f"• {clave:14s} {titulo:28s} {len(dibujo.trazos):4d} trazos")


if __name__ == "__main__":
    main()
