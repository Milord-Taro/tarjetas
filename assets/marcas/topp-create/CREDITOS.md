# Créditos de assets de terceros

## fondo-plano-habs.png

Pliego compuesto por `scripts/preparar_plano_fondo.py` a partir de estos
levantamientos, ambos en dominio público:

### HABS DC,GEO,118-36 — Georgetown University, Healy Building, First Floor Plan

- **Autor:** Historic American Buildings Survey (National Park Service)
- **Licencia:** Dominio público (obra del gobierno federal de EE.UU.)
- **Wikimedia Commons:** https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey_ORIGINAL_DRAWING,_FIRST_FLOOR_PLAN_(FROM_AN_ORIGINAL_IN_THE_OFFICE_OF_THE_VICE_PRESIDENT_FOR_DEVELOPMENT_AND_PHYSICAL_PLANT,_GEORGETOWN_UNIVERSITY_HABS_DC,GEO,118-36.tif
- **Library of Congress:** https://www.loc.gov/pictures/item/dc0121.photos/

### HABS NY,4-BING,3-11 — Binghamton City Hall, First Floor Plan (1897)

- **Autor:** Historic American Buildings Survey (National Park Service)
- **Licencia:** Dominio público (obra del gobierno federal de EE.UU.)
- **Wikimedia Commons:** https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey,_BINGHAMTON_CITY_HALL,_PHOTOCOPY_OF_ORIGINAL_WORKING_DRAWING_OF_FIRST_FLOOR_PLAN_-_1897_FROM_THE_OFFICE_OF_THE_CITY_ENGINEER,_BINGHAMTON,_NEW_HABS_NY,4-BING,3-11.tif
- **Library of Congress:** https://www.loc.gov/pictures/item/ny0457.photos/

### HABS DC,GEO,118-36 — Georgetown University, Healy Building, First Floor Plan

- **Autor:** Historic American Buildings Survey (National Park Service)
- **Licencia:** Dominio público (obra del gobierno federal de EE.UU.)
- **Wikimedia Commons:** https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey_ORIGINAL_DRAWING,_FIRST_FLOOR_PLAN_(FROM_AN_ORIGINAL_IN_THE_OFFICE_OF_THE_VICE_PRESIDENT_FOR_DEVELOPMENT_AND_PHYSICAL_PLANT,_GEORGETOWN_UNIVERSITY_HABS_DC,GEO,118-36.tif
- **Library of Congress:** https://www.loc.gov/pictures/item/dc0121.photos/

El procesado se limita a recortar el área de dibujo, pasar a un solo color
y apilar las vistas a un mismo ancho.

El resto de assets de esta carpeta (logotipos, `edificio-linea.*`,
`fondo-plano-planta/implantacion/reticula/alzado`) son propios del proyecto.

## Entrega de agosto de 2026: iconografía y logos vectoriales

`iconos/*` y `logo-vertical.svg` / `logo-horizontal.svg` los entregó el equipo
de diseño de TOPP CREATE. Son obra propia de la marca.

Cambios hechos al importarlos, todos mecánicos y anotados aquí para poder
pedirlos corregidos en origen:

- **Nombres a minúscula y sin tildes.** `Ubicación.svg` → `ubicacion.svg`: el
  validador del build solo admite `[A-Za-z0-9_.-]` en nombres de archivo, así
  que con la tilde el archivo no se puede referenciar desde `marcas.json`.
- **Fondo blanco quitado de los SVG.** Los siete venían con un
  `<rect width="150" height="150" fill="white"/>` a pantalla completa detrás
  del dibujo. Con eso el icono no se puede poner sobre la cabecera oscura de la
  propia marca: se ve un cuadrado blanco. Los PNG sí venían transparentes.
- **De la carpeta `JPG` no se tomó nada.** No eran JPG sino PNG de 297 px, y a
  diferencia de los de 150 px venían con el fondo blanco incrustado.

Sin tocar, para que lo decida diseño:

- **El trazo es de 1 a 1.5 sobre un lienzo de 150** (≈1 % del alto). A los 32 px
  que miden en la tarjeta eso queda por debajo de medio píxel y el dibujo se
  deshace. Se comprobó que engrosándolo a ~2–3 % vuelven a leerse todos.
- **El color va fijo en el SVG** (`stroke="#1D1D1B"`), así que el icono no puede
  tomar el color del tema. Los logos usan `#2C3235`, que tampoco es ninguno de
  los cinco del manual.
