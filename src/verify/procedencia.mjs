/* Procedencia: cada sello lleva la fecha que declara SU fuente.

   POR QUÉ EXISTE
   Hasta el 2026-09-17 los sellos de P-02, P-03, P-05, P-07 y C-05, y la
   procedencia de `hierarchy.json`, publicaban «Corte 2026-08-30», que es el
   corte de SciVal: `procedencia()` lo ponía por defecto y el export de Scopus
   no declara el suyo (T-06). La ficha técnica lo advertía, y nada impedía que
   volviera a pasar. Hoy un sello de Scopus rotula la fecha de su export
   (D-669).

   Las fechas salen de `meta.json` —`exports.Scopus` y `exports.SciVal`—, no
   de esta prueba: con 2026-09-08 escrito a mano mentiría en la próxima carga.
   Mira las dos capas que pueden romperlo por separado:

     1. los objetos `procedencia` de todos los artefactos de dist/data, y
     2. el HTML de los sellos de la portada y de las secciones, compuesto con
        las funciones que usan el pre-renderizado y el navegador
        (`procedencias`, `explorador`, `seccion`): un campo que se pierde entre
        `series.json` y el sello sólo se ve aquí.

   Sin servidor, como coherencia.mjs. La fila de `hierarchy.json` en «Descarga
   de datos» la compone el pre-renderizado y la comprueba flujos.mjs.

   Uso:  node src/verify/procedencia.mjs [dist] */

import { readFile, readdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const DIST = resolve(process.argv[2] || process.env.DIST || 'dist');
const vx = await import(pathToFileURL(join(DIST, 'assets', 'js', 'vista_explorador.js')).href);
const leer = async (n) => JSON.parse(await readFile(join(DIST, 'data', n), 'utf8'));

const meta = await leer('meta.json');
const { Scopus, SciVal } = meta.exports;
// Si un día el export de Scopus declara su corte, el sello vuelve a «Corte»
// con ESA fecha, y la prueba lo acepta sin tocarla.
const ESPERADO = {
  Scopus: Scopus.fecha_corte ? ['Corte', Scopus.fecha_corte] : ['Export', Scopus.fecha_export],
  SciVal: ['Corte', SciVal.fecha_corte],
};

let fallos = 0;
const ok = (cond, msg) => { if (!cond) fallos++; console.log(`  ${cond ? '·' : '✗'} ${msg}`); };

/* ── 1. Los artefactos ─────────────────────────────────────────────────── */

const procs = [];
function buscar(o, ruta) {
  if (Array.isArray(o)) o.forEach((v, i) => buscar(v, `${ruta}[${i}]`));
  else if (o && typeof o === 'object') {
    for (const [k, v] of Object.entries(o)) {
      if (k === 'procedencia' && v && typeof v === 'object') procs.push([`${ruta}.${k}`, v]);
      buscar(v, `${ruta}.${k}`);
    }
  }
}
for (const f of await readdir(join(DIST, 'data'), { recursive: true })) {
  if (f.endsWith('.json')) buscar(await leer(f), f.replaceAll('\\', '/'));
}

/* Cuántas hay de cada fuente y cuáles traen otra fecha. Con cero de una
   fuente la prueba pasaría sin haber mirado nada: eso también es un fallo. */
const resumen = (titulo, vistos, malos) => {
  console.log(`  ${titulo}`);
  for (const f of ['Scopus', 'SciVal']) {
    malos[f].forEach((m) => console.log(`      ${m}`));
    ok(vistos[f] > 0 && !malos[f].length,
      `${vistos[f]} de ${f} · ${malos[f].length} sin «${ESPERADO[f].join(' ')}»`);
  }
};

const vistosA = { Scopus: 0, SciVal: 0 };
const malosA = { Scopus: [], SciVal: [] };
for (const [ruta, p] of procs) {
  // Las fuentes que no son de Elsevier (PD-01 a PD-04) traen su propia fecha.
  if (!ESPERADO[p.fuente]) continue;
  vistosA[p.fuente]++;
  const [rotulo, fecha] = ESPERADO[p.fuente];
  const bien = rotulo === 'Corte' ? p.corte === fecha : p.corte === null && p.export === fecha;
  if (!bien) malosA[p.fuente].push(`${ruta}: corte ${p.corte}, export ${p.export}`);
}
resumen('Procedencias en los artefactos', vistosA, malosA);

/* ── 2. Los sellos compuestos ──────────────────────────────────────────── */

const series = await leer('series.json');
const { publicaciones } = await leer('publications.json');
const autores = await leer('authors.json');
const proc = vx.procedencias(series, meta);
const jerarquia = meta.jerarquia || {};
const umbral = autores.parametros?.n_minimo_interpretable;
const unidadPorPersona = new Map(autores.autores.map((a) => [a.nombre, (a.unidades || [])[0]]));

const portada = vx.explorador(publicaciones, {}, proc, jerarquia, meta, umbral, null);
const paginas = [['portada', portada.cortes + portada.dinamica + portada.masCitadas],
  ...Object.keys(vx.SECCIONES).map((clave) => [clave,
    vx.seccion(publicaciones, {}, clave, proc, unidadPorPersona, jerarquia, meta, umbral, null).cortes])];

const vistosS = { Scopus: 0, SciVal: 0 };
const malosS = { Scopus: [], SciVal: [] };
for (const [pagina, html] of paginas) {
  for (const [, cuerpo] of html.matchAll(/<p class="sello[^"]*">([\s\S]*?)<\/p>/g)) {
    const fuente = (cuerpo.match(/<b>Fuente<\/b> ([^<]*)<\/span>/) || [])[1];
    if (!ESPERADO[fuente]) continue;
    vistosS[fuente]++;
    const fechas = [...cuerpo.matchAll(/<b>(Corte|Export)<\/b> ([^<]*)<\/span>/g)].map((m) => `${m[1]} ${m[2]}`);
    if (fechas.length !== 1 || fechas[0] !== ESPERADO[fuente].join(' ')) {
      malosS[fuente].push(`${pagina}: «${fechas.join(' · ') || 'sin fecha'}»`);
    }
  }
}
resumen('Sellos de la portada y las secciones', vistosS, malosS);

console.log(`\n  TOTAL: ${fallos} comprobación(es) fallida(s)`);
process.exit(fallos ? 1 : 0);
