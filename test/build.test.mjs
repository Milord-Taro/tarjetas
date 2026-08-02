// El build de punta a punta, con fichas hostiles.
//
// validar.test.mjs comprueba el esquema por dentro; esto comprueba que el build
// de verdad se planta: que sale con código 1, que no escribe nada y —sobre
// todo— que no escribe nada FUERA del directorio de salida.
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, 'scripts', 'build.mjs');

const MARCAS = [
  {
    id: 'topp-create',
    nombre: 'TOPP CREATE',
    colores: { oscuro: '#4D4D4D', claro: '#B3B3B3', fondo: '#FFFFFF' },
    logo: 'logo-vertical-gris.png',
  },
];
const CONFIG = { base_url: 'https://ejemplo.test/tarjetas', tema: 'v2' };

/**
 * Compila las fichas dadas en un directorio temporal.
 * Devuelve { estado, salida, dist, raiz } — `raiz` es el temporal que contiene
 * tanto data/ como dist/, para poder mirar si algo se escribió fuera de sitio.
 */
function compilar(personas, { marcas = MARCAS, config = CONFIG } = {}) {
  const raiz = mkdtempSync(path.join(tmpdir(), 'tarjetas-test-'));
  const dataDir = path.join(raiz, 'data');
  const distDir = path.join(raiz, 'dist');
  mkdirSync(dataDir);
  mkdirSync(distDir);
  writeFileSync(path.join(dataDir, 'marcas.json'), JSON.stringify(marcas));
  writeFileSync(path.join(dataDir, 'personas.json'), JSON.stringify(personas));
  writeFileSync(path.join(dataDir, 'config.json'), JSON.stringify(config));

  let estado = 0;
  let salida = '';
  try {
    salida = execFileSync('node', [BUILD, '--data', dataDir, '--out', distDir], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (error) {
    estado = error.status ?? 1;
    salida = `${error.stdout ?? ''}${error.stderr ?? ''}`;
  }
  return { estado, salida, dist: distDir, raiz };
}

// El manifiesto se escribe junto a la salida, así que cada compilación de test
// tiene el suyo y no toca el del repo.
const leerManifiesto = (raiz) =>
  JSON.parse(readFileSync(path.join(raiz, 'build', 'manifiesto.json'), 'utf8'));

const ficha = (campos) => ({ slug: 'ana-perez', nombre: 'Ana Pérez', marca_id: 'topp-create', ...campos });

test('una ficha correcta compila', () => {
  const { estado, dist } = compilar([ficha({})]);
  assert.equal(estado, 0);
  assert.ok(existsSync(path.join(dist, 'ana-perez', 'index.html')));
  assert.ok(existsSync(path.join(dist, 'ana-perez', 'contacto.vcf')));
  assert.ok(existsSync(path.join(dist, 'index.html')));
});

test('un slug con ".." no escribe fuera de dist/ y aborta el build', () => {
  const { estado, salida, dist, raiz } = compilar([ficha({ slug: '../../escapado' })]);

  assert.equal(estado, 1, 'el build debería fallar');
  assert.match(salida, /slug/);
  // Nada dentro de dist/ …
  assert.deepEqual(readdirSync(dist), []);
  // … y nada fuera tampoco: solo siguen ahí data/ y dist/.
  assert.deepEqual(readdirSync(raiz).sort(), ['data', 'dist']);
  assert.ok(!existsSync(path.join(path.dirname(raiz), 'escapado')));
});

test('un marca_id con ".." no copia imágenes de fuera al sitio', () => {
  const { estado, dist } = compilar([ficha({ marca_id: '../../../assets' })]);
  assert.equal(estado, 1);
  assert.deepEqual(readdirSync(dist), []);
});

test('dos fichas con el mismo slug abortan en vez de pisarse', () => {
  const { estado, salida, dist } = compilar([
    ficha({ nombre: 'Primera Persona' }),
    ficha({ nombre: 'Segunda Persona' }),
  ]);
  assert.equal(estado, 1);
  assert.match(salida, /ya lo usa/);
  assert.deepEqual(readdirSync(dist), []);
});

test('el nombre se escapa en la raíz: es texto libre y sí llega hasta ahí', () => {
  // El slug ya no puede llevar HTML, pero el nombre es texto libre por diseño.
  const { estado, dist } = compilar([ficha({ nombre: 'Ana <script>alert(1)</script> Pérez' })]);
  assert.equal(estado, 0);

  const raizHtml = readFileSync(path.join(dist, 'index.html'), 'utf8');
  assert.ok(!raizHtml.includes('<script>alert(1)</script>'), 'la raíz no debe llevar script crudo');
  assert.ok(raizHtml.includes('&lt;script&gt;'));

  const tarjeta = readFileSync(path.join(dist, 'ana-perez', 'index.html'), 'utf8');
  assert.ok(!tarjeta.includes('<script>alert(1)</script>'));
});

test('la raíz lleva noindex en las dos formas (redirect y listado)', () => {
  const una = compilar([ficha({})]);
  assert.match(readFileSync(path.join(una.dist, 'index.html'), 'utf8'), /noindex/);

  const varias = compilar([ficha({}), ficha({ slug: 'luis-gomez', nombre: 'Luis Gómez' })]);
  assert.match(readFileSync(path.join(varias.dist, 'index.html'), 'utf8'), /noindex/);
});

test('un campo desconocido en la ficha aborta el build', () => {
  const { estado, salida } = compilar([ficha({ url_publica: 'https://falsa.test/pagar' })]);
  assert.equal(estado, 1);
  assert.match(salida, /url_publica/);
});

test('un color en forma corta compila y llega normalizado a seis dígitos', () => {
  // "#fff" es válido en CSS y el build lo aceptaba, pero hacía reventar
  // generar_imagenes.py, que solo entiende #rrggbb.
  const marcas = [{ ...MARCAS[0], colores: { oscuro: '#abc', claro: '#B3B3B3', fondo: '#fff' } }];
  const { estado, dist, raiz } = compilar([ficha({})], { marcas });
  assert.equal(estado, 0);

  const css = readFileSync(path.join(dist, 'ana-perez', 'index.html'), 'utf8');
  assert.ok(css.includes('#AABBCC'), 'el color corto debería expandirse');

  const manifiesto = leerManifiesto(raiz);
  for (const color of Object.values(manifiesto.personas[0].colores)) {
    assert.match(color, /^#[0-9A-F]{6}$/, `${color} debería venir en forma larga y sin alfa`);
  }
});

test('la URL del QR la calcula el build, no la ficha', () => {
  const { estado, raiz } = compilar([ficha({})]);
  assert.equal(estado, 0);
  const manifiesto = leerManifiesto(raiz);
  assert.equal(manifiesto.personas[0].url_publica, 'https://ejemplo.test/tarjetas/ana-perez/');
});

test('data/ del repo compila sin errores ni avisos', () => {
  const salida = execFileSync('node', [path.join(ROOT, 'scripts', 'validar.mjs')], { encoding: 'utf8' });
  assert.match(salida, /✓ data\/ válido/);
  assert.ok(!salida.includes('⚠'), `data/ del repo no debería dar avisos:\n${salida}`);
});

test.after(() => {
  // Los temporales quedan bajo tmpdir(); se limpian al vuelo para no acumular.
  for (const nombre of readdirSync(tmpdir())) {
    if (nombre.startsWith('tarjetas-test-')) {
      rmSync(path.join(tmpdir(), nombre), { recursive: true, force: true });
    }
  }
});
