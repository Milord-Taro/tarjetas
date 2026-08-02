#!/usr/bin/env python3
"""Genera QR + imagen para WhatsApp para cada persona, a partir de
   build/manifiesto.json (que produce `node scripts/build.mjs`, hay que correrlo
   antes).

   Este script NO lee data/*.json. Lo hacía, y era un agujero: toda la
   validación del proyecto vive en build.mjs, así que un dato que la web
   rechazaba llegaba acá intacto. En concreto, un campo "url_publica" en la
   ficha decidía qué URL quedaba grabada en el QR —el QR es lo que se imprime y
   lo que nadie revisa a ojo—. Ahora la única entrada es el manifiesto, que ya
   viene validado y normalizado, y la URL la calcula el build.

   El arte es el mismo del tema v2 —cuña con corte diagonal y, encima, bloque
   cortado en chevron; cuerpo claro con la jerarquía de contacto en un solo
   bloque y pie— pero los colores no están aquí: llegan en el manifiesto por
   ROL (bloque, cuña, superficie, línea…) según el tema activo. Así la imagen
   sigue al tema sin tocar este archivo."""

import json
import math
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent

# Por defecto, el manifiesto del repo. Se puede pasar otro como argumento para
# renderizar una compilación hecha con `build.mjs --out` en otro sitio, que es
# como se sacan las maquetas de un tema sin tocar lo publicado.
MANIFIESTO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build" / "manifiesto.json"

# Roles del arte, con los valores de la v2 como respaldo. Los de verdad los
# resuelve build.mjs según el tema activo (ARTE_POR_TEMA) y llegan en el
# manifiesto: aquí solo se dibuja.
ARTE_RESPALDO = {
    "lienzo": "#F4F1EC",
    "bloque": "#24292D",
    "cuna": "#83855B",
    "superficie": "#83855B",
    "sobre_bloque": "#F4F1EC",
    "sobre_superficie": "#F4F1EC",
    "texto": "#24292D",
    "texto_suave": "#6B6C47",
    "texto_secundario": "#4D4D4D",
    "realce": "#83855B",
    "linea": "#83855B",
    "linea_suave": "#A8AA7C",
    "pie": "#83855B",
    "sobre_pie": "#FFFFFF",
    "marco_qr": "#24292D",
    "qr_modulo": "#24292D",
    "qr_fondo": "#FFFFFF",
}

WIDTH, HEIGHT = 1080, 2000
MARGEN_X = 96
ANCHO_UTIL = WIDTH - 2 * MARGEN_X

# Cabecera: la cuña lleva un corte diagonal simple y el bloque que va encima
# lleva un corte en chevron con el vértice al 20% del ancho — por eso la franja
# de la cuña es delgada a la derecha y ancha a la izquierda.
#
# La profundidad es 0.267 del ancho, la misma proporción que el CSS de la web
# (--corte-prof: 112px sobre una tarjeta de ~420). Antes era 0.30, y con ese
# corte más profundo la diagonal subía tanto hacia la derecha que quedaba
# tocando el pie de "CONSTRUCCIÓN": 0 px de holgura. Con 0.267 y la base 20 px
# más abajo, el tagline respira ~50 px, como en la web.
CORTE_PROF = int(WIDTH * 0.267)  # profundidad total (punta izquierda de la cuña)
CORTE_VERTICE_X = int(WIDTH * 0.20)
CABECERA_BASE = 568              # y donde termina la cuña (borde izquierdo)

LOGO_TOP = 46
LOGO_MAX_W = 400
LOGO_MAX_H = 162
TAGLINE_GAP = 30

# El lienzo sigue midiendo 1080x2000: los 20 px que bajó la cabecera salen del
# cuerpo. En vez de recortárselos a un solo bloque —que descuadraría el ritmo—
# se ajustan todos los aires por el mismo factor, así la tarjeta se cierra de
# forma pareja y mantiene las proporciones entre sus zonas. AIRE es el único
# número que hay que tocar si la cabecera vuelve a cambiar de alto.
AIRE = 0.94
_aire = lambda px: int(round(px * AIRE))

NOMBRE_TOP = CABECERA_BASE + 12
NOMBRE_INTERLINEA = 74
GAP_NOMBRE_CARGO = _aire(20)
GAP_CARGO_REGLA = _aire(18)
GAP_REGLA_SECCION = _aire(56)

GAP_TITULO_REGLA = _aire(32)
GAP_REGLA_FILA = _aire(26)
# Estos tres son métricas de línea, atadas al cuerpo de la letra: no se escalan
# con el aire porque apretarlos no es dar menos espacio, es partir el texto.
ALTO_ETIQUETA = 28
ALTO_VALOR = 42
ALTO_LINEA_DIRECCION = 38
GAP_ENTRE_FILAS = _aire(34)
GAP_ENTRE_SECCIONES = _aire(40)
GAP_SECCION_REDES = _aire(46)
GAP_REDES_QR = _aire(26)

BADGE_RADIO = 30
GAP_BADGE_TEXTO = 26
BADGE_RED_RADIO = 34

QR_TAMANO = 360
QR_MARCO_PAD = 18
QR_MARCO_RADIO = 24
QR_GAP = 48

