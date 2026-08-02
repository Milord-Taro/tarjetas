// Casos hostiles y casos raros del esquema.
//
// Cada bloque de este archivo salió de un hallazgo real de la segunda
// auditoría: son regresiones, no ejercicios. Si alguno vuelve a pasar en verde
// habiendo quitado la validación, es que el agujero volvió.
//
//     node --test test/
import test from 'node:test';
import assert from 'node:assert/strict';
import { validarDatos } from '../scripts/validar.mjs';

const MARCA = { id: 'topp-create', nombre: 'TOPP CREATE' };
const CONFIG = { base_url: 'https://milord-taro.github.io/tarjetas', tema: 'v2' };

// Arma un data/ completo con las fichas que se le pasen.
function validar(personas, extra = {}) {
  return validarDatos({
    marcas: [MARCA],
    personas,
    config: CONFIG,
    temas: ['v1', 'v2'],
    ...extra,
  });
}

const ficha = (campos) => ({ slug: 'ana-perez', nombre: 'Ana Pérez', marca_id: 'topp-create', ...campos });

function rutasConError({ errores }) {
  return errores.map((e) => e.ruta);
}

test('la ficha de ejemplo pasa limpia', () => {
  const resultado = validar([ficha({})]);
  assert.deepEqual(resultado.errores, []);
});

test('rechaza un slug con "..": escribía archivos fuera de dist/', () => {
  for (const slug of ['../../etc/passwd', '../fuera', 'a/b', './x']) {
    const { errores } = validar([ficha({ slug })]);
    assert.ok(
      errores.some((e) => e.ruta.endsWith('.slug')),
      `el slug ${JSON.stringify(slug)} debería rechazarse`
    );
  }
});

test('rechaza un slug con HTML: quedaba como <script> en dist/index.html', () => {
  const { errores } = validar([ficha({ slug: 'a"><script>alert(1)</script>' })]);
  assert.ok(errores.some((e) => e.ruta.endsWith('.slug')));
});

test('rechaza un marca_id con "..": copiaba imágenes del disco a la web', () => {
  const { errores } = validar([ficha({ marca_id: '../../../PRIVADO' })]);
  // Cae por forma y por referencia inexistente; basta con que no pase.
  assert.ok(errores.some((e) => e.ruta.endsWith('.marca_id')));
});

test('rechaza un nombre de archivo con ruta', () => {
  const marcas = [{ ...MARCA, logo: '../../../.git/config' }];
  const { errores } = validarDatos({ marcas, personas: [ficha({})], config: CONFIG });
  assert.ok(errores.some((e) => e.ruta.endsWith('.logo')));
});

test('rechaza slugs repetidos: la segunda ficha pisaba a la primera', () => {
  const { errores } = validar([
    ficha({ slug: 'ana-perez', nombre: 'Ana Pérez' }),
    ficha({ slug: 'ana-perez', nombre: 'Otra Persona' }),
  ]);
  assert.ok(errores.some((e) => e.mensaje.includes('ya lo usa')));
});

test('rechaza un slug que choca con un nombre de tema', () => {
  const { errores } = validar([ficha({ slug: 'v1' })]);
  assert.ok(errores.some((e) => e.mensaje.includes('reservado')));
});

test('rechaza un slug reservado por la raíz del sitio', () => {
  for (const slug of ['index', 'assets', 'robots']) {
    const { errores } = validar([ficha({ slug })]);
    assert.ok(errores.some((e) => e.mensaje.includes('reservado')), slug);
  }
});

test('rechaza url_publica: decidía la URL grabada en el QR impreso', () => {
  const { errores } = validar([ficha({ url_publica: 'https://tarjeta-falsa.example/pagar' })]);
  assert.ok(
    errores.some((e) => e.ruta.endsWith('.url_publica') && e.mensaje.includes('desconocido')),
    'url_publica debería caer como campo desconocido'
  );
});

test('rechaza cualquier campo no previsto (additionalProperties: false)', () => {
  const { errores } = validar([ficha({ telefono_personal: '3001234567' })]);
  assert.ok(errores.some((e) => e.ruta.endsWith('.telefono_personal')));
});

test('exige los campos que dejaban una tarjeta en blanco', () => {
  assert.ok(rutasConError(validar([{ nombre: 'Sin Slug', marca_id: 'topp-create' }])).some((r) => r.endsWith('.slug')));
  assert.ok(rutasConError(validar([{ slug: 'sin-nombre', marca_id: 'topp-create' }])).some((r) => r.endsWith('.nombre')));
  assert.ok(rutasConError(validar([ficha({ nombre: '   ' })])).some((r) => r.endsWith('.nombre')));
});

test('rechaza tipos equivocados en vez de reventar con un stack de Node', () => {
  assert.ok(validar([ficha({ slug: 123 })]).errores.length > 0);
  assert.ok(validar(['no soy un objeto']).errores.length > 0);
  assert.ok(validarDatos({ marcas: [MARCA], personas: {}, config: CONFIG }).errores.length > 0);
});

