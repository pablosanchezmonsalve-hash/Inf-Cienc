/* Desborde horizontal en viewports angostos. Antes cubría sólo index/impacto
   sin guarda de cobertura ni fallo real —desborde>0 se imprimía y el paso
   pasaba igual—, así que nunca habría detectado el propio caso que motivó
   ampliarlo: publicaciones.html (tabla ancha) y produccion.html (Bento Grid
   con heatmap/treemap) nunca se habían comprobado. Ahora cubre las mismas
   11 páginas que contraste.mjs, con su misma guarda, y falla de verdad. */
import { readdir } from 'node:fs/promises';
import { abrir } from './navegador.mjs';

const PUERTO = process.env.PUERTO || 8841;
const PAGINAS = ['index', 'produccion', 'impacto', 'colaboracion', 'tematica',
  'autores', 'publicaciones', 'indicadores', 'produccion-ampliada', 'metodologia', 'autor'];

const DIST = process.argv[2] || process.env.DIST || 'dist';
const enDisco = (await readdir(DIST)).filter(f => f.endsWith('.html'));
const cubiertas = new Set(PAGINAS.map(p => `${p}.html`));
const sinCubrir = enDisco.filter(f => !cubiertas.has(f));
if (sinCubrir.length) {
  console.log(`  ✗ páginas en ${DIST}/ que nadie comprueba: ${sinCubrir.join(', ')}`);
}

const b = await abrir();
let total = 0;
for (const [w, h, etq] of [[430, 900, 'movil'], [860, 1000, 'tableta']]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  const pg = await ctx.newPage();
  for (const p of PAGINAS) {
    const url = `http://127.0.0.1:${PUERTO}/${p}.html`
      + (p === 'autor' ? '?id=giglio-jimenez-a' : '');
    await pg.goto(url, { waitUntil: 'networkidle' });
    await pg.waitForTimeout(600);
    const desborde = await pg.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (desborde > 0) total++;
    console.log(`  ${etq.padEnd(8)} ${p.padEnd(18)} desborde horizontal ${desborde}px`
      + (desborde > 0 ? '  ✗' : ''));
    await pg.screenshot({ path: `.shots/R-${p}-${etq}.png` });
  }
  await ctx.close();
}
await b.close();
console.log(`\n  TOTAL: ${total + sinCubrir.length} fallo(s) de desborde`);
process.exit(total + sinCubrir.length ? 1 : 0);