PIE_ALTO = 80

# Tipografía de la marca que se está dibujando. La declara marcas.json y la
# resuelve build.mjs, que es quien sabe si el archivo existe y bajo qué licencia
# se puede servir; aquí solo se usa. Se fija por persona en main(), porque dos
# marcas distintas pueden traer fuentes distintas.
FUENTE_MARCA = None

# Iconos propios de la marca que reemplazan a los dibujados con primitivas. Los
# decide build.mjs según el tema y llegan por el manifiesto; el rol que no esté
# aquí se sigue dibujando como siempre.
ICONOS_MARCA = {}

# El archivo viene sobre un lienzo de 150 con el dibujo ocupando entre el 46% y
# el 62%. Se recorta al dibujo antes de escalar: usando el lienzo entero el
# icono sale a la mitad de tamaño que los dibujados por código. Y se engrosa el
# trazo, que de origen mide ~1% del lienzo y a este tamaño se ve pálido al lado
# de los otros. Las dos cosas están pedidas en origen
# (docs/iconografia-topp-create.md); esto es el apaño mientras llegan.
DILATAR_TRAZO = 5

DIR_DEJAVU = Path("/usr/share/fonts/truetype/dejavu")

PESOS = {"light": 300, "regular": 400, "medium": 500, "semibold": 600, "bold": 700}


def hex_a_rgb(color_hex):
    """#rrggbb → (r, g, b).

    El manifiesto ya normaliza todo a seis dígitos, pero esto acepta también la
    forma corta y descarta el alfa en vez de reventar: antes un "#fff"
    —perfectamente válido en CSS y aceptado por el build— lanzaba un ValueError
    a mitad de la corrida y las personas que venían después se quedaban sin QR.
    """
    texto = str(color_hex).lstrip("#")
    if len(texto) in (3, 4):
        texto = "".join(c * 2 for c in texto)
    if len(texto) < 6:
        raise ValueError(f"color hex no reconocido: {color_hex!r}")
    return tuple(int(texto[i : i + 2], 16) for i in (0, 2, 4))


def fuente(peso, tamano):
    """peso: 'bold' | 'semibold' | 'medium' | 'regular' | 'light'."""
    # 1) La tipografía de la marca. Si es variable, un solo archivo cubre todos
    # los pesos; si es estática, set_variation_by_axes falla y se usa tal cual
    # (el peso lo dará la variante que la marca haya puesto en el archivo).
    if FUENTE_MARCA and FUENTE_MARCA.exists():
        fnt = ImageFont.truetype(str(FUENTE_MARCA), tamano)
        try:
            fnt.set_variation_by_axes([PESOS[peso]])
        except OSError:
            pass
        return fnt

    # 2) Sin fuente de marca: DejaVu Sans, que viene preinstalada. No es la
    # tipografía corporativa, pero mantiene la legibilidad de la pieza.
    nombre_dejavu = "DejaVuSans-Bold.ttf" if peso in ("bold", "semibold") else "DejaVuSans.ttf"
    ruta_dejavu = DIR_DEJAVU / nombre_dejavu
    if ruta_dejavu.exists():
        return ImageFont.truetype(str(ruta_dejavu), tamano)
    return ImageFont.load_default()


def ancho_espaciado(draw, texto, fnt, espaciado):
    if not texto:
        return 0
    return draw.textlength(texto, font=fnt) + espaciado * (len(texto) - 1)


def texto_centrado(draw, y, texto, fnt, fill):
    draw.text(((WIDTH - draw.textlength(texto, font=fnt)) / 2, y), texto, font=fnt, fill=fill)


def texto_espaciado(draw, xy, texto, fnt, fill, espaciado):
    """Dibuja con tracking (letter-spacing). PIL no lo soporta, así que se va
    carácter por carácter — necesario para los títulos y etiquetas en versalitas."""
    x, y = xy
    for caracter in texto:
        draw.text((x, y), caracter, font=fnt, fill=fill)
        x += draw.textlength(caracter, font=fnt) + espaciado
    return x


def envolver_texto(draw, texto, fnt, ancho_max):
    palabras = texto.split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if draw.textlength(prueba, font=fnt) <= ancho_max:
            actual = prueba
            continue
        if actual:
            lineas.append(actual)
            actual = ""
        if draw.textlength(palabra, font=fnt) <= ancho_max:
            actual = palabra
            continue
        # Palabra sin espacios más ancha que la columna (típico en emails largos):
        # se parte por caracteres para que no se desborde ni se superponga.
        fragmento = ""
        for caracter in palabra:
            prueba_caracter = fragmento + caracter
            if draw.textlength(prueba_caracter, font=fnt) <= ancho_max:
                fragmento = prueba_caracter
            else:
                lineas.append(fragmento)
                fragmento = caracter
        actual = fragmento
    if actual:
        lineas.append(actual)
    return lineas


