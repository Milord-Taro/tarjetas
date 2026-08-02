# Iconografía TOPP CREATE — qué corregir y qué falta

**Fecha:** 2 de agosto de 2026
**Entrega revisada:** carpetas `Iconos` y `Logo` (JPG, PNG y SVG)
**Anexo:** `iconografia-evidencia.png` — las capturas de las que habla este documento

---

## 1. Resumen para dirección

El equipo de diseño entregó siete iconos y los dos logos en vectorial. **Los
logos están perfectos y ya son un avance importante:** hasta ahora solo teníamos
versiones en imagen fija, y las vectoriales se pueden ampliar a cualquier tamaño
—una valla, un plano, un membrete— sin que se pixelen.

Con los iconos hay un problema y dos huecos.

**El problema:** están dibujados con una línea muy fina, pensada para verse
grandes. En la tarjeta digital cada icono ocupa unos 32 píxeles —más o menos el
tamaño de una letra mayúscula— y a ese tamaño la línea desaparece. En el anexo
se ve el mismo archivo grande y pequeño: el de edificios, por ejemplo, se
convierte en una mancha.

No es que estén mal dibujados. Es que están dibujados para un tamaño y se
necesitan para otro. **La buena noticia es que no hay que rehacerlos: basta con
volver a exportarlos con la línea más gruesa.** Es un ajuste de minutos por
icono, no un rediseño.

**Los dos huecos:**

- De los siete iconos, cinco son de servicios (obras, interiorismo, renders,
  portafolio, servicios). Sirven para la página web, pero **la tarjeta de
  presentación no los usa**.
- Para la tarjeta hacen falta seis iconos que no vinieron: correo, WhatsApp,
  sitio web, Instagram, LinkedIn y guardar contacto. Hoy están cubiertos con
  iconos genéricos —no son de la marca—, y eso se nota cuando se ponen al lado
  de uno de TOPP.

**Qué se está pidiendo:** re-exportar los siete que ya existen con la línea más
gruesa, y dibujar los que faltan. Con eso la tarjeta queda 100 % con
iconografía propia y el set sirve también para la web y las propuestas.

---

## 2. Qué está pasando, con el detalle

### La línea es demasiado fina para el tamaño de uso

Los iconos vienen dibujados sobre un lienzo de 150 × 150 con un grosor de línea
de 1 a 1,5. Eso es aproximadamente **el 1 % del alto del icono**.

En la tarjeta se usan a 32 píxeles. A ese tamaño, ese 1 % equivale a **menos de
medio píxel de grosor**: la pantalla no puede dibujar media línea, así que la
difumina hasta que casi desaparece.

Ya se probó engrosando la línea artificialmente y **todos vuelven a leerse
bien**, incluidos los de edificios y grúa, que eran los peores. Por eso la
recomendación es re-exportar y no rediseñar.

### Los iconos traen un fondo blanco pegado

Los siete SVG incluyen un rectángulo blanco a pantalla completa detrás del
dibujo. Eso impide ponerlos sobre cualquier fondo que no sea blanco — incluida
la cabecera negra de la propia marca, donde se vería un cuadrado blanco
alrededor del icono.

Los PNG sí vienen con el fondo transparente, que es lo correcto.

### El color va fijo dentro del archivo

Cada icono tiene el color `#1D1D1B` escrito dentro. Eso significa que el mismo
archivo no se puede usar en negro sobre fondo claro y en claro sobre fondo
oscuro: harían falta dos archivos por icono, y mantenerlos sincronizados.

Si el color se deja "heredable", un solo archivo sirve para los dos casos y
siempre toma el color que le corresponda según dónde se ponga.

### Detalles menores

- **La carpeta se llama `JPG` pero contiene archivos PNG** (de 297 px). Además,
  esos sí traen el fondo blanco incrustado. No se usaron.
- **`Ubicación.svg` lleva tilde en el nombre.** Los nombres de archivo con
  tildes dan problemas en servidores web y en algunos sistemas. Conviene
  entregar siempre en minúscula, sin tildes y sin espacios: `ubicacion.svg`.
- **El grosor no es consistente entre los siete.** Unos usan 1, otros 1,5, y
  `Servicios` mezcla relleno con línea. En un set de siete se disimula; en uno
  de veinte se va a notar mucho.
- **Los logos usan `#2C3235`,** que no es ninguno de los cinco colores del
  manual de marca. Es casi igual al Grafito `#2C2C2C`, pero conviene unificarlo.

---

## 3. Correcciones al set que ya existe

Aplica a los siete: Contacto, Interiorismo, Obras, Portafolio, Renders,
Servicios, Ubicación.

