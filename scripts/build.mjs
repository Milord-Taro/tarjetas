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

function pickLogoFile(dir, preferido) {
  if (!existsSync(dir)) return null;
  if (preferido && existsSync(path.join(dir, preferido))) return preferido;
  for (const candidato of LOGOS_CANDIDATOS) {
    if (existsSync(path.join(dir, candidato))) return candidato;
  }
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
    .replaceAll('\n', '\\n');
}

function render(plantilla, valores) {
  return plantilla.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (coincidencia, clave) =>
    clave in valores ? valores[clave] : ''
  );
}

function construirLogoHtml(marcaNombre, logoFile) {
  const nombreEscapado = escapeHtml(marcaNombre);
  if (!logoFile) {
    return `<p class="logo-fallback">${nombreEscapado}</p>`;
  }
  return (
    `<img class="logo" src="./assets/${escapeHtml(logoFile)}" alt="Logo de ${nombreEscapado}" ` +
    `onerror="this.hidden=true;this.nextElementSibling.hidden=false;">\n        ` +
    `<p class="logo-fallback" hidden>${nombreEscapado}</p>`
  );
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
  if (persona.whatsapp) lineas.push(`TEL;TYPE=CELL:+${persona.whatsapp}`);
  if (marca?.whatsapp) lineas.push(`TEL;TYPE=WORK:+${marca.whatsapp}`);
  if (persona.email) lineas.push(`EMAIL:${escapeVCard(persona.email)}`);
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
const marcasPorId = Object.fromEntries(marcas.map((m) => [m.id, m]));

const temas = listarTemas();
const temaActivo = temas.includes(config.tema) ? config.tema : TEMA_POR_DEFECTO;
if (config.tema && config.tema !== temaActivo) {
  console.warn(`⚠ config.tema "${config.tema}" no existe en templates/, se usa "${temaActivo}".`);
}

const resumen = [];

for (const persona of personas) {
  const marca = persona.marca_id ? marcasPorId[persona.marca_id] : persona.marca;

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
  const logoFile = pickLogoFile(logoDir, marca.logo);
  // Versión clara del logo, para el bloque carbón de la cabecera (tema v2).
  const logoClaroFile =
    marca.logo_claro && existsSync(path.join(logoDir, marca.logo_claro)) ? marca.logo_claro : null;
  // Plano de fondo (lo genera scripts/generar_planos.py) que cubre el cuerpo de
  // la tarjeta a muy baja opacidad.
  const fondoPlanoFile =
    marca.fondo_plano && existsSync(path.join(logoDir, marca.fondo_plano)) ? marca.fondo_plano : null;

  const nombrePartido = partirNombre(persona);

  const camposEscapables = {
    nombre: persona.nombre,
    cargo: persona.cargo,
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
    'marca.color_oscuro': marca.colores?.oscuro ?? '#4D4D4D',
    'marca.color_claro': marca.colores?.claro ?? '#B3B3B3',
    'marca.color_fondo': marca.colores?.fondo ?? '#FFFFFF',
    'marca.color_carbon': marca.colores_secundarios?.carbon ?? '#24292D',
    'marca.color_olivo': marca.colores_secundarios?.olivo ?? '#83855B',
    'marca.color_olivo_texto': marca.colores_secundarios?.olivo_texto ?? '#6B6C47',
    'marca.color_olivo_claro': marca.colores_secundarios?.olivo_claro ?? '#A8AA7C',
    'marca.color_crema': marca.colores_secundarios?.crema ?? '#F4F1EC',
    'marca.tipografia': marca.tipografia ?? 'Montserrat',
  };
  const valoresBase = Object.fromEntries(
    Object.entries(camposEscapables).map(([clave, valor]) => [clave, escapeHtml(valor)])
  );
  valoresBase.logo_html = construirLogoHtml(marca.nombre, logoFile);
  valoresBase.logo_claro_html = construirLogoHtml(marca.nombre, logoClaroFile ?? logoFile);
  valoresBase.redes_html = construirRedesHtml({ persona, marca });
  valoresBase['marca.tagline_html'] = taglineHtml(marca.tagline);
  valoresBase['marca.direccion_html'] = direccionAHtml(marca.direccion);
  valoresBase['marca.mapa_url'] = escapeHtml(mapaUrl(marca.nombre, marca.direccion));
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

    // qr.png, contacto.vcf y tarjeta-whatsapp.png se generan una sola vez, en la
    // raíz de la persona; los temas secundarios los apuntan un nivel arriba.
    const valores = { ...valoresBase, base_recursos: esActivo ? './' : '../' };

    const cardTemplate = readFileSync(path.join(TEMPLATES_DIR, tema, 'card.html'), 'utf8');
    writeFileSync(path.join(outDir, 'index.html'), render(cardTemplate, valores));
    copyFileSync(path.join(TEMPLATES_DIR, tema, 'style.css'), path.join(outDir, 'style.css'));

    const prefijo = esActivo ? '' : `${tema}/`;
    archivosGenerados.push(
      `${prefijo}index.html${esActivo ? `   ← tema activo (${tema})` : ''}`,
      `${prefijo}style.css`
    );
  }

  writeFileSync(path.join(baseDir, 'contacto.vcf'), construirVCard({ persona, marca }));
  archivosGenerados.push('contacto.vcf');

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
