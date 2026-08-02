#!/usr/bin/env python3
"""Genera QR + imagen para WhatsApp para cada persona, a partir de dist/{slug}/
   (que ya debe existir — correr primero `node scripts/build.mjs`).

   La imagen sigue el mismo arte del tema v2: cuña olivo con corte diagonal y,
   encima, bloque carbón cortado en chevron; cuerpo en crema con la jerarquía
   Personal / Empresa y pie olivo."""

import json
import math
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DIST_DIR = ROOT / "dist"

# Paleta por defecto (TOPP CREATE); marcas.json la sobreescribe por marca.
COLORES = {
    "oscuro": "#4D4D4D",
    "claro": "#B3B3B3",
    "fondo": "#FFFFFF",
    "carbon": "#24292D",
    "olivo": "#83855B",
    "olivo_texto": "#6B6C47",
    "olivo_claro": "#A8AA7C",
    "crema": "#F4F1EC",
}

WIDTH, HEIGHT = 1080, 2000
MARGEN_X = 96
ANCHO_UTIL = WIDTH - 2 * MARGEN_X

# Cabecera: mismas proporciones que el CSS del tema v2. El olivo lleva un corte
# diagonal simple y el carbón que va encima lleva un corte en chevron con el
# vértice al 20% del ancho — por eso la franja olivo es delgada a la derecha y
# una cuña ancha a la izquierda.
CORTE_PROF = int(WIDTH * 0.30)   # profundidad total (punta izquierda del olivo)
CORTE_VERTICE_X = int(WIDTH * 0.20)
CABECERA_BASE = 560              # y donde termina la cuña olivo (borde izquierdo)

LOGO_TOP = 60
LOGO_MAX_W = 400
LOGO_MAX_H = 162
TAGLINE_GAP = 30

NOMBRE_TOP = 600
NOMBRE_INTERLINEA = 74
GAP_NOMBRE_CARGO = 20
GAP_CARGO_REGLA = 18
GAP_REGLA_SECCION = 34

GAP_TITULO_REGLA = 32
GAP_REGLA_FILA = 26
ALTO_ETIQUETA = 28
ALTO_VALOR = 42
GAP_ENTRE_FILAS = 22
ALTO_LINEA_DIRECCION = 38
GAP_ENTRE_SECCIONES = 26
GAP_SECCION_REDES = 20
GAP_REDES_QR = 22

BADGE_RADIO = 30
GAP_BADGE_TEXTO = 26
BADGE_RED_RADIO = 34

QR_TAMANO = 200
QR_MARCO_PAD = 18
QR_MARCO_RADIO = 24
QR_GAP = 48

PIE_ALTO = 92

# Directorios donde buscar Montserrat: primero el proyecto, luego el sistema.
DIR_FUENTES_PROYECTO = ROOT / "assets" / "fuentes"
DIR_FUENTES_SISTEMA = Path("/usr/share/fonts")
DIR_DEJAVU = Path("/usr/share/fonts/truetype/dejavu")

PESOS = {"light": 300, "regular": 400, "medium": 500, "semibold": 600, "bold": 700}


def hex_a_rgb(color_hex):
    color_hex = str(color_hex).lstrip("#")
    return tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))


def buscar_fuente(patrones, directorios):
    for directorio in directorios:
        if not directorio.exists():
            continue
        for archivo in directorio.rglob("*.ttf"):
            nombre = archivo.name.lower()
            if any(patron in nombre for patron in patrones):
                return archivo
    return None


