/* Coherencia entre las dos implementaciones de un mismo indicador.

   Varios indicadores se calculan DOS veces: en el build, en Python
   (`src/build/02_indicators.py` → `series.json`), y en el navegador
   (`explorador.js`), que los recalcula sobre el recorte y, bajo Node, para el
   HTML pre-renderizado. Sin filtros, los dos lados tienen que dar lo mismo.

   POR QUÉ EXISTE
   El 2026-09-15 apareció `R-01` publicado al revés: el build contaba Q1 como
   percentil SJR ≤ 25 y el navegador como ≥ 75, y la figura de Impacto decía
   Q1 = 194 donde la serie decía 578. Ninguna comprobación comparaba las dos
   implementaciones, así que cada una pasaba todas las demás por su cuenta.

   Se corre sobre dist/, como el resto de la batería: lo que se compara es lo
   que se publica.

   Uso:  node src/verify/coherencia.mjs [dist] */

import { readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const DIST = resolve(process.argv[2] || process.env.DIST || 'dist');
const X = await import(pathToFileURL(join(DIST, 'assets', 'js', 'explorador.js')).href);
const leer = async (n) => JSON.parse(await readFile(join(DIST, 'data', n), 'utf8'));
const { publicaciones } = await leer('publications.json');
const series = await leer('series.json');

let fallos = 0;

/** Compara dos repartos `{valor, n}` categoría a categoría, sin depender del
    orden: una categoría que falte en un lado cuenta como divergencia. */
function comparar(cod, navegador, build) {
  const a = new Map(navegador.map((d) => [String(d.valor), d.n]));
  const b = new Map(build.map((d) => [String(d.valor), d.n]));
  const claves = [...new Set([...a.keys(), ...b.keys()])];
  const distintas = claves.filter((k) => a.get(k) !== b.get(k));
  if (!distintas.length) {
    console.log(`  · ${cod}: ${claves.length} categorías coinciden`);
    return;
  }
  fallos++;
  console.log(`  ✗ ${cod}: el navegador y series.json no coinciden`);
  distintas.forEach((k) =>
    console.log(`      ${k}: navegador ${a.get(k) ?? '—'} · build ${b.get(k) ?? '—'}`));
}

// R-01 · cuartil de la revista: el mismo corte de percentil SJR en los dos lados.
comparar('R-01', X.porCampo(publicaciones, 'cuartil'), series['R-01'].datos);

// P-02 e I-01 · la tabla «Dinámica anual» de la portada contra las dos series.
const dinamica = X.dinamicaAnual(publicaciones, series['P-02'].datos.map((d) => d.anio));
comparar('P-02 · publicaciones por año (Dinámica anual)',
  dinamica.map((f) => ({ valor: f.anio, n: f.n })), series['P-02'].datos.map((d) => ({ valor: d.anio, n: d.n })));
comparar('I-01 · citas por año (Dinámica anual)',
  dinamica.map((f) => ({ valor: f.anio, n: f.citas })), series['I-01'].datos.map((d) => ({ valor: d.anio, n: d.n })));

// I-03 · FWCI institucional: media aritmética de los FWCI de cada publicación,
// que es la definición de SciVal para un conjunto (Research Metrics Guidebook
// 2019, §5.5.2; D-665), y la mediana, la misma función que usa el recorte.
const i03 = (await leer('kpis.json')).kpis.find((k) => k.codigo === 'I-03');
const fw = publicaciones.map((p) => p.fwci).filter((v) => typeof v === 'number');
const r2 = (v) => Math.round(v * 100) / 100;
const mediaFw = r2(fw.reduce((a, v) => a + v, 0) / fw.length);
if (i03.valor === mediaFw && i03.mediana === r2(X.mediana(fw))) {
  console.log(`  · I-03: media ${mediaFw} y mediana sobre ${fw.length} publicaciones coinciden`);
} else {
  fallos++;
  console.log(`  ✗ I-03: kpis.json ${i03.valor}/${i03.mediana} · publicaciones ${mediaFw}/${r2(X.mediana(fw))}`);
}

console.log(`\n  TOTAL: ${fallos} divergencia(s) entre navegador y build`);
process.exit(fallos ? 1 : 0);
