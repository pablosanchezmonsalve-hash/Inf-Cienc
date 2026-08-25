/* informe_pdf.mjs — el informe institucional en PDF, desde el sitio construido.

   POR QUÉ EXISTE, HABIENDO UN BOTÓN
   El botón de la interfaz resuelve el caso de quien está mirando una sección y
   quiere llevársela. No resuelve el otro: un PDF del informe COMPLETO, igual en
   cada carga, que se pueda archivar y citar. Ese no puede depender de que
   alguien abra un navegador y acierte con los ajustes del diálogo.

   UN SOLO ORIGEN
   No hay una segunda maquetación. Este guion abre las mismas páginas de
   `dist/`, con la misma hoja de estilo y el mismo bloque `@media print` que usa
   el botón, y le pide al navegador el PDF. Si el informe cambia, cambia en un
   sitio; si divergiera, sería porque alguien escribió una segunda definición,
   que es justo lo que aquí no hay.

   Es el mismo patrón que `prerender.mjs` con `vista.js`: un cuerpo de código,
   dos consumidores.

   REQUISITO BLANDO
   Necesita Playwright y Chromium, que este proyecto ya usa para verificar el
   sitio. Sin ellos no corre y lo dice; el sitio se construye igual.

   Uso:  node src/build/informe_pdf.mjs <dist> <salida.pdf>
*/

import { createServer } from 'node:http';
import { readFile, stat, writeFile } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { abrir } from '../verify/navegador.mjs';

const dist = resolve(process.argv[2] || 'dist');
const salida = resolve(process.argv[3] || 'dist/informe-cienciometrico.pdf');

/* Las secciones del informe, en orden de lectura. NO incluye las superficies de
   consulta —publicaciones, autores, la ficha, el catálogo—: son tablas con
   filtro y paginación, y volcarlas enteras produciría un anexo de cientos de
   páginas que nadie lee. Quien las quiera las exporta en CSV. */
const SECCIONES = ['index.html', 'produccion.html', 'impacto.html',
                   'colaboracion.html', 'tematica.html', 'metodologia.html'];

const TIPOS = { '.html': 'text/html; charset=utf-8', '.css': 'text/css',
                '.js': 'text/javascript', '.json': 'application/json',
                '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };

const servir = (raiz) => new Promise((ok) => {
  const s = createServer(async (req, res) => {
    const ruta = join(raiz, decodeURIComponent(req.url.split('?')[0]));
    try {
      if ((await stat(ruta)).isDirectory()) throw new Error('dir');
      res.writeHead(200, { 'content-type': TIPOS[extname(ruta)] || 'application/octet-stream' });
      res.end(await readFile(ruta));
    } catch { res.writeHead(404).end('no'); }
  });
  s.listen(0, '127.0.0.1', () => ok({ s, puerto: s.address().port }));
});

const { s, puerto } = await servir(dist);
const nav = await abrir();
const ctx = await nav.newContext();
const pag = await ctx.newPage();

const partes = [];
for (const seccion of SECCIONES) {
  await pag.goto(`http://127.0.0.1:${puerto}/${seccion}`, { waitUntil: 'networkidle' });
  // Sin esto el PDF sale con los gráficos a medio dibujar en las páginas que
  // los pintan al hidratar: `networkidle` dice que la red calló, no que el
  // navegador terminó.
  await pag.waitForTimeout(400);
  partes.push({ seccion, buffer: await pag.pdf({ format: 'A4', printBackground: true }) });
  console.log(`  ${seccion.padEnd(20)} ${(partes.at(-1).buffer.length / 1024).toFixed(0)} KB`);
}

await nav.close();
s.close();

/* Se emite una parte por sección en vez de un PDF único porque unir PDF exige
   una dependencia de manipulación que este proyecto no tiene, y añadirla por
   esto sería pagar un árbol entero por un grapado. Se declara en vez de
   fingir un informe de una pieza. */
for (const { seccion, buffer } of partes) {
  const destino = salida.replace(/\.pdf$/, `-${seccion.replace(/\.html$/, '')}.pdf`);
  await writeFile(destino, buffer);
}
console.log(`\n  ${partes.length} secciones · ${salida.replace(/\.pdf$/, '-*.pdf')}`);
console.log('  Texto seleccionable y buscable: el navegador embebe las tipografías.');
