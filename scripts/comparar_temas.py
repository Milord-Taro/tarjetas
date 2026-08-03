#!/usr/bin/env python3
"""Pone dos temas lado a lado y mide qué porcentaje de la pieza ocupa cada color.

    python3 scripts/comparar_temas.py            # v2 contra v3
    python3 scripts/comparar_temas.py v1 v3      # cualquier par de templates/
    python3 scripts/comparar_temas.py v2 v3 --abrir

Compila cada tema en un directorio temporal —no toca dist/ ni data/— y compone
una sola imagen con las dos tarjetas y la barra de uso real de la paleta.

Sirve para dos cosas distintas: ver un tema antes de publicarlo, y comprobar si
el reparto de color se parece al que pide el manual de marca. El objetivo del
manual se lee de data/marcas.json cuando la marca lo declara en `uso_paleta`; si
no, se muestra solo lo medido.
"""

import argparse
import collections
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FUENTE = ROOT / "assets" / "fuentes" / "Montserrat-Variable.ttf"

# Colores de la interfaz de la propia lámina (no de la marca).
LAMINA_FONDO = (10, 10, 10)
LAMINA_TEXTO = (245, 242, 235)
LAMINA_SUAVE = (150, 148, 143)
LAMINA_TENUE = (110, 108, 104)
LAMINA_BORDE = (58, 58, 58)

# Cuánto se puede alejar un píxel de un color de la paleta para seguir contando
# como ese color. 30 unidades de distancia euclídea en RGB deja fuera el logo,
# el plano de fondo y los bordes suavizados, que es lo que se quiere.
TOLERANCIA = 30**2


def hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def fuente(peso, tamano):
    if not FUENTE.exists():
        return ImageFont.load_default()
    f = ImageFont.truetype(str(FUENTE), tamano)
    try:
        f.set_variation_by_axes([peso])
    except OSError:
        pass
    return f


def temas_disponibles():
    return sorted(d.name for d in (ROOT / "templates").iterdir() if (d / "card.html").exists())


def compilar(tema, slug, trabajo):
    """Compila un tema en un temporal y devuelve la ruta de su imagen."""
    base = trabajo / tema
    (base / "data").mkdir(parents=True)
    (base / "dist").mkdir(parents=True)
    for nombre in ("marcas.json", "personas.json"):
        shutil.copy(DATA / nombre, base / "data" / nombre)
    config = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
    config["tema"] = tema
    (base / "data" / "config.json").write_text(json.dumps(config), encoding="utf-8")

    for orden in (
        ["node", str(ROOT / "scripts" / "build.mjs"),
         "--data", str(base / "data"), "--out", str(base / "dist")],
        [sys.executable, str(ROOT / "scripts" / "generar_imagenes.py"),
         str(base / "build" / "manifiesto.json")],
    ):
        hecho = subprocess.run(orden, capture_output=True, text=True)
        if hecho.returncode != 0:
            print(hecho.stdout + hecho.stderr)
            raise SystemExit(f"✗ falló al compilar el tema {tema}")

    return base / "dist" / slug / "tarjeta-whatsapp.png"


def medir(ruta, paleta):
    """Reparto de la pieza entre los colores de la paleta, en porcentaje."""
    im = Image.open(ruta).convert("RGB")
    total = im.width * im.height
    cuenta = collections.Counter()
    for n, color in im.getcolors(maxcolors=total):
        mejor, distancia_min = "otros", float("inf")
        for nombre, valor, _ in paleta:
            d = sum((a - b) ** 2 for a, b in zip(color, hex_a_rgb(valor)))
            if d < distancia_min:
                mejor, distancia_min = nombre, d
        cuenta[mejor if distancia_min <= TOLERANCIA else "otros"] += n
    return {clave: 100 * n / total for clave, n in cuenta.items()}


def paleta_de_marca():
    """Colores del manual, con su objetivo de uso si la marca lo declaró."""
    marcas = json.loads((DATA / "marcas.json").read_text(encoding="utf-8"))
    colores = (marcas[0].get("colores") or {}) if marcas else {}
    objetivos = (marcas[0].get("uso_paleta") or {}) if marcas else {}
    etiquetas = {"fondo": "FONDO", "oscuro": "OSCURO", "claro": "CLARO",
                 "apoyo": "APOYO", "acento": "ACENTO"}
    orden = ["fondo", "oscuro", "claro", "apoyo", "acento"]
    return [
        (etiquetas[rol], colores[rol], objetivos.get(rol))
        for rol in orden
        if colores.get(rol)
    ]