def dibujar_cabecera(img, draw, paleta, logo_path, marca):
    """Cabecera: cuña con corte diagonal simple y, encima, el bloque con corte
    en chevron. Las proporciones son las mismas del CSS (0.9 / 0.25 / 0.52 de la
    profundidad total)."""
    draw.polygon(
        [
            (0, 0),
            (WIDTH, 0),
            (WIDTH, CABECERA_BASE - CORTE_PROF * 0.9),
            (0, CABECERA_BASE),
        ],
        fill=paleta["cuna"],
    )
    draw.polygon(
        [
            (0, 0),
            (WIDTH, 0),
            (WIDTH, CABECERA_BASE - CORTE_PROF),
            (CORTE_VERTICE_X, CABECERA_BASE - CORTE_PROF * 0.25),
            (0, CABECERA_BASE - CORTE_PROF * 0.52),
        ],
        fill=paleta["bloque"],
    )

    y_fin_logo = LOGO_TOP + LOGO_MAX_H
    if logo_path and logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        escala = min(LOGO_MAX_W / logo.width, LOGO_MAX_H / logo.height, 1)
        logo = logo.resize((max(1, int(logo.width * escala)), max(1, int(logo.height * escala))), Image.LANCZOS)
        x = (WIDTH - logo.width) // 2
        y = LOGO_TOP + (LOGO_MAX_H - logo.height) // 2
        img.paste(logo, (x, y), logo)
        y_fin_logo = y + logo.height
    else:
        fnt = fuente("semibold", 46)
        texto = marca.get("nombre", "").upper()
        ancho = ancho_espaciado(draw, texto, fnt, 8)
        texto_espaciado(draw, ((WIDTH - ancho) / 2, LOGO_TOP + 60), texto, fnt, paleta["sobre_bloque"], 8)
        y_fin_logo = LOGO_TOP + 120

    tagline = marca.get("tagline")
    if tagline:
        # Palabras en crema y separadores en olivo, como el arte original: se
        # dibujan por tramos alternando el color.
        partes = tagline if isinstance(tagline, list) else [tagline]
        fnt = fuente("medium", 24)
        separador = "  •  "
        tramos = []
        for indice, parte in enumerate(partes):
            if indice:
                tramos.append((separador, paleta["linea_suave"]))
            tramos.append((parte.upper(), paleta["sobre_bloque"]))

        ancho_total = sum(ancho_espaciado(draw, texto, fnt, 5) + 5 for texto, _ in tramos) - 5
        x = (WIDTH - ancho_total) / 2
        for texto, color in tramos:
            x = texto_espaciado(draw, (x, y_fin_logo + TAGLINE_GAP), texto, fnt, color, 5)


def dibujar_fondo_plano(img, plano, y_top, y_fin):
    """Plano arquitectónico de fondo sobre la zona crema, muy tenue — el mismo
    que usa la tarjeta web (lo genera scripts/generar_planos.py)."""
    if not plano or not plano.exists():
        return
    alto_zona = y_fin - y_top
    dibujo = Image.open(plano).convert("RGBA")
    # Se ajusta al ancho y se repite en vertical, igual que en el CSS: escalado
    # para cubrir dejaría el trazo demasiado grueso frente al texto.
    escala = WIDTH / dibujo.width
    dibujo = dibujo.resize((WIDTH, max(1, int(dibujo.height * escala))), Image.LANCZOS)
    dibujo.putalpha(dibujo.getchannel("A").point(lambda v: int(v * 0.05)))

    franja = Image.new("RGBA", (WIDTH, alto_zona), (0, 0, 0, 0))
    for desplazamiento in range(0, alto_zona, dibujo.height):
        franja.alpha_composite(dibujo, (0, desplazamiento))
    img.alpha_composite(franja, (0, y_top))


def dibujar_identidad(draw, y, paleta, persona):
    """Nombre a dos líneas y centrado — pila en carbón, apellidos en olivo."""
    partes = str(persona.get("nombre", "")).split()
    pila = persona.get("nombre_pila") or (" ".join(partes[:2]) if len(partes) > 2 else (partes[0] if partes else ""))
    apellidos = persona.get("apellidos") or (" ".join(partes[2:]) if len(partes) > 2 else " ".join(partes[1:]))

    # Una sola línea: se centra el conjunto y se pinta cada mitad de su color.
    fnt = fuente("bold", 60)
    separacion = draw.textlength(" ", font=fnt)
    ancho_pila = draw.textlength(pila, font=fnt)
    ancho_apellidos = draw.textlength(apellidos, font=fnt)
    x = (WIDTH - (ancho_pila + separacion + ancho_apellidos)) / 2
    draw.text((x, y), pila, font=fnt, fill=paleta["texto"])
    if apellidos:
        draw.text((x + ancho_pila + separacion, y), apellidos, font=fnt, fill=paleta["realce"])
    y += NOMBRE_INTERLINEA - 4

    # Cargo y profesión en la misma línea, separados por una barra en olivo claro.
    # Se dibuja por tramos porque cada uno lleva su color (PIL pinta de un color
    # por llamada); si no hay profesión, es un solo tramo y no aparece la barra.
    partes = [p for p in (persona.get("cargo"), persona.get("profesion")) if p]
    if partes:
        fnt_cargo = fuente("medium", 36)
        tramos = []
        for i, parte in enumerate(partes):
            if i:
                tramos.append(("  |  ", paleta["linea_suave"]))
            tramos.append((parte, paleta["texto_secundario"]))
        ancho_total = sum(draw.textlength(t, font=fnt_cargo) for t, _ in tramos)
        y += GAP_NOMBRE_CARGO
        x = (WIDTH - ancho_total) / 2
        for texto, color in tramos:
            draw.text((x, y), texto, font=fnt_cargo, fill=color)
            x += draw.textlength(texto, font=fnt_cargo)
        y += 44

    # Regla corta en olivo bajo el cargo, igual que en la tarjeta web.
    y += GAP_CARGO_REGLA
    draw.line([(WIDTH / 2 - 59, y), (WIDTH / 2 + 59, y)], fill=paleta["linea"], width=5)
    return y


