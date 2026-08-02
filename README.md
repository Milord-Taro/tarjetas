# Tarjetas de presentación digitales

Sistema de tarjetas de presentación digitales para TOPP CREATE (estudio de
arquitectura, co-fundado por Daniel Manotas) y, a futuro, para otros
profesionales de la familia con marcas propias distintas.

## Estructura

```
data/
  config.json       # base_url pública + tema activo
  marcas.json       # datos de cada marca/empresa (incluye paleta y tagline)
  personas.json     # datos de cada persona, referencian una marca por marca_id
assets/
  marcas/<id>/       # recursos compartidos a nivel empresa (logo, variantes)
  personas/<slug>/   # recursos individuales de cada persona (foto, etc.)
  fuentes/           # Montserrat variable, para que los PNG usen la tipografía corporativa
templates/
  v1/                # tema original: monocromático, colores principales del manual
  v2/                # tema actual: paleta secundaria del roll-up (carbón + olivo + crema)
scripts/
  build.mjs             # genera dist/ a partir de data/
  generar_imagenes.py   # genera QR + imagen para WhatsApp
  generar_edificio.py   # axonométrico de línea (asset alternativo de fondo)
  generar_planos.py     # prototipos de plano dibujados por código (alternativas de fondo)
  preparar_plano_fondo.py # procesa el plano HABS de dominio público que se usa de fondo
dist/                # salida generada, no se edita a mano (se publica en GitHub Pages)
```

## Lógica de separación de carpetas

- `assets/marcas/` es lo compartido a nivel empresa (logo, variantes). Un
  cambio ahí afecta a todas las personas que compartan esa marca.
- `assets/personas/` es exclusivamente individual de cada quien.
- `dist/` es la salida generada (no se edita a mano), lo que eventualmente se
  publica en GitHub Pages.

## Temas

Cada subcarpeta de `templates/` es un tema (`card.html` + `style.css`). El tema
activo se define en `data/config.json` → `"tema"`:

- el tema activo se publica en `dist/{slug}/` — es el que abre el QR;
- los demás quedan en `dist/{slug}/{tema}/` para poder comparar versiones sin
  recompilar. Ej.: `dist/daniel-manotas/v1/`.

`qr.png`, `contacto.vcf` y `tarjeta-whatsapp.png` se generan una sola vez en la
raíz de cada persona; los temas secundarios los referencian un nivel arriba.

## Colores

El manual de marca solo define los tres colores principales (`#4D4D4D`,
`#B3B3B3`, `#FFFFFF`), en `marcas.json` → `colores`. La paleta secundaria de
`colores_secundarios` (carbón `#24292D`, olivo `#83855B`, crema `#F4F1EC`) se
tomó del arte del roll-up aprobado, no del manual. Los tonos `olivo_texto` y
`olivo_claro` son variantes de contraste del mismo olivo, para que el texto
pequeño cumpla AA sobre crema y sobre carbón.

## Cómo regenerar

```bash
python3 scripts/preparar_plano_fondo.py  # solo si se cambia el plano de fondo
node scripts/build.mjs                # HTML + CSS + vCard de cada persona
python3 scripts/generar_imagenes.py   # QR + imagen para WhatsApp (corre después del build)
```

El fondo en uso es un pliego vertical compuesto con dos levantamientos HABS de
dominio público (Healy Building de Georgetown y Binghamton City Hall),
procesados a línea sobre transparente por `preparar_plano_fondo.py`. Se apilan
varias vistas a un mismo ancho porque la tarjeta es un rectángulo muy alto: un
solo plano obligaría a repetir, y el empalme se nota. Así entra completo a lo
ancho —sin recorte lateral— y cubre todo el alto de una pasada.

La procedencia y licencia de cada original quedan en
`assets/marcas/topp-create/CREDITOS.md`; los originales se cachean como
`_fuente-habs*.jpg` para no depender de la red en cada build.

Como alternativas quedan los cuatro planos dibujados por código
(`generar_planos.py`: `planta`, `implantacion`, `reticula`, `alzado`) y el
axonométrico de `generar_edificio.py`. El que se usa se elige en `marcas.json`
con `fondo_plano` / `fondo_plano_png`.

El plano se ajusta al ancho y se repite en vertical, no se escala para cubrir: la
tarjeta es tan alta y angosta que al cubrir el trazo queda grueso y compite con
el texto.

Los QR se escalan a un múltiplo exacto del número de módulos, con vecino más
cercano. Si se interpolan, los bordes quedan difusos y dejan de leerse apenas la
imagen se ve pequeña.

Lo que decide si un QR se escanea desde una pantalla no es la resolución del
archivo sino cuántos píxeles mide cada módulo cuando la imagen se ve completa:
al abrir una imagen de 1080×2000 en un monitor de 1080p se muestra a la mitad,
así que un módulo de 4px queda en 2 y la cámara no lo resuelve. Por eso los dos
QR usan corrección Q en vez de H (menos corrección → menos módulos → módulos más
grandes) y ocupan `QR_TAMANO = 360`: quedan en 4px por módulo en pantalla, el
doble que antes. Si se agranda el QR o se alarga la URL hay que revisar que la
cuenta siga dando — el script avisa si el bloque invade el pie, pero no si los
módulos quedaron muy finos.

Para previsualizar: `python3 -m http.server 8899 --directory dist` y abrir
`http://localhost:8899/daniel-manotas/`.

## Publicación

El sitio vive en GitHub Pages: <https://milord-taro.github.io/tarjetas/>.

`dist/` se versiona y `.github/workflows/pages.yml` lo publica tal cual en cada
push a `main`. El build **no** corre en CI a propósito: `generar_imagenes.py`
depende de Pillow y de la fuente local, y el QR conviene revisarlo a ojo antes de
que se imprima. Entonces el ciclo es: regenerar en local → revisar → commit → push.

`dist/index.html` y `dist/.nojekyll` los genera `build.mjs`. El primero redirige
la raíz a la única tarjeta (o lista todas, si hay varias); el segundo evita que
Pages pase el sitio por Jekyll.

### Migrar a dominio propio

Cuando `tarjetas.toppcreate.com` esté disponible:

1. `data/config.json` → `base_url` al dominio nuevo;
2. crear `dist/CNAME` con el dominio (una línea, sin `https://`);
3. en el DNS, un `CNAME` de `tarjetas` → `milord-taro.github.io`;
4. regenerar (`build.mjs` + `generar_imagenes.py`) y volver a imprimir el QR.

El paso 4 es el costoso: el QR lleva la URL grabada, así que **todo material ya
impreso con el QR viejo deja de servir**. Conviene decidir el dominio antes de
mandar a imprimir en cantidad.