def fuente(peso, tamano):
    """peso: 'bold' | 'semibold' | 'medium' | 'regular' | 'light'."""
    # 1) Montserrat variable en el proyecto: un solo .ttf cubre todos los pesos.
    variable = DIR_FUENTES_PROYECTO / "Montserrat-Variable.ttf"
    if variable.exists():
        fnt = ImageFont.truetype(str(variable), tamano)
        fnt.set_variation_by_axes([PESOS[peso]])
        return fnt

    # 2) Instancias estáticas de Montserrat instaladas en el sistema.
    estatica = buscar_fuente(
        [f"montserrat-{peso}", f"montserrat_{peso}"], [DIR_FUENTES_PROYECTO, DIR_FUENTES_SISTEMA]
    )
    if estatica:
        return ImageFont.truetype(str(estatica), tamano)

    # 3) Sin Montserrat: DejaVu Sans, que viene preinstalada. No es la tipografía
    # corporativa, pero mantiene la legibilidad de la pieza.
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
    """Cabecera del arte del roll-up: cuña olivo con corte diagonal simple y,
    encima, el bloque carbón con corte en chevron. Las proporciones son las
    mismas del CSS (0.9 / 0.25 / 0.52 de la profundidad total)."""
    draw.polygon(
        [
            (0, 0),
            (WIDTH, 0),
            (WIDTH, CABECERA_BASE - CORTE_PROF * 0.9),
            (0, CABECERA_BASE),
        ],
        fill=paleta["olivo"],
    )
    draw.polygon(
        [
            (0, 0),
            (WIDTH, 0),
            (WIDTH, CABECERA_BASE - CORTE_PROF),
            (CORTE_VERTICE_X, CABECERA_BASE - CORTE_PROF * 0.25),
            (0, CABECERA_BASE - CORTE_PROF * 0.52),
        ],
        fill=paleta["carbon"],
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
        texto_espaciado(draw, ((WIDTH - ancho) / 2, LOGO_TOP + 60), texto, fnt, paleta["fondo"], 8)
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
                tramos.append((separador, paleta["olivo_claro"]))
            tramos.append((parte.upper(), paleta["crema"]))

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
    draw.text((x, y), pila, font=fnt, fill=paleta["carbon"])
    if apellidos:
        draw.text((x + ancho_pila + separacion, y), apellidos, font=fnt, fill=paleta["olivo"])
    y += NOMBRE_INTERLINEA - 4

    cargo = persona.get("cargo") or ""
    if cargo:
        y += GAP_NOMBRE_CARGO
        texto_centrado(draw, y, cargo, fuente("medium", 36), paleta["oscuro"])
        y += 44

    # Regla corta en olivo bajo el cargo, igual que en la tarjeta web.
    y += GAP_CARGO_REGLA
    draw.line([(WIDTH / 2 - 59, y), (WIDTH / 2 + 59, y)], fill=paleta["olivo"], width=5)
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


def badge_relleno(draw, cx, cy, radio, paleta, icono):
    """Círculo olivo con el icono en crema: el mismo badge de la tarjeta web."""
    draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio], fill=paleta["olivo"])
    ICONOS[icono](draw, cx, cy, radio * 0.52, paleta["crema"], 3)


def badge_contorno(draw, cx, cy, radio, paleta, icono):
    """Círculo contorneado, como los de la fila de redes en la tarjeta web."""
    draw.ellipse([cx - radio, cy - radio, cx + radio, cy + radio],
                 outline=paleta["olivo"], width=2)
    ICONOS[icono](draw, cx, cy, radio * 0.50, paleta["olivo_texto"], 3)


def dibujar_seccion(draw, y, paleta, titulo, filas):
    """Sección con el mismo armado de la tarjeta web: título en versalitas con la
    regla fina a su derecha, y cada dato con su badge circular, etiqueta y valor."""
    fnt_titulo = fuente("semibold", 24)
    fin_titulo = texto_espaciado(draw, (MARGEN_X, y), titulo.upper(), fnt_titulo, paleta["olivo_texto"], 6)
    medio = y + 16
    draw.line([(fin_titulo + 18, medio), (MARGEN_X + ANCHO_UTIL, medio)], fill=paleta["olivo"], width=1)
    y += GAP_TITULO_REGLA + 8

    fnt_etiqueta = fuente("semibold", 22)
    fnt_valor = fuente("regular", 30)
    texto_x = MARGEN_X + 2 * BADGE_RADIO + GAP_BADGE_TEXTO
    ancho_texto = MARGEN_X + ANCHO_UTIL - texto_x

    visibles = [f for f in filas if f[2]]
    for indice_fila, (icono, etiqueta, valor) in enumerate(visibles):
        y_inicio = y
        draw.text((texto_x, y), etiqueta, font=fnt_etiqueta, fill=paleta["olivo_texto"])
        y += ALTO_ETIQUETA

        # Los valores ya pre-partidos en líneas cortas (la dirección) se dibujan
        # tal cual; el resto se envuelve automáticamente por ancho.
        lineas = valor if isinstance(valor, list) else envolver_texto(draw, valor, fnt_valor, ancho_texto)
        for indice, linea in enumerate(lineas):
            draw.text((texto_x, y), linea, font=fnt_valor, fill=paleta["carbon"])
            y += ALTO_VALOR if indice == 0 and len(lineas) == 1 else ALTO_LINEA_DIRECCION

        badge_relleno(draw, MARGEN_X + BADGE_RADIO, (y_inicio + y) / 2 - 4, BADGE_RADIO, paleta, icono)

        # Línea fina de separación, arrancando después del badge como en la web.
        if indice_fila < len(visibles) - 1:
            y += GAP_ENTRE_FILAS // 2
            draw.line([(texto_x, y), (MARGEN_X + ANCHO_UTIL, y)], fill=paleta["olivo_claro"], width=1)
            y += GAP_ENTRE_FILAS // 2
        else:
            y += GAP_ENTRE_FILAS
    return y


