// Genera dist/{slug}/ a partir de data/marcas.json + data/personas.json + templates/.
//
// Temas: cada subcarpeta de templates/ es un tema (card.html + style.css). El tema
// activo (data/config.json → "tema") se publica en dist/{slug}/ y los demás quedan
// en dist/{slug}/{tema}/ para poder comparar versiones sin volver a compilar.
import { readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'data');
const ASSETS_DIR = path.join(ROOT, 'assets');
const TEMPLATES_DIR = path.join(ROOT, 'templates');
const DIST_DIR = path.join(ROOT, 'dist');

const TEMA_POR_DEFECTO = 'v2';

// Montserrat se sirve desde el propio sitio y no desde fonts.googleapis.com: si
// no, cada persona que escanea el QR le entrega su IP y su User-Agent a Google
// sin saberlo. De paso, la tarjeta se ve igual sin conexión. Es el mismo archivo
// que usa generar_imagenes.py para los PNG.
const FUENTE_ARCHIVO = 'Montserrat-Variable.ttf';
const FUENTE_ORIGEN = path.join(ASSETS_DIR, 'fuentes', FUENTE_ARCHIVO);

const LOGOS_CANDIDATOS = [
  'logo-vertical-gris.png',
  'logo-horizontal-gris.png',
  'logo-emblema-gris.png',
];

// Iconos de la fila de redes. Viven acá y no en la plantilla porque la fila se
// arma en JS: cada persona puede tener unos enlaces sí y otros no.
const ICONOS_REDES = {
  web: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"/><line x1="2.5" y1="12" x2="21.5" y2="12"/><path d="M12 2.5a15 15 0 0 1 4 9.5 15 15 0 0 1-4 9.5 15 15 0 0 1-4-9.5 15 15 0 0 1 4-9.5z"/></svg>',
  instagram: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="2.5" width="19" height="19" rx="5"/><circle cx="12" cy="12" r="4.2"/><line x1="17.6" y1="6.4" x2="17.6" y2="6.4"/></svg>',
  linkedin: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3V9zm7 0h3.8v1.7h.05c.53-.95 1.83-1.95 3.75-1.95C21.6 8.75 23 11 23 14.25V21h-4v-6c0-1.6-.03-3.65-2.25-3.65-2.25 0-2.6 1.73-2.6 3.53V21h-4V9z"/></svg>',
};

// Iconos de las filas de contacto, por tema: cada tema tiene su propio trazo
// (v2 usa la burbuja de WhatsApp, v1 el auricular clásico).
const ICONOS_CONTACTO = {
  v2: {
    whatsapp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.5 8.5 0 0 1-3.9-.9L3 20.5l1.5-4.9A8.4 8.4 0 0 1 12.6 3a8.4 8.4 0 0 1 8.4 8.5z"/><path d="M8.9 8.2c.2-.5.4-.5.7-.5h.5c.2 0 .4 0 .6.5l.7 1.6c.1.3 0 .5-.1.6l-.4.5c-.2.2-.2.3-.1.5a6 6 0 0 0 2.8 2.4c.2.1.4.1.5-.1l.5-.6c.2-.2.3-.2.6-.1l1.6.8c.3.1.4.3.4.5s0 .8-.3 1.1c-.3.4-.9.7-1.4.7-1 0-2.9-.7-4.4-2.2s-2.3-3.3-2.3-4.4c0-.6.3-1.1.6-1.3z"/></svg>',
    correo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4.5" width="19" height="15" rx="2"/><polyline points="3,6 12,13 21,6"/></svg>',
    ubicacion: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
  },
  v1: {
    whatsapp: '<svg class="icono" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    correo: '<svg class="icono" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
    ubicacion: '<svg class="icono icono--muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
  },
};

// ── Saneado de los datos de entrada ──────────────────────────────────────────
// Hoy los JSON los escribe quien mantiene el repo, pero la idea del proyecto es
// que cada profesional aporte su ficha (por PR o por un formulario). Desde ese
// momento data/ es entrada no confiable, y estos valores terminan dentro de
// atributos href, de un bloque <style> y de rutas de archivos que se copian a
// dist/ —que es justo lo que se publica—. Cada uno se valida contra lo que
// realmente puede ser; lo que no pasa, se descarta con un aviso en consola.

