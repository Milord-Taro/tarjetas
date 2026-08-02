// Esquema de data/*.json y su validador.
//
// Este archivo es la única fuente de verdad sobre "qué forma puede tener un
// dato". build.mjs importa las expresiones regulares para sus saneadores, y
// corre validarDatos() antes de generar nada. También se puede correr solo:
//
//     node scripts/validar.mjs
//
// ── Por qué no JSON Schema + ajv ────────────────────────────────────────────
// El esquema son dos objetos y unos veinticinco campos; ajv arrastra un árbol
// de dependencias a un repo que hoy tiene cero. El proyecto se sostiene sobre
// que todo lo que corre es auditable de una sentada, y añadir un node_modules
// para validar veinticinco campos cambia esa relación a cambio de poco. Si el
// esquema crece hasta que esto duela, la migración es directa: la tabla de
// CAMPOS_* de abajo mapea uno a uno a "properties" + "required" +
// "additionalProperties: false".
//
// ── Dos severidades ─────────────────────────────────────────────────────────
// · dura   → el build falla. Son los campos que deciden identidad y rutas de
//            archivo (slug, id, marca_id, nombres de archivo). Un valor raro
//            acá no es una tarjeta fea: es un archivo escrito donde no va, o la
//            ficha de alguien publicada bajo el nombre de otro.
// · blanda → el build avisa y cae al valor por defecto. Son los campos de
//            contenido (colores, teléfonos, enlaces). Que una marca escriba mal
//            su color no debería impedir publicar al resto.

// ── Formas admitidas ────────────────────────────────────────────────────────

// Segmento de URL y nombre de carpeta dentro de dist/. Sin mayúsculas, sin
// tildes y sin puntos: el slug viaja en el QR impreso, se dicta por teléfono y
// se teclea a mano.
export const RE_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

// Identificador de marca. Mismas reglas que el slug: también es un nombre de
// carpeta (assets/marcas/<id>/).
export const RE_ID_MARCA = RE_SLUG;

// Nombres que no pueden ser slug porque chocan con algo que el build ya escribe
// en la raíz de dist/, o con la convención dist/{slug}/{tema}/ de los temas
// secundarios. Los temas se añaden en tiempo de ejecución (ver validarDatos).
export const SLUGS_RESERVADOS = new Set([
  'index', 'assets', 'robots', 'sitemap', 'favicon', 'css', 'js', 'api',
]);