test('exige exactamente una marca: por id o embebida, no las dos ni ninguna', () => {
  const sinMarca = validar([{ slug: 'ana-perez', nombre: 'Ana Pérez' }]);
  assert.ok(sinMarca.errores.some((e) => e.mensaje.includes('marca_id o una marca embebida')));

  const ambas = validar([ficha({ marca: { id: 'propia', nombre: 'Propia' } })]);
  assert.ok(ambas.errores.some((e) => e.mensaje.includes('deja solo uno')));

  const soloEmbebida = validar([
    { slug: 'ana-perez', nombre: 'Ana Pérez', marca: { id: 'propia', nombre: 'Propia' } },
  ]);
  assert.deepEqual(soloEmbebida.errores, []);
});

test('rechaza un marca_id que no existe en marcas.json', () => {
  const { errores } = validar([ficha({ marca_id: 'marca-fantasma' })]);
  assert.ok(errores.some((e) => e.mensaje.includes('no existe en marcas.json')));
});

test('la marca embebida se valida con las mismas reglas', () => {
  const { errores } = validar([
    { slug: 'ana-perez', nombre: 'Ana Pérez', marca: { id: 'propia', nombre: 'P', logo: '../fuera.png' } },
  ]);
  assert.ok(errores.some((e) => e.ruta.includes('.marca.logo')));
});

test('un enlace javascript: no pasa', () => {
  const { errores, avisos } = validar([ficha({ linkedin: 'javascript:alert(1)' })]);
  assert.ok([...errores, ...avisos].some((e) => e.ruta.endsWith('.linkedin')));
});

test('base_url debe ser https: va grabada en el QR', () => {
  for (const base_url of ['http://ejemplo.com', 'no-es-url', 'javascript:alert(1)']) {
    const { errores } = validarDatos({
      marcas: [MARCA],
      personas: [ficha({})],
      config: { base_url },
    });
    assert.ok(errores.some((e) => e.ruta.endsWith('.base_url')), base_url);
  }
});

test('el correo debe caer en un dominio de su marca', () => {
  const marcas = [{ ...MARCA, dominios_correo: ['toppcreate.com'] }];
  const mal = validarDatos({
    marcas,
    personas: [ficha({ email: 'arq.ana@otramarca.com' })],
    config: CONFIG,
  });
  assert.ok(mal.errores.some((e) => e.mensaje.includes('no está entre los dominios')));

  const bien = validarDatos({
    marcas,
    personas: [ficha({ email: 'arq.ana@toppcreate.com' })],
    config: CONFIG,
  });
  assert.deepEqual(bien.errores, []);
});

test('sin dominios_correo declarados no se exige nada', () => {
  const { errores } = validar([ficha({ email: 'ana@loquesea.com' })]);
  assert.deepEqual(errores, []);
});

test('una fuente propia obliga a declarar su licencia', () => {
  // Servir un .ttf desde un sitio público es redistribuirlo, y no toda licencia
  // de escritorio lo permite.
  const sinLicencia = [{ ...MARCA, tipografia: { familia: 'Poppins', archivo: 'Poppins.ttf' } }];
  const falla = validarDatos({ marcas: sinLicencia, personas: [ficha({})], config: CONFIG });
  assert.ok(falla.errores.some((e) => e.ruta.endsWith('tipografia.licencia')));

  const conLicencia = [
    { ...MARCA, tipografia: { familia: 'Poppins', archivo: 'Poppins.ttf', licencia: 'OFL-1.1' } },
  ];
  const pasa = validarDatos({ marcas: conLicencia, personas: [ficha({})], config: CONFIG });
  assert.deepEqual(pasa.errores, []);
});

test('la tipografía admite la forma corta y rechaza rutas en el archivo', () => {
  assert.deepEqual(
    validarDatos({ marcas: [{ ...MARCA, tipografia: 'Montserrat' }], personas: [ficha({})], config: CONFIG }).errores,
    []
  );
  const conRuta = [
    { ...MARCA, tipografia: { familia: 'X', archivo: '../../../etc/passwd', licencia: 'OFL-1.1' } },
  ];
  const { errores } = validarDatos({ marcas: conRuta, personas: [ficha({})], config: CONFIG });
  assert.ok(errores.some((e) => e.ruta.endsWith('tipografia.archivo')));
});

test('listar_en_indice solo admite true o false', () => {
  assert.deepEqual(validar([ficha({ listar_en_indice: true })]).errores, []);
  const { errores, avisos } = validar([ficha({ listar_en_indice: 'sí' })]);
  assert.ok([...errores, ...avisos].some((e) => e.ruta.endsWith('.listar_en_indice')));
});

test('la paleta admite los cinco roles del manual', () => {
  const marcas = [
    {
      ...MARCA,
      colores: {
        oscuro: '#121212', claro: '#8E8B86', fondo: '#F5F2EB',
        apoyo: '#C8C1B8', acento: '#2C2C2C',
      },
    },
  ];
  const { errores, avisos } = validarDatos({ marcas, personas: [ficha({})], config: CONFIG });
  assert.deepEqual(errores, []);
  assert.deepEqual(avisos, []);
});

test('un color mal escrito avisa pero no bloquea la publicación', () => {
  const marcas = [{ ...MARCA, colores: { oscuro: 'rojo', claro: '#B3B3B3', fondo: '#FFF' } }];
  const { errores, avisos } = validarDatos({ marcas, personas: [ficha({})], config: CONFIG });
  assert.deepEqual(errores, [], 'el contenido no debería impedir publicar al resto');
  assert.ok(avisos.some((a) => a.ruta.includes('colores.oscuro')));
});