def componer(tarjetas, paleta, medido, salida):
    # Ancho fijo por tarjeta, no un factor: la pieza pasó a renderizarse a 2x y
    # con un factor la lámina crecía con ella hasta hacerse incómoda de mirar.
    ANCHO_TARJETA = 454
    original = Image.open(tarjetas[0][1])
    ancho_t = ANCHO_TARJETA
    alto_t = round(original.height * ANCHO_TARJETA / original.width)

    PAD, GAP, TOP, PIE = 60, 56, 150, 250
    W = PAD * 2 + ancho_t * len(tarjetas) + GAP * (len(tarjetas) - 1)
    H = TOP + alto_t + PIE

    lamina = Image.new("RGB", (W, H), LAMINA_FONDO)
    d = ImageDraw.Draw(lamina)
    d.text((PAD, 44), "COMPARATIVA DE TEMAS", font=fuente(600, 26), fill=LAMINA_TEXTO)
    d.text((PAD, 84), " · ".join(t for t, _ in tarjetas).upper(),
           font=fuente(300, 20), fill=LAMINA_SUAVE)

    for i, (tema, ruta) in enumerate(tarjetas):
        x = PAD + i * (ancho_t + GAP)
        d.text((x, TOP - 40), tema, font=fuente(600, 22), fill=LAMINA_TEXTO)
        lamina.paste(Image.open(ruta).convert("RGB").resize((ancho_t, alto_t), Image.LANCZOS), (x, TOP))
        d.rectangle([x - 1, TOP - 1, x + ancho_t, TOP + alto_t], outline=LAMINA_BORDE)

    # Barra: cada color ocupa lo que de verdad ocupa en la última pieza.
    by = TOP + alto_t + 54
    d.text((PAD, by - 34), f"USO MEDIDO EN {tarjetas[-1][0].upper()}",
           font=fuente(500, 19), fill=LAMINA_SUAVE)
    ancho_barra = W - PAD * 2
    x = PAD
    for nombre, valor, _ in paleta:
        segmento = max(2, int(ancho_barra * medido.get(nombre, 0) / 100))
        d.rectangle([x, by, x + segmento, by + 42], fill=hex_a_rgb(valor))
        x += segmento
    d.rectangle([PAD, by, PAD + ancho_barra, by + 42], outline=LAMINA_BORDE)

    ty = by + 62
    columna = ancho_barra // max(1, len(paleta))
    for i, (nombre, valor, objetivo) in enumerate(paleta):
        cx = PAD + i * columna
        d.rectangle([cx, ty, cx + 16, ty + 16], fill=hex_a_rgb(valor), outline=LAMINA_BORDE)
        d.text((cx + 24, ty - 2), nombre, font=fuente(600, 15), fill=LAMINA_TEXTO)
        detalle = f"{medido.get(nombre, 0):.1f}%"
        if objetivo is not None:
            detalle += f"  (objetivo {objetivo}%)"
        d.text((cx + 24, ty + 18), detalle, font=fuente(400, 14), fill=LAMINA_SUAVE)
        d.text((cx + 24, ty + 38), valor, font=fuente(300, 13), fill=LAMINA_TENUE)

    salida.parent.mkdir(parents=True, exist_ok=True)
    lamina.save(salida)


def main():
    disponibles = temas_disponibles()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("temas", nargs="*", default=["v2", "v3"],
                   help=f"temas a comparar (hay: {', '.join(disponibles)})")
    p.add_argument("--slug", help="persona a dibujar (por defecto, la primera de personas.json)")
    p.add_argument("-o", "--salida", type=Path, default=ROOT / "build" / "comparativa.png")
    p.add_argument("--abrir", action="store_true", help="abrir la imagen al terminar")
    args = p.parse_args()

    temas = args.temas or ["v2", "v3"]
    for tema in temas:
        if tema not in disponibles:
            raise SystemExit(f"✗ no existe templates/{tema}/  ·  hay: {', '.join(disponibles)}")

    personas = json.loads((DATA / "personas.json").read_text(encoding="utf-8"))
    if not personas:
        raise SystemExit("✗ data/personas.json está vacío.")
    slug = args.slug or personas[0]["slug"]

    with tempfile.TemporaryDirectory(prefix="comparar-temas-") as tmp:
        trabajo = Path(tmp)
        tarjetas = [(tema, compilar(tema, slug, trabajo)) for tema in temas]
        paleta = paleta_de_marca()
        medido = medir(tarjetas[-1][1], paleta)
        componer(tarjetas, paleta, medido, args.salida)

    ruta = args.salida.relative_to(ROOT) if args.salida.is_relative_to(ROOT) else args.salida
    print(f"✓ {ruta}\n")
    print(f"  Reparto medido en {temas[-1]}:")
    for nombre, valor, objetivo in paleta:
        objetivo_txt = f"  (objetivo {objetivo}%)" if objetivo is not None else ""
        print(f"    {nombre:<8} {valor}  {medido.get(nombre, 0):5.1f}%{objetivo_txt}")
    print(f"    {'otros':<8} {'—':<7}  {medido.get('otros', 0):5.1f}%  logo, plano de fondo, bordes suavizados")

    if args.abrir:
        subprocess.run(["xdg-open", str(args.salida)], check=False)


if __name__ == "__main__":
    main()