# ── Iconos ───────────────────────────────────────────────────────────────────
# Se dibujan con primitivas porque PIL no rasteriza los SVG de la tarjeta web.
# Son los mismos motivos, simplificados a lo que se lee bien a ~60px.

def icono_whatsapp(draw, cx, cy, r, color, grosor):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=grosor)
    # Cola de la burbuja, saliendo hacia abajo a la izquierda.
    draw.polygon(
        [(cx - r * 0.60, cy + r * 0.60), (cx - r * 1.12, cy + r * 1.12), (cx - r * 0.22, cy + r * 0.92)],
        fill=color,
    )
    # Auricular: arco en "U" con los extremos redondeados. Hacia arriba se leía
    # como una sonrisa y no como un teléfono.
    caja = [cx - r * 0.50, cy - r * 0.50, cx + r * 0.50, cy + r * 0.50]
    draw.arc(caja, 25, 155, fill=color, width=max(2, int(grosor * 1.4)))
    for angulo in (25, 155):
        ex = cx + r * 0.50 * math.cos(math.radians(angulo))
        ey = cy + r * 0.50 * math.sin(math.radians(angulo))
        radio = grosor * 0.85
        draw.ellipse([ex - radio, ey - radio, ex + radio, ey + radio], fill=color)


def icono_correo(draw, cx, cy, r, color, grosor):
    x0, y0, x1, y1 = cx - r, cy - r * 0.72, cx + r, cy + r * 0.72
    draw.rectangle([x0, y0, x1, y1], outline=color, width=grosor)
    draw.line([(x0, y0), (cx, cy + r * 0.12), (x1, y0)], fill=color, width=grosor, joint="curve")


def icono_ubicacion(draw, cx, cy, r, color, grosor):
    cabeza = cy - r * 0.28
    radio = r * 0.66
    draw.arc([cx - radio, cabeza - radio, cx + radio, cabeza + radio], 145, 35, fill=color, width=grosor)
    for signo in (-1, 1):
        borde = cx + signo * radio * math.cos(math.radians(35))
        draw.line(
            [(borde, cabeza + radio * math.sin(math.radians(35))), (cx, cy + r * 0.92)],
            fill=color, width=grosor,
        )
    interior = r * 0.24
    draw.ellipse([cx - interior, cabeza - interior, cx + interior, cabeza + interior],
                 outline=color, width=max(1, grosor - 1))


def icono_web(draw, cx, cy, r, color, grosor):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=grosor)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=color, width=max(1, grosor - 1))
    draw.ellipse([cx - r * 0.46, cy - r, cx + r * 0.46, cy + r], outline=color, width=max(1, grosor - 1))


def icono_instagram(draw, cx, cy, r, color, grosor):
    draw.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r * 0.34,
                           outline=color, width=grosor)
    interior = r * 0.46
    draw.ellipse([cx - interior, cy - interior, cx + interior, cy + interior],
                 outline=color, width=grosor)
    punto = r * 0.11
    draw.ellipse([cx + r * 0.52 - punto, cy - r * 0.52 - punto,
                  cx + r * 0.52 + punto, cy - r * 0.52 + punto], fill=color)


def icono_linkedin(draw, cx, cy, r, color, grosor):
    fnt = fuente("bold", int(r * 1.5))
    texto = "in"
    ancho = draw.textlength(texto, font=fnt)
    draw.text((cx - ancho / 2, cy - r * 0.86), texto, font=fnt, fill=color)


ICONOS = {
    "whatsapp": icono_whatsapp,
    "correo": icono_correo,
    "ubicacion": icono_ubicacion,
    "web": icono_web,
    "instagram": icono_instagram,
    "linkedin": icono_linkedin,
}


def icono_de_marca(ruta, lado, color):
    """Prepara un icono de la marca para pegarlo dentro de un badge."""
    im = Image.open(ruta).convert("RGBA")
    im = im.crop(im.getbbox())
    alfa = im.getchannel("A").filter(ImageFilter.MaxFilter(DILATAR_TRAZO))
    tinte = Image.new("RGBA", im.size, tuple(color) + (255,))
    tinte.putalpha(alfa)
    escala = lado / max(tinte.size)
    return tinte.resize(
        (max(1, round(tinte.width * escala)), max(1, round(tinte.height * escala))), Image.LANCZOS
    )