export const RE_COLOR = /^#(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
export const RE_TIPOGRAFIA = /^[\w][\w \-]{0,63}$/;
export const RE_NOMBRE_ARCHIVO = /^[\w][\w.\-]{0,127}$/;
export const RE_USUARIO = /^[\w.\-]{1,64}$/;
export const RE_CORREO = /^[^\s@,;:<>"'()[\]\\]+@[^\s@,;:<>"'()[\]\\]+\.[a-z]{2,}$/i;
export const ESQUEMAS_PERMITIDOS = new Set(['https:', 'http:', 'mailto:', 'tel:']);

// ── Tabla de campos ─────────────────────────────────────────────────────────
// tipo: cómo se comprueba · dura: si falla, el build no publica.

const TEXTO = { tipo: 'texto', max: 200 };
const ARCHIVO_BLANDO = { tipo: 'archivo' };
// Los nombres de archivo son duros aunque parezcan contenido: se concatenan con
// path.join y el resultado se copia a dist/, que es exactamente lo que se
// publica. Ver archivoSeguro() en build.mjs.
const ARCHIVO = { tipo: 'archivo', dura: true };

const CAMPOS_PERSONA = {
  slug: { tipo: 'slug', obligatorio: true, dura: true },
  // Duro: un nombre ausente reventaba con un stack de Node, pero uno en blanco
  // era peor —publicaba la tarjeta con el hueco del nombre vacío y sin avisar—.
  nombre: { ...TEXTO, obligatorio: true, min: 1, dura: true },
  nombre_pila: TEXTO,
  apellidos: TEXTO,
  cargo: TEXTO,
  profesion: TEXTO,
  marca_id: { tipo: 'id', dura: true },
  marca: { tipo: 'marca_embebida', dura: true },
  email: { tipo: 'correo' },
  whatsapp: { tipo: 'telefono' },
  telefono_display: TEXTO,
  instagram: { tipo: 'usuario' },
  linkedin: { tipo: 'url' },
  linkedin_display: TEXTO,
  // Todavía no se renderiza en ningún lado; se admite para no romper las fichas
  // que ya lo traen. Antes de usarlo hay que resolver el EXIF (una foto trae
  // GPS y serial de cámara, y eso no se ve en el diff de un PR).
  foto: { tipo: 'archivo_o_nulo', dura: true },
  // Aparecer en el índice de la raíz es opcional y por defecto no. Con una sola
  // persona la raíz redirige a su tarjeta y da igual, pero con varias se
  // convierte en un directorio de nombres y marcas en una URL adivinable, que
  // es una pieza distinta de la que cada quien reparte por QR.
  listar_en_indice: { tipo: 'booleano' },
};

const CAMPOS_MARCA = {
  id: { tipo: 'id', obligatorio: true, dura: true },
  // Duro: un nombre ausente reventaba con un stack de Node, pero uno en blanco
  // era peor —publicaba la tarjeta con el hueco del nombre vacío y sin avisar—.
  nombre: { ...TEXTO, obligatorio: true, min: 1, dura: true },
  tagline: { tipo: 'lineas' },
  // Roles, no nombres de color: cada marca los rellena con los suyos y las
  // plantillas se escriben una sola vez. Los tres primeros son obligatorios de
  // hecho (hay valor por defecto para todos); apoyo y acento son opcionales y
  // los usan las plantillas que los pidan.
  colores: { tipo: 'colores', claves: ['oscuro', 'claro', 'fondo', 'apoyo', 'acento'] },
  // Qué proporción de la pieza debería ocupar cada rol, según el manual. No lo
  // usa el build: lo lee scripts/comparar_temas.py para contrastar el objetivo
  // con el reparto que de verdad tiene la tarjeta.
  uso_paleta: { tipo: 'uso_paleta' },
  colores_secundarios: {
    tipo: 'colores',
    claves: ['carbon', 'olivo', 'olivo_texto', 'olivo_claro', 'crema'],
  },
  tipografia: { tipo: 'tipografia' },
  logo: ARCHIVO,
  logo_claro: ARCHIVO,
  logo_emblema: ARCHIVO,
  ilustracion: ARCHIVO_BLANDO,
  ilustracion_png: ARCHIVO_BLANDO,
  fondo_plano: ARCHIVO,
  fondo_plano_png: ARCHIVO,
  telefono_display: TEXTO,
  whatsapp: { tipo: 'telefono' },
  email: { tipo: 'correo' },
  instagram: { tipo: 'usuario' },
  linkedin: { tipo: 'url' },
  sitio_web: { tipo: 'url' },
  direccion: { tipo: 'lineas' },
  // Dominios de correo de la marca. Opcional, pero si está, los correos de la
  // marca y de su gente tienen que caer ahí: atrapa el dedazo en el dominio y,
  // sobre todo, el correo de otra marca pegado en la ficha equivocada, que en
  // un repo con varias marcas es un error fácil de cometer y difícil de ver.
  dominios_correo: { tipo: 'dominios' },
};

const CAMPOS_CONFIG = {
  // base_url termina grabado dentro del QR impreso. Si sale mal, el material ya
  // impreso apunta a otra parte y no hay forma de corregirlo a posteriori.
  base_url: { tipo: 'url_publica', obligatorio: true, dura: true },
  tema: { tipo: 'texto', max: 64 },
};

// ── Comprobaciones por tipo ─────────────────────────────────────────────────
// Cada una devuelve null si el valor está bien, o el motivo del rechazo.

const COMPROBACIONES = {
  texto: (valor, campo) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    if (campo.min && valor.trim().length < campo.min) return 'no puede estar vacío';
    if (campo.max && valor.length > campo.max) return `no puede pasar de ${campo.max} caracteres`;
    return null;
  },
  slug: (valor) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    if (valor.length < 3 || valor.length > 40) return 'debe medir entre 3 y 40 caracteres';
    if (!RE_SLUG.test(valor)) {
      return 'solo minúsculas sin tildes, dígitos y guiones simples (ej. "daniel-manotas")';
    }
    return null;
  },
  id: (valor) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    if (!RE_ID_MARCA.test(valor)) {
      return 'solo minúsculas sin tildes, dígitos y guiones simples (ej. "topp-create")';
    }
    return null;
  },
  archivo: (valor) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    if (!RE_NOMBRE_ARCHIVO.test(valor)) {
      return 'debe ser un nombre de archivo plano, sin "/" ni ".."';
    }
    return null;
  },
  archivo_o_nulo: (valor, campo) =>
    valor === null ? null : COMPROBACIONES.archivo(valor, campo),
  correo: (valor) =>
    typeof valor === 'string' && RE_CORREO.test(valor.trim()) ? null : 'no parece un correo',
  usuario: (valor) =>
    typeof valor === 'string' && RE_USUARIO.test(String(valor).replace(/^@/, ''))
      ? null
      : 'no parece un usuario de red social',
  telefono: (valor) => {
    const digitos = String(valor ?? '').replace(/\D/g, '');
    return digitos.length >= 7 && digitos.length <= 15
      ? null
      : 'debe tener entre 7 y 15 dígitos, con indicativo de país';
  },
  // Dos formas: "Montserrat" (la familia a secas, cae a la sans del sistema si
  // no hay archivo) o el objeto completo, que es lo que hace falta para servir
  // la fuente de la marca desde el propio sitio.
  //
  // `licencia` es obligatoria cuando hay `archivo`, y no es burocracia:
  // autoalojar un .ttf en un sitio público es redistribuirlo. Montserrat es OFL
  // y no hay problema, pero una fuente de fundición necesita licencia webfont
  // y eso no se ve mirando el archivo.
  tipografia: (valor, campo, ruta, errores) => {
    if (typeof valor === 'string') {
      return RE_TIPOGRAFIA.test(valor.trim()) ? null : 'solo el nombre de la familia, alfanumérico';
    }
    if (typeof valor !== 'object' || valor === null || Array.isArray(valor)) {
      return 'debe ser el nombre de la familia o un objeto { familia, archivo, licencia }';
    }
    const conocidas = ['familia', 'archivo', 'licencia'];
    for (const clave of Object.keys(valor)) {
      if (!conocidas.includes(clave)) {
        errores.push({ ruta: `${ruta}.${clave}`, mensaje: 'campo desconocido', dura: true });
      }
    }
    if (!valor.familia || !RE_TIPOGRAFIA.test(String(valor.familia).trim())) {
      errores.push({ ruta: `${ruta}.familia`, mensaje: 'falta o no es un nombre de familia', dura: true });
    }
    if (valor.archivo !== undefined) {
      if (!RE_NOMBRE_ARCHIVO.test(String(valor.archivo))) {
        errores.push({ ruta: `${ruta}.archivo`, mensaje: 'debe ser un nombre plano, sin "/" ni ".."', dura: true });
      }
      if (!valor.licencia) {
        errores.push({
          ruta: `${ruta}.licencia`,
          mensaje:
            'hace falta declararla: servir la fuente desde el sitio es redistribuirla, ' +
            'y no toda licencia de escritorio lo permite (ej. "OFL-1.1")',
          dura: true,
        });
      }
    }
    return null;
  },
  url: (valor) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    let url;
    try {
      url = new URL(valor.trim());
    } catch {
      return 'debe ser una URL absoluta (con https://)';
    }
    return ESQUEMAS_PERMITIDOS.has(url.protocol) ? null : `esquema no permitido "${url.protocol}"`;
  },
  url_publica: (valor) => {
    if (typeof valor !== 'string') return `debe ser texto, no ${tipoDe(valor)}`;
    let url;
    try {
      url = new URL(valor.trim());
    } catch {
      return 'debe ser una URL absoluta (con https://)';
    }
    return url.protocol === 'https:' ? null : 'debe ser https';
  },
  uso_paleta: (valor, campo, ruta, errores) => {
    if (typeof valor !== 'object' || valor === null || Array.isArray(valor)) {
      return 'debe ser un objeto de rol → porcentaje';
    }
    const roles = ['oscuro', 'claro', 'fondo', 'apoyo', 'acento'];
    for (const [rol, pct] of Object.entries(valor)) {
      if (!roles.includes(rol)) {
        errores.push({ ruta: `${ruta}.${rol}`, mensaje: 'rol de color desconocido', dura: false });
      } else if (!Number.isFinite(pct) || pct < 0 || pct > 100) {
        errores.push({ ruta: `${ruta}.${rol}`, mensaje: 'debe ser un porcentaje entre 0 y 100', dura: false });
      }
    }
    return null;
  },
  booleano: (valor) => (typeof valor === 'boolean' ? null : 'debe ser true o false'),
  dominios: (valor) => {
    if (!Array.isArray(valor) || valor.length === 0) return 'debe ser una lista de dominios';
    return valor.every((d) => typeof d === 'string' && /^[a-z0-9.\-]+\.[a-z]{2,}$/i.test(d))
      ? null
      : 'cada entrada debe ser un dominio (ej. "toppcreate.com")';
  },
  lineas: (valor) => {
    const partes = Array.isArray(valor) ? valor : [valor];
    if (partes.length > 8) return 'no puede pasar de 8 líneas';
    return partes.every((p) => typeof p === 'string' && p.length <= 200)
      ? null
      : 'debe ser un texto o una lista de textos cortos';
  },
  colores: (valor, campo, ruta, errores) => {
    if (typeof valor !== 'object' || valor === null || Array.isArray(valor)) {
      return `debe ser un objeto con ${campo.claves.join(', ')}`;
    }
    for (const [clave, color] of Object.entries(valor)) {
      if (!campo.claves.includes(clave)) {
        errores.push({ ruta: `${ruta}.${clave}`, mensaje: 'clave de color desconocida', dura: false });
      } else if (!RE_COLOR.test(String(color).trim())) {
        errores.push({ ruta: `${ruta}.${clave}`, mensaje: 'no es un color hex', dura: false });
      }
    }
    return null;
  },
  // Marca escrita dentro de la ficha, para un profesional independiente que no
  // comparte marca con nadie. Se valida con la misma tabla que marcas.json.
  marca_embebida: (valor, campo, ruta, errores) => {
    if (typeof valor !== 'object' || valor === null || Array.isArray(valor)) {
      return 'debe ser un objeto con los datos de la marca';
    }
    validarObjeto(valor, CAMPOS_MARCA, ruta, errores);
    return null;
  },
};

