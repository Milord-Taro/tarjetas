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
  v1/                # legacy, no se mantiene
  v2/                # tema activo: paleta del roll-up (carbón + olivo + crema)
  v3/                # mismo arte que la v2 con la paleta oficial del manual
scripts/
  validar.mjs           # esquema de data/ + validador (lo corre build.mjs y CI)
  build.mjs             # genera dist/ a partir de data/
  generar_imagenes.py   # genera QR + imagen para WhatsApp
  generar_edificio.py   # axonométrico de línea (asset alternativo de fondo)
  generar_planos.py     # prototipos de plano dibujados por código (alternativas de fondo)
  preparar_plano_fondo.py # procesa el plano HABS de dominio público que se usa de fondo
test/                # casos hostiles del esquema y del build (node --test test/*.test.mjs)
build/               # manifiesto intermedio build.mjs → generar_imagenes.py (no se versiona)
dist/                # salida generada, no se edita a mano (se publica en GitHub Pages)
```

## Convenciones

Lo que el validador exige y lo que es solo acuerdo, para que sumar gente y
marcas no dependa de recordar cómo se hizo la vez pasada.

| | Convención | ¿Lo revisa el build? |
|---|---|---|
| **slug** | `nombre-apellido`, minúsculas sin tildes, 3–40 caracteres | sí — y que sea único y no choque con `index`, `assets`, `robots` ni con un nombre de tema |
| **id de marca** | igual que el slug (`topp-create`) | sí |
| **correo** | el que fije cada marca; en TOPP CREATE, `arq.nombre@toppcreate.com` | el dominio sí, contra `dominios_correo` de la marca; el prefijo no |
| **logos** | `logo-{vertical\|horizontal\|emblema}-{gris\|blanco}.png` en `assets/marcas/<id>/` | no — pero si falta el declarado, el build busca por esos nombres |
| **fuentes** | `assets/marcas/<id>/fuentes/`, o `assets/fuentes/` si es compartida | sí — que exista y que declare licencia |
| **procedencia** | `CREDITOS.md` por marca, con licencia de cada asset de terceros | no |

El prefijo del correo se deja a cada marca a propósito: `arq.` funciona para
arquitectos y se rompe con el primer ingeniero o abogado. Lo que sí se
comprueba es el dominio, que es donde de verdad duele el error —un correo de
otra marca pegado en la ficha equivocada es fácil de cometer y difícil de ver en
un diff—.

Sobre marcas incompletas: **sin logo** la tarjeta pone el nombre de la marca en
versalitas (en la web y en el PNG); **sin dirección** desaparecen la fila
"Oficina", el enlace a Maps y el `ADR` del vCard. Las dos cosas ya funcionan, no
hay que hacer nada especial.

## Lógica de separación de carpetas

- `assets/marcas/` es lo compartido a nivel empresa (logo, variantes). Un
  cambio ahí afecta a todas las personas que compartan esa marca.
- `assets/personas/` es exclusivamente individual de cada quien.
- `dist/` es la salida generada (no se edita a mano), lo que eventualmente se
  publica en GitHub Pages.

## Qué se publica y qué no

`dist/` se sirve en GitHub Pages: todo lo que entre en `data/personas.json` queda
público en texto plano, indexable y raspable, y además queda en el historial de
git aunque después se borre. Por eso la tarjeta solo lleva canales
**profesionales**:

- el correo corporativo de la persona (`arq.nombre@toppcreate.com`);
- los canales de la empresa (WhatsApp, correo, oficina).

Todo va en un solo bloque **Empresa**: son canales de trabajo y el cliente los
vive como una sola cosa. Los dos correos se distinguen por la etiqueta —"Correo
profesional" el de la persona, "Correo empresarial" el de la marca— y el
calificador solo aparece cuando de verdad hay dos filas del mismo tipo que
separar; con un solo correo, la etiqueta es "Correo" a secas.

El móvil y el correo personales **no van** ni en la tarjeta ni en el `.vcf`. Si
un cliente necesita un contacto más directo, se le entrega aparte y de forma
consentida, después del primer contacto por los canales de la empresa.

Las filas de contacto se arman en `build.mjs` a partir de los campos que
existan: un campo ausente en el JSON no genera fila, y una sección sin filas
desaparece con su título. Así, quitar un dato del JSON basta para quitarlo de la
tarjeta, del vCard y de la imagen.

Antes de sumar a otra persona hay que pedirle consentimiento explícito por cada
dato que se publique: son datos personales de un tercero y aplica la Ley 1581 de
2012.

### Retirar a una persona

La Ley 1581 da derecho a pedir la supresión de los datos, y ese derecho no se
satisface quitando el enlace. Quitar la ficha de `data/personas.json` **no**
despublicaba nada: la carpeta seguía en `dist/`, servida en la misma URL que
lleva grabada el QR ya impreso, solo que sin aparecer en el índice. Ahora el
build se planta si detecta una tarjeta publicada que ya no tiene ficha.

```bash
# 1. quitar la ficha de data/personas.json
node scripts/build.mjs --retirar     # borra dist/{slug}/ del sitio
python3 scripts/generar_imagenes.py
git add -A && git commit && git push # el push despliega y la URL deja de resolver
```

`--retirar` existe para que despublicar sea una decisión y no un descuido: sin
la bandera el build falla y explica las dos salidas posibles.

Dos cosas que conviene decir de frente antes de que alguien firme:

- **El material impreso deja de funcionar.** Es el efecto buscado en un retiro,
  pero si lo que se quería era corregir un dato, cambiar el `slug` tiene el
  mismo costo que retirar: el QR ya repartido apunta a la URL vieja.
- **El historial es otra cosa.** El repo es público y `dist/` se versiona, así
  que todas las versiones anteriores de la tarjeta siguen en el historial de git
  aunque el sitio ya no las sirva. Borrarlas de verdad exige reescribir el
  historial (`git filter-repo`) y un force push, y aun así GitHub puede
  conservar la copia en caché y en los forks que existan. Por eso la
  autorización debería decir que la publicación es en un sitio público con
  historial, y por eso la regla sigue siendo la de arriba: lo que no deba ser
  público no entra en `data/`.

Después de un force push, **comprobar que el workflow corrió**. Es exactamente
el caso que falló antes (ver "Publicación").

### Cómo trata el build los datos de entrada

Hoy los JSON los escribe quien mantiene el repo, pero la idea es que cada
profesional aporte su ficha (por PR o por un formulario). Desde ese momento
`data/` es entrada no confiable. El esquema y su validador viven en
`scripts/validar.mjs`, que se puede correr solo (`node scripts/validar.mjs`) y
que `build.mjs` ejecuta antes de generar nada.

Hay dos severidades, y la diferencia importa:

**Duro — el build no publica nada.** Los campos que deciden identidad y rutas
de archivo. Un valor raro aquí no es una tarjeta fea: es un archivo escrito
donde no va, o la ficha de alguien publicada bajo el nombre de otro.

| Campo | Qué se acepta | Por qué |
|---|---|---|
| `slug`, `marca_id`, `id` | minúsculas, dígitos y guiones simples | son nombres de carpeta: un `..` escribía fuera de `dist/` y copiaba al sitio imágenes de cualquier parte del disco |
| `slug` | no puede ser `index`, `assets`, `robots`… ni un nombre de tema | chocaría con algo que el build ya escribe, o con `dist/{slug}/{tema}/` |
| `slug` | único entre todas las fichas | dos iguales se pisaban en silencio y el índice enlazaba a la primera con la tarjeta de la segunda |
| `nombre` | obligatorio y no vacío | ausente reventaba con un stack de Node; en blanco publicaba la tarjeta con el hueco vacío, sin avisar |
| `logo`, `logo_claro`, `logo_emblema`, `fondo_plano*` | un nombre plano, sin `/` ni `..` | se concatenan con `path.join` y se copian a `dist/`, que es lo que se publica |
| `base_url` | una URL `https` | va grabada dentro del QR impreso |
| *cualquier campo no listado* | se rechaza | sin esto, una ficha cuela datos que nadie revisó y que igual quedan en `data/` y en el historial |

**Blando — se avisa y se usa el valor por defecto.** Los campos de contenido:
que una marca escriba mal su color no debería dejar a las demás personas sin
publicar.

| Campo | Qué se acepta | Por qué |
|---|---|---|
| `sitio_web`, `linkedin` | solo `https:`, `http:`, `mailto:`, `tel:` | escapar no impide un `javascript:` en un `href` |
| `colores.*`, `tipografia` | `#rgb`…`#rrggbbaa`, y nombres alfanuméricos | van dentro de `<style>`, donde el navegador no decodifica entidades: un `;` o un `}` dejarían inyectar reglas nuevas, incluido un `url()` externo |
| `whatsapp`, `email`, `instagram` | dígitos / correo / usuario | se concatenan dentro de URLs que arma el build |

