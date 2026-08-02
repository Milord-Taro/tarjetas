#!/usr/bin/env python3
"""Prepara el plano de fondo de la tarjeta a partir de originales de dominio público.

Fuente: Historic American Buildings Survey (HABS). Los HABS son obra del gobierno
de EE.UU. y están en dominio público; los archivos se toman de Wikimedia Commons.

Los originales son fotocopias: papel gris, bordes de la foto y anotaciones a
mano. Acá se recorta el área de dibujo y se convierte a línea sobre transparente,
para poder teñirla del color de marca y bajarle la opacidad sin arrastrar el
fondo gris de la fotografía.

La tarjeta es un rectángulo muy alto y angosto, así que un solo plano no lo cubre
a lo alto sin repetirse. En vez de repetir —el empalme se nota— se compone un
pliego vertical apilando varias vistas a un mismo ancho, como una lámina de obra.

Salida:
  assets/marcas/topp-create/fondo-plano-habs.png
  assets/marcas/topp-create/CREDITOS.md
"""

import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SALIDA_DIR = ROOT / "assets" / "marcas" / "topp-create"

COLOR_LINEA = (36, 41, 45)
ANCHO_PLIEGO = 1000

FUENTES = {
    "georgetown": {
        "cache": "_fuente-habs.jpg",
        "titulo": "HABS DC,GEO,118-36 — Georgetown University, Healy Building, First Floor Plan",
        "autor": "Historic American Buildings Survey (National Park Service)",
        "licencia": "Dominio público (obra del gobierno federal de EE.UU.)",
        "commons": "https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey_ORIGINAL_DRAWING,_FIRST_FLOOR_PLAN_(FROM_AN_ORIGINAL_IN_THE_OFFICE_OF_THE_VICE_PRESIDENT_FOR_DEVELOPMENT_AND_PHYSICAL_PLANT,_GEORGETOWN_UNIVERSITY_HABS_DC,GEO,118-36.tif",
        "loc": "https://www.loc.gov/pictures/item/dc0121.photos/",
        "descarga": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/"
            "Historic_American_Buildings_Survey_ORIGINAL_DRAWING%2C_FIRST_FLOOR_PLAN_"
            "%28FROM_AN_ORIGINAL_IN_THE_OFFICE_OF_THE_VICE_PRESIDENT_FOR_DEVELOPMENT_"
            "AND_PHYSICAL_PLANT%2C_GEORGETOWN_UNIVERSITY_HABS_DC%2CGEO%2C118-36.tif/"
            "2400px-Historic_American_Buildings_Survey_ORIGINAL_DRAWING%2C_FIRST_FLOOR_PLAN_"
            "%28FROM_AN_ORIGINAL_IN_THE_OFFICE_OF_THE_VICE_PRESIDENT_FOR_DEVELOPMENT_"
            "AND_PHYSICAL_PLANT%2C_GEORGETOWN_UNIVERSITY_HABS_DC%2CGEO%2C118-36.tif.jpg"
        ),
        "recorte": (0.132, 0.125, 0.940, 0.845),
        # Umbrales de tinta/papel, leídos del histograma de cada original.
        "tinta": 95,
        "papel": 185,
    },
    "binghamton": {
        "cache": "_fuente-habs-binghamton.jpg",
        "titulo": "HABS NY,4-BING,3-11 — Binghamton City Hall, First Floor Plan (1897)",
        "autor": "Historic American Buildings Survey (National Park Service)",
        "licencia": "Dominio público (obra del gobierno federal de EE.UU.)",
        "commons": "https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey,_BINGHAMTON_CITY_HALL,_PHOTOCOPY_OF_ORIGINAL_WORKING_DRAWING_OF_FIRST_FLOOR_PLAN_-_1897_FROM_THE_OFFICE_OF_THE_CITY_ENGINEER,_BINGHAMTON,_NEW_HABS_NY,4-BING,3-11.tif",
        "loc": "https://www.loc.gov/pictures/item/ny0457.photos/",
        "descarga": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/"
            "Historic_American_Buildings_Survey%2C_BINGHAMTON_CITY_HALL%2C_PHOTOCOPY_OF_"
            "ORIGINAL_WORKING_DRAWING_OF_FIRST_FLOOR_PLAN_-_1897_FROM_THE_OFFICE_OF_THE_"
            "CITY_ENGINEER%2C_BINGHAMTON%2C_NEW_HABS_NY%2C4-BING%2C3-11.tif/"
            "2400px-Historic_American_Buildings_Survey%2C_BINGHAMTON_CITY_HALL%2C_PHOTOCOPY_OF_"
            "ORIGINAL_WORKING_DRAWING_OF_FIRST_FLOOR_PLAN_-_1897_FROM_THE_OFFICE_OF_THE_"
            "CITY_ENGINEER%2C_BINGHAMTON%2C_NEW_HABS_NY%2C4-BING%2C3-11.tif.jpg"
        ),
        "recorte": (0.068, 0.055, 0.885, 0.905),
        "tinta": 80,
        "papel": 165,
    },
}