function tipoDe(valor) {
  if (valor === null) return 'null';
  return Array.isArray(valor) ? 'una lista' : typeof valor;
}

function validarObjeto(objeto, campos, ruta, errores) {
  for (const [clave, campo] of Object.entries(campos)) {
    if (campo.obligatorio && (objeto[clave] === undefined || objeto[clave] === null)) {
      errores.push({ ruta: `${ruta}.${clave}`, mensaje: 'falta y es obligatorio', dura: true });
    }
  }

  for (const [clave, valor] of Object.entries(objeto)) {
    const campo = campos[clave];
    // El equivalente de additionalProperties:false. Es la mitad del valor de
    // tener esquema: sin esto, una ficha puede traer campos que nadie revisó y
    // que igual quedan publicados en data/ y en el historial del repo.
    if (!campo) {
      errores.push({
        ruta: `${ruta}.${clave}`,
        mensaje: `campo desconocido; los admitidos son: ${Object.keys(campos).join(', ')}`,
        dura: true,
      });
      continue;
    }
    // Ausente u opcional-vacío: ya se comprobó arriba si era obligatorio.
    if (valor === undefined || (valor === null && campo.tipo !== 'archivo_o_nulo')) continue;
    if (valor === '' && !campo.obligatorio) continue;

    const motivo = COMPROBACIONES[campo.tipo](valor, campo, `${ruta}.${clave}`, errores);
    if (motivo) {
      errores.push({ ruta: `${ruta}.${clave}`, mensaje: motivo, dura: Boolean(campo.dura) });
    }
  }
}