Los colores se normalizan a `#rrggbb` en un solo sitio. Antes cada consumidor
los interpretaba por su cuenta y no coincidían: un `#fff` —válido en CSS y
aceptado por el build— hacía reventar `generar_imagenes.py` a mitad de la
corrida, y las personas que venían después se quedaban sin QR.

Todo esto está cubierto por `test/`: cada caso salió de un agujero real, así que
son regresiones. `node --test test/*.test.mjs`.

### El manifiesto

`generar_imagenes.py` **no lee `data/`**. Lo hacía, y era el hueco grande: toda
la validación vive en `build.mjs`, así que un dato que la tarjeta web rechazaba
llegaba al PNG intacto. En concreto, un campo `url_publica` en la ficha decidía
qué URL quedaba grabada en el QR —lo que se imprime y lo que nadie revisa a
ojo— mientras la tarjeta web se veía legítima.

Ahora `build.mjs` emite `build/manifiesto.json` con las fichas ya validadas y
normalizadas, y ese es el único insumo del script de imágenes. La URL la calcula
el build a partir de `base_url` + `slug`, y la ficha no puede influir en ella.
El manifiesto no se versiona: es intermedio, no es lo que se publica.

### Terceros y publicación

- **Sin llamadas de red.** Montserrat se sirve desde el propio sitio
  (`@font-face` en cada `style.css`, archivo copiado por el build): pedirla a
  `fonts.googleapis.com` le entregaba la IP y el User-Agent de quien escanea el
  QR a un tercero. La tarjeta también se ve bien sin conexión.
