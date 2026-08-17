/* Auditoría del sitio construido: errores de consola, peticiones fallidas,
   identificadores duplicados, ARIA roto, enlaces internos rotos y accesibilidad
   estructural. Se corre sobre dist/, no sobre el código fuente. */

import { abrir } from './navegador.mjs';
import { readdir, readFile } from 'node:fs/promises';

const PORT = process.env.PUERTO || 8841;
const DIST = process.argv[2] || process.env.DIST || 'dist';
const RUTAS = [
  ['index.html', ''], ['produccion.html', ''], ['impacto.html', ''],
  ['colaboracion.html', ''], ['tematica.html', ''], ['autores.html', ''],
  ['publicaciones.html', ''], ['indicadores.html', ''],
  ['metodologia.html', ''],
  ['autor.html', '?id=giglio-jimenez-a'],
];

const b = await abrir();
let problemas = 0;
const anotar = (m) => { problemas++; console.log(`      ✗ ${m}`); };

for (const tema of ['light', 'dark']) {
  const ctx = await b.newContext({ viewport: { width: 1360, height: 1000 }, colorScheme: tema });
  const pg = await ctx.newPage();

  for (const [archivo, query] of RUTAS) {
    const consola = [], fallidas = [], excepciones = [];
    pg.removeAllListeners();
    pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') consola.push(`${m.type()}: ${m.text()}`); });
    pg.on('pageerror', e => excepciones.push(e.message));
    pg.on('response', r => { if (r.status() >= 400) fallidas.push(`${r.status()} ${r.url().split('/').pop()}`); });

    await pg.goto(`http://127.0.0.1:${PORT}/${archivo}${query}`, { waitUntil: 'networkidle' });
    await pg.waitForTimeout(700);

    console.log(`  ${tema === 'dark' ? 'oscuro' : 'claro '} ${archivo}`);
    excepciones.forEach(e => anotar(`excepción JS: ${e}`));
    consola.forEach(c => anotar(`consola ${c}`));
    fallidas.forEach(f => anotar(`petición ${f}`));

    const est = await pg.evaluate(() => {
      const r = { dupes: [], ariaRoto: [], sinAlt: 0, h1: 0, saltos: [], botonSinNombre: [], anclasRotas: [] };
      // Identificadores duplicados
      const vistos = new Map();
      document.querySelectorAll('[id]').forEach(e => {
        vistos.set(e.id, (vistos.get(e.id) || 0) + 1);
      });
      vistos.forEach((n, id) => { if (n > 1) r.dupes.push(`${id} ×${n}`); });
      // aria-controls / aria-labelledby / aria-describedby que apuntan a nada
      document.querySelectorAll('[aria-controls],[aria-labelledby],[aria-describedby]').forEach(e => {
        ['aria-controls', 'aria-labelledby', 'aria-describedby'].forEach(a => {
          const v = e.getAttribute(a);
          if (v) v.split(/\s+/).forEach(id => {
            if (!document.getElementById(id)) r.ariaRoto.push(`${a}="${id}"`);
          });
        });
      });
      // Un h1 por página
      r.h1 = document.querySelectorAll('h1').length;
      // Saltos de nivel de encabezado
      const niveles = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]);
      niveles.forEach((n, i) => {
        if (i && n > niveles[i - 1] + 1) r.saltos.push(`h${niveles[i - 1]} → h${n}`);
      });
      // Botones sin nombre accesible
      document.querySelectorAll('button').forEach(bt => {
        const nombre = (bt.getAttribute('aria-label') || bt.textContent || bt.title || '').trim();
        if (!nombre) r.botonSinNombre.push(bt.outerHTML.slice(0, 60));
      });
      // Anclas internas que no existen
      document.querySelectorAll('a[href^="#"]').forEach(a => {
        const id = a.getAttribute('href').slice(1);
        if (id && !document.getElementById(id)) r.anclasRotas.push('#' + id);
      });
      return r;
    });

    est.dupes.forEach(d => anotar(`id duplicado: ${d}`));
    [...new Set(est.ariaRoto)].forEach(a => anotar(`ARIA apunta a nada: ${a}`));
    if (est.h1 !== 1) anotar(`${est.h1} elementos h1 (debe haber 1)`);
    [...new Set(est.saltos)].forEach(s => anotar(`salto de encabezado ${s}`));
    est.botonSinNombre.forEach(x => anotar(`botón sin nombre accesible: ${x}`));
    [...new Set(est.anclasRotas)].forEach(x => anotar(`ancla interna rota ${x}`));
  }
  await ctx.close();
}

// ---- Enlaces internos entre páginas, leídos del HTML desplegable
console.log('\n  Enlaces internos entre páginas');
const htmls = (await readdir(DIST)).filter(f => f.endsWith('.html'));

/* GUARDA DE COBERTURA. La lista RUTAS está escrita a mano porque algunas
   páginas necesitan parámetros —la ficha de autor no dice nada sin `?id=`—,
   pero una lista a mano deja de cubrirlo todo en cuanto alguien añade una
   página, y el barrido sigue diciendo «0 problemas» sobre lo que no miró.
   Este proyecto ya pagó eso dos veces. Si aparece una página que nadie
   comprueba, esto falla y dice cuál. */
const cubiertas = new Set(RUTAS.map(([f]) => f));
for (const f of htmls) {
  if (!cubiertas.has(f)) {
    anotar(`${f} existe en dist/ y no está en RUTAS: nadie la comprueba`);
  }
}
for (const f of htmls) {
  const s = await readFile(`${DIST}/${f}`, 'utf8');
  const destinos = [...s.matchAll(/href="([^"#?:]+\.html)/g)].map(m => m[1]);
  for (const d of new Set(destinos)) {
    if (!htmls.includes(d)) anotar(`${f} enlaza a ${d}, que no existe`);
  }
}

await b.close();
console.log(`\n  TOTAL: ${problemas} problema(s)`);
process.exit(problemas ? 1 : 0);