// Escapar no sirve dentro de <style>: el navegador no decodifica entidades ahí,
// y un ";" o un "}" cerrarían la declaración y dejarían inyectar reglas nuevas
// (por ejemplo un url() a un servidor externo). Por eso los colores y la
// tipografía se validan por forma, no se escapan.
const RE_COLOR = /^#[0-9a-f]{3,8}$/i;
const RE_TIPOGRAFIA = /^[\w][\w \-]{0,63}$/;

// Nombres de archivo de marcas.json: se concatenan con path.join, que resuelve
// "..", y el resultado se copia a dist/. Un nombre como "../../.git/config"
// publicaría un archivo arbitrario del repo. Solo se acepta un nombre plano.
const RE_NOMBRE_ARCHIVO = /^[\w][\w.\-]{0,127}$/;

// Esquemas admitidos en un href. Sin esta lista, un "javascript:..." en
// sitio_web o linkedin queda como enlace ejecutable en la tarjeta publicada.
const ESQUEMAS_PERMITIDOS = new Set(['https:', 'http:', 'mailto:', 'tel:']);

function avisar(contexto, mensaje) {
  console.warn(`⚠ ${contexto}: ${mensaje}`);
}

function colorSeguro(valor, porDefecto, contexto) {
  if (valor === undefined || valor === null || valor === '') return porDefecto;
  if (RE_COLOR.test(String(valor).trim())) return String(valor).trim();
  avisar(contexto, `color inválido ${JSON.stringify(valor)}, se usa ${porDefecto}.`);
  return porDefecto;
}

function tipografiaSegura(valor, porDefecto, contexto) {
  if (valor === undefined || valor === null || valor === '') return porDefecto;
  if (RE_TIPOGRAFIA.test(String(valor).trim())) return String(valor).trim();
  avisar(contexto, `tipografía inválida ${JSON.stringify(valor)}, se usa ${porDefecto}.`);
  return porDefecto;
}

function archivoSeguro(dir, nombre, contexto) {
  if (!nombre) return null;
  if (!RE_NOMBRE_ARCHIVO.test(nombre)) {
    avisar(contexto, `nombre de archivo no permitido ${JSON.stringify(nombre)}, se ignora.`);
    return null;
  }
  // Cinturón y tirantes: además de la forma del nombre, se comprueba que la ruta
  // ya resuelta siga colgando del directorio de la marca.
  const base = path.resolve(dir);
  const resuelta = path.resolve(base, nombre);
  if (!resuelta.startsWith(base + path.sep)) {
    avisar(contexto, `la ruta de ${JSON.stringify(nombre)} se sale de ${dir}, se ignora.`);
    return null;
  }
  return existsSync(resuelta) ? nombre : null;
}

function urlSegura(valor, contexto) {
  const texto = String(valor ?? '').trim();
  if (!texto) return '';
  let url;
  try {
    url = new URL(texto);
  } catch {
    avisar(contexto, `no es una URL absoluta ${JSON.stringify(texto)}, se ignora.`);
    return '';
  }
  if (!ESQUEMAS_PERMITIDOS.has(url.protocol)) {
    avisar(contexto, `esquema no permitido "${url.protocol}", se ignora.`);
    return '';
  }
  return texto;
}

// Identificadores que se concatenan dentro de una URL que arma el build. Se
// acotan a su alfabeto real para que no puedan cerrar la URL y colar otra cosa.
function usuarioSeguro(valor, contexto) {
  const texto = String(valor ?? '').trim().replace(/^@/, '');
  if (!texto) return '';
  if (/^[\w.\-]{1,64}$/.test(texto)) return texto;
  avisar(contexto, `usuario inválido ${JSON.stringify(texto)}, se ignora.`);
  return '';
}

function telefonoSeguro(valor, contexto) {
  const texto = String(valor ?? '').replace(/\D/g, '');
  if (!texto) return '';
  if (texto.length >= 7 && texto.length <= 15) return texto;
  avisar(contexto, `teléfono inválido ${JSON.stringify(valor)}, se ignora.`);
  return '';
}