- **Sin scripts en línea.** El logo se emite como `<img>` o como texto de
  respaldo según lo que el build encuentre en disco, sin el `onerror` que antes
  hacía el cambio en el navegador. La tarjeta ya no ejecuta JavaScript, así que
  admite `script-src 'none'`. (Las variables de marca siguen en un `<style>` en
  línea, de modo que `style-src` necesitaría `'unsafe-inline'` o un hash; y
  GitHub Pages no permite mandar cabeceras, así que una CSP tendría que ir en un
  `<meta http-equiv>`.)
- **`noindex`** en las plantillas y `dist/robots.txt` con `Disallow: /`. No es
  una medida de seguridad —quien tenga el enlace entra igual— pero evita
  buscadores y raspadores que respetan el archivo.
- Las acciones del workflow van **ancladas al SHA** del commit, no al tag: un
  tag se puede mover.

## Temas

Cada subcarpeta de `templates/` es un tema (`card.html` + `style.css`). El tema
activo se define en `data/config.json` → `"tema"`:

- el tema activo se publica en `dist/{slug}/` — es el que abre el QR;
- los demás quedan en `dist/{slug}/{tema}/` para poder comparar versiones sin
  recompilar. Ej.: `dist/daniel-manotas/v1/`.

`qr.png`, `contacto.vcf` y `tarjeta-whatsapp.png` se generan una sola vez en la
raíz de cada persona; los temas secundarios los referencian un nivel arriba.

## Qué hay en dist/

`dist/` se sirve tal cual, así que un archivo que sobra ahí es un archivo
publicado. El build lleva el inventario de lo que emite y al final poda lo que
no esté en la lista: si una marca cambia de logo o de plano de fondo, el
anterior desaparece del sitio en vez de quedarse colgando (así se habían
acumulado cuatro assets que ya nada referenciaba). Lo único que respeta sin
haberlo generado es `qr.png` y `tarjeta-whatsapp.png`, que vienen del script de
Python, y `.gitkeep`.

La carpeta completa de una persona es caso aparte: ver "Retirar a una persona".

## Colores

`marcas.json` → `colores` es el **manual de marca**. Los nombres del JSON son
roles, no colores: cada marca los rellena con los suyos y las plantillas se
escriben una sola vez.

| Rol | TOPP CREATE | Nombre en el manual | Uso |
|---|---|---|---|
| `fondo` | `#F5F2EB` | Marfil | 70 % — fondos claros |
| `oscuro` | `#121212` | Negro Ébano | 20 % — textos y fondos oscuros |
| `claro` | `#8E8B86` | Gris Piedra | 8 % — elementos neutros |
| `apoyo` | `#C8C1B8` | Taupe | 8 % — fondos y superficies neutras |
| `acento` | `#2C2C2C` | Grafito | 2 % — líneas, iconos, resaltados |

`apoyo` y `acento` son opcionales y todavía no los pide ninguna plantilla; el
build igual los resuelve, así que están disponibles en cuanto un tema los use.

`colores_secundarios` (carbón `#24292D`, olivo `#83855B`, crema `#F4F1EC`) es
otra cosa: se tomó del arte del roll-up aprobado, no del manual, y es sobre lo
que está construido el tema **v2**, que es el que se publica. Los tonos
`olivo_texto` y `olivo_claro` son variantes de contraste del mismo olivo, para
que el texto pequeño cumpla AA sobre crema y sobre carbón.