def badge_relleno(img, draw, cx, cy, radio, paleta, icono):
    """Círculo relleno con el icono encima: el mismo badge de la tarjeta web."""
    draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio], fill=paleta["superficie"])
    ruta = ICONOS_MARCA.get(icono)
    if ruta:
        # Al mismo ancho que los dibujados por código (2 * radio * 0.52), para
        # que la columna de badges no quede despareja.
        ico = icono_de_marca(ruta, round(2 * radio * 0.52), paleta["sobre_superficie"])
        img.alpha_composite(ico, (round(cx) - ico.width // 2, round(cy) - ico.height // 2))
    else:
        ICONOS[icono](draw, cx, cy, radio * 0.52, paleta["sobre_superficie"], 3)


def badge_contorno(draw, cx, cy, radio, paleta, icono):
    """Círculo contorneado, como los de la fila de redes en la tarjeta web."""
    draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio],
                 outline=paleta["linea"], width=2)
    ICONOS[icono](draw, cx, cy, radio * 0.50, paleta["texto_suave"], 3)


def dibujar_seccion(img, draw, y, paleta, titulo, filas):
    """Sección con el mismo armado de la tarjeta web: título en versalitas con la
    regla fina a su derecha, y cada dato con su badge circular, etiqueta y valor."""
    fnt_titulo = fuente("semibold", 24)
    fin_titulo = texto_espaciado(draw, (MARGEN_X, y), titulo.upper(), fnt_titulo, paleta["texto_suave"], 6)
    medio = y + 16
    draw.line([(fin_titulo + 18, medio), (MARGEN_X + ANCHO_UTIL, medio)], fill=paleta["linea"], width=1)
    y += GAP_TITULO_REGLA + 8

    fnt_etiqueta = fuente("semibold", 22)
    fnt_valor = fuente("regular", 30)
    texto_x = MARGEN_X + 2 * BADGE_RADIO + GAP_BADGE_TEXTO
    ancho_texto = MARGEN_X + ANCHO_UTIL - texto_x

    visibles = [f for f in filas if f[2]]
    for indice_fila, (icono, etiqueta, valor) in enumerate(visibles):
        y_inicio = y
        draw.text((texto_x, y), etiqueta, font=fnt_etiqueta, fill=paleta["texto_suave"])
        y += ALTO_ETIQUETA

        # Los valores ya pre-partidos en líneas cortas (la dirección) se dibujan
        # tal cual; el resto se envuelve automáticamente por ancho.
        lineas = valor if isinstance(valor, list) else envolver_texto(draw, valor, fnt_valor, ancho_texto)
        for indice, linea in enumerate(lineas):
            draw.text((texto_x, y), linea, font=fnt_valor, fill=paleta["texto"])
            y += ALTO_VALOR if indice == 0 and len(lineas) == 1 else ALTO_LINEA_DIRECCION

        badge_relleno(img, draw, MARGEN_X + BADGE_RADIO, (y_inicio + y) / 2 - 4, BADGE_RADIO, paleta, icono)

        # Línea fina de separación, arrancando después del badge como en la web.
        if indice_fila < len(visibles) - 1:
            y += GAP_ENTRE_FILAS // 2
            draw.line([(texto_x, y), (MARGEN_X + ANCHO_UTIL, y)], fill=paleta["linea_suave"], width=1)
            y += GAP_ENTRE_FILAS // 2
        else:
            y += GAP_ENTRE_FILAS
    return y


QR_BOX = 10


# Corrección de errores. Q recupera el 25% del código, de sobra para el emblema
# del centro, que tapa cerca del 10% del área. Se bajó desde H (30%) porque H
# obligaba a 53 módulos: al ver la imagen completa en un monitor, cada módulo
# quedaba en 2px y la cámara del teléfono no alcanzaba a resolverlos. Menos
# corrección = menos módulos = módulos más grandes, que es lo que se necesita
# para escanear desde una pantalla.
QR_CORRECCION = qrcode.constants.ERROR_CORRECT_Q


def version_qr(datos):
    """Versión (tamaño en módulos) que le toca a este contenido por sí solo."""
    qr = qrcode.QRCode(error_correction=QR_CORRECCION, box_size=QR_BOX, border=2)
    qr.add_data(datos)
    qr.make(fit=True)
    return qr.version