/**
 * Valida los tres JSON de data/ como un conjunto: además de la forma de cada
 * campo comprueba lo que solo se ve mirando todo junto (slugs repetidos,
 * marca_id que no existe, slug que choca con un nombre de tema).
 *
 * Devuelve { errores, avisos }: `errores` son los duros —el build no debe
 * publicar— y `avisos` los blandos, que el build resuelve cayendo al valor por
 * defecto.
 */
export function validarDatos({ marcas, personas, config, temas = [] }) {
  const encontrados = [];

  if (!Array.isArray(marcas)) {
    encontrados.push({ ruta: 'marcas.json', mensaje: 'debe ser una lista de marcas', dura: true });
  }
  if (!Array.isArray(personas)) {
    encontrados.push({ ruta: 'personas.json', mensaje: 'debe ser una lista de personas', dura: true });
  }
  if (typeof config !== 'object' || config === null || Array.isArray(config)) {
    encontrados.push({ ruta: 'config.json', mensaje: 'debe ser un objeto', dura: true });
  }
  if (encontrados.length) return separar(encontrados);

  validarObjeto(config, CAMPOS_CONFIG, 'config.json', encontrados);

  // Comprueba que un correo caiga en los dominios que declaró su marca.
  const revisarDominio = (correo, dominios, ruta) => {
    if (!dominios || typeof correo !== 'string' || !correo.includes('@')) return;
    const dominio = correo.split('@').pop().toLowerCase();
    if (!dominios.some((d) => d.toLowerCase() === dominio)) {
      encontrados.push({
        ruta,
        mensaje: `"${dominio}" no está entre los dominios de la marca (${dominios.join(', ')})`,
        dura: true,
      });
    }
  };

  const idsVistos = new Set();
  const marcasPorId = new Map();
  marcas.forEach((marca, i) => {
    const ruta = `marcas.json[${i}]${marca?.id ? ` (${marca.id})` : ''}`;
    if (typeof marca !== 'object' || marca === null || Array.isArray(marca)) {
      encontrados.push({ ruta, mensaje: 'debe ser un objeto', dura: true });
      return;
    }
    validarObjeto(marca, CAMPOS_MARCA, ruta, encontrados);
    if (typeof marca.id === 'string') {
      if (idsVistos.has(marca.id)) {
        encontrados.push({ ruta: `${ruta}.id`, mensaje: `"${marca.id}" está repetido`, dura: true });
      }
      idsVistos.add(marca.id);
      marcasPorId.set(marca.id, marca);
    }
    revisarDominio(marca.email, marca.dominios_correo, `${ruta}.email`);
  });

  // Un slug igual a un nombre de tema chocaría con dist/{slug}/{tema}/.
  const reservados = new Set([...SLUGS_RESERVADOS, ...temas]);
  const slugsVistos = new Map();

  personas.forEach((persona, i) => {
    const ruta = `personas.json[${i}]${persona?.slug ? ` (${persona.slug})` : ''}`;
    if (typeof persona !== 'object' || persona === null || Array.isArray(persona)) {
      encontrados.push({ ruta, mensaje: 'debe ser un objeto', dura: true });
      return;
    }
    validarObjeto(persona, CAMPOS_PERSONA, ruta, encontrados);

    if (typeof persona.slug === 'string' && RE_SLUG.test(persona.slug)) {
      if (reservados.has(persona.slug)) {
        encontrados.push({
          ruta: `${ruta}.slug`,
          mensaje: `"${persona.slug}" es un nombre reservado (choca con algo que el build ya escribe en dist/)`,
          dura: true,
        });
      }
      // Dos fichas con el mismo slug se pisaban en silencio: ganaba la última y
      // el índice seguía enlazando a la primera por su nombre. Es un cruce de
      // datos entre dos titulares distintos, así que falla.
      if (slugsVistos.has(persona.slug)) {
        encontrados.push({
          ruta: `${ruta}.slug`,
          mensaje: `"${persona.slug}" ya lo usa ${slugsVistos.get(persona.slug)}`,
          dura: true,
        });
      }
      slugsVistos.set(persona.slug, ruta);
    }

    const tieneId = typeof persona.marca_id === 'string';
    if (tieneId && !idsVistos.has(persona.marca_id)) {
      encontrados.push({
        ruta: `${ruta}.marca_id`,
        mensaje: `"${persona.marca_id}" no existe en marcas.json`,
        dura: true,
      });
    }
    if (!tieneId && !persona.marca) {
      encontrados.push({
        ruta: `${ruta}.marca_id`,
        mensaje: 'la ficha necesita marca_id o una marca embebida',
        dura: true,
      });
    }
    if (tieneId && persona.marca) {
      encontrados.push({
        ruta: `${ruta}.marca`,
        mensaje: 'trae marca_id y marca embebida a la vez; deja solo uno',
        dura: true,
      });
    }

    const suMarca = tieneId ? marcasPorId.get(persona.marca_id) : persona.marca;
    revisarDominio(persona.email, suMarca?.dominios_correo, `${ruta}.email`);
  });

  return separar(encontrados);
}