Por eso conviven las dos paletas: la **v2** está construida casi entera sobre el
roll-up (28 usos contra 6 del manual) y la **v3** solo sobre el manual. El
manual no tiene olivo, así que llevar la tarjeta a la paleta nueva no es cambiar
unos valores sino repintar el arte — que es justo lo que es la v3.

### El arte, por roles

La imagen para WhatsApp dibuja la misma pieza que la tarjeta web, así que
también tiene que saber qué color va en cada parte. Eso se declara en
`build.mjs` → `ARTE_POR_TEMA`, por **rol** y no por color:

| Rol | Qué es | v2 | v3 |
|---|---|---|---|
| `lienzo` | fondo del cuerpo | crema | Marfil |
| `bloque` | cabecera en chevron | carbón | Negro Ébano |
| `cuna` | franja bajo la cabecera | olivo | Taupe |
| `superficie` | badges rellenos | olivo | Taupe |
| `texto` | nombre y valores | carbón | Negro Ébano |
| `texto_suave` | títulos y etiquetas | olivo texto | Grafito |
| `texto_secundario` | cargo, pies de QR | oscuro | Grafito |
| `realce` | apellidos | olivo | Gris Piedra |
| `linea` | reglas | olivo | Grafito |
| `linea_suave` | separaciones finas | olivo claro | Gris Piedra |
| `pie` | banda inferior | olivo | Negro Ébano |
| `marco_qr` | marco de los códigos | carbón | Grafito |

El manifiesto lleva ya resuelta la paleta del tema activo, así que un tema nuevo
no obliga a tocar `generar_imagenes.py`.

Dos decisiones de la v3 que vienen del contraste, no del gusto: el **realce**
(los apellidos) es Gris Piedra porque el manual no tiene un acento cromático y
la distinción hay que hacerla por valor — funciona porque es texto grande, a
3.04:1—; y el **texto pequeño** va en Grafito y nunca en Gris Piedra, que sobre
marfil no llega al 4.5:1 que pide AA.

Para sacar una maqueta de un tema sin tocar lo publicado:

```bash
node scripts/build.mjs --data /tmp/m/data --out /tmp/m/dist   # con "tema" cambiado
python3 scripts/generar_imagenes.py /tmp/m/build/manifiesto.json
```

## Tipografía

Cada marca declara la suya en `marcas.json`:

```json
"tipografia": {
  "familia": "Montserrat",
  "archivo": "Montserrat-Variable.ttf",
  "licencia": "OFL-1.1"
}
```

También vale la forma corta (`"tipografia": "Montserrat"`), que solo nombra la
familia: sin archivo no hay `@font-face` y la tarjeta cae a la sans-serif del
sistema. Eso es intencional — mejor una tarjeta con otra tipografía que una
fuente servida sin permiso.

El archivo se busca primero en `assets/marcas/<id>/fuentes/` (lo propio de la
marca) y luego en `assets/fuentes/` (lo compartido, que puede usar cualquiera).
La misma fuente la usan la tarjeta web y el PNG de WhatsApp, para que no se vean
de dos marcas distintas.

**`licencia` es obligatoria cuando hay `archivo`, y no es burocracia:** servir un
`.ttf` desde un sitio público es redistribuirlo. Montserrat es OFL y no hay
problema, pero una fuente de fundición necesita licencia webfont, y eso no se ve
mirando el archivo. El validador no deja publicar una fuente sin licencia
declarada.

## Cómo regenerar

```bash
python3 scripts/preparar_plano_fondo.py  # solo si se cambia el plano de fondo
node scripts/validar.mjs              # opcional: revisa data/ sin generar nada
node scripts/build.mjs                # HTML + CSS + vCard + build/manifiesto.json
python3 scripts/generar_imagenes.py   # QR + imagen para WhatsApp (lee el manifiesto)
node --test test/*.test.mjs           # casos hostiles del esquema y del build
```

El orden importa: `generar_imagenes.py` falla con un mensaje claro si no
encuentra `build/manifiesto.json`.

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

## Cómo ver las tarjetas

Todo funciona **sin internet**: `dist/` es HTML, CSS e imágenes, y la tipografía
se sirve desde el propio sitio.

**Lo más rápido — abrir el archivo directamente.** No hace falta ni servidor:

```bash
xdg-open dist/daniel-manotas/index.html       # tema activo (v2)
xdg-open dist/daniel-manotas/v3/index.html    # v3
xdg-open dist/daniel-manotas/tarjeta-whatsapp.png
```