| # | Corrección | Detalle |
|---|---|---|
| 1 | **Engrosar la línea** | Del 1 % actual al **2–3 % del alto del icono**. Sobre el lienzo de 150 que ya usan, eso es un grosor de **3 a 4,5**. |
| 2 | **Mismo grosor en todos** | Hoy hay 1, 1,5 y una mezcla. Que los siete usen exactamente el mismo valor. |
| 3 | **Quitar el fondo blanco** | Sin el `<rect fill="white">`. El fondo debe quedar transparente. |
| 4 | **Color heredable** | Que la línea use `currentColor` en vez de `#1D1D1B`. Si la herramienta no lo permite, entregar dos versiones: una oscura y una clara. |
| 5 | **Nombres normalizados** | Minúscula, sin tildes, sin espacios: `ubicacion.svg`, no `Ubicación.svg`. |
| 6 | **Carpetas bien rotuladas** | Si dice `JPG`, que sean JPG. Si son PNG a otra resolución, que la carpeta lo diga (`PNG@2x`). |
| 7 | **`Servicios` unificado** | Que sea solo línea, como los otros seis, y no una mezcla de relleno y línea. |

**Cómo comprobarlo antes de entregar:** poner el icono a 32 píxeles en pantalla
y mirarlo. Si a ese tamaño no se reconoce de un vistazo, todavía no está listo.

---

## 4. Iconos que faltan

### Prioridad alta — los necesita la tarjeta digital

Hoy estos seis están cubiertos con iconos genéricos que no son de la marca.

| Icono | Dónde se usa |
|---|---|
| **Correo / mensaje** | Dos filas de la tarjeta: correo profesional y correo empresarial |
| **WhatsApp** | La fila de WhatsApp |
| **Sitio web** | Fila de enlaces |
| **Instagram** | Fila de enlaces |
| **LinkedIn** | Fila de enlaces |
| **Guardar contacto** | El botón del pie de la tarjeta |

Una nota sobre los tres de redes sociales: Instagram, LinkedIn y WhatsApp tienen
marcas registradas con guías de uso propias. Lo habitual es respetar la forma
oficial del símbolo y adaptar solo el color y el grosor al estilo de la casa.

### Prioridad media — para la web y las propuestas

| Icono | Para qué |
|---|---|
| **Teléfono fijo** | Distinguirlo del móvil. El de "Contacto" actual sirve como base |
| **Descargar / PDF** | Fichas, planos, propuestas |
| **Compartir** | Botones de la web |
| **Calendario / agendar** | Solicitar una cita |
| **Cotización / presupuesto** | Llamada a la acción de la web |
| **Buscar** | Buscador de la web |
| **Flechas** (izquierda, derecha, arriba, abajo) | Galerías y carruseles |
| **Cerrar** (equis) | Ventanas y menús |
| **Menú** (tres líneas) | Navegación en móvil |

### Prioridad baja — según a dónde se quiera llegar

Redes que suelen usar los estudios de arquitectura: **Behance**, **Pinterest**,
**YouTube**, **Facebook**.

---

## 5. Especificación para las próximas entregas

Un checklist para que la siguiente tanda entre directo, sin retoques.

**Formato**

- SVG como formato principal, uno por icono.
- PNG con fondo transparente como respaldo, a 512 px de lado.
- Nada de JPG para iconos: el JPG no admite transparencia.

**Construcción**

- Lienzo cuadrado, mismo tamaño para todos.
- Todos los iconos ópticamente del mismo peso: que ninguno se vea más oscuro o
  más cargado que sus vecinos puestos en fila.
- Grosor de línea entre el 2 % y el 3 % del alto del lienzo, idéntico en todos.
- Terminaciones y uniones de línea redondeadas, iguales en todo el set.
- Un margen interior de aproximadamente el 8 % del lienzo, para que al ponerlos
  dentro de un círculo no queden pegados al borde.

**Color**

- Un solo color por icono, heredable (`currentColor`).
- Si no es posible, entregar dos versiones por icono: oscura y clara.
- Los colores del manual son: Negro Ébano `#121212`, Marfil `#F5F2EB`, Gris
  Piedra `#8E8B86`, Taupe `#C8C1B8`, Grafito `#2C2C2C`.

**Nombres y carpetas**

- Minúscula, sin tildes, sin espacios, con guion: `guardar-contacto.svg`.
- Nombre por lo que el icono **significa**, no por lo que dibuja:
  `ubicacion.svg`, no `edificios.svg`.
- Una carpeta por formato, rotulada con lo que de verdad contiene.

**Prueba final antes de entregar**

Poner todos los iconos en fila a 32 píxeles, sobre fondo claro y sobre fondo
oscuro. Los tres criterios son: que cada uno se reconozca solo, que ninguno pese
visiblemente más que los demás, y que ninguno traiga un recuadro alrededor.

---

## 6. Lo que ya quedó resuelto de este lado

Para que no se pida dos veces. Al incorporar la entrega al proyecto se hicieron
estos ajustes, todos mecánicos:

- Nombres pasados a minúscula y sin tildes.
- Fondo blanco retirado de los siete SVG.
- Descartada la carpeta `JPG` (eran PNG con fondo blanco).
- Logos vectoriales incorporados como `logo-vertical.svg` y
  `logo-horizontal.svg`.

Queda anotado en el archivo de créditos del proyecto. **El grosor de línea no se
tocó**, porque esa sí es una decisión de diseño y no un arreglo de archivo.