# Vistas que componen el pliego, de arriba abajo. El giro es solo para variar la
# proporción de cada bloque: en un fondo la orientación del plano es indiferente.
PLIEGO = [
    ("georgetown", 90),
    ("binghamton", 0),
    ("georgetown", 0),
]


def descargar(clave):
    fuente = FUENTES[clave]
    cache = SALIDA_DIR / fuente["cache"]
    if cache.exists():
        return cache
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    peticion = urllib.request.Request(
        fuente["descarga"],
        headers={"User-Agent": "tarjetas-toppcreate/1.0 (generacion de assets de marca)"},
    )
    with urllib.request.urlopen(peticion, timeout=180) as respuesta:
        cache.write_bytes(respuesta.read())
    return cache


def a_linea(clave):
    """Recorta el área de dibujo y pasa la luminancia a alfa: papel transparente,
    línea opaca, y el color de marca como tinta."""
    fuente = FUENTES[clave]
    im = Image.open(descargar(clave)).convert("L")
    w, h = im.size
    x0, y0, x1, y1 = fuente["recorte"]
    im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))

    tinta_plena, papel_limpio = fuente["tinta"], fuente["papel"]
    rango = papel_limpio - tinta_plena
    tabla = [
        255 if v <= tinta_plena else 0 if v >= papel_limpio else int(255 * (papel_limpio - v) / rango)
        for v in range(256)
    ]
    capa = Image.new("RGBA", im.size, COLOR_LINEA + (255,))
    capa.putalpha(im.point(tabla))
    return capa


def componer_pliego():
    bloques = []
    for clave, giro in PLIEGO:
        capa = a_linea(clave)
        if giro:
            capa = capa.rotate(giro, expand=True)
        # Se recorta al área con tinta: los márgenes de papel de cada original
        # dejaban aire muerto arriba del pliego y el dibujo arrancaba más abajo
        # de donde empieza el rectángulo de la tarjeta.
        recorte = capa.getbbox()
        if recorte:
            capa = capa.crop(recorte)
        escala = ANCHO_PLIEGO / capa.width
        bloques.append(capa.resize((ANCHO_PLIEGO, max(1, int(capa.height * escala))), Image.LANCZOS))

    alto = sum(b.height for b in bloques)
    pliego = Image.new("RGBA", (ANCHO_PLIEGO, alto), (0, 0, 0, 0))
    y = 0
    for bloque in bloques:
        pliego.alpha_composite(bloque, (0, y))
        y += bloque.height
    return pliego


def escribir_creditos():
    fichas = []
    for clave, _ in dict.fromkeys(PLIEGO):
        f = FUENTES[clave]
        fichas.append(
            f"### {f['titulo']}\n\n"
            f"- **Autor:** {f['autor']}\n"
            f"- **Licencia:** {f['licencia']}\n"
            f"- **Wikimedia Commons:** {f['commons']}\n"
            f"- **Library of Congress:** {f['loc']}\n"
        )
    texto = (
        "# Créditos de assets de terceros\n\n"
        "## fondo-plano-habs.png\n\n"
        "Pliego compuesto por `scripts/preparar_plano_fondo.py` a partir de estos\n"
        "levantamientos, ambos en dominio público:\n\n"
        + "\n".join(fichas)
        + "\nEl procesado se limita a recortar el área de dibujo, pasar a un solo color\n"
        "y apilar las vistas a un mismo ancho.\n\n"
        "El resto de assets de esta carpeta (logotipos, `edificio-linea.*`,\n"
        "`fondo-plano-planta/implantacion/reticula/alzado`) son propios del proyecto.\n"
    )
    (SALIDA_DIR / "CREDITOS.md").write_text(texto, encoding="utf-8")


def main():
    pliego = componer_pliego()
    salida = SALIDA_DIR / "fondo-plano-habs.png"
    pliego.save(salida)
    escribir_creditos()
    print(f"• {salida.relative_to(ROOT)}  ({pliego.width}x{pliego.height}, proporción 1:{pliego.height/pliego.width:.2f})")
    print(f"• {(SALIDA_DIR / 'CREDITOS.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