**Con servidor local**, que es lo que más se parece a lo publicado (las rutas
absolutas y la descarga del `.vcf` se comportan igual):

```bash
python3 -m http.server 8899 --directory dist
```

| | |
|---|---|
| Raíz | <http://localhost:8899/> |
| Tema activo (v2) | <http://localhost:8899/daniel-manotas/> |
| v3 | <http://localhost:8899/daniel-manotas/v3/> |
| Imagen de WhatsApp | <http://localhost:8899/daniel-manotas/tarjeta-whatsapp.png> |

**Desde el móvil**, en la misma red wifi: arranca el servidor con
`python3 -m http.server 8899 --bind 0.0.0.0 --directory dist`, mira tu IP con
`hostname -I` y entra a `http://ESA-IP:8899/daniel-manotas/v3/`. Es la única
forma de juzgar de verdad la tarjeta, porque se reparte por WhatsApp y se abre
en un teléfono.

**Los dos temas lado a lado, con el reparto de color medido:**

```bash
python3 scripts/comparar_temas.py            # v2 contra v3
python3 scripts/comparar_temas.py v2 v3 --abrir
```

Compila cada tema en un temporal —no toca `dist/` ni `data/`— y deja
`build/comparativa.png` con las dos piezas y una barra que mide qué porcentaje
ocupa cada color, contra el objetivo que declara la marca en `uso_paleta`.

**En internet** está solo el tema activo, en
<https://milord-taro.github.io/tarjetas/>. Los temas secundarios también se
publican, en `/{slug}/{tema}/`, pero solo después de hacer push.

## Publicación

El sitio vive en GitHub Pages: <https://milord-taro.github.io/tarjetas/>.

`dist/` se versiona y `.github/workflows/pages.yml` lo publica tal cual en cada
push a `main`. El build **no** corre en CI a propósito: `generar_imagenes.py`
depende de Pillow y de la fuente local, y el QR conviene revisarlo a ojo antes de
que se imprima. Entonces el ciclo es: regenerar en local → revisar → commit → push.

Lo que sí corre en CI es la comprobación de que el `dist/` commiteado
corresponde al `data/` commiteado: se recompila a un temporal y se compara. Si
no cuadra, no despliega. Antes eso se sostenía solo en la disciplina de quien
publicaba.

El trigger **no** lleva filtro `paths:`. Lo llevaba, y a cambio de ahorrar
despliegues que no cambiaban nada abría una avería silenciosa: un force push no
disparó el workflow y el sitio siguió sirviendo datos viejos durante horas, sin
ninguna señal —Pages sigue publicando el último despliegue exitoso, así que "no
corrió" y "corrió sin cambios" se ven igual desde fuera—. El force push es
además la maniobra con la que se purgan datos personales del historial: es justo
el momento en el que no se puede depender de que el filtro acierte. Si hace
falta forzar un despliegue, `workflow_dispatch` desde la pestaña Actions.

`.github/workflows/validar.yml` revisa las fichas que llegan por PR (esquema,
tests, que el build no escriba fuera de su directorio). Es `pull_request` y no
`pull_request_target`, a propósito: `pull_request_target` corre con el token del
repo base sobre código que nadie ha revisado todavía. Este workflow no despliega
y no usa secretos.

`dist/index.html` y `dist/.nojekyll` los genera `build.mjs`; el segundo evita que
Pages pase el sitio por Jekyll.

La raíz se comporta distinto según cuánta gente haya. Con **una sola persona**
redirige a su tarjeta: la raíz y la tarjeta son la misma cosa. Con **varias**,
esa raíz pasaría a ser un directorio de nombres y marcas en una URL adivinable
—una pieza distinta de la que cada quien reparte por QR, y que nadie
autorizó—, así que solo aparece quien lo pida con `"listar_en_indice": true` en
su ficha. Si no lo pide nadie, queda una página neutra sin nombres.

### Migrar a dominio propio

Cuando `tarjetas.toppcreate.com` esté disponible:

1. `data/config.json` → `base_url` al dominio nuevo;
2. crear `dist/CNAME` con el dominio (una línea, sin `https://`);
3. en el DNS, un `CNAME` de `tarjetas` → `milord-taro.github.io`;
4. regenerar (`build.mjs` + `generar_imagenes.py`) y volver a imprimir el QR.

El paso 4 es el costoso: el QR lleva la URL grabada, así que **todo material ya
impreso con el QR viejo deja de servir**. Conviene decidir el dominio antes de
mandar a imprimir en cantidad.