function separar(encontrados) {
  return {
    errores: encontrados.filter((e) => e.dura),
    avisos: encontrados.filter((e) => !e.dura),
  };
}

export function formatear({ errores, avisos }) {
  return [
    ...avisos.map((a) => `⚠ ${a.ruta}: ${a.mensaje}`),
    ...errores.map((e) => `✗ ${e.ruta}: ${e.mensaje}`),
  ];
}

// ── Uso directo: node scripts/validar.mjs ───────────────────────────────────
if (import.meta.url === `file://${process.argv[1]}`) {
  const { readFileSync, readdirSync, existsSync, statSync } = await import('node:fs');
  const path = (await import('node:path')).default;
  const { fileURLToPath } = await import('node:url');

  const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const leer = (nombre) => {
    try {
      return JSON.parse(readFileSync(path.join(ROOT, 'data', nombre), 'utf8'));
    } catch (error) {
      console.error(`✗ data/${nombre}: ${error.message}`);
      process.exit(1);
    }
  };

  const temasDir = path.join(ROOT, 'templates');
  const temas = existsSync(temasDir)
    ? readdirSync(temasDir).filter((n) => statSync(path.join(temasDir, n)).isDirectory())
    : [];

  const resultado = validarDatos({
    marcas: leer('marcas.json'),
    personas: leer('personas.json'),
    config: leer('config.json'),
    temas,
  });

  for (const linea of formatear(resultado)) console.log(linea);

  if (resultado.errores.length) {
    console.error(`\n✗ ${resultado.errores.length} error(es): data/ no está en condiciones de publicarse.`);
    process.exit(1);
  }
  console.log(`✓ data/ válido${resultado.avisos.length ? ` (${resultado.avisos.length} aviso(s))` : ''}.`);
}