QR_BOX = 10


def generar_qr(datos, color_fill, color_back, emblema=None, objetivo=None):
    """QR con corrección alta para poder incrustar el emblema al centro sin
    perder legibilidad (así lo muestra el arte aprobado).

    Si se pide un tamaño objetivo, se escala a un múltiplo exacto del número de
    módulos y con vecino más cercano. Interpolando, los bordes de módulo quedan
    difusos y la cámara deja de leer el código apenas la imagen se ve pequeña —
    era el caso del QR del vCard, que por ser una URL más larga tiene más módulos.
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=QR_BOX, border=2)
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


def dibujar_qr_enmarcado(img, draw, x, y, qr, paleta, lado_marco):
    """Marco carbón redondeado con el QR centrado. El QR ya viene al tamaño
    exacto que le tocó al escalar por módulos, así que se centra en el marco en
    vez de forzarlo a una medida fija."""
    draw.rounded_rectangle(
        [x, y, x + lado_marco, y + lado_marco], radius=QR_MARCO_RADIO, fill=paleta["carbon"]
    )
    desfase = (lado_marco - qr.width) // 2
    img.paste(qr, (x + desfase, y + desfase))


def generar_tarjeta_whatsapp(persona, marca, paleta, logo_claro, emblema, plano, url_publica, salida):
    # RGBA porque la marca de agua se compone con transparencia; al guardar se
    # aplana a RGB.
    img = Image.new("RGBA", (WIDTH, HEIGHT), paleta["crema"] + (255,))
    draw = ImageDraw.Draw(img)

    dibujar_cabecera(img, draw, paleta, logo_claro, marca)
    dibujar_fondo_plano(img, plano, CABECERA_BASE - 34, HEIGHT - PIE_ALTO)

    y = dibujar_identidad(draw, NOMBRE_TOP, paleta, persona)
    y += GAP_REGLA_SECCION

    y = dibujar_seccion(
        draw, y, paleta, "Personal",
        [
            ("whatsapp", "WhatsApp", persona.get("telefono_display")),
            ("correo", "Correo", persona.get("email")),
        ],
    )
    y += GAP_ENTRE_SECCIONES

    direccion = marca.get("direccion")
    direccion_lineas = direccion if isinstance(direccion, list) else ([direccion] if direccion else [])
    y = dibujar_seccion(
        draw, y, paleta, "Empresa",
        [
            ("whatsapp", "WhatsApp", marca.get("telefono_display")),
            ("correo", "Correo", marca.get("email")),
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
                      fill=paleta["oscuro"])
        y += 2 * BADGE_RED_RADIO + 52

    # Dos QR al final: uno para guardar el contacto, otro para el sitio web.
    # (A diferencia de la tarjeta web, aquí nada es clicable — cada QR reemplaza
    # la acción que en la web sería un elemento interactivo.)
    #
    # Van pegados a los márgenes y con un separador en medio: si quedan juntos, la
    # cámara los toma dentro del mismo encuadre y no se sabe cuál va a leer.
    qr_top = y + GAP_REDES_QR
    qr_contacto = generar_qr(
        f"{url_publica.rstrip('/')}/contacto.vcf", paleta["carbon"], paleta["fondo"], emblema, QR_TAMANO
    )
    qr_sitio = generar_qr(
        marca.get("sitio_web") or url_publica, paleta["carbon"], paleta["fondo"], emblema, QR_TAMANO
    )

    # Los dos marcos comparten medida, tomada del QR más grande de los dos.
    lado_marco = max(qr_contacto.width, qr_sitio.width) + 2 * QR_MARCO_PAD
    # Tres huecos iguales: costado, centro, costado.
    hueco = (WIDTH - 2 * lado_marco) / 3
    x_izq = int(hueco)
    x_der = int(2 * hueco + lado_marco)

    dibujar_qr_enmarcado(img, draw, x_izq, qr_top, qr_contacto, paleta, lado_marco)
    dibujar_qr_enmarcado(img, draw, x_der, qr_top, qr_sitio, paleta, lado_marco)

    fnt_caption = fuente("medium", 26)
    caption_y = qr_top + lado_marco + 22
    for x, texto in ((x_izq, "GUARDAR CONTACTO"), (x_der, "SITIO WEB")):
        ancho = ancho_espaciado(draw, texto, fnt_caption, 3)
        texto_espaciado(draw, (x + (lado_marco - ancho) / 2, caption_y), texto, fnt_caption, paleta["oscuro"], 3)

    # Separador vertical entre los dos QR, para reforzar que son dos acciones.
    x_centro = WIDTH // 2
    draw.line(
        [(x_centro, qr_top + 30), (x_centro, qr_top + lado_marco - 30)],
        fill=paleta["olivo_claro"],
        width=2,
    )

    # Pie olivo con el sitio web, igual que en la tarjeta web.
    pie_top = HEIGHT - PIE_ALTO
    draw.rectangle([0, pie_top, WIDTH, HEIGHT], fill=paleta["olivo"])
    if sitio_web_display:
        fnt_pie = fuente("medium", 26)
        texto_pie = sitio_web_display.upper()
        ancho_pie = ancho_espaciado(draw, texto_pie, fnt_pie, 9)
        texto_espaciado(
            draw,
            ((WIDTH - ancho_pie) / 2, pie_top + (PIE_ALTO - 30) / 2),
            texto_pie,
            fnt_pie,
            paleta["fondo"],
            9,
        )

    fin_contenido = caption_y + 40
    if fin_contenido > pie_top:
        print(f"    ⚠ el contenido ({fin_contenido}px) invade el pie ({pie_top}px)")

    img.convert("RGB").save(salida)


def resolver_marca(persona, marcas_por_id):
    if persona.get("marca_id"):
        return marcas_por_id.get(persona["marca_id"])
    return persona.get("marca")


def paleta_de(marca):
    valores = dict(COLORES)
    valores.update({k: v for k, v in (marca.get("colores") or {}).items() if v})
    valores.update({k: v for k, v in (marca.get("colores_secundarios") or {}).items() if v})
    return {clave: hex_a_rgb(valor) for clave, valor in valores.items()}


def url_publica_de(persona, base_url):
    if persona.get("url_publica"):
        return persona["url_publica"]
    return f"{base_url.rstrip('/')}/{persona['slug']}/"


def main():
    marcas = json.loads((DATA_DIR / "marcas.json").read_text(encoding="utf-8"))
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))
    config = json.loads((DATA_DIR / "config.json").read_text(encoding="utf-8"))
    marcas_por_id = {m["id"]: m for m in marcas}
    base_url = config.get("base_url", "")

    for persona in personas:
        marca = resolver_marca(persona, marcas_por_id)
        if not marca:
            print(f"⚠ {persona['slug']}: sin marca resuelta, se omite.")
            continue

        out_dir = DIST_DIR / persona["slug"]
        if not out_dir.exists():
            print(f"⚠ {persona['slug']}: no existe dist/{persona['slug']}/ — corre antes node scripts/build.mjs.")
            continue

        paleta = paleta_de(marca)

        # El logo claro (sobre el bloque carbón) y el emblema (dentro del QR) los
        # copia build.mjs a dist/{slug}/assets/, junto a la marca correspondiente.
        assets_dir = out_dir / "assets"
        marca_dir = ROOT / "assets" / "marcas" / marca.get("id", "")
        def resolver_asset(nombre):
            for carpeta in (assets_dir, marca_dir):
                if nombre and (carpeta / nombre).exists():
                    return carpeta / nombre
            return None

        logo_claro = resolver_asset(marca.get("logo_claro")) or resolver_asset(marca.get("logo"))
        emblema = resolver_asset(marca.get("logo_emblema"))
        # La web usa el SVG y esta imagen el PNG: PIL no rasteriza SVG.
        plano = resolver_asset(marca.get("fondo_plano_png"))

        url = url_publica_de(persona, base_url)

        qr_path = out_dir / "qr.png"
        generar_qr(url, paleta["carbon"], paleta["fondo"], emblema, 600).save(qr_path)

        whatsapp_path = out_dir / "tarjeta-whatsapp.png"
        generar_tarjeta_whatsapp(
            persona, marca, paleta, logo_claro, emblema, plano, url, whatsapp_path
        )

        print(f"• {persona['slug']}: dist/{persona['slug']}/qr.png -> {url}")
        print(f"           dist/{persona['slug']}/tarjeta-whatsapp.png")

    if base_url == "https://tarjetas.toppcreate.com":
        print(
            "\n⚠ data/config.json usa un base_url de ejemplo. "
            "Actualízalo con la URL real de GitHub Pages antes de compartir los QR."
        )


if __name__ == "__main__":
    main()