function correoSeguro(valor, contexto) {
  const texto = String(valor ?? '').trim();
  if (!texto) return '';
  if (/^[^\s@,;:<>"'()[\]\\]+@[^\s@,;:<>"'()[\]\\]+\.[a-z]{2,}$/i.test(texto)) return texto;
  avisar(contexto, `correo inválido ${JSON.stringify(texto)}, se ignora.`);
  return '';
}

function pickLogoFile(dir, preferido, contexto) {
  if (!existsSync(dir)) return null;
  const elegido = archivoSeguro(dir, preferido, contexto);
  if (elegido) return elegido;
  for (const candidato of LOGOS_CANDIDATOS) {
    if (existsSync(path.join(dir, candidato))) return candidato;
  }
  // Este nombre sale de leer el directorio, no de los datos: ya es plano.
  const archivo = readdirSync(dir).find((f) => /\.(png|jpe?g|svg|webp)$/i.test(f));
  return archivo ?? null;
}

function escapeHtml(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function escapeVCard(valor) {
  return String(valor ?? '')
    .replaceAll('\\', '\\\\')
    .replaceAll(';', '\\;')
    .replaceAll(',', '\\,')
    // \r suelto o \r\n cuentan como salto: sin esto, un \r crudo cortaba la
    // línea del vCard (que se separa con CRLF) y partía el registro en dos.
    .replace(/\r\n?|\n/g, '\\n');
}

function render(plantilla, valores) {
  return plantilla.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (coincidencia, clave) =>
    clave in valores ? valores[clave] : ''
  );
}

// Los campos que viajan dentro de una URL se normalizan una sola vez, acá, y el
// resto del build ya trabaja con datos limpios. Los nombres de archivo no entran
// porque necesitan saber contra qué directorio validarse (ver archivoSeguro).
function sanearMarca(marca) {
  const contexto = `marca "${marca.id ?? marca.nombre ?? '?'}"`;
  return {
    ...marca,
    whatsapp: telefonoSeguro(marca.whatsapp, `${contexto} → whatsapp`),
    email: correoSeguro(marca.email, `${contexto} → email`),
    instagram: usuarioSeguro(marca.instagram, `${contexto} → instagram`),
    sitio_web: urlSegura(marca.sitio_web, `${contexto} → sitio_web`),
    linkedin: urlSegura(marca.linkedin, `${contexto} → linkedin`),
  };
}

function sanearPersona(persona) {
  const contexto = `persona "${persona.slug ?? persona.nombre ?? '?'}"`;
  return {
    ...persona,
    whatsapp: telefonoSeguro(persona.whatsapp, `${contexto} → whatsapp`),
    email: correoSeguro(persona.email, `${contexto} → email`),
    instagram: usuarioSeguro(persona.instagram, `${contexto} → instagram`),
    linkedin: urlSegura(persona.linkedin, `${contexto} → linkedin`),
  };
}

// El build ya sabe si el archivo del logo existe (lo comprobó pickLogoFile), así
// que emite el <img> o el texto de respaldo, nunca los dos. Antes se emitían
// ambos con un onerror inline que hacía el cambio en el navegador: eso obligaba
// a permitir scripts en línea y bloqueaba una CSP estricta.
function construirLogoHtml(marcaNombre, logoFile) {
  const nombreEscapado = escapeHtml(marcaNombre);
  if (!logoFile) {
    return `<p class="logo-fallback">${nombreEscapado}</p>`;
  }
  return `<img class="logo" src="./assets/${encodeURIComponent(logoFile)}" alt="Logo de ${nombreEscapado}">`;
}

// Fila de redes del tema v2: badge circular + etiqueta. Solo se incluyen los
// enlaces que la persona/marca realmente tenga.
function construirRedesHtml({ persona, marca }) {
  const instagram = persona.instagram || marca.instagram || '';
  const linkedin = persona.linkedin || marca.linkedin || '';
  const items = [
    marca.sitio_web && {
      href: marca.sitio_web,
      icono: 'web',
      etiqueta: sitioWebDisplay(marca.sitio_web),
      titulo: 'Sitio web',
    },
    instagram && {
      href: `https://instagram.com/${instagram}`,
      icono: 'instagram',
      etiqueta: `@${instagram}`,
      titulo: 'Instagram',
    },
    linkedin && {
      href: linkedin,
      icono: 'linkedin',
      etiqueta: 'LinkedIn',
      titulo: 'LinkedIn',
    },
  ].filter(Boolean);

  return items
    .map(
      (item) =>
        `<a class="red" href="${escapeHtml(item.href)}" target="_blank" rel="noopener" aria-label="${escapeHtml(item.titulo)}">\n` +
        `          <span class="red__badge" aria-hidden="true">${ICONOS_REDES[item.icono]}</span>\n` +
        `          <span class="red__etiqueta">${escapeHtml(item.etiqueta)}</span>\n` +
        `        </a>`
    )
    .join('\n        ');
}

// Secciones de contacto. Se arman en JS y no en la plantilla porque cada campo es
// opcional: si una persona no publica su móvil, la fila no debe existir (antes la
// plantilla la dejaba fija y quedaba un enlace wa.me/ vacío). Una sección sin
// filas desaparece completa, con su título.
//
// Todo va en un solo bloque "Empresa": partirlo en "Directo" + "Empresa" separaba
// dos cosas que el cliente vive como una sola (son todos canales de trabajo) y
// dejaba una sección de una fila. Lo que sí hay que distinguir son los dos
// correos, y eso se resuelve en la etiqueta —"profesional" el de la persona,
// "empresarial" el de la marca— en vez de con un título de sección.
//
// Solo entra acá lo que la persona haya decidido publicar: el resto (móvil o
// correo personales) se entrega aparte y de forma consentida.
function seccionesContacto({ persona, marca }) {
  const dePersona = [
    persona.whatsapp && {
      icono: 'whatsapp',
      base: 'WhatsApp',
      calificador: 'profesional',
      valor: persona.telefono_display || `+${persona.whatsapp}`,
      href: `https://wa.me/${persona.whatsapp}`,
      externo: true,
    },
    persona.email && {
      icono: 'correo',
      base: 'Correo',
      calificador: 'profesional',
      valor: persona.email,
      href: `mailto:${persona.email}`,
    },
  ].filter(Boolean);

  const deMarca = [
    marca.whatsapp && {
      icono: 'whatsapp',
      base: 'WhatsApp',
      calificador: 'empresarial',
      valor: marca.telefono_display || `+${marca.whatsapp}`,
      href: `https://wa.me/${marca.whatsapp}`,
      externo: true,
    },
    marca.email && {
      icono: 'correo',
      base: 'Correo',
      calificador: 'empresarial',
      valor: marca.email,
      href: `mailto:${marca.email}`,
    },
    marca.direccion && {
      icono: 'ubicacion',
      base: 'Oficina',
      valorHtml: direccionAHtml(marca.direccion),
      href: mapaUrl(marca.nombre, marca.direccion),
      externo: true,
      esDireccion: true,
    },
  ].filter(Boolean);

  // Orden de uso real: primero el WhatsApp (el canal por el que de verdad
  // escriben), después los dos correos juntos —así se leen uno contra otro y la
  // distinción profesional/empresarial se entiende sola— y al final la oficina.
  const orden = { whatsapp: 0, correo: 1, ubicacion: 2 };
  const filas = [...deMarca, ...dePersona].sort(
    (a, b) => orden[a.icono] - orden[b.icono] || (a.calificador === 'profesional' ? -1 : 1)
  );

  // El calificador solo aparece cuando hay dos filas del mismo tipo que
  // distinguir. Con un solo correo, "Correo" a secas se lee mejor.
  const repetidas = new Set(
    filas.map((f) => f.base).filter((base, i, todas) => todas.indexOf(base) !== i)
  );
  const empresa = filas.map((fila) => ({
    ...fila,
    etiqueta:
      repetidas.has(fila.base) && fila.calificador
        ? `${fila.base} ${fila.calificador}`
        : fila.base,
  }));

  return [{ titulo: 'Empresa', aria: 'Contacto empresa', filas: empresa }].filter(
    (seccion) => seccion.filas.length > 0
  );
}

function atributosEnlace(fila) {
  return fila.externo ? ' target="_blank" rel="noopener"' : '';
}

function valorHtml(fila) {
  return fila.valorHtml ?? escapeHtml(fila.valor);
}

function seccionesContactoHtmlV2(secciones) {
  return secciones
    .map((seccion) => {
      const filas = seccion.filas
        .map(
          (fila) =>
            `<li class="contacto${fila.esDireccion ? ' contacto--direccion' : ''}">\n` +
            `            <span class="contacto__badge" aria-hidden="true">${ICONOS_CONTACTO.v2[fila.icono]}</span>\n` +
            `            <span class="contacto__texto">\n` +
            `              <span class="contacto__etiqueta">${escapeHtml(fila.etiqueta)}</span>\n` +
            `              <a class="contacto__valor" href="${escapeHtml(fila.href)}"${atributosEnlace(fila)}>${valorHtml(fila)}</a>\n` +
            `            </span>\n` +
            `          </li>`
        )
        .join('\n          ');
      return (
        `<section class="bloque" aria-label="${escapeHtml(seccion.aria)}">\n` +
        `        <h2 class="bloque__titulo">${escapeHtml(seccion.titulo)}</h2>\n` +
        `        <ul class="contactos">\n          ${filas}\n        </ul>\n` +
        `      </section>`
      );
    })
    .join('\n\n      ');
}

function seccionesContactoHtmlV1(secciones) {
  return secciones
    .map((seccion) => {
      const filas = seccion.filas
        .map(
          (fila) =>
            `<li class="dato${fila.esDireccion ? ' dato--direccion' : ''}">\n` +
            `          ${ICONOS_CONTACTO.v1[fila.icono]}\n` +
            `          <a${fila.esDireccion ? ' class="direccion"' : ''} href="${escapeHtml(fila.href)}"${atributosEnlace(fila)}>${valorHtml(fila)}</a>\n` +
            `        </li>`
        )
        .join('\n        ');
      return (
        `<section class="seccion-contacto" aria-label="${escapeHtml(seccion.aria)}">\n` +
        `      <h2>${escapeHtml(seccion.titulo)}</h2>\n` +
        `      <ul class="datos">\n        ${filas}\n      </ul>\n` +
        `    </section>`
      );
    })
    .join('\n\n    <hr class="separador">\n\n    ');
}

function taglineHtml(tagline) {
  if (!tagline) return '';
  const partes = Array.isArray(tagline) ? tagline : [tagline];
  // Los separadores van en olivo y las palabras en claro, como el arte original.
  return partes.map((p) => escapeHtml(p)).join('<span class="sep" aria-hidden="true">•</span>');
}

function construirVCard({ persona, marca }) {
  const direccionTexto = direccionATexto(marca?.direccion);
  const instagram = persona.instagram || marca?.instagram || '';
  const linkedin = persona.linkedin || marca?.linkedin || '';
  const lineas = [
    'BEGIN:VCARD',
    'VERSION:3.0',
    `N:;${escapeVCard(persona.nombre)};;;`,
    `FN:${escapeVCard(persona.nombre)}`,
  ];
  if (marca?.nombre) lineas.push(`ORG:${escapeVCard(marca.nombre)}`);
  if (persona.cargo) lineas.push(`TITLE:${escapeVCard(persona.cargo)}`);
  // El cargo es la posición en la empresa; la profesión es aparte y en vCard va
  // en ROLE, no concatenada en TITLE (así se importa limpia en la agenda).
  if (persona.profesion) lineas.push(`ROLE:${escapeVCard(persona.profesion)}`);
  if (persona.whatsapp) lineas.push(`TEL;TYPE=CELL:+${persona.whatsapp}`);
  if (marca?.whatsapp) lineas.push(`TEL;TYPE=WORK:+${marca.whatsapp}`);
  // El vCard solo lleva lo que la tarjeta ya publica. Los datos personales
  // (móvil, correo privado) no viajan acá: se entregan aparte y de forma
  // consentida, después del primer contacto por los canales de la empresa.
  if (persona.email) lineas.push(`EMAIL;TYPE=WORK,PREF:${escapeVCard(persona.email)}`);
  if (marca?.email) lineas.push(`EMAIL;TYPE=WORK:${escapeVCard(marca.email)}`);
  if (marca?.sitio_web) lineas.push(`URL:${escapeVCard(marca.sitio_web)}`);
  if (linkedin) lineas.push(`X-SOCIALPROFILE;TYPE=linkedin:${escapeVCard(linkedin)}`);
  if (instagram) {
    lineas.push(`X-SOCIALPROFILE;TYPE=instagram:${escapeVCard(`https://instagram.com/${instagram}`)}`);
  }
  if (direccionTexto) lineas.push(`ADR;TYPE=WORK:;;${escapeVCard(direccionTexto)};;;;`);
  lineas.push('END:VCARD');
  return lineas.join('\r\n') + '\r\n';
}

function sitioWebDisplay(url) {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '');
}

// La dirección se guarda en marcas.json como array de líneas cortas (para mostrarla
// bien distribuida); esto la vuelve a juntar en un solo texto plano para el vCard y Maps.
function direccionATexto(direccion) {
  if (!direccion) return '';
  return Array.isArray(direccion) ? direccion.join(', ') : String(direccion);
}

function direccionAHtml(direccion) {
  if (!direccion) return '';
  const lineas = Array.isArray(direccion) ? direccion : [direccion];
  return lineas.map((linea) => escapeHtml(linea)).join('<br>');
}

function mapaUrl(marcaNombre, direccion) {
  const texto = direccionATexto(direccion);
  if (!texto) return '';
  const consulta = marcaNombre ? `${marcaNombre}, ${texto}` : texto;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(consulta)}`;
}

// Si no vienen nombre_pila/apellidos explícitos, se parte el nombre en dos: la
// primera palabra (y sus iniciales) arriba, el resto abajo.
function partirNombre(persona) {
  if (persona.nombre_pila || persona.apellidos) {
    return { pila: persona.nombre_pila ?? '', apellidos: persona.apellidos ?? '' };
  }
  const partes = String(persona.nombre ?? '').trim().split(/\s+/);
  if (partes.length < 2) return { pila: persona.nombre ?? '', apellidos: '' };
  const corte = partes.length > 2 ? 2 : 1;
  return { pila: partes.slice(0, corte).join(' '), apellidos: partes.slice(corte).join(' ') };
}

function listarTemas() {
  return readdirSync(TEMPLATES_DIR)
    .filter((nombre) => statSync(path.join(TEMPLATES_DIR, nombre)).isDirectory())
    .filter((nombre) => existsSync(path.join(TEMPLATES_DIR, nombre, 'card.html')))
    .sort();
}

const marcas = JSON.parse(readFileSync(path.join(DATA_DIR, 'marcas.json'), 'utf8'));
const personas = JSON.parse(readFileSync(path.join(DATA_DIR, 'personas.json'), 'utf8'));
const config = JSON.parse(readFileSync(path.join(DATA_DIR, 'config.json'), 'utf8'));
const marcasPorId = Object.fromEntries(marcas.map((m) => [m.id, sanearMarca(m)]));

const temas = listarTemas();
const temaActivo = temas.includes(config.tema) ? config.tema : TEMA_POR_DEFECTO;
if (config.tema && config.tema !== temaActivo) {
  console.warn(`⚠ config.tema "${config.tema}" no existe en templates/, se usa "${temaActivo}".`);
}

const resumen = [];

for (const personaCruda of personas) {
  const persona = sanearPersona(personaCruda);
  const marca = persona.marca_id
    ? marcasPorId[persona.marca_id]
    : persona.marca && sanearMarca(persona.marca);

  if (persona.marca_id && !marca) {
    console.warn(`⚠ ${persona.slug}: marca_id "${persona.marca_id}" no existe en marcas.json, se omite.`);
    continue;
  }
  if (!marca) {
    console.warn(`⚠ ${persona.slug}: no tiene marca_id ni marca embebida, se omite.`);
    continue;
  }

  const baseDir = path.join(DIST_DIR, persona.slug);

  // El logo real vive junto a la marca compartida, o en los assets propios
  // de la persona cuando trae su propia marca embebida (profesional independiente).
  const logoDir = persona.marca_id
    ? path.join(ASSETS_DIR, 'marcas', persona.marca_id)
    : path.join(ASSETS_DIR, 'personas', persona.slug);
  const ctxArchivos = `${persona.slug} → assets de marca`;
  const logoFile = pickLogoFile(logoDir, marca.logo, `${ctxArchivos} (logo)`);
  // Versión clara del logo, para el bloque carbón de la cabecera (tema v2).
  const logoClaroFile = archivoSeguro(logoDir, marca.logo_claro, `${ctxArchivos} (logo_claro)`);
  // Plano de fondo (lo genera scripts/generar_planos.py) que cubre el cuerpo de
  // la tarjeta a muy baja opacidad.
  const fondoPlanoFile = archivoSeguro(logoDir, marca.fondo_plano, `${ctxArchivos} (fondo_plano)`);

  const nombrePartido = partirNombre(persona);
  const ctxColores = `${persona.slug} → color`;

  const camposEscapables = {
    nombre: persona.nombre,
    cargo: persona.cargo,
    profesion: persona.profesion,
    slug: persona.slug,
    'persona.nombre_pila': nombrePartido.pila,
    'persona.apellidos': nombrePartido.apellidos,
    'persona.telefono_display': persona.telefono_display,
    'persona.whatsapp': persona.whatsapp,
    'persona.email': persona.email,
    'persona.linkedin': persona.linkedin,
    'marca.nombre': marca.nombre,
    'marca.telefono_display': marca.telefono_display,
    'marca.whatsapp': marca.whatsapp,
    'marca.email': marca.email,
    'marca.sitio_web': marca.sitio_web,
    'marca.sitio_web_display': sitioWebDisplay(marca.sitio_web),
    'marca.instagram': persona.instagram || marca.instagram || '',
    // Estos van dentro del <style> de la plantilla, donde escapar no protege:
    // se validan por forma y, si no pasan, cae el valor por defecto.
    'marca.color_oscuro': colorSeguro(marca.colores?.oscuro, '#4D4D4D', `${ctxColores} oscuro`),
    'marca.color_claro': colorSeguro(marca.colores?.claro, '#B3B3B3', `${ctxColores} claro`),
    'marca.color_fondo': colorSeguro(marca.colores?.fondo, '#FFFFFF', `${ctxColores} fondo`),
    'marca.color_carbon': colorSeguro(marca.colores_secundarios?.carbon, '#24292D', `${ctxColores} carbon`),
    'marca.color_olivo': colorSeguro(marca.colores_secundarios?.olivo, '#83855B', `${ctxColores} olivo`),
    'marca.color_olivo_texto': colorSeguro(marca.colores_secundarios?.olivo_texto, '#6B6C47', `${ctxColores} olivo_texto`),
    'marca.color_olivo_claro': colorSeguro(marca.colores_secundarios?.olivo_claro, '#A8AA7C', `${ctxColores} olivo_claro`),
    'marca.color_crema': colorSeguro(marca.colores_secundarios?.crema, '#F4F1EC', `${ctxColores} crema`),
    'marca.tipografia': tipografiaSegura(marca.tipografia, 'Montserrat', `${ctxColores} tipografia`),
  };
  const valoresBase = Object.fromEntries(
    Object.entries(camposEscapables).map(([clave, valor]) => [clave, escapeHtml(valor)])
  );
  valoresBase.logo_html = construirLogoHtml(marca.nombre, logoFile);
  valoresBase.logo_claro_html = construirLogoHtml(marca.nombre, logoClaroFile ?? logoFile);
  valoresBase.redes_html = construirRedesHtml({ persona, marca });

  const seccionesDeContacto = seccionesContacto({ persona, marca });
  const contactosHtmlPorTema = {
    v1: seccionesContactoHtmlV1(seccionesDeContacto),
    v2: seccionesContactoHtmlV2(seccionesDeContacto),
  };
  valoresBase['marca.tagline_html'] = taglineHtml(marca.tagline);
  valoresBase['marca.direccion_html'] = direccionAHtml(marca.direccion);
  valoresBase['marca.mapa_url'] = escapeHtml(mapaUrl(marca.nombre, marca.direccion));

  // Cargo y profesión van en la misma línea separados por una barra. Se arma aquí
  // y no en la plantilla porque la barra solo debe aparecer si existen los dos.
  const cargoPartes = [persona.cargo, persona.profesion].filter(Boolean);
  valoresBase.cargo_texto = escapeHtml(cargoPartes.join(' | '));
  valoresBase.cargo_html = cargoPartes
    .map((parte) => `<span class="identidad__cargo-parte">${escapeHtml(parte)}</span>`)
    .join('<span class="identidad__sep" aria-hidden="true">|</span>');
  valoresBase.logo_marca_css = [
    logoFile ? `--logo-marca: url('./assets/${encodeURIComponent(logoFile)}');` : '',
    fondoPlanoFile ? `--fondo-plano: url('./assets/${encodeURIComponent(fondoPlanoFile)}');` : '',
  ]
    .filter(Boolean)
    .join('\n    ');

  const archivosGenerados = [];

  for (const tema of temas) {
    const esActivo = tema === temaActivo;
    const outDir = esActivo ? baseDir : path.join(baseDir, tema);
    const assetsOutDir = path.join(outDir, 'assets');
    mkdirSync(assetsOutDir, { recursive: true });

    for (const archivo of [logoFile, logoClaroFile, fondoPlanoFile].filter(Boolean)) {
      copyFileSync(path.join(logoDir, archivo), path.join(assetsOutDir, archivo));
    }

    // qr.png, contacto.vcf, tarjeta-whatsapp.png y la fuente se generan o copian
    // una sola vez, en la raíz de la persona; los temas secundarios los apuntan
    // un nivel arriba. De ahí que style.css también pase por render(): necesita
    // base_recursos para el @font-face.
    const valores = {
      ...valoresBase,
      base_recursos: esActivo ? './' : '../',
      contactos_html: contactosHtmlPorTema[tema] ?? contactosHtmlPorTema.v2,
    };

    const cardTemplate = readFileSync(path.join(TEMPLATES_DIR, tema, 'card.html'), 'utf8');
    writeFileSync(path.join(outDir, 'index.html'), render(cardTemplate, valores));
    const styleTemplate = readFileSync(path.join(TEMPLATES_DIR, tema, 'style.css'), 'utf8');
    writeFileSync(path.join(outDir, 'style.css'), render(styleTemplate, valores));

    const prefijo = esActivo ? '' : `${tema}/`;
    archivosGenerados.push(
      `${prefijo}index.html${esActivo ? `   ← tema activo (${tema})` : ''}`,
      `${prefijo}style.css`
    );
  }

  writeFileSync(path.join(baseDir, 'contacto.vcf'), construirVCard({ persona, marca }));
  archivosGenerados.push('contacto.vcf');

  if (existsSync(FUENTE_ORIGEN)) {
    copyFileSync(FUENTE_ORIGEN, path.join(baseDir, 'assets', FUENTE_ARCHIVO));
    archivosGenerados.push(`assets/${FUENTE_ARCHIVO}`);
  } else {
    console.warn(`⚠ falta ${FUENTE_ORIGEN}: la tarjeta caerá a la sans-serif del sistema.`);
  }

  resumen.push({
    slug: persona.slug,
    nombre: persona.nombre,
    marca: marca.nombre,
    logo: logoFile,
    archivos: archivosGenerados,
  });
}

// La raíz del sitio publicado no es una tarjeta: con una sola persona redirige a
// ella, y con varias lista las disponibles. Sin esto, entrar a la raíz da 404.
const destinoRaiz = resumen.length === 1 ? `./${resumen[0].slug}/` : null;
writeFileSync(
  path.join(DIST_DIR, 'index.html'),
  destinoRaiz
    ? `<!doctype html>
<html lang="es">
<meta charset="utf-8">
<title>Tarjetas de presentación</title>
<meta http-equiv="refresh" content="0; url=${destinoRaiz}">
<link rel="canonical" href="${destinoRaiz}">
<p>Redirigiendo a <a href="${destinoRaiz}">${resumen[0].nombre}</a>…</p>
</html>
`
    : `<!doctype html>
<html lang="es">
<meta charset="utf-8">
<title>Tarjetas de presentación</title>
<h1>Tarjetas de presentación</h1>
<ul>
${resumen.map((item) => `  <li><a href="./${item.slug}/">${escapeHtml(item.nombre)} — ${escapeHtml(item.marca)}</a></li>`).join('\n')}
</ul>
</html>
`
);

// GitHub Pages procesa el sitio con Jekyll si no encuentra este archivo, y Jekyll
// ignora todo lo que empiece por guion bajo.
writeFileSync(path.join(DIST_DIR, '.nojekyll'), '');

// Refuerza el noindex de las plantillas a nivel de sitio. No es una medida de
// seguridad —quien tenga el enlace entra igual— pero evita que los datos de
// contacto terminen en buscadores y en los raspadores que sí respetan el
// archivo. Lo que no debe ser público, simplemente no se pone en data/.
writeFileSync(
  path.join(DIST_DIR, 'robots.txt'),
  ['User-agent: *', 'Disallow: /', ''].join('\n')
);

console.log('\nResumen de generación:\n');
for (const item of resumen) {
  console.log(`• ${item.slug} (${item.nombre} — ${item.marca})`);
  for (const archivo of item.archivos) {
    console.log(`    dist/${item.slug}/${archivo}`);
  }
  if (!item.logo) {
    console.log('    ⚠ sin logo encontrado en assets/, se usará el fallback de texto en la tarjeta');
  }
}
console.log(`\n${resumen.length} tarjeta(s) generada(s) en dist/  ·  temas: ${temas.join(', ')}`);
