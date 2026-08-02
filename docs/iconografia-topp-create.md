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

**El problema son dos cosas pequeñas, ninguna grave:**

1. **Cada icono ocupa una porción distinta de su lienzo.** El del teléfono llena
   el 46 % del cuadro y el de edificios el 62 %. Como el programa los coloca por
   el cuadro y no por el dibujo, unos salen grandes y otros pequeños sin que
   nadie lo haya decidido. Se ve en el punto A del anexo.
2. **La línea es algo fina para el tamaño de uso.** En la tarjeta cada icono
   mide unos 31 píxeles —el tamaño de una letra mayúscula—. A esa medida se
   reconocen los siete, pero se ven más pálidos que un icono corriente puesto al
   lado. En el punto B del anexo están los mismos siete antes y después de
   engrosar la línea.

**No hay que rehacerlos.** Son dos ajustes de exportación: igualar cuánto ocupa
el dibujo dentro del cuadro, y duplicar el grosor de la línea. Minutos por
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

### El dibujo no ocupa lo mismo en todos los lienzos

Los siete vienen sobre un lienzo de 150 × 150, pero el dibujo dentro ocupa una
parte distinta en cada uno: 46 % de ancho en `contacto`, 62 % en `ubicacion`.

Quien coloca los iconos lo hace por el lienzo, porque es lo único que el archivo
declara. El resultado es que puestos en fila unos se ven grandes y otros
pequeños, sin ninguna intención detrás. Se arregla dejando siempre el mismo
margen entre el dibujo y el borde del lienzo.

### La línea es algo fina para el tamaño de uso

El grosor es de 1 a 1,5 sobre el lienzo de 150 — alrededor del **1 % del alto**.
Para comparar: un icono de interfaz corriente ronda el 6 %.

Encuadrados correctamente y a 31 píxeles **los siete se reconocen**, así que el
problema es menor de lo que parecía en una primera prueba. Lo que sí pasa es que
se ven notoriamente más pálidos que los iconos corrientes que están usándose hoy
en la tarjeta, y al mezclarlos la fila queda despareja.

Se probó duplicando el grosor y quedan emparejados. Con eso basta: no hace falta
llegar al 6 % ni cambiar el estilo fino, que es parte del carácter de la marca.

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
| 1 | **Igualar el encuadre** | Que el dibujo ocupe la misma proporción del lienzo en los siete, dejando el mismo margen al borde (≈8 % del lienzo). Hoy va del 46 % al 62 %. |
| 2 | **Duplicar el grosor de línea** | De 1–1,5 a **2,5–3** sobre el lienzo de 150. No más: el trazo fino es parte del carácter de la marca, solo hay que emparejarlo con el resto de la interfaz. |
| 3 | **Mismo grosor en todos** | Hoy hay 1, 1,5 y una mezcla. Que los siete usen exactamente el mismo valor. |
| 4 | **Quitar el fondo blanco** | Sin el `<rect fill="white">`. El fondo debe quedar transparente. |
| 5 | **Color heredable** | Que la línea use `currentColor` en vez de `#1D1D1B`. Si la herramienta no lo permite, entregar dos versiones: una oscura y una clara. |
| 6 | **Nombres normalizados** | Minúscula, sin tildes, sin espacios: `ubicacion.svg`, no `Ubicación.svg`. |
| 7 | **Carpetas bien rotuladas** | Si dice `JPG`, que sean JPG. Si son PNG a otra resolución, que la carpeta lo diga (`PNG@2x`). |
| 8 | **`Servicios` unificado** | Que sea solo línea, como los otros seis, y no una mezcla de relleno y línea. |

**Cómo comprobarlo antes de entregar:** poner los siete en fila a 31 píxeles.
Si alguno se reconoce peor que sus vecinos, o pesa visiblemente más o menos que
ellos, todavía no está listo.

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
- **El dibujo debe ocupar la misma proporción del lienzo en todos.** Es el
  detalle que más descuadra un set y el más fácil de pasar por alto.
- Todos los iconos ópticamente del mismo peso: que ninguno se vea más oscuro o
  más cargado que sus vecinos puestos en fila.
- Grosor de línea alrededor del 2 % del alto del lienzo, idéntico en todos.
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