def generar_qr(datos, color_fill, color_back, emblema=None, objetivo=None, version=None):
    """QR con corrección de errores suficiente para incrustar el emblema al
    centro sin perder legibilidad (así lo muestra el arte aprobado).

    Si se pide un tamaño objetivo, se escala a un múltiplo exacto del número de
    módulos y con vecino más cercano. Interpolando, los bordes de módulo quedan
    difusos y la cámara deja de leer el código apenas la imagen se ve pequeña —
    era el caso del QR del vCard, que por ser una URL más larga tiene más módulos.
    """
    qr = qrcode.QRCode(
        version=version, error_correction=QR_CORRECCION, box_size=QR_BOX, border=2
    )
    qr.add_data(datos)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color_fill, back_color=color_back).convert("RGB")

    if objetivo:
        modulos = img.width // QR_BOX
        escala = max(1, round(objetivo / modulos))
        img = img.resize((modulos * escala, modulos * escala), Image.NEAREST)

    # El emblema se pega después de escalar, para que no se le apliquen los
    # dientes de sierra del vecino más cercano.
    if emblema and emblema.exists():
        lado = img.width
        caja = int(lado * 0.24)
        logo = Image.open(emblema).convert("RGBA")
        # El archivo del emblema trae mucho margen transparente alrededor: sin
        # recortarlo, la marca queda diminuta dentro del hueco blanco del QR.
        recorte = logo.getbbox()
        if recorte:
            logo = logo.crop(recorte)
        # Viene en gris claro; se retiñe al color del QR para que se lea con
        # fuerza dentro del código y no parezca una mancha.
        tinte = Image.new("RGBA", logo.size, (*color_fill, 255))
        tinte.putalpha(logo.getchannel("A"))
        logo = tinte
        escala = min(caja / logo.width, caja / logo.height)
        logo = logo.resize((max(1, int(logo.width * escala)), max(1, int(logo.height * escala))), Image.LANCZOS)
        pad = int(lado * 0.035)
        hueco = max(logo.width, logo.height) + 2 * pad
        fondo = Image.new("RGB", (hueco, hueco), color_back)
        fondo.paste(logo, ((hueco - logo.width) // 2, (hueco - logo.height) // 2), logo)
        img.paste(fondo, ((lado - fondo.width) // 2, (lado - fondo.height) // 2))
    return img


def igualar_qr(codigos, color_back):
    """Deja todos los QR del mismo lado, centrándolos sobre un lienzo del color de
    fondo del código.

    Cada QR se escala a un múltiplo exacto de sus módulos, y como dos códigos con
    distinta cantidad de datos tienen distinta cantidad de módulos, terminan con
    anchos distintos: puestos en marcos iguales, uno se ve con más borde que el
    otro. Se iguala agrandando la zona de silencio del más pequeño —blanco de
    más, que no estorba la lectura— en vez de reescalar, que emborronaría los
    módulos."""
    lado = max(qr.width for qr in codigos)
    iguales = []
    for qr in codigos:
        if qr.width == lado:
            iguales.append(qr)
            continue
        lienzo = Image.new("RGB", (lado, lado), color_back)
        lienzo.paste(qr, ((lado - qr.width) // 2, (lado - qr.height) // 2))
        iguales.append(lienzo)
    return iguales


def dibujar_qr_enmarcado(img, draw, x, y, qr, paleta, lado_marco):
    """Marco carbón redondeado con el QR centrado. El QR ya viene al tamaño
    exacto que le tocó al escalar por módulos, así que se centra en el marco en
    vez de forzarlo a una medida fija."""
    draw.rounded_rectangle(
        [x, y, x + lado_marco, y + lado_marco], radius=QR_MARCO_RADIO, fill=paleta["marco_qr"]
    )
    desfase = (lado_marco - qr.width) // 2
    img.paste(qr, (x + desfase, y + desfase))


def generar_tarjeta_whatsapp(persona, marca, paleta, logo_claro, emblema, plano, url_publica, salida):
    # RGBA porque la marca de agua se compone con transparencia; al guardar se
    # aplana a RGB.
    img = Image.new("RGBA", (WIDTH, HEIGHT), paleta["lienzo"] + (255,))
    draw = ImageDraw.Draw(img)

    dibujar_cabecera(img, draw, paleta, logo_claro, marca)
    dibujar_fondo_plano(img, plano, CABECERA_BASE - 34, HEIGHT - PIE_ALTO)

    y = dibujar_identidad(draw, NOMBRE_TOP, paleta, persona)
    y += GAP_REGLA_SECCION

    direccion = marca.get("direccion")
    direccion_lineas = direccion if isinstance(direccion, list) else ([direccion] if direccion else [])

    # Un solo bloque, igual que la tarjeta web: son todos canales de trabajo. Los
    # dos correos se distinguen por la etiqueta y no por un título de sección, y
    # el calificador solo aparece si de verdad hay dos que separar.
    dos_correos = bool(persona.get("email")) and bool(marca.get("email"))
    dos_whatsapp = bool(persona.get("telefono_display")) and bool(marca.get("telefono_display"))
    y = dibujar_seccion(
        img, draw, y, paleta, "Empresa",
        [
            # dibujar_seccion descarta las filas sin valor: lo que la persona no
            # publica, simplemente no aparece.
            ("whatsapp", "WhatsApp empresarial" if dos_whatsapp else "WhatsApp",
             marca.get("telefono_display")),
            ("whatsapp", "WhatsApp profesional" if dos_whatsapp else "WhatsApp",
             persona.get("telefono_display")),
            ("correo", "Correo profesional" if dos_correos else "Correo", persona.get("email")),
            ("correo", "Correo empresarial" if dos_correos else "Correo", marca.get("email")),
            ("ubicacion", "Oficina", direccion_lineas),
        ],
    )
    y += GAP_SECCION_REDES

    # Fila de enlaces (sitio web · instagram · linkedin), igual que en la tarjeta web.
    # En LinkedIn se muestra el nombre del perfil y no la URL: la que tiene Daniel
    # es la autogenerada (in/daniel-j-manotas-a83a105b), imposible de teclear bien
    # desde una imagen. El enlace real vive en el vCard y en la tarjeta web.
    sitio_web_display = (marca.get("sitio_web") or "").replace("https://", "").replace("http://", "").rstrip("/")
    instagram = persona.get("instagram") or marca.get("instagram") or ""
    linkedin = persona.get("linkedin") or marca.get("linkedin") or ""
    linkedin_display = persona.get("linkedin_display") or persona.get("nombre") or ""
    partes = [
        p
        for p in [
            sitio_web_display,
            f"@{instagram}" if instagram else "",
            f"in/{linkedin_display}" if linkedin else "",
        ]
        if p
    ]
    redes = [
        ("web", sitio_web_display),
        ("instagram", f"@{instagram}" if instagram else ""),
        ("linkedin", linkedin_display if linkedin else ""),
    ]
    redes = [r for r in redes if r[1]]
    if redes:
        fnt = fuente("medium", 27)
        columna = ANCHO_UTIL / len(redes)
        for indice, (icono, etiqueta) in enumerate(redes):
            cx = MARGEN_X + columna * (indice + 0.5)
            badge_contorno(draw, cx, y + BADGE_RED_RADIO, BADGE_RED_RADIO, paleta, icono)
            ancho = draw.textlength(etiqueta, font=fnt)
            draw.text((cx - ancho / 2, y + 2 * BADGE_RED_RADIO + 14), etiqueta, font=fnt,
                      fill=paleta["texto_secundario"])
        y += 2 * BADGE_RED_RADIO + 52

    # Dos QR al final: uno para guardar el contacto, otro para abrir la tarjeta
    # digital. (A diferencia de la tarjeta web, aquí nada es clicable — cada QR
    # reemplaza la acción que en la web sería un elemento interactivo.)
    #
    # El segundo QR llevaba el sitio web, que ya está en texto plano arriba. El de
    # la tarjeta va sin emblema al centro: es el que más se escanea y el logo, aun
    # con corrección de errores alta, le quita módulos legibles.
    #
    # Van pegados a los márgenes y con un separador en medio: si quedan juntos, la
    # cámara los toma dentro del mismo encuadre y no se sabe cuál va a leer.
    qr_top = y + GAP_REDES_QR
    datos_contacto = f"{url_publica.rstrip('/')}/contacto.vcf"

    # Los dos se fuerzan a la misma versión de QR — la que necesita el más largo
    # de los dos, el del vCard. Con distinta versión tienen distinta cantidad de
    # módulos y, como cada uno se escala a un múltiplo entero de los suyos, el
    # más corto terminaba bastante más pequeño y rodeado de blanco. A misma
    # versión, mismos módulos, mismo escalado y misma medida exacta. La URL corta
    # simplemente viaja con más relleno, que no afecta la lectura.
    version = max(version_qr(datos_contacto), version_qr(url_publica))

    qr_contacto = generar_qr(
        datos_contacto, paleta["qr_modulo"], paleta["qr_fondo"], emblema, QR_TAMANO, version
    )
    qr_tarjeta = generar_qr(url_publica, paleta["qr_modulo"], paleta["qr_fondo"], None, QR_TAMANO, version)

    # Red de seguridad por si alguna vez vuelven a diferir (otro contenido, otra
    # marca): antes de enmarcarlos se igualan los lados.
    qr_contacto, qr_tarjeta = igualar_qr([qr_contacto, qr_tarjeta], paleta["qr_fondo"])

    lado_marco = qr_contacto.width + 2 * QR_MARCO_PAD
    # Tres huecos iguales: costado, centro, costado.
    hueco = (WIDTH - 2 * lado_marco) / 3
    x_izq = int(hueco)
    x_der = int(2 * hueco + lado_marco)

    dibujar_qr_enmarcado(img, draw, x_izq, qr_top, qr_contacto, paleta, lado_marco)
    dibujar_qr_enmarcado(img, draw, x_der, qr_top, qr_tarjeta, paleta, lado_marco)

    fnt_caption = fuente("medium", 26)
    caption_y = qr_top + lado_marco + 22
    for x, texto in ((x_izq, "GUARDAR CONTACTO"), (x_der, "TARJETA DIGITAL")):
        ancho = ancho_espaciado(draw, texto, fnt_caption, 3)
        texto_espaciado(draw, (x + (lado_marco - ancho) / 2, caption_y), texto, fnt_caption, paleta["texto_secundario"], 3)

    # Separador vertical entre los dos QR, para reforzar que son dos acciones.
    x_centro = WIDTH // 2
    draw.line(
        [(x_centro, qr_top + 30), (x_centro, qr_top + lado_marco - 30)],
        fill=paleta["linea_suave"],
        width=2,
    )

    # Pie olivo con el sitio web, igual que en la tarjeta web.
    pie_top = HEIGHT - PIE_ALTO
    draw.rectangle([0, pie_top, WIDTH, HEIGHT], fill=paleta["pie"])
    if sitio_web_display:
        fnt_pie = fuente("medium", 26)
        texto_pie = sitio_web_display.upper()
        ancho_pie = ancho_espaciado(draw, texto_pie, fnt_pie, 9)
        texto_espaciado(
            draw,
            ((WIDTH - ancho_pie) / 2, pie_top + (PIE_ALTO - 30) / 2),
            texto_pie,
            fnt_pie,
            paleta["sobre_pie"],
            9,
        )

    fin_contenido = caption_y + 40
    if fin_contenido > pie_top:
        print(f"    ⚠ el contenido ({fin_contenido}px) invade el pie ({pie_top}px)")

    img.convert("RGB").save(salida)


def paleta_de(ficha):
    """Paleta de arte del manifiesto, ya validada y sin canal alfa."""
    valores = dict(ARTE_RESPALDO)
    valores.update({k: v for k, v in (ficha.get("arte") or {}).items() if v})
    return {rol: hex_a_rgb(valor) for rol, valor in valores.items()}


def resolver_asset(assets, dist_assets, clave):
    """Ubica un asset declarado en el manifiesto.

    Los nombres ya los comprobó build.mjs contra la carpeta de la marca, pero
    esta función vuelve a exigir que la ruta resuelta cuelgue de la carpeta en
    la que se la buscó: es la última barrera antes de abrir un archivo del disco
    y meterlo en una pieza que se publica. Se comprueba contra cada base por
    separado y no contra la raíz del repo, porque con `build.mjs --out` la
    salida puede estar fuera del árbol —así se sacan las maquetas—.
    """
    nombre = assets.get(clave)
    if not nombre:
        return None
    for carpeta in (dist_assets, ROOT / assets["dir"]):
        base = carpeta.resolve()
        ruta = (base / nombre).resolve()
        if not ruta.is_relative_to(base):
            print(f"⚠ {clave}: {nombre!r} se sale de {base}, se ignora.")
            return None
        if ruta.exists():
            return ruta
    return None


def main():
    if not MANIFIESTO.exists():
        print(
            f"✗ falta {MANIFIESTO.relative_to(ROOT)}.\n"
            "  Corre antes: node scripts/build.mjs"
        )
        return 1

    manifiesto = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    if manifiesto.get("version") != 1:
        print(f"✗ manifiesto en versión {manifiesto.get('version')!r}; este script espera la 1.")
        return 1

    # El manifiesto guarda su dist relativo a sí mismo.
    dist_dir = (MANIFIESTO.parent / manifiesto["dist"]).resolve()

    for ficha in manifiesto["personas"]:
        slug = ficha["slug"]
        out_dir = dist_dir / slug
        if not out_dir.exists():
            print(f"⚠ {slug}: no existe {out_dir.relative_to(ROOT)}/ — corre antes node scripts/build.mjs.")
            continue

        persona, marca = ficha["persona"], ficha["marca"]
        paleta = paleta_de(ficha)

        # Misma tipografía que la tarjeta web, para que la imagen y la página no
        # se vean de dos marcas distintas.
        global FUENTE_MARCA, ICONOS_MARCA
        ruta_fuente = ficha["assets"].get("fuente")
        FUENTE_MARCA = (ROOT / ruta_fuente) if ruta_fuente else None
        if FUENTE_MARCA and not FUENTE_MARCA.is_relative_to(ROOT):
            print(f"⚠ {slug}: la fuente queda fuera del repo, se ignora.")
            FUENTE_MARCA = None

        ICONOS_MARCA = {}
        for rol, relativa in (ficha["assets"].get("iconos") or {}).items():
            ruta = (ROOT / relativa).resolve()
            if ruta.is_relative_to(ROOT) and ruta.exists():
                ICONOS_MARCA[rol] = ruta
            else:
                print(f"⚠ {slug}: el icono {rol} no aparece en {relativa}, se dibuja el genérico.")

        # El logo claro (sobre el bloque carbón) va en dist/{slug}/assets/ porque
        # la web también lo usa; el emblema (dentro del QR) y el plano en PNG
        # solo los usa esta imagen, así que se leen de la carpeta de la marca.
        assets, dist_assets = ficha["assets"], out_dir / "assets"
        logo_claro = resolver_asset(assets, dist_assets, "logo_claro") or resolver_asset(
            assets, dist_assets, "logo"
        )
        emblema = resolver_asset(assets, dist_assets, "logo_emblema")
        # La web usa el SVG y esta imagen el PNG: PIL no rasteriza SVG.
        plano = resolver_asset(assets, dist_assets, "fondo_plano_png")

        # La URL la calculó el build a partir de base_url + slug. La ficha no
        # puede influir en ella: es lo que se graba en el QR impreso.
        url = ficha["url_publica"]

        # Sin emblema al centro: es el QR que se imprime y el que más se escanea,
        # y el logo tapa módulos. El de la vCard sí lo lleva (ver más abajo).
        generar_qr(url, paleta["qr_modulo"], paleta["qr_fondo"], None, 600).save(out_dir / "qr.png")

        generar_tarjeta_whatsapp(
            persona, marca, paleta, logo_claro, emblema, plano, url,
            out_dir / "tarjeta-whatsapp.png",
        )

        print(f"• {slug}: dist/{slug}/qr.png -> {url}")
        print(f"           dist/{slug}/tarjeta-whatsapp.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
